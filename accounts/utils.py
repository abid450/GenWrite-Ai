import random
import secrets
import re
import string
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache

def generate_verification_code(length=6):
    while True:
        code = ''.join([str(random.randint(0, 9)) for _ in range(length)])
        if not is_simple_code(code):
            return code

def is_simple_code(code):
    simple_patterns = [
        r'^(\d)\1+$', r'^123456$', r'^654321$', r'^112233$', r'^121212$'
    ]
    for pattern in simple_patterns:
        if re.match(pattern, code):
            return True
    return False

def generate_secure_token():
    return secrets.token_urlsafe(32)

def get_expiry_time(minutes=None):
    minutes = minutes or settings.VERIFICATION_CODE_EXPIRY_MINUTES
    return timezone.now() + timedelta(minutes=minutes)

def mask_email(email):
    if not email:
        return email
    try:
        local, domain = email.split('@')
        if len(local) <= 2:
            masked_local = local[0] + '*' * (len(local) - 1)
        else:
            masked_local = local[0] + '*' * (len(local) - 2) + local[-1]
        return f"{masked_local}@{domain}"
    except (ValueError, AttributeError):
        return email

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')

def rate_limit_check(key, limit=10, window=60):
    cache_key = f"rate_limit:{key}"
    current = cache.get(cache_key, {'count': 0, 'reset_at': timezone.now() + timedelta(seconds=window)})
    
    if timezone.now() > current['reset_at']:
        current = {'count': 0, 'reset_at': timezone.now() + timedelta(seconds=window)}
    
    remaining = limit - current['count']
    is_allowed = remaining > 0
    
    if is_allowed:
        current['count'] += 1
        cache.set(cache_key, current, window)
    
    return is_allowed, max(0, remaining), current['reset_at']