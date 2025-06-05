import json
import os

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config/settings.json')
DEVICES_PATH = os.path.join(BASE_DIR, 'config/devices.json')

class ParkingManager:
    def __init__(self):
        self.load_settings()
        self.devices = {}  # now structured as {lot_id: {device_id: {...}}}

    def load_settings(self):
        with open(CONFIG_PATH, 'r') as f:
            self.settings = json.load(f)

    def register_lot(self, lot_id):
        if lot_id not in self.devices:
            self.devices[lot_id] = {}

    def register_device(self, lot_id, device_id, device_type, location):
        self.register_lot(lot_id)
        topic_base = f"polito_parking/{lot_id}/{device_type}/{device_id}"
        self.devices[lot_id][device_id] = {
            "id": device_id,
            "type": device_type,
            "location": location,
            "status": "online",
            "topics": {
                "info": f"{topic_base}/info",
                "command": f"{topic_base}/command"
            }
        }
        return self.devices[lot_id][device_id]["topics"]

    def get_device_status(self, lot_id=None):
        if lot_id:
            return [{"id": d["id"], "status": d.get("status", "unknown")} for d in self.devices.get(lot_id, {}).values()]
        else:
            result = []
            for lot, lot_devices in self.devices.items():
                for d in lot_devices.values():
                    result.append({"lot": lot, "id": d["id"], "status": d.get("status", "unknown")})
            return result

    def get_config(self):
        return self.settings

    def update_parking_capacity(self, new_capacity):
        self.settings["total_slots"] = new_capacity
        with open(CONFIG_PATH, 'w') as f:
            json.dump(self.settings, f, indent=2)
        return self.settings
