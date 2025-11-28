from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from .forms import ResourceForm
from .models import Resource, ResourceCategory


try:
    from .services.youtube_service import YouTubeService
except ImportError:
    # Fallback if service file doesn't exist
    class YouTubeService:
        @staticmethod
        def extract_video_id(url):
            """Simple fallback video ID extraction"""
            if not url:
                return None
            patterns = [
                r'(?:youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
                r'(?:youtu\.be\/)([a-zA-Z0-9_-]{11})',
            ]
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            return None

        @staticmethod
        def get_video_info(video_id):
            """Fallback - assume video is embeddable"""
            return {'title': 'YouTube Video'} if video_id else None

        @staticmethod
        def get_embed_url(video_id):
            return f"https://www.youtube.com/embed/{video_id}" if video_id else None

def resource_detail(request, pk):
    """Детальная страница ресурса"""
    resource = get_object_or_404(Resource, pk=pk)
    
    # YouTube video data
    youtube_data = None
    if resource.url_youtube:
        video_id = YouTubeService.extract_video_id(resource.url_youtube)
        if video_id:
            # Проверяем доступность видео через oEmbed API
            try:
                video_info = YouTubeService.get_video_info(video_id)
                youtube_data = {
                    'video_id': video_id,
                    'embed_url': YouTubeService.get_embed_url(video_id),
                    'is_embeddable': video_info is not None,
                    'title': video_info.get('title') if video_info else resource.title,
                }
            except Exception as e:
                # If there's any error with YouTube service, fallback to basic data
                print(f"YouTube service error: {e}")
                youtube_data = {
                    'video_id': video_id,
                    'embed_url': YouTubeService.get_embed_url(video_id),
                    'is_embeddable': False,
                    'title': resource.title,
                }

    # Похожие ресурсы
    similar_resources = Resource.objects.filter(
        is_published=True, 
        category=resource.category
    ).exclude(pk=resource.pk)[:4]

    context = {
        "resource": resource,
        "similar_resources": similar_resources,
        "youtube_data": youtube_data,
    }
    return render(request, "resources/resource_detail.html", context)



def resource_list(request):
    """Список опубликованных ресурсов"""
    resources = Resource.objects.filter(is_published=True).select_related("category")

    # Фильтрация по категории
    category_id = request.GET.get("category")
    if category_id:
        resources = resources.filter(category_id=category_id)

    # Поиск
    query = request.GET.get("q")
    if query:
        resources = resources.filter(
            Q(title__icontains=query)
            | Q(description__icontains=query)
            | Q(category__name__icontains=query)
        )

    # Пагинация
    paginator = Paginator(resources, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": ResourceCategory.objects.all(),
        "total_resources": resources.count(),
    }
    return render(request, "resources/list.html", context)



@login_required
def resource_create(request):
    """Создание нового ресурса"""
    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            # Здесь можно добавить автора, если нужно
            # resource.author = request.user
            resource.save()
            messages.success(request, _("Resource created successfully!"))
            return redirect("resources:list")
    else:
        form = ResourceForm()

    context = {
        "form": form,
        "title": _("Create Resource"),
    }
    return render(request, "resources/resource_form.html", context)


@login_required
def resource_edit(request, pk):
    """Редактирование ресурса"""
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == "POST":
        form = ResourceForm(request.POST, request.FILES, instance=resource)
        if form.is_valid():
            form.save()
            messages.success(request, _("Resource updated successfully!"))
            return redirect("resources:resource_detail", pk=resource.pk)
    else:
        form = ResourceForm(instance=resource)

    context = {
        "form": form,
        "resource": resource,
        "title": _("Edit Resource"),
    }
    return render(request, "resources/resource_form.html", context)


@login_required
def resource_delete(request, pk):
    """Удаление ресурса"""
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == "POST":
        resource_title = resource.title
        resource.delete()
        messages.success(
            request, _(f'Resource "{resource_title}" deleted successfully!')
        )
        return redirect("resources:list")

    context = {
        "resource": resource,
    }
    return render(request, "resources/resource_confirm_delete.html", context)


@login_required
def unpublished_resources(request):
    """Список неопубликованных ресурсов для редакции"""
    resources = Resource.objects.filter(is_published=False).select_related("category")

    # Пагинация
    paginator = Paginator(resources, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_resources": resources.count(),
    }
    return render(request, "resources/unpublished_resources.html", context)


@login_required
def publish_resource(request, pk):
    """Публикация ресурса"""
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == "POST":
        resource.is_published = True
        resource.save()
        messages.success(
            request, _(f'Resource "{resource.title}" published successfully!')
        )

    return redirect("resources:unpublished_resources")


@login_required
def unpublish_resource(request, pk):
    """Снятие ресурса с публикации"""
    resource = get_object_or_404(Resource, pk=pk)

    if request.method == "POST":
        resource.is_published = False
        resource.save()
        messages.success(
            request, _(f'Resource "{resource.title}" unpublished successfully!')
        )

    return redirect("resources:list")




@login_required
@require_POST
def bulk_publish_resources(request):
    """Массовая публикация ресурсов"""
    resource_ids = request.POST.get('resource_ids', '').split(',')
    
    if not resource_ids or resource_ids == ['']:
        messages.error(request, _("No resources selected for publishing."))
        return redirect("resources:unpublished_resources")
    
    # Фильтруем только существующие и неопубликованные ресурсы
    resources = Resource.objects.filter(
        pk__in=resource_ids,
        is_published=False
    )
    
    published_count = resources.update(is_published=True)
    
    if published_count > 0:
        messages.success(
            request, 
            _(f"Successfully published {published_count} resources!")
        )
    else:
        messages.warning(
            request, 
            _("No resources were published. They might already be published or not exist.")
        )
    
    return redirect("resources:unpublished_resources")

@login_required
@require_POST
def bulk_delete_resources(request):
    """Массовое удаление ресурсов"""
    resource_ids = request.POST.get('resource_ids', '').split(',')
    
    if not resource_ids or resource_ids == ['']:
        messages.error(request, _("No resources selected for deletion."))
        return redirect("resources:unpublished_resources")
    
    # Получаем ресурсы для удаления
    resources = Resource.objects.filter(pk__in=resource_ids)
    deleted_count = resources.count()
    
    # Получаем названия перед удалением для сообщения
    resource_titles = list(resources.values_list('title', flat=True))
    
    # Удаляем ресурсы
    deleted_count = resources.delete()[0]
    
    if deleted_count > 0:
        messages.success(
            request, 
            _(f"Successfully deleted {deleted_count} resources!")
        )
    else:
        messages.warning(
            request, 
            _("No resources were deleted. They might not exist.")
        )
    
    return redirect("resources:unpublished_resources")

@login_required
@require_POST
def bulk_archive_resources(request):
    """Массовое архивирование ресурсов (опционально)"""
    resource_ids = request.POST.get('resource_ids', '').split(',')
    
    if not resource_ids or resource_ids == ['']:
        messages.error(request, _("No resources selected for archiving."))
        return redirect("resources:unpublished_resources")
    
    resources = Resource.objects.filter(pk__in=resource_ids)
    archived_count = resources.update(is_archived=True)
    
    if archived_count > 0:
        messages.success(
            request, 
            _(f"Successfully archived {archived_count} resources!")
        )
    else:
        messages.warning(
            request, 
            _("No resources were archived.")
        )
    
    return redirect("resources:unpublished_resources")

# Дополнительная view для AJAX массовых операций (опционально)
@login_required
@require_POST
def bulk_action_api(request):
    """API для массовых операций (возвращает JSON)"""
    action = request.POST.get('action')
    resource_ids = request.POST.get('resource_ids', '').split(',')
    
    if not resource_ids or resource_ids == ['']:
        return JsonResponse({
            'success': False,
            'message': _('No resources selected.')
        })
    
    resources = Resource.objects.filter(pk__in=resource_ids)
    
    if action == 'publish':
        updated_count = resources.update(is_published=True)
        message = _(f'Published {updated_count} resources')
    elif action == 'unpublish':
        updated_count = resources.update(is_published=False)
        message = _(f'Unpublished {updated_count} resources')
    elif action == 'delete':
        deleted_count = resources.count()
        resources.delete()
        message = _(f'Deleted {deleted_count} resources')
    else:
        return JsonResponse({
            'success': False,
            'message': _('Invalid action.')
        })
    
    return JsonResponse({
        'success': True,
        'message': message,
        'count': updated_count if action != 'delete' else deleted_count
    })

# Дополнительная view для получения статистики (опционально)
@login_required
def unpublished_resources_stats(request):
    """Статистика для неопубликованных ресурсов"""
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    
    stats = {
        'total_unpublished': Resource.objects.filter(is_published=False).count(),
        'added_today': Resource.objects.filter(
            is_published=False,
            created_at__date=today
        ).count(),
        'added_this_week': Resource.objects.filter(
            is_published=False,
            created_at__date__gte=today - timedelta(days=7)
        ).count(),
        'categories_count': Resource.objects.filter(
            is_published=False
        ).values('category').distinct().count(),
    }
    
    return JsonResponse(stats)



@login_required
def unpublished_resources(request):
    """Список неопубликованных ресурсов для редакции"""
    from django.utils import timezone
    from datetime import timedelta
    
    resources = Resource.objects.filter(is_published=False).select_related("category")
    
    # Получаем статистику
    today = timezone.now().date()
    stats = {
        'total_resources': resources.count(),
        'today_count': resources.filter(created_at__date=today).count(),
        'categories_count': resources.values('category').distinct().count(),
    }

    # Пагинация - используем 12 элементов (4 ряда по 3)
    paginator = Paginator(resources, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        **stats,
    }
    return render(request, "resources/unpublished_resources.html", context)