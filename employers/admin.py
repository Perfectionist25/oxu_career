from django.contrib import admin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _

from .models import (
    CandidateNote,
    Company,
    CompanyReview,
    EmployerProfile,
    Interview,
    Job,
    JobApplication,
)


class EmployerProfileInline(admin.TabularInline):
    """Inline admin for employer profiles within company admin"""

    model = EmployerProfile
    extra = 0
    fields = ("user", "position", "department", "is_primary_contact", "is_active")
    verbose_name = "Employer Profile"
    verbose_name_plural = "Employer Profiles"


class JobInline(admin.TabularInline):
    """Inline admin for jobs within company admin"""

    model = Job
    extra = 0
    fields = ("title", "employment_type", "experience_level", "is_active", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Job Posting"
    verbose_name_plural = "Job Postings"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for managing companies"""

    list_display = (
        "name",
        "industry",
        "company_size",
        "is_verified",
        "is_active",
        "created_at",
    )
    list_filter = ("industry", "company_size", "is_verified", "is_active", "created_at")
    search_fields = ("name", "description", "headquarters")
    list_editable = ("is_verified", "is_active")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20
    inlines = [EmployerProfileInline, JobInline]

    fieldsets = (
        (
            _("Basic Information"),
            {"fields": ("name", "description", "website", "logo")},
        ),
        (
            _("Company Details"),
            {"fields": ("industry", "company_size", "founded_year", "headquarters")},
        ),
        (_("Contact Information"), {"fields": ("contact_email", "contact_phone")}),
        (_("Social Media"), {"fields": ("linkedin", "twitter", "facebook")}),
        (_("Status"), {"fields": ("is_verified", "is_active")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    """Admin interface for managing employer profiles"""

    list_display = ("user", "company", "position", "is_primary_contact", "is_active")
    list_filter = ("is_primary_contact", "is_active", "company")
    search_fields = ("user__username", "user__email", "company__name", "position")
    readonly_fields = ("created_at", "updated_at")
    list_per_page = 20

    fieldsets = (
        (
            _("Profile Information"),
            {"fields": ("user", "company", "position", "department", "phone")},
        ),
        (
            _("Permissions"),
            {
                "fields": (
                    "can_post_jobs",
                    "can_manage_jobs",
                    "can_view_candidates",
                    "can_contact_candidates",
                )
            },
        ),
        (_("Status"), {"fields": ("is_primary_contact", "is_active")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


class JobApplicationInline(admin.TabularInline):
    """Inline admin for job applications within job admin"""

    model = JobApplication
    extra = 0
    fields = ("candidate", "status", "created_at")
    readonly_fields = ("created_at",)
    verbose_name = "Job Application"
    verbose_name_plural = "Job Applications"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for managing job postings"""

    list_display = (
        "title",
        "company",
        "employment_type",
        "experience_level",
        "location",
        "is_active",
        "created_at",
    )
    list_filter = (
        "employment_type",
        "experience_level",
        "is_active",
        "is_featured",
        "created_at",
    )
    search_fields = ("title", "company__name", "description", "location")
    list_editable = ("is_active",)
    readonly_fields = ("views_count", "created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20
    inlines = [JobApplicationInline]

    fieldsets = (
        (
            _("Job Information"),
            {
                "fields": (
                    "company",
                    "posted_by",
                    "title",
                    "description",
                    "requirements",
                    "responsibilities",
                    "benefits",
                )
            },
        ),
        (
            _("Job Details"),
            {
                "fields": (
                    "employment_type",
                    "experience_level",
                    "location",
                    "remote_work",
                )
            },
        ),
        (
            _("Salary Information"),
            {"fields": ("salary_min", "salary_max", "currency", "hide_salary")},
        ),
        (
            _("Application Details"),
            {"fields": ("application_url", "contact_email", "skills_required")},
        ),
        (_("Status"), {"fields": ("is_active", "is_featured", "expires_at")}),
        (_("Statistics"), {"fields": ("views_count",)}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )


class InterviewInline(admin.TabularInline):
    """Inline admin for interviews within job application admin"""

    model = Interview
    extra = 0
    fields = ("scheduled_date", "interviewer", "status")
    readonly_fields = ("scheduled_date",)
    verbose_name = "Interview"
    verbose_name_plural = "Interviews"


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    """Admin interface for managing job applications"""

    list_display = ("candidate", "job", "status", "is_read", "created_at")
    list_filter = ("status", "is_read", "created_at")
    search_fields = (
        "candidate__username",
        "candidate__email",
        "job__title",
        "job__company__name",
    )
    readonly_fields = ("created_at", "updated_at", "status_changed_at")
    date_hierarchy = "created_at"
    list_per_page = 20
    inlines = [InterviewInline]

    fieldsets = (
        (
            _("Application Information"),
            {"fields": ("job", "candidate", "cv", "cover_letter", "expected_salary")},
        ),
        (_("Status"), {"fields": ("status", "is_read", "status_changed_at")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    actions = [
        "mark_as_read",
        "mark_as_unread",
        "set_status_new",
        "set_status_reviewed",
    ]

    @display(description=_("Mark selected applications as read"))
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request, _("%(count)d applications marked as read") % {"count": updated}
        )

    @display(description=_("Mark selected applications as unread"))
    def mark_as_unread(self, request, queryset):
        updated = queryset.update(is_read=False)
        self.message_user(
            request, _("%(count)d applications marked as unread") % {"count": updated}
        )


    @display(description=_("Set status to new"))
    def set_status_new(self, request, queryset):
        updated = queryset.update(status="new")
        self.message_user(
            request, _("%(count)d applications set to new status") % {"count": updated}
        )

    @display(description=_("Set status to reviewed"))
    def set_status_reviewed(self, request, queryset):
        updated = queryset.update(status="reviewed")
        self.message_user(
            request,
            _("%(count)d applications set to reviewed status") % {"count": updated},
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
