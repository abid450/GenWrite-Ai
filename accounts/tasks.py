import logging
from celery import shared_task
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from datetime import datetime, timedelta
from .models import User, EmailVerification, VerificationLog

logger = logging.getLogger(__name__)


# ============= Core Email Tasks =============

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_verification_email(self, user_id, verification_code):
    """
    Send verification email to user (runs in background with Celery)
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = 'Verify Your Email Address'
        
        # HTML email template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .code {{ font-size: 36px; font-weight: bold; color: #4CAF50; 
                         letter-spacing: 5px; text-align: center; padding: 20px; 
                         background: white; border-radius: 10px; margin: 20px 0; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #4CAF50; 
                          color: white; text-decoration: none; border-radius: 5px; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #999; }}
                .warning {{ color: #ff9800; font-size: 12px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔐 Email Verification</h2>
                </div>
                <div class="content">
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>Thank you for registering! Please verify your email address by entering the code below:</p>
                    
                    <div class="code">
                        {verification_code}
                    </div>
                    
                    <p>This code will expire in <strong>{settings.VERIFICATION_CODE_EXPIRY_MINUTES} minutes</strong>.</p>
                    
                    <p>If you didn't create an account, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                    <p>&copy; 2024 Email Verification System</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # Plain text version
        text_content = f"""
        Hello {user.username},
        
        Thank you for registering! Your verification code is: {verification_code}
        
        This code will expire in {settings.VERIFICATION_CODE_EXPIRY_MINUTES} minutes.
        
        If you didn't create an account, please ignore this email.
        
        ---
        This is an automated message, please do not reply.
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        # Log successful email send
        VerificationLog.objects.create(
            user=user,
            action='send_verification',
            status='success',
        )
        
        logger.info(f"Verification email sent to {user.email}")
        return {
            'status': 'success',
            'message': f'Verification email sent to {user.email}',
            'user_id': user_id
        }
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'failed', 'error': 'User not found'}
        
    except Exception as e:
        logger.error(f"Failed to send verification email: {str(e)}")
        
        # Log failure
        try:
            user = User.objects.get(id=user_id)
            VerificationLog.objects.create(
                user=user,
                action='send_verification',
                status='failed',
                error_message=str(e)
            )
        except:
            pass
        
        # Retry the task
        raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def send_welcome_email(self, user_id):
    """
    Send welcome email after successful verification
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = '🎉 Welcome to Our Platform!'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ padding: 30px; background: #f9f9f9; }}
                .button {{ display: inline-block; padding: 12px 24px; background: #2196F3; 
                          color: white; text-decoration: none; border-radius: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Welcome Aboard! 🎉</h2>
                </div>
                <div class="content">
                    <p>Dear <strong>{user.username}</strong>,</p>
                    <p>Your email has been successfully verified!</p>
                    <p>Welcome to our platform. We're excited to have you on board.</p>
                    <p>You can now:</p>
                    <ul>
                        <li>Access all features</li>
                        <li>Update your profile</li>
                        <li>Connect with other users</li>
                    </ul>
                    <p>Best regards,<br>The Team</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Welcome to Our Platform!
        
        Dear {user.username},
        
        Your email has been successfully verified!
        
        Welcome aboard!
        
        Best regards,
        The Team
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Welcome email sent to {user.email}")
        return {'status': 'success', 'message': f'Welcome email sent to {user.email}'}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'failed', 'error': 'User not found'}
        
    except Exception as e:
        logger.error(f"Failed to send welcome email: {str(e)}")
        raise self.retry(exc=e, countdown=30)


# ============= Cleanup Tasks =============

@shared_task
def cleanup_expired_verifications():
    """
    Periodic task to clean up expired verifications
    """
    try:
        expired = EmailVerification.objects.filter(
            expired_at__lte=timezone.now(),
            status__in=['pending', 'failed']
        )
        
        count = expired.count()
        expired.update(status='expired')
        
        logger.info(f"Cleaned up {count} expired verifications")
        return {
            'status': 'success',
            'cleaned_up': count,
            'message': f'Successfully cleaned up {count} expired verifications'
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup expired verifications: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


@shared_task
def cleanup_old_logs():
    """
    Clean up old verification logs (older than 30 days)
    """
    try:
        cutoff_date = timezone.now() - timedelta(days=30)
        deleted_count = VerificationLog.objects.filter(created_at__lte=cutoff_date).delete()[0]
        
        logger.info(f"Cleaned up {deleted_count} old logs")
        return {
            'status': 'success',
            'deleted_count': deleted_count,
            'message': f'Cleaned up {deleted_count} logs older than 30 days'
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old logs: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= DAILY REPORT TASK =============

@shared_task(bind=True, max_retries=3, default_retry_delay=300)
def send_daily_report(self):
    """
    Advanced Daily Report with Analytics
    - User Analytics
    - Login Security Analytics
    - Suspicious Activity Tracking
    - Email Verification Analytics
    """
    try:
    
        from django.contrib.auth import get_user_model
        from accounts.models import EmailVerification
    
        
        User = get_user_model()
        
        today = timezone.now().date()
        today_start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
        today_end = timezone.make_aware(datetime.combine(today, datetime.max.time()))
        
        # ============= 1. USER ANALYTICS =============
        
        # New users today
        new_users = User.objects.filter(date_joined__range=(today_start, today_end)).count()
        
        # Verified users today
        verified_users = User.objects.filter(email_verified_at__range=(today_start, today_end)).count()
        
        # Total users
        total_users = User.objects.count()
        verified_total = User.objects.filter(is_email_verified=True).count()
        
        # User growth (last 7 days vs previous 7 days)
        last_7_days_start = today_start - timedelta(days=7)
        previous_7_days_start = last_7_days_start - timedelta(days=7)
        
        new_users_last_7 = User.objects.filter(date_joined__gte=last_7_days_start).count()
        new_users_previous_7 = User.objects.filter(
            date_joined__range=(previous_7_days_start, last_7_days_start - timedelta(seconds=1))
        ).count()
        
        growth_percentage = ((new_users_last_7 - new_users_previous_7) / new_users_previous_7 * 100) if new_users_previous_7 > 0 else 0
        
        # Daily average users (last 30 days)
        last_30_days_start = today_start - timedelta(days=30)
        users_last_30 = User.objects.filter(date_joined__gte=last_30_days_start).count()
        daily_avg = users_last_30 / 30 if users_last_30 > 0 else 0
        
        # ============= 2. LOGIN & SECURITY ANALYTICS =============
        
        # Try to get LoginHistory from security app
        successful_logins = 0
        failed_logins = 0
        unique_ips = 0
        most_active_users = []
        
        try:
            from security.models import LoginLog
            
            # Login success vs failure
            successful_logins = LoginLog.objects.filter(
                created_at__range=(today_start, today_end),
                status='success'
            ).count()
            
            failed_logins = LoginLog.objects.filter(
                created_at__range=(today_start, today_end),
                status__in=['failed', 'otp_failed']
            ).count()
            
            total_logins = successful_logins + failed_logins
            login_success_rate = (successful_logins / total_logins * 100) if total_logins > 0 else 0
            
            # Unique IPs
            unique_ips = LoginLog.objects.filter(
                created_at__range=(today_start, today_end)
            ).values('ip_address').distinct().count()
            
            # Most active users
            most_active_users = LoginLog.objects.filter(
                created_at__range=(today_start, today_end),
                status='success'
            ).values('user__email').annotate(
                login_count=Count('id')
            ).order_by('-login_count')[:5]
            
        except ImportError:
            logger.warning("Security app not found, login analytics skipped")
        
        # ============= 3. SUSPICIOUS ACTIVITIES =============
        
        suspicious_count = 0
        critical_activities = 0
        suspicious_by_type = []
        top_suspicious_ips = []
        needs_alert = False
        
        try:
            from security.models import SuspiciousActivity
            
            suspicious_count = SuspiciousActivity.objects.filter(
                created_at__range=(today_start, today_end)
            ).count()
            
            critical_activities = SuspiciousActivity.objects.filter(
                created_at__range=(today_start, today_end),
                severity__gte=3
            ).count()
            
            suspicious_by_type = SuspiciousActivity.objects.filter(
                created_at__range=(today_start, today_end)
            ).values('activity_type').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            top_suspicious_ips = SuspiciousActivity.objects.filter(
                created_at__range=(today_start, today_end)
            ).values('ip_address').annotate(
                count=Count('id')
            ).order_by('-count')[:5]
            
            needs_alert = critical_activities > 5 or suspicious_count > 20
            
        except ImportError:
            logger.warning("Security app not found, suspicious activity analytics skipped")
        
        # ============= 4. EMAIL VERIFICATION ANALYTICS =============
        
        pending_verifications = EmailVerification.objects.filter(
            status='pending',
            is_used=False
        ).count()
        
        expired_verifications = EmailVerification.objects.filter(
            expired_at__lte=timezone.now(),
            is_used=False
        ).count()
        
        # Average verification time
        verified_records = EmailVerification.objects.filter(
            verified_at__isnull=False,
            created_at__gte=last_30_days_start
        )
        avg_verification_time = 0
        if verified_records.exists():
            total_seconds = sum(
                (v.verified_at - v.created_at).total_seconds() 
                for v in verified_records
            )
            avg_verification_time = total_seconds / verified_records.count() / 60
        
        # ============= 5. ACTIVE USERS & RETENTION =============
        
        active_users_last_7 = 0
        retention_rate = 0
        
        try:
            from security.models import LoginLog
            
            active_users_last_7 = LoginLog.objects.filter(
                created_at__gte=today_start - timedelta(days=7)
            ).values('user').distinct().count()
            
            # User retention
            new_users_last_7_list = User.objects.filter(
                date_joined__gte=last_7_days_start
            ).values_list('id', flat=True)
            
            if len(new_users_last_7_list) > 0:
                retained_users = LoginLog.objects.filter(
                    user_id__in=new_users_last_7_list,
                    created_at__gte=last_7_days_start
                ).values('user').distinct().count()
                retention_rate = (retained_users / len(new_users_last_7_list) * 100)
                
        except ImportError:
            pass
        
        # ============= 6. HOURLY DISTRIBUTION =============
        
        hourly_data = []
        peak_hour = {'hour': 0, 'count': 0}
        
        for hour in range(24):
            hour_start = today_start + timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)
            count = User.objects.filter(
                date_joined__range=(hour_start, hour_end)
            ).count()
            hourly_data.append({'hour': hour, 'count': count})
            if count > peak_hour['count']:
                peak_hour = {'hour': hour, 'count': count}
        
        # ============= Prepare Email Content =============
        
        subject = f'📊 Daily Analytics Report - {today}'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px; }}
                .section {{ background: #f8f9fa; margin: 20px 0; padding: 20px; border-radius: 10px; }}
                .section h2 {{ color: #333; border-left: 4px solid #667eea; padding-left: 15px; }}
                .stat-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .stat-card {{ background: white; padding: 15px; border-radius: 8px; text-align: center; }}
                .stat-number {{ font-size: 28px; font-weight: bold; color: #667eea; }}
                .stat-label {{ color: #666; font-size: 14px; }}
                .trend-up {{ color: green; }}
                .trend-down {{ color: red; }}
                .alert {{ background: #fee2e2; border-left: 4px solid #ef4444; padding: 15px; margin: 15px 0; border-radius: 5px; }}
                table {{ width: 100%; border-collapse: collapse; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background: #f1f5f9; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Daily Analytics Report</h1>
                    <p>{today}</p>
                </div>
                
                {'<div class="alert"><strong>⚠️ ALERT:</strong> High suspicious activity detected! ' + str(critical_activities) + ' critical activities today.</div>' if needs_alert else ''}
                
                <!-- 1. User Analytics -->
                <div class="section">
                    <h2>👥 User Analytics</h2>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number">{new_users}</div><div class="stat-label">New Users</div></div>
                        <div class="stat-card"><div class="stat-number">{verified_users}</div><div class="stat-label">Email Verified</div></div>
                        <div class="stat-card"><div class="stat-number">{total_users:,}</div><div class="stat-label">Total Users</div></div>
                        <div class="stat-card"><div class="stat-number">{verified_total:,}</div><div class="stat-label">Verified Users</div></div>
                    </div>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number {growth_percentage >= 0 and 'trend-up' or 'trend-down'}">{growth_percentage:.1f}%</div><div class="stat-label">7-Day Growth</div></div>
                        <div class="stat-card"><div class="stat-number">{daily_avg:.1f}</div><div class="stat-label">Daily Avg (30d)</div></div>
                        <div class="stat-card"><div class="stat-number">{active_users_last_7:,}</div><div class="stat-label">Active Users (7d)</div></div>
                        <div class="stat-card"><div class="stat-number">{retention_rate:.1f}%</div><div class="stat-label">Retention Rate</div></div>
                    </div>
                </div>
                
                <!-- 2. Login & Security -->
                <div class="section">
                    <h2>🔐 Login & Security</h2>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number">{successful_logins:,}</div><div class="stat-label">Successful Logins</div></div>
                        <div class="stat-card"><div class="stat-number">{failed_logins:,}</div><div class="stat-label">Failed Logins</div></div>
                        <div class="stat-card"><div class="stat-number">{login_success_rate:.1f}%</div><div class="stat-label">Success Rate</div></div>
                        <div class="stat-card"><div class="stat-number">{unique_ips}</div><div class="stat-label">Unique IPs</div></div>
                    </div>
                    {f'<h3>🏆 Most Active Users</h3><table><tr><th>User</th><th>Logins</th></tr>' + ''.join(f'<tr><td>{u["user__email"]}</td><td>{u["login_count"]}</td></tr>' for u in most_active_users) + '</table>' if most_active_users else ''}
                </div>
                
                <!-- 3. Suspicious Activities -->
                <div class="section">
                    <h2>⚠️ Suspicious Activities</h2>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number">{suspicious_count}</div><div class="stat-label">Total Suspicious</div></div>
                        <div class="stat-card"><div class="stat-number">{critical_activities}</div><div class="stat-label">Critical (≥3)</div></div>
                    </div>
                    {f'<h3>By Type</h3><table><tr><th>Activity Type</th><th>Count</th></tr>' + ''.join(f'<tr><td>{s["activity_type"]}</td><td>{s["count"]}</td></tr>' for s in suspicious_by_type) + '</table>' if suspicious_by_type else ''}
                    {f'<h3>Top Suspicious IPs</h3><table><tr><th>IP Address</th><th>Attempts</th></tr>' + ''.join(f'<tr><td>{ip["ip_address"]}</td><td>{ip["count"]}</td></tr>' for ip in top_suspicious_ips) + '</table>' if top_suspicious_ips else ''}
                </div>
                
                <!-- 4. Email Verification -->
                <div class="section">
                    <h2>📧 Email Verification</h2>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number">{pending_verifications}</div><div class="stat-label">Pending</div></div>
                        <div class="stat-card"><div class="stat-number">{expired_verifications}</div><div class="stat-label">Expired</div></div>
                        <div class="stat-card"><div class="stat-number">{avg_verification_time:.1f}</div><div class="stat-label">Avg Time (min)</div></div>
                    </div>
                </div>
                
                <!-- 5. Peak Hours -->
                <div class="section">
                    <h2>⏰ Peak Activity Hours</h2>
                    <div class="stat-grid">
                        <div class="stat-card"><div class="stat-number">{peak_hour['hour']}:00 - {peak_hour['hour']+1}:00</div><div class="stat-label">Peak Hour</div></div>
                        <div class="stat-card"><div class="stat-number">{peak_hour['count']}</div><div class="stat-label">Registrations</div></div>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #999;">
                    <p>Generated at: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Daily Analytics Report - {today}
        =================================
        
        👥 USER ANALYTICS
        - New Users Today: {new_users}
        - Email Verified Today: {verified_users}
        - Total Users: {total_users:,}
        - Verified Users: {verified_total:,}
        - 7-Day Growth: {growth_percentage:.1f}%
        - Daily Avg (30 days): {daily_avg:.1f}
        - Active Users (Last 7 days): {active_users_last_7:,}
        - User Retention Rate: {retention_rate:.1f}%
        
        🔐 LOGIN & SECURITY
        - Successful Logins: {successful_logins:,}
        - Failed Logins: {failed_logins:,}
        - Login Success Rate: {login_success_rate:.1f}%
        - Unique IP Addresses: {unique_ips}
        
        ⚠️ SUSPICIOUS ACTIVITIES
        - Total Suspicious: {suspicious_count}
        - Critical (Severity ≥3): {critical_activities}
        
        📧 EMAIL VERIFICATION
        - Pending Verifications: {pending_verifications}
        - Expired Codes: {expired_verifications}
        - Avg Verification Time: {avg_verification_time:.1f} minutes
        
        ⏰ PEAK HOURS
        - Peak Registration Hour: {peak_hour['hour']}:00
        - Registrations: {peak_hour['count']}
        """
        
        # Send email
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [settings.EMAIL_HOST_USER]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"Daily analytics report sent for {today}")
        
        return {
            'status': 'success',
            'date': str(today),
            'stats': {
                'new_users': new_users,
                'total_users': total_users,
                'growth_rate': growth_percentage,
                'suspicious_count': suspicious_count,
                'needs_alert': needs_alert
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to send daily analytics report: {str(e)}")
        raise self.retry(exc=e, countdown=300)



# ============= Processing Tasks =============

@shared_task
def process_pending_emails():
    """
    Process and check pending email verifications
    """
    try:
        # Get pending verifications that are about to expire (within 5 minutes)
        warning_threshold = timezone.now() + timedelta(minutes=5)
        
        about_to_expire = EmailVerification.objects.filter(
            status='pending',
            is_used=False,
            expired_at__lte=warning_threshold,
            expired_at__gte=timezone.now()
        )
        
        expire_count = about_to_expire.count()
        
        # Get total pending
        total_pending = EmailVerification.objects.filter(
            status='pending',
            is_used=False
        ).count()
        
        logger.info(f"Pending verifications: {total_pending}, About to expire: {expire_count}")
        
        return {
            'status': 'success',
            'total_pending': total_pending,
            'about_to_expire': expire_count,
            'message': f'Found {total_pending} pending verifications'
        }
        
    except Exception as e:
        logger.error(f"Failed to process pending emails: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Test/Debug Tasks =============

@shared_task
def test_email_task():
    """
    Simple test task to check if Celery is working
    """
    logger.info("Test task executed successfully!")
    return {
        'status': 'success',
        'message': 'Celery is working properly!',
        'timestamp': str(timezone.now())
    }


@shared_task
def send_test_email(email_address):
    """
    Send a test email to verify email configuration
    """
    try:
        subject = 'Celery Test Email'
        message = f"""
        Hello,
        
        This is a test email from Celery.
        If you received this, your Celery + Email configuration is working properly!
        
        Timestamp: {timezone.now()}
        
        Best regards,
        Celery Worker
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [email_address],
            fail_silently=False,
        )
        
        logger.info(f"Test email sent to {email_address}")
        return {'status': 'success', 'message': f'Test email sent to {email_address}'}
        
    except Exception as e:
        logger.error(f"Failed to send test email: {str(e)}")
        return {'status': 'failed', 'error': str(e)}


# ============= Batch Processing Tasks =============

@shared_task
def send_bulk_verification_emails(user_ids, verification_codes):
    """
    Send verification emails to multiple users (batch processing)
    """
    results = {
        'success': [],
        'failed': [],
        'total': len(user_ids)
    }
    
    for i, user_id in enumerate(user_ids):
        try:
            result = send_verification_email.delay(user_id, verification_codes[i])
            results['success'].append({
                'user_id': user_id,
                'task_id': result.id
            })
        except Exception as e:
            results['failed'].append({
                'user_id': user_id,
                'error': str(e)
            })
    
    logger.info(f"Bulk email sent: {len(results['success'])} success, {len(results['failed'])} failed")
    return results


@shared_task
def cleanup_all_expired():
    """
    Comprehensive cleanup of all expired data
    """
    try:
        # Clean expired verifications
        expired_verifications = EmailVerification.objects.filter(
            expired_at__lte=timezone.now()
        )
        verifications_count = expired_verifications.count()
        expired_verifications.update(status='expired')
        
        # Clean old logs (90 days)
        cutoff_date = timezone.now() - timedelta(days=90)
        logs_count = VerificationLog.objects.filter(created_at__lte=cutoff_date).delete()[0]
        
        logger.info(f"Cleanup completed: {verifications_count} verifications, {logs_count} logs")
        
        return {
            'status': 'success',
            'expired_verifications': verifications_count,
            'deleted_logs': logs_count,
            'timestamp': str(timezone.now())
        }
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        return {'status': 'failed', 'error': str(e)}
    



# ============= NEW 2FA LOGIN TASKS (শুধু এই অংশটুকু যোগ করুন) =============

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_2fa_otp_email(self, user_id, otp_code):
    """
    Send 2FA OTP email for login
    This is the NEW task for 2FA login
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = 'Your 2FA Login Verification Code'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #6c63ff; color: white; padding: 20px; text-align: center; }}
                .code {{ font-size: 36px; font-weight: bold; color: #6c63ff; 
                         text-align: center; padding: 20px; background: #f4f4f4; 
                         letter-spacing: 5px; }}
                .warning {{ color: #ff9800; font-size: 12px; text-align: center; }}
                .footer {{ margin-top: 30px; text-align: center; font-size: 12px; color: #999; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>🔐 Two-Factor Authentication (2FA)</h2>
                </div>
                <div style="padding: 20px;">
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>We detected a login attempt to your account.</p>
                    <p>Your verification code is:</p>
                    <div class="code">{otp_code}</div>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                    <p class="warning">If you didn't attempt to login, please ignore this email.</p>
                </div>
                <div class="footer">
                    <p>This is an automated message, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        2FA Verification Code
        
        Hello {user.username},
        
        We detected a login attempt to your account.
        
        Your verification code is: {otp_code}
        
        This code will expire in 10 minutes.
        
        If you didn't attempt to login, please ignore this email.
        
        ---
        This is an automated message, please do not reply.
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"2FA OTP email sent to {user.email}")
        return {'status': 'success', 'user_id': user_id, 'otp_code': otp_code}
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'status': 'failed', 'error': 'User not found'}
    except Exception as e:
        logger.error(f"Failed to send 2FA OTP email: {str(e)}")
        raise self.retry(exc=e, countdown=60)


@shared_task
def send_2fa_enable_test_otp(self, user_id, otp_code):
    """
    Send test OTP when user enables 2FA
    This is the NEW task for enabling 2FA
    """
    try:
        user = User.objects.get(id=user_id)
        
        subject = '2FA Setup - Test Verification Code'
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #4CAF50; color: white; padding: 20px; text-align: center; }}
                .code {{ font-size: 36px; font-weight: bold; color: #4CAF50; 
                         text-align: center; padding: 20px; background: #f4f4f4; 
                         letter-spacing: 5px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Enable 2FA - Test Verification</h2>
                </div>
                <div style="padding: 20px;">
                    <p>Hello <strong>{user.username}</strong>,</p>
                    <p>You are enabling Two-Factor Authentication (2FA) for your account.</p>
                    <p>Your test verification code is:</p>
                    <div class="code">{otp_code}</div>
                    <p>Enter this code to complete 2FA setup.</p>
                    <p>This code will expire in <strong>10 minutes</strong>.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Enable 2FA - Test Verification
        
        Hello {user.username},
        
        You are enabling Two-Factor Authentication (2FA) for your account.
        
        Your test verification code is: {otp_code}
        
        Enter this code to complete 2FA setup.
        This code will expire in 10 minutes.
        """
        
        email = EmailMultiAlternatives(
            subject,
            text_content,
            settings.DEFAULT_FROM_EMAIL,
            [user.email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        
        logger.info(f"2FA enable test OTP sent to {user.email}")
        return {'status': 'success', 'user_id': user_id}
        
    except Exception as e:
        logger.error(f"Failed to send 2FA enable test OTP: {str(e)}")
        raise self.retry(exc=e, countdown=60)


# ============= CLEANUP TASKS (ইতিমধ্যে থাকলে রাখুন, না থাকলে যোগ করুন) =============

@shared_task
def cleanup_expired_verifications():
    """
    Clean up expired email verifications
    """
    from django.utils import timezone
    expired = EmailVerification.objects.filter(
        expired_at__lte=timezone.now(),
        status__in=['pending', 'failed']
    )
    count = expired.count()
    expired.update(status='expired')
    logger.info(f"Cleaned up {count} expired verifications")
    return {'cleaned_up': count}



#------------------------Order ---------------------------------------
@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_order_confirmation_email(self, user_email, order_number):
    try:
        subject = f'Order #{order_number} Confirmation'
        message = f'Thank you for your order! Order #{order_number} has been confirmed.'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user_email])
        logger.info(f"Order confirmation email sent to {user_email}")
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        raise self.retry(exc=e, countdown=60)

@shared_task
def cleanup_expired_carts():
    from django.utils import timezone
    from datetime import timedelta
    from .models import Cart
    cutoff = timezone.now() - timedelta(days=7)
    deleted, _ = Cart.objects.filter(updated_at__lt=cutoff).delete()
    logger.info(f"Cleaned up {deleted} expired carts")
    return {'deleted': deleted}



#-----------------------------------------------------------------------------------------------
# apps/content/tasks.py

import logging
import time
from decimal import Decimal
from datetime import timedelta
from typing import Dict, Any, List
from celery import shared_task, group
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, F, Count, Sum, Avg
from django.utils import timezone
from django.conf import settings

from Ai_Model.models import ContentGenerationTasks, BatchJob
from GenWrite_Ai.OpenAi_Client import OpenAIClient




# ============================================
# 1. Main Content Generation Task
# ============================================

@shared_task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    time_limit=120,
    soft_time_limit=90,
    acks_late=True,
    name='apps.content.tasks.generate_content_task'
)
def generate_content_task(self, task_id: str) -> Dict[str, Any]:
    """
    Generate content using OpenAI API
    
    Args:
        task_id: ContentGenerationTask ID
    
    Returns:
        Dict with generation results
    """
    start_time = time.time()
    
    try:
        # Get task from database with related objects
        task = ContentGenerationTasks.objects.select_related(
            'user', 'content_type', 'user__profile'
        ).get(id=task_id)
        
        logger.info(f"Starting content generation for task {task_id}")
        
        # Update status to processing
        task.status = 'processing'
        task.started_at = timezone.now()
        task.save(update_fields=['status', 'started_at'])
        
        # Check cache first
        cache_key = generate_cache_key(task)
        cached_content = cache.get(cache_key)
        
        if cached_content:
            logger.info(f"Cache hit for task {task_id}")
            generated_content = cached_content
            from_cache = True
            tokens_used = 0
            cost = Decimal('0')
        else:
            # Initialize OpenAI client
            client = OpenAIClient()
            
            # Generate content based on content type
            result = client.generate_content(
                prompt=task.prompt,
                content_type=task.content_type.name,
                parameters=task.parameters or {}
            )
            
            generated_content = result['content']
            tokens_used = result.get('tokens_used', 0)
            from_cache = False
            
            # Calculate cost
            cost = Decimal(str(tokens_used)) * task.content_type.price_per_token
            
            # Cache for 24 hours if content is not personalized
            if not is_personalized(task.prompt):
                cache.set(cache_key, generated_content, timeout=86400)
                logger.info(f"Cached content for task {task_id}")
        
        # Calculate metrics
        processing_time = time.time() - start_time
        
        # Update task with results
        with transaction.atomic():
            task.generated_content = generated_content
            task.status = 'completed'
            task.processing_time = processing_time
            task.tokens_used = tokens_used if not from_cache else 0
            task.cost = cost
            task.completed_at = timezone.now()
            task.save(update_fields=[
                'generated_content', 'status', 'processing_time',
                'tokens_used', 'cost', 'completed_at'
            ])
        
        logger.info(
            f"Task {task_id} completed in {processing_time:.2f}s, "
            f"tokens: {tokens_used}, from_cache: {from_cache}"
        )
        
        return {
            'task_id': task_id,
            'status': 'completed',
            'processing_time': processing_time,
            'tokens_used': tokens_used,
            'cost': str(cost),
            'from_cache': from_cache
        }
        
    except ContentGenerationTasks.DoesNotExist:
        logger.error(f"Task {task_id} not found")
        return {
            'task_id': task_id,
            'status': 'failed',
            'error': 'Task not found'
        }
        
    except Exception as e:
        logger.error(f"Task {task_id} failed: {str(e)}", exc_info=True)
        
        # Update task as failed
        try:
            task = ContentGenerationTasks.objects.get(id=task_id)
            task.status = 'failed'
            task.error_message = str(e)
            task.error_code = getattr(e, 'code', 'UNKNOWN_ERROR')
            task.save(update_fields=['status', 'error_message', 'error_code'])
        except ContentGenerationTasks.DoesNotExist:
            pass
        
        # Retry if within limits
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying task {task_id}, attempt {self.request.retries + 1}")
            raise self.retry(exc=e)
        
        raise


# ============================================
# 2. Bulk Content Generation Tasks
# ============================================

@shared_task(
    bind=True,
    name='apps.content.tasks.bulk_generate_content',
    max_retries=3
)
def bulk_generate_content(self, task_ids: List[str]) -> Dict[str, Any]:
    """
    Generate multiple contents in parallel
    
    Args:
        task_ids: List of ContentGenerationTask IDs
    
    Returns:
        Dict with group result
    """
    logger.info(f"Starting bulk generation for {len(task_ids)} tasks")
    
    # Create group of tasks
    job = group(generate_content_task.s(task_id) for task_id in task_ids)
    
    # Execute asynchronously
    result = job.apply_async()
    
    logger.info(f"Bulk generation started with group ID: {result.id}")
    
    return {
        'group_id': result.id,
        'total_tasks': len(task_ids),
        'status': 'started'
    }


@shared_task(
    bind=True,
    name='apps.content.tasks.process_batch_job',
    max_retries=2
)
def process_batch_job(self, batch_job_id: str) -> Dict[str, Any]:
    """
    Process a batch job
    
    Args:
        batch_job_id: BatchJob ID
    
    Returns:
        Dict with batch processing status
    """
    try:
        batch_job = BatchJob.objects.get(id=batch_job_id)
        logger.info(f"Processing batch job {batch_job_id}")
        
        # Update status to processing
        batch_job.status = 'processing'
        batch_job.save(update_fields=['status'])
        
        # Get all task IDs
        task_ids = list(batch_job.tasks.values_list('id', flat=True))
        
        # Start bulk generation
        result = bulk_generate_content.delay(task_ids)
        
        # Save group ID for tracking
        batch_job.celery_group_id = result.id
        batch_job.save(update_fields=['celery_group_id'])
        
        logger.info(f"Batch job {batch_job_id} started with group ID: {result.id}")
        
        return {
            'batch_id': str(batch_job.id),
            'group_id': result.id,
            'total_tasks': len(task_ids),
            'status': 'processing'
        }
        
    except BatchJob.DoesNotExist:
        logger.error(f"Batch job {batch_job_id} not found")
        return {
            'batch_id': batch_job_id,
            'status': 'failed',
            'error': 'Batch job not found'
        }
        
    except Exception as e:
        logger.error(f"Batch job {batch_job_id} failed: {str(e)}", exc_info=True)
        
        try:
            batch_job = BatchJob.objects.get(id=batch_job_id)
            batch_job.status = 'failed'
            batch_job.save(update_fields=['status'])
        except BatchJob.DoesNotExist:
            pass
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        
        raise


# ============================================
# 3. Cleanup & Maintenance Tasks
# ============================================

@shared_task(name='apps.content.tasks.cleanup_old_tasks')
def cleanup_old_tasks(days: int = 30) -> Dict[str, int]:
    """
    Cleanup old completed tasks
    
    Args:
        days: Delete tasks older than this many days
    
    Returns:
        Dict with count of deleted tasks
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    # Delete old completed tasks
    old_tasks = ContentGenerationTasks.objects.filter(
        status='completed',
        completed_at__lt=cutoff_date
    )
    
    count = old_tasks.count()
    
    # Delete in batches to avoid memory issues
    batch_size = 100
    deleted_count = 0
    
    while old_tasks.exists():
        ids = list(old_tasks[:batch_size].values_list('id', flat=True))
        ContentGenerationTasks.objects.filter(id__in=ids).delete()
        deleted_count += len(ids)
        logger.info(f"Deleted {deleted_count} old tasks so far...")
    
    logger.info(f"Deleted {deleted_count} old tasks older than {days} days")
    
    return {'deleted_count': deleted_count}


@shared_task(name='apps.content.tasks.cleanup_failed_tasks')
def cleanup_failed_tasks(days: int = 7) -> Dict[str, int]:
    """
    Cleanup old failed tasks
    
    Args:
        days: Delete failed tasks older than this many days
    
    Returns:
        Dict with count of deleted tasks
    """
    cutoff_date = timezone.now() - timezone.timedelta(days=days)
    
    failed_tasks = ContentGenerationTasks.objects.filter(
        status='failed',
        created_at__lt=cutoff_date
    )
    
    count = failed_tasks.count()
    failed_tasks.delete()
    
    logger.info(f"Deleted {count} old failed tasks")
    
    return {'deleted_count': count}


@shared_task(name='apps.content.tasks.cleanup_expired_cache')
def cleanup_expired_cache() -> Dict[str, int]:
    """
    Clean up expired cache entries
    """
    # Redis cache cleanup
    try:
        from django.core.cache import cache
        # Note: Redis cache doesn't need manual cleanup usually
        # But we can call cache.clear() if needed
        logger.info("Cache cleanup completed")
    except Exception as e:
        logger.error(f"Cache cleanup failed: {str(e)}")
    
    return {'status': 'completed'}


# ============================================
# 4. Retry Failed Tasks
# ============================================

@shared_task(name='apps.content.tasks.retry_failed_tasks')
def retry_failed_tasks() -> Dict[str, int]:
    """
    Automatically retry failed tasks that haven't exceeded max retries
    """
    failed_tasks = ContentGenerationTasks.objects.filter(
        status='failed',
        retry_count__lt=F('max_retries')
    )
    
    retried_count = 0
    
    for task in failed_tasks:
        # Update retry count
        task.retry_count += 1
        task.status = 'pending'
        task.error_message = None
        task.error_code = None
        task.save(update_fields=['retry_count', 'status', 'error_message', 'error_code'])
        
        # Retry the task
        generate_content_task.delay(str(task.id))
        retried_count += 1
        
        logger.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries})")
    
    logger.info(f"Retried {retried_count} failed tasks")
    
    return {'retried_count': retried_count}


# ============================================
# 5. Task Status Monitoring
# ============================================

@shared_task(name='apps.content.tasks.check_stuck_tasks')
def check_stuck_tasks(timeout_minutes: int = 30) -> Dict[str, int]:
    """
    Check for tasks that have been processing for too long
    
    Args:
        timeout_minutes: Time in minutes after which a processing task is considered stuck
    
    Returns:
        Dict with count of recovered tasks
    """
    timeout_threshold = timezone.now() - timezone.timedelta(minutes=timeout_minutes)
    
    stuck_tasks = ContentGenerationTasks.objects.filter(
        status='processing',
        started_at__lt=timeout_threshold
    )
    
    recovered_count = 0
    
    for task in stuck_tasks:
        task.status = 'pending'
        task.retry_count += 1
        task.save(update_fields=['status', 'retry_count'])
        
        # Retry the task
        generate_content_task.delay(str(task.id))
        recovered_count += 1
        
        logger.warning(f"Recovered stuck task {task.id} (processing for too long)")
    
    logger.info(f"Recovered {recovered_count} stuck tasks")
    
    return {'recovered_count': recovered_count}


# ============================================
# 6. Analytics Tasks
# ============================================

@shared_task(name='apps.content.tasks.update_daily_stats')
def update_daily_stats() -> Dict[str, Any]:
    """
    Update daily statistics for content generation
    """
    today = timezone.now().date()
    yesterday = today - timezone.timedelta(days=1)
    
    # Get yesterday's stats
    stats = ContentGenerationTasks.objects.filter(
        created_at__date=yesterday
    ).aggregate(
        total_tasks=Count('id'),
        completed_tasks=Count('id', filter=Q(status='completed')),
        failed_tasks=Count('id', filter=Q(status='failed')),
        total_tokens=Sum('tokens_used'),
        total_cost=Sum('cost'),
        avg_processing_time=Avg('processing_time')
    )
    
    logger.info(f"Daily stats for {yesterday}: {stats}")
    
    # Store in cache for quick access
    cache_key = f"daily_stats_{yesterday}"
    cache.set(cache_key, stats, timeout=86400 * 7)  # Keep for 7 days
    
    return {
        'date': str(yesterday),
        'stats': stats
    }


# ============================================
# 7. Helper Functions
# ============================================

def generate_cache_key(task: ContentGenerationTasks) -> str:
    """
    Generate cache key for task
    
    Args:
        task: ContentGenerationTask instance
    
    Returns:
        Cache key string
    """
    # Remove user-specific parts from prompt for caching
    prompt_hash = hash(task.prompt.strip().lower())
    return f"content_cache_{task.content_type.id}_{prompt_hash}"


def is_personalized(prompt: str) -> bool:
    """
    Check if prompt contains personalized information
    
    Args:
        prompt: User prompt
    
    Returns:
        True if content is personalized (should not be cached)
    """
    personalized_keywords = [
        'my name', 'my company', 'my business', 'my website',
        'my brand', 'for me', 'personalized', 'customized'
    ]
    
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in personalized_keywords)


# ============================================
# 8. Celery Chain Tasks (Complex Workflows)
# ============================================

@shared_task(name='apps.content.tasks.generate_and_save')
def generate_and_save(prompt: str, content_type_id: int, user_id: int) -> Dict[str, Any]:
    """
    Generate content and save to database in a chain
    
    Args:
        prompt: User prompt
        content_type_id: Content type ID
        user_id: User ID
    
    Returns:
        Dict with task result
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = User.objects.get(id=user_id)
    
    # Create task record
    task = ContentGenerationTasks.objects.create(
        user=user,
        content_type_id=content_type_id,
        prompt=prompt,
        status='pending'
    )
    
    # Start generation
    result = generate_content_task.delay(str(task.id))
    
    return {
        'task_id': str(task.id),
        'celery_task_id': result.id,
        'status': 'started'
    }


@shared_task(name='apps.content.tasks.batch_chain')
def batch_chain(tasks_data: List[Dict]) -> Dict[str, Any]:
    """
    Create a chain of tasks for sequential processing
    
    Args:
        tasks_data: List of task data dicts
    
    Returns:
        Dict with chain result
    """
    from celery import chain
    
    # Create chain of tasks
    task_chain = chain(
        generate_and_signature(task_data) for task_data in tasks_data
    )
    
    result = task_chain.apply_async()
    
    return {
        'chain_id': result.id,
        'total_tasks': len(tasks_data),
        'status': 'started'
    }


def generate_and_signature(task_data: Dict) -> Any:
    """
    Generate Celery signature for task
    
    Args:
        task_data: Task data dictionary
    
    Returns:
        Celery signature
    """
    return generate_and_save.s(
        prompt=task_data['prompt'],
        content_type_id=task_data['content_type_id'],
        user_id=task_data['user_id']
    )