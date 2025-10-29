from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mass_mail
from django.db.models import Q
import os
from .models import Resource, StudyPlan

def send_resource_recommendations(user, resources, subject, message):
    """Отправка рекомендаций ресурсов пользователю"""
    email_list = []
    
    for resource in resources:
        personalized_message = message.format(
            resource_title=resource.title,
            resource_type=resource.get_resource_type_display(),
            resource_url=resource.get_absolute_url()
        )
        
        email_list.append((
            subject,
            personalized_message,
            None,  # from_email
            [user.email],
        ))
    
    if email_list:
        return send_mass_mail(email_list, fail_silently=True)
    
    return 0

def get_personalized_recommendations(user, limit=10):
    """Получение персонализированных рекомендаций ресурсов"""
    try:
        from cvbuilder.models import CV
        
        # Получаем навыки пользователя из его резюме
        user_cvs = CV.objects.filter(user=user, status='published')
        user_skills = []
        
        for cv in user_cvs:
            user_skills.extend([skill.name.lower() for skill in cv.skills.all()])
        
        # Уникальные навыки
        user_skills = list(set(user_skills))
        
        if not user_skills:
            # Если нет навыков, возвращаем популярные ресурсы
            return Resource.objects.filter(is_published=True).order_by('-views_count')[:limit]
        
        # Ищем ресурсы с совпадающими тегами и ключевыми словами
        recommended_resources = Resource.objects.filter(is_published=True)
        
        # Создаем Q-объекты для поиска
        skill_queries = Q()
        for skill in user_skills[:10]:  # Ограничиваем количество навыков
            skill_queries |= Q(tags__icontains=skill)
            skill_queries |= Q(keywords__icontains=skill)
            skill_queries |= Q(title__icontains=skill)
            skill_queries |= Q(description__icontains=skill)
        
        recommended_resources = recommended_resources.filter(skill_queries)
        
        # Если недостаточно рекомендаций, добавляем популярные ресурсы
        if recommended_resources.count() < limit:
            additional_resources = Resource.objects.filter(
                is_published=True
            ).exclude(
                pk__in=recommended_resources.values_list('pk', flat=True)
            ).order_by('-views_count')[:limit - recommended_resources.count()]
            
            recommended_resources = list(recommended_resources) + list(additional_resources)
        
        return recommended_resources[:limit]
        
    except Exception:
        # В случае ошибки возвращаем популярные ресурсы
        return Resource.objects.filter(is_published=True).order_by('-views_count')[:limit]

def generate_study_plan_progress(study_plan):
    """Генерация прогресса учебного плана"""
    items = study_plan.studyplanitem_set.all()
    total_items = items.count()
    completed_items = items.filter(completed=True).count()
    
    if total_items == 0:
        return 0
    
    progress = (completed_items / total_items) * 100
    return round(progress, 1)

def get_file_info(file_path):
    """Получение информации о файле"""
    if not file_path or not os.path.exists(file_path):
        return None
    
    file_stats = os.stat(file_path)
    size = file_stats.st_size
    
    # Конвертация размера в читаемый формат
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.1f} MB"

def generate_resource_stats(timeframe='all'):
    """Генерация статистики по ресурсам"""
    from django.utils import timezone
    from datetime import timedelta
    
    now = timezone.now()
    
    if timeframe == 'week':
        start_date = now - timedelta(days=7)
    elif timeframe == 'month':
        start_date = now - timedelta(days=30)
    elif timeframe == 'year':
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = None
    
    resources = Resource.objects.all()
    
    if start_date:
        resources = resources.filter(created_at__gte=start_date)
    
    stats = {
        'total_resources': resources.count(),
        'published_resources': resources.filter(is_published=True).count(),
        'total_views': sum(resource.views_count for resource in resources),
        'total_downloads': sum(resource.downloads_count for resource in resources),
        'total_likes': sum(resource.likes_count for resource in resources),
        'free_resources': resources.filter(is_free=True, is_published=True).count(),
        'featured_resources': resources.filter(is_featured=True, is_published=True).count(),
    }
    
    return stats