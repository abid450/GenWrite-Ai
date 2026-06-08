from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(User)

@admin.register(EmailVerification)
class EmailAdmin(admin.ModelAdmin):
    list_display = ['user', 'verification_code', 'status', 'attempts', 'created_at',
                    'updated_at', 'expired_at', 'verified_at', 'request_ip', 'user_agent']
    
    search_fields = ['user__username', 'user__email',  'verification_code', 'user_agent']

admin.site.register(VerificationLog)
admin.site.register(PhoneVerification)
