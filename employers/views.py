from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Avg, Q  # Убрали Count, так как он не используется
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Временные формы (создадим позже)
from .forms import (
    CompanyForm,
    EmployerProfileForm,
    JobApplicationForm,
    JobForm,
    JobSearchForm,
)

# Исправленные импорты моделей
from .models import (
    Company,
    EmployerProfile,
    Job,
    JobApplication,
)


def job_list(request):
    """Список вакансий"""
    form = JobSearchForm(request.GET or None)
    jobs = Job.objects.filter(is_active=True)

    if form.is_valid():
        query = form.cleaned_data.get("query")
        location = form.cleaned_data.get("location")
        employment_type = form.cleaned_data.get("employment_type")
        experience_level = form.cleaned_data.get("experience_level")
        industry = form.cleaned_data.get("industry")
        remote_work = form.cleaned_data.get("remote_work")

        if query:
            jobs = jobs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(company__name__icontains=query)
                | Q(skills_required__icontains=query)
            )

        if location:
            jobs = jobs.filter(location__icontains=location)

        if employment_type:
            jobs = jobs.filter(employment_type__in=employment_type)

        if experience_level:
            jobs = jobs.filter(experience_level__in=experience_level)

        if industry:
            jobs = jobs.filter(company__industry__in=industry)

        if remote_work:
            jobs = jobs.filter(remote_work=True)

    # Пагинация
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "form": form,
        "total_jobs": jobs.count(),
    }
    return render(request, "employers/job_list.html", context)


def job_detail(request, pk):
    """Детальная страница вакансии"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Увеличиваем счетчик просмотров
    job.views_count += 1
    job.save()

    # Проверяем, откликался ли пользователь
    has_applied = False
    if request.user.is_authenticated:
        has_applied = JobApplication.objects.filter(
            job=job, candidate=request.user
        ).exists()

    application_form = JobApplicationForm()

    # Похожие вакансии
    similar_jobs = Job.objects.filter(
        is_active=True,
        company__industry=job.company.industry,
        experience_level=job.experience_level,
    ).exclude(pk=job.pk)[:4]

    context = {
        "job": job,
        "has_applied": has_applied,
        "application_form": application_form,
        "similar_jobs": similar_jobs,
    }
    return render(request, "employers/job_detail.html", context)


@login_required
def apply_for_job(request, pk):
    """Отклик на вакансию"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Проверяем, не откликался ли уже
    if JobApplication.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, _("You have already applied for this job."))
        return redirect("employers:job_detail", pk=job.pk)

    if request.method == "POST":
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()

            messages.success(
                request, _("Your application has been submitted successfully!")
            )
            return redirect("employers:job_detail", pk=job.pk)
    else:
        form = JobApplicationForm()

    context = {
        "job": job,
        "form": form,
    }
    return render(request, "employers/apply_for_job.html", context)


@login_required
def employer_dashboard(request):
    """Дашборд работодателя"""
    try:
        employer_profile = EmployerProfile.objects.get(
            user=request.user, is_active=True
        )
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("You need to complete your employer profile first."))
        return redirect("employers:create_employer_profile")

    company = employer_profile.company
    jobs = Job.objects.filter(company=company)
    applications = JobApplication.objects.filter(job__company=company)

    # Статистика
    stats = {
        "total_jobs": jobs.count(),
        "active_jobs": jobs.filter(is_active=True).count(),
        "total_applications": applications.count(),
        "new_applications": applications.filter(status="new").count(),
        "interview_scheduled": applications.filter(status="interview").count(),
    }

    # Последние отклики
    recent_applications = applications.select_related("candidate", "job").order_by(
        "-created_at"
    )[:5]

    context = {
        "employer_profile": employer_profile,
        "company": company,
        "stats": stats,
        "recent_applications": recent_applications,
    }
    return render(request, "employers/employer_dashboard.html", context)


@login_required
def create_employer_profile(request):
    """Создание профиля работодателя"""
    if EmployerProfile.objects.filter(user=request.user).exists():
        messages.info(request, _("You already have an employer profile."))
        return redirect("employers:employer_dashboard")

    if request.method == "POST":
        company_form = CompanyForm(request.POST, request.FILES)
        profile_form = EmployerProfileForm(request.POST)

        if company_form.is_valid() and profile_form.is_valid():
            # Создаем компанию
            company = company_form.save()

            # Создаем профиль работодателя
            profile = profile_form.save(commit=False)
            profile.user = request.user
            profile.company = company
            profile.is_primary_contact = True
            profile.can_post_jobs = True
            profile.can_manage_jobs = True
            profile.can_view_candidates = True
            profile.can_contact_candidates = True
            profile.save()

            messages.success(request, _("Employer profile created successfully!"))
            return redirect("employers:employer_dashboard")
    else:
        company_form = CompanyForm()
        profile_form = EmployerProfileForm()

    context = {
        "company_form": company_form,
        "profile_form": profile_form,
    }
    return render(request, "employers/create_employer_profile.html", context)


@login_required
def my_applications(request):
    """Мои отклики"""
    applications = (
        JobApplication.objects.filter(candidate=request.user)
        .select_related("job", "job__company")
        .order_by("-created_at")
    )

    context = {
        "applications": applications,
    }
    return render(request, "employers/my_applications.html", context)


def company_list(request):
    """Список компаний"""
    companies = Company.objects.filter(is_active=True, is_verified=True)

    # Фильтрация по индустрии
    industry = request.GET.get("industry")
    if industry:
        companies = companies.filter(industry=industry)

    # Поиск
    query = request.GET.get("q")
    if query:
        companies = companies.filter(
            Q(name__icontains=query) | Q(description__icontains=query)
        )

    # Пагинация
    paginator = Paginator(companies, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "industries": Company.INDUSTRY_CHOICES,
        "total_companies": companies.count(),
    }
    return render(request, "employers/company_list.html", context)


def company_detail(request, pk):
    """Детальная страница компании"""
    company = get_object_or_404(Company, pk=pk, is_active=True)
    jobs = company.jobs.filter(is_active=True)

    # Отзывы
    reviews = company.reviews.filter(is_published=True)

    # Средний рейтинг
    from django.db.models import Avg
    avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

    context = {
        "company": company,
        "jobs": jobs,
        "reviews": reviews,
        "avg_rating": round(avg_rating, 1),
        "review_count": reviews.count(),
    }
    return render(request, "employers/company_detail.html", context)


# AJAX views
@login_required
def update_application_status(request, pk):
    """Обновление статуса отклика (AJAX)"""
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        application = get_object_or_404(JobApplication, pk=pk)
        new_status = request.POST.get("status")

        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()

            return JsonResponse(
                {
                    "success": True,
                    "new_status": application.get_status_display(),
                    "status_class": new_status,
                }
            )

    return JsonResponse({"success": False})


@login_required
def get_candidate_cvs(request, user_id):
    """Получение резюме кандидата (AJAX)"""
    from cvbuilder.models import CV

    cvs = CV.objects.filter(user_id=user_id, status="published")

    cv_list = [
        {
            "id": cv.id,
            "title": cv.title,
            "full_name": cv.full_name,
        }
        for cv in cvs
    ]

    return JsonResponse({"cvs": cv_list})


# Декоратор для проверки прав работодателя - ДОБАВЛЕНО
def employer_required(function):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")
        if EmployerProfile.objects.filter(user=request.user, is_active=True).exists():
            return function(request, *args, **kwargs)
        messages.error(
            request,
            _("You need to complete your employer profile to access this page."),
        )
        return redirect("employers:create_employer_profile")

    return wrapper


# Дополнительные представления для работодателей - ДОБАВЛЕНО
@employer_required
def post_job(request):
    """Публикация новой вакансии"""
    employer_profile = EmployerProfile.objects.get(user=request.user, is_active=True)

    if not employer_profile.can_post_jobs:
        messages.error(request, _("You do not have permission to post jobs."))
        return redirect("employers:employer_dashboard")

    if request.method == "POST":
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.company = employer_profile.company
            job.posted_by = employer_profile
            job.save()

            messages.success(request, _("Job posted successfully!"))
            return redirect("employers:job_detail", pk=job.pk)
    else:
        form = JobForm(initial={"contact_email": employer_profile.user.email})

    return render(request, "employers/post_job.html", {"form": form})


@employer_required
def manage_jobs(request):
    """Управление вакансиями компании"""
    employer_profile = EmployerProfile.objects.get(user=request.user, is_active=True)
    jobs = Job.objects.filter(company=employer_profile.company).order_by("-created_at")

    # Статистика по вакансиям
    job_stats = {
        "total": jobs.count(),
        "active": jobs.filter(is_active=True).count(),
        "featured": jobs.filter(is_featured=True).count(),
        "expired": jobs.filter(expires_at__lt=timezone.now()).count(),
    }

    context = {
        "jobs": jobs,
        "job_stats": job_stats,
    }
    return render(request, "employers/manage_jobs.html", context)
