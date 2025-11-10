from django.core.mail import send_mass_mail
from django.db.models import Q

from .models import Job, JobApplication


def send_bulk_application_update(applications, subject, message):
    """Массовая рассылка обновлений статуса откликов"""
    email_list = []

    for application in applications:
        personalized_message = message.format(
            job_title=application.job.title,
            company_name=application.job.company.name,
            status=application.get_status_display(),
        )

        email_list.append(
            (
                subject,
                personalized_message,
                None,  # from_email
                [application.candidate.email],
            )
        )

    if email_list:
        return send_mass_mail(email_list, fail_silently=True)

    return 0


def get_job_recommendations(user, limit=10):
    """Получение рекомендаций вакансий для пользователя"""
    from cvbuilder.models import CV

    try:
        # Получаем навыки пользователя из его резюме
        user_cvs = CV.objects.filter(user=user, status="published")
        user_skills = []

        for cv in user_cvs:
            user_skills.extend([skill.name.lower() for skill in cv.skills.all()])

        # Уникальные навыки
        user_skills = list(set(user_skills))

        if not user_skills:
            # Если нет навыков, возвращаем популярные вакансии
            return Job.objects.filter(is_active=True).order_by("-views_count")[:limit]

        # Ищем вакансии с совпадающими навыками
        recommended_jobs = Job.objects.filter(is_active=True)

        # Создаем Q-объекты для поиска по навыкам
        skill_queries = Q()
        for skill in user_skills[:10]:  # Ограничиваем количество навыков для поиска
            skill_queries |= Q(skills_required__icontains=skill)
            skill_queries |= Q(preferred_skills__icontains=skill)

        recommended_jobs = recommended_jobs.filter(skill_queries)

        # Если недостаточно рекомендаций, добавляем популярные вакансии
        if recommended_jobs.count() < limit:
            additional_jobs = (
                Job.objects.filter(is_active=True)
                .exclude(pk__in=recommended_jobs.values_list("pk", flat=True))
                .order_by("-views_count")[: limit - recommended_jobs.count()]
            )

            # Convert to lists and combine to avoid reassigning a QuerySet
            recommended_jobs_list = list(recommended_jobs) + list(additional_jobs)
            return recommended_jobs_list[:limit]

        return recommended_jobs[:limit]

    except Exception:
        # В случае ошибки возвращаем популярные вакансии
        return Job.objects.filter(is_active=True).order_by("-views_count")[:limit]


def generate_job_stats(timeframe="all"):
    """Генерация статистики по вакансиям"""
    from datetime import timedelta

    from django.utils import timezone

    now = timezone.now()

    if timeframe == "week":
        start_date = now - timedelta(days=7)
    elif timeframe == "month":
        start_date = now - timedelta(days=30)
    elif timeframe == "year":
        start_date = now - timedelta(days=365)
    else:  # all
        start_date = None

    jobs = Job.objects.all()
    applications = JobApplication.objects.all()

    if start_date:
        jobs = jobs.filter(created_at__gte=start_date)
        applications = applications.filter(created_at__gte=start_date)

    stats = {
        "total_jobs": jobs.count(),
        "active_jobs": jobs.filter(is_active=True).count(),
        "total_applications": applications.count(),
        "applications_per_job": round(applications.count() / max(jobs.count(), 1), 1),
        "remote_jobs_count": jobs.filter(remote_work=True, is_active=True).count(),
        "featured_jobs_count": jobs.filter(is_featured=True, is_active=True).count(),
    }

    return stats
