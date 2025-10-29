from django.utils.translation import gettext_lazy as _

def employers_context(request):
    """Контекстный процессор для employers"""
    from .models import Company
    
    try:
        total_companies = Company.objects.filter(is_active=True, is_verified=True).count()
        top_companies = Company.objects.filter(is_active=True, is_verified=True)[:8]
    except:
        total_companies = 0
        top_companies = []
    
    return {
        'total_companies': total_companies,
        'top_companies': top_companies,
    }