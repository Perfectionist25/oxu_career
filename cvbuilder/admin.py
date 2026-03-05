from django.contrib import admin
from modeltranslation.admin import TranslationAdmin

from .models import CV, Language, CVTemplate


admin.site.register(CVTemplate)







































class LanguageInline(admin.TabularInline):
    """Inline admin for languages in CV"""

    model = Language
    extra = 0
    fields = ["name", "level"]
    verbose_name = "Language"
    verbose_name_plural = "Languages"


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
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
                    "address",
                    "city",
                    "region",
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
    inlines = [LanguageInline]




































@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """Admin interface for languages"""

    list_display = ("name", "level", "cv")
    list_filter = ("level",)
    search_fields = ("name", "cv__title", "cv__user__username")
    list_per_page = 20
    ordering = ("name",)

