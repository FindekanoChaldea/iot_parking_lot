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
		self.generic_keyboard = InlineKeyboardMarkup(inline_keyboard =[[InlineKeyboardButton(text='SwitchON', callback_data='ON_light1')],[InlineKeyboardButton(text='SwitchOFF', callback_data='OFF_light1')]])

