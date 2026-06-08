import requests
from user_agents import parse
from django.core.cache import cache
from .models import SuspiciousActivity, SecurityAlert, LoginLog, LoginSession
from datetime import datetime, timedelta
import secrets



def get_client_ip(request):
    """Get client IP address from request"""

    x_forwarded_for =request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')



def get_user_agent(request):
    """Get user agent from request"""
    
    return request.META.get('HTTP_USER_AGENT')


def parse_device_info(request):
     """
    Parse device information from request
    Returns: dict with device, browser, OS info
    """
     
     user_agent_string = get_user_agent(request)
     user_agent = parse(user_agent_string)

    # Determine device type
     if user_agent.is_mobile:
       device_type = 'Mobile'
    
     elif user_agent.is_tablet:
       device_type = 'Tablet'
    
     elif user_agent.is_pc:
       device_type = 'Desktop'

     else:
       device_type = 'Unknown'

    # Get device name]
     device_name = user_agent.device.family or 'Unknown'

     # Browser info
     browser = user_agent.browser.family or 'Unknown'
     browser_version = user_agent.browser.version_string or 'Unknown'
     # OS info
     os = user_agent.os.family or 'Unknown'
     os_version = user_agent.os.version_string or 'Unknown'
    
     return {
        'device_type': device_type,
        'device_name': device_name,
        'browser': browser,
        'browser_version': browser_version,
        'os': os,
        'os_version': os_version,
        'user_agent_string': user_agent_string
    }



def get_location_from_ip(ip_address):
    """
    Get location from IP address using free API
    """
    if not ip_address or ip_address.startswith('127.') or ip_address.startswith('192.168'):
        return 'Local Network'
    
    # Check cache first
    cache_key = f"ip_location_{ip_address}"
    cached_location = cache.get(cache_key)
    if cached_location:
        return cached_location
    
    try:
        # Using free ip-api.com
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
                # Cache for 1 hour
                cache.set(cache_key, location, 3600)
                return location
    except Exception:
        pass
    
    return 'Unknown'


def get_isp_from_ip(ip_address):
    """
    Get ISP from IP address
    """
    if not ip_address or ip_address.startswith('127.') or ip_address.startswith('192.168'):
        return 'Local Network'
    
    cache_key = f"ip_isp_{ip_address}"
    cached_isp = cache.get(cache_key)
    if cached_isp:
        return cached_isp
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                isp = data.get('isp', 'Unknown')
                cache.set(cache_key, isp, 3600)
                return isp
    except Exception:
        pass
    
    return 'Unknown'


def generate_session_token():
    """Generate unique session token"""
    import secrets
    return secrets.token_urlsafe(32)


def rate_limit_check(key, limit=5, window=300):
    """
    Check rate limit for OTP verification
    """
    from django.core.cache import cache
    from datetime import timedelta
    from django.utils import timezone
    
    cache_key = f"rate_limit:{key}"
    current = cache.get(cache_key)
    
    if current is None:
        cache.set(cache_key, 1, window)
        return True, limit - 1
    
    if current >= limit:
        return False, 0
    
    cache.incr(cache_key)
    return True, limit - current - 1

         
import hashlib
from django.utils import timezone

#  Fingerprint --------------------------------------------------
def get_device_fingerprint(request):
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    ip_address = get_client_ip(request)

    fingerprint_string = f"{user_agent}|{accept_language}|{ip_address}"
    return hashlib.sha256(fingerprint_string.encode()).hexdigest()



# Location ip --------------------------------------------------------------

def get_location_from_ip(ip_address):
    if not ip_address or ip_address.startswith('127.') or ip_address.startswith('192.168'):
        return 'Local Network'
    
    cache_key = f"ip_location_{ip_address}"
    cached = cache.get(cache_key)
    if cached:
        return cached
    
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}', timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
                cache.set(cache_key, location, 3600)
                return location
    except:
        pass
    return 'Unknown'


def generate_session_token():
    return secrets.token_urlsafe(32)



# ========== রুল ১: ব্রুট ফোর্স (বারবার ভুল পাসওয়ার্ড) ==========
def check_brute_force(user, request):
    ip = get_client_ip(request)
    cache_key = f"brute_force_{user.id if user else 'anon'}_{ip}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, 300)

    severity = 1
    if attempts >= 10:
        severity = 4
        SecurityAlert.objects.create(
            title="Critical: Brute Force Attack",
            alert_type=SecurityAlert.AlertType.BRUTE_FORCE,
            priority=SecurityAlert.Priority.URGENT,
            user=user,
            message=f"{attempts} failed attempts from {ip}",
            ip_address=ip,
            location=get_location_from_ip(ip)
        )
    elif attempts >= 5:
        severity = 3
    elif attempts >= 3:
        severity = 2

    SuspiciousActivity.objects.create(
        user=user,
        activity_type='brute_force',
        severity=severity,
        ip_address=ip,
        location=get_location_from_ip(ip),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        device_info=parse_device_info(request),
        details=f"{attempts} failed login attempts"
    )
    return attempts >= 3


# ========== রুল ২: অস্বাভাবিক লোকেশন ==========
def check_unusual_location(user, request, current_location):
    if not user:
        return False
    
    seven_days_ago = timezone.now() - timedelta(days=7)
    prev_locations = LoginLog.objects.filter(
        user=user, status='success', created_at__gte=seven_days_ago
    ).exclude(location__isnull=True).values_list('location', flat=True).distinct()
    
    if prev_locations and current_location and current_location not in prev_locations:
        SuspiciousActivity.objects.create(
            user=user,
            activity_type='unusual_location',
            severity=2,
            ip_address=get_client_ip(request),
            location=current_location,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_info=parse_device_info(request),
            details=f'New location: {current_location}'
        )
        return True
    return False


# ========== রুল ৩: অস্বাভাবিক ডিভাইস ==========
def check_unusual_device(user, request, device_info):
    if not user:
        return False
    
    thirty_days_ago = timezone.now() - timedelta(days=30)
    prev_devices = LoginSession.objects.filter(
        user=user, login_time__gte=thirty_days_ago
    ).values_list('device_name', 'browser', 'os').distinct()
    
    current = f"{device_info.get('device_name')}_{device_info.get('browser')}_{device_info.get('os')}"
    
    for d in prev_devices:
        if current == f"{d[0]}_{d[1]}_{d[2]}":
            return False
    
    SuspiciousActivity.objects.create(
        user=user,
        activity_type='unusual_device',
        severity=2,
        ip_address=get_client_ip(request),
        location=get_location_from_ip(get_client_ip(request)),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        device_info=device_info,
        details=f'New device: {device_info.get("device_name")}'
    )
    return True


# ========== রুল ৪: অস্বাভাবিক সময় ==========
def check_unusual_time(user, request):
    if not user:
        return False
    
    hour = timezone.now().hour
    if 0 <= hour < 5:
        SuspiciousActivity.objects.create(
            user=user,
            activity_type='unusual_time',
            severity=1,
            ip_address=get_client_ip(request),
            location=get_location_from_ip(get_client_ip(request)),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_info=parse_device_info(request),
            details=f'Login at {hour}:00 (unusual hour)'
        )
        return True
    return False


# ========== রুল ৫: OTP ব্যর্থতা ==========
def check_otp_failures(user, request, otp_attempts):
    if not user or otp_attempts < 3:
        return False
    
    SuspiciousActivity.objects.create(
        user=user,
        activity_type='verification_failed',
        severity=2,
        ip_address=get_client_ip(request),
        location=get_location_from_ip(get_client_ip(request)),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        device_info=parse_device_info(request),
        details=f'{otp_attempts} failed OTP attempts'
    )
    return True


# ========== রুল ৬: দ্রুত লগইন চেষ্টা ==========
def check_rapid_login_attempts(request):
    ip = get_client_ip(request)
    cache_key = f"rapid_{ip}"
    attempts = cache.get(cache_key, 0) + 1
    cache.set(cache_key, attempts, 60)
    
    if attempts >= 5:
        SuspiciousActivity.objects.create(
            user=None,
            activity_type='brute_force',
            severity=3,
            ip_address=ip,
            location=get_location_from_ip(ip),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            device_info=parse_device_info(request),
            details=f'{attempts} attempts in 1 minute'
        )
        return True
    return False


# ========== মাস্টার ফাংশন (এক কলেই সব হবে) ==========
def check_all_security_rules(user, request, is_successful=True, otp_attempts=0):
    """
    এই একটি ফাংশন কল করলেই সব রুলস চেক হবে
    """
    device_info = parse_device_info(request)
    location = get_location_from_ip(get_client_ip(request))
    
    # রুল ৬: দ্রুত লগইন
    check_rapid_login_attempts(request)
    
    if user:
        # রুল ৪: অস্বাভাবিক সময়
        check_unusual_time(user, request)
        # রুল ২: অস্বাভাবিক লোকেশন
        check_unusual_location(user, request, location)
        # রুল ৩: অস্বাভাবিক ডিভাইস
        check_unusual_device(user, request, device_info)
        # রুল ৫: OTP ব্যর্থতা
        check_otp_failures(user, request, otp_attempts)
    
    # রুল ১: ব্রুট ফোর্স (শুধু ব্যর্থ লগইনে)
    if not is_successful:
        check_brute_force(user, request)


#_________________________________________________________

def is_ip_blocked(ip_address):
    """
    Check if IP address is blocked
    """
    cache_key = f"blocked_ip_{ip_address}"
    return cache.get(cache_key, False)


def block_ip(ip_address, duration_minutes=60, reason=None):
    """
    Block an IP address temporarily
    """
    cache_key = f"blocked_ip_{ip_address}"
    cache.set(cache_key, {
        'reason': reason,
        'blocked_at': str(timezone.now())
    }, duration_minutes * 60)
    
    from .models import SuspiciousActivity
    SuspiciousActivity.objects.create(
        user=None,
        activity_type=SuspiciousActivity.ActivityType.ACCOUNT_FROZEN,
        severity=SuspiciousActivity.Severity.HIGH,
        ip_address=ip_address,
        details=f"IP blocked: {reason}"
    )
    
    return True


def calculate_login_metrics(date=None):
    """
    Calculate daily login security metrics
    """
    from .models import LoginHistory, LoginSecurityMetrics, SuspiciousActivity
    
    if date is None:
        date = timezone.now().date()
    
    date_start = timezone.make_aware(datetime.combine(date, datetime.min.time()))
    date_end = timezone.make_aware(datetime.combine(date, datetime.max.time()))
    
    # Get login history for the date
    logins = LoginHistory.objects.filter(login_time__range=(date_start, date_end))
    
    # Calculate metrics
    total_logins = logins.count()
    successful_logins = logins.filter(is_successful=True).count()
    failed_logins = total_logins - successful_logins
    
    # Unique users
    unique_users = logins.values('user').distinct().count()
    new_users = logins.filter(user__date_joined__range=(date_start, date_end)).values('user').distinct().count()
    
    # Suspicious activities
    suspicious_count = SuspiciousActivity.objects.filter(
        created_at__range=(date_start, date_end)
    ).count()
    
    brute_force_count = SuspiciousActivity.objects.filter(
        created_at__range=(date_start, date_end),
        activity_type=SuspiciousActivity.ActivityType.BRUTE_FORCE
    ).count()
    
    # Device stats
    mobile_logins = logins.filter(device_type='Mobile').count()
    desktop_logins = logins.filter(device_type='Desktop').count()
    tablet_logins = logins.filter(device_type='Tablet').count()
    
    # Location stats
    unique_locations = logins.exclude(location__isnull=True).values('location').distinct().count()
    
    # Top IPs
    from django.db.models import Count
    top_ips = list(logins.values('ip_address').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Top devices
    top_devices = list(logins.values('device_name').annotate(
        count=Count('id')
    ).order_by('-count')[:10])
    
    # Hourly distribution
    hourly_dist = {}
    for hour in range(24):
        hour_start = date_start + timedelta(hours=hour)
        hour_end = hour_start + timedelta(hours=1)
        count = logins.filter(login_time__range=(hour_start, hour_end)).count()
        hourly_dist[str(hour)] = count
    
    # Create or update metrics
    metrics, created = LoginSecurityMetrics.objects.update_or_create(
        date=date,
        defaults={
            'total_logins': total_logins,
            'successful_logins': successful_logins,
            'failed_logins': failed_logins,
            'unique_users_logged_in': unique_users,
            'new_users_logged_in': new_users,
            'suspicious_activities': suspicious_count,
            'brute_force_attempts': brute_force_count,
            'mobile_logins': mobile_logins,
            'desktop_logins': desktop_logins,
            'tablet_logins': tablet_logins,
            'unique_locations': unique_locations,
            'top_ips': top_ips,
            'top_devices': top_devices,
            'hourly_distribution': hourly_dist,
        }
    )
    
    return metrics