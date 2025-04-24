from ..registration_payments import RegistrationPaymentHandler
from ..share_payments import SharePaymentHandler
from ..welfare_payments import WelfarePaymentHandler

class PaymentHandlerFactory:
    _handlers = {
        'REGISTRATION': RegistrationPaymentHandler,
        'SHARES': SharePaymentHandler,
        'WELFARE': WelfarePaymentHandler
    }

    @classmethod
    def get_handler(cls, payment_type):
        handler_class = cls._handlers.get(payment_type)
        if not handler_class:
            raise ValueError(f"No handler found for payment type: {payment_type}")
        return handler_class()