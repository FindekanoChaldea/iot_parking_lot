#This code is for MQTT subscription and publishment.
from ParkingMQTT import ParkingMQTT as client
from Car import Car
import cherrypy
import os
import time
import math
from datetime import datetime
import json
import threading
from utils import FileManager, CarStatus, ScannerStatus, GateStatus, PaymentStatus, PaymentMethod

class Parking():
    exposed = True
        
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port, self)
        self.num_lots = 100
        self.bookings = {}
        self.parkings = {}
        self.devices = {}
        self.client.start()
        self.free_stop = 20 ##seconds
        self.checking_time = 5 ##seconds
            
    def book(self, plate_license, expecting_time):
        if len(self.parkings) + len(self.bookings) < 100:
            booking = Car(plate_license, expecting_time = expecting_time)
            booking.save('../data/bookings.json')
            self.bookings[plate_license] = booking
        else:
            print("no more parking lots available")
    
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
                    fileManager = FileManager()
                    fileManager.find_and_delete('../data/bookings.json', plate_license)
                    self.publish(device.command_topic_scanner, ScannerStatus.STANDBY)

            else:
                if len(self.parkings) + len(self.bookings) < self.num_lots:
                    self.publish(device.command_topic_gate, GateStatus.OPEN)
                    while not device.timestamp:
                        time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                    car = Car(plate_license, device.timestamp)
                    print(f"New Car {plate_license} checked in")
                    self.parkings[plate_license] = car
                    self.publish(device.command_topic_scanner, ScannerStatus.STANDBY)
                else:
                    print("no more parking lots available")
        threading.Thread(target=check_in_thread).start()
    
    def check(self, plate_license, method):
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHARGED:
            fee = 1.50 * math.ceil((self.payment_time - self.start_time).seconds / 3600)
            car.check(fee, method, datetime.now())
            return True   
        elif (datetime.now() - car.start_time).seconds > self.free_stop:
                car.status = CarStatus.CHARGED
                self.check(plate_license, method)
        else:
            print("no payment needed")
            return False
        
    def pay(self, plate_license):
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHECKED:
            if (datetime.now() - car.start_time).seconds > self.checking_time:
                car.failPay()
                return 'It has been to long, please retry'
            else:
                if car.pay():
                    return (f"Car {plate_license} paid, please exit within {self.free_stop/60} minutes")
                else:
                    return ("Payment failed")
                
    def check_out(self, plate_license, device):
        def check_out_thread():
            if plate_license in self.parkings.keys():
                car = self.parkings[plate_license]           
                if car.status == CarStatus.PAID or car.status == CarStatus.CHARGED:
                    if (datetime.now() - car.start_time).seconds/60 <= self.free_stop:                
                        self.publich(device.command_topic_gate, GateStatus.OPEN)
                        while True:
                            if device.timestamp:
                                car.exit(device.timestamp)
                                print(f"Car {plate_license} exited")
                                device.timestamp = None
                                break               
                        del self.parkings[plate_license]
                        self.publich(device.command_topic_scanner, ScannerStatus.STANDBY)
                    else: 
                        print("stay more than {self.free_stop} after payment/entering, need to pay")
                        car.status = CarStatus.CHARGED
                        
                else:
                    print("need to pay before exit")
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
            print(f"Scanner {topic.split('/')[-2]} detected plate: {payload}")
            for device in self.devices.values():
                if device.info_topic_scanner == topic:     
                    self.check_in(plate_license, device) 
                    break              
                    
        elif topic.split('/')[-2].startswith('gate'):
            entry_time = datetime.strptime(payload, "%Y-%m-%d %H:%M:%S")
            print(f"Gate {topic.split('/')[-2]} opened at: {payload}")
            for device in self.devices.values():
                if device.info_topic_gate == topic:     
                    device.timestamp = entry_time              
                    break

    def GET(self):
        """
        Serve the payment_interface.html file.
        """
        dir_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        file_path = os.path.join(dir_path, 'frontend', 'payment_interface.html')
        if not os.path.exists(file_path):
            raise cherrypy.HTTPError(404, "File not found")
        return open(file_path).read()

    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def POST(self, *uri):
        """
        Handle the payment processing logic.
        """
        try:
            # Parse the JSON input
            data = cherrypy.request.json
            if len(uri) == 0:
                raise cherrypy.HTTPError(400, "Missing required fields: plate_license or payment_method")
            if uri[0] == 'check':
                plate_license = data.get("plate_license")
                payment_method = data.get("payment_method")
                car = self.parkings[plate_license]
                # Validate input
                if not plate_license or not payment_method:
                    raise cherrypy.HTTPError(400, "Missing required fields: plate_license or payment_method")
                if plate_license not in self.parkings.keys():
                    raise cherrypy.HTTPError(400, "Plate license not found in parking records.")
                if self.check(plate_license, payment_method):
                    charged = True
                    amount = car.payment.amount
                else:
                    charged = False
                    amount = 0
                    message = "No payment needed"
                return {"charged": charged, 'amount': amount, "message": message}
            # Simulate payment processing
            if uri[0] == 'process_payment':
                plate_license = data.get("plate_license")
                car = self.parkings[plate_license]
                message = self.pay(plate_license)
                # Return success response
                return {"message": message}

        except Exception as e:
            cherrypy.log(f"Error processing payment: {str(e)}")
            raise cherrypy.HTTPError(500, "An error occurred while processing the payment.")