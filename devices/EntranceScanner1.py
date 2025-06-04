import os
import  json
import  time
import random
from Scanner import Scanner
from src.config_loader import ConfigLoader

        
ConfigLoader = ConfigLoader()
host = ConfigLoader.RESTFUL.host
port = ConfigLoader.RESTFUL.port
URL = f"http://{host}:{port}"
entranceScanner1 = Scanner(URL)


# # Simulate with fake data in teast/fake_cars.json
# path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'fake_cars_1.json')
# cars = []
# with open(path, 'r') as file:
#     cars = json.load(file)
# for car in cars:
#     entranceScanner1.scan_plate(car)
#     time.sleep(random.randint(5, 10))  # Simulate random time intervals
        