import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.password_validation import CommonPasswordValidator, NumericPasswordValidator
import hashlib
import requests
from datetime import datetime


# ============= Password Validators =============

def validate_strong_password(value):
    """
    Validate password strength:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(value) < 8:
        raise ValidationError(
            _('Password must be at least 8 characters long.'),
            code='password_too_short'
        )
    
    if not re.search(r'[A-Z]', value):
        raise ValidationError(
            _('Password must contain at least one uppercase letter (A-Z).'),
            code='password_no_upper'
        )
    
    if not re.search(r'[a-z]', value):
        raise ValidationError(
            _('Password must contain at least one lowercase letter (a-z).'),
            code='password_no_lower'
        )
    
    if not re.search(r'\d', value):
        raise ValidationError(
            _('Password must contain at least one digit (0-9).'),
            code='password_no_digit'
        )
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', value):
        raise ValidationError(
            _('Password must contain at least one special character (!@#$%^&*(),.?":{}|<>).'),
            code='password_no_special'
        )
    
    # Check for common patterns
    common_patterns = [
        r'123456', r'password', r'qwerty', r'abc123', 
        r'admin', r'welcome', r'letmein', r'12345678'
    ]
    
    for pattern in common_patterns:
        if pattern in value.lower():
            raise ValidationError(
                _(f'Password contains common pattern "{pattern}". Please choose a stronger password.'),
                code='password_common_pattern'
            )
    
    # Check for keyboard patterns
    keyboard_patterns = [
        r'qwerty', r'asdfgh', r'zxcvbn', r'1qaz2wsx', 
        r'qwertyuiop', r'asdfghjkl', r'zxcvbnm'
    ]
    
    for pattern in keyboard_patterns:
        if pattern in value.lower():
            raise ValidationError(
                _('Password contains keyboard pattern. Please choose a stronger password.'),
                code='password_keyboard_pattern'
            )
    
    # Check for repeated characters
    if re.search(r'(.)\1{2,}', value):
        raise ValidationError(
            _('Password contains repeated characters (e.g., "aaa"). Please choose a stronger password.'),
            code='password_repeated_chars'
        )
    
    # Check for sequential characters
    for i in range(len(value) - 2):
        if ord(value[i+1]) == ord(value[i]) + 1 and ord(value[i+2]) == ord(value[i]) + 2:
            raise ValidationError(
                _('Password contains sequential characters (e.g., "abc", "123"). Please choose a stronger password.'),
                code='password_sequential'
            )
        


#-----------------------  Username -----------------------------
def validate_username_format(value):
    """
    Validate username format (alphanumeric, dot, underscore, hyphen)
    """
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise ValidationError(
            _('Username can only contain letters, digits, and @/./+/-/_ characters.'),
            code='invalid_username_format'
        )
    
    if value.startswith('_') or value.startswith('-') or value.startswith('.'):
        raise ValidationError(
            _('Username cannot start with underscore, hyphen, or dot.'),
            code='username_invalid_start'
        )
    
    if value.endswith('_') or value.endswith('-') or value.endswith('.'):
        raise ValidationError(
            _('Username cannot end with underscore, hyphen, or dot.'),
            code='username_invalid_end'
        )
    
    if '__' in value or '--' in value or '..' in value:
        raise ValidationError(
            _('Username cannot contain consecutive special characters.'),
            code='username_consecutive_special'
        )


def validate_username_length(value):
    """
    Validate username length
    """
    if len(value) < 3:
        raise ValidationError(
            _('Username must be at least 3 characters long.'),
            code='username_too_short'
        )
    
    if len(value) > 30:
        raise ValidationError(
            _('Username cannot exceed 30 characters.'),
            code='username_too_long'
        )



# ============= Phone Number Validators =============

def validate_bangladesh_phone_number(value):
    """
    Validate Bangladeshi phone number format
    """
    # Remove any spaces, dashes, or plus signs
    cleaned = re.sub(r'[\s\-\(\)\+]', '', value)
    
    # Check for Bangladesh format
    patterns = [
        r'^01[3-9]\d{8}$',      # 013XXXXXXX, 014XXXXXXX, etc.
        r'^8801[3-9]\d{8}$',    # 88013XXXXXXX
    ]
    
    if not any(re.match(pattern, cleaned) for pattern in patterns):
        raise ValidationError(
            _('Enter a valid Bangladeshi phone number (e.g., 01XXXXXXXXX or 8801XXXXXXXXX).'),
            code='invalid_bd_phone'
        )


def validate_phone_number_length(value):
    """
    Validate phone number length
    """
    cleaned = re.sub(r'[\s\-\(\)\+]', '', value)
    
    if len(cleaned) < 11:
        raise ValidationError(
            _('Enter a valid phone number.'),
            code='phone_too_short'
        )
    
    if len(cleaned) > 11:
        raise ValidationError(
            _('Phone number is too long. Maximum 11 digits allowed.'),
            code='phone_too_long'
        )
    
    


# ============= Verification Code Validators =============

def validate_verification_code(value):
    """
    Validate verification code format
    """
    if not value.isdigit():
        raise ValidationError(
            _('Verification code must contain only digits.'),
            code='invalid_code_format'
        )
    
    if len(value) not in [6, 8, 10]:
        raise ValidationError(
            _('Verification code must be 6, 8, or 10 digits long.'),
            code='invalid_code_length'
        )


def validate_verification_code_not_simple(value):
    """
    Prevent simple/guessable verification codes
    """
    simple_codes = [
        '000000', '111111', '222222', '333333', '444444', '555555',
        '666666', '777777', '888888', '999999', '123456', '654321',
        '12345678', '87654321', '112233', '121212', '123123'
    ]
    
    if value in simple_codes:
        raise ValidationError(
            _('This verification code is too simple. Please generate another.'),
            code='simple_verification_code'
        )

def get_operator_from_phone(value):
    """
    Get mobile operator name from Bangladeshi phone number
    Supports: 019XXXXXXXXX, 88019XXXXXXXXX, +88019XXXXXXXXX
    """
    import re
    
    # Convert to string
    value = str(value)
    
    # Remove all non-digit characters (spaces, dashes, plus, parentheses)
    cleaned = re.sub(r'\D', '', value)
    
    # Remove country code 880 if present
    if cleaned.startswith('880'):
        cleaned = cleaned[3:]
    
    # Now we have number without country code
    # It should be 11 digits starting with 0 or 10 digits starting with 1
    
    # Get the operator prefix (first 3 digits)
    if cleaned.startswith('0') and len(cleaned) >= 3:
        # Format: 01981200657 → prefix = '019'
        prefix = cleaned[:3]
    elif len(cleaned) >= 3:
        # Format: 1981200657 → add '0' → prefix = '019'
        prefix = '0' + cleaned[:2]
    else:
        return 'Unknown'
    
    # Operator mapping
    operators = {
        '017': 'Grameenphone',
        '013': 'Grameenphone',
        '018': 'Robi',
        '016': 'Robi/Airtel',
        '019': 'Banglalink',
        '014': 'Banglalink',
        '015': 'Teletalk',
    }
    
    return operators.get(prefix, 'Unknown')


def validate_phone_operator(value, allowed_operators=None):
    """
    Validate phone number belongs to specific operator(s)
    
    Usage:
        validate_phone_operator('01712345678')  # Valid (Grameenphone)
        validate_phone_operator('01912345678', ['Grameenphone', 'Robi'])  # Valid only for GP or Robi
    """
    if allowed_operators is None:
        allowed_operators = ['Grameenphone', 'Robi', 'Banglalink', 'Teletalk', 'Airtel']
    
    # Get operator from phone number
    operator = get_operator_from_phone(value)
    
    # Check if operator is valid
    if operator == 'Unknown':
        raise ValidationError(
            _('Could not determine operator from this phone number. Please enter a valid Bangladeshi number.')
        )
    
    # Check if operator is in allowed list
    if operator not in allowed_operators:
        # Create user-friendly message
        operator_list = ', '.join(allowed_operators)
        raise ValidationError(
            _(f'Phone number must be from one of these operators: {operator_list}. Your number is from {operator}.')
        )
    
    return operator  # Return operator name for additional use