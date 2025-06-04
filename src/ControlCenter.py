#This code is for MQTT subscription and publishment.
from ParkingMQTT import ParkingMQTT as client
from Car import Car
import time
import math
from datetime import datetime
import json
import threading
from utils import CarStatus, ScannerStatus, GateStatus
from zoneinfo import ZoneInfo
import requests

italy_tz = ZoneInfo("Europe/Rome")

class Passage:
    def __init__(self, parking_lot_id, id, gate_id, info_topic_gate, command_topic_gate, scanner_id, info_topic_scanner, command_topic_scanner, timestamp = None):
        self.parking_lot_id = parking_lot_id
        self.id = id
        self.gate_id = gate_id
        self.info_topic_gate = info_topic_gate
        self.command_topic_gate = command_topic_gate
        self.scanner_id = scanner_id
        self.info_topic_scanner = info_topic_scanner
        self.command_topic_scanner = command_topic_scanner
        self.timestamp = timestamp
        
class Parking():
    exposed = True
        
    def __init__(self, client_id, broker, port, URL):
        # RESTFul
        self.URL = URL
        # URL
        self.URL = URL
        self.URL_PASSAGE= ''
        self.URL_CONFIG = ''
        # MQTT client initialization
        self.client = client(client_id, broker, port, self)
        self.client.start()
        
        self.bot = None
        self.bookings = {}
        self.parkings = {}
        self.passages = {}
        
        self.num_lots = 100
        self.free_stop = 60 ##seconds
        self.check_pay_interval = 60 ##seconds
        self.booking_expire_time = 300 ##seconds
        self.hourly_rate = 1.50 # euros   
        self.book_filter_interval = 600  # seconds, every 10 minutes   
        self.payment_filter_interval = 60 ##seconds 
        
        self.listening_catalog()
        self.listening_config()   
                
    def book(self, plate_license, expecting_time):
        if plate_license in self.bookings.keys():
            return [False, f"Car {plate_license} already booked at {(self.bookings[plate_license].expecting_time).strftime('%Y-%m-%d %H:%M:%S')}, please cancel it first"]
        elif len(self.parkings) + len(self.bookings) < self.num_lots:
                booking = Car(plate_license, expecting_time = expecting_time)
                booking.book()
                self.bookings[plate_license] = booking
                print(f"Car {plate_license} at {datetime.strftime(expecting_time,"%Y-%m-%d %H:%M:%S")} Booking successful")
                return [True, f"Car {plate_license} Booking successful, please check in before {datetime.strftime(expecting_time,"%Y-%m-%d %H:%M:%S")}!"]
        else:
            return [False, "No more parking lots available"]
        
    def cancel_booking(self, plate_license):
        if plate_license in self.bookings.keys():
            booking = self.bookings[plate_license]
            booking.cancel()
            del self.bookings[plate_license]
            print(f"Car {plate_license} Booking cancelled")
            return [True, f"Car {plate_license} Booking cancelled"]
        else:
            return [False, f"Car {plate_license} not found in bookings"]
    
    def check_in(self, plate_license, passage):
        if plate_license in self.bookings.keys():
            booking = self.bookings[plate_license]
            if booking.is_expired(self.booking_expire_time):
                print("Booking expired, checking available parking lots")
                del self.bookings[plate_license]
                self.check_in(plate_license, passage)
            else:
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
                while not passage.timestamp:
                    time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                booking.enter(passage.timestamp)
                print(f"Booking Car {plate_license} checked in")
                passage.timestamp = None
                del self.bookings[plate_license]
                self.parkings[plate_license] = booking
                booking.cancel()       
                self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)

        else:
            if len(self.parkings) + len(self.bookings) < self.num_lots:
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
                while not passage.timestamp:
                    time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                car = Car(plate_license, passage.timestamp)
                print(f"\n\nNew Car {plate_license} checked in\n\n")
                passage.timestamp = None
                self.parkings[plate_license] = car
                self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)
            else:
                self.publish(passage.command_topic_gate, GateStatus.CLOSE)
                print("\nno more parking lots available\n")
    
    def check(self, plate_license, method):
        if plate_license not in self.parkings.keys():
            return [False, f"Plate license {plate_license} not found in parking records"]
        if self.parkings[plate_license].status == CarStatus.CHECKED:
            return [True, f"Your Car {plate_license} last check still valid, please pay it"]
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHARGED:
            fee = self.hourly_rate * math.ceil((datetime.now() - car.start_time).total_seconds()/3600)
            car.check(fee, method, datetime.now())
            return [True, f"Car {plate_license} checked, please pay {fee} euros in {math.ceil(self.check_pay_interval/60)} minutes"]   
        elif (datetime.now() - car.start_time).total_seconds() > self.free_stop:
                car.status = CarStatus.CHARGED
                self.check(plate_license, method)
        else:
            msg = "Very short period after entering or last payment, No payment needed"
            print(msg)
            return [False, msg]
        
    def pay(self, plate_license):
        car = self.parkings[plate_license]
        if car.status == CarStatus.CHECKED:
            if (datetime.now() - car.payment.time).total_seconds() > self.check_pay_interval:
                car.failPay()
                return [False, f'It has been more than {self.check_pay_interval} since you checked, please retry']
            else:
                ## there should be connecting to payment gateway here in real world
                return [True, (f"This is your link to pay,"
                        f"http://payment_gateway.com/pay?plate_license={plate_license}&amount={car.payment.amount} (it is fake),"
                        f"please process it within {math.ceil(self.check_pay_interval/60)} minutes")]
    
    def paid(self, plate_license):
        car = self.parkings[plate_license]
        car.paid()
        return [True, f"Car {plate_license} paid, please exit within {math.ceil(self.free_stop/60)} minutes"]
                
    def check_out(self, plate_license, passage):
        if plate_license in self.parkings.keys():
            car = self.parkings[plate_license]  
            if car.status == CarStatus.CHECKED:
                self.publish(passage.command_topic_gate, GateStatus.CLOSE)
                print("need to pay before exit")
                
            elif car.status == CarStatus.PAID or car.status == CarStatus.ENTERED:
                if (datetime.now() - car.start_time).total_seconds() <= self.free_stop:                
                    self.publish(passage.command_topic_gate, GateStatus.OPEN)
                    while not passage.timestamp:
                        time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                    car.exit(passage.timestamp)
                    print(f"Car {plate_license} exited")
                    passage.timestamp = None             
                    del self.parkings[plate_license]
                    self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)
                else: 
                    self.publish(passage.command_topic_gate, GateStatus.CLOSE)
                    print(f"{car.plate_license} stayed more than {math.ceil(self.free_stop/60)} minutes after payment/entering, need to pay")
                    car.status = CarStatus.CHARGED                    
            else:
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
        
    def connect_device(self, passage):
        self.passages[passage.id] = passage
        self.client.subscribe(passage.info_topic_scanner)
        self.client.subscribe(passage.info_topic_gate)
    
    def disconnect_device(self, passage_id):
        if passage_id in self.passages.keys():
            del self.passages[passage_id]
            self.client.unsubscribe(self.passages[passage_id].info_topic_scanner)
            self.client.unsubscribe(self.passages[passage_id].info_topic_gate)
            print(f"Disconnected passage {passage_id} with gate {self.passages[passage_id].gate_id} and scanner {self.passages[passage_id].scanner_id}")
        else:
            print(f"Passage {passage_id} not found in devices")
    
    def connect_bot(self, bot):
        self.client.subscribe(bot.info_topic)
        self.bot = bot
        
    def publish(self, topic, message):
        self.client.publish(topic, message)
        print(f"Published message: {message} to topic: {topic}") 
        
    def notify(self, topic, payload):
        def notify_thread():
            try:
                data = json.loads(payload)
                if 'scanner' in topic.split('/')[-2] and topic.split('/')[-3] == 'entrance':
                    plate_license = data
                    print(f"EntranceScanner {topic.split('/')[-2]} detected plate: {data}")
                    for passage in self.passages.values():
                        if passage.info_topic_scanner == topic:     
                            self.check_in(plate_license, passage) 
                            break              
                            
                elif 'gate' in topic.split('/')[-2] and topic.split('/')[-3] == 'entrance':
                    entry_time = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                    print(f"EntranceGate {topic.split('/')[-2]} opened at: {data}")
                    for passage in self.passages.values():
                        if passage.info_topic_gate == topic:     
                            passage.timestamp = entry_time              
                            break
                
                elif 'scanner' in topic.split('/')[-2] and topic.split('/')[-3] == 'exit':
                    plate_license = data
                    print(f"ExitScanner {topic.split('/')[-2]} detected plate: {data}")
                    for passage in self.passages.values():
                        if passage.info_topic_scanner == topic:     
                            self.check_out(plate_license, passage) 
                            break              
                            
                elif 'gate' in topic.split('/')[-2] and topic.split('/')[-3] == 'exit':
                    exit_time = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                    print(f"ExitGate {topic.split('/')[-2]} opened at: {data}")
                    for passage in self.passages.values():
                        if passage.info_topic_gate == topic:     
                            passage.timestamp = exit_time              
                            break       
                elif topic == self.bot.info_topic:            
                    print(f'Received message: "{data}" from topic: "{self.bot.info_topic}"')
                    if data['action'] == 'book':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        expecting_time = datetime.strptime(data['expecting_time'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=italy_tz)
                        result = self.book(plate_license, expecting_time)
                        response = [chat_id, result[1]]
                        self.publish(self.bot.command_topic, response)
                    elif data['action'] == 'cancel':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        result = self.cancel_booking(plate_license)
                        response = [chat_id, result[1]]
                        self.client.publish(self.bot.command_topic, response)
                    elif data['action'] == 'availability':
                        num_lots = self.num_lots - len(self.parkings) - len(self.bookings)
                        chat_id = data['chat_id'] 
                        response = [chat_id, f"Free parking lots: {num_lots}"]
                        self.client.publish(self.bot.command_topic, response)  
                    elif data['action'] == 'pay_check':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        result = self.check(plate_license, 'online')
                        response = [chat_id, result[1]]
                        self.client.publish(self.bot.command_topic, response)
                    elif data['action'] == 'pay_pay':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        message = self.pay(plate_license)
                        response = [chat_id, message]
                        self.client.publish(self.bot.command_topic, response)
                        
                        # Simulate payment processing time
                        # In a real-world scenario, you would waiting for the payment gateway response
                        process = 3
                        message = [True, "lets assume the link is valid and you are processing the payment via it..."]
                        self.client.publish(self.bot.command_topic, response)
                        while process > 0:
                            message = [chat_id, f"Payment processing... {process} seconds remaining"]
                            self.client.publish(self.bot.command_topic, response)
                            time.sleep(1)
                            process -= 1
                        message = self.paid(plate_license)
                        response = [chat_id, message]
                        self.client.publish(self.bot.command_topic, response)
                        

                    
            except Exception as e:
                print("Error in notify_thread:", e)
        threading.Thread(target=notify_thread).start()
                
    def run(self):
        def keep_alive():
            start = time.time()
            while True:
                time.sleep(2)
                now = time.time()
                for car in self.parkings.values():
                    if car.status == CarStatus.CHECKED:
                        if (now - car.payment.time).seconds > self.check_pay_interval:
                            car.failPay()
                if (now - start) > self.book_filter_interval:
                    for booking in self.bookings.values():
                        if booking.is_expired(self.booking_expire_time):
                            del self.bookings[booking.plate_license]
                    start = now
        threading.Thread(target=keep_alive).start()  
       
    def listening_catalog(self):
        def listening_thread():
            while True:
                data = None
                while True:
                    try:
                        res = requests.get(self.URL_PASSAGE)
                        if res and res.ok:
                            data = res.json()
                            break
                    except Exception:
                        pass
                    time.sleep(1)
                data = res.json()
                if data[0]:
                    parking_lot_id, id, gate_id, info_topic_gate, command_topic_gate, scanner_id, info_topic_scanner, command_topic_scanner = data
                    passage = Passage(parking_lot_id, id, gate_id, info_topic_gate, command_topic_gate, scanner_id, info_topic_scanner, command_topic_scanner)
                    self.connect_device(passage)
                    print(f"New passage {id} connected with gate {gate_id} and scanner {scanner_id} ")
                else:
                    passage_id = data[1]
                    self.disconnect_device(passage_id)
                    print(f"Passage {passage_id} disconnected")
                time.sleep(1)
        threading.Thread(target=listening_thread).start()
        
    def listening_config(self):
        def listening_thread():
            while True:
                try:
                    res = requests.get(self.URL_CONFIG)
                    if res and res.ok:
                        break
                except Exception:
                    pass
                time.sleep(1)
            data = res.json()
            if 'num_lots' in data.keys():
                self.num_lots = data['num_lots']
                print(f"Configuration updated: num_lots={self.num_lots}")
            if 'free_stop' in data.keys():
                self.free_stop = data['free_stop']
                print(f"Configuration updated: free_stop={self.free_stop} seconds")
            if 'checking_time' in data.keys():
                self.check_pay_interval = data['checking_time']
                print(f"Configuration updated: checking_time={self.check_pay_interval} seconds")
            if 'hourly_rate' in data.keys():
                self.hourly_rate = data['hourly_rate']
                print(f"Configuration updated: hourly_rate={self.hourly_rate} euros")
            if 'check_book_interval' in data.keys():
                self.book_filter_interval = data['check_book_interval']
                print(f"Configuration updated: check_book_interval={self.book_filter_interval} seconds")
        threading.Thread(target=listening_thread).start()
       
       
if __name__ == '__main__': 
    from config_loader import ConfigLoader
    config_loader = ConfigLoader()
    client_id = 'ParkingSystem'
    broker = config_loader.MQTT.broker
    port = config_loader.MQTT.port
    host = config_loader.RESTful.host
    port_RESTFUL = config_loader.RESTful.port
    URL = f"http://{host}:{port_RESTFUL}"
    parking = Parking(client_id, broker, port, URL)
    parking.run()


