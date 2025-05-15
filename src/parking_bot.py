import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from datetime import datetime
import json
import os

class ParkingBot:
    def __init__(self, token, parking, booking_file="BOOKING.json"):
        self.token = token
        self.bot = telepot.Bot(token)
        self.parking = parking
        self.booking_file = booking_file
        self.user_states = {}  # 保存用户输入状态

        self.callback_dict = {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }

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
            self.user_states[chat_id] = {'step': 'plate'}
            self.bot.sendMessage(chat_id, "Please enter your plate number:")
        elif text.lower().startswith('/cancel'):
            self.handle_cancel(chat_id, text)
        elif chat_id in self.user_states:
            self.handle_booking_step(chat_id, text)
        else:
            self.bot.sendMessage(chat_id, "Unknown command. Use /book or /cancel <plate>.")

    def handle_booking_step(self, chat_id, text):
        state = self.user_states[chat_id]
        if state['step'] == 'plate':
            state['plate'] = text.upper()
            state['step'] = 'time'
            self.bot.sendMessage(chat_id, "Enter expected arrival time (format: YYYY-MM-DD HH:MM:SS):")
        elif state['step'] == 'time':
            try:
                expecting_time = datetime.strptime(text, "%Y-%m-%d %H:%M:%S")
                result, message = self.parking.book(state['plate'], expecting_time)
                if result:
                    self.save_booking_to_json(state['plate'], expecting_time)
                self.bot.sendMessage(chat_id, message)
            except ValueError:
                self.bot.sendMessage(chat_id, "Invalid format. Please use YYYY-MM-DD HH:MM:SS")
            finally:
                del self.user_states[chat_id]

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

    def save_booking_to_json(self, plate, time_obj):
        booking_data = {}
        if os.path.exists(self.booking_file):
            with open(self.booking_file, 'r') as f:
                try:
                    booking_data = json.load(f)
                except json.JSONDecodeError:
                    booking_data = {}

        booking_data[plate] = {
            "plate": plate,
            "expecting_time": time_obj.strftime("%Y-%m-%d %H:%M:%S")
        }

        with open(self.booking_file, 'w') as f:
            json.dump(booking_data, f, indent=4)

        print(f"Saved booking for {plate} to {self.booking_file}")

    def remove_booking_from_json(self, plate):
        if os.path.exists(self.booking_file):
            with open(self.booking_file, 'r') as f:
                try:
                    booking_data = json.load(f)
                except json.JSONDecodeError:
                    booking_data = {}

            if plate in booking_data:
                del booking_data[plate]

                with open(self.booking_file, 'w') as f:
                    json.dump(booking_data, f, indent=4)

                print(f"Removed booking for {plate} from {self.booking_file}")

if __name__ == '__main__':
    token = '7675586421:AAHgUOVDNULEl2r6U9u2I8IsZzerUQKFROg'
    broker = 'mqtt.eclipseprojects.io'
    port = 1883
    client_id = 'parking_bot'

    bot = ParkingBot(token, client_id, broker, port)
    bot.start()

    while True:
        time.sleep(5)
