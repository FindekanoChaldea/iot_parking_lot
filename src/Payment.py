from utils import PaymentMethod as Method, PaymentStatus as Status
import time

class Payment:
    def __init__(self, amount, method, time, currency='euro'):
        self.amount = amount
        self.paymentMethod = method
        self.time = time
        self.currency = currency
        self.status = Status.PENDING
    
    def pay(self):
        if self.paymentMethod == Method.CARD:
            return self.pay_card()
        
        elif self.paymentMethod == Method.CASH:
            return self.pay_cash()
    
    def pay_card(self):
        # Simulate card payment processing
        time.sleep(2)
        self.status = Status.COMPLETED
        return True
    
    def pay_cash(self):
        # Simulate cash payment processing
        time.sleep(2)
        self.status = Status.COMPLETED
        return True