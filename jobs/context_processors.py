from django.utils.translation import gettext_lazy as _
from django.db.models import Q

def jobs_context(request):
    """Контекстный процессор для jobs"""
    from .models import Job, Industry, Company
    from django.db.models import Count
    
    return {
        'total_active_jobs': Job.objects.filter(is_active=True).count(),
        'featured_jobs_count': Job.objects.filter(is_active=True, is_featured=True).count(),
        'top_industries': Industry.objects.annotate(
            job_count=Count('company__jobs', filter=Q(company__jobs__is_active=True))
        ).order_by('-job_count')[:8],
        'top_companies': Company.objects.filter(is_active=True, is_verified=True).annotate(
            job_count=Count('jobs', filter=Q(jobs__is_active=True))
        ).order_by('-job_count')[:6],
        'urgent_jobs_count': Job.objects.filter(is_active=True, is_urgent=True).count(),
    }