import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ParkingMQTT import ParkingMQTT as client
from src.bin.TimeControl import TimeControl
import time
import json
from src.utils import ScannerStatus as Status
import threading
import requests

class Scanner():
        
    def __init__(self, URL):
        self.time_control = TimeControl()
        self.URL = URL
        self.notice_interval = None
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
        if data and data[0]:
            URL_UPDATE = data[1]['URL_UPDATE']
            broker = data[1]['broker']
            port = data[1]['port']
            client_id = data[1]['id']
            parking_lot_id = data[1]['parking_lot_id']
            info_topic = data[1]['info_topic']
            command_topic = data[1]['command_topic']
            notice_interval = data[1]['notice_interval']
        self.client = client(client_id, broker, port, self)
        self.client.start()
        print(f'scanner {client_id} initialized')
        time.sleep(1)
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.status = Status.STANDBY
        self.URL_UPDATE = URL_UPDATE
        self.payload = {
            "id": client_id,
            "parking_lot_id": parking_lot_id,
            "info_topic": info_topic,
            "command_topic": command_topic
        }
        try:
            res = requests.post(self.URL_UPDATE, json = self.payload) 
        except Exception as e:
            print("Catalog connection failed:", e)
        self.notice_interval = notice_interval  # seconds 

    def publish(self, message):
        self.client.publish(self.topic, message)
    
    def scan_plate(self, plate_license):
        if self.status == Status.SCANNED:
            print("Please wait the previous car to pass.")
        else:
            self.publish(plate_license)
            self.status = Status.SCANNED
    
    def notify(self, topic, payload):
        payload = json.loads(payload)
        if payload == Status.STANDBY:
            self.status = Status.STANDBY 
    
    def run(self):
        while True:
            if self.notice_interval:
                time.sleep(self.notice_interval)
                try:
                    res = requests.post(self.URL_UPDATE, json = self.payload) 
                    print("[Scanner] Status updated")
                except Exception as e:
                    print("[Scanner] Status POST failed:", e)    
            else:
                time.sleep(5)
        