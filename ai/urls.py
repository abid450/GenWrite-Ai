"""
URL configuration for ai project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from GenWrite_Ai.views import *
from security_alert.views import *
from accounts.views import UserViewSet
from security.views import *
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='users')
router.register(r'types', ContentTypeViewSet, basename='content_type')
router.register(r'tasks', ContentTaskViewSet, basename='content-task')
router.register(r'batches', BatchJobViewSet, basename='batch-job')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include(router.urls)),

     # ============= Authentication URLs =============
    # JWT Token endpoints
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),


     # ============= 2FA URLs =============
    path('2fa/login/', TwoFactorLoginView.as_view(), name='2fa_login'),
    path('2fa/verify/', TwoFactorVerifyView.as_view(), name='2fa_verify'),
    path('2fa/enable/', TwoFAEnableView.as_view(), name='2fa_enable'),
    path('2fa/verify-enable/', TwoFAVerifyEnableView.as_view(), name='2fa_verify_enable'),
    path('2fa/disable/', TwoFADisableView.as_view(), name='2fa_disable'),


    path('security/suspicious/', SuspiciousActivityListView.as_view(), name='suspicious_activities'),
    path('security/suspicious/<int:activity_id>/resolve/', ResolveSuspiciousActivityView.as_view(), name='resolve_activity'),
    path('security/alerts/', SecurityAlertListView.as_view(), name='security_alerts'),
    path('security/alerts/<int:alert_id>/acknowledge/', AcknowledgeAlertView.as_view(), name='acknowledge_alert'),
    path('security/block-ip/', BlockIPView.as_view(), name='block_ip'),
    path('security/dashboard/', SecurityDashboardView.as_view(), name='security_dashboard'),
    path('security/my-security/', UserSecurityView.as_view(), name='my_security'),
]



