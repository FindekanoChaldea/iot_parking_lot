import ParkingMQTT as client
from src.bin import EntranceDevice
import time
import random
import os
import json

class EntranceConnector():

    def __init__(self, EntranceDevice, client_id, broker, port, pub_topic, sub_topic):
        self.client = client(client_id, broker, port)
        self.EntranceDevice = EntranceDevice
        self.client.start()
        self.topic = pub_topic
        self.client.subscribe(sub_topic)

    def publish(self, message):
        self.client.publish(self.topic, message)
        # print(f"Published message: {message} to topic: {self.topic}")
        
    def run(self):
        if self.EntranceDevice.get_status() == EntranceDevice.Status.CHECKING:
            message = EntranceDevice.plate_license
            self.publish(message)
    
if __name__ == "__main__":
    entranceDevice = EntranceDevice()
    client_id = 'EntranceDevice'
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    pub_topic = 'polito_parking/entrance'
    sub_topic = 'polito_parking/entrance/response'
    entranceConnector = EntranceConnector(entranceDevice, client_id, broker, port, pub_topic, sub_topic)
    # Simulate with fake data in teast/fake_cars.json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'fake_cars.json')
    cars = []
    with open(path, 'r') as file:
        cars = json.load(file)
    for car in cars:
        plate_license = entranceDevice.scan_plate(car)
        time.sleep(random.randint(1, 10))  # Simulate random time intervals
        