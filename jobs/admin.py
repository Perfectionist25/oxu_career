from django.contrib import admin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _



from .models import Job, JobApplication, SavedJob, ViewedJob, JobAlert


class JobInline(admin.TabularInline):
    model = Job
    extra = 0
    fields = ("title", "employment_type", "location", "is_active", "created_at")
    readonly_fields = ("created_at",)

class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ("user", "status", "created_at")
    readonly_fields = ("created_at",)



@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for Job model with optimized display and filters"""

    list_display = (
        "title",
        "employer_company",
        "job_market",
        "employment_type",
        "experience_level",
        "candidate_type",
        "gender_requirement",
        "location",
        "is_active",
        "is_featured",
        "created_at",
    )
    list_filter = (
        "job_market",
        "employment_type",
        "experience_level",
        "candidate_type",
        "gender_requirement",
        "is_active",
        "is_featured",
        "created_at",
    )
    search_fields = ("title", "company__name", "description", "location")
    list_editable = ("is_active", "is_featured")
    readonly_fields = (
        "views_count",
        "applications_count",
        "created_at",
        "updated_at",
        "employer_info",
    )
    inlines = [JobApplicationInline]

    fieldsets = (
        (
            _("Job Information"),
            {"fields": ("title", "description", "employer")},
        ),
        (
            _("Location & Type"),
            {
                "fields": (
                    "job_market",
                    "location",
                    "employment_type",
                    "experience_level",
                    "candidate_type",
                    "gender_requirement",
                )
            },
        ),
        (
            _("Salary Information"),
            {
                "fields": (
                    "salary_min",
                    "salary_max",
                    "currency",
                    "hide_salary",
                )
            },
        ),
        (
            _("Job Details"),
            {"fields": ("requirements", "responsibilities", "benefits")}
        ),
        (_("Skills"), {"fields": ("skills_required",)}),
        (
            _("Contact Information"),
            {"fields": ("contact_email",)},
        ),
        (
            _("Status"),
            {"fields": ("is_active", "is_featured", "expires_at")},
        ),
        (_("Statistics"), {"fields": ("views_count", "applications_count")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Company"), ordering="company__name")
    def employer_company(self, obj):
        return obj.company.name

    @display(description=_("Employer"))
    def employer_info(self, obj):
        if obj.company:
            return f"{obj.company.name} ({obj.created_by.user.username if obj.created_by else 'N/A'})"
        return "-"

    actions = ["activate_jobs", "deactivate_jobs", "mark_as_featured"]

    @display(description=_("Activate selected jobs"))
    def activate_jobs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _("%(count)d jobs activated") % {"count": updated})

    @display(description=_("Deactivate selected jobs"))
    def deactivate_jobs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _("%(count)d jobs deactivated") % {"count": updated})

    @display(description=_("Mark selected jobs as featured"))
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(
            request, _("%(count)d jobs marked as featured") % {"count": updated}
        )



@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ("user", "job_with_company", "status", "is_read", "created_at")
    list_filter = ("status", "is_read", "created_at")
    search_fields = (
        "user__username",
        "user__email",
        "job__title",
        "job__company__name",
    )
    raw_id_fields = ["user", "job", "cv"]
    readonly_fields = ("created_at", "updated_at", "status_changed_at")

    fieldsets = (
        (
            _("Application Information"),
            {"fields": ("job", "user", "cv", "cover_letter")},
        ),
        (
            _("Candidate Details"),
            {"fields": ("expected_salary", "notice_period", "available_from")},
        ),
        (_("Status"), {"fields": ("status", "is_read", "status_changed_at", "source")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Job"))
    def job_with_company(self, obj):
        return f"{obj.job.title} - {obj.job.company.name}"

    actions = [
        "mark_as_reviewed",
        "mark_as_interview",
        "mark_as_rejected",
        "mark_as_read",
        "mark_as_hired",
        "mark_as_withdrawn",
    ]

    @display(description=_("Mark as reviewed"))
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status="reviewed")
        self.message_user(
            request, _("%(count)d applications marked as reviewed") % {"count": updated}
        )

    @display(description=_("Mark as interview"))
    def mark_as_interview(self, request, queryset):
        updated = queryset.update(status="interview")
        self.message_user(
            request,
            _("%(count)d applications marked as interview") % {"count": updated},
        )

    @display(description=_("Mark as rejected"))
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status="rejected")
        self.message_user(
            request, _("%(count)d applications marked as rejected") % {"count": updated}
        )

    @display(description=_("Mark as hired"))
    def mark_as_hired(self, request, queryset):
        updated = queryset.update(status="hired")
        self.message_user(
            request, _("%(count)d applications marked as hired") % {"count": updated}
        )

    @display(description=_("Mark as withdrawn"))
    def mark_as_withdrawn(self, request, queryset):
        updated = queryset.update(status="withdrawn")
        self.message_user(
            request, _("%(count)d applications marked as withdrawn") % {"count": updated}
        )

    @display(description=_("Mark as read"))
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(
            request, _("%(count)d applications marked as read") % {"count": updated}
        )


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job_with_company", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "job__title", "job__company__name")
    raw_id_fields = ["user", "job"]
    readonly_fields = ("created_at",)

    @display(description=_("Job"))
    def job_with_company(self, obj):
        return f"{obj.job.title} - {obj.job.company.name}"


@admin.register(ViewedJob)
class ViewedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job_with_company", "first_viewed_at", "last_viewed_at")
    list_filter = ("first_viewed_at", "last_viewed_at")
    search_fields = ("user__username", "job__title", "job__company__name")
    raw_id_fields = ["user", "job"]
    readonly_fields = ("first_viewed_at", "last_viewed_at")

    @display(description=_("Job"))
    def job_with_company(self, obj):
        return f"{obj.job.title} - {obj.job.company.name}"


@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "is_active", "frequency", "last_sent", "created_at")
    list_filter = ("is_active", "frequency", "created_at")
    search_fields = ("user__username", "name", "keywords")
    raw_id_fields = ["user"]
    readonly_fields = ("created_at", "updated_at", "last_sent")

    fieldsets = (
        (
            _("Alert Information"),
            {"fields": ("user", "name", "is_active", "frequency")},
        ),
        (
            _("Search Criteria"),
            {
                "fields": (
                    "keywords",
                    "location",
                    "industry",
                    "employment_type",
                    "experience_level",
                )
            },
        ),
        (_("Timestamps"), {"fields": ("last_sent", "created_at", "updated_at")}),
    )

    actions = ["activate_alerts", "deactivate_alerts"]

    @display(description=_("Activate selected alerts"))
    def activate_alerts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _("%(count)d alerts activated") % {"count": updated})

    @display(description=_("Deactivate selected alerts"))
    def deactivate_alerts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(
            request, _("%(count)d alerts deactivated") % {"count": updated}
        )
