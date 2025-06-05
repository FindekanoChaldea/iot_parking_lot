from Scanner import Scanner
import  time
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.RESTful.host
port = config_loader.RESTful.port
URL = f"http://{host}:{port}"
entranceScanner1 = Scanner(URL)
entranceScanner1.run()

while True:
    c = input("Press Enter to scan a plate or type 'q' to quit: ")
    if c.lower() == 'q':
        break
    entranceScanner1.scan_plate(c)
    time.sleep(1)  # Simulate a delay between scans
        