from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Notification, UserActivity, Skill, UserSkill, EmailVerification
from django.utils.translation import gettext_lazy as _

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Админ-панель для кастомной модели пользователя"""
    
    list_display = ('username', 'email', 'get_full_name', 'user_type', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('user_type', 'is_verified', 'is_active', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal Info'), {'fields': (
            'first_name', 'last_name', 'email', 
            'date_of_birth', 'phone_number', 'avatar', 'bio'
        )}),
        (_('Location'), {'fields': ('country', 'city', 'address')}),
        (_('Professional Info'), {'fields': (
            'user_type', 'organization', 'position',
            'website', 'linkedin', 'github', 'resume'
        )}),
        (_('Settings'), {'fields': (
            'email_notifications', 'job_alerts', 'newsletter'
        )}),
        (_('Status'), {'fields': (
            'is_verified', 'verification_token', 
            'profile_views', 'resume_views', 'last_activity'
        )}),
        (_('Permissions'), {'fields': (
            'is_active', 'is_staff', 'is_superuser',
            'groups', 'user_permissions'
        )}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'user_type'),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined', 'profile_views', 'resume_views', 'last_activity')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'user__username')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'ip_address', 'created_at')
    list_filter = ('activity_type', 'created_at')
    search_fields = ('user__username', 'description', 'ip_address')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'description')
    list_filter = ('category',)
    search_fields = ('name', 'description')

@admin.register(UserSkill)
class UserSkillAdmin(admin.ModelAdmin):
    list_display = ('user', 'skill', 'proficiency', 'years_of_experience', 'is_primary')
    list_filter = ('proficiency', 'is_primary', 'skill__category')
    search_fields = ('user__username', 'skill__name')

@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'expires_at')
    list_filter = ('created_at', 'expires_at')
    search_fields = ('user__username', 'user__email', 'token')
    readonly_fields = ('created_at',)