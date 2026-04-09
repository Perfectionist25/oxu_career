from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.text import Truncator
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

class ContactMessage(models.Model):
    STATUS_CHOICES = [
        ("new", _("New")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("spam", _("Spam")),
    ]

    name = models.CharField(max_length=255, verbose_name=_("Name"))
    email = models.EmailField(verbose_name=_("Email"))
    subject = models.CharField(max_length=255, blank=True, verbose_name=_("Subject"))
    message = models.TextField(verbose_name=_("Message"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Phone"))
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="new", verbose_name=_("Status")
    )
    is_processed = models.BooleanField(default=False, verbose_name=_("Processed"))
    processed_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Processed At")
    )
    admin_notes = models.TextField(blank=True, verbose_name=_("Admin Notes"))
    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name=_("IP Address")
    )
    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Contact Message")
        verbose_name_plural = _("Contact Messages")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["created_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_processed"]),
        ]

    def __str__(self):
        return f"Message from {self.name} ({self.email})"

    def get_status_color(self):
        """Status color for admin panel"""
        colors = {
            "new": "orange",
            "in_progress": "blue",
            "completed": "green",
            "spam": "red",
        }
        return colors.get(self.status, "gray")


class SystemNotification(models.Model):
    message_ru = models.TextField(verbose_name=_("Message (Russian)"))
    message_uz = models.TextField(blank=True, verbose_name=_("Message (Uzbek)"))
    message_en = models.TextField(blank=True, verbose_name=_("Message (English)"))
    start_at = models.DateTimeField(verbose_name=_("Start at"))
    end_at = models.DateTimeField(verbose_name=_("End at"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_system_notifications",
        verbose_name=_("Created by"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("System notification")
        verbose_name_plural = _("System notifications")
        ordering = ["-start_at", "-created_at"]
        indexes = [
            models.Index(fields=["is_active", "start_at", "end_at"]),
            models.Index(fields=["-start_at", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.short_message} [{self.start_at:%Y-%m-%d %H:%M}]"

    def clean(self):
        if self.start_at and self.end_at and self.end_at <= self.start_at:
            raise ValidationError(
                {"end_at": _("End date and time must be later than start date and time.")}
            )

        if not self.message_ru:
            raise ValidationError(
                {
                    "message_ru": _(
                        "Russian text is required because it is used as the fallback language."
                    )
                }
            )

    @property
    def short_message(self):
        return Truncator(self.message_ru or self.message_uz or self.message_en).chars(90)

    def get_message(self, language_code=None):
        normalized_language = (language_code or get_language() or "ru").split("-")[0]
        localized_message = {
            "ru": self.message_ru,
            "uz": self.message_uz,
            "en": self.message_en,
        }.get(normalized_language)
        return localized_message or self.message_ru

    @property
    def localized_message(self):
        return self.get_message()

    def is_currently_displayed(self, at=None):
        if not self.start_at or not self.end_at:
            return False
        at = at or timezone.now()
        return self.is_active and self.start_at <= at <= self.end_at


class UserNotificationDismissal(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="system_notification_dismissals",
        verbose_name=_("User"),
    )
    notification = models.ForeignKey(
        SystemNotification,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="dismissals",
        verbose_name=_("Notification"),
    )
    dismissed_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Dismissed at"))

    class Meta:
        verbose_name = _("User notification dismissal")
        verbose_name_plural = _("User notification dismissals")
        ordering = ["-dismissed_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "notification"],
                name="core_unique_user_notification_dismissal",
            )
        ]
        indexes = [
            models.Index(fields=["user", "dismissed_at"]),
            models.Index(fields=["notification", "dismissed_at"]),
        ]

    def __str__(self):
        return f"{self.user} -> {self.notification.short_message}"
