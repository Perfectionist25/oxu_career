from django.db.models import Q


def jobs_context(request):
    """Контекстный процессор для jobs"""
    from django.db.models import Count

    # Company lives in the employers app; import it from there.
    from employers.models import Company
    from .models import Industry, Job

    # Jobs/companies exist in different apps in this project. We avoid
    # attempting to annotate Industry from Company (there's no FK linking
    # them here) and instead return a simple industries list.
    return {
        "total_active_jobs": Job.objects.filter(is_active=True).count(),
        "featured_jobs_count": Job.objects.filter(
            is_active=True, is_featured=True
        ).count(),
        "top_industries": Industry.objects.all().order_by("name")[:8],
    "top_companies": Company.objects.filter(is_active=True, is_verified=True)
    .annotate(jobs_count=Count("jobs", filter=Q(jobs__is_active=True)))
    .order_by("-jobs_count")[:6],
        "urgent_jobs_count": Job.objects.filter(is_active=True, is_urgent=True).count(),
    }
