from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
# ЗАКОММЕНТИРУЙТЕ эту строку - временно отключаем modeltranslation
# from modeltranslation.admin import TranslationAdmin

from .models import (
    Alumni,
    Company,
    Connection,
    Event,
    Job,
    Mentorship,
    Message,
    News,
    Skill,
)


# ИЗМЕНИТЕ TranslationAdmin на admin.ModelAdmin
@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):  # ИЗМЕНИТЕ здесь
    """Admin interface for alumni profiles with comprehensive management"""

    list_display = (
        "user",
        "graduation_year",
        "faculty",
        "current_position",
        "company",
        "is_mentor",
        "is_visible",
        "created_at",
    )
    list_filter = (
        "graduation_year",
        "faculty",
        "degree",
        "is_mentor",
        "is_visible",
        "is_open_to_opportunities",
        "created_at",
        "country",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "name",
        "faculty",
        "current_position",
        "company__name",
        "specialization",
        "city",
    )
    readonly_fields = ("created_at", "updated_at", "profile_photo", "profile_views")
    filter_horizontal = ("skills",)
    list_per_page = 25
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "name", "graduation_year", "faculty", "degree", "specialization")},
        ),
        (
            "Professional Information",
            {"fields": ("current_position", "company", "profession", "industry", "skills", "expertise_areas", "years_of_experience", "is_open_to_opportunities")},
        ),
        (
            "Contact Information",
            {"fields": ("email", "phone", "linkedin", "github", "telegram", "twitter", "facebook", "instagram", "website")},
        ),
        (
            "Location",
            {"fields": ("country", "city")},
        ),
        (
            "Bio and Media",
            {"fields": ("bio", "photo", "resume", "profile_photo")},
        ),
        (
            "Settings and Status",
            {"fields": ("is_mentor", "is_visible", "show_contact_info", "profile_views")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @display(description="Profile Photo")
    def profile_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url,
            )
        return "No photo"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Admin interface for company profiles"""

    list_display = ("name", "industry", "website", "is_verified", "is_active", "created_at")
    list_filter = ("industry", "is_verified", "is_active", "founded_year", "created_at")
    search_fields = ("name", "industry", "description", "website", "email", "address")
    readonly_fields = ("created_at", "updated_at", "company_logo")
    list_per_page = 20

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "industry", "description", "website", "logo", "company_logo")},
        ),
        (
            "Contact Information",
            {"fields": ("email", "phone", "address")},
        ),
        (
            "Company Details",
            {"fields": ("employees_count", "founded_year")},
        ),
        (
            "Status",
            {"fields": ("is_verified", "is_active")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @display(description="Logo")
    def company_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "No logo"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Admin interface for job postings"""

    list_display = (
        "title",
        "company",
        "employment_type",
        "location",
        "salary_range",
        "is_active",
        "views",
        "created_at",
    )
    list_filter = (
        "employment_type",
        "remote_work",
        "currency",
        "is_active",
        "expires_at",
        "created_at",
    )
    search_fields = ("title", "company__name", "posted_by__name", "location", "description")
    readonly_fields = ("created_at", "updated_at", "views")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "company", "posted_by", "employment_type")},
        ),
        (
            "Location",
            {"fields": ("location", "remote_work")},
        ),
        (
            "Salary",
            {"fields": ("salary_min", "salary_max", "currency")},
        ),
        (
            "Description",
            {"fields": ("description", "requirements", "benefits")},
        ),
        (
            "Contact",
            {"fields": ("contact_email", "application_url")},
        ),
        (
            "Status",
            {"fields": ("is_active", "expires_at", "views")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @display(description="Salary Range")
    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min} - {obj.salary_max} {obj.currency}"
        elif obj.salary_min:
            return f"from {obj.salary_min} {obj.currency}"
        elif obj.salary_max:
            return f"up to {obj.salary_max} {obj.currency}"
        return "Not specified"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin interface for alumni events"""

    list_display = (
        "title",
        "event_type",
        "date",
        "time",
        "location",
        "organizer",
        "participants_count",
        "registration_required",
        "is_active",
        "created_at",
    )
    list_filter = ("event_type", "registration_required", "is_active", "date", "organizer")
    search_fields = ("title", "description", "location", "organizer__name")
    readonly_fields = ("created_at", "updated_at", "participants_count")
    filter_horizontal = ("participants",)
    date_hierarchy = "date"
    list_per_page = 20

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "description", "event_type", "organizer")},
        ),
        (
            "Date and Time",
            {"fields": ("date", "time", "location")},
        ),
        (
            "Registration",
            {"fields": ("registration_required", "max_participants", "participants", "participants_count")},
        ),
        (
            "Status",
            {"fields": ("is_active",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )

    @display(description="Participants Count")
    def participants_count(self, obj):
        return obj.participants.count()


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Admin interface for alumni news and announcements"""

    list_display = ("title", "author", "category", "is_published", "views", "created_at")
    list_filter = ("is_published", "category", "created_at", "updated_at", "author")
    search_fields = ("title", "content", "author__name", "tags")
    readonly_fields = ("created_at", "updated_at", "views")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("title", "slug", "author", "category", "content", "image", "tags")},
        ),
        (
            "Status",
            {"fields": ("is_published", "views")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    """Admin interface for mentorship relationships"""

    list_display = ("mentor", "mentee", "status", "start_date", "end_date", "rating", "created_at")
    list_filter = (
        "status",
        "expected_duration",
        "communication_preference",
        "start_date",
        "end_date",
        "created_at",
    )
    search_fields = ("mentor__name", "mentee__name", "message")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Participants",
            {"fields": ("mentor", "mentee")},
        ),
        (
            "Request Details",
            {"fields": ("message", "expected_duration", "communication_preference")},
        ),
        (
            "Status",
            {"fields": ("status", "start_date", "end_date")},
        ),
        (
            "Feedback",
            {"fields": ("mentee_feedback", "mentor_feedback", "rating")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin interface for skills and competencies"""

    list_display = ("name", "category", "slug")
    list_filter = ("category",)
    search_fields = ("name", "description", "category")
    prepopulated_fields = {"slug": ("name",)}
    list_per_page = 25
    ordering = ("category", "name")

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("name", "slug", "category", "description")},
        ),
    )


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    """Admin interface for networking connections between alumni"""

    list_display = ("from_user", "to_user", "status", "created_at", "responded_at")
    list_filter = ("status", "created_at", "responded_at")
    search_fields = ("from_user__name", "to_user__name", "message")
    readonly_fields = ("created_at", "responded_at")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Participants",
            {"fields": ("from_user", "to_user")},
        ),
        (
            "Connection Details",
            {"fields": ("status", "message")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "responded_at")},
        ),
    )


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for internal messaging between alumni"""

    list_display = ("sender", "receiver", "subject", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = ("sender__name", "receiver__name", "subject", "body")
    readonly_fields = ("created_at",)
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Participants",
            {"fields": ("sender", "receiver")},
        ),
        (
            "Message Content",
            {"fields": ("subject", "body", "is_read")},
        ),
        (
            "Threading",
            {"fields": ("parent_message",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at",)},
        ),
    )


# Inline admin classes
class JobInline(admin.TabularInline):
    """Inline for company job postings"""

    model = Job
    extra = 0
    fields = ("title", "employment_type", "location", "is_active")
    readonly_fields = ("created_at",)
    show_change_link = True


class MentorshipInline(admin.TabularInline):
    """Inline for mentorship relationships"""

    model = Mentorship
    extra = 0
    fields = ("mentee", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentor"
    show_change_link = True


# Add inline to CompanyAdmin
CompanyAdmin.inlines = [JobInline]


# Add inline to AlumniAdmin for mentorship (only if alumni is a mentor)
class MentorshipAsMentorInline(admin.TabularInline):
    model = Mentorship
    extra = 0
    fields = ("mentee", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentor"
    verbose_name = "Mentorship (as mentor)"
    verbose_name_plural = "Mentorships (as mentor)"
    show_change_link = True


class MentorshipAsMenteeInline(admin.TabularInline):
    model = Mentorship
    extra = 0
    fields = ("mentor", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentee"
    verbose_name = "Mentorship (as mentee)"
    verbose_name_plural = "Mentorships (as mentee)"
    show_change_link = True


# Add both inlines to AlumniAdmin
AlumniAdmin.inlines = [MentorshipAsMentorInline, MentorshipAsMenteeInline]

# Admin site customization
admin.site.site_header = "Alumni Association Management Panel"
admin.site.site_title = "Alumni Association"
admin.site.index_title = "Welcome to the Management Panel"