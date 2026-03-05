from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin
from .models import *

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


admin.site.site_header = "Alumni Association Management Panel"
admin.site.site_title = "Alumni Association"
admin.site.index_title = "Welcome to the Management Panel"