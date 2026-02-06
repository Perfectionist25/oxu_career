

def employers_context(request):
    """Контекстный процессор для employers"""
    from .models import Company

    try:
        total_companies = Company.objects.filter(
            is_active=True, is_verified=True
        ).count()
        top_companies = Company.objects.filter(is_active=True, is_verified=True)[:8]
    except Exception:
        total_companies = 0
        top_companies = Company.objects.none()

    return {
        "total_companies": total_companies,
        "top_companies": top_companies,
    }
