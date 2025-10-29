from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from .models import Resource, ResourceReview, StudyPlan

@receiver(post_save, sender=ResourceReview)
def send_review_notification(sender, instance, created, **kwargs):
    """Отправка уведомления о новом отзыве"""
    if created and instance.is_approved:
        subject = _('New Review for {resource_title}').format(
            resource_title=instance.resource.title
        )
        
        context = {
            'resource': instance.resource,
            'review': instance,
            'user': instance.user,
        }
        
        message = render_to_string('resources/emails/new_review.txt', context)
        html_message = render_to_string('resources/emails/new_review.html', context)
        
        # Отправляем email создателю ресурса
        resource_creator = instance.resource.created_by
        if resource_creator.email:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [resource_creator.email],
                html_message=html_message,
                fail_silently=True,
            )

@receiver(post_save, sender=Resource)
def update_resource_stats(sender, instance, **kwargs):
    """Обновление статистики ресурса"""
    # Можно добавить логику для обновления агрегированной статистики
    pass

@receiver(post_delete, sender=Resource)
def cleanup_resource_files(sender, instance, **kwargs):
    """Очистка файлов ресурса при удалении"""
    if instance.file:
        instance.file.delete(save=False)
    if instance.thumbnail:
        instance.thumbnail.delete(save=False)