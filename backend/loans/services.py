from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from loans.models import Loan, LoanApproval, Penalty

class LoanProcessor:
    @staticmethod
    def calculate_due_date(loan):
        if not loan.disbursement_date:
            return None
            
        months_map = {
            'MONTHLY': 1,
            'TWO_MONTHS': 2,
            'THREE_MONTHS': 3,
            'FOUR_MONTHS': 4
        }
        
        months = months_map.get(loan.repayment_period, 1)
        return loan.disbursement_date + timedelta(days=30 * months)

    @staticmethod
    def process_loan_approval(loan, admin):
        with transaction.atomic():
            # Remove admin from pending approvals
            loan.pending_approvals.remove(admin)
            
            # Create approval record
            LoanApproval.objects.create(
                loan=loan,
                admin=admin,
                approved=True
            )
            
            # Check if all approvals are complete
            if loan.pending_approvals.count() == 0:
                loan.status = 'APPROVED'
                loan.approval_date = timezone.now()
                loan.approvals_completed = True
                loan.save()

    @staticmethod
    def check_for_penalties():
        """Daily job to check for late payments"""
        current_date = timezone.now().date()
        
        overdue_loans = Loan.objects.filter(
            status='ACTIVE',
            due_date__lt=current_date,
            penalty_amount=0  # Only apply penalty once
        )
        
        for loan in overdue_loans:
            loan.penalty_amount = Decimal('500.00')
            loan.save()
            
            # Create penalty record
            Penalty.objects.create(
                loan=loan,
                amount=Decimal('500.00'),
                reason='Late payment penalty'
            )