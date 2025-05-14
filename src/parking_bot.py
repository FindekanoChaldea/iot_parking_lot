import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import json
from ParkingMQTT import ParkingMQTT

class ParkingBot:
    def __init__(self, token, client_id, broker, port, notifier, base_topic="/parking"):
        self.token = token
        self.bot = telepot.Bot(self.token)
        self.chat_ids = []
        self.base_topic = base_topic
        self.client = ParkingMQTT(client_id, broker, port, notifier)
        self.keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='Check empty slot', callback_data='CHECK_SLOT')],
            [InlineKeyboardButton(text='Book a slot', callback_data='BOOK_SLOT')]
        ])

    def start(self):
        MessageLoop(self.bot, {
            'chat': self.on_chat_message,
            'callback_query': self.on_callback_query
        }).run_as_thread()
        print("Bot is running...")
        self.client.start()

    def on_chat_message(self, msg):
        content_type, chat_type, chat_id = telepot.glance(msg)
        if content_type == 'text':
            text = msg['text']
            if chat_id not in self.chat_ids:
                self.chat_ids.append(chat_id)

            if text == '/start':
                self.bot.sendMessage(chat_id, "Welcome to Smart Parking! Use /options to view commands.")
            elif text == '/options':
                self.bot.sendMessage(chat_id, 'Choose an action:', reply_markup=self.keyboard)

    def on_callback_query(self, msg):
        query_id, chat_id, query_data = telepot.glance(msg, flavor='callback_query')
        if query_data == 'CHECK_SLOT':
            self.client.subscribe(self.base_topic + "/status")
            self.bot.sendMessage(chat_id, "Subscribed to parking status.")
        elif query_data == 'BOOK_SLOT':
            self.client.publish(self.base_topic + "/booking/request", {"from": "bot_user"})
            self.bot.sendMessage(chat_id, "Booking request sent!")

    def notify(self, topic, payload):
        try:
            data = json.loads(payload.decode('utf-8'))
        except:
            data = str(payload)

        message = f"Update from {topic}:\n{json.dumps(data, indent=2)}"
        for chat_id in self.chat_ids:
            self.bot.sendMessage(chat_id, message)
