from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import ResourceCategory, Resource

@admin.register(ResourceCategory)
class ResourceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'resource_count')  # Убрали 'created_at'
    list_filter = ()  # Убрали 'created_at'
    search_fields = ('name', 'description')
    # Убрали readonly_fields = ('created_at',)
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('name', 'description')
        }),
        # Убрали секцию с временными метками
    )
    
    def resource_count(self, obj):
        return obj.resources.count()
    resource_count.short_description = _('Resources Count')


@admin.register(Resource)
class ResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'is_published', 'has_youtube')  # Убрали 'created_at', 'updated_at'
    list_filter = ('category', 'is_published')  # Убрали 'created_at'
    search_fields = ('title', 'description', 'category__name')
    list_editable = ('is_published',)
    # Убрали readonly_fields = ('created_at', 'updated_at')
    list_per_page = 20
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('title', 'category', 'description')
        }),
        (_('Media Content'), {
            'fields': ('image', 'url_youtube')
        }),
        (_('Publication Status'), {
            'fields': ('is_published',)
        }),
        # Убрали секцию с временными метками
    )
    
    def has_youtube(self, obj):
        return bool(obj.url_youtube)
    has_youtube.boolean = True
    has_youtube.short_description = _('YouTube')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')
    
    actions = ['publish_resources', 'unpublish_resources', 'duplicate_resources']
    
    def publish_resources(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, _('%(count)d resources published successfully') % {'count': updated})
    publish_resources.short_description = _('Publish selected resources')
    
    def unpublish_resources(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, _('%(count)d resources unpublished successfully') % {'count': updated})
    unpublish_resources.short_description = _('Unpublish selected resources')
    
    def duplicate_resources(self, request, queryset):
        for resource in queryset:
            resource.pk = None
            resource.title = f"{resource.title} (Copy)"
            resource.is_published = False
            resource.save()
        self.message_user(request, _('%(count)d resources duplicated successfully') % {'count': queryset.count()})
    duplicate_resources.short_description = _('Duplicate selected resources')