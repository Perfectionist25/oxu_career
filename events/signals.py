from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .models import Event, EventRegistration


@receiver(pre_save, sender=EventRegistration)
def update_registration_count(sender, instance, **kwargs):
    """Обновление счетчика регистраций при изменении статуса"""
    if instance.pk:
        try:
            old_instance = EventRegistration.objects.get(pk=instance.pk)
            if old_instance.status == "registered" and instance.status != "registered":
                # Уменьшаем счетчик
                instance.event.registration_count -= 1
                instance.event.save()
            elif (
                old_instance.status != "registered" and instance.status == "registered"
            ):
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
