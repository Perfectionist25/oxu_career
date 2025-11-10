from django.contrib import admin

from .models import CV, CVTemplate, Education, Experience, Skill, Language

# Убраны Project, Certificate, CVSettings так как этих моделей больше нет


class EducationInline(admin.TabularInline):
    model = Education
    extra = 0
    fields = ["institution", "degree", "field_of_study", "graduation_year"]


class ExperienceInline(admin.TabularInline):
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


class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0
    fields = ["name", "level"]


class LanguageInline(admin.TabularInline):
    model = Language
    extra = 0
    fields = ["name", "level"]


@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active", "created_at")
    search_fields = ("name",)


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "full_name", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("title", "user__username", "full_name")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Основная информация", {"fields": ("user", "title", "template", "status")}),
        (
            "Личная информация",
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
        ("О себе", {"fields": ("summary",)}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )
    inlines = [EducationInline, ExperienceInline, SkillInline, LanguageInline]


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ("institution", "degree", "field_of_study", "graduation_year", "cv")
    list_filter = ("degree", "graduation_year")
    search_fields = ("institution", "degree", "field_of_study", "cv__title")


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ("position", "company", "start_date", "end_date", "is_current", "cv")
    list_filter = ("start_date", "is_current")
    search_fields = ("company", "position", "cv__title")


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "cv")
    list_filter = ("level",)
    search_fields = ("name", "cv__title")


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ("name", "level", "cv")
    list_filter = ("level",)
    search_fields = ("name", "cv__title")


# Убраны админ-классы для удаленных моделей:
# ProjectAdmin, CertificateAdmin, CVSettingsAdmin
