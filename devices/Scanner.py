import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ParkingMQTT import ParkingMQTT as client
from src.TimeControl import TimeControl
import time
import json
from src.utils import ScannerStatus as Status
import threading
import requests

class Scanner():
        
    def __init__(self, URL):
        self.time_control = TimeControl()
        self.URL = URL
        self.URL_DEVICE = ''
        # continuously try to connect to the server until successful for 60 seconds
        print('connecting to server...')
        timer1 = self.time_control.add_timer(60)
        data = None
        while not timer1.timeout:
            try:
                res = requests.post(self.URL, json = 'newscanner')
                if res and res.ok:
                    data = res.json()
                    print('initializing scanner')
                    break
            except Exception as e:
                pass
            time.sleep(1)
        if timer1.timeout:
            print("Failed to connect to the server for a long time.")
            return
    
        # if successful, get the broker information and initialize the client
        URL_UPDATE, broker, port, client_id, parking_lot_id, info_topic, command_topic = data
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.status = Status.STANDBY
        self.URL_UPDATE = URL_UPDATE
        self.payload = {
            "client_id": client_id,
            "parking_lot_id": parking_lot_id,
            "info_topic_scanner": info_topic,
            "command_topic_scanner": command_topic
        }
        try:
            res = requests.post(self.URL_UPDATE, json = self.payload) 
        except Exception as e:
            print("Catalog connection failed:", e)
        self.notice_interval = 120  # seconds 
        print('scanner initialized')

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}\n")
    
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
        def keep_alive():
            while True:
                time.sleep(self.notice_interval)
                try:
                    res = requests.post(self.URL_UPDATE, json = self.payload) 
                    print("[Sensor] Data sent:", res.text)
                except Exception as e:
                    print("[Sensor] POST failed:", e)      
        threading.Thread(target=keep_alive).start()
        