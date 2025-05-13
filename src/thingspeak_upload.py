
import requests

class ThingSpeakClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.url = "https://api.thingspeak.com/update"

    def upload_record(self, plate_license, entry_time, payment_time, exit_time, total_payment):
        payload = {
            "api_key": self.api_key,
            "field1": plate_license,
            "field2": entry_time,
            "field3": payment_time,
            "field4": exit_time,
            "field5": total_payment
        }
        # Send the data to ThingSpeak           
        response = requests.post(self.url, data=payload)
        if response.status_code == 200 and response.text != '0':
            print(f"ThingSpeak uoload successfully，Entry ID: {response.text}")
        else:
            print(f"Upload failed: {response.status_code}，response text: {response.text}")
