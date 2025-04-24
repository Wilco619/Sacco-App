from django.db import models
from django.conf import settings

class Transaction(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled by User'),
        ('FAILED', 'Failed'),
        ('TIMEOUT', 'Timed Out')
    )

    PAYMENT_TYPES = (
        ('REGISTRATION', 'Registration'),
        ('SHARES', 'Shares'),
        ('LOAN', 'Loan'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mpesa_transactions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    id_number = models.CharField(max_length=100, blank=True, null=True)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPES, default='SHARES')
    mpesa_code = models.CharField(max_length=100, unique=True, null=True, blank=True)
    phone_number = models.CharField(max_length=15)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    timestamp = models.DateTimeField(auto_now_add=True)
    result_code = models.CharField(max_length=10, blank=True, null=True)
    result_description = models.CharField(max_length=100, blank=True, null=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True)
    profit_recorded = models.BooleanField(default=False)
    description = models.CharField(
        max_length=255, 
        blank=True, 
        null=True,
        help_text="Description of the transaction"
    )

    def __str__(self):
        return f"{self.mpesa_code or 'No Code'} - {self.amount} - {self.status}"
