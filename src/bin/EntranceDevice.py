# Simulate gate open + assign TIC

class EntranceDevice:
    
    class Status:
        STATUS_STANDBY = 0
        STATUS_CHECKING = 1
        STATUS_APPROVE = 2
        STATUS_REJECT = 3

    def __init__(self):
        self.is_on = False

    def turn_on(self):
        self.is_on = True
        self.status = EntranceDevice.Status.STATUS_STANDBY
        
    def get_status(self):
        return self.status

    def scan_plate(self, plate_license):
        # Simulate scanning a license plate
        self.plate_license = plate_license
        self.status = EntranceDevice.Status.STATUS_CHECKING
    
    def open_gate(self, plate_license, time):
        # Simulate opening the gate
        ## send msg to center to confirm the entry
        self.plate_license, self.time = plate_license, time
    
