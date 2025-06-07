#This code is for MQTT subscription and publishment.
from ParkingMQTT import ParkingMQTT as client
from Car import Car
import time
import math
from datetime import datetime, timedelta
import json
import threading
from utils import CarStatus, ScannerStatus, GateStatus
import requests
from TimeControl import TimeControl

class Passage:
    def __init__(self, parking_lot_id, id, scanner_id, info_topic_scanner, command_topic_scanner, gate_id, info_topic_gate, command_topic_gate, timestamp = None):
        self.parking_lot_id = parking_lot_id
        self.id = id
        self.gate_id = gate_id
        self.info_topic_gate = info_topic_gate
        self.command_topic_gate = command_topic_gate
        self.scanner_id = scanner_id
        self.info_topic_scanner = info_topic_scanner
        self.command_topic_scanner = command_topic_scanner
        self.timestamp = timestamp

class Bot:
    def __init__(self, id, info_topic, command_topic):
        self.id = id
        self.info_topic = info_topic
        self.command_topic = command_topic

class Lot:
    def __init__(self, id, num_lots):
        self.id = id
        self.num_lots = int(num_lots)
        self.passages = {}
        self.bookings = {}
        self.parkings = {}

    def add_passage(self, passage):
        self.passages[passage.id] = passage
    
    def set_num_lots(self, num_lots):
        num_lots = int(num_lots)
    
    def availability(self):
        available_lots = self.num_lots - len(self.parkings) - len(self.bookings)
        return available_lots
        
    def remove_passage(self, passage_id):
        if passage_id in self.passages:
            del self.passages[passage_id]
            print(f"Passage {passage_id} removed from parking lot {self.id}")
        else:
            print(f"Passage {passage_id} not found in parking lot {self.id}")
         
class Parking():
        
    def __init__(self, URL):
        #utilities
        self.time_control = TimeControl()
        # RESTFul
        self.URL = URL
        print('connecting to server...')
        [
        self.id,
        self.broker,
        self.port,
        self.URL_CATALOG,
        self.URL_PASSAGE,
        self.URL_LOT,
        
        self.free_stop,
        self.check_pay_interval,        
        self.booking_expire_time,
        self.hourly_rate,
        self.book_filter_interval,
        self.payment_filter_interval
         ] = [None] * 12
        self.load_config()
        
        self.client = client(self.id, self.broker, self.port, self)
        self.client.start()
        
        self.bot = None
        # self.bookings = {}
        # self.parkings = {}
        # self.passages = {}
        self.parking_lots = {}
        
        print(f"\n{self.id} initialized, free stop time: {self.free_stop} seconds, hourly rate: {self.hourly_rate} euros\n")
        self.listening_catalog()
        
    def load_config(self):
        timer = self.time_control.add_timer(60)
        data = None
        while not timer.timeout:
            try:
                res = requests.post(self.URL, json = 'parking_properties')
                if res and res.ok:
                    data = res.json()
                    break
            except Exception as e:
                pass
            time.sleep(3)
        # MQTT client initialization
        if [
            self.id,
            self.broker,
            self.port,
            self.URL_CATALOG,
            self.URL_PASSAGE,
            self.URL_LOT,
            self.free_stop,
            self.check_pay_interval,        
            self.booking_expire_time,
            self.hourly_rate,
            self.book_filter_interval,
            self.payment_filter_interval,
        ] != data:
            [
                self.id,
                self.broker,
                self.port,
                self.URL_CATALOG,
                self.URL_PASSAGE,
                self.URL_LOT,
                self.free_stop,
                self.check_pay_interval,        
                self.booking_expire_time,
                self.hourly_rate,
                self.book_filter_interval,
                self.payment_filter_interval,
            ] = data
            print(f"Config loaded: id = {self.id}, broker = {self.broker}, port = {self.port}, URL_CATALOG = {self.URL_CATALOG}, URL_PASSAGE = {self.URL_PASSAGE}, URL_CONFIG = {self.URL_LOT}, free_stop = {self.free_stop}, check_pay_interval = {self.check_pay_interval}, booking_expire_time = {self.booking_expire_time}, hourly_rate = {self.hourly_rate}, book_filter_interval = {self.book_filter_interval}, payment_filter_interval = {self.payment_filter_interval}\n")
            
    def book(self, lot_id, plate_license, expecting_time):
        if plate_license in self.parking_lots[lot_id].bookings.keys():
            return [False, f"Car {plate_license} already booked at {(self.bookings[plate_license].expecting_time).strftime('%Y-%m-%d %H:%M:%S')}, please cancel it first"]
        elif self.parking_lots[lot_id].availability():
                booking = Car(lot_id, plate_license, expecting_time = expecting_time)
                booking.book()
                self.parking_lots[lot_id].bookings[plate_license] = booking
                print(f"Car {plate_license} at {datetime.strftime(expecting_time,"%Y-%m-%d %H:%M:%S")} Booking successful")
                return [True, f"Car {plate_license} Booking successful, please check in before {datetime.strftime(expecting_time,"%Y-%m-%d %H:%M:%S")}!"]
        else:
            return [False, f"No more parking lots available in {lot_id}"]
        
    def cancel_booking(self, plate_license):
        for lot_id, lot in self.parking_lots.items():
            if plate_license in lot.bookings:
                booking = lot.bookings[plate_license]
                booking.cancel()
                del self.parking_lots[lot_id].bookings[plate_license]
                print(f"Car {plate_license} Booking cancelled")
                return [True, f"Car {plate_license} Booking cancelled"]
        return [False, f"Car {plate_license} not found in bookings"]
    
    def check_in(self, lot_id, plate_license, passage):
        if plate_license in self.parking_lots[lot_id].bookings.keys():
            booking = self.parking_lots[lot_id].bookings[plate_license]
            if booking.is_expired(self.booking_expire_time):
                print("Booking expired, checking available parking lots")
                del self.parking_lots[lot_id].bookings[plate_license]
                self.check_in(lot_id,plate_license, passage)
            else:
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
                while not passage.timestamp:
                    time.sleep(0.1)  # Ensure the loop doesn't block indefinitely
                booking.enter(passage.timestamp)
                print(f"Booking Car {plate_license} checked in")
                passage.timestamp = None
                del self.parking_lots[lot_id].bookings[plate_license]
                self.parking_lots[lot_id].parkings[plate_license] = booking
                booking.cancel()       
                self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)

        else:
            if self.parking_lots[lot_id].availability():
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
                while not passage.timestamp:
                    time.sleep(2)  # Ensure the loop doesn't block indefinitely
                car = Car(lot_id, plate_license, passage.timestamp)
                print(f"\n\nNew Car {plate_license} checked in\n\n")
                passage.timestamp = None
                self.parking_lots[lot_id].parkings[plate_license] = car
                self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)
            else:
                self.publish(passage.command_topic_gate, GateStatus.CLOSE)
                print("\nno more parking lots available\n")
    
    def check(self, plate_license, method):
        found = False
        for lot_id, lot in self.parking_lots.items():
            if plate_license in lot.parkings.keys():
                found = True
                car = lot.parkings[plate_license]
                break
        if not found:
            return [False, f"Plate license {plate_license} not found in parking records"]
        if car.status == CarStatus.CHECKED:
            return [True, f"Your Car {plate_license} last check still valid, please pay it"]
        if car.status == CarStatus.CHARGED:
            fee = self.hourly_rate * math.ceil((datetime.now() - car.start_time).total_seconds()/3600)
            car.check(fee, method, datetime.now())
            return [True, f"Car {plate_license} checked, please pay {fee} euros in {math.ceil(self.check_pay_interval/60)} minutes"]   
        elif (datetime.now() - car.start_time).total_seconds() > self.free_stop:
            car.status = CarStatus.CHARGED
            return self.check(plate_license, method)
        else:
            msg = "Very short period after entering or last payment, No payment needed"
            print(msg)
            return [False, msg]
        
    def pay(self, plate_license):
        for lot_id, lot in self.parking_lots.items():
            if plate_license in lot.parkings:
                car = lot.parkings[plate_license]
                break
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
        for lot_id, lot in self.parking_lots.items():
            if plate_license in lot.parkings:
                car = lot.parkings[plate_license]
                break
        car.paid()
        return [True, f"Car {plate_license} paid, please exit within {math.ceil(self.free_stop/60)} minutes"]
                
    def check_out(self, lot_id, plate_license, passage):
        if plate_license in self.parking_lots[lot_id].parkings.keys():
            car = self.parking_lots[lot_id].parkings[plate_license]  
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
                    del self.parking_lots[lot_id].parkings[plate_license]
                    self.publish(passage.command_topic_scanner, ScannerStatus.STANDBY)
                else: 
                    self.publish(passage.command_topic_gate, GateStatus.CLOSE)
                    print(f"{car.plate_license} stayed more than {math.ceil(self.free_stop/60)} minutes after payment/entering, need to pay")
                    car.status = CarStatus.CHARGED                    
            else:
                self.publish(passage.command_topic_gate, GateStatus.OPEN)
        
    def connect_device(self, lot_id, passage):
        self.parking_lots[lot_id].passages[passage.id] = passage
        self.client.subscribe(passage.info_topic_scanner)
        self.client.subscribe(passage.info_topic_gate)
    
    def disconnect_device(self, passage_id):
        found = False
        for lot in self.parking_lots.values():
            if passage_id in lot.passages.keys():
                passage = lot.passages[passage_id]
                self.parking_lots[lot.id].remove_passage(passage_id)
                self.client.unsubscribe(passage.info_topic_scanner)
                self.client.unsubscribe(passage.info_topic_gate)
                gate_id = passage.gate_id
                scanner_id = passage.scanner_id
                print(f"Disconnected passage {passage_id} with gate {gate_id} and scanner {scanner_id}")
                found = True
                break
        if not found:
            print(f"Passage {passage_id} not found in devices")
    
    def connect_bot(self, bot):
        self.client.subscribe(bot.info_topic)
        self.bot = bot
    
    def availability(self):
        available_lots = {}
        for lot in self.parking_lots.values():
            if lot.availability() > 0:
                available_lots[lot.id] = lot.availability()
        msg =''
        for lot_id, num_lots in available_lots.items():
            msg += f"Parking lot /{lot_id} has {num_lots} free lots\n"
        return [True, msg] if available_lots else [False, "No free parking lots available"]
    
    def publish(self, topic, message):
        self.client.publish(topic, message)
        
    def notify(self, topic, payload):
        def notify_thread():
            try:
                data = json.loads(payload)
                if 'scanner' in topic.split('/')[-2] and topic.split('/')[-3] == 'entrance':
                    plate_license = data
                    lot_id = topic.split('/')[-4]
                    lot = self.parking_lots.get(lot_id)
                    print(f"EntranceScanner {topic.split('/')[-2]} detected plate: {data}")
                    for passage in lot.passages.values():
                        if passage.info_topic_scanner == topic:     
                            self.check_in(lot_id, plate_license, passage) 
                            break              
                            
                elif 'gate' in topic.split('/')[-2] and topic.split('/')[-3] == 'entrance':
                    entry_time = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                    lot_id = topic.split('/')[-4]
                    lot = self.parking_lots.get(lot_id)
                    print(f"EntranceGate {topic.split('/')[-2]} opened at: {data}")
                    for passage in lot.passages.values():
                        if passage.info_topic_gate == topic:     
                            passage.timestamp = entry_time              
                            break
                
                elif 'scanner' in topic.split('/')[-2] and topic.split('/')[-3] == 'exit':
                    plate_license = data
                    lot_id = topic.split('/')[-4]
                    lot = self.parking_lots.get(lot_id)
                    print(f"ExitScanner {topic.split('/')[-2]} detected plate: {data}")
                    for passage in lot.passages.values():
                        if passage.info_topic_scanner == topic:     
                            self.check_out(lot_id, plate_license, passage) 
                            break              
                            
                elif 'gate' in topic.split('/')[-2] and topic.split('/')[-3] == 'exit':
                    exit_time = datetime.strptime(data, "%Y-%m-%d %H:%M:%S")
                    lot_id = topic.split('/')[-4]
                    lot = self.parking_lots.get(lot_id)
                    print(f"ExitGate {topic.split('/')[-2]} opened at: {data}")
                    for passage in lot.passages.values():
                        if passage.info_topic_gate == topic:     
                            passage.timestamp = exit_time              
                            break       
                elif topic == self.bot.info_topic:            
                    print(f'Received message: "{data}" from topic: "{self.bot.info_topic}"')
                    if data['action'] == '/book':
                        plate_license = data['plate_license']
                        parking_lot_id = data['parking_lot_id']
                        chat_id = data['chat_id']
                        expecting_time = datetime.strptime(data['expecting_time'], "%Y-%m-%d %H:%M:%S")
                        result = self.book(parking_lot_id, plate_license, expecting_time)
                        response = [chat_id, result]
                        self.publish(self.bot.command_topic, response)
                    elif data['action'] == '/cancel':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        result = self.cancel_booking(plate_license)
                        response = [chat_id, result]
                        self.client.publish(self.bot.command_topic, response)
                    elif data['action'] == '/availability':
                        chat_id = data['chat_id'] 
                        result = self.availability()
                        response = [chat_id, result]
                        self.client.publish(self.bot.command_topic, response)  
                    elif data['action'] == '/pay_check':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        result = self.check(plate_license, 'online')
                        response = [chat_id, result]
                        self.client.publish(self.bot.command_topic, response)
                    elif data['action'] == '/pay_pay':
                        plate_license = data['plate_license']
                        chat_id = data['chat_id']
                        message = self.pay(plate_license)
                        response = [chat_id, message]
                        self.client.publish(self.bot.command_topic, response)
                        
                        # Simulate payment processing time
                        # In a real-world scenario, you would waiting for the payment gateway response
                        process = 3
                        message = [chat_id, [True, "lets assume the link is valid and you are processing the payment via it..."]]
                        self.client.publish(self.bot.command_topic, message)
                        while process > 0:
                            message = [chat_id, [True, f"Payment processing... {process} seconds remaining"]]
                            self.client.publish(self.bot.command_topic, message)
                            time.sleep(1)
                            process -= 1
                        message = self.paid(plate_license)
                        response = [chat_id, message]
                        self.client.publish(self.bot.command_topic, response)
            except Exception as e:
                print("Error in notify_thread:", e)
        threading.Thread(target=notify_thread).start()
                
    def run(self):
        start = datetime.now()
        while True:
            time.sleep(2)
            now = datetime.now()
            for lot in self.parking_lots.values():
                for car in lot.parkings.values():
                    if car.status == CarStatus.CHECKED:
                        if (now - car.payment.time).total_seconds() > self.check_pay_interval:
                            car.failPay()
                if (now - start).total_seconds() > self.book_filter_interval:
                    for booking in lot.bookings.values():
                        if booking.is_expired(self.booking_expire_time):
                            del lot.bookings[booking.plate_license]
                    start = now
       
    def listening_catalog(self):
        def listening_thread():
            time.sleep(5)
            self.load_config()
            while True:
                try:
                    res1 = requests.get(self.URL_PASSAGE)
                    if res1 and res1.ok:
                        data = res1.json()
                        if data[0]:
                            parking_lot_id, id, scanner_id, info_topic_scanner, command_topic_scanner, gate_id, info_topic_gate, command_topic_gate = data[1]
                            passage = Passage(parking_lot_id, id, scanner_id, info_topic_scanner, command_topic_scanner, gate_id, info_topic_gate, command_topic_gate)
                            self.connect_device(parking_lot_id, passage)
                            print(f"New passage {id} connected with gate {gate_id} and scanner {scanner_id} ")
                        else:
                            passage_id = data[1]
                            self.disconnect_device(passage_id)
                            print(f"Passage {passage_id} disconnected")
                    res2 = requests.get(f"{self.URL}/addbot")
                    if res2 and res2.ok:
                        data = res2.json()
                        if data[0]:
                            id, info_topic, command_topic = data[1]
                            bot = Bot(id, info_topic, command_topic)
                            self.connect_bot(bot)
                            print(f"New bot {id} connected")
                        else:
                            bot_id = data[1][0]
                            if self.bot and self.bot.id == bot_id:
                                self.client.unsubscribe(self.bot.info_topic)
                                self.bot = None
                                print(f"Bot {bot_id} disconnected")
                    res3 = requests.get(self.URL_LOT)
                    if res3 and res3.ok:
                        data = res3.json()
                        if data[0]:
                            id, num_lots = data[1]
                            self.parking_lots[id] = Lot(id, num_lots)
                            print(f"Parking lot {id} added with {num_lots} lots")
                        else:
                            lot_id = data[1]
                            if lot_id in self.parking_lots.keys():
                                del self.parkings[lot_id]
                                print(f"Parking lot {lot_id} deleted")
                except Exception:
                    pass
                time.sleep(3)
                # if data[0]:
                #     parking_lot_id, id, scanner_id, info_topic_scanner, command_topic_scanner, gate_id, info_topic_gate, command_topic_gate = data[1]
                #     passage = Passage(parking_lot_id, id, scanner_id, info_topic_scanner, command_topic_scanner, gate_id, info_topic_gate, command_topic_gate)
                #     self.connect_device(passage)
                #     print(f"New passage {id} connected with gate {gate_id} and scanner {scanner_id} ")
                # else:
                #     passage_id = data[1]
                #     self.disconnect_device(passage_id)
                #     print(f"Passage {passage_id} disconnected")
                
        threading.Thread(target=listening_thread).start()
       
       
if __name__ == '__main__': 
    from config_loader import ConfigLoader
    config_loader = ConfigLoader()
    host_RESTful = config_loader.RESTful.host
    port_RESTFUL = config_loader.RESTful.port
    URL = f"http://{host_RESTful}:{port_RESTFUL}"
    parking = Parking(URL)
    parking.run()


