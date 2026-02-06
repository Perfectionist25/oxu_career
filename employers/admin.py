from django.contrib import admin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _

from .models import (
    CandidateNote,
    CompanyReview,
    Interview,
)


@admin.register(CandidateNote)
class CandidateNoteAdmin(admin.ModelAdmin):
    """Admin interface for managing employer notes about candidates"""

    list_display = ("candidate", "employer", "job", "is_private", "created_at")
    list_filter = ("is_private", "created_at")
    search_fields = ("candidate__username", "employer__user__username", "note")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            _("Note Information"),
            {"fields": ("candidate", "employer", "job", "note", "is_private")},
        ),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    """Admin interface for managing interviews"""

    list_display = (
        "application",
        "interviewer",
        "scheduled_date",
        "status",
        "created_at",
    )
    list_filter = ("status", "scheduled_date")
    search_fields = (
        "application__candidate__username",
        "application__job__title",
        "interviewer__user__username",
    )
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "scheduled_date"
    list_per_page = 20

    fieldsets = (
        (
            _("Interview Information"),
            {
                "fields": (
                    "application",
                    "interviewer",
                    "scheduled_date",
                    "duration",
                    "location",
                )
            },
        ),
        (_("Interview Details"), {"fields": ("notes", "status", "feedback", "rating")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    """Admin interface for managing company reviews"""

    list_display = (
        "company",
        "author",
        "rating",
        "is_verified",
        "is_published",
        "created_at",
    )
    list_filter = ("rating", "is_verified", "is_published", "created_at")
    search_fields = ("company__name", "author__username", "title")
    list_editable = ("is_verified", "is_published")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            _("Review Information"),
            {"fields": ("company", "author", "rating", "title", "review")},
        ),
        (_("Pros and Cons"), {"fields": ("pros", "cons")}),
        (_("Status"), {"fields": ("is_anonymous", "is_verified", "is_published")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    actions = ["publish_reviews", "unpublish_reviews", "verify_reviews"]

    @display(description=_("Publish selected reviews"))
    def publish_reviews(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(
            request, _("%(count)d reviews published") % {"count": updated}
        )

    @display(description=_("Unpublish selected reviews"))
    def unpublish_reviews(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(
            request, _("%(count)d reviews unpublished") % {"count": updated}
        )

    @display(description=_("Verify selected reviews"))
    def verify_reviews(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, _("%(count)d reviews verified") % {"count": updated})
