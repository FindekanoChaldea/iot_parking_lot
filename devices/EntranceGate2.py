from Gate import Gate
import  time
from src.config_loader import ConfigLoader


config_loader = ConfigLoader()
host = config_loader.CHERRYPY.host
port = config_loader.CHERRYPY.port
URL = f"http://{host}:{port}"
entranceGate2 = Gate(URL)
entranceGate2.run()