from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView

from .forms import *
from .models import *

# Декоратор для проверки, что пользователь админ или суперадмин
def admin_required(function=None):
    actual_decorator = user_passes_test(
        lambda u: u.is_active and (u.is_staff or u.is_superuser),
        login_url='/accounts/login/',
        redirect_field_name=None
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def event_list(request):
    """Список опубликованных мероприятий - доступно всем"""
    events = Event.objects.filter(status="published").select_related("category")
    
    # Используем форму поиска для фильтрации
    form = EventSearchForm(request.GET or None)
    
    if form.is_valid():
        events = form.get_filtered_queryset(events)
    else:
        # Сортировка по умолчанию
        events = events.order_by('-start_date')
    
    # Пагинация
    paginator = Paginator(events, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "form": form,
        "total_events": events.count(),
    }
    return render(request, "events/event_list.html", context)


class EventCalendarView(ListView):
    """Календарь мероприятий - доступно всем"""
    model = Event
    template_name = "events/event_calendar.html"
    context_object_name = "events"
    
    def get_queryset(self):
        return Event.objects.filter(status="published").select_related("category")


def event_categories(request):
    """Категории мероприятий - доступно всем"""
    categories = EventCategory.objects.all()
    context = {
        "categories": categories,
    }
    return render(request, "events/categories.html", context)


def event_detail(request, slug):
    """Детальная страница мероприятия - доступно всем"""
    event = get_object_or_404(
        Event.objects.select_related("category").prefetch_related(
            "photos"
        ),
        slug=slug, status="published"
    )
    
    # Увеличение счетчика просмотров только один раз за сессию (24 часа)
    session_key = f"event_viewed_{event.id}"
    if not request.session.get(session_key):
        event.views_count += 1
        event.save(update_fields=["views_count"])
        request.session[session_key] = True
        request.session.set_expiry(86400)  # 24 часа в секундах
    
    context = {
        "event": event,
        "is_admin": request.user.is_staff or request.user.is_superuser,
    }
    return render(request, "events/detail.html", context)


@login_required
def create_event(request):
    """Создание мероприятия - только авторизованные пользователи"""
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.status = "published"  # Автоматически публикуем
            event.save()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:event_detail", slug=event.slug)
    else:
        form = EventForm()
    
    context = {
        "form": form,
        "title": _("Create Event"),
    }
    return render(request, "events/create_event.html", context)


@login_required
def edit_event(request, slug):
    """Редактирование мероприятия - только автор или админ"""
    event = get_object_or_404(Event, slug=slug)
    
    # Проверка прав
    if not (request.user == event.organizer or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("You don't have permission to edit this event."))
        return redirect("events:event_detail", slug=slug)
    
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully!"))
            return redirect("events:event_detail", slug=event.slug)
    else:
        form = EventForm(instance=event)
    
    context = {
        "form": form,
        "event": event,
        "title": _("Edit Event"),
    }
    return render(request, "events/edit_event.html", context)


@login_required
def delete_event(request, slug):
    """Удаление мероприятия - только автор или админ"""
    event = get_object_or_404(Event, slug=slug)
    
    # Проверка прав
    if not (request.user == event.organizer or request.user.is_staff or request.user.is_superuser):
        messages.error(request, _("You don't have permission to delete this event."))
        return redirect("events:event_detail", slug=slug)
    
    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully!"))
        return redirect("events:event_list")
    
    context = {
        "event": event,
    }
    return render(request, "events/delete_event.html", context)


@login_required
def my_events(request):
    """Мои мероприятия (организатора) - доступно авторизованным пользователям"""
    events = Event.objects.filter(
        organizer=request.user
    ).select_related("category").order_by("-created_at")
    
    # Пагинация
    paginator = Paginator(events, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "total_events": events.count(),
    }
    return render(request, "events/my_events.html", context)


# ============ АДМИН ФУНКЦИИ ============

@login_required
@admin_required
def admin_event_list(request):
    """Админ: список всех мероприятий"""
    events = Event.objects.all().select_related("category")
    
    # Фильтры
    status_filter = request.GET.get("status")
    category_filter = request.GET.get("category")
    search_query = request.GET.get("search", "")
    
    if status_filter:
        events = events.filter(status=status_filter)
    
    if category_filter:
        events = events.filter(category_id=category_filter)
    
    if search_query:
        events = events.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    # Сортировка
    sort_by = request.GET.get("sort", "-created_at")
    events = events.order_by(sort_by)
    
    # Статистика
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status="published").count()
    draft_events = Event.objects.filter(status="draft").count()
    
    # Пагинация
    paginator = Paginator(events, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        "page_obj": page_obj,
        "categories": EventCategory.objects.all(),
        "search_query": search_query,
        "stats": {
            "total": total_events,
            "published": published_events,
            "draft": draft_events,
        },
    }
    return render(request, "events/admin_event_list.html", context)


@login_required
@admin_required
def admin_event_create(request):
    """Админ: создание мероприятия"""
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            if not event.organizer:
                event.organizer = request.user
            event.save()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:admin_event_edit", pk=event.pk)
    else:
        form = EventForm()
    
    context = {
        "form": form,
        "title": _("Create Event"),
    }
    return render(request, "events/admin/event_form.html", context)


@login_required
@admin_required
def admin_event_edit(request, pk):
    """Админ: редактирование мероприятия"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, _("Event updated successfully!"))
            return redirect("events:admin_event_list")
    else:
        form = EventForm(instance=event)
    
    context = {
        "form": form,
        "event": event,
        "title": _("Edit Event"),
    }
    return render(request, "events/admin_event_form.html", context)


@login_required
@admin_required
def admin_event_delete(request, pk):
    """Админ: удаление мероприятия"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully!"))
        return redirect("events:admin_event_list")
    
    context = {
        "event": event,
    }
    return render(request, "events/admin/event_delete.html", context)


@login_required
@admin_required
def admin_event_publish(request, pk):
    """Админ: публикация мероприятия"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == "POST":
        event.status = "published"
        event.save()
        messages.success(request, _(f'Event "{event.title}" published successfully!'))
    
    return redirect("events:admin_event_list")


@login_required
@admin_required
def admin_event_unpublish(request, pk):
    """Админ: снятие мероприятия с публикации"""
    event = get_object_or_404(Event, pk=pk)
    
    if request.method == "POST":
        event.status = "draft"
        event.save()
        messages.success(request, _(f'Event "{event.title}" unpublished successfully!'))
    
    return redirect("events:admin_event_list")


@login_required
@admin_required
def admin_category_list(request):
    """Админ: список категорий"""
    categories = EventCategory.objects.all()
    
    context = {
        "categories": categories,
    }
    return render(request, "events/admin/category_list.html", context)


@login_required
@admin_required
def admin_category_create(request):
    """Админ: создание категории"""
    if request.method == "POST":
        form = EventCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category created successfully!"))
            return redirect("events:admin_category_list")
    else:
        form = EventCategoryForm()
    
    context = {
        "form": form,
        "title": _("Create Category"),
    }
    return render(request, "events/admin/category_form.html", context)


@login_required
@admin_required
def admin_category_edit(request, pk):
    """Админ: редактирование категории"""
    category = get_object_or_404(EventCategory, pk=pk)
    
    if request.method == "POST":
        form = EventCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _("Category updated successfully!"))
            return redirect("events:admin_category_list")
    else:
        form = EventCategoryForm(instance=category)
    
    context = {
        "form": form,
        "category": category,
        "title": _("Edit Category"),
    }
    return render(request, "events/admin/category_form.html", context)


@login_required
@admin_required
def admin_category_delete(request, pk):
    """Админ: удаление категории"""
    category = get_object_or_404(EventCategory, pk=pk)
    
    if request.method == "POST":
        category.delete()
        messages.success(request, _("Category deleted successfully!"))
        return redirect("events:admin_category_list")
    
    context = {
        "category": category,
    }
    return render(request, "events/admin/category_delete.html", context)


# ============ JSON API ============

def api_events(request):
    """API для получения событий (для календаря)"""
    events = Event.objects.filter(status="published").select_related("category")
    
    # Фильтры
    start = request.GET.get("start")
    end = request.GET.get("end")
    category = request.GET.get("category")
    
    if start and end:
        try:
            start_date = timezone.datetime.fromisoformat(start)
            end_date = timezone.datetime.fromisoformat(end)
            events = events.filter(
                start_date__gte=start_date,
                start_date__lte=end_date
            )
        except ValueError:
            pass
    
    if category:
        events = events.filter(category_id=category)
    
    data = []
    for event in events:
        data.append({
            "id": event.id,
            "title": event.title,
            "start": event.start_date.isoformat(),
            "end": event.end_date.isoformat() if event.end_date else None,
            "url": reverse("events:event_detail", kwargs={"slug": event.slug}),
            "color": event.category.color if event.category else "#667eea",
            "location": event.location,
            "category": event.category.name if event.category else "Other",
        })
    
    return JsonResponse(data, safe=False)


def api_event_stats(request):
    """API для статистики событий"""
    if not (request.user.is_staff or request.user.is_superuser):
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status="published").count()
    draft_events = Event.objects.filter(status="draft").count()
    
    # События по месяцам
    from django.db.models.functions import TruncMonth
    from django.db.models import Count
    
    monthly_stats = (
        Event.objects
        .filter(created_at__year=timezone.now().year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    
    data = {
        "total": total_events,
        "published": published_events,
        "draft": draft_events,
        "monthly_stats": list(monthly_stats),
    }
    
    return JsonResponse(data)