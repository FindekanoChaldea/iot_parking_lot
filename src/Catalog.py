from utils import FileManager
import os
import json
import requests
from config_loader import ConfigLoader
import threading
import time
import math
import cherrypy
from utils import TimeControl

class Device: 
    def __init__(self, id, parking_lot_id, info_topic, command_topic, URL_UPDATE):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.info_topic = info_topic
        self.command_topic = command_topic
        self.URL_UPDATE = URL_UPDATE
        self.paired = False  # Indicates if the device is paired within a passage
        self.passage = None  # Reference to the passage if paired
        self.inactive = None  # Last active time of the device, used to check if the device is inactive
    def mark(self, time):
        self.inactive = time  # Record the last active time of the device
    def to_dict(self):
        return {
            "client_id": self.id,
            "parking_lot_id": self.parking_lot_id,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
            "URL_UPDATE": self.URL_UPDATE,
        }
        
class Passage:
    def __init__(self, id, scanner, gate, parking_lot_id):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.scanner = scanner
        self.scanner.paired = True
        self.scanner.passage = self
        self.gate = gate
        self.gate.paired = True
        self.gate.passage = self
        
    def unpair(self):
        self.scanner.paired = False
        self.scanner.passage = None
        self.gate.paired = False
        self.gate.passage = None
        
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
        return {
            "parking_lot_id": self.parking_lot_id,
            "id": self.id,
            "scanner_id": self.scanner.id,
            "info_topic_scanner": self.scanner.info_topic,
            "command_topic_scanner": self.scanner.command_topic,
            "gate_id": self.gate.id,
            "info_topic_gate": self.gate.info_topic,
            "command_topic_gate": self.gate.command_topic
        }
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
    def __init__(self, id, token, info_topic, command_topic, URL_UPDATE):
        self.id = id
        self.token = token
        self.info_topic = info_topic
        self.command_topic = command_topic
        self.URL_UPDATE = URL_UPDATE
        self.inactive = None  # Last active time of the bot, used to check if the bot is inactive
    def mark(self, time):
        self.inactive = time  # Record the last active time of the device 
    def info(self):
        return {
            "id": self.id,
            "token": self.token,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
            "URL_UPDATE": self.URL_UPDATE
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
        data[self.id] = self.info()
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
        def __init__(self, catalog, dict):
            self.parking_id = dict["parking_id"]
            self.broker = dict["broker"]
            self.port = dict["port"]
            self.catalog_uri = dict["catalog_uri"]
            self.passage_uri = dict["passage_uri"]
            self.lot_uri = dict["lot_uri"]
            self.free_stop = dict["free_stop"]
            self.check_pay_interval = dict["check_pay_interval"]
            self.booking_expire_time = dict["booking_expire_time"]
            self.hourly_rate = dict["hourly_rate"]
            self.book_filter_interval = dict["book_filter_interval"]
            self.payment_filter_interval = dict["payment_filter_interval"]
            self.device_inactive_limit = dict["device_inactive_limit"]
            self.book_start_time = dict["book_start_time"]
            self.time_out = dict["time_out"]
            self.notice_interval = dict["notice_interval"]
            self.URL_CATALOG = f"{catalog.URL}{self.catalog_uri}"
            self.URL_PASSAGE = f"{catalog.URL}{self.passage_uri}"
            self.URL_LOT = f"{catalog.URL}{self.lot_uri}"
            
        def parking_properties(self):
            return {
                "parking_id": self.parking_id,
                "broker": self.broker,
                "port": self.port,
                "URL_CATALOG": self.URL_CATALOG,
                "URL_PASSAGE": self.URL_PASSAGE,
                "URL_LOT": self.URL_LOT,
                "free_stop": self.free_stop,
                "check_pay_interval": self.check_pay_interval,
                "booking_expire_time": self.booking_expire_time,
                "hourly_rate": self.hourly_rate,
                "book_filter_interval": self.book_filter_interval,
                "payment_filter_interval": self.payment_filter_interval,
            }
    exposed = True 
    def __init__(self, URL, path):
        # utilities
        self.fileManager = FileManager()
        self.time_control = TimeControl()
        self.PATH = self.fileManager.abpath(path)
        self.parking_config = None
        
        # CHERRYPY
        self.last_post = {}
        # check if the device is initiating and the command is confirmed
        self.connecting_device = None
        # URLs
        self.URL = URL

        self.parking_lots = {}
        self.devices = {}
        self.passages = {}
        self.bot = None
        
        
    def load_config(self, dict):
        try:
            self.parking_config = self.ParkingConfig(self,dict)
            self.listen_devices()
            self.listen_bot()
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
        msg2 = [True, {"id": id, "num": num}]
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
            msg2 = [True, {
                "URL_UPDATE": URL,
                "broker": self.parking_config.broker,
                "port": self.parking_config.port,
                "id": id,
                "parking_lot_id": parking_lot_id,
                "info_topic": info_topic,
                "command_topic": command_topic,
                "notice_interval": self.parking_config.notice_interval
            }]
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
            msg2 = [False, {"message": "Please remove the existing bot first."}]
        else:
            # Create a new bot
            info_topic = f"parking/{id}/info"
            command_topic = f"parking/{id}/command"
            URL = f"{self.URL}/{id}"
            self.bot = Bot(id, token, info_topic, command_topic, URL)
            if self.activate_bot():
                self.bot.save(self.PATH)
                msg1 =  [True, f"New bot {id} added."]
                # Send the bot information to the device
                msg2 = [True, {
                    "token": token,
                    "URL_UPDATE": URL,
                    "broker": self.parking_config.broker,
                    "port": self.parking_config.port,
                    "id": id,
                    "info_topic": info_topic,
                    "command_topic": command_topic,
                    "book_start_time": self.parking_config.book_start_time,
                    "time_out": self.parking_config.time_out,
                    "notice_interval": self.parking_config.notice_interval
                }]
            else:
                msg1 = [False, f"Failed to connect the Control Center."]
                msg2 = [False, {"message": "Please try again."}]
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
        msg = [True, {
            "id": self.bot.id,
            "info_topic": self.bot.info_topic,
            "command_topic": self.bot.command_topic,
            "URL_UPDATE": self.bot.URL_UPDATE
        }]
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
            if self.bot:
                show += f"Telegram Bot ID: {self.bot.id}    Info_topic: {self.bot.info_topic}    Command_topic: {self.bot.command_topic}\n"
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
    # If a device does not respond for device_inactive_limit, warn and disconnect it
    # This is a background thread that runs indefinitely
    def listen_devices(self):
        def listening_thread():
            # Continuously listen for new devices or passages
            while True:
                time.sleep(3)
                try:
                    warning = ''
                    status = ''
                    now = time.time()
                    to_delete = []
                    # Check all devices in the catalog
                    for lot in self.devices.values():
                        for device in lot.values():
                            URL = device.URL_UPDATE
                            res = requests.get(URL)
                            if res and res.ok:
                                data = res.json()
                                id = data.get("id")
                                parking_lot_id = data.get("parking_lot_id")
                                info_topic = data.get("info_topic")
                                command_topic = data.get("command_topic")
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
                                device.inactive = None  # Reset the inactive time
                            else:
                                if not device.inactive:
                                    device.mark(now)  # Mark the device as inactive
                                elif now - device.inactive > self.parking_config.device_inactive_limit:  # If the device has not responded for within given minutes
                                    if device.paired:
                                        self.unpair(device.passage.id, device.parking_lot_id)
                                    warning += (
                                        f"Device {device.id} in {device.parking_lot_id} is not responding for {math.ceil(self.parking_config.device_inactive_limit/60)} miniutes.\n"
                                        f"Device is deleted from Catalog.\n"
                                    )
                                    to_delete.append((device.id, device.parking_lot_id))
                    for (device_id, parking_lot_id) in to_delete:
                        self.delete_device(device_id, parking_lot_id)
                    print(f"{status}\n{warning}")  
                except Exception as e:
                    print(e)
        threading.Thread(target=listening_thread).start()
        
    def listen_bot(self):
        def listening_thread():
            # Continuously listen for new devices or passages
            while True:
                time.sleep(3)
                try:
                    warning = ''
                    status = ''
                    now = time.time()
                    if self.bot:
                        resbot = requests.get(self.bot.URL_UPDATE)
                        if resbot and resbot.ok:
                            data = resbot.json()
                            id = data.get("id")
                            token = data.get('token')
                            info_topic = data.get("info_topic")
                            command_topic = data.get("command_topic")
                            if self.bot.id != id or self.bot.token != token or self.bot.info_topic != info_topic or self.bot.command_topic != command_topic:
                                # Update the bot information if it has changed
                                warning += (
                                    f"Bot {self.bot.id} configuration was changed,\n"
                                    f"from\n"
                                    f"    ID: {self.bot.id}, Token: {self.bot.token}, Info Topic: {self.bot.info_topic}, Command Topic: {self.bot.command_topic}\n"
                                    f"to\n"
                                    f"    ID: {id}, Token: {token}, Info Topic: {info_topic}, Command Topic: {command_topic}\n"
                                    f"Please check the bot configuration.\n"
                                )
                            else:
                                status += (
                                    f"Bot {self.bot.id} is active.\n"
                                )
                            self.bot.inactive = None  # Reset the inactive time
                        else:
                            if not self.bot.inactive:
                                self.bot.mark(now)  # Mark the device as inactive
                            elif now - self.bot.inactive > self.parking_config.device_inactive_limit:
                                warning += (
                                    f"Bot {self.bot.id} is not responding for {math.ceil(self.parking_config.device_inactive_limit/60)} miniutes.\n"
                                    f"Bot is deleted from Catalog.\n"
                                )
                                self.delete_bot()
                    print(f"{status}\n{warning}")  
                except Exception as e:
                    print(e)
        threading.Thread(target=listening_thread).start()
   

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
                if data.get('action', None) == 'config':
                    data.pop('config', None) 
                    return self.load_config(data)
                
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
                    return l
            
        elif uri[0] == 'catalog':
            if not self.parking_config:
                return [False, "Please load configuration first"]
            else:
                action = data.get('action')
                if action == 'device':
                    return self.load_device()
                elif action == 'passage':
                    return self.load_passage()
                elif action == 'parking_lot':
                    parking_lot_id = data.get('parking_lot_id')
                    num = data.get('num')
                    return self.add_parking_lot(parking_lot_id, num)
                elif action == 'pair':
                    scanner_id = data.get('scanner_id')
                    gate_id = data.get('gate_id')
                    passage_id = data.get('passage_id')
                    parking_lot_id = data.get('parking_lot_id')
                    return self.pair(scanner_id, gate_id, passage_id, parking_lot_id)
                elif action == 'unpair':
                    passage_id = data.get('passage_id')
                    parking_lot_id = data.get('parking_lot_id')
                    return self.unpair(passage_id, parking_lot_id)
                elif action in ('entrance_gate', 'exit_gate', 'entrance_scanner', 'exit_scanner'):
                    in_out, type = action.split('_')
                    id = data.get('id')
                    parking_lot_id = data.get('parking_lot_id')
                    if not self.connecting_device:
                        return [False, "No device is initiating, please intiate the device first."]
                    else:
                        self.connecting_device.connect_device(id, parking_lot_id, in_out, type)
                    return self.connecting_device.interface_msg
                elif action == 'delete_device':
                    id = data.get('id')
                    parking_lot_id = data.get('parking_lot_id')
                    return self.delete_device(id, parking_lot_id)
                elif action == 'bot':
                    id = data.get('id')
                    token = data.get('token')
                    if not self.connecting_device:
                        return [False,"No device is initiating, please intiate the device first."]
                    self.connecting_device.connect_bot(id, token)
                    return self.connecting_device.interface_msg
                elif action == 'delete_bot':
                    return self.delete_bot()
                else:
                    cherrypy.response.status = 400
                    return "Invalid request"   
                
        else:
            self.last_post[uri] = data
            return [True, "Data send successfully"]               

if __name__ == "__main__":
    
    config_loader = ConfigLoader()
    host_CHERRYPY = config_loader.CHERRYPY.host
    port_CHERRYPY = config_loader.CHERRYPY.port
    broker_MQTT = config_loader.MQTT.broker
    port_MQTT = config_loader.MQTT.port
    URL = f"http://{host_CHERRYPY}:{port_CHERRYPY}"
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
    cherrypy.server.socket_host = host_CHERRYPY
    cherrypy.server.socket_port = port_CHERRYPY
    cherrypy.tree.mount(catalog, '/', config)
    cherrypy.engine.start()
    cherrypy.engine.block()

    