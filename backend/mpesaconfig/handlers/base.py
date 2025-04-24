from abc import ABC, abstractmethod
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class BasePaymentHandler(ABC):
    @abstractmethod
    def process_payment(self, mpesa_transaction, **kwargs):
        pass

    def get_payment_status(self, transaction):
        """Get payment status"""
        try:
            # Handle transaction as either dict or object
            payment_type = (
                transaction.get('payment_type') 
                if isinstance(transaction, dict) 
                else getattr(transaction, 'payment_type', None)
            )

            return {
                'success': True,
                'payment_type': payment_type,
                'status': transaction.get('status') if isinstance(transaction, dict) else transaction.status,
                'amount': str(transaction.get('amount', 0)) if isinstance(transaction, dict) else str(transaction.amount)
            }
        except Exception as e:
            logger.error(f"Error getting payment status: {str(e)}")
            return {
                'success': False,
                'message': 'Failed to get payment status'
            }

    def log_payment(self, message, level='info', **kwargs):
        log_func = getattr(logger, level)
        log_func(f"{self.__class__.__name__}: {message}", extra=kwargs)

    def initiate_mpesa_payment(self, phone, amount, transaction):
        """Base method for initiating M-Pesa payment"""
        try:
            from ..views import MPesaViewSet
            
            # Create MPesa viewset instance
            mpesa_view = MPesaViewSet()
            
            # Initiate STK push using the viewset method
            stk_response = mpesa_view.trigger_stk_push(
                phone=phone,
                amount=amount,
                description=f"Payment for {transaction.payment_type}"
            )
            
            if stk_response.get('ResponseCode') == '0':
                # Update transaction with checkout request ID
                transaction.checkout_request_id = stk_response.get('CheckoutRequestID')
                transaction.save()
                
                return {
                    'success': True,
                    'checkoutRequestId': stk_response.get('CheckoutRequestID'),
                    'message': 'Payment initiated successfully'
                }
            else:
                return {
                    'success': False,
                    'message': stk_response.get('errorMessage', 'Failed to initiate payment')
                }
                
        except Exception as e:
            logger.error(f"Failed to initiate M-Pesa payment: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e)
            }