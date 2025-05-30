import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config/settings.json')
DEVICES_PATH = os.path.join(BASE_DIR, 'config/devices.json')

class ParkingManager:
    def __init__(self):
        self.load_settings()
        self.load_devices()

    def load_settings(self):
        with open(CONFIG_PATH, 'r') as f:
            self.settings = json.load(f)

    def load_devices(self):
        with open(DEVICES_PATH, 'r') as f:
            self.devices = json.load(f)

    def get_device_status(self):
        return [{"id": d["id"], "status": d.get("status", "unknown")} for d in self.devices]

    def get_config(self):
        return self.settings

    def update_parking_capacity(self, new_capacity):
        self.settings["total_slots"] = new_capacity
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.settings, f, indent=2)
        return self.settings
