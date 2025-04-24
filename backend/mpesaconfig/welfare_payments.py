from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from django.utils import timezone
from welfare.models import WelfareContribution, WelfareFund
from mpesaconfig.models import Transaction
from .handlers.base import BasePaymentHandler
import logging

logger = logging.getLogger(__name__)

class WelfarePaymentHandler(BasePaymentHandler):
    def process_payment(self, mpesa_transaction, **kwargs):
        """Handle welfare payment processing"""
        try:
            with transaction.atomic():
                user = mpesa_transaction.user
                if not user:
                    raise ValueError("User is required for welfare payment")

                # Get active welfare fund
                welfare_fund = WelfareFund.objects.filter(status='ACTIVE').first()
                if not welfare_fund:
                    raise ValueError("No active welfare fund found")

                # Validate amount
                amount = mpesa_transaction.amount
                if amount != welfare_fund.minimum_contribution:
                    raise ValueError(f"Invalid amount. Required amount is {welfare_fund.minimum_contribution}")

                # Create welfare contribution
                contribution = WelfareContribution.objects.create(
                    member=user,
                    welfare_fund=welfare_fund,
                    amount=amount,
                    payment_method='MPESA',
                    reference_number=mpesa_transaction.checkout_request_id,
                    receipt_number=mpesa_transaction.mpesa_code,
                    status='CONFIRMED',
                    contribution_date=timezone.now()
                )

                # Update welfare fund total
                welfare_fund.total_amount += amount
                welfare_fund.save()

                self.log_payment(
                    f"Welfare contribution recorded for user {user.id_number}",
                    contribution_id=contribution.id,
                    amount=str(amount)
                )

                return {
                    'success': True,
                    'contribution_id': contribution.id,
                    'amount': str(contribution.amount),
                    'fund_name': welfare_fund.name,
                    'contribution_date': contribution.contribution_date.isoformat(),
                    'status': contribution.status
                }

        except Exception as e:
            self.log_payment(f"Welfare payment failed: {str(e)}", level='error')
            logger.error(f"Welfare payment error: {str(e)}", exc_info=True)
            raise

    def get_payment_status(self, transaction):
        status = super().get_payment_status(transaction)
        try:
            # Get user from transaction (handle both dict and object)
            user = (
                transaction.get('user')
                if isinstance(transaction, dict)
                else getattr(transaction, 'user', None)
            )

            if not user:
                raise ValueError("User is required for welfare status")

            # Get latest contribution
            latest_contribution = WelfareContribution.objects.filter(
                member=user
            ).order_by('-contribution_date').first()

            if latest_contribution:
                current_month = timezone.now()
                has_contributed = WelfareContribution.objects.filter(
                    member=user,
                    contribution_date__year=current_month.year,
                    contribution_date__month=current_month.month,
                    status='CONFIRMED'
                ).exists()

                status.update({
                    'last_contribution_date': latest_contribution.contribution_date.isoformat(),
                    'last_contribution_amount': str(latest_contribution.amount),
                    'contribution_status': latest_contribution.status,
                    'has_contributed_this_month': has_contributed,
                    'fund_name': latest_contribution.welfare_fund.name
                })
            else:
                status['contribution_status'] = 'no_contributions'

            return status

        except Exception as e:
            logger.error(f"Failed to get welfare status: {str(e)}", exc_info=True)
            return {
                'success': False,
                'message': str(e),
                'contribution_status': 'error'
            }

    def initiate_payment(self, phone, amount, user, **kwargs):
        """Initialize welfare payment"""
        try:
            # Validate active welfare fund exists
            welfare_fund = WelfareFund.objects.filter(status='ACTIVE').first()
            if not welfare_fund:
                raise ValueError("No active welfare fund found")

            # Check for existing contribution this month
            current_month = timezone.now()
            existing_contribution = WelfareContribution.objects.filter(
                member=user,
                contribution_date__year=current_month.year,
                contribution_date__month=current_month.month,
                status='CONFIRMED'
            ).exists()

            if existing_contribution:
                raise ValueError("Already contributed for this month")

            # Create M-Pesa transaction
            with transaction.atomic():
                mpesa_transaction = Transaction.objects.create(
                    user=user,
                    phone_number=phone,
                    amount=amount,
                    payment_type='WELFARE',
                    status='PENDING'
                )

                # Initiate M-Pesa payment using parent class method
                payment_response = super().initiate_mpesa_payment(
                    phone=phone,
                    amount=amount,
                    transaction=mpesa_transaction
                )

                if not payment_response.get('success'):
                    mpesa_transaction.status = 'FAILED'
                    mpesa_transaction.save()
                    raise ValueError(payment_response.get('message'))

                return {
                    'success': True,
                    'message': 'Payment initiated successfully',
                    'checkoutRequestId': payment_response['checkoutRequestId']
                }

        except Exception as e:
            self.log_payment(f"Payment initiation failed: {str(e)}", level='error')
            raise ValueError(str(e))

    def process_successful_payment(self, transaction):
        """Process successful welfare payment"""
        try:
            with transaction.atomic():
                welfare_fund = WelfareFund.objects.filter(status='ACTIVE').first()
                if not welfare_fund:
                    raise ValueError("No active welfare fund found")

                # Create contribution record
                contribution = WelfareContribution.objects.create(
                    member=transaction.user,
                    welfare_fund=welfare_fund,
                    amount=transaction.amount,
                    payment_method='MPESA',
                    reference_number=transaction.checkout_request_id,
                    receipt_number=transaction.mpesa_code,
                    status='CONFIRMED',
                    contribution_date=timezone.now()
                )

                # Update welfare fund total
                welfare_fund.total_amount += transaction.amount
                welfare_fund.save()

                # Update transaction status
                transaction.status = 'COMPLETED'
                transaction.save()

                return {
                    'success': True,
                    'contribution_id': contribution.id,
                    'amount': str(contribution.amount),
                    'fund_name': welfare_fund.name,
                    'contribution_date': contribution.contribution_date.isoformat()
                }

        except Exception as e:
            logger.error(f"Failed to process successful payment: {str(e)}")
            raise