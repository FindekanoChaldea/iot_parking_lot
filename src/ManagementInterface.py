import requests
import re
import time
from config_loader import ConfigLoader
from TimeControl import TimeControl

time_control = TimeControl()
ConfigLoader = ConfigLoader()
host_RESTful = ConfigLoader.RESTful.host
port_RESTful = ConfigLoader.RESTful.port
catalog_uri = ConfigLoader.RESTful.catalog_uri
passage_uri = ConfigLoader.RESTful.passage_uri
config_uri = ConfigLoader.RESTful.config_uri  

URL = f"http://{host_RESTful}:{port_RESTful}"
URL_CATALOG = f"{URL}{catalog_uri}"
URL_PASSAGE = f"{URL}{passage_uri}"
URL_CONFIG = f"{URL}{config_uri}"
token = ConfigLoader.telegram_bot_token

class ParkingConfig:
    def __init__(self):
        self.catalog_uri = catalog_uri
        self.passage_uri = passage_uri
        self.config_uri = config_uri
        self.free_stop = 60 ##seconds
        self.check_pay_interval = 60 ##seconds
        self.booking_expire_time = 300 ##seconds
        self.hourly_rate = 1.50 # euros   
        self.book_filter_interval = 600  # seconds, every 10 minutes   
        self.payment_filter_interval = 60 ##seconds 
        
        self.unpaired_time_limit = 300  # Check every 5 minutes
        self.listen_device_info_interval = 300  # Check every 5 minutes
        
        self.notice_interval = 120
    
    def load_config(self):
        return {"config": [
            self.catalog_uri,
            self.passage_uri,
            self.config_uri,
            self.free_stop,
            self.check_pay_interval,
            self.booking_expire_time,
            self.hourly_rate,
            self.book_filter_interval,
            self.payment_filter_interval,
            self.unpaired_time_limit,
            self.listen_device_info_interval,
            self.notice_interval
        ]}
       
    def show_default(self):
        print(f"Default configurations:\n"
              f"catalog_uri: {self.catalog_uri}\n"
              f"passage_uri: {self.passage_uri}\n"
              f"config_uri: {self.config_uri}\n"
              f"Free_stop: {self.free_stop} seconds, within which the car will not be charged\n"
              f"check_pay_interval: {self.check_pay_interval} seconds, the time limit between the fee check and finish transaction\n"
              f"booking_expire_time: {self.booking_expire_time} seconds, the time limit of no appearance after the booking time\n"
              f"hourly_rate: {self.hourly_rate} euros, the hourly rate for parking\n"
              f"book_filter_interval: {self.book_filter_interval} seconds, check if there are expired books by interval\n"
              f"payment_filter_interval: {self.payment_filter_interval} seconds, check if there are expired payments by interval\n"
              f"unpaired_time_limit: {self.unpaired_time_limit} seconds, the time limit for the devices (scanner/gate) to pair, disconnect more than that\n"
              f"listen_device_info_interval: {self.listen_device_info_interval} seconds, check the device status by interval\n"
              f"notice_interval {self.notice_interval} seconds, the devices update their info by interval\n")


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
        "Press 'i' to initiate or change the system configurations\n"   
        "Press 's' to show the list of devices\n"
        "Press 'p' to add a new parking lot\n"
        "Press 'add' to add a new device\n"
        "Press 'addb' to add the telegram bot\n"
        "Press 'pair' to pair a scanner with a gate\n"
        "Press 'unpair' to unpair a passage devices\n"
    ).lower()
    
    if cmd == 'i':
        parking_config = ParkingConfig()
        while True:
            qiut = False
            while True:
                c = input(
                    f"Here are the default configurations:\n\n"
                    f"{parking_config.show_default()}\n\n"
                    f"Type the property name to change the configurations\n"
                    f"Press 'q' to quit\n"
                )
                if c == "catalog_uri":
                    new_value = input("Enter the new catalog URI (default: /catalog): ").strip()
                    if new_value:
                        parking_config.catalog_uri = new_value
                    break
                elif c == "passage_uri":
                    new_value = input("Enter the new passage URI (default: /passage): ").strip()
                    if new_value:
                        parking_config.passage_uri = new_value
                    break
                elif c == "config_uri": 
                    new_value = input("Enter the new config URI (default: /config): ").strip()
                    if new_value:
                        parking_config.config_uri = new_value
                    break
                elif c == "free_stop":
                    new_value = input("Enter the new free stop time in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.free_stop = int(new_value)
                    break
                elif c == "check_pay_interval":
                    new_value = input("Enter the new check pay interval in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.check_pay_interval = int(new_value)
                    break
                elif c == "booking_expire_time":
                    new_value = input("Enter the new booking expire time in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.booking_expire_time = int(new_value)
                    break
                elif c == "hourly_rate":    
                    new_value = input("Enter the new hourly rate in euros (default: 1.50): ").strip()
                    if new_value.replace('.', '', 1).isdigit():
                        parking_config.hourly_rate = float(new_value)
                    break
                elif c == "book_filter_interval":
                    new_value = input("Enter the new book filter interval in seconds (default: 600): ").strip()
                    if new_value.isdigit():
                        parking_config.book_filter_interval = int(new_value)
                    break
                elif c == "payment_filter_interval":
                    new_value = input("Enter the new payment filter interval in seconds (default: 60): ").strip()
                    if new_value.isdigit():
                        parking_config.payment_filter_interval = int(new_value)
                    break
                elif c == "unpaired_time_limit":
                    new_value = input("Enter the new unpaired time limit in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.unpaired_time_limit = int(new_value)
                    break
                elif c == "listen_device_info_interval":
                    new_value = input("Enter the new listen device info interval in seconds (default: 300): ").strip()
                    if new_value.isdigit():
                        parking_config.listen_device_info_interval = int(new_value)
                    break
                elif c == "notice_interval":
                    new_value = input("Enter the new notice interval in seconds (default: 120): ").strip()
                    if new_value.isdigit():
                        parking_config.notice_interval = int(new_value)
                    break
                elif c == "q":
                    qiut = True
                    break
                else:
                    print("Invalid property name. Please try again.\n")
            if qiut:
                break
            else:
                # Wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CONFIG, 'POST', 10, post = parking_config.load_config())
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
            timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c])
            if timeout:
                print("No response from the server. Please check the server status.\n")
                continue
            print(f"{res[1]}\n")
        
    elif cmd == 'p':
        c = 'parking_lot'
        while True:
            parking_lot_id = input("Enter the ID of the parking lot (format: lot + Number) ,or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            pattern = r'^lot\d+$'
            if re.match(pattern, parking_lot_id):
                #wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c, parking_lot_id])
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
            else:
                print("Invalid parking lot ID format. Please use 'lot#' format.\n")
    
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
                parking_lot_id = input(f"Enter the ID of the parking lot where you want to add the {type} (format: lot + Number), or 'q' to quit: ").lower()
                if parking_lot_id== 'q':
                    break
                id = input(f"Enter the ID of the {in_out} {type} (format: {in_out}_{type} + Number), or 'q' to quit: ").lower()
                if id== 'q':
                    break
                if re.match(r'^lot\d+$', parking_lot_id) and re.match(fr'^{in_out}_{type}\d+$', id):
                    # wait for the response from the server, try up to 10 seconds
                    timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c, id, parking_lot_id])
                    if timeout:
                        print("No response from the server. Please check the server status.\n")
                        break
                    elif res[0]:
                        print(f"{res[1]}\n")
                        break
                    else:
                        print(f"{res[1]}\n")
                else:
                    print(f"Invalid input. Please ensure the parking lot ID and the {type} ID follows valid format.\n")                                   
        
    elif cmd == 'addb':
        c = 'bot'
        while True:
            bot_id = input("Enter the ID of the telegram bot (format: bot + anything not space), or 'q' to quit: ").lower()
            if bot_id == 'q':
                break
            if re.match(r'^bot\S*$', bot_id):
                # wait for the response from the server, try up to 10 seconds   
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c, bot_id, token])
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
            else:
                print("Invalid bot ID format. Please use 'bot#' format.\n")
    
    elif cmd == 'pair':
        c == 'pair'
        in_out = ''
        quit = False
        while True:
            in_out = input(
                "Press 'entrance' to pair a scanner with a gate in an entrance\n"
                "Press 'exit' to pair a scanner with a gate in an exit\n"
                "Press 'q' to quit\n"
            ).lower()
            if in_out== 'q':
                quit = True
                break
            elif in_out == 'entrance' or in_out == 'exit':
                break
            else:
                print("Invalid command. Please do again.\n")
        if quit:
            continue
        while True:
            parking_lot_id = input("Enter the ID of the parking lot to add the passage (format: lot + Number), or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            scanner_id = input("Enter the ID of an added scanner (format: scanner + Number), or 'q' to quit: ").lower()
            if scanner_id == 'q':
                break
            gate_id = input("Enter the ID of an added gate (format: gate + Number), or 'q' to quit: ").lower()
            if gate_id == 'q':
                break
            passage_id = input(f"Enter the ID of the new {in_out} (format: {in_out} + Number), or 'q' to quit: ").lower()
            if passage_id == 'q':
                break
            if re.match(r'^lot\d+$', parking_lot_id) and re.match(r'^scanner\d+$', scanner_id) and re.match(r'^gate\d+$', gate_id) and re.match(fr'^{in_out}\d+$', passage_id):
                # wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c, scanner_id, gate_id, passage_id, parking_lot_id])
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
            else:
                print("Invalid input. Please ensure the IDs are valid.\n")
                       
    elif cmd == 'unpair':
        c == 'unpair'
        while True:
            parking_lot_id = input("Enter the ID of the parking lot where you want to unpair a passage (format: lot + Number), or 'q' to quit: ").lower()
            if parking_lot_id == 'q':
                break
            passage_id = input("Enter the ID of the passage (format: exit/entrance + Number), or 'q' to quit: ").lower()
            if passage_id == 'q':
                break
            if re.match(r'^lot\d+$', parking_lot_id) and re.match(r'^(exit|entrance)\d+$', passage_id):
                
                # wait for the response from the server, try up to 10 seconds
                timeout, res = get_response(URL_CATALOG, 'POST', 10, post = [c, passage_id, parking_lot_id])
                if timeout:
                    print("No response from the server. Please check the server status.\n")
                    break
                elif res[0]:
                    print(f"{res[1]}\n")
                    break
                else:
                    print(f"{res[1]}\n")
            else:
                print("Invalid input. Please ensure the IDs are valid.\n")
                       
    else:
        print("Invalid command. Please do again.\n")
    