from utils import FileManager
import os
import json
import requests
from config_loader import ConfigLoader
import threading
import time


class Device: 
    def __init__(self, id, parking_lot_id, info_topic, command_topic):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.info_topic = info_topic
        self.command_topic = command_topic
        self.paired = False  # Indicates if the device is paired within a passage
    
    def to_dict(self):
        return {
            "client_id": self.id,
            "parking_lot_id": self.parking_lot_id,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
        }

class TollMachine:
    def __init__(self, id, info_topic, command_topic):
        self.id = id
        self.info_topic = info_topic
        self.command_topic = command_topic
        
    def to_dict(self):
        return {
            "client_id": self.id,
            "info_topic": self.info_topic,
            "command_topic": self.command_topic,
        }
        
class Passage:
    def __init__(self, id, scanner, gate, parking_lot_id):
        self.id = id
        self.parking_lot_id = parking_lot_id
        self.scanner = scanner
        self.gate = gate
        
    def save(self, path):
        if os.path.exists(path):
            with open(path, "r") as f:
                data = json.load(f)
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
        with open(self.PATH, "w") as f:
            json.dump(data, f, indent=2)
    def info(self):
        return [self.parking_lot_id, self.id,
                self.scanner.id,self.scanner.info_topic, self.scanner.command_topic,
                self.gate.id, self.gate.info_topic, self.gate.command_topic]
        
class Catalog:
 
    def __init__(self, URL, broker, port, path):
        
        self.broker = broker
        self.port = port
        self.fileManager = FileManager()
        self.PATH = self.fileManager.abpath(path)
        
        self.devices = {}
        self.passages = {}
        self.toll_machines = {}
        self.bot = None

        self.URL = URL
        self.URL_INTERFACE = f"{self.URL}/interface"
        self.URL_CATALOG = f"{self.URL}/catalog"
        self.URL_DEVICE = f"{self.URL}/newdevice"
        self.listen_catalog()
        self.listen_devices()
        self.check_devices()

    def add_parking_lot(self, id):
        if id in self.devices.keys():
            raise ValueError(f"Parking lot {id} already exists.")
        self.devices[id] = {}
        self.passages[id] = {}
        
    def add_device(self, id, parking_lot_id, in_out, type):
        if parking_lot_id not in self.devices:
            msg = [False, f"Parking lot {parking_lot_id} does not exist"]
            requests.post(self.URL_INTERFACE, msg)
            return
        if id in self.devices[parking_lot_id]:
            msg = [False, f"{in_out} {type} {id} already exists in parking lot {parking_lot_id}."]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Create a new device
        info_topic= f"parking/{parking_lot_id}/{in_out}/{id}/info",
        command_topic = f"parking/{parking_lot_id}/{in_out}/{id}/command",
        device = Device(id, parking_lot_id, info_topic, command_topic)
        self.devices[parking_lot_id][id] = device
        msg1 =  [True, f"New {in_out} {type} {id} added to parking lot {parking_lot_id}."]
        requests.post(self.URL_INTERFACE, msg1)
        # Send the device information to the device
        msg2 = [self.broker, self.port, id, parking_lot_id, info_topic, command_topic]
        requests.post(self.URL_DEVICE, json=msg2)

    def pair(self, scanner_id, gate_id, passage_id, parking_lot_id):
        # Check if the parking lot exists
        if parking_lot_id not in self.devices:
            msg = [False, f"Parking lot {parking_lot_id} does not exist"]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Check if the scanner and gate exist and are not already paired
        if scanner_id not in self.devices[parking_lot_id] or gate_id not in self.devices[parking_lot_id]:
            msg = [False, f"Scanner {scanner_id} or gate {gate_id} does not exist in parking lot {parking_lot_id}."]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Check if the scanner and gate are already paired
        elif self.devices[parking_lot_id][scanner_id].paired or self.devices[parking_lot_id][gate_id].paired:
            msg = [False, f"Scanner {scanner_id} or gate {gate_id} is already configured."]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Check if the passage already exists
        if passage_id in self.passages[parking_lot_id]:
            msg = f"Passage {passage_id} already exists in parking lot {parking_lot_id}."
            requests.post(self.URL_INTERFACE, msg)
            return
        # Create the passage with the scanner and gate
        scanner = self.devices[parking_lot_id][scanner_id]
        gate = self.devices[parking_lot_id][gate_id]
        passage = Passage(passage_id, scanner, gate, parking_lot_id)
        scanner.paired = True
        gate.paired = True
        self.passages[parking_lot_id][passage_id] = passage
        passage.save(self.PATH)
        msg1 = f"New passage {passage_id} created with scanner {scanner_id} and gate {gate_id} in parking lot {parking_lot_id}."
        requests.post(self.URL_INTERFACE, msg1)
        msg2 = [True, passage.info()]
        URL_PASSAGE = f"{self.URL}/newpassage"
        requests.post(URL_PASSAGE, json=msg2)
    
    def unpair(self, passage_id, parking_lot_id):
        # Check if the parking lot exists
        if parking_lot_id not in self.passages:
            msg = [False, f"Parking lot {parking_lot_id} does not exist"]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Check if the passage exists
        if passage_id not in self.passages[parking_lot_id]:
            msg = [False, f"Passage {passage_id} does not exist in parking lot {parking_lot_id}."]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Unpair the scanner and gate from the passage
        passage = self.passages[parking_lot_id][passage_id]
        passage.scanner.paired = False
        passage.gate.paired = False
        del self.passages[parking_lot_id][passage_id]
        passage.save(self.PATH)
        msg1 = [True, f"Devices for passage {passage_id} unpaired successfully from parking lot {parking_lot_id}, you can shot down the devices."]
        requests.post(self.URL_INTERFACE, msg1)
        msg2 = [False, passage.info()]
        URL_PASSAGE = f"{self.URL}/newpassage"
        requests.post(URL_PASSAGE, json=msg2)
    
    def connect_bot(self, id):
        # Check if the is already a bot
        if self.bot:
            msg = [False, f"Telegram bot already exists."]
            requests.post(self.URL_INTERFACE, msg)
            return
        # Create a new bot
        info_topic = f"parking/{id}/info"
        command_topic = f"parking/{id}/command"
        self.bot = [id, info_topic, command_topic]
        msg1 =  [True, f"New bot {id} added."]
        requests.post(self.URL_INTERFACE, msg1)
        # Send the bot information to the device
        msg2 = [self.broker, self.port, id, info_topic, command_topic]
        URL_TOLL = f"{self.URL}/newbot"
        requests.post(URL_TOLL, json=msg2)
    
    def load_device(self):
        data = self.fileManager.read_json(self.PATH)
        show = ''
        for lot_id, devices in data.items():
            show += f"Parking Lot ID: {lot_id}\n"
            for device_id, device in devices.items():
                show += f"  Device ID: {device_id}    Info_topic: {device.info_topic}    Command_topic: {device.command_topic}\n"
        msg = show
        requests.post(self.URL_INTERFACE, msg)
    
    def load_passage(self):
        data = self.fileManager.read_json(self.PATH)
        show = ''
        for lot_id, passages in data.items():
            show += f"Parking Lot ID: {lot_id}\n"
            for passage_id, passage in passages.items():
                show += f"    Passage ID: {passage_id}\n"
                show += f"        Device ID: {passage.scanner.id}    Info_topic: {passage.scanner.info_topic}    Command_topic: {passage.scanner.command_topic}\n"
                show += f"        Device ID: {passage.gate.id}    Info_topic: {passage.gate.info_topic}    Command_topic: {passage.gate.command_topic}\n"
        msg = show
        requests.post(self.URL_INTERFACE, msg)
    
    # Continuously listen for commands from the RESTful interface
    # If a new device or passage is added, call the appropriate method to handle it
    # If a device is paired or unpaired, call the appropriate method to handle it
    # This is a background thread that runs indefinitely
    def listen_catalog(self):
        def listening_thread():
            # Continuously listen for new devices or passages
            while True:
                try:
                    res = requests.get(self.URL_CATALOG)
                    if res and res.ok:
                        data = res.json()
                        if data[0] == 'device':
                            self.load_device()
                        elif data[0] == 'passage':
                            self.load_passage()
                        elif data[0] == 'parking_lot':
                            parking_lot_id = data[1]
                            self.add_parking_lot(parking_lot_id)
                        elif (data[0] == 'entrance_gate' or data[0] == 'exit_gate' 
                            or data[0] == 'entrance_scanner' or data[0] == 'exit_scanner'):
                            in_out, type = data[0].split('_')
                            _, id, parking_lot_id = data
                            self.add_device(id, parking_lot_id, in_out, type)
                        elif data[0] == 'pair':
                            _, scanner_id, gate_id, passage_id, parking_lot_id = data
                            self.pair(scanner_id, gate_id, passage_id, parking_lot_id) 
                        elif data[0] == 'unpair':
                            _, passage_id, parking_lot_id = data
                            self.unpair(passage_id, parking_lot_id)
                        elif data[0] == 'bot':
                            _, id = data
                            self.connect_bot(id)
                except Exception:
                    pass   
                time.sleep(1)
        threading.Thread(target=listening_thread).start()


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
                                    URL = f"{self.URL}/{device.parking_lot_id}/{device.id}"
                                    res = requests.get(URL)
                                    if res and res.ok:
                                        data = res.json()
                                        id, info_topic, command_topic = data
                                        if device.id != id or device.info_topic != info_topic or device.command_topic != command_topic:
                                            # Update the device information if it has changed
                                            warning += (
                                                f"Device {device.id} in {device.parking_lot_id} configuration was changed,\n"
                                                f"from\n"
                                                f"    ID: {device.id}, Info Topic: {device.info_topic}, Command Topic: {device.command_topic}\n"
                                                f"to\n"
                                                f"    ID: {id}, Info Topic: {info_topic}, Command Topic: {command_topic}\n"
                                                f"Please check the device configuration.\n"
                                            )
                                        else:
                                            status += (
                                                f"Device {device.id} in {device.parking_lot_id} is active.\n"
                                            )
                                    else:
                                        now = time.time()
                                        if now - start > 300:  # If the device has not responded for 5 minutes
                                            warning += (
                                                f"Device {device.id} in {device.parking_lot_id} is not responding for 5 miniutes.\n"
                                                f"Please check the device.\n"
                                            )
                                            issue = True  
                        print(status + warning)
                        if issue:
                            break    
                    except Exception:
                        pass   
                    time.sleep(30)
        threading.Thread(target=listening_thread).start()
   
    # Check devices every 5 minutes to see if they are still paired
    # If a device is not paired, remove it from the catalog
    # This is a background thread that runs indefinitely     
    def check_devices(self):
        def check_thread():
            while True:
                time.sleep(300)  # Check every 5 minutes
                for lot in self.devices.values():
                    for device in lot.values():
                        if not device.paired:
                            self.devices[device.parking_lot_id].pop(device.id, None)
        threading.Thread(target=check_thread).start()
                    
        
    # def add_entranceScanner(self, id, parking_lot_id):
    #     if parking_lot_id not in self.devices:
    #         msg = [False, f"Parking lot {parking_lot_id} does not exist"]
    #         requests.post(self.URL_INTERFACE, msg)
    #         return
    #     if id in self.devices[parking_lot_id]:
    #         msg = [False, f"Entrance scanner {id} already exists in parking lot {parking_lot_id}."]
    #         requests.post(self.URL_INTERFACE, msg)
    #         return
    #     # Create a new entrance scanner device
    #     info_topic_scanner = f"parking/{parking_lot_id}/entrance/{id}/info",
    #     command_topic_scanner = f"parking/{parking_lot_id}/entrance/{id}/command",
    #     entrance_scanner = Device(id, parking_lot_id, info_topic_scanner, command_topic_scanner)
    #     self.devices[parking_lot_id][id] = entrance_scanner
    #     msg1 = [True, f"New entrance scanner {id} added to parking lot {parking_lot_id}."]
    #     requests.post(self.URL_INTERFACE, msg1)
    #     # Send the device information to the device
    #     msg2 = [id, parking_lot_id, info_topic_scanner, command_topic_scanner]
    #     requests.post(self.URL_DEVICE, json=msg2)
        
    # def add_exitGate(self, id, parking_lot_id):
        # if parking_lot_id not in self.devices:
        #     msg = [False, f"Parking lot {parking_lot_id} does not exist"]
        #     requests.post(self.URL_INTERFACE, msg)
        #     return
        # if id in self.devices[parking_lot_id]:
        #     msg = [False, f"Exit gate {id} already exists in parking lot {parking_lot_id}."]
        #     requests.post(self.URL_INTERFACE, msg)
        #     return
        # # Create a new exit gate device
        # info_topic_gate = f"parking/{parking_lot_id}/eixt/{id}/info",
        # command_topic_gate = f"parking/{parking_lot_id}/eixt/{id}/command",
        # exit_gate = Device(id, parking_lot_id, info_topic_gate, command_topic_gate)
        # self.devices[parking_lot_id][id] = exit_gate
        # msg1 = [True, f"New exit gate {id} added to parking lot {parking_lot_id}."]
        # requests.post(self.URL_INTERFACE, msg1)
        # # Send the device information to the device
        # msg2 = [id, parking_lot_id, info_topic_gate, command_topic_gate]
        # URL_APPEND = f"{self.URL}/newGate"
        # requests.post(self.URL_DEVICE, json=msg2)
              
    # def add_exitScanner(self, id, parking_lot_id):
    #     if parking_lot_id not in self.devices:
    #         msg = [False, f"Parking lot {parking_lot_id} does not exist"]
    #         requests.post(self.URL_INTERFACE, msg)
    #         return
    #     if id in self.devices[parking_lot_id]:
    #         msg = [False, f"Exit scanner {id} already exists in parking lot {parking_lot_id}."]
    #         requests.post(self.URL_INTERFACE, msg)
    #         return
    #     # Create a new exit scanner device
    #     info_topic_scanner = f"parking/{parking_lot_id}/eixt/{id}/info",
    #     command_topic_scanner = f"parking/{parking_lot_id}/eixt/{id}/command",
    #     exit_scanner = Device(id, parking_lot_id, info_topic_scanner, command_topic_scanner)
    #     self.devices[parking_lot_id][id] = exit_scanner
    #     msg1 = [True, f"New exit scanner {id} added to parking lot {parking_lot_id}."]
    #     requests.post(self.URL_INTERFACE, msg1)
    #     # Send the device information to the device
    #     msg2 = [id, parking_lot_id, info_topic_scanner, command_topic_scanner]
    #     requests.post(self.URL_DEVICE, json=msg2)     

if __name__ == "__main__":
    ConfigLoader = ConfigLoader()
    host = ConfigLoader.RESTFUL.host
    port_RESTFUL = ConfigLoader.RESTFUL.port
    URL = f"http://{host}:{port_RESTFUL}"
    path = 'config/devices.json'
    broker = ConfigLoader.MQTT.broker
    port_MQTT = ConfigLoader.MQTT.port
    catalog = Catalog(URL, broker, port_MQTT, path)
    