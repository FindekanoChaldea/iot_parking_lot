from utils import PaymentMethod as Method, PaymentStatus as Status

class Payment:
    def __init__(self, plate_license, amount, method, time, currency='euro'):
        self.plate_license = plate_license
        self.amount = amount
        self.paymentMethod = method
        self.time = time
        self.currency = currency
        self.status = Status.PENDING
    
    def add_method(self, method):
        if method in [Method.MACHINE, Method.ONLINE]:
            self.paymentMethod = method
        else:
            raise ValueError("Invalid payment method. Use 'machine' or 'online'.")
    
    def paid(self):
        self.status = Status.COMPLETED
        
    