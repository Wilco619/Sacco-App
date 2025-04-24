from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from accounts.models import ShareCapital
from decimal import Decimal
from django.utils import timezone
import logging
from .handlers.base import BasePaymentHandler

logger = logging.getLogger(__name__)

class SharePaymentHandler(BasePaymentHandler):
    def process_payment(self, mpesa_transaction, **kwargs):
        """Handle share payment processing"""
        try:
            with transaction.atomic():
                user = mpesa_transaction.user
                if not user:
                    raise ValueError("User is required for share purchase")

                # Get or create ShareCapital record
                share_capital, created = ShareCapital.objects.get_or_create(
                    member=user,
                    defaults={
                        'number_of_shares': 0,
                        'value_per_share': Decimal('1000.00'),
                        'total_value': Decimal('0.00'),
                        'status': 'ACTIVE',
                        'certificate_number': f"SHR{user.id_number}{timezone.now().strftime('%Y%m')}"
                    }
                )

                # Calculate new shares
                amount = mpesa_transaction.amount
                new_shares = int(amount / 1000)  # Each share is 1000 KSH

                # Update share capital
                share_capital.number_of_shares += new_shares
                share_capital.total_value += amount

                # Update monthly contribution if this amount is higher
                if amount > share_capital.monthly_contribution:
                    share_capital.monthly_contribution = amount

                share_capital.last_payment_date = timezone.now().date()
                share_capital.save()

                self.log_payment(
                    f"Updated share capital for user {user.id_number}",
                    shares_added=new_shares,
                    total_shares=share_capital.number_of_shares
                )

                return {
                    'success': True,
                    'shares_purchased': new_shares,
                    'total_shares': share_capital.number_of_shares,
                    'total_value': str(share_capital.total_value),
                    'monthly_contribution': str(share_capital.monthly_contribution),
                    'transaction_date': timezone.now().isoformat()
                }

        except Exception as e:
            self.log_payment(f"Share payment failed: {str(e)}", level='error')
            logger.error(f"Share payment error: {str(e)}", exc_info=True)
            raise

    def get_payment_status(self, transaction):
        status = super().get_payment_status(transaction)
        try:
            share_capital = ShareCapital.objects.get(member=transaction.user)
            status.update({
                'total_shares': share_capital.number_of_shares,
                'total_value': str(share_capital.total_value),
                'last_contribution_date': share_capital.last_payment_date.isoformat() if share_capital.last_payment_date else None
            })
        except ShareCapital.DoesNotExist:
            status['shares_status'] = 'no_shares'
        return status