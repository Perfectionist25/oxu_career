from django.contrib import admin
from .models import CVTemplate, CV, Education, Experience, Skill, Project, Language, Certificate, CVSettings

class EducationInline(admin.TabularInline):
    model = Education
    extra = 0

class ExperienceInline(admin.TabularInline):
    model = Experience
    extra = 0

class SkillInline(admin.TabularInline):
    model = Skill
    extra = 0

class ProjectInline(admin.TabularInline):
    model = Project
    extra = 0

class LanguageInline(admin.TabularInline):
    model = Language
    extra = 0

class CertificateInline(admin.TabularInline):
    model = Certificate
    extra = 0

@admin.register(CVTemplate)
class CVTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')

@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'template')
    search_fields = ('title', 'user__username', 'full_name')
    inlines = [EducationInline, ExperienceInline, SkillInline, ProjectInline, LanguageInline, CertificateInline]

@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'degree', 'cv', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('institution', 'degree', 'field_of_study')

@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('position', 'company', 'cv', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('company', 'position')

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'cv', 'category')
    list_filter = ('level', 'category')
    search_fields = ('name', 'category')

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'cv', 'start_date', 'end_date')
    list_filter = ('start_date', 'end_date')
    search_fields = ('name', 'technologies')

@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('name', 'level', 'cv')
    list_filter = ('level',)
    search_fields = ('name',)

@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ('name', 'issuing_organization', 'cv', 'issue_date')
    list_filter = ('issue_date',)
    search_fields = ('name', 'issuing_organization')

@admin.register(CVSettings)
class CVSettingsAdmin(admin.ModelAdmin):
    list_display = ('cv', 'font_family', 'font_size')
    search_fields = ('cv__title',)