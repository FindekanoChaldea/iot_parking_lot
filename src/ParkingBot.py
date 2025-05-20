import telepot
from config_loader import ConfigLoader
from ParkingMQTT import ParkingMQTT as client
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime, timedelta
import time
import json
from zoneinfo import ZoneInfo  

italy_tz = ZoneInfo("Europe/Rome")  # Define the Italy timezone

class Status:
        Input_plate = 'plate'
        Input_time = 'time'
        Cancel = 'cancel'

class Chat: 
    def __init__(self, chat_id):
        self.chat_id = chat_id
        self.status = None
        self.plate_license = None
        self.expecting_time = None

    def set_status(self, status):
        self.status = status

    def set_plate_license(self, plate):
        self.plate_license = plate

    def set_expecting_time(self, expecting_time):
        self.expecting_time = expecting_time

    def get_expecting_time(self):
        return self.expecting_time.strftime("%Y-%m-%d %H:%M:%S") if self.expecting_time else None
    
    def to_dict(self):
        return {
            'action': 'book',
            'chat_id': self.chat_id,
            'plate_license': self.plate_license,
            'expecting_time': self.expecting_time.strftime("%Y-%m-%d %H:%M:%S")
        } if self.expecting_time else{
            'action': 'cancel',
            'chat_id': self.chat_id,
            'plate_license': self.plate_license,
        }


class ParkingBot:    
    def __init__(self, token, client_id, broker, port, info_topic, command_topic):
        self.client = client(client_id, broker, port, self)
        self.client.start()
        self.info_topic = info_topic
        self.client.subscribe(command_topic)
        self.token = token
        self.bot = telepot.Bot(self.token)
        self.chats = {}
        self.callback_dict = {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }

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

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type != 'text':
            self.bot.sendMessage(chat_id, "Please send text only.")
            return
        text = msg['text'].strip()
        print(f'Received message: "{text}" from chat_id: "{chat_id}"')
        # Command Handling
        if text.lower() == '/start':
            self.chats[chat_id] = Chat(chat_id)
            self.bot.sendMessage(chat_id, "Welcome to Polito Parking Lot! Send /book to reserve a spot, /cancel to cancel.")
        elif text.lower() == '/book':
            self.chats[chat_id].set_status(Status.Input_plate)
            self.bot.sendMessage(chat_id, "Please enter your plate number:")
        elif text.lower() == '/cancel':           
            self.chats[chat_id].set_status(Status.Cancel)
            self.bot.sendMessage(chat_id, "Please enter your plate number to cancel:")
        elif chat_id in self.chats.keys():
            if self.chats[chat_id].status == Status.Input_plate:
                self.handle_booking(chat_id, text)
            elif self.chats[chat_id].status == Status.Cancel:
                self.handle_cancel(chat_id, text)
        else:
            self.bot.sendMessage(chat_id, "Welcome to Polito Parking Lot! Send /start to start.")


    def on_callback_query(self, msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data.startswith('time_'):
            self.handle_booking(chat_id, query_data)
        elif chat_id not in self.chats.keys():
            self.bot.sendMessage(chat_id, "Session finished, Send /start to start.")
            return
        elif query_data == 'Confirm':
            chat = self.chats[chat_id]
            data = chat.to_dict()
            self.bot.sendMessage(chat_id, "Checking availability...")   
            self.publish(data)
        elif query_data == 'Modify':
            self.chats[chat_id].set_status(Status.Input_plate)
            self.bot.sendMessage(chat_id, "Please enter your plate number:")
            self.publish(data)
        elif query_data == 'Quit':
            del self.chats[chat_id]
            self.bot.sendMessage(chat_id, "Reservation quit")
        else:
            self.bot.sendMessage(chat_id, "Welcome to Polito Parking Lot! Send /start to start.")
            
    def handle_booking(self, chat_id, text):
        status = self.chats[chat_id].status
        if status == Status.Input_plate:
            plate_license = text.replace(" ", "").upper()
            chat = self.chats[chat_id]
            chat.set_plate_license(plate_license)
            chat.set_status(Status.Input_time)
            times = self.generate_time()
            keyboard_buttons = [
                [InlineKeyboardButton(text=datetime.strftime(times[i], "%m-%d %H:%M"), callback_data='time_' + datetime.strftime(times[i], "%Y-%m-%d %H:%M:%S")),
                InlineKeyboardButton(text=datetime.strftime(times[i+1], "%m-%d %H:%M"), callback_data='time_' + datetime.strftime(times[i+1], "%Y-%m-%d %H:%M:%S"))]
                for i in range(0, len(times), 2)
                ]   
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            self.bot.sendMessage(chat_id, "Choose arrival time (The reservation will ONLY be valid BEFORE the selected time!):", reply_markup=keyboard)
        elif status == Status.Input_time:
            time_text = text.split('_')[1]
            expecting_time = datetime.strptime(time_text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=italy_tz)  
            chat = self.chats[chat_id]
            chat.set_expecting_time(expecting_time)  
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text = 'Confirm', callback_data = 'Confirm'), InlineKeyboardButton(text = 'Modify', callback_data = 'Modify'), InlineKeyboardButton(text = 'Quit', callback_data = 'Quit')]])
            self.bot.sendMessage(chat_id, f"Your reservation: Car {chat.plate_license} at {chat.get_expecting_time()}", reply_markup=keyboard)                  
                
    def confirm (self, chat_id, msg):
        self.bot.sendMessage(chat_id, msg)
        self.chats[chat_id].set_status(None)   
        del self.chats[chat_id]    
    
    def handle_cancel(self, chat_id, text):
        plate_license = text.upper()
        chat = self.chats[chat_id]
        chat.set_plate_license(plate_license)
        self.bot.sendMessage(chat_id, "Checking your booking...")   
        self.publish(chat.to_dict()) 

    def generate_time(self, n=4, tz=italy_tz):
        now = datetime.now(tz)
        ## time xx:yy
        ## if yy < 15, next_time = xx:30
        ## if 15 <= yy < 45, next_time = xx+1:00
        ## if 45 <= yy < 60, next_time = xx+1:30
        if now.minute < 15:
            next_time = now.replace(minute=30, second=0, microsecond=0)
        elif now.minute >= 15 and now.minute < 45:    
            next_time = now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            next_time = now.replace(minute=30, second=0, microsecond=0)
        times = []
        for _ in range(n):
            times.append(next_time)
            next_time += timedelta(minutes=30)
        return times

if __name__ == '__main__':
    config_loader = ConfigLoader()
    token = config_loader.telegram_bot_token
    client_id = "TelegramBot"
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    info_topic = "polito_parking/bot/info"
    command_topic = "polito_parking/bot/command"
    bot = ParkingBot(token, client_id, broker, port, info_topic, command_topic)
    bot.start()
    while True:
        time.sleep(5)
