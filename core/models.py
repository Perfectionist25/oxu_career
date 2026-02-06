# core/models.py
from django.db import models
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
