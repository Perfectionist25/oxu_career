from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import Industry, Company, Job, JobApplication, SavedJob, JobAlert, CompanyReview, InterviewExperience

class JobInline(admin.TabularInline):
    model = Job
    extra = 0
    fields = ('title', 'employment_type', 'location', 'is_active', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ('name', 'job_count', 'company_count')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    
    def job_count(self, obj):
        return Job.objects.filter(company__industry=obj).count()
    job_count.short_description = _('Jobs')
    
    def company_count(self, obj):
        return obj.company_set.count()
    company_count.short_description = _('Companies')

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'company_size', 'is_verified', 'is_active', 'job_count')
    list_filter = ('industry', 'company_size', 'is_verified', 'is_active', 'created_at')
    search_fields = ('name', 'description', 'headquarters')
    list_editable = ('is_verified', 'is_active')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [JobInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description', 'website', 'logo')
        }),
        (_('Company Details'), {
            'fields': ('industry', 'company_size', 'founded_year', 'headquarters')
        }),
        (_('Contact Information'), {
            'fields': ('contact_email', 'contact_phone')
        }),
        (_('Social Media'), {
            'fields': ('linkedin', 'twitter', 'facebook')
        }),
        (_('Status'), {
            'fields': ('is_verified', 'is_active')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def job_count(self, obj):
        return obj.jobs.count()
    job_count.short_description = _('Jobs')

class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    fields = ('candidate', 'status', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'company', 'employment_type', 'experience_level', 'location', 'is_active', 'is_featured', 'created_at')
    list_filter = ('employment_type', 'experience_level', 'education_level', 'is_active', 'is_featured', 'is_urgent', 'created_at')
    search_fields = ('title', 'company__name', 'description', 'location')
    list_editable = ('is_active', 'is_featured')
    readonly_fields = ('views_count', 'applications_count', 'created_at', 'updated_at')
    inlines = [JobApplicationInline]
    
    fieldsets = (
        (_('Job Information'), {
            'fields': ('title', 'short_description', 'description', 'company')
        }),
        (_('Location & Type'), {
            'fields': ('location', 'remote_work', 'hybrid_work', 'employment_type', 'experience_level', 'education_level')
        }),
        (_('Salary Information'), {
            'fields': ('salary_min', 'salary_max', 'currency', 'hide_salary', 'salary_negotiable')
        }),
        (_('Job Details'), {
            'fields': ('requirements', 'responsibilities', 'benefits')
        }),
        (_('Skills'), {
            'fields': ('skills_required', 'preferred_skills')
        }),
        (_('Contact Information'), {
            'fields': ('contact_email', 'contact_person', 'application_url')
        }),
        (_('Status'), {
            'fields': ('is_active', 'is_featured', 'is_urgent', 'expires_at')
        }),
        (_('Statistics'), {
            'fields': ('views_count', 'applications_count')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_jobs', 'deactivate_jobs', 'mark_as_featured', 'mark_as_urgent']
    
    def activate_jobs(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('%(count)d jobs activated') % {'count': updated})
    activate_jobs.short_description = _('Activate selected jobs')
    
    def deactivate_jobs(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('%(count)d jobs deactivated') % {'count': updated})
    deactivate_jobs.short_description = _('Deactivate selected jobs')
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, _('%(count)d jobs marked as featured') % {'count': updated})
    mark_as_featured.short_description = _('Mark as featured')
    
    def mark_as_urgent(self, request, queryset):
        updated = queryset.update(is_urgent=True)
        self.message_user(request, _('%(count)d jobs marked as urgent') % {'count': updated})
    mark_as_urgent.short_description = _('Mark as urgent')

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('candidate', 'job', 'status', 'is_read', 'created_at')
    list_filter = ('status', 'is_read', 'created_at')
    search_fields = ('candidate__username', 'candidate__email', 'job__title', 'job__company__name')
    readonly_fields = ('created_at', 'updated_at', 'status_changed_at')
    
    fieldsets = (
        (_('Application Information'), {
            'fields': ('job', 'candidate', 'cv', 'cover_letter')
        }),
        (_('Candidate Details'), {
            'fields': ('expected_salary', 'notice_period', 'available_from')
        }),
        (_('Status'), {
            'fields': ('status', 'is_read', 'status_changed_at', 'source')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['mark_as_reviewed', 'mark_as_interview', 'mark_as_rejected', 'mark_as_read']
    
    def mark_as_reviewed(self, request, queryset):
        updated = queryset.update(status='reviewed')
        self.message_user(request, _('%(count)d applications marked as reviewed') % {'count': updated})
    mark_as_reviewed.short_description = _('Mark as reviewed')
    
    def mark_as_interview(self, request, queryset):
        updated = queryset.update(status='interview')
        self.message_user(request, _('%(count)d applications marked as interview') % {'count': updated})
    mark_as_interview.short_description = _('Mark as interview')
    
    def mark_as_rejected(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, _('%(count)d applications marked as rejected') % {'count': updated})
    mark_as_rejected.short_description = _('Mark as rejected')
    
    def mark_as_read(self, request, queryset):
        updated = queryset.update(is_read=True)
        self.message_user(request, _('%(count)d applications marked as read') % {'count': updated})
    mark_as_read.short_description = _('Mark as read')

@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ('user', 'job', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'job__title')
    readonly_fields = ('created_at',)

@admin.register(JobAlert)
class JobAlertAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'is_active', 'frequency', 'last_sent', 'created_at')
    list_filter = ('is_active', 'frequency', 'created_at')
    search_fields = ('user__username', 'name', 'keywords')
    readonly_fields = ('created_at', 'updated_at', 'last_sent')
    
    fieldsets = (
        (_('Alert Information'), {
            'fields': ('user', 'name', 'is_active', 'frequency')
        }),
        (_('Search Criteria'), {
            'fields': ('keywords', 'location', 'industry', 'employment_type', 'experience_level')
        }),
        (_('Timestamps'), {
            'fields': ('last_sent', 'created_at', 'updated_at')
        }),
    )
    
    actions = ['activate_alerts', 'deactivate_alerts']
    
    def activate_alerts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('%(count)d alerts activated') % {'count': updated})
    activate_alerts.short_description = _('Activate selected alerts')
    
    def deactivate_alerts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('%(count)d alerts deactivated') % {'count': updated})
    deactivate_alerts.short_description = _('Deactivate selected alerts')

@admin.register(CompanyReview)
class CompanyReviewAdmin(admin.ModelAdmin):
    list_display = ('company', 'author', 'job_title', 'overall_rating', 'employment_status', 'is_verified', 'is_published', 'created_at')
    list_filter = ('overall_rating', 'employment_status', 'is_verified', 'is_published', 'created_at')
    search_fields = ('company__name', 'author__username', 'job_title', 'title')
    list_editable = ('is_verified', 'is_published')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Review Information'), {
            'fields': ('company', 'author', 'job_title', 'employment_status')
        }),
        (_('Ratings'), {
            'fields': ('overall_rating', 'work_life_balance', 'salary_benefits', 'career_growth', 'management')
        }),
        (_('Review Content'), {
            'fields': ('title', 'pros', 'cons', 'advice')
        }),
        (_('Status'), {
            'fields': ('is_anonymous', 'is_verified', 'is_published')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['publish_reviews', 'unpublish_reviews', 'verify_reviews']
    
    def publish_reviews(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, _('%(count)d reviews published') % {'count': updated})
    publish_reviews.short_description = _('Publish selected reviews')
    
    def unpublish_reviews(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, _('%(count)d reviews unpublished') % {'count': updated})
    unpublish_reviews.short_description = _('Unpublish selected reviews')
    
    def verify_reviews(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, _('%(count)d reviews verified') % {'count': updated})
    verify_reviews.short_description = _('Verify selected reviews')

@admin.register(InterviewExperience)
class InterviewExperienceAdmin(admin.ModelAdmin):
    list_display = ('company', 'author', 'job_title', 'difficulty', 'offer_status', 'is_published', 'created_at')
    list_filter = ('difficulty', 'offer_status', 'is_published', 'created_at')
    search_fields = ('company__name', 'author__username', 'job_title')
    list_editable = ('is_published',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        (_('Interview Information'), {
            'fields': ('company', 'author', 'job_title')
        }),
        (_('Process Details'), {
            'fields': ('process_description', 'difficulty', 'duration_days')
        }),
        (_('Interview Content'), {
            'fields': ('interview_questions', 'offer_status', 'recommendations')
        }),
        (_('Status'), {
            'fields': ('is_anonymous', 'is_published')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['publish_experiences', 'unpublish_experiences']
    
    def publish_experiences(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, _('%(count)d interview experiences published') % {'count': updated})
    publish_experiences.short_description = _('Publish selected experiences')
    
    def unpublish_experiences(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, _('%(count)d interview experiences unpublished') % {'count': updated})
    unpublish_experiences.short_description = _('Unpublish selected experiences')