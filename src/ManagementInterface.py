import requests
import re
import time
from config_loader import ConfigLoader
from TimeControl import TimeControl

time_control = TimeControl()
ConfigLoader = ConfigLoader()
host_RESTful = ConfigLoader.RESTful.host
port_RESTful = ConfigLoader.RESTful.port
broker_MQTT = ConfigLoader.MQTT.broker
port_MQTT = ConfigLoader.MQTT.port
catalog_uri = ConfigLoader.RESTful.catalog_uri
passage_uri = ConfigLoader.RESTful.passage_uri
lot_uri = ConfigLoader.RESTful.lot_uri

URL = f"http://{host_RESTful}:{port_RESTful}"
URL_CATALOG = f"{URL}{catalog_uri}"
URL_PASSAGE = f"{URL}{passage_uri}"
URL_LOT = f"{URL}{lot_uri}"
token = ConfigLoader.telegram_bot_token

class ParkingConfig:
    def __init__(self):
        self.config = {
            "parking_id": "ParkingSystem",
            "broker": broker_MQTT,
            "port": port_MQTT,
            "catalog_uri": catalog_uri,
            "passage_uri": passage_uri,
            "lot_uri": lot_uri,
            "free_stop": 60,  # seconds
            "check_pay_interval": 60,  # seconds
            "booking_expire_time": 300,  # seconds
            "hourly_rate": 1.50,  # euros
            "book_filter_interval": 600,  # seconds
            "payment_filter_interval": 60,  # seconds
            "device_inactive_limit": 30,  # Check every 30 s
            "book_start_time": 30,
            "time_out": 300,
            "notice_interval": 20
        }
    
    def load_config(self):
        return {
            "parking_id": self.config['parking_id'],
            "broker": self.config['broker'],
            "port": self.config['port'],
            "catalog_uri": self.config['catalog_uri'],
            "passage_uri": self.config['passage_uri'],
            "lot_uri": self.config['lot_uri'],
            "free_stop": self.config['free_stop'],
            "check_pay_interval": self.config['check_pay_interval'],
            "booking_expire_time": self.config['booking_expire_time'],
            "hourly_rate": self.config['hourly_rate'],
            "book_filter_interval": self.config['book_filter_interval'],
            "payment_filter_interval": self.config['payment_filter_interval'],
            "device_inactive_limit": self.config['device_inactive_limit'],
            "book_start_time": self.config['book_start_time'],
            "time_out": self.config['time_out'],
            "notice_interval": self.config['notice_interval']
        }
       
    def show_default(self):
        return (
            f"Default configurations:\n\n"
            f"parking_id: {self.config['parking_id']}, system name\n"
            f"broker: {self.config['broker']}, MQTT broker\n"
            f"port: {self.config['port']}, MQTT port\n"
            f"catalog_uri: {self.config['catalog_uri']}\n"
            f"passage_uri: {self.config['passage_uri']}\n"
            f"config_uri: {self.config['lot_uri']}\n"
            f"free_stop: {self.config['free_stop']} seconds, within which the car will not be charged\n"
            f"check_pay_interval: {self.config['check_pay_interval']} seconds, the time limit between the fee check and finish transaction\n"
            f"booking_expire_time: {self.config['booking_expire_time']} seconds, the time limit of no appearance after the booking time\n"
            f"hourly_rate: {self.config['hourly_rate']} euros, the hourly rate for parking\n"
            f"book_filter_interval: {self.config['book_filter_interval']} seconds, check if there are expired books by interval\n"
            f"payment_filter_interval: {self.config['payment_filter_interval']} seconds, check if there are expired payments by interval\n"
            f"listen_device_info_interval: {self.config['device_inactive_limit']} seconds, check the device status by interval\n"
            f"book_start_time: {self.config['book_start_time']} seconds, available booking time after the operation time\n"
            f"time_out: {self.config['time_out']} seconds, chat expire without interaction\n"
            f"notice_interval: {self.config['notice_interval']} seconds, the devices update their info by interval\n"
        )

def get_response(url, action, timeout, post = None):
    timer = time_control.add_timer(timeout)
    data = None
    while not timer.timeout:
        try:
            if action == 'POST':
                res = requests.post(url, json = post)
                if res.ok:
                    data = res.json()
                    if data is None:
                        continue
                    else: break
                else:
                    time.sleep(0.5)
            else:
                res = requests.get(url)
                if res.ok:
                    data = res.json()
                    if data is None:
                        continue
                    else: break
                else:
                    time.sleep(0.5)
        except requests.exceptions.RequestException as e:
            time.sleep(0.5)
    return timer.timeout, data
    
    
while True:
    
    cmd = input(   
        "Press 'i' to initiate the system configurations\n"   
        "Press 's' to show the list of devices\n"
        "Press 'p' to add a new parking lot\n"
        "Type 'add' to add a new device\n"
        "Type 'delete' to delete a device\n"
        "Type 'addb' to add the telegram bot\n"
        "Type 'deleteb' to delete the bot\n"
        "Type 'pair' to pair a scanner with a gate\n"
        "Type 'unpair' to unpair a passage devices\n"
    ).lower()
    
    if cmd == 'i':
        parking_config = ParkingConfig()
        while True:
            print(f"\nHere are the default configuration:\n"
                  f"Press 'Enter' to continue with default configuration\n")
            qiut = False
            while True:
                c = input(
                    f"{parking_config.show_default()}\n"
                    f"Type the property name to change the configuration, press 'Enter' to load the configuration, Press 'q' to quit\n"
                )
                if c== "":
                    break
                elif c == 'parking_id':
                    new_value = input("Enter the new parking system ID (default: ParkingSystem): ").strip()
                    if new_value:
                        parking_config.config['parking_id'] = new_value
                elif c == 'broker':
                    new_value = input("Enter the new MQTT broker address (default: localhost): ").strip()
                    if new_value:
                        parking_config.config['broker'] = new_value
                elif c == 'port':
                    new_value = input("Enter the new MQTT port (default: 1883): ").strip()
                    if new_value.isdigit():
                        parking_config.config
                elif c == "catalog_uri":
                    new_value = input("Enter the new catalog URI (default: /catalog): ").strip()
                    if new_value:
                        parking_config.config['catalog_uri'] = new_value
                elif c == "passage_uri":
                    new_value = input("Enter the new passage URI (default: /passage): ").strip()
                    if new_value:
                        parking_config.config['passage_uri'] = new_value
                elif c == "lot_uri": 
                    new_value = input("Enter the new config URI (default: /config): ").strip()
                    if new_value:
                        parking_config.config['lot_uri'] = new_value
                elif c == "free_stop":
                    new_value = input("Enter the new free stop time in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.config['free_stop'] = int(new_value)
                elif c == "check_pay_interval":
                    new_value = input("Enter the new check pay interval in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.config['check_pay_interval'] = int(new_value)
                elif c == "booking_expire_time":
                    new_value = input("Enter the new booking expire time in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.config['booking_expire_time'] = int(new_value)
                elif c == "hourly_rate":    
                    new_value = input("Enter the new hourly rate in euros (default: 1.50): ").strip()
                    if new_value.replace('.', '', 1).isdigit():
                        parking_config.config['hourly_rate'] = float(new_value)
                elif c == "book_filter_interval":
                    new_value = input("Enter the new book filter interval in seconds (default: 600): ").strip()
                    if new_value.isdigit():
                        parking_config.config['book_filter_interval'] = int(new_value)
                elif c == "payment_filter_interval":
                    new_value = input("Enter the new payment filter interval in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.config['payment_filter_interval'] = int(new_value)
                elif c == "device_inactive_limit":
                    new_value = input("Enter the new listen device info interval in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.config['device_inactive_limit'] = int(new_value)
                elif c == "book_start_time":
                    new_value = input("Enter the new book start time in seconds (default: 30): ").strip()
                    if new_value.isdigit():
                        parking_config.config['book_start_time'] = int(new_value)
                elif c == "time_out":
                    new_value = input("Enter the new time out in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.config['time_out'] = int(new_value)
                elif c == "notice_interval":
                    new_value = input("Enter the new notice interval in seconds (default: 120): ").strip()
                    if new_value.isdigit():
                        parking_config.config['notice_interval'] = int(new_value)
                elif c == "q":
                    qiut = True
                    break
                else:
                    print("Invalid property name. Please try again.\n")
            if qiut:
                break
            else:
                # Wait for the response from the server, try up to 10 seconds
                payload = parking_config.load_config()
                payload['action'] = 'config'
                timeout, res = get_response(URL, 'POST', 10, post = payload)
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    continue
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
    
    elif cmd == 's':
        c = ''
        quit = False
        while True:
            cmd2 = input(
                "Press 'd' to show the list of all devices\n"
                "Press 'p' to show the devices by passage\n"
                "Press 'q' to quit\n"
            ).lower()
            if cmd2 == 'd':
                c = 'device'
                break
            elif cmd2 == 'p':
                c = 'passage'
                break
            elif cmd2 == 'q':
                quit = True
                break
            else:
                print("Invalid command. Please do again.\n")
        if quit:
            continue
        else: 
            # Wait for the response from the server, try up to 10 seconds
            timeout, res = get_response(URL_CATALOG, 'POST', 10, post = {"action": c})
            if timeout:
                print("No response from the server. Please check the server status.\n")
                continue
            print(f"{res[1]}\n")
        
    elif cmd == 'p':
        c = 'parking_lot'
        while True:
            parking_lot_id = input("Enter the ID of the parking lot, or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            parking_lot_id = f"lot_{parking_lot_id}"
            num = input("Enter the number of parking spaces in the parking lot, or 'q' to quit: ").lower()
            if num == 'q':
                break
            
            #wait for the response from the server, try up to 10 seconds
            timeout, res = get_response(URL_CATALOG, 'POST', 10, post = {"action": c, "parking_lot_id": parking_lot_id, "num": num})
            if timeout:
                print("No response from the server. Please check the server status.\n")
                break
            elif res[0]:
                print(f"{res[1]}\n")
                break
            else:
                print(f"{res[1]}\n")
    
    elif cmd == 'add':
        c = ''   
        type = ''
        in_out = ''
        quit = False
        while True:
            cmd2 = input(
                "Press 'ins' to add an entrance scanner \n"
                "Press 'ing' to add an entrance gate \n"
                "Press 'outs' to add an exit scanner \n"
                "Press 'outg' to add an exit gate \n"
                "Press 'q' to quit\n"
            ).lower()           
            if cmd2 == 'ins':
                c = 'entrance_scanner'   
                type = 'scanner'
                in_out = 'entrance' 
            elif cmd2 == 'ing':
                c = 'entrance_gate'   
                type = 'gate'
                in_out = 'entrance'
            elif cmd2 == 'outs':
                c = 'exit_scanner'   
                type = 'scanner'
                in_out = 'exit'
            elif cmd2 == 'outg':
                c = 'exit_gate'   
                type = 'gate'
                in_out = 'exit'  
            elif cmd2 == 'q':
                quit = True
            else:
                print("Invalid command. Please do again.\n")
                continue
            break
        if quit:
            continue
        else:
            while True:
                parking_lot_id = input(f"Enter the ID of the parking lot where you want to add the {type}, or 'q' to quit: ").lower()
                if parking_lot_id== 'q':
                    break 
                parking_lot_id = f"lot_{parking_lot_id}"   
                               
                id = input(f"Enter the ID of the {in_out} {type}, or 'q' to quit: ").lower()
                if id== 'q':
                    break
                id =f"{parking_lot_id}_{in_out}_{type}_{id}"
                # wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post = {"action": c, "id": id, "parking_lot_id": parking_lot_id})
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")                         
        
    elif cmd == 'delete':
        c = 'delete_device'
        type = ''
        in_out = ''
        quit = False
        while True:
            cmd2 = input(
                "Press 'ins' to delete an entrance scanner \n"
                "Press 'ing' to delete an entrance gate \n"
                "Press 'outs' to delete an exit scanner \n"
                "Press 'outg' to delete an exit gate \n"
                "Press 'q' to quit\n"
            ).lower()           
            if cmd2 == 'ins':  
                type = 'scanner'
                in_out = 'entrance' 
            elif cmd2 == 'ing':  
                type = 'gate'
                in_out = 'entrance'
            elif cmd2 == 'outs':   
                type = 'scanner'
                in_out = 'exit'
            elif cmd2 == 'outg':  
                type = 'gate'
                in_out = 'exit'  
            elif cmd2 == 'q':
                quit = True
            else:
                print("Invalid command. Please do again.\n")
                continue
            break
        if quit:
            continue
        else:
            while True:
                parking_lot_id = input(f"Enter the ID of the parking lot where you want to delete the {in_out} {type}, or 'q' to quit: ").lower()
                if parking_lot_id== 'q':
                    break 
                parking_lot_id = f"lot_{parking_lot_id}"   
                               
                id = input(f"Enter the ID of the {in_out} {type} to delete, or 'q' to quit: ").lower()
                if id== 'q':
                    break
                id =f"{parking_lot_id}_{in_out}_{type}_{id}"
                
                # wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post={"action": c, "id": id, "parking_lot_id": parking_lot_id})
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
        
    elif cmd == 'addb':
        c = 'bot'
        while True:
            bot_id = input("Enter the ID of the telegram bot, or 'q' to quit: ").lower()
            if bot_id == 'q':
                break
            bot_id = f"bot_{bot_id}"
            # wait for the response from the server, try up to 10 seconds   
            timeout, res = get_response(URL_CATALOG, 'POST', 10, post={"action": c, "id": bot_id, "token": token})
            if timeout:
                print("No response from the server. Please check the server status.\n")
                break
            elif res[0]:
                print(f"{res[1]}\n")
                break
            else:
                print(f"{res[1]}\n")
    
    elif cmd == 'deleteb':
        c = 'delete_bot'
        while True:
            # wait for the response from the server, try up to 10 seconds
            timeout, res = get_response(URL_CATALOG, 'POST', 10, post = {"action": c})
            if timeout:
                print("No response from the server. Please check the server status.\n")
                break
            elif res[0]:
                print(f"{res[1]}\n")
                break
            else:
                print(f"{res[1]}\n")
    
    elif cmd == 'pair':
        c = 'pair'
        in_out = ''
        quit = False
        while True:
            in_out = input(
                "Press 'in' to pair a scanner with a gate in an entrance\n"
                "Press 'out' to pair a scanner with a gate in an exit\n"
                "Press 'q' to quit\n"
            ).lower()
            if in_out== 'q':
                quit = True
                break
            elif in_out == 'in' or in_out == 'out':
                in_out = 'entrance' if in_out == 'in' else 'exit'
                break
            else:
                print("Invalid command. Please do again.\n")
        if quit:
            continue
        while True:
            parking_lot_id = input("Enter the ID of the parking lot to add the passage, or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            parking_lot_id = f"lot_{parking_lot_id}"
            scanner_id = input(f"Enter the ID of an added scanner, or 'q' to quit: ").lower()
            if scanner_id == 'q':
                break
            scanner_id = f"{parking_lot_id}_{in_out}_scanner_{scanner_id}"
            gate_id = input(f"Enter the ID of an added gate, or 'q' to quit: ").lower()
            if gate_id == 'q':
                break
            gate_id = f"{parking_lot_id}_{in_out}_gate_{gate_id}"
            passage_id = input(f"Enter the ID of the new {in_out}, or 'q' to quit: ").lower()
            if passage_id == 'q':
                break
            passage_id = f"{parking_lot_id}_{in_out}_{passage_id}"
            
            timeout, res = get_response(
                URL_CATALOG,
                'POST',
                10,
                post={
                    "action": c,
                    "scanner_id": scanner_id,
                    "gate_id": gate_id,
                    "passage_id": passage_id,
                    "parking_lot_id": parking_lot_id
                }
            )
            if timeout:
                print("No response from the server. Please check the server status.\n")
                break
            elif res[0]:
                print(f"{res[1]}\n")
                break
            else:
                print(f"{res[1]}\n")
                       
    elif cmd == 'unpair':
        c = 'unpair'
        in_out = ''
        quit = False
        while True:
            in_out = input(
                "Press 'in' to unpair a scanner with a gate in an entrance\n"
                "Press 'out' to unpair a scanner with a gate in an exit\n"
                "Press 'q' to quit\n"
            ).lower()
            if in_out== 'q':
                quit = True
                break
            elif in_out == 'in' or in_out == 'out':
                in_out = 'entrance' if in_out == 'in' else 'exit'
                break
            else:
                print("Invalid command. Please do again.\n")
        if quit:
            continue
        while True:
            parking_lot_id = input("Enter the ID of the parking lot where you want to unpair a passage, or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            parking_lot_id = f"lot_{parking_lot_id}"
            passage_id = input("Enter the ID of the passage, or 'q' to quit: ").lower()
            if passage_id == 'q':
                break
            passage_id = f"{parking_lot_id}_{in_out}_{passage_id}"
            # wait for the response from the server, try up to 10 seconds
            timeout, res = get_response(
                URL_CATALOG,
                'POST',
                10,
                post={"action": c, "passage_id": passage_id, "parking_lot_id": parking_lot_id}
            )
            if timeout:
                print("No response from the server. Please check the server status.\n")
                break
            elif res[0]:
                print(f"{res[1]}\n")
                break
            else:
                print(f"{res[1]}\n")
                       
    else:
        print("Invalid command. Please do again.\n")
    