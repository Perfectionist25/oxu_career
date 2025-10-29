from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.generic import ListView, DetailView
from django.utils import timezone
import os
from .models import (
    Resource, ResourceCategory, ResourceReview, ResourceDownload, ResourceLike,
    StudyPlan, StudyPlanItem, CareerPath, LearningTrack
)
from .forms import (
    ResourceForm, ResourceReviewForm, StudyPlanForm, CareerPathForm,
    LearningTrackForm, ResourceSearchForm, StudyPlanItemForm
)

# def index(request):
#     """Главная страница ресурсов"""
#     context = {
#         'page_title': _('Resurslar'),
#         'description': _('OXU bitiruvchilari uchun foydali resurslar va materiallar'),
#     }
#     return render(request, 'resources/list.html', context)


def resource_list(request):
    """Список ресурсов"""
    form = ResourceSearchForm(request.GET or None)
    resources = Resource.objects.filter(is_published=True)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        resource_type = form.cleaned_data.get('resource_type')
        level = form.cleaned_data.get('level')
        language = form.cleaned_data.get('language')
        free_only = form.cleaned_data.get('free_only')
        featured_only = form.cleaned_data.get('featured_only')
        
        if query:
            resources = resources.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(content__icontains=query) |
                Q(tags__icontains=query) |
                Q(keywords__icontains=query)
            )
        
        if category:
            resources = resources.filter(category=category)
        
        if resource_type:
            resources = resources.filter(resource_type=resource_type)
        
        if level:
            resources = resources.filter(level=level)
        
        if language:
            resources = resources.filter(language=language)
        
        if free_only:
            resources = resources.filter(is_free=True)
        
        if featured_only:
            resources = resources.filter(is_featured=True)
    
    # Сортировка
    sort = request.GET.get('sort', 'newest')
    if sort == 'popular':
        resources = resources.order_by('-views_count', '-likes_count')
    elif sort == 'rating':
        resources = resources.annotate(avg_rating=Avg('reviews__rating')).order_by('-avg_rating')
    elif sort == 'featured':
        resources = resources.order_by('-is_featured', '-created_at')
    else:  # newest
        resources = resources.order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'total_resources': resources.count(),
        'categories': ResourceCategory.objects.all(),
        'featured_resources': resources.filter(is_featured=True)[:5],
    }
    return render(request, 'resources/list.html', context)

def resource_detail(request, slug):
    """Детальная страница ресурса"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    # Увеличиваем счетчик просмотров
    resource.views_count += 1
    resource.save()
    
    # Проверяем, лайкнул ли пользователь ресурс
    is_liked = False
    if request.user.is_authenticated:
        is_liked = ResourceLike.objects.filter(resource=resource, user=request.user).exists()
    
    # Проверяем, скачивал ли пользователь ресурс
    has_downloaded = False
    if request.user.is_authenticated:
        has_downloaded = ResourceDownload.objects.filter(resource=resource, user=request.user).exists()
    
    # Формы
    review_form = ResourceReviewForm()
    
    # Отзывы
    reviews = resource.reviews.filter(is_approved=True)
    
    # Средний рейтинг
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg'] or 0
    
    # Похожие ресурсы
    similar_resources = Resource.objects.filter(
        is_published=True,
        category=resource.category,
        level=resource.level
    ).exclude(pk=resource.pk)[:4]
    
    context = {
        'resource': resource,
        'is_liked': is_liked,
        'has_downloaded': has_downloaded,
        'review_form': review_form,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
        'similar_resources': similar_resources,
    }
    return render(request, 'resources/resource_detail.html', context)

@login_required
def download_resource(request, slug):
    """Скачивание ресурса"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    if not resource.is_downloadable():
        messages.error(request, _('This resource is not available for download.'))
        return redirect('resources:resource_detail', slug=resource.slug)
    
    if resource.requires_login and not request.user.is_authenticated:
        messages.error(request, _('You need to login to download this resource.'))
        return redirect('accounts:login')
    
    # Записываем факт скачивания
    if request.user.is_authenticated:
        download, created = ResourceDownload.objects.get_or_create(
            resource=resource,
            user=request.user
        )
        if created:
            resource.downloads_count += 1
            resource.save()
    
    # Отдаем файл для скачивания
    response = HttpResponse(resource.file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(resource.file.name)}"'
    return response

@login_required
def like_resource(request, slug):
    """Лайк ресурса"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    if request.method == 'POST':
        like, created = ResourceLike.objects.get_or_create(
            resource=resource,
            user=request.user
        )
        
        if created:
            resource.likes_count += 1
            resource.save()
            messages.success(request, _('Resource liked!'))
        else:
            like.delete()
            resource.likes_count -= 1
            resource.save()
            messages.info(request, _('Resource unliked.'))
    
    return redirect('resources:resource_detail', slug=resource.slug)

@login_required
def add_review(request, slug):
    """Добавление отзыва о ресурсе"""
    resource = get_object_or_404(Resource, slug=slug, is_published=True)
    
    # Проверяем, не оставлял ли пользователь уже отзыв
    if ResourceReview.objects.filter(resource=resource, user=request.user).exists():
        messages.warning(request, _('You have already reviewed this resource.'))
        return redirect('resources:resource_detail', slug=resource.slug)
    
    if request.method == 'POST':
        form = ResourceReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.resource = resource
            review.user = request.user
            review.save()
            
            messages.success(request, _('Thank you for your review!'))
            return redirect('resources:resource_detail', slug=resource.slug)
    else:
        form = ResourceReviewForm()
    
    context = {
        'resource': resource,
        'form': form,
    }
    return render(request, 'resources/add_review.html', context)

@login_required
def study_plans(request):
    """Список учебных планов пользователя"""
    study_plans = StudyPlan.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = StudyPlanForm(request.POST)
        if form.is_valid():
            study_plan = form.save(commit=False)
            study_plan.user = request.user
            study_plan.save()
            
            messages.success(request, _('Study plan created successfully!'))
            return redirect('resources:study_plan_detail', pk=study_plan.pk)
    else:
        form = StudyPlanForm()
    
    context = {
        'study_plans': study_plans,
        'form': form,
    }
    return render(request, 'resources/study_plans.html', context)

@login_required
def study_plan_detail(request, pk):
    """Детальная страница учебного плана"""
    study_plan = get_object_or_404(StudyPlan, pk=pk, user=request.user)
    items = study_plan.studyplanitem_set.select_related('resource').order_by('order')
    
    if request.method == 'POST':
        form = StudyPlanItemForm(request.POST)
        if form.is_valid():
            resource = form.cleaned_data['resource']
            order = form.cleaned_data['order']
            notes = form.cleaned_data['notes']
            
            # Проверяем, не добавлен ли уже ресурс
            if StudyPlanItem.objects.filter(study_plan=study_plan, resource=resource).exists():
                messages.warning(request, _('This resource is already in your study plan.'))
            else:
                StudyPlanItem.objects.create(
                    study_plan=study_plan,
                    resource=resource,
                    order=order,
                    notes=notes
                )
                messages.success(request, _('Resource added to study plan!'))
            
            return redirect('resources:study_plan_detail', pk=study_plan.pk)
    else:
        form = StudyPlanItemForm()
    
    # Прогресс выполнения
    total_items = items.count()
    completed_items = items.filter(completed=True).count()
    progress = round((completed_items / total_items * 100), 1) if total_items > 0 else 0
    
    context = {
        'study_plan': study_plan,
        'items': items,
        'form': form,
        'progress': progress,
        'completed_items': completed_items,
        'total_items': total_items,
    }
    return render(request, 'resources/study_plan_detail.html', context)

@login_required
def mark_item_completed(request, item_id):
    """Отметка элемента учебного плана как выполненного"""
    item = get_object_or_404(StudyPlanItem, pk=item_id, study_plan__user=request.user)
    
    if request.method == 'POST':
        item.completed = not item.completed
        if item.completed:
            item.completed_at = timezone.now()
        else:
            item.completed_at = None
        item.save()
        
        return JsonResponse({
            'success': True,
            'completed': item.completed,
            'completed_at': item.completed_at.strftime('%Y-%m-%d') if item.completed_at else None
        })
    
    return JsonResponse({'success': False})

def career_paths(request):
    """Список карьерных путей"""
    career_paths = CareerPath.objects.filter(is_active=True)
    
    context = {
        'career_paths': career_paths,
    }
    return render(request, 'resources/career_paths.html', context)

def career_path_detail(request, pk):
    """Детальная страница карьерного пути"""
    career_path = get_object_or_404(CareerPath, pk=pk, is_active=True)
    learning_tracks = career_path.learning_tracks.filter(is_active=True)
    
    context = {
        'career_path': career_path,
        'learning_tracks': learning_tracks,
    }
    return render(request, 'resources/career_path_detail.html', context)

def learning_track_detail(request, pk):
    """Детальная страница обучающего трека"""
    learning_track = get_object_or_404(LearningTrack, pk=pk, is_active=True)
    track_resources = learning_track.trackresource_set.select_related('resource').order_by('order')
    
    context = {
        'learning_track': learning_track,
        'track_resources': track_resources,
    }
    return render(request, 'resources/learning_track_detail.html', context)

def categories(request):
    """Список категорий ресурсов"""
    categories = ResourceCategory.objects.annotate(
        resource_count=Count('resources', filter=Q(resources__is_published=True))
    ).order_by('order', 'name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'resources/categories.html', context)

def category_detail(request, pk):
    """Ресурсы по категории"""
    category = get_object_or_404(ResourceCategory, pk=pk)
    resources = category.resources.filter(is_published=True).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(resources, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'total_resources': resources.count(),
    }
    return render(request, 'resources/category_detail.html', context)

# AJAX views
@login_required
def get_resource_suggestions(request):
    """Получение предложений ресурсов для учебного плана"""
    query = request.GET.get('q', '')
    
    if query:
        resources = Resource.objects.filter(
            is_published=True,
            title__icontains=query
        )[:10]
    else:
        resources = Resource.objects.filter(is_published=True)[:10]
    
    suggestions = [{
        'id': resource.id,
        'title': resource.title,
        'resource_type': resource.get_resource_type_display(),
        'level': resource.get_level_display(),
    } for resource in resources]
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def remove_from_study_plan(request, item_id):
    """Удаление ресурса из учебного плана"""
    item = get_object_or_404(StudyPlanItem, pk=item_id, study_plan__user=request.user)
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, _('Resource removed from study plan.'))
        return redirect('resources:study_plan_detail', pk=item.study_plan.pk)
    
    return redirect('resources:study_plans')