from django.contrib import admin
# ЗАКОММЕНТИРУЙТЕ эту строку - временно отключаем modeltranslation
# from modeltranslation.admin import TranslationAdmin

from .models import CV, CVTemplate, Education, Experience, Skill, Language


class EducationInline(admin.TabularInline):
    """Inline admin for education entries in CV"""

    model = Education
    extra = 0
    fields = ["institution", "degree", "field_of_study", "graduation_year"]
    verbose_name = "Education"
    verbose_name_plural = "Education"


class ExperienceInline(admin.TabularInline):
    """Inline admin for work experience entries in CV"""

    model = Experience
    extra = 0
    fields = [
        "company",
        "position",
        "start_date",
        "end_date",
        "is_current",
        "description",
    ]
    verbose_name = "Work Experience"
    verbose_name_plural = "Work Experience"


class SkillInline(admin.TabularInline):
    """Inline admin for skills in CV"""

    model = Skill
    extra = 0
    fields = ["name", "level"]
    verbose_name = "Skill"
    verbose_name_plural = "Skills"


class LanguageInline(admin.TabularInline):
    """Inline admin for languages in CV"""

    model = Language
    extra = 0
    fields = ["name", "level"]
    verbose_name = "Language"
    verbose_name_plural = "Languages"


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    """Admin interface for CV templates"""

    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)
    readonly_fields = ("created_at",)
    list_per_page = 20

    fieldsets = (
        (
            "Template Information",
            {"fields": ("name", "thumbnail", "template_file", "is_active")},
        ),
        (
            "Timestamps",
            {"fields": ("created_at",)},
        ),
    )


# ИЗМЕНИТЕ TranslationAdmin на admin.ModelAdmin
@admin.register(CV)
class CVAdmin(admin.ModelAdmin):  # ИЗМЕНИТЕ здесь
    """Admin interface for CV management with comprehensive editing"""

    list_display = ("title", "user", "full_name", "status", "template", "created_at")
    list_filter = ("status", "template", "created_at", "updated_at")
    search_fields = ("title", "user__username", "user__first_name", "user__last_name", "full_name")
    readonly_fields = ("created_at", "updated_at")
    date_hierarchy = "created_at"
    list_per_page = 20

    fieldsets = (
        (
            "Basic Information",
            {"fields": ("user", "title", "template", "status")},
        ),
        (
            "Personal Information",
            {
                "fields": (
                    "full_name",
                    "email",
                    "phone",
                    "location",
                    "salary_expectation",
                )
            },
        ),
        (
            "Professional Summary",
            {"fields": ("summary",)},
        ),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at")},
        ),
    )
    inlines = [EducationInline, ExperienceInline, SkillInline, LanguageInline]


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    """Admin interface for education entries"""

    list_display = ("institution", "degree", "field_of_study", "graduation_year", "cv")
    list_filter = ("degree", "graduation_year")
    search_fields = ("institution", "field_of_study", "cv__title", "cv__user__username")
    list_per_page = 20
    ordering = ("-graduation_year",)


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    """Admin interface for work experience entries"""

    list_display = ("position", "company", "start_date", "end_date", "is_current", "cv")
    list_filter = ("start_date", "is_current", "company")
    search_fields = ("company", "position", "cv__title", "cv__user__username")
    date_hierarchy = "start_date"
    list_per_page = 20
    ordering = ("-start_date",)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Admin interface for skills"""

    list_display = ("name", "level", "cv")
    list_filter = ("level",)
    search_fields = ("name", "cv__title", "cv__user__username")
    list_per_page = 25
    ordering = ("name",)


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin interface for languages"""

    list_display = ("name", "level", "cv")
    list_filter = ("level",)
    search_fields = ("name", "cv__title", "cv__user__username")
    list_per_page = 20
    ordering = ("name",)


# Removed admin classes for deleted models:
# ProjectAdmin, CertificateAdmin, CVSettingsAdmin