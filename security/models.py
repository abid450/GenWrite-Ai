from django.db import models
# Create your models here.
from django.db import models
from django.utils import timezone
from django.conf import settings

# Create your models here.

# ------------------------Login ------------------------------------------
class EmailOTP(models.Model):
    """
    Simple Email OTP Model for 2FA
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_otp'
    )

    otp_code = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    otp_attempts = models.PositiveSmallIntegerField(default=0)
    is_2fa_enabled = models.BooleanField(default=False)
    enabled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'email_otps'

    def __str__(self):
        return f"Email OTP for {self.user.email} - {'Enabled' if self.is_2fa_enabled else 'Disabled'}"
    
    def generate_otp(self):
        import random
        self.otp_code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        self.otp_expires_at = timezone.now() + timezone.timedelta(minutes=10)
        self.otp_attempts = 0
        self.save(update_fields=['otp_code', 'otp_expires_at', 'otp_attempts'])
        return self.otp_code
    
    def verify_otp(self, code):
        """Verify OTP code"""
        if not self.otp_code or not self.otp_expires_at:
            return False
        
        # Check expiry
        if timezone.now() > self.otp_expires_at:
            return False
        
        # Check attempts (max 5)
        if self.otp_attempts >= 5:
            return False
        
        # Verify code
        if self.otp_code == code:
            # Clear OTP after successful verification
            self.otp_code = None
            self.otp_expires_at = None
            self.save(update_fields=['otp_code', 'otp_expires_at'])
            return True
        
        # Increment failed attempts
        self.otp_attempts += 1
        self.save(update_fields=['otp_attempts'])
        return False
    
    def enable_2fa(self):
        """Enable 2FA for user"""
        self.is_2fa_enabled = True
        self.enabled_at = timezone.now()
        self.save(update_fields=['is_2fa_enabled', 'enabled_at'])
        return True
    
    def disable_2fa(self):
        """Disable 2FA for user"""
        self.is_2fa_enabled = False
        self.otp_code = None
        self.otp_expires_at = None
        self.otp_attempts = 0
        self.save()
        return True
    

class LoginSession(models.Model):
     """
    Track user login sessions with device, IP, OS info
    """
     user = models.ForeignKey(
         settings.AUTH_USER_MODEL,
         on_delete=models.CASCADE,
         related_name= 'login_sessions'
     )

     session_token = models.CharField(max_length=100, unique=True)
     is_active = models.BooleanField(default=True)
     device_type = models.CharField(max_length=50, blank=True, null=True)
     device_name = models.CharField(max_length=150, blank=True, null=True)
     browser = models.CharField(max_length=100, blank=True, null=True)
     browser_version = models.CharField(max_length=50, blank=True, null=True)
     os = models.CharField(max_length=100, blank=True, null=True)
     os_version = models.CharField(max_length=50, blank=True, null=True)

     ip_address = models.GenericIPAddressField(blank=True, null=True)
     location = models.CharField(max_length=170, blank=True, null=True)
     isp = models.CharField(max_length=200, blank=True, null=True)  # Internet Provider
    
    # 2FA info
     used_2fa = models.BooleanField(default=False)
     otp_code_used = models.CharField(max_length=6, blank=True, null=True)
    
    # Timestamps
     login_time = models.DateTimeField(auto_now_add=True)
     last_activity = models.DateTimeField(auto_now=True)
     logout_time = models.DateTimeField(blank=True, null=True)

     class Meta:
         db_table = 'login_sessions'
         ordering = ['-login_time']
         indexes = [
             models.Index(fields=['user', '-login_time']),
             models.Index(fields=['session_token']),
             models.Index(fields=['ip_address']),
         ]

     def __str__(self):
         return f"{self.user.email} - {self.login_time} - {self.device_type}"
     
     def get_duration(self):
         end_times = self.logout_time or timezone.now()
         delta = end_times - self.login_time
         return int(delta.total_seconds() / 60)
     
     def end_session(self):
         self.is_active = False
         self.logout_time = timezone.now()
         self.save(update_fields=['is_active', 'logout_time'])
         


class LoginLog(models.Model):
    """
    Log all login attempts (successful and failed)
    """
    class LoginStatus(models.TextChoices):
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        BLOCKED = 'blocked', 'Blocked'
        OTP_REQUIRED = 'otp_required', 'OTP Required'
        OTP_FAILED = 'otp_failed', 'OTP Failed'
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='login_logs',
        null=True
    )
    session = models.ForeignKey(LoginSession, on_delete=models.SET_NULL, null=True)
    
    # Login info
    status = models.CharField(max_length=20, choices=LoginStatus.choices)
    email = models.EmailField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Device info
    device_type = models.CharField(max_length=50, blank=True, null=True)
    device_name = models.CharField(max_length=200, blank=True, null=True)
    browser = models.CharField(max_length=100, blank=True, null=True)
    browser_version = models.CharField(max_length=50, blank=True, null=True)
    os = models.CharField(max_length=100, blank=True, null=True)
    os_version = models.CharField(max_length=50, blank=True, null=True)
    
    # Network info
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Error info
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'login_logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.email or self.username} - {self.status} - {self.created_at}"
    



# Suspicious Activity -----------------------------------------------
class SuspiciousActivity(models.Model):

    class ActivityType(models.TextChoices):
        BRUTE_FORCE = 'brute_force', 'Brute Force Attack'
        MULTIPLE_FAILED_LOGINS = 'multiple_failed', 'Multiple Failed Logins'
        UNUSUAL_LOCATION = 'unusual_location', 'Unusual Location Login'
        UNUSUAL_DEVICE = 'unusual_device', 'Unusual Device Login'
        UNUSUAL_TIME = 'unusual_time', 'Unusual Time Login'
        VERIFICATION_FAILED = 'verification_failed', 'Multiple Verification Failures'
        ACCOUNT_FROZEN = 'account_frozen', 'Account Frozen'
        PASSWORD_RESET_ABUSE = 'password_reset_abuse', 'Password Reset Abuse'

    
    class Severity(models.IntegerChoices):
        LOW = 1, 'Low'
        MEDIUM = 2, 'medium'
        HIGH = 3, 'high'
        CRITICAL = 4, 'critical'
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='suspicious_activities', null=True, blank=True)
    activity_type = models.CharField(max_length=50, choices=ActivityType.choices)
    severity = models.IntegerField(choices=Severity.choices, default=Severity.MEDIUM)

    ip_address = models.GenericIPAddressField()
    location = models.CharField(max_length=200, blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    device_info = models.JSONField(default=dict, blank=True)

    details = models.TextField(blank=True, null=True)
    metadata = models.JSONField(default=dict, blank=True) 

    # Status
    is_resolved = models.BooleanField(default=False)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.CharField(max_length=150, blank=True, null=True)
    resolution_note = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'suspicious_activities'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['activity_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['is_resolved']),
        ]
    

    def __str__(self):
        return f"{self.get_activity_type_display()} - {self.ip_address} - {self.created_at}"
    
    def resolve(self, resolved_by, note=None):
        self.is_resolved = True
        self.resolved_at = timezone.now()
        self.resolved_by = resolved_by
        self.resolution_note = note
        self.save(update_fields=['is_resolved', 'resolved_at', 'resolved_by', 'resolution_note'])




# Security Alert --------------------------------------------------------------
class SecurityAlert(models.Model):
    """
    Security alerts for real-time monitoring
    """
    class AlertType(models.TextChoices):
        SUSPICIOUS_LOGIN = 'suspicious_login', 'Suspicious Login'
        BRUTE_FORCE = 'brute_force', 'Brute Force Detected'
        DATA_BREACH = 'data_breach', 'Potential Data Breach'
        ACCOUNT_TAKEOVER = 'account_takeover', 'Account Takeover Attempt'
        API_ABUSE = 'api_abuse', 'API Abuse Detected'

    class Priority(models.IntegerChoices):
        LOW = 1, 'Low'
        MEDIUM = 2, 'Medium'
        HIGH = 3, 'High'
        URGENT = 4, 'Urgent'

    title = models.CharField(max_length=150)
    alert_type = models.CharField(max_length=50, choices=AlertType.choices)
    priority = models.CharField(choices=Priority.choices, default=Priority.MEDIUM)

    # Related data
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    suspicious_activity = models.ForeignKey(SuspiciousActivity, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Details
    message = models.TextField()
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True, null=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_acknowledged = models.BooleanField(default=False)
    acknowledged_by = models.CharField(max_length=150, blank=True, null=True)
    acknowledged_at = models.DateTimeField(blank=True, null=True)
    
    # Action taken
    action_taken = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'security_alerts'
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"


# Login Security details ------------------------------------------------
class LoginSecurityMetrics(models.Model):
    """
    Daily login security metrics for analytics
    """
    date = models.DateField(unique=True)
    
    # Login metrics
    total_logins = models.IntegerField(default=0)
    successful_logins = models.IntegerField(default=0)
    failed_logins = models.IntegerField(default=0)
    
    # User metrics
    unique_users_logged_in = models.IntegerField(default=0)
    new_users_logged_in = models.IntegerField(default=0)
    
    # Security metrics
    suspicious_activities = models.IntegerField(default=0)
    brute_force_attempts = models.IntegerField(default=0)
    blocked_ips = models.IntegerField(default=0)
    
    # Device metrics
    mobile_logins = models.IntegerField(default=0)
    desktop_logins = models.IntegerField(default=0)
    tablet_logins = models.IntegerField(default=0)
    
    # Location metrics
    unique_locations = models.IntegerField(default=0)
    
    # JSON fields for detailed stats
    top_ips = models.JSONField(default=list, blank=True)
    top_devices = models.JSONField(default=list, blank=True)
    hourly_distribution = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'login_security_metrics'
        ordering = ['-date']
    
    def __str__(self):
        return f"Metrics for {self.date}"

     