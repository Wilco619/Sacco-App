# users/models.py
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .utils import validate_image
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where id_number is the unique identifier
    for authentication instead of usernames.
    """
    def create_user(self, id_number, email, password=None, **extra_fields):
        """
        Create and save a user with the given id_number and password.
        """
        if not id_number:
            raise ValueError('Users must have an ID number')
        if not email:
            raise ValueError('Users must have an email address')

        email = self.normalize_email(email)
        user = self.model(
            id_number=id_number,
            email=email,
            **extra_fields
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, id_number, email, first_name, last_name, phone_number, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given id_number and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'ADMIN')

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        return self.create_user(id_number, email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """
    Custom User Model where id_number is the unique identifier
    """
    USER_TYPE_CHOICES = (
        ('ADMIN', 'Admin'),
        ('MEMBER', 'Member'),
    )
    
    id_number = models.CharField(_('ID Number'), max_length=20, unique=True)
    email = models.EmailField(_('Email Address'), unique=True)
    first_name = models.CharField(_('First Name'), max_length=50)
    last_name = models.CharField(_('Last Name'), max_length=50)
    phone_number = models.CharField(_('Phone Number'), max_length=15, unique=True)
    address = models.TextField(_('Address'), blank=True, null=True)
    user_type = models.CharField(_('User Type'), max_length=10, choices=USER_TYPE_CHOICES, default='MEMBER')
    date_joined = models.DateTimeField(_('Date Joined'), default=timezone.now)
    password_changed = models.BooleanField(_('Password Changed'), default=False)
    is_staff = models.BooleanField(_('Staff Status'), default=False)
    is_active = models.BooleanField(_('Active'), default=True)
    is_first_login = models.BooleanField(default=True)
    
    USERNAME_FIELD = 'id_number'
    REQUIRED_FIELDS = ['email', 'first_name', 'last_name', 'phone_number']
    
    objects = CustomUserManager()
    
    class Meta:
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.id_number})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"


class UserProfile(models.Model):
    """
    Extended profile for users with additional information
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    
    # Basic profile fields
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    date_of_birth = models.DateField(_('Date of Birth'), blank=True, null=True)
    gender = models.CharField(_('Gender'), max_length=10, blank=True, null=True)
    occupation = models.CharField(_('Occupation'), max_length=100, blank=True, null=True)
    next_of_kin = models.CharField(_('Next of Kin'), max_length=100, blank=True, null=True)
    next_of_kin_contact = models.CharField(_('Next of Kin Contact'), max_length=15, blank=True, null=True)
    
    # Document fields
    id_front_image = models.ImageField(_('ID Front Image'), upload_to='id_images/', blank=True, null=True)
    id_back_image = models.ImageField(_('ID Back Image'), upload_to='id_images/', blank=True, null=True)
    passport_photo = models.ImageField(_('Passport Photo'), upload_to='passport_photos/', blank=True, null=True)
    signature = models.ImageField(_('Signature Image'), upload_to='signatures/', blank=True, null=True)
    
    # Verification fields (removed duplicates)
    id_front_verified = models.BooleanField(_('ID Front Verified'), default=False)
    id_back_verified = models.BooleanField(_('ID Back Verified'), default=False)
    passport_photo_verified = models.BooleanField(_('Passport Photo Verified'), default=False)
    signature_verified = models.BooleanField(_('Signature Verified'), default=False)
    
    verification_status = models.CharField(
        _('Verification Status'),
        max_length=20,
        choices=[
            ('PENDING', 'Pending'),
            ('VERIFIED', 'Verified'),
            ('REJECTED', 'Rejected')
        ],
        default='PENDING'
    )
    verification_notes = models.TextField(_('Verification Notes'), blank=True, null=True)
    verified_at = models.DateTimeField(_('Verified At'), blank=True, null=True)
    verified_by = models.ForeignKey(
        'CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='verifications_done'
    )

    @property
    def documents_verified(self):
        """Check if all required documents are verified"""
        return all([
            self.id_front_verified,
            self.id_back_verified,
            self.passport_photo_verified,
            self.signature_verified
        ])

    def clean(self):
        super().clean()
        if self.profile_picture:
            validate_image(self.profile_picture)
        if self.id_front_image:
            validate_image(self.id_front_image)
        if self.id_back_image:
            validate_image(self.id_back_image)
        if self.passport_photo:
            validate_image(self.passport_photo)
        if self.signature:
            validate_image(self.signature)
    
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"


class OTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, db_index=True)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'

    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile for every new user"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile whenever the user is saved"""
    try:
        instance.profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance)