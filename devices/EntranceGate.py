from src import ParkingMQTT as client
import time
from datetime import datetime
import json
from threading import Lock
from src.utils import GateStatus as Status

class EntranceGate():
        
    def __init__(self, client_id, broker, port, pub_topic, sub_topic):
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.topic = pub_topic
        self.client.subscribe(sub_topic)
        self.status = Status.CLOSE
        self.lock = Lock()

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}")
        
    def notify(self, topic, payload): 
        with self.lock:
            payload = json.loads(payload)
            if payload == Status.OPEN:
                self.status = Status.OPEN
                time.sleep(0.5)  # Simulate gate open time and assume the car went through
                self.status = Status.CLOSE
                self.publish(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            elif payload == Status.CLOSE:
                return "The parking is either full or fully booked, no reservation found"
            else :
                Exception ("Unknown command received")
        
if __name__ == "__main__":
    client_id = 'EntranceGate'
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    pub_topic = 'polito_parking/entrance/gate/action'
    sub_topic = 'polito_parking/entrance/gate/command'
    entranceGate = EntranceGate(client_id, broker, port, pub_topic, sub_topic)
    while True:
        pass