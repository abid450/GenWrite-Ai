from django.db import models

# Create your models here.
import uuid
import re
import json
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from .utils import generate_verification_code, get_expiry_time
from django.conf import settings
from django.core.exceptions import ValidationError


# ============= Custom Phone Number Validator for Bangladesh =============
def validate_bangladesh_phone_number(value):
    """
    Validate Bangladeshi phone number format
    Supported formats:
    - 01XXXXXXXXX (11 digits, starts with 01)
    - +8801XXXXXXXXX (14 digits, starts with +8801)
    - 8801XXXXXXXXX (13 digits, starts with 8801)
    """
    cleaned = re.sub(r'[\s\-\(\)]', '', value)    
    has_plus = value.startswith('+')
    
    # Validation patterns for Bangladesh
    patterns = [
        r'^01[3-9]\d{8}$',      # 013XXXXXXXX, 014XXXXXXXX, 015XXXXXXXX, 016XXXXXXXX, 017XXXXXXXX, 018XXXXXXXX, 019XXXXXXXX
        r'^8801[3-9]\d{8}$',    # 88013XXXXXXXX, 88014XXXXXXXX, etc.
        r'^\+8801[3-9]\d{8}$',  # +88013XXXXXXXX, +88014XXXXXXXX, etc.
    ]

    return cleaned


def format_bangladesh_phone_number(value):
    """
    Format Bangladeshi phone number to a standard format
    Returns: +8801XXXXXXXXX format
    """
    cleaned = re.sub(r'\D', '', value)

    if cleaned.startswith('880'):
        cleaned = cleaned[3:]

    if cleaned.startswith('0'):
        cleaned = cleaned[1:]

    if len(cleaned) == 10:
        return f"+880{cleaned}"
    
    return value

    

class User(AbstractUser):
    phone_regex = RegexValidator(
        regex=r'^(\+8801[3-9]\d{8}|8801[3-9]\d{8}|01[3-9]\d{8})$',
        message='Enter a valid Bangladeshi phone number. '
            'Format: 01XXXXXXXXX (e.g., 01712345678) or +8801XXXXXXXXX (e.g., +8801712345678)'
    )

    phone_number = models.CharField(
        max_length=18,
        validators=[phone_regex, validate_bangladesh_phone_number],
        blank= True,
        null= True,
        help_text= "Bangladeshi phone number (e.g., 01712345678 or +8801712345678)"


    )

    phone_number_international = models.CharField(
        max_length=18,
        blank=True,
        null= True,
        help_text= "Phone number in international format (+8801XXXXXXXXX)"
    )

    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    bio = models.TextField(max_length=500, blank=True, null=True)
    is_email_verified = models.BooleanField(default=False)
    email_verified_at = models.DateTimeField(blank=True, null=True)

    # IP tracking
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    registration_ip = models.GenericIPAddressField(blank=True, null=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_email_verified']),
        ]
    
    def __str__(self):
        return f"{self.email} ({self.username})"
    
    def save(self, *args, **kwargs):
        # Auto-format phone number if provided
        if self.phone_number:
            # Store both raw and formatted versions
            self.phone_number_international = format_bangladesh_phone_number(self.phone_number)
            
            # Clean the phone number for consistency
            cleaned = re.sub(r'\D', '', self.phone_number)
            if cleaned.startswith('0'):
                self.phone_number = cleaned  # Store as 01XXXXXXXXX
            elif cleaned.startswith('880'):
                self.phone_number = cleaned[3:]  # Convert 8801X to 01X
                self.phone_number = f"0{self.phone_number}"
        
        super().save(*args, **kwargs)
    
    def verify_email(self):
        """Mark email as verified"""
        self.is_email_verified = True
        self.email_verified_at = timezone.now()
        self.save(update_fields=['is_email_verified', 'email_verified_at'])
    
    def get_formatted_phone(self):
        """Get formatted phone number for display"""
        if self.phone_number_international:
            return self.phone_number_international
        elif self.phone_number:
            return format_bangladesh_phone_number(self.phone_number)
        return None
    
    @property
    def phone_display(self):
        """Get phone number for display (masked)"""
        phone = self.get_formatted_phone()
        if phone and len(phone) >= 10:
            return phone[:6] + '****' + phone[-2:]
        return phone


class EmailVerification(models.Model):
    """
    Model to manage email verification codes
    """

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VERIFIED = 'verified', 'Verified'
        EXPIRED = 'expired', 'Expired'
        FAILED = 'failed', 'Failed'
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='email_verification'
    )
    verification_code = models.CharField(
        max_length=10, 
        default=generate_verification_code
    )
    status = models.CharField(
        max_length=10, 
        choices=VerificationStatus.choices, 
        default=VerificationStatus.PENDING
    )
    attempts = models.PositiveSmallIntegerField(default=0)
    is_used = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expired_at = models.DateTimeField(default=get_expiry_time)
    verified_at = models.DateTimeField(blank=True, null=True)
    
    # Metadata
    request_ip = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'email_verifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['verification_code']),
            models.Index(fields=['expired_at']),
        ]
    
    def __str__(self):
        return f"Verification for {self.user.email} - {self.status}"
    
    def is_expired(self):
        """Check if verification code has expired"""
        return timezone.now() > self.expired_at
    
    def can_retry(self):
        """Check if user can request new code"""
        return (
            self.status != self.VerificationStatus.VERIFIED and
            self.attempts < settings.MAX_VERIFICATION_ATTEMPTS and
            not self.is_expired()
        )
    
    def mark_as_verified(self):
        """Mark verification as successful"""
        self.status = self.VerificationStatus.VERIFIED
        self.is_used = True
        self.verified_at = timezone.now()
        self.save()
        self.user.verify_email()
    
    def mark_as_failed(self):
        """Mark verification as failed"""
        self.attempts += 1
        if self.attempts >= 5:
            self.status = self.VerificationStatus.FAILED
        self.save()
    
    def regenerate_code(self):
        """Generate new verification code"""
        self.verification_code = generate_verification_code()
        self.expired_at = get_expiry_time()
        self.attempts = 0
        self.status = self.VerificationStatus.PENDING
        self.save()
        return self.verification_code



class VerificationLog(models.Model):
    """
    Log all verification attempts for audit
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='verification_logs')
    verification = models.ForeignKey(EmailVerification, on_delete=models.CASCADE, null=True)
    action = models.CharField(max_length=50)  # 'send', 'verify', 'resend', 'register'
    status = models.CharField(max_length=20)  # 'success', 'failed', 'pending'
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'verification_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.action} - {self.status}"


# ============= Additional Model for Phone Verification (Optional) =============

class PhoneVerification(models.Model):
    """
    Model for phone number verification (SMS)
    """
    class VerificationType(models.TextChoices):
        REGISTRATION = 'registration', 'Registration'
        LOGIN = 'login', 'Login'
        PASSWORD_RESET = 'password_reset', 'Password Reset'
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    phone_number = models.CharField(max_length=17)
    verification_code = models.CharField(max_length=6)
    verification_type = models.CharField(max_length=20, choices=VerificationType.choices)
    is_verified = models.BooleanField(default=False)
    attempts = models.PositiveSmallIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expired_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'phone_verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Phone verification for {self.phone_number}"
    
    def is_expired(self):
        return timezone.now() > self.expired_at
    
    def save(self, *args, **kwargs):
        if not self.expired_at:
            self.expired_at = timezone.now() + timezone.timedelta(minutes=10)
        super().save(*args, **kwargs)


# ============= Helper Functions =============

def get_operator_from_phone(phone_number):
    """
    Detect mobile operator from Bangladeshi phone number
    """
    # Remove all non-digit characters
    cleaned = re.sub(r'\D', '', phone_number)
    
    # Remove country code if present
    if cleaned.startswith('880'):
        cleaned = cleaned[3:]
    if cleaned.startswith('0'):
        cleaned = cleaned[1:]
    
    # Check prefix
    if len(cleaned) >= 3:
        prefix = cleaned[:3]
        
        operators = {
            'Grameenphone': ['017', '013'],
            'Robi': ['018', '016'],
            'Banglalink': ['019', '014'],
            'Teletalk': ['015'],
            'Airtel': ['016'],
        }
        
        for operator, prefixes in operators.items():
            if prefix in prefixes:
                return operator
    
    return 'Unknown'






