import sys
import os
# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time 
import requests
import threading
from src.ParkingMQTT import ParkingMQTT as client
from src.TimeControl import TimeControl

class transaction:
    def __init__(self, plate_license, amount, payment_method, time):
        self.plate_license = plate_license
        self.amount = amount
        self.payment_method = payment_method
        self.time = time
        self.status = 'Pending'
        
    def process_payment(self):
        # Simulate payment processing
        time.sleep(2)
        self.status = 'Completed'
        return True    
    
class Toll:
    def __init__(self, URL):
        self.time_control = TimeControl()
        self.URL = URL
        self.URL_TOLL = f"{URL}/newtoll"
        print('initializing Toll Machine...')
        # continuously try to connect to the server until successful for 60 seconds
        print('connecting to server...')
        timer1 = self.time_control.add_timer(60)
        while not timer1.timeout:
            try:
                res = requests.post(self.URL, json = 'newtoll')
                if res and res.ok:
                    print('initializing Toll Machine...')
                    break
            except Exception as e:
                pass
            time.sleep(1)
        if timer1.timeout:
            print("Failed to connect to the server for a long time.")
            return
        # continuously try to get the broker information until successful for 60 seconds
        timer2 = self.time_control.add_timer(60)
        while not timer2.timeout:
            try:
                res = requests.get(self.URL_TOLL)
                if res and res.ok:
                    break
            except Exception:
                pass
            time.sleep(1)
        if timer2.timeout:
            print("Failed to get the broker information for a long time.")
            return
        # if successful, get the broker information and initialize the client
        broker, port, client_id, parking_lot_id, info_topic, command_topic = res.json()
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.URL_UPDATE = f"{URL}/{client_id}"
        self.payload = {
            "client_id": client_id,
            "info_topic_scanner": info_topic,
            "command_topic_scanner": command_topic
        }
        try:
            res = requests.post(self.URL_UPDATE, json = self.payload) 
        except Exception as e:
            print("Catalog connection failed:", e)
        self.notice_interval = 120  # seconds  
        self.transactions = {}
        print('Toll machine initialized')

    def check(self, plate_license):
        
        return self.payment
    
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
    
    def listen(self):
        def listen_thread():
            while True:
                res = requests.get(self.URL_TOLL)
                if res.ok:
                    data = res.json()
                    if data[0]:
                        plate_license, amount, payment_method, time = data[1:]
                        self.process_payment(plate_license, amount, payment_method, time)
                else:
                    time.sleep(0.5)
        threading.Thread(target=listen_thread)
