## To store the devices' information, manage the topics of the messages
import os
import json

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
device_path = os.path.join(folder, 'config', 'devices.json')

class Device: 
    def __init__(self, id, gate_id, info_topic_gate, command_topic_gate, scanner_id, info_topic_scanner, command_topic_scanner, timestamp = None):
        self.id = id
        self.gate_id = gate_id
        self.info_topic_gate = info_topic_gate
        self.command_topic_gate = command_topic_gate
        self.scanner_id = scanner_id
        self.info_topic_scanner = info_topic_scanner
        self.command_topic_scanner = command_topic_scanner
        self.timestamp = timestamp

class Bot:
    def __init__(self, id, info_topic, command_topic):
        self.id = id
        self.info_topic = info_topic
        self.command_topic = command_topic

class DeviceManager:
    def __init__(self):
        self.config = {}
        with open(device_path, 'r') as file:
            try:
                self.config = json.load(file)
            except json.JSONDecodeError:
                pass
            
        self.entrance1 = Device(self.config['devices']['entrance1']['id'],
                                    self.config['devices']['entrance1']['gate_id'],
                                    self.config['devices']['entrance1']['info_topic_gate'],
                                    self.config['devices']['entrance1']['command_topic_gate'],
                                    self.config['devices']['entrance1']['scanner_id'],
                                    self.config['devices']['entrance1']['info_topic_scanner'],
                                    self.config['devices']['entrance1']['command_topic_scanner'])
        self.entrance2 = Device(self.config['devices']['entrance2']['id'],
                                    self.config['devices']['entrance2']['gate_id'],
                                    self.config['devices']['entrance2']['info_topic_gate'],
                                    self.config['devices']['entrance2']['command_topic_gate'],
                                    self.config['devices']['entrance2']['scanner_id'],
                                    self.config['devices']['entrance2']['info_topic_scanner'],
                                    self.config['devices']['entrance2']['command_topic_scanner'])
        self.exit1 = Device(self.config['devices']['exit1']['id'],
                                    self.config['devices']['exit1']['gate_id'],
                                    self.config['devices']['exit1']['info_topic_gate'],
                                    self.config['devices']['exit1']['command_topic_gate'],
                                    self.config['devices']['exit1']['scanner_id'],
                                    self.config['devices']['exit1']['info_topic_scanner'],
                                    self.config['devices']['exit1']['command_topic_scanner'])
        self.exit2 = Device(self.config['devices']['exit2']['id'],
                                    self.config['devices']['exit2']['gate_id'],
                                    self.config['devices']['exit2']['info_topic_gate'],
                                    self.config['devices']['exit2']['command_topic_gate'],
                                    self.config['devices']['exit2']['scanner_id'],
                                    self.config['devices']['exit2']['info_topic_scanner'],
                                    self.config['devices']['exit2']['command_topic_scanner'])
        self.bot = Bot(self.config['devices']['bot']['id'],
                        self.config['devices']['bot']['info_topic'],
                        self.config['devices']['bot']['command_topic'])
