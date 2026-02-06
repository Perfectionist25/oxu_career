from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from .models import Job, JobAlert, JobApplication


@receiver(post_save, sender=JobApplication)
def send_application_confirmation(sender, instance, created, **kwargs):
    """Отправка подтверждения отклика"""
    if created:
        subject = _("Application Confirmation - {job_title}").format(
            job_title=instance.job.title
        )

        context = {
            "job": instance.job,
            "application": instance,
            "user": instance.candidate,
        }

        message = render_to_string("jobs/emails/application_confirmation.txt", context)
        html_message = render_to_string(
            "jobs/emails/application_confirmation.html", context
        )

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [instance.candidate.email],
            html_message=html_message,
            fail_silently=True,
        )


@receiver(post_save, sender=Job)
def check_job_alerts(sender, instance, created, **kwargs):
    """Проверка оповещений о вакансиях при создании новой вакансии"""
    if created and instance.is_active:
        from django.utils import timezone

        # Поиск подходящих оповещений
        alerts = JobAlert.objects.filter(is_active=True)

        # Базовые условия
        if instance.location:
            alerts = alerts.filter(
                Q(location__icontains=instance.location) | Q(location="")
            )

        if instance.employment_type:
            alerts = alerts.filter(
                Q(employment_type=instance.employment_type) | Q(employment_type="")
            )

        if instance.experience_level:
            alerts = alerts.filter(
                Q(experience_level=instance.experience_level) | Q(experience_level="")
            )

        # Проверка ключевых слов
        if instance.company.industry:
            alerts = alerts.filter(
                Q(industry=instance.company.industry) | Q(industry__isnull=True)
            )

        matching_alerts = []
        for alert in alerts:
            # Проверка ключевых слов
            if alert.keywords:
                keywords = [kw.strip().lower() for kw in alert.keywords.split(",")]
                matches = any(
                    kw in instance.title.lower()
                    or kw in instance.description.lower()
                    or kw in instance.skills_required.lower()
                    for kw in keywords
                )
                if not matches:
                    continue

            matching_alerts.append(alert)

        # Отправка email для подходящих оповещений
        for alert in matching_alerts:
            subject = _("New Job Alert: {job_title}").format(job_title=instance.title)

            context = {
                "job": instance,
                "alert": alert,
                "user": alert.user,
            }

            message = render_to_string("jobs/emails/job_alert.txt", context)
            html_message = render_to_string("jobs/emails/job_alert.html", context)

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [alert.user.email],
                html_message=html_message,
                fail_silently=True,
            )

            # Обновляем время последней отправки
            alert.last_sent = timezone.now()
            alert.save()
