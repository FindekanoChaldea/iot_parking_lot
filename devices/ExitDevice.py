# Check payment and allow exit

class ExitDevice:

    def scan_plate(self, plate_license, time):
        # Simulate scanning a license plate
        return plate_license, time
    
    def open_gate(self, plate_license, time):
        # Simulate opening the gate
        ## send msg to center to confirm the exit
        return plate_license, time