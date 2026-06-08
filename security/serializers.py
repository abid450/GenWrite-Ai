# accounts/serializers.py - যোগ করুন

from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import *

# security/views.py
from django.contrib.auth import get_user_model  # ← এই লাইন যোগ করুন

User = get_user_model()  # ← এই লাইন যোগ করুন

# এখন User ব্যবহার করুন
class TwoFactorLoginSerializer(serializers.Serializer):
    """
    Step 1: Login with email/password
    """
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)
    
    def validate(self, data):
        email = data.get('email')
        password = data.get('password')
        
        user = None

        try:
            user_obj = User.objects.get(email=email)
            user =  authenticate(username=user_obj.username, password=password)
        
        except User.DoesNotExist:
            pass
        
        if not user:
            raise serializers.ValidationError("Invalid email or password")
        
        # Check if user is active
        if not user.is_active:
            raise serializers.ValidationError("Account is deactivated")
        
        
        return {
            'user' : user,
            'email' : email
        }


class TwoFactorOTPSendSerializer(serializers.Serializer):
    """
    Resend OTP
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(min_length=6, max_length=6, required=True)
    remember_device = serializers.BooleanField(default=False)
    


class TwoFactorVerifySerializer(serializers.Serializer):
    """
    Step 2: Verify OTP and complete login
    """
    email = serializers.EmailField(required=True)
    otp_code = serializers.CharField(min_length=6, max_length=6)
    remember_device = serializers.BooleanField(default=False)


class TwoFAEnableSerializer(serializers.Serializer):
    """
    Enable 2FA for user
    """
    pass  # No fields needed, just POST request


class TwoFADisableSerializer(serializers.Serializer):
    """
    Disable 2FA for user
    """
    otp_code = serializers.CharField(min_length=6, max_length=6, required=True)


class LoginSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for login session info
    """
    duration_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = LoginSession
        fields = [
            'id', 'device_type', 'device_name', 'browser', 'os',
            'ip_address', 'location', 'login_time', 'last_activity',
            'logout_time', 'is_active', 'duration_minutes'
        ]
    
    def get_duration_minutes(self, obj):
        return obj.get_duration()
    


class SuspiciousActivitySerializer(serializers.ModelSerializer):
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    user_email = serializers.CharField(source='user.email', read_only=True)

    class Meta:
        model = SuspiciousActivity
        fields = [

            'id', 'user', 'user_email', 'activity_type', 'activity_type_display',
            'severity', 'severity_display', 'ip_address', 'location',
            'user_agent', 'details', 'metadata', 'is_resolved',
            'created_at', 'resolved_at', 'resolved_by', 'resolution_note'
        ]

    
class SecurityAlertSerializer(serializers.ModelSerializer):
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    
    class Meta:
        model = SecurityAlert
        fields = [
            'id', 'title', 'alert_type', 'alert_type_display', 'priority',
            'priority_display', 'user', 'message', 'ip_address', 'location',
            'is_read', 'is_acknowledged', 'created_at'
        ]



class LoginSecurityMetricsSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoginSecurityMetrics
        fields = '__all__'