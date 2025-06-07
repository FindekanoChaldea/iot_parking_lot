from utils import FileManager
import os
import json
import requests
from config_loader import ConfigLoader
import threading
import time
import math
import cherrypy
from TimeControl import TimeControl

class Device: 
    def __init__(self, id, parking_lot_id, info_topic, command_topic, URL):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.info_topic = info_topic
        self.command_topic = command_topic
        self.URL = URL
        self.paired = False  # Indicates if the device is paired within a passage

    def to_dict(self):
        return {
            "client_id": self.id,
            "parking_lot_id": self.parking_lot_id,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
        }
        
class Passage:
    def __init__(self, id, scanner, gate, parking_lot_id):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.scanner = scanner
        self.scanner.paired = True
        self.gate = gate
        self.gate.paired = True
        
    def unpair(self):
        self.scanner.paired = False
        self.gate.paired = False
        
    def save(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}
        lot_id = self.parking_lot_id
        id = self.id
        # Ensure the parking lot key exists
        if lot_id not in data:
            data[lot_id] = {}
        # Save the device under its parking lot
        data[lot_id][id] = {
            "scanner": self.scanner.to_dict(),
            "gate": self.gate.to_dict(),
        }
        # Write back to file
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    def info(self):
        return [self.parking_lot_id, self.id,
                self.scanner.id,self.scanner.info_topic, self.scanner.command_topic,
                self.gate.id, self.gate.info_topic, self.gate.command_topic]  
    def delete(self, path):
        # find the passage in the file and delete it
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            lot_id = self.parking_lot_id
            id = self.id
            # Check if the parking lot exists
            if lot_id in data and id in data[lot_id]:
                del data[lot_id][id]
                # Write back to file
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                return True
            else:
                return False
     
class Bot:
    def __init__(self, id, token, info_topic, command_topic):
        self.id = id
        self.token = token
        self.info_topic = info_topic
        self.command_topic = command_topic
    def info(self):
        return [self.id, self.token, self.info_topic, self.command_topic]  
    def to_dict(self):
        return {
            "id": self.id,
            "token": self.token,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
        }   
    def save(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = {}
        else:
            data = {}
        # Save the bot under its ID
        data[self.id] = self.to_dict()
        # Write back to file
        with open(path, "w") as f:
            json.dump(data, f, indent=2)
    def delete(self, path): 
        # find the bot in the file and delete it
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
            # Check if the bot exists
            if self.id in data:
                del data[self.id]
                # Write back to file
                with open(path, "w") as f:
                    json.dump(data, f, indent=2)
                return True
            else:
                return False
        
class Catalog:
    
    class ParkingConfig:
        def __init__(self, catalog, list):
            [
            # parking properties
            self.parking_id,
            self.broker,
            self.port,
            self.catalog_uri,
            self.passage_uri,
            self.lot_uri,
            self.free_stop,
            self.check_pay_interval,
            self.booking_expire_time,
            self.hourly_rate,
            self.book_filter_interval,
            self.payment_filter_interval,
            # catalog
            self.device_inactive_limit,
            
            #devices
            self.book_start_time,
            self.time_out,
            self.notice_interval
            ] =list
            self.URL_CATALOG = f"{catalog.URL}{self.catalog_uri}"
            self.URL_PASSAGE = f"{catalog.URL}{self.passage_uri}"
            self.URL_LOT = f"{catalog.URL}{self.lot_uri}"
            
        def parking_properties(self):
            return [
                self.parking_id,
                self.broker,
                self.port,
                self.URL_CATALOG,
                self.URL_PASSAGE,
                self.URL_LOT,
                
                self.free_stop,
                self.check_pay_interval,        
                self.booking_expire_time,
                self.hourly_rate,
                self.book_filter_interval,
                self.payment_filter_interval,
            ]
    exposed = True 
    def __init__(self, URL, path):
        # utilities
        self.fileManager = FileManager()
        self.time_control = TimeControl()
        self.PATH = self.fileManager.abpath(path)
        self.parking_config = None
        
        # RESTful
        self.last_post = {}
        # check if the device is initiating and the command is confirmed
        self.connecting_device = None
        # URLs
        self.URL = URL

        self.parking_lots = {}
        self.devices = {}
        self.passages = {}
        self.bot = None
        
        
    def load_config(self, list):
        try:
            self.parking_config = self.ParkingConfig(self,list)
            self.listen_devices()
            return [True, "configuration loaded"]
        except Exception as e:
            return[False, f"Failed to load configuration: {e}"]
    
    def get_response(self, url, action, timeout, post = None):
        timer = self.time_control.add_timer(timeout)
        data = None
        while not timer.timeout:
            try:
                if action == 'POST':
                    res = requests.post(url, json = post)
                    if res and res.ok:
                        data = res.json()
                        break
                    else:
                        time.sleep(0.5)
                else:
                    res = requests.get(url)
                    if res.ok:
                        data = res.json()
                        break
                    else:
                        time.sleep(0.5)
            except requests.exceptions.RequestException as e:
                time.sleep(0.5)
        return timer.timeout, data

    def add_parking_lot(self, id, num):
        msg1 = []
        if id in self.parking_lots.keys():
            msg1 = [False, f"Parking lot {id} updated."]
        else:
            msg1 = [True, f"Parking lot {id} added successfully."]
        self.parking_lots[id] = num
        self.devices[id] = {}
        self.passages[id] = {}
        msg2 = [True, [id, num]]
        timeout, _ = self.get_response(self.parking_config.URL_LOT, 'POST', 5, msg2)
        if timeout:
            return [False, f"Failed to connect to the ControlCenter..."]
        # Save the parking lot to the file
        print(f"Parking lot {id} added successfully.")
        return msg1
        
    class ConnectingDevice:
        class Type:
            SCANNER = 'scanner'
            GATE = 'gate'
            BOT = 'bot'
        def __init__(self, catalog):
            self.type = None
            self.catalog = catalog
            self.device_initiating = False
            self.device_msg = None
            self.interface_msg = None
            self.refer = ""
        def connect_device(self, id, parking_lot_id, in_out, type):
            if self.type != type:
                self.interface_msg = [False, f"Dectected {self.type} waiting to be intialized, not {type}, please try again."]
                return
            self.interface_msg, self.device_msg = self.catalog.add_device(id, parking_lot_id, in_out, type)
            self.refer = f"{in_out} {type} {id}"
        def connect_bot(self, id, token):
            if self.type != self.Type.BOT:
                self.interface_msg = [False, f"Dectected {self.type} waiting to be intialized, not {self.Type.BOT}, please try again."]
                return
            self.interface_msg, self.device_msg = self.catalog.connect_bot(id, token)
            self.refer = f"bot {id}"
    
    def add_device(self, id, parking_lot_id, in_out, type):
        msg1 = []
        msg2 = []
        if parking_lot_id not in self.devices:
            msg1 = [False, f"Parking lot {parking_lot_id} does not exist"]
        elif id in self.devices[parking_lot_id]:
            msg1 = [False, f"{in_out} {type} {id} already exists in parking lot {parking_lot_id}."]
        # Create a new device
        else:
            info_topic= f"parking/{parking_lot_id}/{in_out}/{id}/info"
            command_topic = f"parking/{parking_lot_id}/{in_out}/{id}/command"
            URL = f"{self.URL}/{parking_lot_id}/{in_out}/{type}/{id}"
            device = Device(id, parking_lot_id, info_topic, command_topic, URL)
            msg1 =  [True, f"New {in_out} {type} {id} added to parking lot {parking_lot_id}."]
            # Send the device information to the device
            msg2 = [URL, self.parking_config.broker, self.parking_config.port, id, parking_lot_id, info_topic, command_topic, self.parking_config.notice_interval ]
            # Add the device to the catalog 
            self.devices[parking_lot_id][id] = device
            print(f"New {in_out} {type} {id} added to parking lot {parking_lot_id}.")
        return msg1, msg2

    def delete_device(self, id, parking_lot_id):
        msg1 = []
        # Check if the parking lot exists
        if parking_lot_id not in self.devices.keys():
            msg1 = [False, f"Parking lot {parking_lot_id} does not exist"]
        # Check if the device exists
        elif id not in self.devices[parking_lot_id].keys():
            msg1 = [False, f"Device {id} does not exist in parking lot {parking_lot_id}."]
        # Delete the device from the catalog
        elif self.devices[parking_lot_id][id].paired:
            msg1 = [False, f"Device {id} is paired with a passage in parking lot {parking_lot_id}, please unpair it first."]
        else:
            del self.devices[parking_lot_id][id]
            msg1 = [True, f"Device {id} deleted successfully from parking lot {parking_lot_id}."]
            print(f"Device {id} deleted successfully from parking lot {parking_lot_id}.")
        return msg1

    def pair(self, scanner_id, gate_id, passage_id, parking_lot_id):
        # Check if the parking lot exists
        msg1 = []
        if parking_lot_id not in self.devices.keys():
            msg1 = [False, f"Parking lot {parking_lot_id} does not exist"]
        # Check if the scanner and gate exist and are not already paired
        elif scanner_id not in self.devices[parking_lot_id].keys() or gate_id not in self.devices[parking_lot_id].keys():
            msg1 = [False, f"Scanner {scanner_id} or gate {gate_id} does not exist in parking lot {parking_lot_id}."]
        # Check if the scanner and gate are already paired
        elif self.devices[parking_lot_id][scanner_id].paired or self.devices[parking_lot_id][gate_id].paired:
            msg1 = [False, f"Scanner {scanner_id} or gate {gate_id} is already configured."]
        # Check if the passage already exists
        elif passage_id in self.passages[parking_lot_id].keys():
            msg1 = [False, f"Passage {passage_id} already exists in parking lot {parking_lot_id}..."]
        # Create the passage with the scanner and gate
        else:
            scanner = self.devices[parking_lot_id][scanner_id]
            gate = self.devices[parking_lot_id][gate_id]
            passage = Passage(passage_id, scanner, gate, parking_lot_id)
            self.passages[parking_lot_id][passage_id] = passage
            msg1 = [True, f"New passage {passage_id} created with scanner {scanner_id} and gate {gate_id} in parking lot {parking_lot_id}."]
            msg2 = [True, passage.info()]
            timeout, _ = self.get_response(self.parking_config.URL_PASSAGE, 'POST', 5, msg2)
            if timeout:
                return[False, f"Failed to connect to the ControlCenter..."]
            print(f"New passage {passage_id} created with scanner {scanner_id} and gate {gate_id} in parking lot {parking_lot_id}.")
            passage.save(self.PATH)
        return msg1
    
    def unpair(self, passage_id, parking_lot_id):
        msg1 = []
        # Check if the parking lot exists
        if parking_lot_id not in self.passages.keys():
            msg1 = [False, f"Parking lot {parking_lot_id} does not exist"]
        # Check if the passage exists
        if passage_id not in self.passages[parking_lot_id].keys():
            msg1 = [False, f"Passage {passage_id} does not exist in parking lot {parking_lot_id}."]
        # Unpair the scanner and gate from the passage
        else:
            passage = self.passages[parking_lot_id][passage_id]
            passage.unpair()
            passage.delete(self.PATH)
            del self.passages[parking_lot_id][passage_id]
            msg1 = [True, f"Devices for passage {passage_id} unpaired successfully from parking lot {parking_lot_id}, you can shot down the devices."]
            msg2 = [False, passage.info()]
            timeout, _ = self.get_response(self.parking_config.URL_PASSAGE, 'POST', 5, msg2)
            if timeout:
                print(f"Failed to connect to the ControlCenter.")
                return[False, f"Failed to connect to the ControlCenter..."]
            print(f"Devices for passage {passage_id} unpaired successfully from parking lot {parking_lot_id}, you can shot down the devices.")
        return msg1
    
    def connect_bot(self, id, token):
        msg1 = []
        msg2 = []
        # Check if the is already a bot
        if self.bot:
            msg1 = [False, f"Telegram bot already exists."]
            msg2 = [False, "Please remove the existing bot first."]
        else:
            # Create a new bot
            info_topic = f"parking/{id}/info"
            command_topic = f"parking/{id}/command"
            URL = f"{self.URL}/{id}"
            self.bot = Bot(id, token, info_topic, command_topic)
            if self.activate_bot():
                self.bot.save(self.PATH)
                msg1 =  [True, f"New bot {id} added."]
                # Send the bot information to the device
                msg2 = [True, [token, URL, self.parking_config.broker, self.parking_config.port, id, info_topic, command_topic, self.parking_config.book_start_time, self.parking_config.time_out, self.parking_config.notice_interval]]
            else:
                msg1 = [False, f"Failed to connect the Control Center."]
                msg2 = [False, "Please try again."]
        return msg1 , msg2
    
    def delete_bot(self):
        msg1 = []
        # Check if the bot exists
        if not self.bot:
            msg1 = [False, f"Telegram bot does not exist."]
        else:
            # Delete the bot from the catalog
            bot = self.bot
            self.bot.delete(self.PATH)
            self.bot = None
            msg1 = [True, f"Telegram bot deleted successfully."]
            msg2 = [False, bot.info()]
            timeout, _ = self.get_response(f"{self.URL}/addbot", 'POST', 5, msg2)
            if timeout:
                print(f"Failed to connect to the ControlCenter.")
                return [False, f"Failed to connect to the ControlCenter."]
            print(f"Telegram bot deleted successfully.")
        return msg1
    
    def activate_bot(self):
        msg = [True, [self.bot.id, self.bot.info_topic, self.bot.command_topic]]
        timeout, _ = self.get_response(F"{self.URL}/addbot", 'POST', 5, msg)
        if timeout:
            return False
        else:
            return True
    
    def load_device(self):
        data = self.devices
        msg = None
        if not data:
            msg = [False, "No devices found."]
        else:
            # Format the data for display
            show = ''
            for lot_id, devices in data.items():
                show += f"Parking Lot ID: {lot_id} {self.parking_lots[lot_id]} spots\n"
                for device_id, device in devices.items():
                    show += f"  Device ID: {device_id}    Info_topic: {device.info_topic}    Command_topic: {device.command_topic}\n"
            msg = [True, show]
        return msg
        
    def load_passage(self):
        data = self.passages
        msg = None
        if not data:
            msg = [False, "No passages found in the catalog."]
        else:
            show = ''
            for lot_id, passages in data.items():
                show += f"Parking Lot ID: {lot_id} {self.parking_lots[lot_id]}spots\n"
                for passage_id, passage in passages.items():
                    show += f"    Passage ID: {passage_id}\n"
                    show += f"        Device ID: {passage.scanner.id}    Info_topic: {passage.scanner.info_topic}    Command_topic: {passage.scanner.command_topic}\n"
                    show += f"        Device ID: {passage.gate.id}    Info_topic: {passage.gate.info_topic}    Command_topic: {passage.gate.command_topic}\n"
            msg = [True, show]
        return msg
    
    # Continuously listen for changes in device configurations
    # If a device configuration changes unexpectly, raise a warning
    # If a device does not respond for 5 minutes, mark it as not responding
    # This is a background thread that runs indefinitely
    def listen_devices(self):
        def listening_thread():
            # Continuously listen for new devices or passages
            while True:
                start = time.time()
                while True:
                    try:
                        warning = ''
                        status = ''
                        issue = False
                        for lot in self.passages.values():
                            for passage in lot.values():
                                for device in [passage.scanner, passage.gate]:
                                    URL = device.URL_UPDATE
                                    res = requests.get(URL)
                                    if res and res.ok:
                                        data = res.json()
                                        id, parking_lot_id, info_topic, command_topic = data
                                        if device.id != id or device.parking_lot_id != parking_lot_id or device.info_topic != info_topic or device.command_topic != command_topic:
                                            # Update the device information if it has changed
                                            warning += (
                                                f"Device {device.id} in {device.parking_lot_id} configuration was changed,\n"
                                                f"from\n"
                                                f"    ID: {device.id}, Patking lot: {device.parking_lot_id}, Info Topic: {device.info_topic}, Command Topic: {device.command_topic}\n"
                                                f"to\n"
                                                f"    ID: {id}, Patking lot: {parking_lot_id}, Info Topic: {info_topic}, Command Topic: {command_topic}\n"
                                                f"Please check the device configuration.\n"
                                            )
                                        else:
                                            status += (
                                                f"Device {device.id} in {device.parking_lot_id} is active.\n"
                                            )
                                    else:
                                        now = time.time()
                                        if now - start > self.parking_config.device_inactive_limit:  # If the device has not responded for within given minutes
                                            if device.paired:
                                                self.unpair(passage.id, device.parking_lot_id)
                                                warning += (
                                                    f"Device {device.id} in {device.parking_lot_id} is not responding for {math.ceil(self.parking_config.device_inactive_limit/60)} miniutes.\n"
                                                    f"Device is deleted from Catalog.\n"
                                                )
                                            else: 
                                                self.delete_device(device.id, device.parking_lot_id)
                                                warning += (
                                                    f"Device {device.id} in {device.parking_lot_id} is not responding for {math.ceil(self.parking_config.device_inactive_limit/60)} miniutes.\n"
                                                    f"All devices from the passage {passage.id} are deleted from Catalog.\n"
                                                )
                        print(status + warning)  
                    except Exception:
                        pass   
                    time.sleep(10)
        threading.Thread(target=listening_thread).start()
   
    # Check devices every 5 minutes to see if they are still paired
    # If a device is not paired, remove it from the catalog
    # This is a background thread that runs indefinitely     
    # def check_devices(self):
    #     def check_thread():
    #         while True:
    #             time.sleep(self.parking_config.unpaired_time_limit)  # Check every 5 minutes
    #             for lot in self.devices.values():
    #                 for device in lot.values():
    #                     if not device.paired:
    #                         print(f"Device {device.id} in parking lot {device.parking_lot_id} is not paired for long time, removing from catalog, initiate it again if needed.")
    #                         self.devices[device.parking_lot_id].pop(device.id, None)
    #     threading.Thread(target=check_thread).start()

    @cherrypy.tools.json_out()
    def GET(self, *uri, **params):
        try:
            return self.last_post.pop(uri)
        except KeyError:
            cherrypy.response.status = 404
            return
        
    @cherrypy.tools.json_out()
    @cherrypy.tools.json_in()
    def POST(self, *uri, **params):
        data = cherrypy.request.json
        if not uri:
            if isinstance(data, dict):
                try:
                    l = data.get('config', None)
                    if l:   
                        return self.load_config(l)
                except Exception as e:
                    return[False, f"Failed to load configuration: {e}"]
                
            elif isinstance(data, str):
                if data.lower() == 'newscanner':
                    self.connecting_device = self.ConnectingDevice(self)
                    self.connecting_device.type = self.connecting_device.Type.SCANNER
                    timer = self.time_control.add_timer(60)
                    while not self.connecting_device.device_msg and not timer.timeout:    
                        time.sleep(0.1)
                    if not timer.timeout:
                        print(f"Configuration sent to {self.connecting_device.refer}.")
                        return self.connecting_device.device_msg
                    else: print("Failed, please try again.")
                elif data.lower() == 'newgate':
                    self.connecting_device = self.ConnectingDevice(self)
                    self.connecting_device.type = self.connecting_device.Type.GATE
                    timer = self.time_control.add_timer(60)
                    while not self.connecting_device.device_msg and not timer.timeout:    
                        time.sleep(0.1)
                    if not timer.timeout:
                        print(f"Configuration sent to {self.connecting_device.refer}.")
                        return self.connecting_device.device_msg
                    else: print("Failed, please try again.")
                elif data.lower() == 'newbot':
                    self.connecting_device = self.ConnectingDevice(self)
                    self.connecting_device.type = self.connecting_device.Type.BOT
                    timer = self.time_control.add_timer(60)
                    while not self.connecting_device.device_msg and not timer.timeout:    
                        time.sleep(0.1)
                    if not timer.timeout:
                        print(f"Configuration sent to {self.connecting_device.refer}.")
                        return self.connecting_device.device_msg
                    else: print("Failed, please try again.")
                elif data.lower() == 'parking_properties':
                    while not self.parking_config:
                        time.sleep(0.5)
                    l = self.parking_config.parking_properties()
                    if l:
                        print("Parking properties loaded to ControlCenter successfully.")
                        return l
            
        elif uri[0] == 'catalog':
            if not self.parking_config:
                if data[0] == 'config':
                    return self.load_config(data[1])
                else: return [False, "Please load configuration first"]
            else:
                if data[0] == 'device':
                    return self.load_device()
                elif data[0] == 'passage':
                    return self.load_passage()
                elif data[0] == 'parking_lot':
                    _, parking_lot_id, num = data
                    return self.add_parking_lot(parking_lot_id, num)
                elif data[0] == 'pair':
                    _, scanner_id, gate_id, passage_id, parking_lot_id = data
                    return self.pair(scanner_id, gate_id, passage_id, parking_lot_id) 
                elif data[0] == 'unpair':
                    _, passage_id, parking_lot_id = data
                    return self.unpair(passage_id, parking_lot_id)
                elif (data[0] == 'entrance_gate' or data[0] == 'exit_gate' 
                    or data[0] == 'entrance_scanner' or data[0] == 'exit_scanner'):
                    in_out, type = data[0].split('_')
                    _, id, parking_lot_id = data
                    if not self.connecting_device:
                        return [False, "No device is initiating, please intiate the device first."]
                    else: self.connecting_device.connect_device(id, parking_lot_id, in_out, type)
                    return self.connecting_device.interface_msg
                elif data[0] == 'delete_device':
                    _, id, parking_lot_id = data
                    return self.delete_device(id, parking_lot_id)
                elif data[0] == 'bot':
                    _, id, token = data
                    if not self.connecting_device:
                        return [False,"No device is initiating, please intiate the device first."]
                    self.connecting_device.connect_bot(id, token)
                    return self.connecting_device.interface_msg
                elif data[0] == 'delete_bot':
                    return self.delete_bot()
                else:
                    cherrypy.response.status = 400
                    return "Invalid request"   
                
        else:
            self.last_post[uri] = data
            return [True, "Data send successfully"]               

if __name__ == "__main__":
    
    config_loader = ConfigLoader()
    host_RESTful = config_loader.RESTful.host
    port_RESTful = config_loader.RESTful.port
    broker_MQTT = config_loader.MQTT.broker
    port_MQTT = config_loader.MQTT.port
    URL = f"http://{host_RESTful}:{port_RESTful}"
    path = 'config/devices.json'
    catalog = Catalog(URL, path)
    
    def handle_error(status, message, traceback, version):
        cherrypy.response.headers['Content-Type'] = 'application/json'
        return json.dumps({'message':message})
    cherrypy.config.update({
        'error_page.default': handle_error
    })
    config = {
		'/': {
			'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
			'tools.sessions.on': True
		}
	}
    # Mount the PaymentService class and start the server
    cherrypy.server.socket_host = config_loader.RESTful.host
    cherrypy.server.socket_port = config_loader.RESTful.port
    cherrypy.tree.mount(catalog, '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()

    