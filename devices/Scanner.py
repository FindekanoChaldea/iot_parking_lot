from src import ParkingMQTT as client
import time
import random
import os
import json
from src.utils import ScannerStatus as Status

class Scanner():
        
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
            time.sleep(0.1)  # Wait for the scanner to be ready
            pass
        self.publish(plate_license)
        self.status = Status.SCANNED
    
    def notify(self, topic, payload):
        payload = json.loads(payload)
        if payload == Status.STANDBY:
            self.status = Status.STANDBY
    
    def run(self):
        self.client.loop_forever()
        
        