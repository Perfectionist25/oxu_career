from django.utils.translation import gettext_lazy as _

def events_context(request):
    """Контекстный процессор для events"""
    from .models import Event, EventCategory
    from django.utils import timezone
    
    return {
        'upcoming_events_count': Event.objects.filter(
            status='published', 
            start_date__gt=timezone.now()
        ).count(),
        'event_categories': EventCategory.objects.all()[:8],
        'featured_events': Event.objects.filter(
            status='published', 
            is_featured=True,
            start_date__gt=timezone.now()
        )[:3],
    }