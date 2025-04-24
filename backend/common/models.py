from django.db import models
from django.utils.translation import gettext_lazy as _
from users.models import CustomUser
from django.utils import timezone


class AuditLog(models.Model):
    """
    Model for tracking system actions and user activities
    """
    ACTION_CHOICES = (
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('PASSWORD_CHANGE', 'Password Change'),
        ('OTHER', 'Other'),
    )
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs'
    )
    action = models.CharField(_('Action'), max_length=20, choices=ACTION_CHOICES)
    entity_type = models.CharField(_('Entity Type'), max_length=50)
    entity_id = models.CharField(_('Entity ID'), max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(_('Timestamp'), default=timezone.now)
    ip_address = models.GenericIPAddressField(_('IP Address'), blank=True, null=True)
    user_agent = models.TextField(_('User Agent'), blank=True, null=True)
    details = models.JSONField(_('Details'), blank=True, null=True)
    
    class Meta:
        verbose_name = _('Audit Log')
        verbose_name_plural = _('Audit Logs')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.action} - {self.entity_type} - {self.timestamp}"


class Notification(models.Model):
    """
    Model for system notifications to users
    """
    TYPE_CHOICES = (
        ('SYSTEM', 'System'),
        ('TRANSACTION', 'Transaction'),
        ('ACCOUNT', 'Account'),
        ('LOAN', 'Loan'),
        ('WELFARE', 'Welfare'),
        ('DIVIDEND', 'Dividend'),
    )
    
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    )
    
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    type = models.CharField(_('Type'), max_length=15, choices=TYPE_CHOICES)
    title = models.CharField(_('Title'), max_length=100)
    message = models.TextField(_('Message'))
    created_at = models.DateTimeField(_('Created At'), default=timezone.now)
    read = models.BooleanField(_('Read'), default=False)
    read_at = models.DateTimeField(_('Read At'), null=True, blank=True)
    priority = models.CharField(_('Priority'), max_length=10, choices=PRIORITY_CHOICES, default='MEDIUM')
    link = models.CharField(_('Link'), max_length=255, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"


class Document(models.Model):
    """
    Model for general document storage and management
    """
    DOCUMENT_TYPE_CHOICES = (
        ('POLICY', 'Policy Document'),
        ('CONTRACT', 'Contract'),
        ('REPORT', 'Report'),
        ('FORM', 'Form'),
        ('MINUTES', 'Meeting Minutes'),
        ('OTHER', 'Other'),
    )
    
    title = models.CharField(_('Title'), max_length=100)
    document_type = models.CharField(_('Document Type'), max_length=15, choices=DOCUMENT_TYPE_CHOICES)
    file = models.FileField(_('File'), upload_to='documents/')
    description = models.TextField(_('Description'), blank=True, null=True)
    uploaded_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='uploaded_documents'
    )
    uploaded_at = models.DateTimeField(_('Uploaded At'), default=timezone.now)
    is_public = models.BooleanField(_('Is Public'), default=False)
    version = models.CharField(_('Version'), max_length=20, blank=True, null=True)
    
    class Meta:
        verbose_name = _('Document')
        verbose_name_plural = _('Documents')
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return f"{self.title} - {self.document_type}"


class Setting(models.Model):
    """
    Model for system-wide settings
    """
    SETTING_TYPE_CHOICES = (
        ('GENERAL', 'General'),
        ('SYSTEM', 'System'),
        ('LOAN', 'Loan'),
        ('SAVINGS', 'Savings'),
        ('WELFARE', 'Welfare'),
        ('NOTIFICATION', 'Notification'),
    )
    
    DATA_TYPE_CHOICES = (
        ('STRING', 'String'),
        ('INTEGER', 'Integer'),
        ('DECIMAL', 'Decimal'),
        ('BOOLEAN', 'Boolean'),
        ('JSON', 'JSON'),
        ('DATE', 'Date'),
        ('DATETIME', 'DateTime'),
    )
    
    key = models.CharField(_('Key'), max_length=100, unique=True)
    value = models.TextField(_('Value'))
    data_type = models.CharField(_('Data Type'), max_length=10, choices=DATA_TYPE_CHOICES)
    setting_type = models.CharField(_('Setting Type'), max_length=15, choices=SETTING_TYPE_CHOICES)
    description = models.TextField(_('Description'))
    is_public = models.BooleanField(_('Is Public'), default=False)
    created_at = models.DateTimeField(_('Created At'), default=timezone.now)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)
    updated_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='updated_settings'
    )
    
    class Meta:
        verbose_name = _('Setting')
        verbose_name_plural = _('Settings')
    
    def __str__(self):
        return f"{self.key} - {self.setting_type}"