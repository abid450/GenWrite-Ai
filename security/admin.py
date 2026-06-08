from django.contrib import admin
from .models import *
# Register your models here.
admin.site.register(EmailOTP)
admin.site.register(LoginSession)
admin.site.register(LoginLog)
admin.site.register(SuspiciousActivity)
admin.site.register(SecurityAlert)
admin.site.register(LoginSecurityMetrics)