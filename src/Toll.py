import math

class Toll:
    def __init__(self, plate_license, start_time, payment_time):
        self.plate_license = plate_license
        self.start_time = start_time
        self.payment_time = payment_time

    def calculate_price(self):
        # free if less than 20 minutes, more than 20 minutes will be charged by one hour
        # for simulation, we use 20 seconds instad of minutes, 1 minute instead of 1 hour
        if (self.payment_time - self.start_time).seconds > 20:
            return 1.50 * math.ceil((self.payment_time - self.start_time).seconds / 60)
        else:
            return 0.0