from .models import AuditLog


def log_activity(request, action, entity_type, entity_id=None, details=None):
    """
    Utility function to create audit log entries
    
    Args:
        request: The request object
        action: The action performed (one of AuditLog.ACTION_CHOICES)
        entity_type: The type of entity being acted upon
        entity_id: The ID of the entity (optional)
        details: Additional details as a JSON-serializable dict (optional)
    
    Returns:
        The created AuditLog instance
    """
    user = request.user if request.user.is_authenticated else None
    
    # Get IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')
    
    # Get user agent
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    # Create and save the audit log
    audit_log = AuditLog.objects.create(
        user=user,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        ip_address=ip_address,
        user_agent=user_agent,
        details=details
    )
    
    return audit_log


def create_notification(recipient, type, title, message, priority='MEDIUM', link=None):
    """
    Utility function to create user notifications
    
    Args:
        recipient: CustomUser instance to receive the notification
        type: The notification type (one of Notification.TYPE_CHOICES)
        title: Notification title
        message: Notification message content
        priority: Priority level (default: 'MEDIUM')
        link: Optional URL or path related to the notification
    
    Returns:
        The created Notification instance
    """
    from .models import Notification
    
    notification = Notification.objects.create(
        recipient=recipient,
        type=type,
        title=title,
        message=message,
        priority=priority,
        link=link
    )
    
    return notification


def get_setting_value(key, default=None):
    """
    Utility function to retrieve a setting value
    
    Args:
        key: The setting key
        default: Default value if setting is not found
    
    Returns:
        The setting value or the default value
    """
    from .models import Setting
    
    try:
        setting = Setting.objects.get(key=key)
        
        # Convert value based on data type
        if setting.data_type == 'INTEGER':
            return int(setting.value)
        elif setting.data_type == 'DECIMAL':
            return float(setting.value)
        elif setting.data_type == 'BOOLEAN':
            return setting.value.lower() == 'true'
        elif setting.data_type == 'JSON':
            import json
            return json.loads(setting.value)
        else:
            return setting.value
    except Setting.DoesNotExist:
        return default