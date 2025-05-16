#This code is for MQTT subscription and publishment.
from ParkingMQTT import ParkingMQTT as client
from Car import Car
import cherrypy
import os
import time
import math
from datetime import datetime,timedelta
import json
import threading
from utils import FileManager, CarStatus, ScannerStatus, GateStatus, PaymentStatus, PaymentMethod
from zoneinfo import ZoneInfo

italy_tz = ZoneInfo("Europe/Rome")

class Parking():
    exposed = True
        
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port, self)
        self.num_lots = 100
        self.bookings = {}
        self.parkings = {}
        self.devices = {}
        self.client.start()
        self.free_stop = 30 ##seconds
        self.checking_time = 60 ##seconds
        self.hourly_rate = 1.50 # euros
        self.booking_advance = 2 # hours
    
    def connect_bot(self, info_topic, command_topic):
        self.client.subscribe(info_topic)
        self.bot_command_topic = command_topic
            
    def book(self, plate_license, expecting_time):
        if len(self.parkings) + len(self.bookings) < self.num_lots:
            if (expecting_time - datetime.now(italy_tz)).total_seconds() > 3600*2:
                return [False, f"Booking time should be no more than 2 hours in advance,the time now is {datetime.now(italy_tz)}"]
            else:
                booking = Car(plate_license, expecting_time = expecting_time)
                booking.book()
                self.bookings[plate_license] = booking
                return [True, f"Car {plate_license} at {expecting_time} Booking successful"]
        else:
            return [False, "No more parking lots available"]
        
    def cancel_booking(self, plate_license):
        if plate_license in self.bookings.keys():
            del self.bookings[plate_license]
            # Remove the booking from the JSON file
            booking_file = "bookings.json"
            if os.path.exists(booking_file):
                with open(booking_file, 'r') as f:
                    try:
                        booking_data = json.load(f)
                    except json.JSONDecodeError:
                        booking_data = {}
                if plate_license in booking_data:
                    del booking_data[plate_license]
                    with open(booking_file, 'w') as f:
                        json.dump(booking_data, f, indent=4)
            return [True, f"Car {plate_license} Booking scancelled"]
        return False
    
    def check_in(self, plate_license, device):
        def check_in_thread():
            if plate_license in self.bookings.keys():
                booking = self.bookings[plate_license]
                if booking.is_expired():
                    print("Booking expired")
                    del self.bookings[plate_license]
                else:
                    self.publish(device.command_topic_gate, GateStatus.OPEN)
                    while not device.timestamp:
                        time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                    booking.enter(device.timestamp)
                    print(f"Booking Car {plate_license} checked in")
                    device.timestamp = None
                    del self.bookings[plate_license]
                    self.parkings[plate_license] = booking
                    booking.cancel()       
                    self.publish(device.command_topic_scanner, ScannerStatus.STANDBY)

            else:
                if len(self.parkings) + len(self.bookings) < self.num_lots:
                    self.publish(device.command_topic_gate, GateStatus.OPEN)
                    while not device.timestamp:
                        time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                    car = Car(plate_license, device.timestamp)
                    print(f"\n\nNew Car {plate_license} checked in\n\n")
                    device.timestamp = None
                    self.parkings[plate_license] = car
                    self.publish(device.command_topic_scanner, ScannerStatus.STANDBY)
                else:
                    self.publish(device.command_topic_gate, GateStatus.CLOSE)
                    print("\nno more parking lots available\n")
        threading.Thread(target=check_in_thread).start()
    
    def check(self, plate_license, method):
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHARGED:
            fee = self.hourly_rate * math.ceil((datetime.now() - car.start_time).seconds/3600)
            car.check(fee, method, datetime.now())
            return True   
        elif (datetime.now() - car.start_time).seconds > self.free_stop:
                car.status = CarStatus.CHARGED
                self.check(plate_license, method)
                return True
        else:
            print("No payment needed")
            return False
        
    def pay(self, plate_license):
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHECKED:
            if (datetime.now() - car.payment.time).seconds > self.checking_time:
                car.failPay()
                return 'It has been to long, please retry'
            else:
                if car.pay():
                    return (f"Car {plate_license} paid, please exit within {math.ceil(self.free_stop/60)} minutes")
                else:
                    return ("Payment failed")
                
    def check_out(self, plate_license, device):
        def check_out_thread():
            if plate_license in self.parkings.keys():
                car = self.parkings[plate_license]  
                if car.status == CarStatus.CHECKED:
                    car.failPay()
                    self.publish(device.command_topic_gate, GateStatus.CLOSE)
                    print("need to pay before exit")
                    
                elif car.status == CarStatus.PAID or car.status == CarStatus.CHARGED:
                    if (datetime.now() - car.start_time).seconds <= self.free_stop:                
                        self.publish(device.command_topic_gate, GateStatus.OPEN)
                        while not device.timestamp:
                            time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                        car.exit(device.timestamp)
                        print(f"Car {plate_license} exited")
                        device.timestamp = None             
                        del self.parkings[plate_license]
                        self.publish(device.command_topic_scanner, ScannerStatus.STANDBY)
                    else: 
                        self.publish(device.command_topic_gate, GateStatus.CLOSE)
                        print(f"{car.plate_license} stayed more than {math.ceil(self.free_stop/60)} minutes after payment/entering, need to pay")
                        car.status = CarStatus.CHARGED                    
                else:
                    self.publish(device.command_topic_gate, GateStatus.OPEN)
        threading.Thread(target=check_out_thread).start()
        
    def connect_device(self, device):
        self.devices[device.id] = device
        self.client.subscribe(device.info_topic_scanner)
        self.client.subscribe(device.info_topic_gate)
    
    def publish(self, topic, message):
        self.client.publish(topic, message)
        print(f"Published message: {message} to topic: {topic}") 
        
    def notify(self, topic, payload):
        payload = json.loads(payload)
        if topic.split('/')[-2].startswith('scanner') and topic.split('/')[-3] == 'entrance':
            plate_license = payload
            print(f"EntranceScanner {topic.split('/')[-2]} detected plate: {payload}")
            for device in self.devices.values():
                if device.info_topic_scanner == topic:     
                    self.check_in(plate_license, device) 
                    break              
                    
        elif topic.split('/')[-2].startswith('gate') and topic.split('/')[-3] == 'entrance':
            entry_time = datetime.strptime(payload, "%Y-%m-%d %H:%M:%S")
            print(f"EntranceGate {topic.split('/')[-2]} opened at: {payload}")
            for device in self.devices.values():
                if device.info_topic_gate == topic:     
                    device.timestamp = entry_time              
                    break
        
        elif topic.split('/')[-2].startswith('scanner') and topic.split('/')[-3] == 'exit':
            plate_license = payload
            print(f"ExitScanner {topic.split('/')[-2]} detected plate: {payload}")
            for device in self.devices.values():
                if device.info_topic_scanner == topic:     
                    self.check_out(plate_license, device) 
                    break              
                    
        elif topic.split('/')[-2].startswith('gate') and topic.split('/')[-3] == 'exit':
            exit_time = datetime.strptime(payload, "%Y-%m-%d %H:%M:%S")
            print(f"ExitGate {topic.split('/')[-2]} opened at: {payload}")
            for device in self.devices.values():
                if device.info_topic_gate == topic:     
                    device.timestamp = exit_time              
                    break       
        elif topic.split('/')[-1] == 'bot':
            data = json.loads(payload)
            if data['action'] == 'book':
                plate_license = data['plate_license']
                expecting_time = datetime.strptime(data['expecting_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=italy_tz)
                result = self.book(plate_license, expecting_time)
                self.publish(result[1])

            elif data['action'] == 'cancel':
                plate_license = data['plate_license']
                plate_license = data.get('plate')
                chat_id = data.get('chat_id')
                success = self.cancel_booking(plate_license)
                # 通过MQTT回复结果
                msg = (f"Booking for {plate_license} has been cancelled."
                            if success else f"No active booking found for plate: {plate_license}")
                response = {'chat_id': chat_id, 'msg': msg}
                self.client.publish('polito_parking/bot/info', json.dumps([chat_id, msg]))
                print(f"Booking for {plate_license} has been cancelled.")
                print(f"Published message: {msg} to topic: polito_parking/bot/info")    
    def run(self):
        def keep_alive():
            while True:
                time.sleep(1)
        threading.Thread(target=keep_alive).start()  
        
    def GET(self):
        """
        Serve the payment_interface.html file.
        """
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(dir_path, 'frontend', 'payment_interface.html')
        if not os.path.exists(file_path):
            raise cherrypy.HTTPError(404, "File not found")
        return open(file_path, encoding = 'utf-8').read()

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri):
        """
        Handle the payment processing logic.
        """
        # Parse the JSON input
        data = cherrypy.request.json
        if len(uri) == 0:
            raise cherrypy.HTTPError(400,"Missing required fields: plate_license or payment_method")
        if uri[0] == 'check':
            plate_license = data.get("plate_license")
            payment_method = data.get("payment_method")                
            if plate_license not in self.parkings.keys():
                raise cherrypy.HTTPError(400,"Plate license not found in parking records")
            car = self.parkings[plate_license]
            if self.check(plate_license, payment_method):
                charged = True
                amount = car.payment.amount
                message = f"Car {plate_license} checked, please pay in {math.ceil(self.checking_time/60)} minutes"
            else:
                charged = False
                amount = 0
                message = "Very short Period, No payment needed"
            return {"charged": charged, 'amount': amount, "message": message}
        # Simulate payment processing
        if uri[0] == 'process_payment':
            plate_license = data.get("plate_license")
            car = self.parkings[plate_license]
            message = self.pay(plate_license)
            # Return success response
            return {"message": message}

