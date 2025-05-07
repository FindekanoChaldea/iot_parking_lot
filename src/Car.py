from datetime import datetime
from Payment import Payment
from utils import CarStatus as Status, FileManager
from thingspeak_upload import upload_record

class Car:
    PAID_CARS_FILE = 'tests/paid_cars.json'
    PARKINGS_FILE = 'data/parkings.json'
    BOOKINGS_FILE = 'data/bookings.json'
      
    def __init__(self, plate_license, entry_time = None, expecting_time = None):
        self.plate_license = plate_license
        self.entry_time = entry_time
        if entry_time:
            self.status = Status.ENTERED
        else:
            self.status = Status.BOOKED
            self.expecting_time = expecting_time
        self.start_time = entry_time
        self.total_payment = 0.0
        self.exit_time = None
        self.payment_time = None
        self.fileManager = FileManager()
        
    def book(self):
        path = self.fileManager.abpath(self.BOOKINGS_FILE)
        self.save(path)
        
    def enter(self, entry_time):
        self.entry_time = entry_time
        self.status = Status.ENTERED
        
    def is_expired(self):
        if (datetime.now() - self.expecting_time).seconds/60 > 20:
            path = self.fileManager.abpath(self.BOOKINGS_FILE)
            self.fileManager.find_and_delete(path, self.plate_license)
            return True
        else:
            return False
    def cancel(self):
        path = self.fileManager.abpath(self.BOOKINGS_FILE)
        self.fileManager.find_and_delete(path, self.plate_license)
    
    def check(self, amount, payment_method, payment_time):
        self.payment = Payment(amount, payment_method, payment_time)
        self.status = Status.CHECKED
    
    def failPay(self):
        del self.payment
        self.status = Status.CHARGED
       
    def pay(self):
        boolean = self.payment.pay()
        self.start_time = self.payment.time
        self.payment_time = self.payment.time
        self.total_payment += self.payment.amount
        self.payment.pay()
        del self.payment
        self.status = Status.PAID
        
        # this is just for the exit simulation!!!!!
        path = self.fileManager.abpath(self.PAID_CARS_FILE)
        self.save(path)
        
        return boolean
        
    def exit(self, exit_time):
        self.exit_time = exit_time
        path = self.fileManager.abpath(self.PARKINGS_FILE)
        self.save(path)
        self.status == Status.EXITED
    
    def save(self, file_path):
        field = {
            f'{self.plate_license}': 
                {
                'plate_license': f'{self.plate_license}',
                'entry_time': datetime.strftime(self.entry_time, "%Y-%m-%d %H:%M:%S") if self.entry_time else None,
                'payment_time': datetime.strftime(self.payment_time, "%Y-%m-%d %H:%M:%S") if self.payment_time else None,
                'exit_time': datetime.strftime(self.exit_time, "%Y-%m-%d %H:%M:%S") if self.exit_time else None,
                'total_payment': f'{self.total_payment}',
            }
        }
        self.fileManager.add_fields(file_path, field)
        
        upload_record(
            api_key='G0BK8P0ST9KHYR7H',
            plate_license=self.plate_license,
            entry_time=field[self.plate_license]['entry_time'],
            payment_time=field[self.plate_license]['payment_time'],
            exit_time=field[self.plate_license]['exit_time'],
            total_payment=field[self.plate_license]['total_payment']
        )

    
