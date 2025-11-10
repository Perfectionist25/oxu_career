from django.contrib import admin
from django.contrib.admin import display
from django.utils.html import format_html

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


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    """Админ-панель для выпускников"""

    list_display = (
        "user",
        "graduation_year",
        "faculty",
        "current_position",
        "company",
        "is_mentor",
        "is_visible",
    )
    list_filter = (
        "graduation_year",
        "faculty",
        "is_mentor",
        "is_visible",
        "created_at",
    )
    search_fields = (
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "faculty",
        "company",
    )
    readonly_fields = ("created_at", "updated_at", "profile_photo")
    filter_horizontal = ("skills",)

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("user", "graduation_year", "faculty", "specialization")},
        ),
        (
            "Профессиональная информация",
            {"fields": ("current_position", "company", "skills")},
        ),
        (
            "Контакты и социальные сети",
            {"fields": ("phone", "linkedin", "github", "telegram", "website")},
        ),
        ("О себе", {"fields": ("bio", "photo", "profile_photo")}),
        (
            "Настройки видимости",
            {"fields": ("is_mentor", "is_visible", "show_contact_info")},
        ),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )

    @display(description="Фото профиля")
    def profile_photo(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.photo.url,
            )
        return "Нет фото"


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    """Админ-панель для компаний"""

    list_display = ("name", "industry", "website", "created_at")
    list_filter = ("industry", "created_at")
    search_fields = ("name", "industry", "description")
    readonly_fields = ("created_at", "updated_at", "company_logo")

    @display(description="Логотип")
    def company_logo(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="50" height="50" />', obj.logo.url)
        return "Нет логотипа"


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    """Админ-панель для вакансий"""

    list_display = (
        "title",
        "company",
        "employment_type",
        "location",
        "salary_range",
        "is_active",
        "created_at",
    )
    list_filter = (
        "employment_type",
        "remote_work",
        "currency",
        "is_active",
        "created_at",
    )
    search_fields = ("title", "company__name", "location", "description")
    readonly_fields = ("created_at", "updated_at", "views")
    date_hierarchy = "created_at"

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("title", "company", "posted_by", "employment_type")},
        ),
        ("Местоположение", {"fields": ("location", "remote_work")}),
        ("Зарплата", {"fields": ("salary_min", "salary_max", "currency")}),
        ("Описание", {"fields": ("description", "requirements", "benefits")}),
        ("Контакты", {"fields": ("contact_email", "application_url")}),
        ("Статус", {"fields": ("is_active", "expires_at", "views")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )

    @display(description="Зарплата")
    def salary_range(self, obj):
        if obj.salary_min and obj.salary_max:
            return f"{obj.salary_min} - {obj.salary_max} {obj.currency}"
        elif obj.salary_min:
            return f"от {obj.salary_min} {obj.currency}"
        elif obj.salary_max:
            return f"до {obj.salary_max} {obj.currency}"
        return "Не указана"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Админ-панель для мероприятий"""

    list_display = (
        "title",
        "event_type",
        "date",
        "time",
        "location",
        "registration_required",
        "is_active",
    )
    list_filter = ("event_type", "registration_required", "is_active", "date")
    search_fields = ("title", "description", "location")
    readonly_fields = ("created_at", "updated_at", "participants_count")
    filter_horizontal = ("participants",)

    @display(description="Количество участников")
    def participants_count(self, obj):
        return obj.participants.count()


@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    """Админ-панель для новостей"""

    list_display = ("title", "author", "created_at", "updated_at", "is_published")
    list_filter = ("is_published", "created_at", "updated_at")
    search_fields = ("title", "content", "author__username")
    readonly_fields = ("created_at", "updated_at", "views")
    prepopulated_fields = {"slug": ("title",)}

    fieldsets = (
        (
            "Основная информация",
            {"fields": ("title", "slug", "author", "content", "image", "tags")},
        ),
        ("Статус", {"fields": ("is_published", "views")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Mentorship)
class MentorshipAdmin(admin.ModelAdmin):
    """Админ-панель для менторства"""

    list_display = ("mentor", "mentee", "status", "created_at", "updated_at")
    list_filter = (
        "status",
        "expected_duration",
        "communication_preference",
        "created_at",
    )
    search_fields = ("mentor__user__username", "mentee__user__username", "message")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("Участники", {"fields": ("mentor", "mentee")}),
        (
            "Детали запроса",
            {"fields": ("message", "expected_duration", "communication_preference")},
        ),
        ("Статус", {"fields": ("status", "start_date", "end_date")}),
        ("Отзыв", {"fields": ("mentee_feedback", "mentor_feedback", "rating")}),
        ("Даты", {"fields": ("created_at", "updated_at")}),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Админ-панель для навыков"""

    list_display = ("name", "category")
    list_filter = ("category",)
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Connection)
class ConnectionAdmin(admin.ModelAdmin):
    """Админ-панель для связей между выпускниками"""

    list_display = ("from_user", "to_user", "status", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("from_user__user__username", "to_user__user__username")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Админ-панель для сообщений"""

    list_display = ("sender", "receiver", "subject", "is_read", "created_at")
    list_filter = ("is_read", "created_at")
    search_fields = (
        "sender__user__username",
        "receiver__user__username",
        "subject",
        "body",
    )
    readonly_fields = ("created_at",)

    fieldsets = (
        ("Основная информация", {"fields": ("sender", "receiver", "subject", "body")}),
        ("Статус", {"fields": ("is_read", "parent_message")}),
        ("Дата отправки", {"fields": ("created_at",)}),
    )


# Inline админ-классы
class JobInline(admin.TabularInline):
    """Inline для вакансий компании"""

    model = Job
    extra = 0
    fields = ("title", "employment_type", "location", "is_active")
    readonly_fields = ("created_at",)
    show_change_link = True


class MentorshipInline(admin.TabularInline):
    """Inline для менторских отношений"""

    model = Mentorship
    extra = 0
    fields = ("mentee", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentor"
    show_change_link = True


# Добавляем inline к CompanyAdmin
CompanyAdmin.inlines = [JobInline]


# Добавляем inline к AlumniAdmin для менторства (только если alumni является ментором)
class MentorshipAsMentorInline(admin.TabularInline):
    model = Mentorship
    extra = 0
    fields = ("mentee", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentor"
    verbose_name = "Менторство (как ментор)"
    verbose_name_plural = "Менторства (как ментор)"
    show_change_link = True


class MentorshipAsMenteeInline(admin.TabularInline):
    model = Mentorship
    extra = 0
    fields = ("mentor", "status", "created_at")
    readonly_fields = ("created_at",)
    fk_name = "mentee"
    verbose_name = "Менторство (как менти)"
    verbose_name_plural = "Менторства (как менти)"
    show_change_link = True


# Добавляем оба inline к AlumniAdmin
AlumniAdmin.inlines = [MentorshipAsMentorInline, MentorshipAsMenteeInline]

# Кастомизация админ-панели
admin.site.site_header = "Панель управления Ассоциацией Выпускников"
admin.site.site_title = "Ассоциация Выпускников"
admin.site.index_title = "Добро пожаловать в панель управления"
