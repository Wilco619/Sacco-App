# users/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
import random
import string

from .models import CustomUser, UserProfile


def generate_random_password(length=10):
    """Generate a random password of specified length"""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for i in range(length))


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for newly created users"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Ensure profile is saved when user is saved"""
    instance.profile.save()


@receiver(post_save, sender=CustomUser)
def send_credentials_email(sender, instance, created, **kwargs):
    """Send email with login credentials when a new member is created"""
    if created and instance.user_type == 'MEMBER':
        subject = 'Your SACCO Account Credentials'
        message = f"""
        Hello {instance.get_full_name()},
        
        Your SACCO account has been created successfully.
        
        Your login credentials are:
        Username: {instance.id_number}
        
        Please login with the temporary password provided to you and change your password immediately.
        
        Thank you,
        SACCO Management Team
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list, fail_silently=False)
        except Exception as e:
            # Log the error but don't interrupt the user creation process
            print(f"Error sending email: {str(e)}")