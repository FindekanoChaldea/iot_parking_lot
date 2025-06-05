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
        URL_UPDATE, broker, port, client_id, parking_lot_id, info_topic, command_topic, notice_interval = data
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.status = Status.CLOSE
        self.lock = Lock()
        self.URL_UPDATE = URL_UPDATE
        self.payload = {
            "client_id": client_id,
            "parking_lot_id": parking_lot_id,
            "info_topic_gate": info_topic,
            "command_topic_gate": command_topic
        }
        try:
            res = requests.post(self.URL_UPDATE, json = self.payload) 
        except Exception as e:
            print("Catalog connection failed:", e)
        self.notice_interval = notice_interval  # seconds
        print('gate initialized')
        
    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}")
    
    def open_close(self):
        print("Gate is opening...")
        time.sleep(0.5)  # Simulate gate opening time
        print("Gate is closing...")
    
    def notify(self, topic, payload): 
        with self.lock:
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
                Exception ("Unknown command received")
                
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
             
    
        