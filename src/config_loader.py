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
        self.MQTT = self.MQTT(self)
        self.CHERRYPY = self.CHERRYPY(self)
        self.telegram_bot_token = self.config['telegram_bot_token']
        
    class MQTT:
        def __init__(self, config_loader):
            self.config_loader = config_loader
            self.broker = config_loader.config['MQTT']['broker']
            self.port = config_loader.config['MQTT']['port']
    
    class CHERRYPY:
        def __init__(self, config_loader):
            self.config_loader = config_loader
            self.host = config_loader.config['CHERRYPY']['host']
            self.port = config_loader.config['CHERRYPY']['port']
            self.catalog_uri = config_loader.config['CHERRYPY']['catalog_uri']
            self.passage_uri = config_loader.config['CHERRYPY']['passage_uri']
            self.lot_uri = config_loader.config['CHERRYPY']['lot_uri']
            
    class Bot:
        def __init__(self, config_loader):
            self.config_loader = config_loader
            self.token = config_loader.telegram_bot_token