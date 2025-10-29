from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import (
    ResourceCategory, Resource, ResourceReview, ResourceDownload, 
    ResourceLike, StudyPlan, StudyPlanItem, CareerPath, LearningTrack, TrackResource
)

class ResourceReviewInline(admin.TabularInline):
    model = ResourceReview
    extra = 0
    fields = ('user', 'rating', 'comment', 'is_approved')
    readonly_fields = ('created_at',)

class ResourceDownloadInline(admin.TabularInline):
    model = ResourceDownload
    extra = 0
    fields = ('user', 'downloaded_at')
    readonly_fields = ('downloaded_at',)

class ResourceLikeInline(admin.TabularInline):
    model = ResourceLike
    extra = 0
    fields = ('user', 'created_at')
    readonly_fields = ('created_at',)

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_count', 'order', 'color_display')
    list_filter = ('name',)
    search_fields = ('name', 'description')
    list_editable = ('order',)
    
    def resource_count(self, obj):
        return obj.resources.filter(is_published=True).count()
    resource_count.short_description = _('Resources')
    
    def color_display(self, obj):
        return format_html(
            '<div style="width: 20px; height: 20px; background-color: {}; border-radius: 3px;"></div>',
            obj.color
        )
    color_display.short_description = _('Color')

@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'resource_type', 'level', 'language', 'is_published', 'is_featured', 'views_count', 'created_at')
    list_filter = ('resource_type', 'category', 'level', 'language', 'is_published', 'is_featured', 'is_free', 'created_at')
    search_fields = ('title', 'description', 'content', 'tags', 'author')
    list_editable = ('is_published', 'is_featured')
    readonly_fields = ('views_count', 'downloads_count', 'likes_count', 'created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ResourceReviewInline, ResourceDownloadInline, ResourceLikeInline]
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'slug', 'short_description', 'description', 'category', 'resource_type')
        }),
        (_('Content'), {
            'fields': ('content', 'external_url', 'file', 'thumbnail')
        }),
        (_('Metadata'), {
            'fields': ('author', 'publisher', 'language', 'level', 'duration')
        }),
        (_('SEO & Organization'), {
            'fields': ('tags', 'keywords', 'meta_description')
        }),
        (_('Access & Status'), {
            'fields': ('is_published', 'is_featured', 'is_free', 'requires_login')
        }),
        (_('Statistics'), {
            'fields': ('views_count', 'downloads_count', 'likes_count')
        }),
        (_('Owner'), {
            'fields': ('created_by',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    actions = ['publish_resources', 'unpublish_resources', 'mark_as_featured']
    
    def publish_resources(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, _('%(count)d resources published') % {'count': updated})
    publish_resources.short_description = _('Publish selected resources')
    
    def unpublish_resources(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, _('%(count)d resources unpublished') % {'count': updated})
    unpublish_resources.short_description = _('Unpublish selected resources')
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, _('%(count)d resources marked as featured') % {'count': updated})
    mark_as_featured.short_description = _('Mark as featured')

@admin.register(ResourceReview)
class ResourceReviewAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'rating', 'short_comment', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('resource__title', 'user__username', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')
    
    def short_comment(self, obj):
        if len(obj.comment) > 50:
            return f"{obj.comment[:50]}..."
        return obj.comment
    short_comment.short_description = _('Comment')
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, _('%(count)d reviews approved') % {'count': updated})
    approve_reviews.short_description = _('Approve selected reviews')
    
    def disapprove_reviews(self, request, queryset):
        updated = queryset.update(is_approved=False)
        self.message_user(request, _('%(count)d reviews disapproved') % {'count': updated})
    disapprove_reviews.short_description = _('Disapprove selected reviews')

@admin.register(ResourceDownload)
class ResourceDownloadAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'downloaded_at')
    list_filter = ('downloaded_at',)
    search_fields = ('resource__title', 'user__username')
    readonly_fields = ('downloaded_at',)

@admin.register(ResourceLike)
class ResourceLikeAdmin(admin.ModelAdmin):
    list_display = ('resource', 'user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('resource__title', 'user__username')
    readonly_fields = ('created_at',)

class StudyPlanItemInline(admin.TabularInline):
    model = StudyPlanItem
    extra = 0
    fields = ('resource', 'order', 'completed', 'completed_at')
    readonly_fields = ('completed_at',)

@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'is_public', 'resource_count', 'created_at')
    list_filter = ('is_public', 'created_at')
    search_fields = ('name', 'user__username', 'description')
    inlines = [StudyPlanItemInline]
    readonly_fields = ('created_at', 'updated_at')
    
    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = _('Resources')

@admin.register(StudyPlanItem)
class StudyPlanItemAdmin(admin.ModelAdmin):
    list_display = ('study_plan', 'resource', 'order', 'completed', 'completed_at')
    list_filter = ('completed', 'completed_at')
    search_fields = ('study_plan__name', 'resource__title')
    readonly_fields = ('completed_at',)

@admin.register(CareerPath)
class CareerPathAdmin(admin.ModelAdmin):
    list_display = ('name', 'industry', 'resource_count', 'is_active', 'created_at')
    list_filter = ('industry', 'is_active', 'created_at')
    search_fields = ('name', 'industry', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = _('Resources')

class TrackResourceInline(admin.TabularInline):
    model = TrackResource
    extra = 0
    fields = ('resource', 'order', 'is_required')

@admin.register(LearningTrack)
class LearningTrackAdmin(admin.ModelAdmin):
    list_display = ('name', 'career_path', 'level', 'resource_count', 'is_active', 'created_at')
    list_filter = ('career_path', 'level', 'is_active', 'created_at')
    search_fields = ('name', 'career_path__name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    inlines = [TrackResourceInline]
    
    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = _('Resources')

@admin.register(TrackResource)
class TrackResourceAdmin(admin.ModelAdmin):
    list_display = ('track', 'resource', 'order', 'is_required')
    list_filter = ('track', 'is_required')
    search_fields = ('track__name', 'resource__title')
    list_editable = ('order', 'is_required')