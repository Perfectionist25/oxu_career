from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from .models import Interview, JobApplication


@receiver(post_save, sender=JobApplication)
def send_application_notification(sender, instance, created, **kwargs):
    """Отправка уведомления о новом отклике"""
    if created:
        subject = _("New Job Application Received")
        message = _(
            "You have received a new application for the position: {job_title}\n"
            "Candidate: {candidate_name}\n"
            "View application: {application_url}"
        ).format(
            job_title=instance.job.title,
            candidate_name=instance.candidate.get_full_name()
            or instance.candidate.username,
            application_url=f"{settings.SITE_URL}/employers/applications/{instance.pk}/",
        )

        # Отправляем email работодателю
        employer_email = instance.job.contact_email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [employer_email],
            fail_silently=True,
        )


@receiver(post_save, sender=Interview)
def send_interview_invitation(sender, instance, created, **kwargs):
    """Отправка приглашения на собеседование"""
    if created:
        subject = _("Interview Invitation - {company}").format(
            company=instance.application.job.company.name
        )
        message = _(
            "Dear {candidate_name},\n\n"
            "You have been invited for an interview for the position: {job_title}\n"
            "Date and Time: {datetime}\n"
            "Location: {location}\n"
            "Duration: {duration} minutes\n"
            "Interviewer: {interviewer}\n\n"
            "Best regards,\n{company} Team"
        ).format(
            candidate_name=instance.application.candidate.get_full_name()
            or instance.application.candidate.username,
            job_title=instance.application.job.title,
            datetime=instance.scheduled_date.strftime("%Y-%m-%d %H:%M"),
            location=instance.location,
            duration=instance.duration,
            interviewer=instance.interviewer.user.get_full_name()
            or instance.interviewer.user.username,
            company=instance.application.job.company.name,
        )

        # Отправляем email кандидату
        candidate_email = instance.application.candidate.email
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [candidate_email],
            fail_silently=True,
        )
