from PIL import Image
import os
from django.core.exceptions import ValidationError
import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings


import time
import logging

logger = logging.getLogger(__name__)

def validate_image(image_field):
    """
    Validates image files:
    1. Checks if the file is a valid image
    2. Ensures the file size is reasonable
    3. Makes sure the image dimensions are appropriate
    """
    if not image_field:
        return
        
    # Check file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB in bytes
    if image_field.size > max_size:
        raise ValidationError(f"Image size should not exceed 5MB. Current size: {image_field.size/(1024*1024):.2f}MB")
    
    # Check if it's a valid image
    try:
        img = Image.open(image_field)
        img.verify()  # Verify it's an image
    except Exception:
        raise ValidationError("Uploaded file is not a valid image")
    
    # Check image dimensions
    img = Image.open(image_field)
    width, height = img.size
    
    # Reasonable min/max dimensions
    min_dimension = 100  # At least 100x100 pixels
    max_dimension = 5000  # Not more than 5000x5000 pixels
    
    if width < min_dimension or height < min_dimension:
        raise ValidationError(f"Image dimensions too small. Minimum {min_dimension}x{min_dimension} pixels")
    
    if width > max_dimension or height > max_dimension:
        raise ValidationError(f"Image dimensions too large. Maximum {max_dimension}x{max_dimension} pixels")
        
    return True

def generate_otp():
    """Generate a 6-digit OTP"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])


def send_otp_email(user, otp_code):
    subject = 'Your OTP Code for Login'
    message = f'Your OTP code is: {otp_code}\nThis code will expire in 10 minutes.'
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user.email]
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            recipient_list,
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send OTP email: {str(e)}")
        return False


def send_welcome_email(user, password):
    subject = 'Welcome to SACCO - Your Account Details'
    message = f"""
Hello {user.first_name},

Your SACCO account has been created successfully.

Your login credentials are:
ID Number: {user.id_number}
Password: {password}

For security reasons, please change your password when you first log in.

Best regards,
SACCO Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")
        return False


def send_password_reset_email(user, new_password):
    """
    Send password reset email to user
    Returns True if email was sent successfully, False otherwise
    """
    subject = 'SACCO - Password Reset'
    message = f"""
Hello {user.first_name},

Your password has been reset by an administrator.

Your new login credentials are:
ID Number: {user.id_number}
New Password: {new_password}

For security reasons, please change your password when you next log in.

Best regards,
SACCO Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False


def send_password_change_notification(user):
    """
    Send notification email when user changes their password
    """
    subject = 'SACCO - Password Change Notification'
    message = f"""
Hello {user.first_name},

This email is to confirm that your password was recently changed.

If you did not make this change, please contact our support team immediately.

Best regards,
SACCO Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send password change notification to {user.email}: {str(e)}")
        return False


def create_otp(user):
    start_time = time.time()
    """Create new OTP for user"""
    from .models import OTP
    
    # Invalidate any existing OTPs
    OTP.objects.filter(user=user, is_used=False).update(is_used=True)
    
    # Create new OTP
    otp_code = generate_otp()
    expires_at = timezone.now() + timedelta(minutes=5)
    
    otp = OTP.objects.create(
        user=user,
        code=otp_code,
        expires_at=expires_at
    )
    
    # Print OTP to terminal for development
    print(f"\n=== OTP for {user.email} ===")
    print(f"Code: {otp_code}")
    print("========================\n")
    
    # Send OTP via email
    send_otp_email(user, otp_code)
    
    return otp


def send_document_rejection_email(user, document_type, notes):
    """Send email notification for document rejection"""
    subject = 'Document Verification Failed'
    
    document_names = {
        'id_front': 'ID Front',
        'id_back': 'ID Back',
        'passport_photo': 'Passport Photo',
        'signature': 'Signature',
        'all': 'All Documents'
    }
    
    document_name = document_names.get(document_type, document_type)
    
    message = f"""
    Dear {user.get_full_name()},

    Your document verification for {document_name} has been rejected.

    Reason: {notes}

    Please upload a new version of the document(s) through your profile.

    Best regards,
    Sacco Team
    """
    
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send rejection email: {str(e)}")
        return False


def send_document_verification_email(user, document_type, all_verified=False):
    """Send email notification for document verification"""
    try:
        document_names = {
            'id_front': 'ID Front',
            'id_back': 'ID Back',
            'passport_photo': 'Passport Photo',
            'signature': 'Signature',
            'all': 'All Documents'
        }
        
        document_name = document_names.get(document_type, document_type)
        
        if all_verified:
            subject = 'All Documents Verified Successfully'
            message = f"""
            Dear {user.get_full_name()},
            
            We are pleased to inform you that all your documents have been verified successfully.
            You can now access all Sacco services.
            
            Best regards,
            Sacco Team
            """
        else:
            subject = f'Document Verification Status - {document_name}'
            message = f"""
            Dear {user.get_full_name()},
            
            Your {document_name.lower()} has been verified successfully.
            
            Best regards,
            Sacco Team
            """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        return False