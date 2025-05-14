import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import time
import json
from ParkingMQTT import ParkingMQTT

class ParkingBot:
    def __init__(self, token, client_id, broker, port, base_topic="/parking"):
        self.token = token
        self.bot = telepot.Bot(token)
        self.callback_dict = {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }
        self.chat_ids = []
        self.base_topic = base_topic
        self.client = ParkingMQTT(client_id, broker, port, notifier=self)

        self.generic_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Check empty slot', callback_data='CHECK_SLOT')],
            [InlineKeyboardButton(text='Book a slot', callback_data='BOOK_SLOT')]
        ])

    def start(self):
        MessageLoop(self.bot, self.callback_dict).run_as_thread()
        print("Telegram bot is running...")
        self.client.start()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if chat_id not in self.chat_ids:
            self.chat_ids.append(chat_id)

        if content_type == 'text':
            text = msg['text']
            if text == '/start':
                self.bot.sendMessage(chat_id, "Welcome to Smart Parking Bot.\nUse /options to view available actions.")
            elif text == '/options':
                self.bot.sendMessage(chat_id, "Choose an option:", reply_markup=self.generic_keyboard)

    def on_callback_query(self, msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')

        if query_data == 'CHECK_SLOT':
            topic = self.base_topic + "/status"
            self.client.subscribe(topic)
            self.bot.sendMessage(chat_id, "Subscribed to parking status updates.")
        elif query_data == 'BOOK_SLOT':
            self.publish_booking(chat_id)
            self.bot.sendMessage(chat_id, "Booking request sent.")

    def publish_booking(self, chat_id):
        topic = self.base_topic + "/booking/request"
        msg = {
            "chat_id": chat_id,
            "timestamp": time.time(),
            "action": "book"
        }
        self.client.publish(topic, msg)

    def notify(self, topic, payload):
        try:
            decoded = payload.decode('utf-8')
            data = json.loads(decoded)
        except Exception:
            data = str(payload)

        for chat_id in self.chat_ids:
            self.bot.sendMessage(chat_id, f"Topic: {topic}\nData: {data}")
