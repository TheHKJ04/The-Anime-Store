from django.contrib import admin

# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTPLog

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'username', 'is_email_verified', 'date_joined']
    list_filter = ['is_email_verified', 'is_active', 'date_joined']
    fieldsets = UserAdmin.fieldsets + (
        ('Email Verification', {'fields': ('is_email_verified', 'otp')}),
    )

@admin.register(OTPLog)
class OTPLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'is_used']
    list_filter = ['created_at', 'is_used']