from Gate import Gate
import  time
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.RESTful.host
port = config_loader.RESTful.port
URL = f"http://{host}:{port}"
entranceGate1 = Gate(URL)
while True: 
    time.sleep(1)