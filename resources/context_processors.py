from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q

def resources_context(request):
    """Контекстный процессор для resources"""
    from .models import Resource, ResourceCategory, CareerPath
    
    try:
        total_resources = Resource.objects.filter(is_published=True).count()
        featured_resources_count = Resource.objects.filter(is_published=True, is_featured=True).count()
        resource_categories = ResourceCategory.objects.annotate(
            resource_count=Count('resources', filter=Q(resources__is_published=True))
        ).order_by('order', 'name')[:10]
        career_paths_count = CareerPath.objects.filter(is_active=True).count()
        popular_resources = Resource.objects.filter(is_published=True).order_by('-views_count')[:5]
    except:
        total_resources = 0
        featured_resources_count = 0
        resource_categories = []
        career_paths_count = 0
        popular_resources = []
    
    return {
        'total_resources': total_resources,
        'featured_resources_count': featured_resources_count,
        'resource_categories': resource_categories,
        'career_paths_count': career_paths_count,
        'popular_resources': popular_resources,
    }