import json
import Toll
from datetime import datetime
from utils import CarStatus as Status, FileManager

class Car:
        
    def __init__(self, plate_license, entry_time = None, expecting_time = None):
        self.plate_license = plate_license
        if entry_time:
            self.entry_time = entry_time
            self.status = Status.CHECKED
        else:
            self.status = Status.BOOKED
            self.expecting_time = expecting_time
        self.start_time = entry_time
        self.total_payment = 0.0
    
    def enter(self, entry_time):
        self.entry_time = entry_time
        
    def is_expired(self):
        if (datetime.now() - self.expecting_time).seconds/60 > 20:
            return True
        else:
            return False
        
    def pay(self, payment_time):
        self.payment_time = payment_time
        toll = Toll(self.plate_license, self.start_time, payment_time)
        payment = toll.calculate_price()
        self.total_payment += payment
        self.status = Status.PAID
        
    def exit(self, exit_time):
        self.exit_time = exit_time
        if self.status == Status.PAID:
            if (self.exit_time - self.payment_time).seconds/60 <= 20:
                self.openexitGate()
                self.status = Status.EXITED
            else: ## stay more than 20 minutes after payment, need to pay more
                # print("stay more than 20 minutes after payment, need to pay more")
                self.start_time = self.payment_time
        else:
            # print("need to pay before exit")
            pass        
    
    def save(self, file_path):
        fileManager = FileManager()
        field = {
            f'{self.plate_license}': 
                {
                'plate_license': self.plate_license,
                'entry_time': self.entry_time,
                'payment_time': self.payment_time,
                'exit_time': self.exit_time,
                'total_payment': self.total_payment,
            }
        }
        fileManager.add_fields(file_path, field)

    
