import os
import  json
import  time
import random
from Scanner import Scanner

        
client_id = 'EntranceScanner1'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/scanner1/info'
sub_topic = 'polito_parking/entrance/scanner1/command'
entranceScanner1 = Scanner(client_id, broker, port, pub_topic, sub_topic)


# Simulate with fake data in teast/fake_cars.json
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'fake_cars_1.json')
cars = []
with open(path, 'r') as file:
    cars = json.load(file)
for car in cars:
    entranceScanner1.scan_plate(car)
    time.sleep(random.randint(5, 10))  # Simulate random time intervals
        