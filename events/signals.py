from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Event, EventRegistration

@receiver(post_save, sender=EventRegistration)
def send_registration_confirmation(sender, instance, created, **kwargs):
    """Отправка подтверждения регистрации"""
    if created:
        subject = _('Registration Confirmation - {event_title}').format(
            event_title=instance.event.title
        )
        
        context = {
            'event': instance.event,
            'registration': instance,
            'user': instance.user,
        }
        
        message = render_to_string('events/emails/registration_confirmation.txt', context)
        html_message = render_to_string('events/emails/registration_confirmation.html', context)
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.user.email],
            html_message=html_message,
            fail_silently=True,
        )

@receiver(pre_save, sender=EventRegistration)
def update_registration_count(sender, instance, **kwargs):
    """Обновление счетчика регистраций при изменении статуса"""
    if instance.pk:
        try:
            old_instance = EventRegistration.objects.get(pk=instance.pk)
            if old_instance.status == 'registered' and instance.status != 'registered':
                # Уменьшаем счетчик
                instance.event.registration_count -= 1
                instance.event.save()
            elif old_instance.status != 'registered' and instance.status == 'registered':
                # Увеличиваем счетчик
                instance.event.registration_count += 1
                instance.event.save()
        except EventRegistration.DoesNotExist:
            pass

@receiver(post_save, sender=Event)
def send_event_reminder(sender, instance, **kwargs):
    """Отправка напоминания о мероприятии (заглушка для демонстрации)"""
    # В реальном приложении здесь была бы логика отправки напоминаний
    # за день до мероприятия или в день мероприятия
    pass