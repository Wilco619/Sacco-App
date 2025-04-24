from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from django.utils import timezone


class FinancialPeriod(models.Model):
    """
    Model representing financial periods for accounting and reporting
    """
    STATUS_CHOICES = (
        ('UPCOMING', 'Upcoming'),
        ('ACTIVE', 'Active'),
        ('CLOSED', 'Closed'),
    )
    
    period_name = models.CharField(_('Period Name'), max_length=100)
    start_date = models.DateField(_('Start Date'))
    end_date = models.DateField(_('End Date'))
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='UPCOMING')
    description = models.TextField(_('Description'), blank=True, null=True)
    closed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='closed_periods'
    )
    closed_at = models.DateTimeField(_('Closed At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Financial Period')
        verbose_name_plural = _('Financial Periods')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.period_name} ({self.start_date} - {self.end_date})"


class Member(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('withdrawn', 'Withdrawn')
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    full_name = models.CharField(_('Full Name'), max_length=100)
    id_number = models.CharField(_('ID Number'), max_length=20, unique=True)
    phone_number = models.CharField(_('Phone Number'), max_length=15)
    email = models.EmailField(_('Email Address'))
    registration_date = models.DateField(_('Registration Date'), default=timezone.now)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='pending')
    group = models.ForeignKey('MemberGroup', on_delete=models.SET_NULL, null=True, blank=True)
    total_shares = models.DecimalField(_('Total Shares'), max_digits=12, decimal_places=2, default=0)
    registration_paid = models.BooleanField(_('Registration Paid'), default=False)

    def __str__(self):
        return self.full_name

    @property
    def needs_registration_payment(self):
        return not self.registration_paid


class Savings(models.Model):
    """Model for member savings"""
    TYPE_CHOICES = (
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal')
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='savings')
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    date = models.DateTimeField(_('Transaction Date'), default=timezone.now)
    type = models.CharField(_('Transaction Type'), max_length=10, choices=TYPE_CHOICES)
    description = models.TextField(_('Description'), blank=True)

    class Meta:
        verbose_name_plural = 'Savings'


class Share(models.Model):
    """Model for member shares"""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='member_shares')
    number_of_shares = models.PositiveIntegerField(_('Number of Shares'))
    purchase_date = models.DateField(_('Purchase Date'), default=timezone.now)
    unit_price = models.DecimalField(_('Unit Price'), max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, decimal_places=2)

    def save(self, *args, **kwargs):
        self.total_amount = self.number_of_shares * self.unit_price
        super().save(*args, **kwargs)


class Dividend(models.Model):
    """Model for member dividends"""
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    )

    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='dividends')
    year = models.PositiveIntegerField(_('Year'))
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    payment_status = models.CharField(_('Payment Status'), max_length=10, 
                                    choices=PAYMENT_STATUS_CHOICES, default='pending')
    calculation_date = models.DateTimeField(_('Calculation Date'), auto_now_add=True)
    payment_date = models.DateTimeField(_('Payment Date'), null=True, blank=True)


class MemberGroup(models.Model):
    """Model for organizing members into groups"""
    name = models.CharField(_('Group Name'), max_length=100, unique=True)
    description = models.TextField(_('Description'), blank=True)
    created_date = models.DateTimeField(_('Created Date'), auto_now_add=True)

    def __str__(self):
        return self.name


class FeeType(models.Model):
    """
    Model representing different types of fees charged by the SACCO
    """
    CALCULATION_METHOD_CHOICES = (
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'),
        ('TIERED', 'Tiered'),
    )
    
    APPLICATION_FREQUENCY_CHOICES = (
        ('ONE_TIME', 'One Time'),
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
        ('ANNUALLY', 'Annually'),
        ('ON_EVENT', 'On Event'),
    )
    
    name = models.CharField(_('Fee Name'), max_length=50)
    description = models.TextField(_('Description'))
    calculation_method = models.CharField(_('Calculation Method'), max_length=10, choices=CALCULATION_METHOD_CHOICES)
    rate_or_amount = models.DecimalField(_('Rate (%) or Amount'), max_digits=8, decimal_places=2)
    minimum_amount = models.DecimalField(_('Minimum Amount'), max_digits=8, decimal_places=2, default=0.00)
    maximum_amount = models.DecimalField(_('Maximum Amount'), max_digits=8, decimal_places=2, null=True, blank=True)
    application_frequency = models.CharField(_('Application Frequency'), max_length=10, choices=APPLICATION_FREQUENCY_CHOICES)
    active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('Fee Type')
        verbose_name_plural = _('Fee Types')
    
    def __str__(self):
        return self.name


class Fee(models.Model):
    """
    Model representing fees charged to members
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PAID', 'Paid'),
        ('WAIVED', 'Waived'),
    )
    
    fee_type = models.ForeignKey(FeeType, on_delete=models.PROTECT, related_name='charged_fees')
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='fees')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    date_charged = models.DateTimeField(_('Date Charged'), default=timezone.now)
    due_date = models.DateField(_('Due Date'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True, null=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='PENDING')
    date_paid = models.DateTimeField(_('Date Paid'), null=True, blank=True)
    waived = models.BooleanField(_('Waived'), default=False)
    waiver_reason = models.TextField(_('Waiver Reason'), blank=True, null=True)
    waived_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='waived_fees'
    )
    
    class Meta:
        verbose_name = _('Fee')
        verbose_name_plural = _('Fees')
    
    def __str__(self):
        return f"{self.fee_type.name} - {self.member.get_full_name()} - {self.amount}"


class MembershipFee(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='membership_fees')
    fee_type = models.CharField(_('Fee Type'), max_length=20)
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(_('Payment Date'), auto_now_add=True)
    mpesa_receipt = models.CharField(_('M-Pesa Receipt'), max_length=20, null=True, blank=True)
    checkout_request_id = models.CharField(_('Checkout Request ID'), max_length=100, null=True, blank=True)
    is_initial_payment = models.BooleanField(_('Is Initial Payment'), default=False)

    class Meta:
        verbose_name = 'Membership Fee'
        verbose_name_plural = 'Membership Fees'
        ordering = ['-payment_date']

    def __str__(self):
        return f"{self.member.full_name} - {self.fee_type} - {self.amount}"


class Profit(models.Model):
    """Model for tracking SACCO profits from various sources"""
    SOURCE_CHOICES = (
        ('REGISTRATION', 'Registration Fee'),
        ('LOAN_INTEREST', 'Loan Interest'),
        ('PENALTIES', 'Penalties'),
        ('OTHER', 'Other Sources')
    )

    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    source = models.CharField(_('Profit Source'), max_length=20, choices=SOURCE_CHOICES)
    date_recorded = models.DateTimeField(_('Date Recorded'), default=timezone.now)
    description = models.TextField(_('Description'), blank=True)
    reference_id = models.CharField(_('Reference ID'), max_length=100, blank=True, null=True)
    member = models.ForeignKey(
        Member, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='related_profits'
    )
    financial_period = models.ForeignKey(
        FinancialPeriod,
        on_delete=models.PROTECT,
        related_name='profits',
        null=True
    )

    class Meta:
        verbose_name = 'Profit'
        verbose_name_plural = 'Profits'
        ordering = ['-date_recorded']

    def __str__(self):
        return f"{self.source} - {self.amount} - {self.date_recorded.date()}"