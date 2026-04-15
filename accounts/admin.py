from django.contrib import admin
from django.contrib.admin import display
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from .forms import CaptchaAdminAuthenticationForm, StudentCertificateForm
from .models import *

admin.site.login_form = CaptchaAdminAuthenticationForm

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
                )
            },
        ),
        (
            _("Status"),
            {"fields": ("user_type", "is_active")},
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


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "owner",
        "industry",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = (
        "is_verified",
        "is_active",
        "industry",
        "created_at",
    )
    search_fields = (
        "name",
        "owner__username",
        "owner__email",
        "industry",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_per_page = 20

    fieldsets = (
        (
            _("Company Identification"),
            {"fields": ("name", "company_type", "company_size")},
        ),
        (
            _("Description"),
            {"fields": ("description", "industry", "tags")},
        ),
        (
            _("Contact Information"),
            {"fields": ("email", "phone", "website")},
        ),
        (
            _("Status"),
            {"fields": ("is_verified", "is_active")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(CompanyDocument)
class CompanyDocumentAdmin(admin.ModelAdmin):
    """Admin interface for CompanyDocument model"""

    list_display = (
        "title",
        "company",
        "document_type",
        "is_verified",
        "verified_by",
        "verified_at",
        "created_at",
    )
    list_filter = (
        "document_type",
        "is_verified",
        "verified_by",
        "created_at",
    )
    search_fields = (
        "title",
        "company__name",
        "company__legal_name",
    )
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("Document Information"),
            {"fields": ("company", "document_type", "title", "file")},
        ),
        (
            _("Verification"),
            {"fields": ("is_verified", "verified_by", "verified_at")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )

    def save_model(self, request, obj, form, change):
        """Сохранить модель и установить verified_by если документ верифицирован"""
        if obj.is_verified and not obj.verified_by:
            obj.verified_by = request.user
            obj.verified_at = timezone.now()
        elif not obj.is_verified:
            obj.verified_by = None
            obj.verified_at = None
        super().save_model(request, obj, form, change)


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """Admin interface for EmployerProfile with personal information"""

    list_display = (
        "user",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__email",
        "user__first_name",
        "user__last_name",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
    )
    list_per_page = 20

    fieldsets = (
        (
            _("User Information"),
            {"fields": ("user",)},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    """Admin interface for StudentProfile with educational information"""

    list_display = (
        "user",
        "faculty",
        "specialty",
        "education_level",
        "graduation_year",
    )
    list_filter = ("education_level", "faculty", "graduation_year")
    search_fields = ("user__username", "user__email", "faculty", "specialty", "student_id")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("Student Information"),
            {"fields": ("user", "student_id", "faculty", "specialty")},
        ),
        (_("Education"), {"fields": ("education_level", "graduation_year")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(StudentCertificate)
class StudentCertificateAdmin(admin.ModelAdmin):
    form = StudentCertificateForm
    list_display = (
        "title",
        "student_user",
        "issuer",
        "file_kind",
        "is_active",
        "issue_date",
        "uploaded_at",
        "file_link",
    )
    list_filter = ("is_active", "uploaded_at", "issue_date")
    search_fields = (
        "title",
        "issuer",
        "description",
        "student__user__username",
        "student__user__email",
        "student__user__first_name",
        "student__user__last_name",
    )
    ordering = ("-uploaded_at",)
    readonly_fields = (
        "uploaded_at",
        "updated_at",
        "filename",
        "extension",
        "file_link",
    )
    list_per_page = 20
    autocomplete_fields = ("student",)

    fieldsets = (
        (
            _("Certificate Information"),
            {
                "fields": (
                    "student",
                    "title",
                    "file",
                    "filename",
                    "extension",
                    "file_link",
                    "description",
                    "issuer",
                    "issue_date",
                    "is_active",
                )
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("uploaded_at", "updated_at")},
        ),
    )

    @display(description=_("Student"), ordering="student__user__username")
    def student_user(self, obj):
        return obj.student.user.get_full_name() or obj.student.user.username

    @display(description=_("File Type"))
    def file_kind(self, obj):
        if obj.is_pdf:
            return _("PDF")
        if obj.is_image:
            return _("Image")
        return (obj.extension or "-").upper()

    @display(description=_("File"))
    def file_link(self, obj):
        if not obj.pk or not obj.file:
            return "-"
        return format_html(
            '<a href="{}" target="_blank" rel="noopener">{}</a>',
            obj.get_file_url(),
            _("Open file"),
        )


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    """Admin interface for AdminProfile model"""

    list_display = ("user", *AdminProfile.PERMISSION_FIELDS, "created_at")
    list_filter = AdminProfile.PERMISSION_FIELDS
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("User Information"),
            {"fields": ("user",)},
        ),
        (
            _("Admin Permissions"),
            {
                "fields": AdminProfile.PERMISSION_FIELDS
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(HemisAuth)
class HemisAuthAdmin(admin.ModelAdmin):
    """Admin interface for HemisAuth model"""

    list_display = ("user", "hemis_user_id", "last_sync", "created_at")
    list_filter = ("last_sync", "created_at")
    search_fields = ("user__username", "user__email", "hemis_user_id")
    readonly_fields = ("created_at", "last_sync")
    list_per_page = 20

    fieldsets = (
        (
            _("User Information"),
            {"fields": ("user", "hemis_user_id")},
        ),
        (
            _("Authentication Tokens"),
            {"fields": ("access_token", "refresh_token", "token_expires")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "last_sync")},
        ),
    )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    """Admin interface for UserActivity model"""

    list_display = (
        "user",
        "activity_type",
        "related_company",
        "ip_address",
        "created_at",
    )
    list_filter = ("activity_type", "created_at", "related_company")
    search_fields = ("user__username", "description", "ip_address")
    readonly_fields = ("created_at",)
    list_per_page = 30
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Activity Information"),
            {"fields": ("user", "activity_type", "description", "related_company")},
        ),
        (
            _("Technical Information"),
            {"fields": ("ip_address", "user_agent")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at",)},
        ),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin interface for Notification model"""

    list_display = (
        "user",
        "notification_type",
        "title",
        "is_read",
        "related_company",
        "created_at",
    )
    list_filter = ("notification_type", "is_read", "related_company", "created_at")
    search_fields = ("user__username", "title", "message")
    readonly_fields = ("created_at",)
    list_per_page = 30
    date_hierarchy = "created_at"

    fieldsets = (
        (
            _("Notification Information"),
            {"fields": ("user", "notification_type", "title", "message")},
        ),
        (
            _("Status and Links"),
            {"fields": ("is_read", "related_url", "related_company")},
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at",)},
        ),
    )




@admin.register(OAuthToken)
class OAuthTokenAdmin(admin.ModelAdmin):
    """Admin interface for OAuthToken model - manage OAuth tokens for users"""

    list_display = (
        "user",
        "token_type",
        "is_valid",
        "expires_at",
        "created_at",
        "updated_at",
    )
    list_filter = ("token_type", "created_at", "updated_at")
    search_fields = ("user__username", "user__email")
    readonly_fields = ("created_at", "updated_at", "access_token", "refresh_token")

    fieldsets = (
        (
            _("User Information"),
            {"fields": ("user",)},
        ),
        (
            _("Token Information"),
            {
                "fields": (
                    "access_token",
                    "refresh_token",
                    "token_type",
                    "expires_in",
                    "expires_at",
                    "scope",
                )
            },
        ),
        (
            _("Timestamps"),
            {"fields": ("created_at", "updated_at")},
        ),
    )

    def is_valid(self, obj):
        """Display if token is currently valid"""
        if obj.is_expired():
            return format_html(
                '<span style="color: red;">❌ Expired</span>'
            )
        return format_html(
            '<span style="color: green;">✓ Valid</span>'
        )
    is_valid.short_description = _("Token Status")
