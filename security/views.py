from django.shortcuts import render
# Create your views here.
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.core.cache import cache
from security.models import EmailOTP, LoginSession, LoginLog
from .serializers import *
from accounts.tasks import send_2fa_otp_email
from .utils import *
import logging
import uuid
from django.contrib.auth import get_user_model


logger = logging.getLogger(__name__)


User = get_user_model()

# ============= 2FA Login Views =============
class TwoFactorLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TwoFactorLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        email = serializer.validated_data['email']

        check_all_security_rules(
            user=user,
            request=request,
            is_successful=True,
            otp_attempts=0
        )

        device_info = parse_device_info(request)
        client_ip = get_client_ip(request)
        location = get_location_from_ip(client_ip)


        try:
            email_otp = EmailOTP.objects.get(user=user)
            requires_2fa = email_otp.is_2fa_enabled
        except EmailOTP.DoesNotExist:
            requires_2fa = False

        if not requires_2fa:
            refresh = RefreshToken.for_user(user)

        
        # Create session
            session_token = generate_session_token()
            session = LoginSession.objects.create(
                user=user,
                session_token=session_token,
                is_active=True,
                device_type=device_info['device_type'],
                device_name=device_info['device_name'],
                browser=device_info['browser'],
                browser_version=device_info['browser_version'],
                os=device_info['os'],
                os_version=device_info['os_version'],
                ip_address=client_ip,
                location=location,
                used_2fa=False
            )
            
            # Update user last login
            user.last_login = timezone.now()
            user.last_login_ip = client_ip
            user.save(update_fields=['last_login', 'last_login_ip'])
            
            # Log success
            LoginLog.objects.create(
                user=user,
                session=session,
                status=LoginLog.LoginStatus.SUCCESS,
                email=user.email,
                username=user.username,
                device_type=device_info['device_type'],
                device_name=device_info['device_name'],
                browser=device_info['browser'],
                os=device_info['os'],
                ip_address=client_ip,
                location=location
            )
            
            logger.info(f"User {user.email} logged in from {client_ip} ({device_info['device_type']})")
            
            return Response({
                'success': True,
                'requires_2fa': False,
                'tokens': {
                    'access': str(refresh.access_token),
                    'refresh': str(refresh),
                },
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_email_verified': user.is_email_verified,
                },
                'session': {
                    'token': session_token,
                    'device': device_info['device_name'],
                    'location': location,
                    'login_time': session.login_time
                }
            })
        
        # 2FA Required - Generate OTP
        email_otp, created = EmailOTP.objects.get_or_create(user=user)
        otp_code = email_otp.generate_otp()
        
        # Send OTP via Celery (background)
        send_2fa_otp_email.delay(user.id, otp_code)
        
        # Create temp session for OTP verification
        temp_token = str(uuid.uuid4())
        cache.set(f"2fa_temp_{temp_token}", {
            'user_id': user.id,
            'device_info': device_info,
            'client_ip': client_ip,
            'location': location,
            'created_at': timezone.now().isoformat()
        }, timeout=300)  # 5 minutes
        
        # Log OTP required
        LoginLog.objects.create(
            user=user,
            status=LoginLog.LoginStatus.OTP_REQUIRED,
            email=user.email,
            username=user.username,
            device_type=device_info['device_type'],
            device_name=device_info['device_name'],
            browser=device_info['browser'],
            os=device_info['os'],
            ip_address=client_ip,
            location=location
        )
        
        logger.info(f"2FA OTP sent to {user.email} for login from {client_ip}")
        
        return Response({
            'success': True,
            'requires_2fa': True,
            'temp_token': temp_token,
            'message': f'Verification code sent to {user.email}',
            'expires_in': 10  # minutes
        })



class TwoFactorVerifyView(APIView):
    """
    Step 2: Verify OTP and complete login
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp_code']
        remember_device = serializer.validated_data.get('remember_device', False)
        
        # Get temp token from header or body
        temp_token = request.headers.get('X-Temp-Token') or request.data.get('temp_token')
        
        if not temp_token:
            return Response({
                'success': False,
                'error': 'Temp token required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get temp data from cache
        temp_data = cache.get(f"2fa_temp_{temp_token}")
        if not temp_data:
            return Response({
                'success': False,
                'error': 'Session expired. Please login again.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get user
        try:
            user = User.objects.get(id=temp_data['user_id'])
        except User.DoesNotExist:
            return Response({
                'success': False,
                'error': 'User not found'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify email matches
        if user.email != email:
            return Response({
                'success': False,
                'error': 'Email mismatch'
            }, status=status.HTTP_400_BAD_REQUEST)
        

        client_ip = temp_data.get('client_ip', get_client_ip(request))

        # Rate limiting check
        cache_key = f"otp_verify_{user.id}_{client_ip}"
        is_allowed, remaining = rate_limit_check(cache_key, limit=5, window=300)
        
        if not is_allowed:
            LoginLog.objects.create(
                user=user,
                status=LoginLog.LoginStatus.BLOCKED,
                email=user.email,
                username=user.username,
                device_type=temp_data['device_info']['device_type'],
                ip_address=temp_data['client_ip'],
                location=temp_data['location'],
                error_message='Rate limit exceeded'
            )
            
            return Response({
                'success': False,
                'error': 'Too many attempts. Please try again later.'
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Verify OTP
        try:
            email_otp = EmailOTP.objects.get(user=user)
        except EmailOTP.DoesNotExist:
            return Response({
                'success': False,
                'error': '2FA not enabled for this account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_otp.verify_otp(otp_code):
            LoginLog.objects.create(
                user=user,
                status=LoginLog.LoginStatus.OTP_FAILED,
                email=user.email,
                username=user.username,
                device_type=temp_data['device_info']['device_type'],
                ip_address=temp_data['client_ip'],
                location=temp_data['location'],
                error_message='Invalid OTP code'
            )
            
            return Response({
                'success': False,
                'error': 'Invalid or expired OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # OTP verified - create session and login
        refresh = RefreshToken.for_user(user)
        
        # Create login session
        session_token = generate_session_token()
        session = LoginSession.objects.create(
            user=user,
            session_token=session_token,
            is_active=True,
            device_type=temp_data['device_info']['device_type'],
            device_name=temp_data['device_info']['device_name'],
            browser=temp_data['device_info']['browser'],
            browser_version=temp_data['device_info']['browser_version'],
            os=temp_data['device_info']['os'],
            os_version=temp_data['device_info']['os_version'],
            ip_address=temp_data['client_ip'],
            location=temp_data['location'],
            used_2fa=True,
            otp_code_used=otp_code
        )
        
        # Update user last login
        user.last_login = timezone.now()
        user.last_login_ip = temp_data['client_ip']
        user.save(update_fields=['last_login', 'last_login_ip'])
        
        # Log success
        LoginLog.objects.create(
            user=user,
            session=session,
            status=LoginLog.LoginStatus.SUCCESS,
            email=user.email,
            username=user.username,
            device_type=temp_data['device_info']['device_type'],
            device_name=temp_data['device_info']['device_name'],
            browser=temp_data['device_info']['browser'],
            os=temp_data['device_info']['os'],
            ip_address=temp_data['client_ip'],
            location=temp_data['location']
        )
        
        # Clear temp cache
        cache.delete(f"2fa_temp_{temp_token}")
        
        logger.info(f"User {user.email} logged in with 2FA from {temp_data['client_ip']}")
        
        return Response({
            'success': True,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_email_verified': user.is_email_verified,
            },
            'session': {
                'token': session_token,
                'device': temp_data['device_info']['device_name'],
                'location': temp_data['location'],
                'login_time': session.login_time
            }
        })
    


# ============= 2FA Management Views =============

class TwoFAEnableView(APIView):
    """
    Enable 2FA for authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        email_otp, created = EmailOTP.objects.get_or_create(user=request.user)
        
        if email_otp.is_2fa_enabled:
            return Response({
                'success': False,
                'error': '2FA is already enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate test OTP to verify email works
        otp_code = email_otp.generate_otp()
        send_2fa_otp_email.delay(request.user.id, otp_code)
        
        return Response({
            'success': True,
            'message': f'Test OTP sent to {request.user.email}. Please verify to enable 2FA.',
            'requires_verification': True
        })


class TwoFAVerifyEnableView(APIView):
    """
    Verify OTP and enable 2FA
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return Response({
                'success': False,
                'error': 'OTP code required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_otp = EmailOTP.objects.get(user=request.user)
        except EmailOTP.DoesNotExist:
            return Response({
                'success': False,
                'error': '2FA not initialized'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if email_otp.is_2fa_enabled:
            return Response({
                'success': False,
                'error': '2FA is already enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_otp.verify_otp(otp_code):
            return Response({
                'success': False,
                'error': 'Invalid OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Enable 2FA
        email_otp.enable_2fa()
        
        logger.info(f"2FA enabled for user {request.user.email}")
        
        return Response({
            'success': True,
            'message': '2FA enabled successfully!'
        })


class TwoFADisableView(APIView):
    """
    Disable 2FA for authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        otp_code = request.data.get('otp_code')
        
        if not otp_code:
            return Response({
                'success': False,
                'error': 'OTP code required to disable 2FA'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            email_otp = EmailOTP.objects.get(user=request.user)
        except EmailOTP.DoesNotExist:
            return Response({
                'success': False,
                'error': '2FA is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_otp.is_2fa_enabled:
            return Response({
                'success': False,
                'error': '2FA is not enabled'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if not email_otp.verify_otp(otp_code):
            return Response({
                'success': False,
                'error': 'Invalid OTP code'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        email_otp.disable_2fa()
        
        logger.info(f"2FA disabled for user {request.user.email}")
        
        return Response({
            'success': True,
            'message': '2FA disabled successfully!'
        })