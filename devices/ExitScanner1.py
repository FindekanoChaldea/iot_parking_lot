from Scanner import Scanner
import  time
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.RESTful.host
port = config_loader.RESTful.port
URL = f"http://{host}:{port}"
exitScanner1 = Scanner(URL)
exitScanner1.run()

while True:
    c = input("Press Enter to scan a plate or type 'q' to quit: \n")
    if c.lower() == 'q':
        break
    exitScanner1.scan_plate(c)
    time.sleep(1)  # Simulate a delay between scans
        