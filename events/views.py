from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import Event, EventRegistration, EventSpeaker, EventSession, EventComment, EventRating, EventCategory
from .forms import (
    EventForm, EventRegistrationForm, EventSpeakerForm, EventSessionForm,
    EventCommentForm, EventRatingForm, EventSearchForm, BulkEmailForm
)

def event_list(request):
    """Список мероприятий"""
    form = EventSearchForm(request.GET or None)
    events = Event.objects.filter(status='published')
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        event_type = form.cleaned_data.get('event_type')
        date_range = form.cleaned_data.get('date_range')
        location = form.cleaned_data.get('location')
        online_only = form.cleaned_data.get('online_only')
        free_only = form.cleaned_data.get('free_only')
        
        if query:
            events = events.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(short_description__icontains=query) |
                Q(tags__icontains=query)
            )
        
        if category:
            events = events.filter(category=category)
        
        if event_type:
            events = events.filter(event_type=event_type)
        
        if date_range:
            now = timezone.now()
            if date_range == 'today':
                events = events.filter(start_date__date=now.date())
            elif date_range == 'week':
                events = events.filter(start_date__week=now.isocalendar()[1])
            elif date_range == 'month':
                events = events.filter(start_date__month=now.month)
            elif date_range == 'upcoming':
                events = events.filter(start_date__gt=now)
            elif date_range == 'past':
                events = events.filter(end_date__lt=now)
        
        if location:
            events = events.filter(
                Q(location__icontains=location) |
                Q(venue__icontains=location) |
                Q(address__icontains=location)
            )
        
        if online_only:
            events = events.filter(online_event=True)
        
        if free_only:
            events = events.filter(is_free=True)
    
    # Сортировка
    sort = request.GET.get('sort', 'start_date')
    if sort == 'popular':
        events = events.order_by('-views_count')
    elif sort == 'newest':
        events = events.order_by('-created_at')
    else:
        events = events.order_by('start_date')
    
    # Пагинация
    paginator = Paginator(events, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Предстоящие мероприятия для сайдбара
    upcoming_events = Event.objects.filter(
        status='published', 
        start_date__gt=timezone.now()
    ).order_by('start_date')[:5]
    
    context = {
        'page_obj': page_obj,
        'form': form,
        'upcoming_events': upcoming_events,
        'total_events': events.count(),
        'categories': EventCategory.objects.all(),
    }
    return render(request, 'events/list.html', context)

def event_detail(request, slug):
    """Детальная страница мероприятия"""
    event = get_object_or_404(Event, slug=slug, status='published')
    
    # Увеличиваем счетчик просмотров
    event.views_count += 1
    event.save()
    
    # Проверяем регистрацию пользователя
    is_registered = False
    registration = None
    if request.user.is_authenticated:
        try:
            registration = EventRegistration.objects.get(event=event, user=request.user)
            is_registered = True
        except EventRegistration.DoesNotExist:
            pass
    
    # Формы
    registration_form = EventRegistrationForm()
    comment_form = EventCommentForm()
    rating_form = EventRatingForm()
    
    # Проверяем, может ли пользователь оценить мероприятие
    can_rate = False
    if request.user.is_authenticated and event.is_past() and is_registered:
        try:
            EventRating.objects.get(event=event, user=request.user)
        except EventRating.DoesNotExist:
            can_rate = True
    
    # Связанные данные
    speakers = event.speakers.all()
    sessions = event.sessions.all()
    comments = event.comments.filter(is_approved=True, parent_comment__isnull=True)
    photos = event.photos.all()[:8]
    
    # Статистика оценок
    ratings_stats = event.ratings.aggregate(
        avg_rating=Avg('rating'),
        avg_content=Avg('content_rating'),
        avg_organization=Avg('organization_rating'),
        total_ratings=Count('id')
    )
    
    context = {
        'event': event,
        'is_registered': is_registered,
        'registration': registration,
        'registration_form': registration_form,
        'comment_form': comment_form,
        'rating_form': rating_form,
        'can_rate': can_rate,
        'speakers': speakers,
        'sessions': sessions,
        'comments': comments,
        'photos': photos,
        'ratings_stats': ratings_stats,
    }
    return render(request, 'events/event_detail.html', context)

@login_required
def register_for_event(request, slug):
    """Регистрация на мероприятие"""
    event = get_object_or_404(Event, slug=slug, status='published')
    
    # Проверяем, не зарегистрирован ли уже
    if EventRegistration.objects.filter(event=event, user=request.user).exists():
        messages.warning(request, _('You are already registered for this event.'))
        return redirect('events:event_detail', slug=event.slug)
    
    # Проверяем условия регистрации
    if not event.is_registration_open():
        messages.error(request, _('Registration for this event is closed.'))
        return redirect('events:event_detail', slug=event.slug)
    
    if event.registration_full():
        if event.waitlist_enabled:
            messages.info(request, _('This event is full, but you can join the waiting list.'))
        else:
            messages.error(request, _('This event is full. Registration is closed.'))
            return redirect('events:event_detail', slug=event.slug)
    
    if request.method == 'POST':
        form = EventRegistrationForm(request.POST)
        if form.is_valid():
            registration = form.save(commit=False)
            registration.event = event
            registration.user = request.user
            
            # Определяем статус регистрации
            if event.registration_full() and event.waitlist_enabled:
                registration.status = 'waiting'
                messages.info(request, _('You have been added to the waiting list.'))
            else:
                registration.status = 'registered'
                event.registration_count += 1
                event.save()
                messages.success(request, _('You have successfully registered for the event!'))
            
            registration.save()
            return redirect('events:event_detail', slug=event.slug)
    else:
        form = EventRegistrationForm()
    
    context = {
        'event': event,
        'form': form,
    }
    return render(request, 'events/register_for_event.html', context)

@login_required
def cancel_registration(request, slug):
    """Отмена регистрации на мероприятие"""
    event = get_object_or_404(Event, slug=slug, status='published')
    
    try:
        registration = EventRegistration.objects.get(event=event, user=request.user)
        
        if registration.status == 'registered':
            event.registration_count -= 1
            event.save()
            messages.success(request, _('Your registration has been cancelled.'))
        else:
            messages.info(request, _('You have been removed from the waiting list.'))
        
        registration.delete()
        
    except EventRegistration.DoesNotExist:
        messages.error(request, _('You are not registered for this event.'))
    
    return redirect('events:event_detail', slug=event.slug)

@login_required
def my_events(request):
    """Мои мероприятия"""
    registrations = EventRegistration.objects.filter(
        user=request.user
    ).select_related('event').order_by('-registration_date')
    
    # Разделяем на предстоящие и прошедшие
    upcoming = [r for r in registrations if r.event.is_upcoming() or r.event.is_ongoing()]
    past = [r for r in registrations if r.event.is_past()]
    
    context = {
        'upcoming_registrations': upcoming,
        'past_registrations': past,
    }
    return render(request, 'events/my_events.html', context)

@login_required
def create_event(request):
    """Создание мероприятия"""
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.organizer = request.user
            event.status = 'draft'
            event.save()
            
            # Добавляем организатора как со-организатора
            event.co_organizers.add(request.user)
            
            messages.success(request, _('Event created successfully!'))
            return redirect('events:event_detail', slug=event.slug)
    else:
        form = EventForm()
    
    context = {
        'form': form,
    }
    return render(request, 'events/create_event.html', context)

@login_required
def manage_events(request):
    """Управление мероприятиями организатора"""
    events = Event.objects.filter(organizer=request.user).order_by('-created_at')
    
    # Статистика
    stats = {
        'total': events.count(),
        'published': events.filter(status='published').count(),
        'draft': events.filter(status='draft').count(),
        'upcoming': events.filter(status='published', start_date__gt=timezone.now()).count(),
    }
    
    context = {
        'events': events,
        'stats': stats,
    }
    return render(request, 'events/manage_events.html', context)

@login_required
def event_registrations(request, slug):
    """Просмотр регистраций на мероприятие"""
    event = get_object_or_404(Event, slug=slug, organizer=request.user)
    registrations = event.registrations.select_related('user').order_by('-registration_date')
    
    # Статистика по регистрациям
    registration_stats = registrations.aggregate(
        total=Count('id'),
        registered=Count('id', filter=Q(status='registered')),
        waiting=Count('id', filter=Q(status='waiting')),
        attended=Count('id', filter=Q(status='attended')),
    )
    
    context = {
        'event': event,
        'registrations': registrations,
        'registration_stats': registration_stats,
    }
    return render(request, 'events/event_registrations.html', context)

# AJAX views
@login_required
def add_event_comment(request, slug):
    """Добавление комментария к мероприятию"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        event = get_object_or_404(Event, slug=slug, status='published')
        form = EventCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.event = event
            comment.user = request.user
            comment.save()
            
            return JsonResponse({
                'success': True,
                'comment_id': comment.id,
                'user_name': request.user.get_full_name() or request.user.username,
                'comment': comment.comment,
                'created_at': comment.created_at.strftime('%d %b %Y, %H:%M'),
            })
    
    return JsonResponse({'success': False})

@login_required
def submit_event_rating(request, slug):
    """Оценка мероприятия"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        event = get_object_or_404(Event, slug=slug, status='published')
        
        # Проверяем, может ли пользователь оценить
        if not event.is_past():
            return JsonResponse({'success': False, 'error': _('You can only rate past events.')})
        
        try:
            EventRegistration.objects.get(event=event, user=request.user, status='attended')
        except EventRegistration.DoesNotExist:
            return JsonResponse({'success': False, 'error': _('You must have attended the event to rate it.')})
        
        try:
            EventRating.objects.get(event=event, user=request.user)
            return JsonResponse({'success': False, 'error': _('You have already rated this event.')})
        except EventRating.DoesNotExist:
            pass
        
        form = EventRatingForm(request.POST)
        if form.is_valid():
            rating = form.save(commit=False)
            rating.event = event
            rating.user = request.user
            rating.save()
            
            return JsonResponse({'success': True, 'message': _('Thank you for your rating!')})
    
    return JsonResponse({'success': False})

class EventCalendarView(ListView):
    """Календарь мероприятий"""
    model = Event
    template_name = 'events/event_calendar.html'
    context_object_name = 'events'
    
    def get_queryset(self):
        return Event.objects.filter(status='published')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_month'] = timezone.now().month
        context['current_year'] = timezone.now().year
        return context

def event_categories(request):
    """Список категорий мероприятий"""
    categories = EventCategory.objects.annotate(
        event_count=Count('event', filter=Q(event__status='published'))
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'events/event_categories.html', context)