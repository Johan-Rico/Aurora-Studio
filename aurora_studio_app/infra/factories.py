import os
from .gateaways import MockPaymentProcessor, BankProcessor

class PaymentFactory:
    @staticmethod
    def get_payment_processor():
        provider = os.getenv('PAYMENT_PROVIDER', 'BANK')

        if provider == 'MOCK':
            return MockPaymentProcessor()
        
        return BankProcessor()