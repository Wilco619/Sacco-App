from decimal import Decimal
from django.db import transaction, models
from django.utils import timezone
from .models import Member, MembershipFee, Share

class MembershipService:
    MEMBERSHIP_FEE = Decimal('1000.00')
    WELFARE_FEE = Decimal('400.00')
    MIN_SHARE_AMOUNT = Decimal('1000.00')

    @staticmethod
    @transaction.atomic
    def register_member(user_data):
        """Register a new member with pending status"""
        member = Member.objects.create(**user_data, status='pending')
        return member

    @staticmethod
    @transaction.atomic
    def process_initial_payments(member, payment_data):
        """Process initial membership payments"""
        total_required = MembershipService.MEMBERSHIP_FEE + \
                        MembershipService.WELFARE_FEE + \
                        MembershipService.MIN_SHARE_AMOUNT
        
        if payment_data['amount'] < total_required:
            raise ValueError("Insufficient payment amount for registration")

        # Record membership fee
        MembershipFee.objects.create(
            member=member,
            fee_type='membership',
            amount=MembershipService.MEMBERSHIP_FEE,
            is_initial_payment=True,
            receipt_number=payment_data['receipt_number']
        )
        member.membership_fee_paid = True

        # Record welfare fee
        MembershipFee.objects.create(
            member=member,
            fee_type='welfare',
            amount=MembershipService.WELFARE_FEE,
            is_initial_payment=True,
            receipt_number=f"{payment_data['receipt_number']}-W"
        )
        member.initial_welfare_paid = True
        member.last_welfare_payment = timezone.now().date()

        # Record initial share
        Share.objects.create(
            member=member,
            number_of_shares=1,
            unit_price=MembershipService.MIN_SHARE_AMOUNT,
            total_amount=MembershipService.MIN_SHARE_AMOUNT
        )
        member.initial_share_paid = True
        member.monthly_share_amount = MembershipService.MIN_SHARE_AMOUNT

        # Activate membership
        member.activate_membership()
        return member

    @staticmethod
    def process_monthly_share(member, amount, receipt_number):
        """Process monthly share payment with balance check"""
        expected_amount = member.monthly_share_amount
        
        if amount != expected_amount:
            # Calculate any backdated amounts needed
            current_shares = Share.objects.filter(member=member).aggregate(
                total=models.Sum('total_amount'))['total'] or 0
            
            expected_total = member.monthly_share_amount * \
                           member.get_membership_months()
            
            if current_shares < expected_total:
                raise ValueError(
                    f"Please clear previous month's share balance. "
                    f"Expected: {expected_total}, Current: {current_shares}"
                )

        Share.objects.create(
            member=member,
            number_of_shares=amount/MembershipService.MIN_SHARE_AMOUNT,
            unit_price=MembershipService.MIN_SHARE_AMOUNT,
            total_amount=amount
        )
        return True

    @staticmethod
    def process_monthly_welfare(member, receipt_number):
        """Process monthly welfare fee"""
        if member.last_welfare_payment:
            last_payment = member.last_welfare_payment
            today = timezone.now().date()
            
            if last_payment.month == today.month and last_payment.year == today.year:
                raise ValueError("Welfare fee already paid for this month")

        MembershipFee.objects.create(
            member=member,
            fee_type='welfare',
            amount=MembershipService.WELFARE_FEE,
            receipt_number=receipt_number
        )
        member.last_welfare_payment = timezone.now().date()
        member.save()
        return True