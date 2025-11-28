from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
# ЗАКОММЕНТИРУЙТЕ эту строку - временно отключаем modeltranslation
# from modeltranslation.admin import TranslationAdmin

from .models import (
    Event,
    EventCategory,
    EventPhoto
)


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):  # ИЗМЕНИТЕ здесь
    list_display = ("name", "event_count", "color_display")
    list_filter = ("name",)
    search_fields = ("name", "description")

    @display(description=_("Events"))
    def event_count(self, obj):
        return obj.event_set.count()

    @display(description=_("Color"))
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 3px;"></div>',
            obj.color,
        )

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for Event model with comprehensive management"""

    list_display = (
        "title",
        "event_type",
        "start_date",
        "end_date",
        "status",
        "is_featured"
    )
    list_filter = (
        "status",
        "event_type",
        "category",
        "is_featured",
        "created_at",
    )
    search_fields = ("title", "description", "location")
    list_editable = ("status", "is_featured")
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
        (_("Date & Time"), {"fields": ("start_date", "end_date")}),
        (
            _("Location"),
            {"fields": ("location",)},
        ),
        (_("Media"), {"fields": ("banner_image", "thumbnail")}),
        (_("Pricing"), {"fields": ("is_free", "price", "currency")}),
        (
            _("Settings"),
            {
                "fields": (
                    "status",
                    "is_featured",
                    "tags",
                )
            },
        ),
        (
            _("Statistics"),
            {"fields": ("views_count",)},
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    actions = ["publish_events", "unpublish_events", "mark_as_featured"]

    @display(description=_("Publish selected events"))
    def publish_events(self, request, queryset):
        updated = queryset.update(status="published")
        self.message_user(request, _("%(count)d events published") % {"count": updated})

    @display(description=_("Unpublish selected events"))
    def unpublish_events(self, request, queryset):
        updated = queryset.update(status="draft")
        self.message_user(
            request, _("%(count)d events unpublished") % {"count": updated}
        )

    @display(description=_("Mark as featured"))
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request, _("%(count)d events marked as featured") % {"count": updated}
        )


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
        (_("Display"), {"fields": ("order",)}),
        (_("Timestamps"), {"fields": ("uploaded_at",)}),
    )
