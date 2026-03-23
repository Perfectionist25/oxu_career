from django.contrib import admin
from django.contrib.admin import display
from django.utils import timezone
from django.utils.html import format_html
from django.utils.text import Truncator
from django.utils.translation import gettext_lazy as _

from .models import (
    ContactMessage,
    SystemNotification,
    UserNotificationDismissal,
)


class ContactMessageAdmin(admin.ModelAdmin):
    """Admin panel for contact messages"""

    list_display = (
        "name",
        "email",
        "short_message",
        "created_at",
        "is_processed",
        "processed_status",
    )
    list_filter = ("is_processed", "created_at")
    search_fields = ("name", "email", "message")
    readonly_fields = (
        "name",
        "email",
        "message",
        "created_at",
        "updated_at",
        "message_preview",
    )
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (_("Sender Information"), {"fields": ("name", "email", "created_at")}),
        (_("Message"), {"fields": ("message_preview", "message")}),
        (
            _("Message Processing"),
            {"fields": ("is_processed", "processed_at", "admin_notes", "updated_at")},
        ),
    )

    actions = [
        "mark_as_processed",
        "mark_as_unprocessed",
        "export_emails",
        "send_bulk_reply",
    ]

    @display(description=_("Message"))
    def short_message(self, obj):
        """Short message display"""
        if len(obj.message) > 100:
            return f"{obj.message[:100]}..."
        return obj.message

    @display(description=_("Message Preview"))
    def message_preview(self, obj):
        """Message preview with formatting"""
        html = (
            '<div style="background: #f8f9fa; padding: 15px; '
            'border-radius: 5px; border-left: 4px solid #007cba; '
            'white-space: pre-wrap; font-family: Arial, sans-serif;">{}</div>'
        )
        return format_html(html, obj.message)

    @display(description=_("Status"))
    def processed_status(self, obj):
        """Processing status with color indication"""
        if obj.is_processed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Processed</span>'
            )
        else:
            return format_html(
                '<span style="color: orange; font-weight: bold;">● Pending</span>'
            )

    @display(description=_("Mark as Processed"))
    def mark_as_processed(self, request, queryset):
        """Mark selected messages as processed"""
        updated = queryset.update(is_processed=True)
        self.message_user(request, f"{updated} messages marked as processed.")

    @display(description=_("Mark as Unprocessed"))
    def mark_as_unprocessed(self, request, queryset):
        """Mark selected messages as unprocessed"""
        updated = queryset.update(is_processed=False)
        self.message_user(request, f"{updated} messages marked as unprocessed.")

    @display(description=_("Export Email Addresses"))
    def export_emails(self, request, queryset):
        """Export email addresses of selected messages"""
        emails = list(queryset.values_list("email", flat=True).distinct())

        preview_emails = ", ".join(emails[:5])
        more = "..." if len(emails) > 5 else ""
        self.message_user(
            request,
            f"Found {len(emails)} unique email addresses: {preview_emails}{more}",
        )

    @display(description=_("Send Bulk Reply"))
    def send_bulk_reply(self, request, queryset):
        """Bulk reply sending (placeholder for demonstration)"""
        unprocessed = queryset.filter(is_processed=False)
        count = unprocessed.count()

        if count == 0:
            self.message_user(
                request, _("No unprocessed messages to reply to."), level="warning"
            )
            return


        self.message_user(
            request,
            _("Ready to send bulk reply to {count} messages. In a real system, email would be sent here.").format(count=count),
            level="success",
        )

    def get_queryset(self, request):
        """Query optimization"""
        return super().get_queryset(request).select_related()

    def has_add_permission(self, request):
        """Prevent adding new messages through admin"""
        return False

    def has_delete_permission(self, request, obj=None):
        """Allow deletion only for superusers"""
        return request.user.is_superuser

    def save_model(self, request, obj, form, change):
        """Automatic update of processing date"""
        if obj.is_processed and not obj.processed_at:
            from django.utils import timezone

            obj.processed_at = timezone.now()
        elif not obj.is_processed:
            obj.processed_at = None

        super().save_model(request, obj, form, change)



admin.site.register(ContactMessage, ContactMessageAdmin)


class SystemNotificationStatusFilter(admin.SimpleListFilter):
    title = _("Display status")
    parameter_name = "display_status"

    def lookups(self, request, model_admin):
        return (
            ("current", _("Showing now")),
            ("scheduled", _("Scheduled")),
            ("expired", _("Expired")),
        )

    def queryset(self, request, queryset):
        now = timezone.now()
        value = self.value()
        if value == "current":
            return queryset.filter(is_active=True, start_at__lte=now, end_at__gte=now)
        if value == "scheduled":
            return queryset.filter(start_at__gt=now)
        if value == "expired":
            return queryset.filter(end_at__lt=now)
        return queryset


@admin.register(SystemNotification)
class SystemNotificationAdmin(admin.ModelAdmin):
    list_display = (
        "message_preview",
        "is_active",
        "start_at",
        "end_at",
        "showing_now",
        "created_by",
    )
    list_filter = ("is_active", SystemNotificationStatusFilter, "start_at", "end_at")
    search_fields = (
        "message_ru",
        "message_uz",
        "message_en",
        "created_by__username",
        "created_by__email",
    )
    readonly_fields = (
        "created_by",
        "created_at",
        "updated_at",
        "showing_now",
        "message_preview",
    )
    date_hierarchy = "start_at"
    ordering = ("-start_at", "-created_at")
    list_select_related = ("created_by",)

    fieldsets = (
        (
            _("Notification content"),
            {
                "fields": (
                    "message_preview",
                    "message_ru",
                    "message_uz",
                    "message_en",
                )
            },
        ),
        (
            _("Display settings"),
            {"fields": ("is_active", "start_at", "end_at", "showing_now")},
        ),
        (
            _("Metadata"),
            {"fields": ("created_by", "created_at", "updated_at")},
        ),
    )

    @display(description=_("Text"))
    def message_preview(self, obj):
        return Truncator(obj.message_ru).chars(90)

    @display(boolean=True, description=_("Showing now"))
    def showing_now(self, obj):
        return obj.is_currently_displayed()

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("created_by")

    def save_model(self, request, obj, form, change):
        if not change and request.user.is_authenticated and not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(UserNotificationDismissal)
class UserNotificationDismissalAdmin(admin.ModelAdmin):
    list_display = ("user", "notification_preview", "dismissed_at")
    list_filter = ("dismissed_at",)
    search_fields = (
        "user__username",
        "user__email",
        "notification__message_ru",
        "notification__message_uz",
        "notification__message_en",
    )
    readonly_fields = ("user", "notification", "dismissed_at")
    ordering = ("-dismissed_at",)
    list_select_related = ("user", "notification")

    @display(description=_("Notification"))
    def notification_preview(self, obj):
        return obj.notification.short_message

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False







