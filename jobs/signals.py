from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import pre_save
from django.db.models import Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _

from accounts.models import Notification
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

        employer_user = getattr(instance.job.company, "owner", None)
        if employer_user and employer_user != instance.user:
            Notification.objects.create(
                user=employer_user,
                notification_type="application_update",
                title=_("New job application received"),
                message=_("{candidate} applied for '{job_title}'.").format(
                    candidate=instance.user.get_full_name() or instance.user.username,
                    job_title=instance.job.title,
                ),
                related_url=instance.job.get_absolute_url(),
                related_company=instance.job.company,
            )


@receiver(pre_save, sender=JobApplication)
def track_previous_application_status(sender, instance, **kwargs):
    """Cache previous status to detect status changes on post_save."""
    if not instance.pk:
        instance._previous_status = None
        return
    previous_status = (
        JobApplication.objects.filter(pk=instance.pk)
        .values_list("status", flat=True)
        .first()
    )
    instance._previous_status = previous_status


@receiver(post_save, sender=JobApplication)
def notify_candidate_on_status_change(sender, instance, created, **kwargs):
    """Send in-app notification to candidate when application status changes."""
    if created:
        return

    previous_status = getattr(instance, "_previous_status", None)
    if not previous_status or previous_status == instance.status:
        return

    Notification.objects.create(
        user=instance.user,
        notification_type="application_update",
        title=_("Application status updated"),
        message=_("Your application for '{job_title}' is now '{status}'.").format(
            job_title=instance.job.title,
            status=instance.get_status_display(),
        ),
        related_url=instance.job.get_absolute_url(),
        related_company=instance.job.company,
    )


@receiver(post_save, sender=Job)
def check_job_alerts(sender, instance, created, **kwargs):
    """Проверка оповещений о вакансиях при создании новой вакансии"""
    if created and instance.is_active:
        from django.utils import timezone


        alerts = JobAlert.objects.filter(is_active=True)


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


        if instance.company.industry:
            alerts = alerts.filter(
                Q(industry=instance.company.industry) | Q(industry__isnull=True)
            )

        matching_alerts = []
        for alert in alerts:

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


            alert.last_sent = timezone.now()
            alert.save()
