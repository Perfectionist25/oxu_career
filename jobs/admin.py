from django.contrib import admin
from django.contrib.admin import display
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import Job, Industry, JobApplication, SavedJob, JobAlert


class JobInline(admin.TabularInline):
    model = Job
    extra = 0
    fields = ("title", "employment_type", "location", "is_active", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Industry)
class IndustryAdmin(TranslationAdmin):
    list_display = ("name", "job_count")
    list_filter = ("name",)
    search_fields = ("name", "description")

    @display(description=_("Jobs"))
    def job_count(self, obj):
        # Считаем вакансии через EmployerProfile
        from accounts.models import EmployerProfile

        employer_profiles = EmployerProfile.objects.filter(industry=obj.name)
        return Job.objects.filter(employer__in=employer_profiles).count()


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ("candidate", "status", "created_at")
    readonly_fields = ("created_at",)


@admin.register(Job)
class JobAdmin(TranslationAdmin):
    """Admin interface for Job model with optimized display and filters"""

    list_display = (
        "title",
        "employer_company",
        "employment_type",
        "experience_level",
        "location",
        "is_active",
        "is_featured",
        "created_at",
    )
    list_filter = (
        "employment_type",
        "experience_level",
        "is_active",
        "is_featured",
        "created_at",
    )
    search_fields = ("title", "employer__company_name", "description", "location")
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
                    "location",
                    "employment_type",
                    "experience_level",
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

    @display(description=_("Company"), ordering="employer__company_name")
    def employer_company(self, obj):
        return obj.employer.company_name

    @display(description=_("Employer"))
    def employer_info(self, obj):
        if obj.employer:
            return f"{obj.employer.company_name} ({obj.employer.user.username})"
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
class JobApplicationAdmin(TranslationAdmin):
    list_display = ("candidate", "job_with_company", "status", "is_read", "created_at")
    list_filter = ("status", "is_read", "created_at")
    search_fields = (
        "candidate__username",
        "candidate__email",
        "job__title",
        "job__employer__company_name",
    )
    readonly_fields = ("created_at", "updated_at", "status_changed_at")

    fieldsets = (
        (
            _("Application Information"),
            {"fields": ("job", "candidate", "cv", "cover_letter")},
        ),
        (
            _("Candidate Details"),
            {"fields": ("expected_salary", "notice_period")},
        ),
        (_("Status"), {"fields": ("status", "is_read", "status_changed_at", "source")}),
        (_("Timestamps"), {"fields": ("created_at", "updated_at")}),
    )

    @display(description=_("Job"))
    def job_with_company(self, obj):
        return f"{obj.job.title} - {obj.job.employer.company_name}"

    actions = [
        "mark_as_reviewed",
        "mark_as_interview",
        "mark_as_rejected",
        "mark_as_read",
    ]

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
    search_fields = ("user__username", "job__title", "job__employer__company_name")
    readonly_fields = ("created_at",)

    @display(description=_("Job"))
    def job_with_company(self, obj):
        return f"{obj.job.title} - {obj.job.employer.company_name}"



@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "is_active", "frequency", "last_sent", "created_at")
    list_filter = ("is_active", "frequency", "created_at")
    search_fields = ("user__username", "name", "keywords")
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
