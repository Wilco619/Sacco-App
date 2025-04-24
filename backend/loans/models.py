from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from django.utils import timezone
from django.db.models import Sum


class Loan(models.Model):
    """
    Model representing a loan issued to a member
    """
    LOAN_TYPE_CHOICES = (
        ('PERSONAL', 'Personal Loan'),
        ('BUSINESS', 'Business Loan'),
        ('EMERGENCY', 'Emergency Loan'),
        ('EDUCATION', 'Education Loan'),
        ('ASSET', 'Asset Financing'),
    )
    
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
        ('ACTIVE', 'Active'),
        ('FULLY_PAID', 'Fully Paid'),
        ('DEFAULTED', 'Defaulted'),
        ('WRITTEN_OFF', 'Written Off'),
        ('REJECTED', 'Rejected'),
    )
    
    REPAYMENT_FREQUENCY_CHOICES = (
        ('DAILY', 'Daily'),
        ('WEEKLY', 'Weekly'),
        ('MONTHLY', 'Monthly'),
        ('QUARTERLY', 'Quarterly'),
    )
    
    REPAYMENT_PERIOD_CHOICES = (
        ('MONTHLY', 'Monthly'),
        ('TWO_MONTHS', 'Every Two Months'),
        ('THREE_MONTHS', 'Every Three Months'),
        ('FOUR_MONTHS', 'Every Four Months'),
    )
    
    loan_id = models.CharField(_('Loan ID'), max_length=20, unique=True)
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='loans')
    loan_type = models.CharField(_('Loan Type'), max_length=15, choices=LOAN_TYPE_CHOICES)
    principal_amount = models.DecimalField(_('Principal Amount'), max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(_('Interest Rate (% p.a.)'), max_digits=5, decimal_places=2)
    interest_type = models.CharField(
        _('Interest Type'), 
        max_length=15, 
        choices=[('FLAT', 'Flat Rate'), ('REDUCING', 'Reducing Balance')],
        default='REDUCING'
    )
    term_months = models.PositiveIntegerField(_('Loan Term (Months)'))
    repayment_frequency = models.CharField(_('Repayment Frequency'), max_length=10, choices=REPAYMENT_FREQUENCY_CHOICES, default='MONTHLY')
    application_date = models.DateTimeField(_('Application Date'), auto_now_add=True)
    approval_date = models.DateTimeField(_('Approval Date'), null=True, blank=True)
    disbursement_date = models.DateTimeField(_('Disbursement Date'), null=True, blank=True)
    first_payment_date = models.DateField(_('First Payment Date'), null=True, blank=True)
    maturity_date = models.DateField(_('Maturity Date'), null=True, blank=True)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='APPLIED')
    purpose = models.TextField(_('Loan Purpose'))
    
    # Calculated fields
    total_interest = models.DecimalField(_('Total Interest'), max_digits=12, decimal_places=2, default=0.00)
    total_amount = models.DecimalField(_('Total Amount (Principal + Interest)'), max_digits=12, decimal_places=2, default=0.00)
    monthly_installment = models.DecimalField(_('Monthly Installment'), max_digits=12, decimal_places=2, default=0.00)
    
    # Balance tracking
    principal_balance = models.DecimalField(_('Principal Balance'), max_digits=12, decimal_places=2, default=0.00)
    interest_balance = models.DecimalField(_('Interest Balance'), max_digits=12, decimal_places=2, default=0.00)
    
    # Documentation fields
    has_collateral = models.BooleanField(_('Has Collateral'), default=False)
    collateral_details = models.TextField(_('Collateral Details'), blank=True, null=True)
    
    # Approval information
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_loans'
    )
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True, null=True)
    
    # New fields
    repayment_period = models.CharField(
        _('Repayment Period'),
        max_length=20,
        choices=REPAYMENT_PERIOD_CHOICES,
        default='MONTHLY'
    )
    pending_approvals = models.ManyToManyField(
        CustomUser,
        related_name='pending_loan_approvals',
        blank=True,
        help_text="Admins who still need to approve this loan"
    )
    approvals_completed = models.BooleanField(default=False)
    due_date = models.DateField(_('Due Date'), null=True, blank=True)
    penalty_amount = models.DecimalField(
        _('Penalty Amount'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    
    class Meta:
        verbose_name = _('Loan')
        verbose_name_plural = _('Loans')
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.loan_id} - {self.member.get_full_name()} - {self.principal_amount}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        from django.utils.translation import gettext_lazy as _
        
        # Check if member has shares >= loan amount
        from accounts.models import ShareCapital
        try:
            shares = ShareCapital.objects.get(member=self.member)
            if shares.total_value < self.principal_amount:
                raise ValidationError(
                    _('Loan amount cannot exceed total shares value. '
                      f'Maximum loan amount available: KES {shares.total_value:,.2f} '
                      f'based on your shares value.')
                )
        except ShareCapital.DoesNotExist:
            raise ValidationError(_('Member must have shares to request a loan'))

        # Check if member has active loans
        if self.member.loans.filter(
            status__in=['APPROVED', 'DISBURSED', 'ACTIVE']
        ).exclude(pk=self.pk).exists():
            raise ValidationError(_('Member has other active loans'))

        # Check welfare contributions
        from welfare.models import WelfareContribution
        current_month = timezone.now()
        if not WelfareContribution.objects.filter(
            member=self.member,
            contribution_date__year=current_month.year,
            contribution_date__month=current_month.month,
            status='CONFIRMED'
        ).exists():
            raise ValidationError(_('Must pay current month welfare contribution'))

    def save(self, *args, **kwargs):
        # Initial calculations when loan is disbursed
        if self.status == 'DISBURSED' and not self.principal_balance:
            self.principal_balance = self.principal_amount
            
            # Calculate total interest based on interest type
            if self.interest_type == 'FLAT':
                self.total_interest = (self.principal_amount * self.interest_rate * self.term_months) / (100 * 12)
            else:  # REDUCING
                # Simple estimation for reducing balance
                self.total_interest = (self.principal_amount * self.interest_rate * (self.term_months + 1)) / (100 * 24)
            
            self.total_amount = self.principal_amount + self.total_interest
            self.interest_balance = self.total_interest
            self.monthly_installment = self.total_amount / self.term_months
            
            # Set maturity date
            if self.disbursement_date and not self.maturity_date:
                # Simplified calculation, can be refined
                self.maturity_date = self.disbursement_date + timezone.timedelta(days=30*self.term_months)
                
        if not self.pk:  # New loan
            self.clean()
            # Set pending approvals for all admins
            super().save(*args, **kwargs)  # Save first to get PK
            from django.contrib.auth.models import Group
            admin_group = Group.objects.get(name='Admin')
            self.pending_approvals.set(admin_group.user_set.all())
        else:
            self.clean()
        super(Loan, self).save(*args, **kwargs)

    def validate_member_eligibility(self):
        """Validate member eligibility for loan"""
        from welfare.models import WelfareContribution
        from accounts.models import ShareCapital
        
        errors = []
        
        # Check registration
        if not self.member.is_active or not self.member.groups.filter(name='Member').exists():
            errors.append("Must be an active SACCO member")

        # Check welfare contributions
        current_month = timezone.now()
        has_welfare = WelfareContribution.objects.filter(
            member=self.member,
            contribution_date__year=current_month.year,
            contribution_date__month=current_month.month,
            status='CONFIRMED'
        ).exists()
        if not has_welfare:
            errors.append("Must pay current month welfare contribution")

        # Check shares value
        try:
            shares = ShareCapital.objects.get(member=self.member)
            if shares.total_value < self.principal_amount:
                errors.append("Insufficient shares value for requested loan amount")
        except ShareCapital.DoesNotExist:
            errors.append("No shares found for member")

        # Check active loans
        active_loans = Loan.objects.filter(
            member=self.member,
            status__in=['APPROVED', 'DISBURSED', 'ACTIVE']
        ).exclude(pk=self.pk).exists()
        if active_loans:
            errors.append("Member has other active loans")

        if errors:
            raise ValidationError(" | ".join(errors))

    def validate_guarantors(self):
        """Validate guarantor requirements"""
        total_guaranteed = self.guarantors.filter(
            status='ACCEPTED'
        ).aggregate(total=Sum('amount'))['total'] or 0

        if total_guaranteed < self.principal_amount:
            raise ValidationError(
                f"Insufficient guarantor amount. Required: {self.principal_amount}, Got: {total_guaranteed}"
            )

    def validate_loan_terms(self):
        """Validate loan terms and conditions"""
        errors = []

        if not self.repayment_period:
            errors.append("Repayment period is required")

        if not self.interest_rate or self.interest_rate <= 0:
            errors.append("Invalid interest rate")

        if not self.principal_amount or self.principal_amount <= 0:
            errors.append("Invalid principal amount")

        if errors:
            raise ValidationError(" | ".join(errors))

    def get_available_loan_amount(self):
        """Calculate maximum loan amount available based on shares"""
        from accounts.models import ShareCapital
        try:
            shares = ShareCapital.objects.get(member=self.member)
            return {
                'available_amount': shares.total_value,
                'shares_value': shares.total_value,
            }
        except ShareCapital.DoesNotExist:
            return {
                'available_amount': 0,
                'shares_value': 0,
            }


class Guarantor(models.Model):
    """
    Model representing a guarantor for a loan
    """
    STATUS_CHOICES = (
        ('REQUESTED', 'Requested'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='guarantors')
    guarantor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='guarantees')
    guaranteed_amount = models.DecimalField(_('Guaranteed Amount'), max_digits=12, decimal_places=2)
    request_date = models.DateTimeField(_('Request Date'), default=timezone.now)
    response_date = models.DateTimeField(_('Response Date'), null=True, blank=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='REQUESTED')
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Guarantor')
        verbose_name_plural = _('Guarantors')
    
    def __str__(self):
        return f"{self.guarantor.get_full_name()} - {self.loan.loan_id}"


class GuarantorRequest(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='guarantor_requests')
    guarantor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='guarantor_requests_received')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('APPROVED', 'Approved'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    request_date = models.DateTimeField(auto_now_add=True)
    response_date = models.DateTimeField(null=True, blank=True)

    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Ensure guarantor is a SACCO member
        if not self.guarantor.groups.filter(name='Member').exists():
            raise ValidationError(_('Guarantor must be a SACCO member'))

        # Check guarantor's shares
        from accounts.models import ShareCapital
        try:
            shares = ShareCapital.objects.get(member=self.guarantor)
            if shares.total_value < self.amount:
                raise ValidationError(_('Guarantor does not have sufficient shares'))
        except ShareCapital.DoesNotExist:
            raise ValidationError(_('Guarantor must have shares'))


class LoanRepayment(models.Model):
    """
    Model representing loan repayment transactions
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('PROCESSED', 'Processed'),
        ('FAILED', 'Failed'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    payment_amount = models.DecimalField(_('Payment Amount'), max_digits=12, decimal_places=2)
    principal_component = models.DecimalField(_('Principal Component'), max_digits=12, decimal_places=2)
    interest_component = models.DecimalField(_('Interest Component'), max_digits=12, decimal_places=2)
    penalties_component = models.DecimalField(_('Penalties Component'), max_digits=12, decimal_places=2, default=0.00)
    payment_date = models.DateTimeField(_('Payment Date'), default=timezone.now)
    payment_method = models.CharField(_('Payment Method'), max_length=20)
    transaction_reference = models.CharField(_('Transaction Reference'), max_length=50, blank=True, null=True)
    receipt_number = models.CharField(_('Receipt Number'), max_length=20, blank=True, null=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='PENDING')
    processed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_repayments'
    )
    principal_balance_after = models.DecimalField(_('Principal Balance After'), max_digits=12, decimal_places=2)
    interest_balance_after = models.DecimalField(_('Interest Balance After'), max_digits=12, decimal_places=2)
    
    class Meta:
        verbose_name = _('Loan Repayment')
        verbose_name_plural = _('Loan Repayments')
        ordering = ['-payment_date']
    
    def __str__(self):
        return f"Repayment: {self.payment_amount} - {self.loan.loan_id}"


class PenaltyType(models.Model):
    """
    Model representing different types of penalties
    """
    CALCULATION_METHOD_CHOICES = (
        ('FIXED', 'Fixed Amount'),
        ('PERCENTAGE', 'Percentage'),
    )
    
    name = models.CharField(_('Penalty Name'), max_length=50)
    description = models.TextField(_('Description'))
    calculation_method = models.CharField(_('Calculation Method'), max_length=10, choices=CALCULATION_METHOD_CHOICES)
    rate_or_amount = models.DecimalField(_('Rate (%) or Amount'), max_digits=8, decimal_places=2)
    grace_period_days = models.PositiveIntegerField(_('Grace Period (Days)'), default=0)
    active = models.BooleanField(_('Active'), default=True)
    
    class Meta:
        verbose_name = _('Penalty Type')
        verbose_name_plural = _('Penalty Types')
    
    def __str__(self):
        return self.name


class Penalty(models.Model):
    """
    Model representing penalties imposed on loans
    """
    STATUS_CHOICES = (
        ('IMPOSED', 'Imposed'),
        ('PAID', 'Paid'),
        ('WAIVED', 'Waived'),
    )
    
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='penalties')
    penalty_type = models.ForeignKey(PenaltyType, on_delete=models.PROTECT, related_name='applied_penalties')
    amount = models.DecimalField(_('Amount'), max_digits=12, decimal_places=2)
    date_imposed = models.DateTimeField(_('Date Imposed'), default=timezone.now)
    due_date = models.DateField(_('Due Date'))
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='IMPOSED')
    waived = models.BooleanField(_('Waived'), default=False)
    waiver_reason = models.TextField(_('Waiver Reason'), blank=True, null=True)
    waived_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='waived_penalties'
    )
    waived_at = models.DateTimeField(_('Waived At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Penalty')
        verbose_name_plural = _('Penalties')
    
    def __str__(self):
        return f"Penalty: {self.amount} - {self.loan.loan_id}"


class LoanApproval(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='admin_approvals')
    admin = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    approved = models.BooleanField(default=False)
    approval_date = models.DateTimeField(null=True, blank=True)
    comments = models.TextField(blank=True)

    class Meta:
        unique_together = ['loan', 'admin']

    def save(self, *args, **kwargs):
        if self.approved and not self.approval_date:
            self.approval_date = timezone.now()
        super().save(*args, **kwargs)