# Shared logic like JSON parsing, data formatting etc.
# Searching for similar codes onling.
import os
import json

class CarStatus:
    BOOKED = 'booked'
    ENTERED = 'entered'
    CHARGED = 'charged'
    CHECKED = 'checked'
    PAID = 'paid'
    EXITED = 'exited'

class ScannerStatus:
    STANDBY = 'standby'
    SCANNED = 'scanned'

class GateStatus:
    CLOSE = 'close'
    OPEN = 'open'

class PaymentMethod:
    MACHINE = 'machine'
    ONLINE = 'online'

class PaymentStatus:
    PENDING = 'pending'
    COMPLETED = 'completed'
    FAILED = 'failed'

class FileManager:    
    def __init__(self):
        pass
    
    def abpath(self, relative_path):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(script_dir, relative_path)
        
    def add_fields(self, file_path, new_fields):
        # Step 1: Check if the file exists
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist!")
            return
        # Step 2: Load the old data
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        # Step 3: Update the old data with new fields
        data.update(new_fields)
        # Step 4: Save it back
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

        print(f"Updated {file_path} with new fields!")
    
    
    def find_and_delete(self,file_path, plate_license):
        # Step 1: Check if the file exists
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist!")
            return False
        # Step 2: Load the old data
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        # Step 3: Delete the specified field and save the file
        if plate_license in data.keys():
            del data[plate_license]
            print(f"Deleted {plate_license} from {file_path}")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            return True
        else:
            print(f"{plate_license} not found in {file_path}")
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            return False
        
    def read_json(self, file_path):
        # Step 1: Check if the file exists
        if not os.path.exists(file_path):
            print(f"{file_path} does not exist!")
            return {}
        # Step 2: Load the data from the file
        with open(file_path, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
        return data