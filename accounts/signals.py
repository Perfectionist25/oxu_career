from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import Company, EmployerProfile, CustomUser, StudentProfile, AdminProfile


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """Create a simple profile record after a CustomUser is created.
    
    Используем get_or_create вместо create, чтобы избежать дублирования.
    """
    if not created:
        return

    try:
        with transaction.atomic():
            if instance.user_type == "student":
                StudentProfile.objects.get_or_create(user=instance)
            elif instance.user_type in ("admin", "main_admin"):
                # Проверяем, существует ли уже профиль
                admin_profile, created_profile = AdminProfile.objects.get_or_create(
                    user=instance
                )
                # Если профиль уже существует, просто возвращаем его
                # В противном случае будет создан новый с дефолтными значениями
    except Exception as e:
        # Логируем ошибку, но не прерываем выполнение
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating profile for user {instance.id}: {str(e)}")


@receiver(post_save, sender=Company)
def cleanup_inactive_primary_company(sender, instance, **kwargs):
    """Очистить primary_company_id при деактивации компании
    
    Внимание: в модели EmployerProfile поле называется primary_company_id,
    а не primary_company!
    """
    if not instance.is_active:
        # Найти всех работодателей, у которых эта компания primary
        # Используем primary_company_id, так как именно так называется поле
        EmployerProfile.objects.filter(primary_company_id=instance).update(primary_company_id=None)
        
        # Опционально: логирование для отладки
        if instance.pk:
            count = EmployerProfile.objects.filter(primary_company_id=instance).count()
            if count > 0:
                print(f"Cleared primary_company_id for {count} employer profiles (company: {instance.name})")


@receiver(pre_save, sender=StudentProfile)
def delete_old_avatar_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    if old.avatar and old.avatar != instance.avatar:
        old.avatar.delete(save=False)


@receiver(post_delete, sender=StudentProfile)
def delete_avatar_on_delete(sender, instance, **kwargs):
    if instance.avatar:
        instance.avatar.delete(save=False)
