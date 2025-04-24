from datetime import timezone
from rest_framework import status
from rest_framework.response import Response
from django.db import transaction
from finance.models import Member, MembershipFee, Profit, FinancialPeriod
from .handlers.base import BasePaymentHandler
import logging

logger = logging.getLogger(__name__)

class RegistrationPaymentHandler(BasePaymentHandler):
    def process_payment(self, mpesa_transaction, **kwargs):
        """Handle registration payment processing"""
        try:
            with transaction.atomic():
                user = mpesa_transaction.user
                if not user:
                    raise ValueError("User is required for registration")

                # Create or update member
                member, created = Member.objects.get_or_create(
                    user=user,
                    defaults={
                        'id_number': mpesa_transaction.id_number or user.id_number,
                        'phone_number': mpesa_transaction.phone_number,
                        'full_name': f"{user.first_name} {user.last_name}",
                        'email': user.email,
                        'status': 'active',
                        'registration_paid': True
                    }
                )

                if not created:
                    member.registration_paid = True
                    member.status = 'active'
                    member.save(update_fields=['registration_paid', 'status'])

                self.log_payment(f"Member status updated: {member.id}")

                # Create membership fee record matching exact model fields
                membership_fee = MembershipFee.objects.create(
                    member=member,
                    fee_type='registration',  # Required field
                    amount=mpesa_transaction.amount,  # Required field
                    mpesa_receipt=mpesa_transaction.mpesa_code,  # Optional
                    checkout_request_id=mpesa_transaction.checkout_request_id,  # Optional
                    is_initial_payment=True  # Default is False
                )

                self.log_payment(f"Membership fee recorded: {membership_fee.id}")

                # Record profit if not already recorded
                if not mpesa_transaction.profit_recorded:
                    profit = Profit.objects.create(
                        amount=mpesa_transaction.amount,
                        source='REGISTRATION',
                        description=f'Registration fee from {member.full_name}',
                        reference_id=mpesa_transaction.mpesa_code,
                        member=member
                    )
                    mpesa_transaction.profit_recorded = True
                    mpesa_transaction.save()
                    
                    self.log_payment(f"Profit recorded: {profit.id}")

                return {
                    'success': True,
                    'registration_completed': True,
                    'member_id': member.id,
                    'status': member.status,
                    'registration_paid': member.registration_paid,
                    'membership_fee_id': membership_fee.id
                }

        except Exception as e:
            self.log_payment(f"Registration payment failed: {str(e)}", level='error')
            logger.error(f"Registration payment error: {str(e)}", exc_info=True)
            raise

    def get_payment_status(self, transaction):
        status = super().get_payment_status(transaction)
        try:
            member = Member.objects.get(user=transaction.user)
            status.update({
                'registration_paid': member.registration_paid,
                'member_status': member.status,
                'registration_date': member.created_at.isoformat() if member.created_at else None
            })
        except Member.DoesNotExist:
            status['member_status'] = 'pending'
        return status