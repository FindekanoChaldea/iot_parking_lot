import telepot
from telepot.loop import MessageLoop
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import time
from MyMQTT import MyMQTT


class ParkingBot():
	def __init__(self,token, client_id, broker, port, base_topic):
		self.token = token
		self.bot = telepot.Bot(self.token)
		self.callback_dict = {'chat':self.on_chat_message,
							  'callback_query': self.queries}
		self.client_mqtt = ParkingMQTT(client_id,broker,port)
		self.base_topic = base_topic
		self.generic_keyboard = InlineKeyboardMarkup(inline_keyboard =[[InlineKeyboardButton(text='Check empty slot', callback_data='CHECK_SLOT'))],[InlineKeyboardButton(text='Book a slot', callback_data='BOOK_SLOT')]])

