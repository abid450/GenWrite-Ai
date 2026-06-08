from django.shortcuts import render

# Create your views here.
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EmailVerification, VerificationLog
from .serializers import (
    UserSerializer, UserRegistrationSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, ChangePasswordSerializer,
    UserProfileUpdateSerializer, UserDetailSerializer
)
from .tasks import send_verification_email, send_welcome_email
from .permissions import IsOwnerOrAdmin
from .utils import get_client_ip, get_user_agent


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserRegistrationSerializer
        elif self.action == 'update_profile':
            return UserProfileUpdateSerializer
        elif self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'verify_email', 'resend_verification']:
            return [AllowAny()]
        return super().get_permissions()
    
    def create(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        verification = EmailVerification.objects.get(user=user)
        send_verification_email.delay(user.id, verification.verification_code)
        
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'message': f'Verification email sent to {user.email}'
        }, status=status.HTTP_201_CREATED)
    
    @action(detail=False, methods=['post'], url_path='verify-email')
    def verify_email(self, request):
        serializer = EmailVerificationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        verification = serializer.validated_data['verification']
        verification.request_ip = get_client_ip(request)
        verification.user_agent = get_user_agent(request)
        verification.save(update_fields=['request_ip', 'user_agent'])
        verification.mark_as_verified()
        send_welcome_email.delay(verification.user.id)

        VerificationLog.objects.create(
            user= verification.user,
            verification=verification,
            action='verify',
            status='success',
            ip_address=get_client_ip(request),
            user_agent=get_user_agent(request)
        )
        
        return Response({
            'success': True,
            'message': 'Email verified successfully!'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='resend-verification')
    def resend_verification(self, request):
        serializer = ResendVerificationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = serializer.user
        verification, created = EmailVerification.objects.get_or_create(
            user=user,
            defaults={'verification_code': '000000'}  # Temporary, will be regenerated
        )
        
        new_code = verification.regenerate_code()
        send_verification_email.delay(user.id, new_code)
        
        return Response({
            'success': True,
            'message': f'Verification code sent to {user.email}'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['post'], url_path='change-password', permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'success': True,
            'message': 'Password changed successfully'
        }, status=status.HTTP_200_OK)
    
    @action(detail=False, methods=['get'], url_path='me', permission_classes=[IsAuthenticated])
    def get_me(self, request):
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['put', 'patch'], url_path='profile', permission_classes=[IsAuthenticated])
    def update_profile(self, request):
        user = request.user
        serializer = UserProfileUpdateSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserDetailSerializer(user).data)
    
    @action(detail=False, methods=['get'], url_path='verification-status', permission_classes=[IsAuthenticated])
    def verification_status(self, request):
        user = request.user
        if user.is_email_verified:
            return Response({'is_verified': True, 'verified_at': user.email_verified_at})
        
        try:
            verification = EmailVerification.objects.get(user=user)
            return Response({
                'is_verified': False,
                'status': verification.status,
                'expires_at': verification.expired_at,
                'attempts_remaining': 5 - verification.attempts
            })
        except EmailVerification.DoesNotExist:
            return Response({'is_verified': False, 'status': 'not_started'})