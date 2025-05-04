# This code is to read JSON config.
import os
import json

folder = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
setting_path = os.path.join(folder, 'config', 'settings.json')

class ConfigLoader:
    def __init__(self):
        self.config = {}
        with open(setting_path, 'r') as file:
            try:
                self.config = json.load(file)
            except json.JSONDecodeError:
                pass
        self.mqtt = self.MQTT(self)
        self.payment_api = self.Payment_api(self)
        
    class MQTT:
        def __init__(self, config_loader):
            self.config_loader = config_loader
            self.broker = config_loader.config['MQTT']['broker']
            self.port = config_loader.config['MQTT']['port']
    
    class Payment_api:
        def __init__(self, config_loader):
            self.config_loader = config_loader
            self.host = config_loader.config['payment_api']['host']
            self.port = config_loader.config['payment_api']['port']
            self.uri = config_loader.config['payment_api']['uri']