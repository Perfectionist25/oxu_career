

def events_context(request):
    """Контекстный процессор для events"""
    from django.utils import timezone

    from .models import Event, EventCategory

    return {
        "upcoming_events_count": Event.objects.filter(
            status="published", start_date__gt=timezone.now()
        ).count(),
        "event_categories": EventCategory.objects.all()[:8],
        "featured_events": Event.objects.filter(
            status="published", is_featured=True, start_date__gt=timezone.now()
        )[:3],
    }
