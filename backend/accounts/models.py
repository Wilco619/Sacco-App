from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from django.utils import timezone


class SavingsAccount(models.Model):
    """
    Model representing a member's savings account
    """
    ACCOUNT_TYPE_CHOICES = (
        ('REGULAR', 'Regular Savings'),
        ('FIXED', 'Fixed Deposit'),
        ('JUNIOR', 'Junior Savings'),
        ('RETIREMENT', 'Retirement Savings'),
    )
    
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('DORMANT', 'Dormant'),
        ('CLOSED', 'Closed'),
        ('FROZEN', 'Frozen'),
    )
    
    account_number = models.CharField(_('Account Number'), max_length=20, unique=True)
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='savings_accounts')
    account_type = models.CharField(_('Account Type'), max_length=20, choices=ACCOUNT_TYPE_CHOICES)
    balance = models.DecimalField(_('Current Balance'), max_digits=12, decimal_places=2, default=0.00)
    minimum_balance = models.DecimalField(_('Minimum Balance'), max_digits=12, decimal_places=2, default=0.00)
    date_opened = models.DateTimeField(_('Date Opened'), default=timezone.now)
    date_closed = models.DateTimeField(_('Date Closed'), null=True, blank=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    interest_rate = models.DecimalField(_('Interest Rate (%)'), max_digits=5, decimal_places=2, default=0.00)
    last_interest_calculation = models.DateTimeField(_('Last Interest Calculation'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Savings Account')
        verbose_name_plural = _('Savings Accounts')
    
    def __str__(self):
        return f"{self.account_number} - {self.member.get_full_name()}"


class ShareCapital(models.Model):
    """Model representing a member's share capital in the SACCO"""
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('TRANSFERRED', 'Transferred'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='shares')
    certificate_number = models.CharField(_('Certificate Number'), max_length=20, unique=True)
    number_of_shares = models.PositiveIntegerField(_('Number of Shares'))
    value_per_share = models.DecimalField(_('Value Per Share'), max_digits=10, decimal_places=2)
    total_value = models.DecimalField(_('Total Value'), max_digits=12, decimal_places=2)
    date_purchased = models.DateTimeField(_('Date Purchased'), default=timezone.now)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='ACTIVE')
    monthly_contribution = models.DecimalField(_('Monthly Contribution'), max_digits=12, decimal_places=2, default=0)
    compensation_paid = models.DecimalField(_('Compensation Amount'), max_digits=12, decimal_places=2, default=0)
    last_payment_date = models.DateField(_('Last Payment Date'), null=True)
    
    class Meta:
        verbose_name = _('Share Capital')
        verbose_name_plural = _('Share Capital')
    
    def calculate_compensation_amount(self, new_monthly_amount):
        """Calculate compensation needed when increasing monthly contribution"""
        if not self.last_payment_date:
            return 0
        
        months_since_start = (timezone.now().date() - self.last_payment_date).days // 30
        current_expected = self.monthly_contribution * months_since_start
        new_expected = new_monthly_amount * months_since_start
        return new_expected - current_expected
    
    def update_monthly_contribution(self, new_amount, compensation_paid=0):
        """Update monthly contribution amount and handle compensation"""
        self.monthly_contribution = new_amount
        self.compensation_paid += compensation_paid
        self.save()
    
    def __str__(self):
        return f"Shares: {self.number_of_shares} - {self.member.get_full_name()}"


# class Transaction(models.Model):
#     """
#     Model representing financial transactions in the system
#     """
#     TRANSACTION_TYPE_CHOICES = (
#         ('DEPOSIT', 'Deposit'),
#         ('WITHDRAWAL', 'Withdrawal'),
#         ('TRANSFER', 'Transfer'),
#         ('LOAN_DISBURSEMENT', 'Loan Disbursement'),
#         ('LOAN_REPAYMENT', 'Loan Repayment'),
#         ('INTEREST_EARNED', 'Interest Earned'),
#         ('CHARGE', 'Charge/Fee'),
#         ('DIVIDEND', 'Dividend Payment'),
#         ('SHARE_PURCHASE', 'Share Purchase'),
#         ('SHARE_SALE', 'Share Sale'),
#     )
    
#     STATUS_CHOICES = (
#         ('PENDING', 'Pending'),
#         ('COMPLETED', 'Completed'),
#         ('FAILED', 'Failed'),
#         ('REVERSED', 'Reversed'),
#     )
    
#     transaction_id = models.CharField(_('Transaction ID'), max_length=50, unique=True)
#     account = models.ForeignKey(SavingsAccount, on_delete=models.CASCADE, related_name='transactions', null=True, blank=True)
#     member = models.ForeignKey(
#         'users.CustomUser',
#         on_delete=models.CASCADE,
#         related_name='account_transactions'
#     )
#     transaction_type = models.CharField(_('Transaction Type'), max_length=20, choices=TRANSACTION_TYPE_CHOICES)
#     amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
#     balance_after = models.DecimalField(_('Balance After'), max_digits=12, decimal_places=2)
#     date = models.DateTimeField(_('Transaction Date'), default=timezone.now)
#     description = models.TextField(_('Description'))
#     reference_number = models.CharField(_('Reference Number'), max_length=50, blank=True, null=True)
#     status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='PENDING')
#     processed_by = models.ForeignKey(
#         CustomUser, 
#         on_delete=models.SET_NULL, 
#         null=True, 
#         blank=True, 
#         related_name='processed_transactions'
#     )
    
#     class Meta:
#         verbose_name = _('Transaction')
#         verbose_name_plural = _('Transactions')
#         ordering = ['-date']
    
#     def __str__(self):
#         return f"{self.transaction_id} - {self.transaction_type} - {self.amount}"


class AuditLog(models.Model):
    user = models.ForeignKey('users.CustomUser', on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50)
    model_name = models.CharField(max_length=50)
    object_id = models.CharField(max_length=50)
    changes = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)