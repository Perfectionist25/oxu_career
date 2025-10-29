from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mass_mail
from .models import EventRegistration

def send_bulk_event_email(event, subject, message, recipient_type='all'):
    """Массовая рассылка email участникам мероприятия"""
    if recipient_type == 'all':
        recipients = EventRegistration.objects.filter(event=event)
    elif recipient_type == 'confirmed':
        recipients = EventRegistration.objects.filter(event=event, status='registered')
    elif recipient_type == 'waiting':
        recipients = EventRegistration.objects.filter(event=event, status='waiting')
    elif recipient_type == 'attended':
        recipients = EventRegistration.objects.filter(event=event, status='attended')
    else:
        return 0
    
    email_list = []
    for registration in recipients:
        email_list.append((
            subject,
            message,
            None,  # from_email (используется DEFAULT_FROM_EMAIL)
            [registration.user.email],
        ))
    
    if email_list:
        sent_count = send_mass_mail(email_list, fail_silently=True)
        return sent_count
    
    return 0

def generate_event_stats(event):
    """Генерация статистики по мероприятию"""
    registrations = event.registrations.all()
    
    stats = {
        'total_registrations': registrations.count(),
        'confirmed': registrations.filter(status='registered').count(),
        'waiting_list': registrations.filter(status='waiting').count(),
        'attended': registrations.filter(status='attended').count(),
        'cancelled': registrations.filter(status='cancelled').count(),
        'no_show': registrations.filter(status='no_show').count(),
    }
    
    # Процент посещаемости
    if stats['confirmed'] > 0:
        stats['attendance_rate'] = round((stats['attended'] / stats['confirmed']) * 100, 1)
    else:
        stats['attendance_rate'] = 0
    
    return stats