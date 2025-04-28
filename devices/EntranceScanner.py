from src import ParkingMQTT as client
import time
import random
import os
import json
from src.utils import ScannerStatus as Status

class EntranceScanner():
        
    def __init__(self, client_id, broker, port, pub_topic, sub_topic):
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = pub_topic
        self.client.subscribe(sub_topic)
        self.status = Status.STANDBY

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}")
    
    def scan_plate(self, plate_license):
        while self.status == Status.SCANNED:
            time.sleep(0.2)  # Wait for the scanner to be ready
            pass
        self.plate_license = plate_license
        self.status = Status.SCANNED
    
    def notify(self, topic, payload): 
        payload = json.loads(payload)
        if payload == Status.STANDBY:
            self.status = Status.STANDBY
                
    def run(self):
        while True:
            if self.status == Status.SCANNED:
                self.publish(self.plate_license)
            time.sleep(0.2)
        
if __name__ == "__main__":
    client_id = 'EntranceScanner'
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    pub_topic = 'polito_parking/entrance/scanner/plate'
    sub_topic = 'polito_parking/entrance/scanner/command'
    entranceScanner = EntranceScanner(client_id, broker, port, pub_topic, sub_topic)
    entranceScanner.run()
    # Simulate with fake data in teast/fake_cars.json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'fake_cars.json')
    cars = []
    with open(path, 'r') as file:
        cars = json.load(file)
    for car in cars:
        entranceScanner.scan_plate(car)
        time.sleep(random.randint(3, 10))  # Simulate random time intervals
        