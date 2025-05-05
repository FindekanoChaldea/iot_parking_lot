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

class Gate():
        
    def __init__(self, client_id, broker, port, info_topic, command_topic):
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.status = Status.CLOSE
        self.lock = Lock()

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}")
    
    def open_close(self):
        time.sleep(0.5)  # Simulate gate opening time
    
    def notify(self, topic, payload): 
        with self.lock:
            payload = json.loads(payload)
            if payload == Status.OPEN:
                self.status = Status.OPEN
                self.open_close()  # Simulate gate open time and assume the car went through
                self.status = Status.CLOSE
                self.publish(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            elif payload == Status.CLOSE:
                return
            else :
                Exception ("Unknown command received")
                
    
        