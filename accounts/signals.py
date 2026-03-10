from django.contrib.auth.signals import user_logged_in, user_login_failed
from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .middleware import BruteForceProtectionMiddleware
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

                admin_profile, created_profile = AdminProfile.objects.get_or_create(
                    user=instance
                )


    except Exception as e:

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


        EmployerProfile.objects.filter(primary_company_id=instance).update(primary_company_id=None)


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


def _get_request_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


def _is_django_admin_login_request(request):
    return bool(request and (request.path or "").startswith("/admin/login/"))


@receiver(user_login_failed)
def track_django_admin_login_failures(sender, credentials, request=None, **kwargs):
    if not _is_django_admin_login_request(request):
        return

    ip_address = _get_request_ip(request)
    if not ip_address:
        return

    username = str((credentials or {}).get("username", "")).strip() or None
    BruteForceProtectionMiddleware.record_failed_attempt(ip_address, username)


@receiver(user_logged_in)
def clear_django_admin_login_failures(sender, request, user, **kwargs):
    if not _is_django_admin_login_request(request):
        return

    ip_address = _get_request_ip(request)
    if not ip_address:
        return

    username = getattr(user, "get_username", lambda: None)()
    BruteForceProtectionMiddleware.clear_attempts(ip_address, username)
