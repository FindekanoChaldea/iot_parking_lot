import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.ParkingMQTT import ParkingMQTT as client
import time
from datetime import datetime
import json
from threading import Lock
from src.utils import GateStatus as Status
import threading
import requests
from src.TimeControl import TimeControl

class Gate():
        
    def __init__(self, URL):
        self.time_control = TimeControl()
        self.URL = URL
        self.notice_interval = None
        # continuously try to connect to the server until successful for 60 seconds
        print('connecting to server...')
        data = None
        timer1 = self.time_control.add_timer(60)
        while not timer1.timeout:
            try:
                res = requests.post(self.URL, json = 'newgate')
                if res and res.ok:
                    data = res.json()
                    print('initializing gate...')
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
        print(f'gate {client_id} initialized')
        time.sleep(1)
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.status = Status.CLOSE
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
    
    def open_close(self):
        print("Gate is opening...")
        time.sleep(0.5)  # Simulate gate opening time
        print("Gate is closing...")
    
    def notify(self, topic, payload): 
        print(f"[Gate] Received command on topic: {topic} with payload: {payload}")
        payload = json.loads(payload)
        if payload == Status.OPEN:
            self.status = Status.OPEN
            self.open_close()  # Simulate gate open time and assume the car went through
            self.status = Status.CLOSE
            self.publish(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        elif payload == Status.CLOSE:
            if topic.split('/')[-3] == 'exit':
                print(f"\nstayed too long after payment/entering, need to pay\n")
            elif topic.split('/')[-3] == 'entrance':
                print("\nno more parking lots available\n")
        else :
            print ("Unknown command received")
                
    def run(self):
        while True:
            if self.notice_interval:
                time.sleep(self.notice_interval)
                try:
                    res = requests.post(self.URL_UPDATE, json = self.payload) 
                    print("[Gate] Status updated")
                except Exception as e:
                    print("[Gate] Status POST failed:", e)  
            else:
                time.sleep(5)    
             
    
        