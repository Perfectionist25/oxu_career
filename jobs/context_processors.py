from django.db.models import Q


def jobs_context(request):
    """Контекстный процессор для jobs"""
    from django.db.models import Count


    from accounts.models import Company
    from .models import Job




    return {
        "total_active_jobs": Job.objects.filter(is_active=True).count(),
        "featured_jobs_count": Job.objects.filter(
            is_active=True, is_featured=True
        ).count(),
    "top_companies": Company.objects.filter(is_active=True, is_verified=True)
    .annotate(jobs_count=Count("jobs", filter=Q(jobs__is_active=True)))
    .order_by("-jobs_count")[:6],
        "urgent_jobs_count": Job.objects.filter(is_active=True, is_urgent=True).count(),
    }
