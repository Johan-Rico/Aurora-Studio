from ..domain.interfaces import PaymentProcessor

class BankProcessor(PaymentProcessor):
    def pay(self, amount):
        print(f"Pagado: ${amount}")
        return True

class MockPaymentProcessor(PaymentProcessor):
    def pay(self, amount):
        print(f"MOCK PAGADO: ${amount}")
        return True