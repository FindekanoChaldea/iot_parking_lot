from Scanner import Scanner
import  time
import threading
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.RESTful.host
port = config_loader.RESTful.port
URL = f"http://{host}:{port}"
entranceScanner1 = Scanner(URL)
threading.Thread(target=entranceScanner1.run).start()
while True:
    c = input("Press Enter to scan a plate or type 'q' to quit: \n")
    if c.lower() == 'q':
        break
    entranceScanner1.scan_plate(c)
    time.sleep(1)  # Simulate a delay between scans
    
        