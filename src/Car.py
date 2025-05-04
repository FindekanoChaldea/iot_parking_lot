from datetime import datetime
import Payment
from utils import CarStatus as Status, FileManager

class Car:
        
    def __init__(self, plate_license, entry_time = None, expecting_time = None):
        self.plate_license = plate_license
        self.entry_time = entry_time
        if entry_time:
            self.status = Status.ENTERED
        else:
            self.status = Status.BOOKED
            self.expecting_time = expecting_time
        self.start_time = entry_time
        self.total_payment = None
    
    def enter(self, entry_time):
        self.entry_time = entry_time
        self.status = Status.ENTERED
        
    def is_expired(self):
        if (datetime.now() - self.expecting_time).seconds/60 > 20:
            fileManager = FileManager()
            fileManager.find_and_delete('../data/bookings.json', self.plate_license)
            return True
        else:
            return False
    
    def check(self, amount, payment_method, payment_time):
        self.payment = Payment(amount, payment_method, payment_time)
        self.status = Status.CHECKED
    
    def failPay(self):
        del self.payment
        self.status = Status.CHARGED
       
    def pay(self):
        boolean = self.payment.pay()
        self.start_time = self.payment.time
        self.total_payment += self.payment.amount
        self.payment.pay()
        del self.payment
        self.status = Status.PAID
        return boolean
        
    def exit(self, exit_time):
        self.exit_time = exit_time
        self.status == Status.EXITED
    
    def save(self, file_path):
        fileManager = FileManager()
        field = {
            f'{self.plate_license}': 
                {
                'plate_license': self.plate_license,
                'entry_time': datetime.strptime(self.entry_time, "%Y-%m-%d %H:%M:%S"),
                'payment_time': datetime.strptime(self.payment_time, "%Y-%m-%d %H:%M:%S"),
                'exit_time': datetime.strptime(self.exit_time, "%Y-%m-%d %H:%M:%S"),
                'total_payment': self.total_payment,
            }
        }
        fileManager.add_fields(file_path, field)

    
