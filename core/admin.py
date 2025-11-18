from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import ContactMessage


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
        # In a real application, generate a CSV file here
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

        # In a real application, email sending logic would be here
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


# Регистрация модели
admin.site.register(ContactMessage, ContactMessageAdmin)

# Дополнительно: если у вас есть другие модели в core, добавьте их здесь
# Например, для модели Settings (если есть)

# class SettingsAdmin(admin.ModelAdmin):
#     list_display = ('key', 'value', 'description')
#     list_editable = ('value',)
#
# admin.site.register(Settings, SettingsAdmin)
