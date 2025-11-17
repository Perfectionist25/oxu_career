# accounts/admin.py
from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import (
    AdminProfile,
    CustomUser,
    EmployerProfile,
    HemisAuth,
    Notification,
    StudentProfile,
    UserActivity,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "date_joined",
    )
    list_filter = ("user_type", "is_active", "is_staff", "date_joined")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "first_name",
                    "last_name",
                    "email",
                    "phone_number",
                    "date_of_birth",
                    "bio",
                    "avatar",
                    "country",
                    "city",
                    "address",
                )
            },
        ),
        (_("Social media"), {"fields": ("website", "linkedin", "github", "telegram")}),
        (
            _("Preferences"),
            {"fields": ("email_notifications", "job_alerts", "newsletter")},
        ),
        (
            _("Status"),
            {"fields": ("user_type", "is_verified", "is_active_employer", "is_active")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (
            _("Permissions"),
            {
                "fields": ("is_staff", "is_superuser", "groups", "user_permissions"),
            },
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "password1", "password2", "user_type"),
            },
        ),
    )


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "user",
        "industry",
        "company_size",
        "is_verified",
        "created_at",
    )
    list_filter = ("industry", "company_size", "is_verified", "created_at")
    search_fields = ("company_name", "user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            _("Company Information"),
            {"fields": ("user", "company_name", "company_logo", "company_description")},
        ),
        (
            _("Contact Information"),
            {"fields": ("company_email", "company_phone", "company_website")},
        ),
        (_("Social Media"), {"fields": ("company_linkedin", "company_telegram")}),
        (
            _("Company Details"),
            {"fields": ("company_size", "industry", "founded_year", "headquarters")},
        ),
        (_("Statistics"), {"fields": ("jobs_posted", "total_views")}),
        (_("Status"), {"fields": ("is_verified",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "faculty",
        "specialty",
        "education_level",
        "graduation_year",
    )
    list_filter = ("education_level", "faculty", "graduation_year")
    search_fields = ("user__username", "user__email", "faculty", "specialty")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (
            _("Student Information"),
            {"fields": ("user", "student_id", "faculty", "specialty")},
        ),
        (_("Education"), {"fields": ("education_level", "graduation_year", "gpa")}),
        (
            _("Career Preferences"),
            {"fields": ("desired_position", "desired_salary", "work_type")},
        ),
        (_("Statistics"), {"fields": ("resumes_created", "jobs_applied")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "can_manage_students",
        "can_manage_employers",
        "can_manage_jobs",
    )
    list_filter = ("can_manage_students", "can_manage_employers", "can_manage_jobs")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("Admin Information"), {"fields": ("user",)}),
        (
            _("Permissions"),
            {
                "fields": (
                    "can_manage_students",
                    "can_manage_employers",
                    "can_manage_jobs",
                    "can_manage_resumes",
                    "can_view_statistics",
                )
            },
        ),
        (
            _("Statistics"),
            {"fields": ("students_managed", "employers_created", "jobs_approved")},
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(HemisAuth)
class HemisAuthAdmin(admin.ModelAdmin):
    list_display = ("user", "last_sync", "created_at", "is_token_valid")
    list_filter = ("last_sync", "created_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "last_sync", "is_token_valid_display")

    fieldsets = (
        (_("Hemis Authentication"), {"fields": ("user",)}),
        (_("Tokens"), {"fields": ("access_token", "refresh_token", "token_expires")}),
        (_("User Data"), {"fields": ("hemis_user_data",)}),
        (_("Timestamps"), {"fields": ("last_sync", "created_at")}),
        (_("Status"), {"fields": ("is_token_valid_display",)}),
    )

    @display(boolean=True, description=_("Token valid"))
    def is_token_valid(self, obj):
        return obj.is_token_valid()

    @display(boolean=True, description=_("Token valid"))
    def is_token_valid_display(self, obj):
        return obj.is_token_valid()


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "activity_type", "ip_address", "created_at")
    list_filter = ("activity_type", "created_at")
    search_fields = ("user__username", "description", "ip_address")
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            _("Activity Information"),
            {"fields": ("user", "activity_type", "description")},
        ),
        (_("Technical Details"), {"fields": ("ip_address", "user_agent")}),
        (_("Timestamps"), {"fields": ("created_at",)}),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_type", "title", "is_read", "created_at")
    list_filter = ("notification_type", "is_read", "created_at")
    search_fields = ("user__username", "title", "message")
    readonly_fields = ("created_at",)

    fieldsets = (
        (
            _("Notification Information"),
            {"fields": ("user", "notification_type", "title", "message")},
        ),
        (_("Status"), {"fields": ("is_read", "related_url")}),
        (_("Timestamps"), {"fields": ("created_at",)}),
    )
