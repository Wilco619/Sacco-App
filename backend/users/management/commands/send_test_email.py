from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Send a test email to verify SMTP connection'

    def handle(self, *args, **kwargs):
        subject = 'Test Email'
        message = 'This is a test email to verify SMTP connection.'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = ['recipient@example.com']  # Replace with a valid email address for testing

        try:
            send_mail(subject, message, from_email, recipient_list)
            self.stdout.write(self.style.SUCCESS("Test email sent successfully."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to send test email: {str(e)}"))
