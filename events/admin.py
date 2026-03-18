
from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget

from .models import (
    Event,
    EventCategory,
    EventEmployerCategory,
    EventParticipation,
    EventPhoto,
)
from .forms import EventForm


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "event_count", "color_display")
    list_filter = ("name",)
    search_fields = ("name", "description")




    @display(description=_("Events"))
    def event_count(self, obj):
        return obj.event_set.count()

    @display(description=_("Color"))
    def color_display(self, obj):
        if obj.color:
            return format_html(
                '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 3px;"></div>',
                obj.color,
            )
        return "-"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model"""

    form = EventForm

    list_display = (
        "title",
        "event_type",
        "start_date",
        "end_date",
        "status",
        "max_participants",
        "occupied_seats",
        "views_count",
    )

    list_filter = (
        "status",
        "event_type",
        "category",
        "created_at",
    )

    search_fields = ("title", "description", "location")
    list_editable = ("status",)
    readonly_fields = ("views_count", "created_at", "updated_at")


    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            _("Basic Information"),
            {
                "fields": (
                    "title",
                    "slug",
                    "short_description",
                    "description",
                    "category",
                    "event_type",
                )
            },
        ),
        (
            _("Date & Time"),
            {
                "fields": ("start_date", "end_date"),
                "classes": ("collapse",)
            }
        ),
        (
            _("Location"),
            {
                "fields": ("location", "max_participants", "allowed_employer_categories"),
                "classes": ("collapse",)
            },
        ),
        (
            _("Media"),
            {
                "fields": ("banner_image", "thumbnail"),
                "classes": ("collapse",)
            }
        ),
        (
            _("Settings"),
            {
                "fields": ("status", "tags",),
                "classes": ("collapse",)
            },
        ),
        (
            _("Statistics"),
            {
                "fields": ("views_count",),
                "classes": ("collapse",)
            },
        ),
        (
            _("Timestamps"),
            {
                "fields": ("created_at", "updated_at"),
                "classes": ("collapse",)
            }
        ),
    )

    actions = ["publish_events", "unpublish_events"]

    @admin.action(description=_("Publish selected events"))
    def publish_events(self, request, queryset):
        updated = queryset.update(status="published")
        self.message_user(
            request,
            _("Successfully published %(count)d event(s)") % {"count": updated},
            level='success'
        )

    @admin.action(description=_("Unpublish selected events"))
    def unpublish_events(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(
            request,
            _("Successfully unpublished %(count)d event(s)") % {"count": updated},
            level='warning'
        )

    list_per_page = 25
    date_hierarchy = 'start_date'
    save_on_top = True

    @display(description=_("Occupied Seats"))
    def occupied_seats(self, obj):
        return obj.seats_occupied


@admin.register(EventEmployerCategory)
class EventEmployerCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name",)


@admin.register(EventParticipation)
class EventParticipationAdmin(admin.ModelAdmin):
    list_display = (
        "event",
        "user",
        "role",
        "status",
        "attendance_status",
        "registered_at",
        "checked_in_at",
    )
    list_filter = ("role", "status", "attendance_status", "event")
    search_fields = ("event__title", "user__username", "user__email", "user__full_name")
    readonly_fields = ("registered_at", "checked_in_at", "updated_at", "qr_token")


@admin.register(EventPhoto)
class EventPhotoAdmin(admin.ModelAdmin):
    list_display = ("event", "caption", "uploaded_by", "uploaded_at")
    list_filter = ("event", "uploaded_at")
    search_fields = ("event__title", "caption", "uploaded_by__username")

    fieldsets = (
        (
            _("Photo Information"),
            {"fields": ("event", "image", "caption", "uploaded_by")},
        ),
        (_("Timestamps"), {"fields": ("uploaded_at",)},),
    )
