# accounts/admin.py
from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
# ЗАКОММЕНТИРУЙТЕ эту строку:
# from modeltranslation.admin import TranslationAdmin

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
    """Admin interface for CustomUser model with role-based management"""

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "user_type",
        "is_active",
        "date_joined",
    )
    list_filter = ("user_type", "is_active", "is_staff", "date_joined", "is_verified")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("date_joined", "last_login")

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
class EmployerProfileAdmin(admin.ModelAdmin):  # ИЗМЕНИТЕ здесь
    """Admin interface for EmployerProfile with company management"""

    list_display = (
        "company_name",
        "user",
        "industry",
        "company_size",
        "is_verified",
        "created_at",
    )
    list_filter = ("industry", "company_size", "is_verified", "created_at", "founded_year")
    search_fields = ("company_name", "user__username", "user__email", "headquarters")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("Company Information"),
            {"fields": ("user", "company_name", "company_logo", "company_description")},
        ),
        (
            _("Contact Information"),
            {"fields": ("company_email", "company_phone", "company_website")},
        ),
        (_("Social Media"), {"fields": ("company_linkedin", "company_telegram")},
        ),
        (
            _("Company Details"),
            {"fields": ("company_size", "industry", "founded_year", "headquarters")},
        ),
        (_("Statistics"), {"fields": ("jobs_posted", "total_views")},
        ),
        (_("Status"), {"fields": ("is_verified",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):  # ИЗМЕНИТЕ здесь
    """Admin interface for StudentProfile with educational information"""

    list_display = (
        "user",
        "faculty",
        "specialty",
        "education_level",
        "graduation_year",
        "gpa",
    )
    list_filter = ("education_level", "faculty", "graduation_year", "work_type")
    search_fields = ("user__username", "user__email", "faculty", "specialty", "student_id")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("Student Information"),
            {"fields": ("user", "student_id", "faculty", "specialty")},
        ),
        (_("Education"), {"fields": ("education_level", "graduation_year", "gpa")},
        ),
        (
            _("Career Preferences"),
            {"fields": ("desired_position", "desired_salary", "work_type")},
        ),
        (_("Statistics"), {"fields": ("resumes_created", "jobs_applied")},
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )