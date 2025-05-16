import telepot
from ParkingMQTT import ParkingMQTT as client
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import time
import json
import os
from zoneinfo import ZoneInfo  

italy_tz = ZoneInfo("Europe/Rome")  # Define the Italy timezone

class ParkingBot:
    class Status:
        Input_plate = 'plate'
        Input_time = 'time'
        
    def __init__(self, token, client_id, broker, port, info_topic, command_topic):
        self.client = client(client_id, broker, port, self)
        self.topic = info_topic
        self.client.subscribe(command_topic)
        self.token = token
        self.bot = telepot.Bot(token)
        self.user_states = {}
        self.callback_dict = {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }

    def publish(self, message):
        self.client.publish(self.topic, message)
        print(f"Published message: {message} to topic: {self.topic}")
    
    def notify(self, topic, payload):
        payload = json.loads(payload)
        client_id = payload[0]
        msg = payload[1]
        self.confirm(client_id, msg)
    
    def start(self):
        MessageLoop(self.bot, self.callback_dict).run_as_thread()
        print("ParkingBot is running...")

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)

        if content_type != 'text':
            self.bot.sendMessage(chat_id, "Please send text only.")
            return

        text = msg['text'].strip()

        # Command Handling
        if text.lower() == '/start':
            self.bot.sendMessage(chat_id, "Welcome to ParkingBot! Use /book to reserve a spot, /cancel <plate> to cancel.")
        elif text.lower() == '/book':
            self.user_states[chat_id] = self.Status.Input_plate
            self.bot.sendMessage(chat_id, "Please enter your plate number:")
        elif text.lower().startswith('/cancel'):
            self.handle_cancel(chat_id, text)
        elif chat_id in self.user_states.keys():
            self.handle_booking_step(chat_id, text)
        else:
            self.bot.sendMessage(chat_id, "Unknown command. Use /book or /cancel <plate>.")

    def handle_booking_step(self, chat_id, text):
        plate_license = None
        expecting_time = None
        states = self.user_states[chat_id]
        if states == self.Status.Input_plate:
            plate_license = text.upper()
            self.user_states[chat_id] = self.Status.Input_time
            self.bot.sendMessage(chat_id, "Enter expected arrival time (format: YYYY-MM-DD HH:MM:SS):")
        elif states == self.Status.Input_time:
            try:
                expecting_time = datetime.strptime(text, "%Y-%m-%d %H:%M:%S").replace(tzinfo=italy_tz)
            except ValueError:
                self.bot.sendMessage(chat_id, "Invalid format. Please use YYYY-MM-DD HH:MM:SS")
            finally:
                del self.user_states[chat_id]
        data = {'chat_id': chat_id,
                'action': 'book',
                'plate': plate_license,
                'expecting_time': expecting_time.strftime("%Y-%m-%d %H:%M:%S")}
        self.publish(json.dumps(data))
                
    def confirm (self, chat_id, msg):
        self.bot.sendMessage(chat_id, msg)       
    
    def handle_cancel(self, chat_id, text):
        try:
            plate = text.split(' ')[1].upper()
        except IndexError:
            self.bot.sendMessage(chat_id, "Please provide the plate number. Usage: /cancel ABC123")
            return

        if plate in self.parking.bookings:
            del self.parking.bookings[plate]
            self.remove_booking_from_json(plate)
            self.bot.sendMessage(chat_id, f"Booking for {plate} has been cancelled.")
        else:
            self.bot.sendMessage(chat_id, f"No active booking found for plate: {plate}")

    def on_callback_query(self, msg):
        query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
        self.bot.answerCallbackQuery(query_id, text="Not implemented")

    # def save_booking_to_json(self, plate, time_obj):
    #     booking_data = {}
    #     if os.path.exists(self.booking_file):
    #         with open(self.booking_file, 'r') as f:
    #             try:
    #                 booking_data = json.load(f)
    #             except json.JSONDecodeError:
    #                 booking_data = {}

    #     booking_data[plate] = {
    #         "plate": plate,
    #         "expecting_time": time_obj.strftime("%Y-%m-%d %H:%M:%S")
    #     }

    #     with open(self.booking_file, 'w') as f:
    #         json.dump(booking_data, f, indent=4)

    #     print(f"Saved booking for {plate} to {self.booking_file}")

    # def remove_booking_from_json(self, plate):
    #     if os.path.exists(self.booking_file):
    #         with open(self.booking_file, 'r') as f:
    #             try:
    #                 booking_data = json.load(f)
    #             except json.JSONDecodeError:
    #                 booking_data = {}

    #         if plate in booking_data:
    #             del booking_data[plate]

    #             with open(self.booking_file, 'w') as f:
    #                 json.dump(booking_data, f, indent=4)

    #             print(f"Removed booking for {plate} from {self.booking_file}")

if __name__ == '__main__':
    token = '7675586421:AAHgUOVDNULEl2r6U9u2I8IsZzerUQKFROg'
    client_id = "TelegramBot"
    broker = "mqtt.eclipseprojects.io"
    port = 1883
    info_topic = "polito_parking/bot/info"
    command_topic = "polito_parking/bot/command"
    bot = ParkingBot(token, client_id, broker, port, info_topic, command_topic)
    bot.start()
