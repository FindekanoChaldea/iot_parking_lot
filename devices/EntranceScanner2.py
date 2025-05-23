import os
import  json
import  time
import random
from Scanner import Scanner

        
client_id = 'EntranceScanner2'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/entrance/scanner2/info'
sub_topic = 'polito_parking/entrance/scanner2/command'
entranceScanner2 = Scanner(client_id, broker, port, pub_topic, sub_topic)
# Simulate with fake data in teast/fake_cars.json
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'fake_cars_2.json')
cars = []
with open(path, 'r') as file:
    cars = json.load(file)
for car in cars:
    entranceScanner2.scan_plate(car)
    time.sleep(random.randint(3, 10))  # Simulate random time intervals
        