from django.shortcuts import render
from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count, Q
from security.models import SuspiciousActivity, SecurityAlert, LoginSecurityMetrics, LoginLog, LoginSession
# Create your views here.

from security.serializers import SuspiciousActivitySerializer, LoginSecurityMetricsSerializer, SecurityAlertSerializer
from security.utils import calculate_login_metrics, is_ip_blocked, block_ip

import logging

logger = logging.getLogger(__name__)




class SuspiciousActivityListView(APIView):
    """
    List all suspicious activities (Admin only)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        activities = SuspiciousActivity.objects.all().order_by('-severity', '-created_at')
        
        # Apply filters
        status_filter = request.GET.get('status')
        severity_filter = request.GET.get('severity')
        user_id = request.GET.get('user_id')
        
        if status_filter == 'resolved':
            activities = activities.filter(is_resolved=True)
        elif status_filter == 'unresolved':
            activities = activities.filter(is_resolved=False)
        
        if severity_filter:
            activities = activities.filter(severity=severity_filter)
        
        if user_id:
            activities = activities.filter(user_id=user_id)
        
        serializer = SuspiciousActivitySerializer(activities, many=True)
        return Response({
            'count': activities.count(),
            'results': serializer.data
        })


class ResolveSuspiciousActivityView(APIView):
    """
    Resolve a suspicious activity
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, activity_id):
        try:
            activity = SuspiciousActivity.objects.get(id=activity_id)
            note = request.data.get('note', '')
            
            activity.resolve(
                resolved_by=request.user.username,
                note=note
            )
            
            return Response({
                'success': True,
                'message': 'Activity resolved successfully'
            })
        except SuspiciousActivity.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Activity not found'
            }, status=status.HTTP_404_NOT_FOUND)


class SecurityAlertListView(APIView):
    """
    List security alerts (Admin only)
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        alerts = SecurityAlert.objects.all().order_by('-priority', '-created_at')
        
        # Filter by read status
        read_filter = request.GET.get('read')
        if read_filter == 'false':
            alerts = alerts.filter(is_read=False)
        
        serializer = SecurityAlertSerializer(alerts, many=True)
        return Response({
            'unread_count': alerts.filter(is_read=False).count(),
            'high_priority_count': alerts.filter(priority=4, is_read=False).count(),
            'results': serializer.data
        })


class AcknowledgeAlertView(APIView):
    """
    Acknowledge a security alert
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request, alert_id):
        try:
            alert = SecurityAlert.objects.get(id=alert_id)
            alert.is_read = True
            alert.is_acknowledged = True
            alert.acknowledged_by = request.user.username
            alert.acknowledged_at = timezone.now()
            alert.save()
            
            return Response({
                'success': True,
                'message': 'Alert acknowledged'
            })
        except SecurityAlert.DoesNotExist:
            return Response({
                'success': False,
                'error': 'Alert not found'
            }, status=status.HTTP_404_NOT_FOUND)


class BlockIPView(APIView):
    """
    Block an IP address
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def post(self, request):
        ip_address = request.data.get('ip_address')
        duration = request.data.get('duration', 60)  # minutes
        reason = request.data.get('reason', 'Manual block')
        
        if not ip_address:
            return Response({
                'success': False,
                'error': 'IP address required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        block_ip(ip_address, duration, reason)
        
        return Response({
            'success': True,
            'message': f'IP {ip_address} blocked for {duration} minutes'
        })


class SecurityDashboardView(APIView):
    """
    Security dashboard with analytics
    """
    permission_classes = [IsAuthenticated, IsAdminUser]
    
    def get(self, request):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        # Calculate metrics for today
        calculate_login_metrics(today)
        
        # Get recent metrics
        recent_metrics = LoginSecurityMetrics.objects.filter(
            date__gte=week_ago
        ).order_by('-date')
        
        # Get unresolved suspicious activities
        unresolved_activities = SuspiciousActivity.objects.filter(
            is_resolved=False
        ).count()
        
        critical_activities = SuspiciousActivity.objects.filter(
            is_resolved=False,
            severity=4
        ).count()
        
        # Get unread alerts
        unread_alerts = SecurityAlert.objects.filter(is_read=False).count()
        
        # Get blocked IPs summary
        # (This is approximate - actual blocked IPs are in cache)
        
        return Response({
            'summary': {
                'unresolved_activities': unresolved_activities,
                'critical_activities': critical_activities,
                'unread_alerts': unread_alerts,
            },
            'metrics': {
                'recent': LoginSecurityMetricsSerializer(recent_metrics, many=True).data
            }
        })


class UserSecurityView(APIView):
    """
    Get security info for current user
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get recent login sessions
        recent_sessions = LoginSession.objects.filter(
            user=user,
            is_active=False
        ).order_by('-login_time')[:10]
        
        session_data = []
        for session in recent_sessions:
            session_data.append({
                'device': f"{session.device_name} ({session.device_type})",
                'browser': session.browser,
                'os': session.os,
                'ip_address': session.ip_address,
                'location': session.location,
                'login_time': session.login_time,
                'logout_time': session.logout_time
            })
        
        # Get login attempts
        recent_attempts = LoginLog.objects.filter(user=user).order_by('-created_at')[:20]
        attempt_data = []
        for attempt in recent_attempts:
            attempt_data.append({
                'status': attempt.status,
                'device': attempt.device_name,
                'ip_address': attempt.ip_address,
                'location': attempt.location,
                'created_at': attempt.created_at
            })
        
        # Get suspicious activities for this user
        suspicious_activities = SuspiciousActivity.objects.filter(user=user).order_by('-created_at')[:10]
        suspicious_data = SuspiciousActivitySerializer(suspicious_activities, many=True).data
        
        return Response({
            'email': user.email,
            'is_2fa_enabled': hasattr(user, 'email_otp') and user.email_otp.is_2fa_enabled,
            'recent_sessions': session_data,
            'recent_login_attempts': attempt_data,
            'suspicious_activities': suspicious_data
        })