from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from django.utils import timezone
from datetime import date


class WelfareFund(models.Model):
    """
    Model representing a welfare fund in the SACCO
    """
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )
    
    name = models.CharField(_('Fund Name'), max_length=100)
    description = models.TextField(_('Description'))
    total_amount = models.DecimalField(_('Total Amount'), max_digits=12, decimal_places=2, default=0.00)
    date_established = models.DateField(
        _('Date Established'),
        default=date.today
    )
    contribution_frequency = models.CharField(
        _('Contribution Frequency'),
        max_length=10,
        choices=[
            ('MONTHLY', 'Monthly'),
            ('QUARTERLY', 'Quarterly'),
            ('ANNUALLY', 'Annually'),
            ('ONETIME', 'One Time')
        ],
        default='MONTHLY'
    )
    minimum_contribution = models.DecimalField(_('Minimum Contribution'), max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='ACTIVE')
    
    class Meta:
        verbose_name = _('Welfare Fund')
        verbose_name_plural = _('Welfare Funds')
    
    def __str__(self):
        return f"{self.name} - {self.total_amount}"


class WelfareContribution(models.Model):
    """
    Model representing contributions to a welfare fund
    """
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('REJECTED', 'Rejected'),
    )
    
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='welfare_contributions')
    welfare_fund = models.ForeignKey(WelfareFund, on_delete=models.CASCADE, related_name='contributions')
    amount = models.DecimalField(_('Amount'), max_digits=10, decimal_places=2)
    contribution_date = models.DateTimeField(_('Contribution Date'), default=timezone.now)
    payment_method = models.CharField(_('Payment Method'), max_length=50)
    reference_number = models.CharField(_('Reference Number'), max_length=50, blank=True, null=True)
    receipt_number = models.CharField(_('Receipt Number'), max_length=50, blank=True, null=True)
    status = models.CharField(_('Status'), max_length=10, choices=STATUS_CHOICES, default='PENDING')
    processed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='processed_welfare_contributions'
    )
    processed_at = models.DateTimeField(_('Processed At'), null=True, blank=True)
    
    class Meta:
        verbose_name = _('Welfare Contribution')
        verbose_name_plural = _('Welfare Contributions')
        ordering = ['-contribution_date']
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.welfare_fund.name} - {self.amount}"


class WelfareBenefit(models.Model):
    """
    Model representing benefits claimed from welfare funds
    """
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('UNDER_REVIEW', 'Under Review'),
        ('APPROVED', 'Approved'),
        ('DISBURSED', 'Disbursed'),
        ('REJECTED', 'Rejected'),
    )
    
    REASON_CHOICES = (
        ('MEDICAL', 'Medical'),
        ('BEREAVEMENT', 'Bereavement'),
        ('EDUCATION', 'Education'),
        ('RETIREMENT', 'Retirement'),
        ('DISABILITY', 'Disability'),
        ('OTHER', 'Other'),
    )
    
    member = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='welfare_benefits')
    welfare_fund = models.ForeignKey(WelfareFund, on_delete=models.CASCADE, related_name='benefits')
    reason = models.CharField(_('Reason'), max_length=20, choices=REASON_CHOICES)
    other_reason = models.TextField(_('Other Reason Details'), blank=True, null=True)
    amount = models.DecimalField(_('Amount Requested'), max_digits=10, decimal_places=2)
    approved_amount = models.DecimalField(_('Approved Amount'), max_digits=10, decimal_places=2, null=True, blank=True)
    application_date = models.DateTimeField(_('Application Date'), default=timezone.now)
    approval_date = models.DateTimeField(_('Approval Date'), null=True, blank=True)
    disbursement_date = models.DateTimeField(_('Disbursement Date'), null=True, blank=True)
    status = models.CharField(_('Status'), max_length=15, choices=STATUS_CHOICES, default='APPLIED')
    
    # Supporting documentation
    has_documentation = models.BooleanField(_('Has Supporting Documents'), default=False)
    document_description = models.TextField(_('Document Description'), blank=True, null=True)
    
    # Approval information
    reviewed_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='reviewed_benefits'
    )
    approved_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_benefits'
    )
    rejection_reason = models.TextField(_('Rejection Reason'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Welfare Benefit')
        verbose_name_plural = _('Welfare Benefits')
        ordering = ['-application_date']
    
    def __str__(self):
        return f"{self.member.get_full_name()} - {self.welfare_fund.name} - {self.amount}"


class WelfareDocument(models.Model):
    """
    Model for storing welfare benefit supporting documents
    """
    benefit = models.ForeignKey(WelfareBenefit, on_delete=models.CASCADE, related_name='documents')
    document = models.FileField(_('Document'), upload_to='welfare_documents/')
    title = models.CharField(_('Title'), max_length=100)
    description = models.TextField(_('Description'), blank=True, null=True)
    uploaded_at = models.DateTimeField(_('Uploaded At'), default=timezone.now)
    
    class Meta:
        verbose_name = _('Welfare Document')
        verbose_name_plural = _('Welfare Documents')
    
    def __str__(self):
        return f"{self.title} - {self.benefit.member.get_full_name()}"