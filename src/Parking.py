#This code is for MQTT subscription and publishment.
import ParkingMQTT as client
import src.Car as Car
import time
from datetime import datetime
import json
from utils import FileManager, CarStatus, ScannerStatus, GateStatus

class Parking():
    def __init__(self, client):
        self.client = client
        self.num_lots = 100
        self.bookings = {}
        self.parkings = {}
        self.pub_topics = []
        self.sub_topics = []
        self.client.start()

    def book(self, plate_license):
        if len(self.parkings) + len(self.bookings) < 100:
            booking = Car(plate_license, expecting_time = datetime.now())
            booking.save('../data/bookings.json')
            self.bookings[plate_license] = booking
        else:
            print("no more parking lots available")
    
    def check_in(self):
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

    def add_subscribe(self, entrance_scanner, entrance_gate, exit_scanner, exit_gate):
        self.client.subscribe(entrance_scanner)
        self.client.subscribe(entrance_gate)
        self.client.subscribe(exit_scanner)
        self.client.subscribe(exit_gate)
        self.entrance_scanner_sub = entrance_scanner
        self.entrance_gate_sub = entrance_gate
        self.exit_scanner_sub = exit_scanner
        self.exit_gate_sub = exit_gate
            
    def add_publish(self, entrance_scanner, entrance_gate, exit_scanner, exit_gate):
        self.entrance_scanner_pub = entrance_scanner
        self.entrance_gate_pub = entrance_gate
        self.exit_scanner_pub = exit_scanner
        self.exit_gate_pub = exit_gate
    
    def publish(self, topic, message):
        self.client.publish(topic, message)
        print(f"Published message: {message} to topic: {self.topic}") 
        
    def notify(self, topic, payload):
        payload = json.loads(payload)
        if topic == self.entrance_scanner_sub:
            self.plate_license = payload
        elif topic == self.entrance_gate_sub:
            self.entry_time = datetime.strptime(payload, "%Y-%m-%d %H:%M:%S")
            
    def run(self):
        while True:
            if self.plate_license:
                self.check_in()
            time.sleep(0.1)