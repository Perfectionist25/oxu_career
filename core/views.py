from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.views.generic import TemplateView, ListView
from django.db.models import Count
from .models import ContactMessage
from .forms import ContactForm
from jobs.models import Job
from events.models import Event
from alumni.models import Alumni
from resources.models import Resource

def home(request):
    """Главная страница"""
    # Получаем данные для главной страницы
    stats = {
        'alumni_count': Alumni.objects.count(),
        'jobs_count': Job.objects.filter(is_active=True).count(),
        'companies_count': 50,  # Можно заменить на реальный запрос
        'resources_count': Resource.objects.filter(is_published=True).count(),
    }
    
    # Последние вакансии
    latest_jobs = Job.objects.filter(is_active=True).select_related('company')[:6]
    
    # Предстоящие мероприятия
    from django.utils import timezone
    upcoming_events = Event.objects.filter(
        status='published', 
        start_date__gt=timezone.now()
    ).order_by('start_date')[:3]
    
    context = {
        'stats': stats,
        'latest_jobs': latest_jobs,
        'upcoming_events': upcoming_events,
    }
    return render(request, 'home.html', context)

def about(request):
    """Страница "О нас" """
    team_stats = {
        'years_established': 15,
        'team_members': 12,
        'success_stories': 350,
    }
    
    context = {
        'team_stats': team_stats,
        'page_title': 'О нас - Ассоциация Выпускников',
    }
    return render(request, 'core/about.html', context)

def contact(request):
    """Страница контактов"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Сохраняем сообщение
            contact_message = form.save(commit=False)
            
            # Добавляем дополнительную информацию
            if request.user.is_authenticated:
                contact_message.user = request.user
            
            # Сохраняем IP и User Agent
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                contact_message.ip_address = x_forwarded_for.split(',')[0]
            else:
                contact_message.ip_address = request.META.get('REMOTE_ADDR')
            
            contact_message.user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
            contact_message.save()
            
            # Показываем сообщение об успехе
            messages.success(
                request, 
                'Ваше сообщение успешно отправлено! Мы свяжемся с вами в ближайшее время.'
            )
            
            # Если это AJAX запрос
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'message': 'Ваше сообщение успешно отправлено!'
                })
            
            return redirect('contact_success')
        else:
            # Если форма невалидна и это AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = ContactForm()
    
    # Контактная информация
    contact_info = {
        'email': 'contact@alumni-association.ru',
        'phone': '+7 (495) 123-45-67',
        'address': 'Москва, ул. Студенческая, д. 15',
        'working_hours': 'Пн-Пт: 9:00-18:00',
    }
    
    context = {
        'form': form,
        'contact_info': contact_info,
        'page_title': 'Контакты - Ассоциация Выпускников',
    }
    return render(request, 'core/contact.html', context)

def contact_success(request):
    """Страница успешной отправки сообщения"""
    return render(request, 'core/contact_success.html', {
        'page_title': 'Сообщение отправлено - Ассоциация Выпускников'
    })

def privacy_policy(request):
    """Политика конфиденциальности"""
    return render(request, 'core/privacy_policy.html', {
        'page_title': 'Политика конфиденциальности - Ассоциация Выпускников'
    })

def terms_of_service(request):
    """Пользовательское соглашение"""
    return render(request, 'core/terms_of_service.html', {
        'page_title': 'Пользовательское соглашение - Ассоциация Выпускников'
    })

def faq(request):
    """Часто задаваемые вопросы"""
    faq_items = [
        {
            'question': 'Как присоединиться к ассоциации выпускников?',
            'answer': 'Для присоединения необходимо заполнить регистрационную форму на нашем сайте...'
        },
        {
            'question': 'Какие преимущества дает членство в ассоциации?',
            'answer': 'Членство предоставляет доступ к базе выпускников, менторским программам...'
        },
        {
            'question': 'Как найти однокурсников?',
            'answer': 'Используйте поиск по выпускникам, фильтруя по году выпуска и факультету...'
        },
        {
            'question': 'Могу ли я стать ментором?',
            'answer': 'Да, в вашем профиле можно отметить опцию "Готов быть ментором"...'
        },
    ]
    
    return render(request, 'core/faq.html', {
        'faq_items': faq_items,
        'page_title': 'Часто задаваемые вопросы - Ассоциация Выпускников'
    })

# API views
def api_stats(request):
    """API для получения статистики"""
    stats = {
        'alumni_count': 1250,
        'companies_count': 89,
        'active_jobs': 45,
        'upcoming_events': 5,
        'mentors_available': 230,
    }
    return JsonResponse(stats)

def health_check(request):
    """Проверка работоспособности приложения"""
    return JsonResponse({'status': 'ok', 'message': 'Application is running'})

# Обработчики ошибок
def handler404(request, exception):
    """Кастомная страница 404"""
    return render(request, 'core/404.html', status=404)

def handler500(request):
    """Кастомная страница 500"""
    return render(request, 'core/500.html', status=500)

def handler403(request, exception):
    """Кастомная страница 403"""
    return render(request, 'core/403.html', status=403)

def handler400(request, exception):
    """Кастомная страница 400"""
    return render(request, 'core/400.html', status=400)

# Class-Based Views для статических страниц
class AboutView(TemplateView):
    """Класс-представление для страницы "О нас" """
    template_name = 'core/about.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'О нас - Ассоциация Выпускников',
            'team_stats': {
                'years_established': 15,
                'team_members': 12,
                'success_stories': 350,
            }
        })
        return context

class FAQView(TemplateView):
    """Класс-представление для страницы FAQ"""
    template_name = 'core/faq.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'page_title': 'Часто задаваемые вопросы - Ассоциация Выпускников',
            'faq_items': [
                {
                    'question': 'Как присоединиться к ассоциации выпускников?',
                    'answer': 'Для присоединения необходимо заполнить регистрационную форму...'
                },
                # ... другие вопросы
            ]
        })
        return context

# Дополнительные представления для администрирования (только для staff)
def contact_messages_list(request):
    """Список сообщений обратной связи (для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для просмотра этой страницы.')
        return redirect('home')
    
    messages_list = ContactMessage.objects.all().order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(messages_list, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Статистика
    stats = {
        'total': ContactMessage.objects.count(),
        'new': ContactMessage.objects.filter(is_processed=False).count(),
        'processed': ContactMessage.objects.filter(is_processed=True).count(),
    }
    
    context = {
        'page_obj': page_obj,
        'stats': stats,
        'page_title': 'Сообщения обратной связи',
    }
    return render(request, 'core/contact_messages_list.html', context)

def contact_message_detail(request, pk):
    """Детальное просмотр сообщения (для администраторов)"""
    if not request.user.is_staff:
        messages.error(request, 'У вас нет прав для просмотра этой страницы.')
        return redirect('home')
    
    message = get_object_or_404(ContactMessage, pk=pk)
    
    if request.method == 'POST':
        # Обработка изменения статуса
        new_status = request.POST.get('status')
        admin_notes = request.POST.get('admin_notes')
        
        if new_status in dict(ContactMessage.STATUS_CHOICES):
            message.status = new_status
            message.is_processed = (new_status == 'completed')
            message.admin_notes = admin_notes
            message.save()
            messages.success(request, 'Статус сообщения обновлен.')
            return redirect('contact_message_detail', pk=message.pk)
    
    context = {
        'message': message,
        'page_title': f'Сообщение от {message.name}',
    }
    return render(request, 'core/contact_message_detail.html', context)