from Scanner import Scanner
import time
import threading
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.CHERRYPY.host
port = config_loader.CHERRYPY.port
URL = f"http://{host}:{port}"
exitScanner1 = Scanner(URL)
threading.Thread(target=exitScanner1.run).start()
time.sleep(2)  # Allow some time for the scanner to initialize
while True: 
    time.sleep(2)
    c = input("Press Enter to scan a plate or type 'q' to quit: \n")
    if c.lower() == 'q':
        break
    c = c.strip().upper()  # Ensure no leading/trailing spaces
    exitScanner1.scan_plate(c)
        