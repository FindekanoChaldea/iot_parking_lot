import telepot
from config_loader import ConfigLoader
from ParkingMQTT import ParkingMQTT as client
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import time
import requests
import json
import threading
from TimeControl import TimeControl
from zoneinfo import ZoneInfo  

italy_tz = ZoneInfo("Europe/Rome")  # Define the Italy timezone

class Status:
        START = 'start'
        BOOK_PLATE = 'book_plate'
        BOOK_TIME = 'book_time'
        AVAILABILITY = 'availability'
        CANCEL= 'cancel'
        PAY_CHECK = 'pay_check'
        PAY_PAY = 'pay_pay'
        PAY_CANCEL = 'pay_cancel'

class Chat: 
    def __init__(self, chat_id, timeout_callback=None):
        self.chat_id = chat_id
        self.status = Status.START
        self.plate_license = None
        self.expecting_time = None
        self.timer = None
        self.timeout_callback = timeout_callback

    def set_status(self, status):
        self.status = status

    def set_plate_license(self, plate):
        self.plate_license = plate

    def set_expecting_time(self, expecting_time):
        self.expecting_time = expecting_time

    def get_expecting_time(self):
        return self.expecting_time.strftime("%Y-%m-%d %H:%M:%S") if self.expecting_time else None
    
    def to_dict(self):
        if self.status == Status.AVAILABILITY:
            return {
                'action': 'availability',
                'chat_id': self.chat_id
            }
        elif self.status == Status.BOOK_TIME:
            return {
                'action': 'book',
                'chat_id': self.chat_id,
                'plate_license': self.plate_license,
                'expecting_time': self.expecting_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        elif self.status == Status.CANCEL:
            return {
                'action': 'cancel',
                'chat_id': self.chat_id,
                'plate_license': self.plate_license,
            }
        elif self.status == Status.PAY_CHECK:
            return {
                'action': 'pay_check',
                'chat_id': self.chat_id,
                'plate_license': self.plate_license,
            }
        elif self.status == Status.PAY_PAY:
            return {
                'action': 'pay_pay',
                'chat_id': self.chat_id,
                'plate_license': self.plate_license,
            }
            
    def reset_timer(self, timeout=300):
        if self.timer:
            self.timer.cancel()
        if self.timeout_callback:
            self.timer = threading.Timer(timeout, self.timeout_callback, args=(self.chat_id,))
            self.timer.start()

    def cancel_timer(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
            

class ParkingBot:
    
    def __init__(self, URL):
        self.time_control = TimeControl()
        self.URL = URL
        # continuously try to connect to the server until successful for 60 seconds
        print('connecting to server...')
        timer1 = self.time_control.add_timer(60)
        data = None
        while not timer1.timeout:
            try:
                res = requests.post(self.URL, json = 'newbot')
                if res and res.ok:
                    data = res.json()
                    print('initializing bot')
                    break
            except Exception as e:
                pass
            time.sleep(1)
        # if successful, get the broker information and initialize the client
        if data[0]:
            token, URL_UPDATE, broker, port, client_id, info_topic, command_topic, book_start_time, time_out, notice_interval = data[1]
        else:
            print('Failed to connect to the server, exiting...')
            return
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.info_topic = info_topic
        self.client.subscribe(command_topic)

        self.URL_UPDATE = URL_UPDATE
        self.payload = {
            "client_id": client_id,
            "info_topic_gate": info_topic,
            "command_topic_gate": command_topic
        }
        try:
            res = requests.post(self.URL_UPDATE, json = self.payload) 
        except Exception as e:
            print("Catalog connection failed:", e)
            
        # Initialize the Telegram bot with the provided token
        self.token = token
        self.bot = telepot.Bot(self.token)
        self.chats = {}
        self.callback_dict = {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }
        
        # Necessary properties
        self.book_start_time = book_start_time  # 30 minutes after the current time
        self.time_out = time_out  # Timeout for each inactive chat session in seconds
        self.notice_interval = notice_interval # seconds
        print('bot initialized')
    
    def publish(self, message):
        self.client.publish(self.info_topic, message)
        print(f'Published message: "{message}" to topic: "{self.info_topic}"')
    
    def notify(self, topic, payload):
        data = json.loads(payload)
        print(f'Received message: "{data}"')
        chat_id = data[0]
        msg = data[1]
        self.confirm(chat_id, msg)
    
    def start(self):
        MessageLoop(self.bot, self.callback_dict).run_as_thread()
        print("ParkingBot is running...")

    def timeout_session(self, chat_id):
        if chat_id in self.chats:
            del self.chats[chat_id]
            
    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if chat_id not in self.chats:
            self.chats[chat_id] = Chat(chat_id, timeout_callback=self.timeout_session)
            chat = self.chats[chat_id]
            chat.reset_timer(timeout = self.time_out)
        if content_type != 'text':
            self.bot.sendMessage(chat_id, "Please send text only.")
            return
        text = msg['text'].strip()
        print(f'Received message: "{text}" from chat_id: "{chat_id}"')
        # Command Handling
        if chat_id not in self.chats.keys() and text.lower() != '/start':
            self.bot.sendMessage(chat_id, "Welcome to Polito Parking Lot! Send /start to start.")
        elif text.lower() == '/start':
            self.chats[chat_id] = Chat(chat_id)
            self.bot.sendMessage(chat_id, "Send /availability to check free spots, /book to reserve a spot, /cancel to cancel reservation, /pay to pay your parking fee")
        elif text.lower() == '/availability':
            self.chats[chat_id].set_status(Status.AVAILABILITY)
            self.publish(self.chats[chat_id].to_dict())
        elif text.lower() == '/book':
            self.chats[chat_id].set_status(Status.BOOK_PLATE)
            self.bot.sendMessage(chat_id, "Please enter your plate number:")
        elif text.lower() == '/cancel':           
            self.chats[chat_id].set_status(Status.CANCEL)
            self.bot.sendMessage(chat_id, "Please enter your plate number to cancel:")
        elif text.lower() == '/pay':
            self.chats[chat_id].set_status(Status.PAY_CHECK)
            self.bot.sendMessage(chat_id, "Please enter your plate number to pay:")
        elif chat_id in self.chats.keys():
            if self.chats[chat_id].status == Status.BOOK_PLATE:
                self.handle_booking(chat_id, text)
            elif self.chats[chat_id].status == Status.PAY_CHECK:
                self.handle_pay(chat_id, text)
            elif self.chats[chat_id].status == Status.PAY_PAY:
                pass
            elif self.chats[chat_id].status == Status.CANCEL:
                self.handle_cancel(chat_id, text)
            else:
                self.bot.sendMessage(chat_id, "Send /availability to check free spots, /book to reserve a spot, /cancel to cancel reservation, /pay to pay your parking fee")


    def on_callback_query(self, msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data.startswith('time_'):
            self.handle_booking(chat_id, query_data)
        elif chat_id not in self.chats.keys():
            self.bot.sendMessage(chat_id, "Session finished, Send /start to start.")
            return
        elif self.chats[chat_id].status == Status.BOOK_TIME:
            if query_data == 'Confirm':
                chat = self.chats[chat_id]
                data = chat.to_dict()
                self.bot.sendMessage(chat_id, "Checking availability...")   
                self.publish(data)
            elif query_data == 'Modify':
                self.chats[chat_id].set_status(Status.BOOK_PLATE)
                self.bot.sendMessage(chat_id, "Please enter your plate number:")
            elif query_data == 'Quit':
                del self.chats[chat_id]
                self.bot.sendMessage(chat_id, "Reservation quit")
        elif self.chats[chat_id].status == Status.PAY_CHECK:
            if query_data == 'Confirm':
                self.chats[chat_id].set_status(Status.PAY_PAY)
                self.handle_pay(chat_id, None)
            elif query_data == 'PayLater':
                self.bot.sendMessage(chat_id, "Payment postponed. You will be charged again accordingly later.")          
        else:
            self.bot.sendMessage(chat_id, "Welcome to Polito Parking Lot! Send /start to start.")
             
    def handle_booking(self, chat_id, text):
        status = self.chats[chat_id].status
        if status == Status.BOOK_PLATE:
            plate_license = text.replace(" ", "").upper()
            chat = self.chats[chat_id]
            chat.set_plate_license(plate_license)
            chat.set_status(Status.BOOK_TIME)
            times = self.generate_time()
            keyboard_buttons = [
                [InlineKeyboardButton(text=datetime.strftime(times[i], "%m-%d %H:%M"), callback_data='time_' + datetime.strftime(times[i], "%Y-%m-%d %H:%M:%S")),
                InlineKeyboardButton(text=datetime.strftime(times[i+1], "%m-%d %H:%M"), callback_data='time_' + datetime.strftime(times[i+1], "%Y-%m-%d %H:%M:%S"))]
                for i in range(0, len(times), 2)
                ]   
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            self.bot.sendMessage(chat_id, "Choose arrival time (The reservation will ONLY be valid BEFORE the selected time!):", reply_markup=keyboard)
        elif status == Status.BOOK_TIME:
            time_text = text.split('_')[1]
            expecting_time = datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=italy_tz)  
            chat = self.chats[chat_id]
            chat.set_expecting_time(expecting_time)  
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = 'Confirm', callback_data = 'Confirm'), InlineKeyboardButton(text = 'Modify', callback_data = 'Modify'), InlineKeyboardButton(text = 'Quit', callback_data = 'Quit')]])
            self.bot.sendMessage(chat_id, f"Your reservation: Car {chat.plate_license} at {chat.get_expecting_time()}", reply_markup=keyboard)                     
    
    def handle_cancel(self, chat_id, text):
        plate_license = text.upper()
        chat = self.chats[chat_id]
        chat.set_plate_license(plate_license)
        self.bot.sendMessage(chat_id, "Checking your booking...")   
        self.publish(chat.to_dict()) 
    
    def handle_pay(self, chat_id, text):
        status = self.chats[chat_id].status
        if status == Status.PAY_CHECK:
            plate_license = text.replace(" ", "").upper()
            chat = self.chats[chat_id]
            chat.set_plate_license(plate_license)
            self.bot.sendMessage(chat_id, "Checking your payment...")   
            self.publish(chat.to_dict())  
        elif status == Status.PAY_PAY:
            chat = self.chats[chat_id]
            self.bot.sendMessage(chat_id, "Processing your payment...")   
            self.publish(chat.to_dict())
        
    def confirm (self, chat_id, msg):
        chat = self.chats[chat_id]
        if self.chats[chat_id].status == Status.AVAILABILITY:
            self.bot.sendMessage(chat_id, msg)
            self.bot.sendMessage(chat_id, "Send /availability to check free spots, /book to reserve a spot, /cancel to cancel reservation, /pay to pay your parking fee")
            return
        elif self.chats[chat_id].status == Status.PAY_CHECK:
            if msg[0]:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = 'Confirm', callback_data = 'Confirm'), InlineKeyboardButton(text = 'Pay Later', callback_data = 'PayLater')]])
                self.bot.sendMessage(chat_id, msg[1], reply_markup=keyboard) 
            else:
                self.bot.sendMessage(chat_id, msg[1])
            return
        elif self.chats[chat_id].status == Status.PAY_PAY:
            if msg[0]:
                self.bot.sendMessage(chat_id, msg[1])
            else:
                self.bot.sendMessage(chat_id, msg[1])
            return
        self.chats[chat_id].set_status(None)   
        del self.chats[chat_id] 

    def generate_time(self, n=4, tz=italy_tz):
        now = datetime.now(tz)
        ## start xx:yy
        ## start = now.minute + self.book_start_time
        ## if yy < 30, start = xx:30
        ## if yy >= 30, start = xx+1:00
        start = (now + timedelta(minutes=self.book_start_time))
        if start.minute < 30:
            next_time = start.replace(minute=30, second=0, microsecond=0)
        elif start.minute >= 30:    
            next_time = start.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        times = []
        for _ in range(n):
            times.append(next_time)
            next_time += timedelta(minutes=30)
        return times

if __name__ == '__main__':

    config_loader = ConfigLoader()
    host = config_loader.RESTful.host
    port = config_loader.RESTful.port
    URL = f"http://{host}:{port}"
    bot = ParkingBot(URL)
    bot.start()
    while True:
        time.sleep(5)
