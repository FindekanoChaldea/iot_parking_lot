#This code is for MQTT subscription and publishment.
import ParkingMQTT as client
import src.Car as Car
import time
from datetime import datetime
import json
from utils import FileManager, CarStatus, ScannerStatus, GateStatus

class Parking():
    
    def __init__(self, client_id, broker, port):
        self.client = client(client_id, broker, port, self)
        self.num_lots = 100
        self.bookings = {}
        self.parkings = {}
        self.devices = {}
        self.temp = {}
        # self.pub_topics = []
        # self.sub_topics = []
        self.client.start()

    def book(self, plate_license):
        if len(self.parkings) + len(self.bookings) < 100:
            booking = Car(plate_license, expecting_time = datetime.now())
            booking.save('../data/bookings.json')
            self.bookings[plate_license] = booking
        else:
            print("no more parking lots available")
    
    def check_in(self, device):
        if self.plate_license in self.bookings.keys():
            booking = self.bookings[self.plate_license]
            if booking.is_expired():
                print("Booking expired")
                return
            else:
                self.publich(self.entrance_gate_pub, GateStatus.OPEN)
                while True:
                    if self.entry_time:
                        booking.enter(self.entry_time)
                        break
                del self.bookings[self.plate_license]
                self.parkings[self.plate_license] = booking
                booking.status = CarStatus.CHECKED
            fileManager = FileManager()
            fileManager.find_and_delete('../data/bookings.json', self.plate_license)
            self.plate_license = None
            self.entry_time = None
            self.publich(self.entrance_scanner_pub, ScannerStatus.STANDBY)
            print("Booking checked in")
        else:
            if len(self.parkings) + len(self.bookings) < 100:
                self.publich(self.entrance_gate_pub, GateStatus.OPEN)
                while True:
                    if self.entry_time:
                        car = Car(self.plate_license, self.entry_time)
                        break
                self.parkings[self.plate_license] = car
            else:
                print("no more parking lots available")
                return
            self.plate_license = None
            self.entry_time = None
            self.publich(self.entrance_scanner_pub, ScannerStatus.STANDBY)  
            print("New car checked in")    
                     
    # def check_out(self):
    #     if self.plate_license in self.parkings.keys():
    #         car = self.parkings[self.plate_license]
    #         while True:
    #             if self.exit_time:
    #                 car.exit(self.exit_time)
    #                 break
    #         if car.status == CarStatus.EXITED:
    #             del self.parkings[self.plate_license]
    #             fileManager = FileManager()
    #             fileManager.find_and_delete('../data/parkings.json', self.plate_license)
    #             print("Car checked out")
    #         else:
    #             print("need to pay before exit")
    #     else:
    #         print("Car not found in parking")
    class Device:
        def __init__(self, id, gate_id, pub_topic_gate, sub_topic_gate, pub_topic_scanner, sub_topic_scanner, scanner_id):
            self.id = id
            self.gate_id = gate_id
            self.pub_topic_gate = pub_topic_gate
            self.sub_topic_gate = sub_topic_gate
            self.scanner_id = scanner_id
            self.pub_topic_scanner = pub_topic_scanner
            self.sub_topic_scanner = sub_topic_scanner
    
    def connect(self, device):
        self.client.subscribe(device.pub_topic_scanner)
        self.client.subscribe(device.pub_topic_gate)
        self.devices[device.id] = device
 
               
    # def add_subscribe(self, entrance_scanner, entrance_gate, exit_scanner, exit_gate):
    #     self.client.subscribe(entrance_scanner)
    #     self.client.subscribe(entrance_gate)
    #     self.client.subscribe(exit_scanner)
    #     self.client.subscribe(exit_gate)
    #     self.entrance_scanner_sub = entrance_scanner
    #     self.entrance_gate_sub = entrance_gate
    #     self.exit_scanner_sub = exit_scanner
    #     self.exit_gate_sub = exit_gate
            
    # def add_publish(self, entrance_scanner, entrance_gate, exit_scanner, exit_gate):
    #     self.entrance_scanner_pub = entrance_scanner
    #     self.entrance_gate_pub = entrance_gate
    #     self.exit_scanner_pub = exit_scanner
    #     self.exit_gate_pub = exit_gate
    
    def publish(self, topic, message):
        self.client.publish(topic, message)
        print(f"Published message: {message} to topic: {self.topic}") 
        
    def notify(self, topic, payload):
        payload = json.loads(payload)
        if topic.split('/')[-2] == 'scanner':
            plate_license = payload
            self.temp[topic] = plate_license
            for device in self.devices.values:
                if device.pub_topic_scanner == topic:
                    
                    self.plate_license = plate_license
                    self.entrance_scanner_pub = device.pub_topic_scanner
                    self.entrance_gate_pub = device.pub_topic_gate
                    break
        elif topic.split('/')[-2] == 'gate':
            self.entry_time = datetime.strptime(payload, "%Y-%m-%d %H:%M:%S")
            
    def run(self):
        while True:
            if self.plate_license:
                self.check_in()
            time.sleep(0.1)
