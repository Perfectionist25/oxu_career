from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _

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
        return redirect("resources:resource_list")

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
