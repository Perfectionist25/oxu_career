from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import (
    Event,
    EventCategory,
    EventComment,
    EventPhoto,
    EventRating,
    EventRegistration,
    EventSession,
    EventSpeaker,
)


class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    fields = ("user", "status", "registration_date", "payment_status")
    readonly_fields = ("registration_date",)


class EventSpeakerInline(admin.TabularInline):
    model = EventSpeaker
    extra = 0
    fields = ("name", "title", "organization", "order")


class EventSessionInline(admin.TabularInline):
    model = EventSession
    extra = 0
    fields = ("title", "session_type", "start_time", "end_time", "location")


@admin.register(EventCategory)
class EventCategoryAdmin(TranslationAdmin):
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
class EventAdmin(TranslationAdmin):
    """Admin interface for Event model with comprehensive management"""

    list_display = (
        "title",
        "organizer",
        "event_type",
        "start_date",
        "end_date",
        "status",
        "is_featured",
        "registration_count",
    )
    list_filter = (
        "status",
        "event_type",
        "category",
        "is_featured",
        "online_event",
        "created_at",
    )
    search_fields = ("title", "description", "organizer__username", "location")
    list_editable = ("status", "is_featured")
    readonly_fields = ("views_count", "registration_count", "created_at", "updated_at")
    prepopulated_fields = {"slug": ("title",)}
    inlines = [EventRegistrationInline, EventSpeakerInline, EventSessionInline]

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
            {"fields": ("location", "venue", "online_event", "online_link", "address")},
        ),
        (_("Organizer"), {"fields": ("organizer", "co_organizers")}),
        (_("Media"), {"fields": ("banner_image", "thumbnail")}),
        (
            _("Registration"),
            {
                "fields": (
                    "registration_required",
                    "registration_type",
                    "registration_deadline",
                    "max_participants",
                    "waitlist_enabled",
                )
            },
        ),
        (_("Pricing"), {"fields": ("is_free", "price", "currency")}),
        (
            _("Settings"),
            {
                "fields": (
                    "status",
                    "is_featured",
                    "show_attendee_list",
                    "allow_comments",
                    "tags",
                    "registration_link",
                    "materials_link",
                )
            },
        ),
        (_("Statistics"), {"fields": ("views_count", "registration_count")}),
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


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "event",
        "status",
        "registration_date",
        "payment_status",
        "has_attended",
    )
    list_filter = ("status", "payment_status", "registration_date", "event")
    search_fields = ("user__username", "user__email", "event__title")
    readonly_fields = ("registration_date",)

    fieldsets = (
        (
            _("Registration Information"),
            {"fields": ("event", "user", "status", "registration_date")},
        ),
        (
            _("Additional Information"),
            {"fields": ("dietary_restrictions", "special_requirements", "comments")},
        ),
        (_("Payment"), {"fields": ("payment_status", "payment_amount")}),
        (_("Check-in"), {"fields": ("qr_code", "check_in_time")}),
    )

    actions = ["mark_as_attended", "mark_as_no_show", "confirm_payment"]

    @display(description=_("Mark as attended"))
    def mark_as_attended(self, request, queryset):
        updated = queryset.update(status="attended")
        self.message_user(
            request,
            _("%(count)d registrations marked as attended") % {"count": updated},
        )

    @display(description=_("Mark as no show"))
    def mark_as_no_show(self, request, queryset):
        updated = queryset.update(status="no_show")
        self.message_user(
            request, _("%(count)d registrations marked as no show") % {"count": updated}
        )

    @display(description=_("Confirm payment"))
    def confirm_payment(self, request, queryset):
        updated = queryset.update(payment_status="paid")
        self.message_user(
            request, _("%(count)d payments confirmed") % {"count": updated}
        )


@admin.register(EventSpeaker)
class EventSpeakerAdmin(admin.ModelAdmin):
    list_display = ("name", "event", "organization", "order")
    list_filter = ("event",)
    search_fields = ("name", "title", "organization", "event__title")

    fieldsets = (
        (
            _("Speaker Information"),
            {"fields": ("event", "name", "title", "organization", "bio", "photo")},
        ),
        (
            _("Contact Information"),
            {"fields": ("email", "website", "linkedin", "twitter")},
        ),
        (_("Display"), {"fields": ("order",)}),
    )


@admin.register(EventSession)
class EventSessionAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "event",
        "session_type",
        "start_time",
        "end_time",
        "duration",
    )
    list_filter = ("session_type", "event")
    search_fields = ("title", "description", "event__title")

    fieldsets = (
        (
            _("Session Information"),
            {"fields": ("event", "title", "description", "session_type")},
        ),
        (_("Timing"), {"fields": ("start_time", "end_time")}),
        (_("Location"), {"fields": ("location",)}),
        (_("Speakers"), {"fields": ("speakers",)}),
        (_("Materials"), {"fields": ("presentation_url", "materials_url")}),
        (_("Display"), {"fields": ("order",)}),
    )


@admin.register(EventComment)
class EventCommentAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "short_comment", "is_approved", "created_at")
    list_filter = ("is_approved", "created_at")
    search_fields = ("user__username", "event__title", "comment")
    list_editable = ("is_approved",)
    readonly_fields = ("created_at", "updated_at")

    @display(description=_("Comment"))
    def short_comment(self, obj):
        if len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment

    actions = ["approve_comments", "disapprove_comments"]

    @display(description=_("Approve selected comments"))
    def approve_comments(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(
            request, _("%(count)d comments approved") % {"count": updated}
        )

    @display(description=_("Disapprove selected comments"))
    def disapprove_comments(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(
            request, _("%(count)d comments disapproved") % {"count": updated}
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


@admin.register(EventRating)
class EventRatingAdmin(admin.ModelAdmin):
    list_display = ("user", "event", "rating", "overall_rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("user__username", "event__title", "comment")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (_("Rating Information"), {"fields": ("event", "user", "rating", "comment")}),
        (
            _("Detailed Ratings"),
            {"fields": ("content_rating", "organization_rating", "venue_rating")},
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )
