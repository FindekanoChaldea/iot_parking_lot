import time
import os
import json
import random
from Scanner import Scanner

client_id = 'ExitScanner1'
broker = "mqtt.eclipseprojects.io"
port = 1883
pub_topic = 'polito_parking/exit/scanner1/info'
sub_topic = 'polito_parking/exit/scanner1/command'
exitScanner1 = Scanner(client_id, broker, port, pub_topic, sub_topic)




# this is for simulate the exit of the cars
path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'paid_cars.json')

while True:
    with open(path, 'r+') as file:
        # Lock the file to prevent access by others
        os.chmod(path, 0o600)  # Set file permissions to be accessible only by the owner
        fields = {}
        # Check if the file is empty
        if os.stat(path).st_size == 0:
            file.seek(0)
            json.dump(fields, file)
            file.truncate()
            os.chmod(path, 0o644)  # Restore file permissions before exiting
            pass
        else :
            fields = json.load(file)
            if not fields:  # Stop the loop if the file is empty
                os.chmod(path, 0o644)  # Restore file permissions before exiting
                pass
            else:
                field = fields.popitem()[1]  # Remove and get the first key-value pair, then take the value
                file.seek(0)  # Move to the beginning of the file
                json.dump(fields, file)  # Write the updated list back to the file
                file.truncate()  # Remove any leftover data
                plate_license = field['plate_license']
                exitScanner1.scan_plate(plate_license)  # Simulate random time intervals
    # Restore file permissions after processing
    os.chmod(path, 0o644)  # Set file permissions back to default
    time.sleep(random.randint(3, 5))