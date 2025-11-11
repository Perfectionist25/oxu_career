from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView
from .forms import *
from .models import *

@login_required
def unpublished_events(request):
    """Список неопубликованных мероприятий для редакции"""
    events = Event.objects.filter(status="draft").select_related("category", "organizer")

    # Пагинация
    paginator = Paginator(events, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "total_events": events.count(),
    }
    return render(request, "events/unpublished_events.html", context)


@login_required
def publish_event(request, pk):
    """Публикация мероприятия"""
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.status = "published"
        event.save()
        messages.success(
            request, _(f'Event "{event.title}" published successfully!')
        )

    return redirect("events:unpublished_events")


@login_required
def unpublish_event(request, pk):
    """Снятие мероприятия с публикации"""
    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.status = "draft"
        event.save()
        messages.success(
            request, _(f'Event "{event.title}" unpublished successfully!')
        )

    return redirect("events:event_list")


def event_list(request):
    """Список мероприятий"""
    events = Event.objects.filter(status="published").select_related("category", "organizer")

    # Фильтры
    category = request.GET.get("category")
    event_type = request.GET.get("type")
    search = request.GET.get("search")

    if category:
        events = events.filter(category__slug=category)
    if event_type:
        events = events.filter(event_type=event_type)
    if search:
        events = events.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(short_description__icontains=search)
        )

    # Сортировка
    sort = request.GET.get("sort", "start_date")
    if sort == "start_date":
        events = events.order_by("start_date")
    elif sort == "title":
        events = events.order_by("title")
    elif sort == "category":
        events = events.order_by("category__name")

    # Пагинация
    paginator = Paginator(events, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": EventCategory.objects.all(),
        "event_types": Event.EVENT_TYPE_CHOICES,
        "total_events": events.count(),
    }
    return render(request, "events/list.html", context)


class EventCalendarView(ListView):
    """Календарь мероприятий"""
    model = Event
    template_name = "events/calendar.html"
    context_object_name = "events"

    def get_queryset(self):
        return Event.objects.filter(status="published").select_related("category", "organizer")


def event_categories(request):
    """Категории мероприятий"""
    categories = EventCategory.objects.all()
    context = {
        "categories": categories,
    }
    return render(request, "events/categories.html", context)


def event_detail(request, slug):
    """Детальная страница мероприятия"""
    event = get_object_or_404(
        Event.objects.select_related("category", "organizer").prefetch_related(
            "speakers", "sessions", "photos", "comments__user", "ratings"
        ),
        slug=slug, status="published"
    )

    # Увеличение счетчика просмотров
    event.views_count += 1
    event.save(update_fields=["views_count"])

    # Проверка регистрации пользователя
    user_registration = None
    if request.user.is_authenticated:
        user_registration = EventRegistration.objects.filter(
            event=event, user=request.user
        ).first()

    # Средний рейтинг
    avg_rating = event.ratings.aggregate(models.Avg("rating"))["rating__avg"] or 0

    # Количество зарегистрированных участников
    registered_count = event.registrations.filter(status='registered').count()

    # Зарегистрированные участники для списка
    registered_registrations = event.registrations.filter(status='registered')[:10]

    context = {
        "event": event,
        "user_registration": user_registration,
        "avg_rating": round(avg_rating, 1),
        "total_ratings": event.ratings.count(),
        "registered_count": registered_count,
        "registered_registrations": registered_registrations,
        "is_admin": request.user.is_staff,
    }
    return render(request, "events/detail.html", context)


@login_required
def register_for_event(request, slug):
    """Регистрация на мероприятие"""
    event = get_object_or_404(Event, slug=slug, status="published")

    if not event.is_registration_open():
        messages.error(request, _("Registration is closed for this event."))
        return redirect("events:event_detail", slug=slug)

    if event.registration_full():
        if event.waitlist_enabled:
            # Добавление в лист ожидания
            registration, created = EventRegistration.objects.get_or_create(
                event=event, user=request.user,
                defaults={"status": "waiting"}
            )
            if created:
                messages.success(request, _("You have been added to the waiting list."))
            else:
                messages.info(request, _("You are already on the waiting list."))
        else:
            messages.error(request, _("Event is full."))
    else:
        # Регистрация
        registration, created = EventRegistration.objects.get_or_create(
            event=event, user=request.user,
            defaults={"status": "registered"}
        )
        if created:
            event.registration_count += 1
            event.save(update_fields=["registration_count"])
            messages.success(request, _("Successfully registered for the event!"))
        else:
            messages.info(request, _("You are already registered for this event."))

    return redirect("events:event_detail", slug=slug)


@login_required
def cancel_registration(request, slug):
    """Отмена регистрации на мероприятие"""
    event = get_object_or_404(Event, slug=slug)
    registration = get_object_or_404(EventRegistration, event=event, user=request.user)

    if request.method == "POST":
        registration.status = "cancelled"
        registration.save()

        if registration.status == "registered":
            event.registration_count -= 1
            event.save(update_fields=["registration_count"])

        messages.success(request, _("Registration cancelled successfully."))

    return redirect("events:event_detail", slug=slug)


@login_required
def my_events(request):
    """Мои мероприятия"""
    registrations = EventRegistration.objects.filter(
        user=request.user
    ).select_related("event__category", "event__organizer").order_by("-registration_date")

    # Фильтры по статусу
    status_filter = request.GET.get("status")
    if status_filter:
        registrations = registrations.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(registrations, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "registration_statuses": EventRegistration.STATUS_CHOICES,
    }
    return render(request, "events/my_events.html", context)


@login_required
def create_event(request):
    """Создание мероприятия"""
    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.save()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:manage_events")
    else:
        form = EventForm()

    context = {
        "form": form,
    }
    return render(request, "events/create_event.html", context)


@login_required
def manage_events(request):
    """Управление моими мероприятиями"""
    events = Event.objects.filter(organizer=request.user).select_related("category")

    # Фильтры
    status_filter = request.GET.get("status")
    if status_filter:
        events = events.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(events, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "event_statuses": Event.EVENT_STATUS_CHOICES,
    }
    return render(request, "events/manage_events.html", context)


@login_required
def event_registrations(request, slug):
    """Список регистраций на мероприятие"""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    registrations = event.registrations.select_related("user").order_by("-registration_date")

    # Фильтры
    status_filter = request.GET.get("status")
    if status_filter:
        registrations = registrations.filter(status=status_filter)

    # Пагинация
    paginator = Paginator(registrations, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "event": event,
        "page_obj": page_obj,
        "registration_statuses": EventRegistration.STATUS_CHOICES,
    }
    return render(request, "events/event_registrations.html", context)


@login_required
def admin_event_list(request):
    """Админ: список всех мероприятий"""
    if not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    events = Event.objects.all().select_related("category", "organizer")

    # Фильтры
    status_filter = request.GET.get("status")
    organizer_filter = request.GET.get("organizer")
    search = request.GET.get("search")

    if status_filter:
        events = events.filter(status=status_filter)
    if organizer_filter:
        events = events.filter(organizer__username=organizer_filter)
    if search:
        events = events.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )

    # Статистика
    total_events = Event.objects.count()
    published_events = Event.objects.filter(status="published").count()
    draft_events = Event.objects.filter(status="draft").count()
    cancelled_events = Event.objects.filter(status="cancelled").count()
    completed_events = Event.objects.filter(status="completed").count()

    # Пагинация
    paginator = Paginator(events, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "event_statuses": Event.EVENT_STATUS_CHOICES,
        "status_choices": Event.EVENT_STATUS_CHOICES,
        "categories": EventCategory.objects.all(),
        "organizers": Event.objects.values_list("organizer__username", flat=True).distinct(),
        "stats": {
            "total": total_events,
            "published": published_events,
            "draft": draft_events,
            "cancelled": cancelled_events,
            "completed": completed_events,
        },
    }
    return render(request, "events/admin_event_list.html", context)


@login_required
def admin_event_create(request):
    """Админ: создание мероприятия"""
    if not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, _("Event created successfully!"))
            return redirect("events:admin_event_edit", pk=event.pk)
    else:
        form = EventForm()

    context = {
        "form": form,
        "title": _("Create Event"),
    }
    return render(request, "events/admin_event_form.html", context)


@login_required
def admin_event_edit(request, pk):
    """Админ: редактирование мероприятия"""
    if not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    event = get_object_or_404(Event, pk=pk)

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
    return render(request, "events/admin_event_form.html", context)


@login_required
def admin_event_delete(request, pk):
    """Админ: удаление мероприятия"""
    if not request.user.is_staff:
        messages.error(request, _("Access denied."))
        return redirect("events:event_list")

    event = get_object_or_404(Event, pk=pk)

    if request.method == "POST":
        event.delete()
        messages.success(request, _("Event deleted successfully!"))
        return redirect("events:admin_event_list")

    context = {
        "event": event,
    }
    return render(request, "events/admin_event_delete.html", context)


@login_required
def add_event_comment(request, slug):
    """Добавление комментария к мероприятию"""
    event = get_object_or_404(Event, slug=slug, status="published")

    if not event.allow_comments:
        return JsonResponse({"error": "Comments are disabled for this event."}, status=400)

    if request.method == "POST":
        comment_text = request.POST.get("comment")
        if comment_text:
            EventComment.objects.create(
                event=event,
                user=request.user,
                comment=comment_text
            )
            return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request."}, status=400)


@login_required
def submit_event_rating(request, slug):
    """Отправка оценки мероприятия"""
    event = get_object_or_404(Event, slug=slug, status="published")

    if request.method == "POST":
        rating = request.POST.get("rating")
        comment = request.POST.get("comment", "")

        # Проверка, что пользователь зарегистрирован на мероприятие
        registration = EventRegistration.objects.filter(
            event=event, user=request.user, status="attended"
        ).exists()

        if not registration:
            return JsonResponse({"error": "You must attend the event to rate it."}, status=400)

        EventRating.objects.update_or_create(
            event=event,
            user=request.user,
            defaults={
                "rating": rating,
                "comment": comment,
                "content_rating": rating,  # Для простоты
                "organization_rating": rating,
            }
        )
        return JsonResponse({"success": True})

    return JsonResponse({"error": "Invalid request."}, status=400)
