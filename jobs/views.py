from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST

from accounts.models import EmployerProfile
from typing import Any, Iterable, cast

from .forms import *
from .models import *

@login_required
def employer_applications(request):
    """Ish beruvchilar uchun arizalarni ko'rish"""
    if not request.user.is_employer:
        messages.error(request, _("Faqat ish beruvchilar bu sahifani ko'rishi mumkin."))
        return redirect("jobs:list")

    try:
        employer_profile = request.user.employer_profile
        employer_jobs = Job.objects.filter(employer=employer_profile)
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("Iltimos, avval ish beruvchi profilingizni to'ldiring."))
        return redirect("accounts:employer_profile_update")

    if not employer_jobs.exists():
        messages.info(
            request, _("Arizalarni ko'rish uchun avval vakansiya yaratishingiz kerak.")
        )
        return redirect("jobs:job_create")

    # Arizalarni olish
    applications = (
        JobApplication.objects.filter(job__in=employer_jobs)
        .select_related("job", "job__employer", "candidate", "cv")
        .order_by("-created_at")
    )

    # Status bo'yicha filter
    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)

    # Arizalar statistikasi
    status_counts = {
        "total": applications.count(),
        "applied": applications.filter(status="applied").count(),
        "reviewed": applications.filter(status="reviewed").count(),
        "shortlisted": applications.filter(status="shortlisted").count(),
        "interview": applications.filter(status="interview").count(),
        "rejected": applications.filter(status="rejected").count(),
        "hired": applications.filter(status="hired").count(),
    }

    context = {
        "applications": applications,
        "status_filter": status_filter,
        "status_counts": status_counts,
    }

    return render(request, "jobs/applications.html", context)

@login_required
def job_create(request):
    """Yangi vakansiya yaratish"""
    if not request.user.is_employer:
        messages.error(request, _("Faqat ish beruvchilar vakansiya yarata oladi."))
        return redirect("jobs:list")

    try:
        employer_profile = request.user.employer_profile
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("Avval ish beruvchi profilingizni to'ldiring."))
        return redirect("accounts:employer_profile_update")

    if request.method == "POST":
        form = JobForm(request.POST, user=request.user)
        if form.is_valid():
            job = form.save(commit=False)
            job.employer = employer_profile
            job.created_by = request.user

            if "save_draft" in request.POST:
                job.is_active = False
                job.save()
                messages.success(request, _("Vakansiya qoralama sifatida saqlandi."))
            else:
                job.is_active = True
                job.save()
                messages.success(request, _("Vakansiya muvaffaqiyatli e'lon qilindi!"))

            return redirect("jobs:my_jobs")
        else:
            messages.error(request, _("Iltimos, xatolarni to'g'rilang."))
    else:
        form = JobForm(user=request.user)

    context = {
        "form": form,
        "today": timezone.now().date(),
    }
    return render(request, "jobs/job_form.html", context)

@login_required
def job_edit(request, pk):
    """Mavjud vakansiyani tahrirlash"""
    job = get_object_or_404(Job, pk=pk)

    # Ruxsatni tekshirish
    try:
        employer_profile = request.user.employer_profile
        if job.employer != employer_profile:
            messages.error(request, _("Sizda bu vakansiyani tahrirlash huquqi yo'q."))
            return redirect("jobs:job_detail", pk=pk)
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("Sizda bu vakansiyani tahrirlash huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    if request.method == "POST":
        form = JobForm(request.POST, instance=job, user=request.user)
        if form.is_valid():
            job = form.save()

            if "save_draft" in request.POST:
                job.is_active = False
                job.save()
                messages.success(request, _("Vakansiya qoralama sifatida saqlandi."))
            else:
                job.is_active = True
                job.save()
                messages.success(request, _("Vakansiya muvaffaqiyatli yangilandi!"))

            return redirect("jobs:my_jobs")
        else:
            messages.error(request, _("Iltimos, xatolarni to'g'rilang."))
    else:
        form = JobForm(instance=job, user=request.user)

    context = {
        "form": form,
        "today": timezone.now().date(),
    }
    return render(request, "jobs/job_form.html", context)

@login_required
def job_delete(request, pk):
    """Vakansiyani o'chirish"""
    job = get_object_or_404(Job, pk=pk)

    # Ruxsatni tekshirish
    try:
        employer_profile = request.user.employer_profile
        if not request.user.is_employer or job.employer != employer_profile:
            messages.error(request, _("Sizda bu vakansiyani o'chirish huquqi yo'q."))
            return redirect("jobs:job_detail", pk=pk)
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("Sizda bu vakansiyani o'chirish huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    if request.method == "POST":
        job_title = job.title
        job.delete()
        messages.success(
            request, _(f"'{job_title}' vakansiyasi muvaffaqiyatli o'chirildi.")
        )
        return redirect("jobs:my_jobs")

    context = {
        "job": job,
    }
    return render(request, "jobs/job_confirm_delete.html", context)

@login_required
def my_jobs(request):
    """Mening vakansiyalarim (ish beruvchilar uchun) va arizalarim (talabalar uchun)"""
    context = {}

    if request.user.is_employer:
        # Ish beruvchi uchun - yaratilgan vakansiyalar
        try:
            employer_profile = request.user.employer_profile
            jobs = Job.objects.filter(employer=employer_profile).order_by("-created_at")
        except EmployerProfile.DoesNotExist:
            jobs = Job.objects.none()

        # Statistikalar
        total_jobs = jobs.count()
        active_jobs = jobs.filter(is_active=True).count()
        draft_jobs = jobs.filter(is_active=False).count()

        # Paginatsiya
        paginator = Paginator(jobs, 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "jobs": page_obj,
                "my_jobs": page_obj,
                "total_jobs": total_jobs,
                "active_jobs": active_jobs,
                "draft_jobs": draft_jobs,
                "is_employer_view": True,
            }
        )

    elif request.user.is_student:
        # Talaba uchun - vakansiyalarga arizalar
        applications = (
            JobApplication.objects.filter(candidate=request.user)
            .select_related("job", "job__employer")
            .order_by("-created_at")
        )

        # Statistikalar
        total_applications = applications.count()
        pending_applications = applications.filter(status="applied").count()
        reviewed_applications = applications.filter(status="reviewed").count()
        interview_applications = applications.filter(status="interview").count()
        accepted_applications = applications.filter(status="hired").count()
        rejected_applications = applications.filter(status="rejected").count()

        # Paginatsiya
        paginator = Paginator(list(cast(Iterable[Any], applications)), 10)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context.update(
            {
                "applications": page_obj,
                "my_jobs": page_obj,
                "total_applications": total_applications,
                "pending_applications": pending_applications,
                "reviewed_applications": reviewed_applications,
                "interview_applications": interview_applications,
                "accepted_applications": accepted_applications,
                "rejected_applications": rejected_applications,
                "is_student_view": True,
            }
        )

    else:
        messages.error(request, _("Sizda bu sahifani ko'rish huquqi yo'q"))
        return redirect("accounts:home")

    return render(request, "jobs/my_jobs.html", context)

@login_required
def saved_jobs(request):
    """Saqlangan vakansiyalar"""
    if not request.user.is_student:
        messages.error(request, _("Sizda bu sahifani ko'rish huquqi yo'q"))
        return redirect("accounts:home")

    saved_jobs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job", "job__employer")
        .order_by("-created_at")
    )

    # Paginatsiya
    paginator = Paginator(saved_jobs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "saved_jobs": page_obj,
        "total_saved": saved_jobs.count(),
    }

    return render(request, "jobs/saved_jobs.html", context)

@login_required
def job_list(request):
    """Vakansiyalar ro'yxati"""
    form = JobSearchForm(request.GET or None)
    
    # Права доступа в зависимости от типа пользователя
    if request.user.is_staff or request.user.is_superuser:
        # Админы и суперадмины видят все вакансии
        jobs = Job.objects.all()
    elif request.user.is_employer:
        # Работодатели видят только свои вакансии в любом состоянии
        try:
            employer_profile = request.user.employer_profile
            jobs = Job.objects.filter(employer=employer_profile)
        except EmployerProfile.DoesNotExist:
            jobs = Job.objects.none()
            messages.error(request, _("Iltimos, avval ish beruvchi profilingizni to'ldiring."))
    elif request.user.is_student:
        # Студенты и выпускники видят только опубликованные вакансии
        jobs = Job.objects.filter(is_active=True)
    else:
        # Гости и другие типы пользователей не имеют доступа
        messages.error(request, _("Sizda vakansiyalarni ko'rish huquqi yo'q."))
        return redirect("accounts:home")

    # Поиск и фильтрация
    if form.is_valid():
        query = form.cleaned_data.get("query")
        employment_type = form.cleaned_data.get("employment_type")
        experience_level = form.cleaned_data.get("experience_level")
        remote_work = form.cleaned_data.get("remote_work")
        salary_min = form.cleaned_data.get("salary_min")

        if query:
            jobs = jobs.filter(
                Q(title__icontains=query)
                | Q(description__icontains=query)
                | Q(employer__company_name__icontains=query)
                | Q(skills_required__icontains=query)
            )

        if employment_type:
            jobs = jobs.filter(employment_type__in=employment_type)

        if experience_level:
            jobs = jobs.filter(experience_level__in=experience_level)

        if remote_work:
            jobs = jobs.filter(remote_work=True)

        if salary_min:
            jobs = jobs.filter(
                Q(salary_min__gte=salary_min)
                | Q(salary_max__gte=salary_min)
            )

    # Сортировка
    sort = request.GET.get("sort", "newest")
    if sort == "salary":
        jobs = jobs.order_by("-salary_max", "-salary_min")
    elif sort == "views":
        jobs = jobs.order_by("-views_count")
    elif sort == "applications":
        jobs = jobs.order_by("-applications_count")
    else:
        jobs = jobs.order_by("-created_at")

    # Пагинация
    paginator = Paginator(jobs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Статистика
    total_jobs = jobs.count()
    
    # Для студентов и выпускников показываем рекомендуемые вакансии
    featured_jobs = []
    if request.user.is_student or request.user.is_alumni:
        featured_jobs = jobs.filter(is_featured=True)[:5]

    context = {
        "page_obj": page_obj,
        "form": form,
        "jobs": jobs,
        "total_jobs": total_jobs,
        "featured_jobs": featured_jobs,
        "is_admin": request.user.is_staff or request.user.is_superuser,
        "is_employer": request.user.is_employer,
        "is_student": request.user.is_student,
    }
    return render(request, "jobs/job_list.html", context)

@login_required
def job_detail(request, pk):
    """Vakansiya batafsil sahifasi"""
    # Получаем вакансию с проверкой прав доступа
    if request.user.is_staff or request.user.is_superuser:
        # Админы видят все вакансии
        job = get_object_or_404(Job, pk=pk)
    elif request.user.is_employer:
        # Работодатели видят только свои вакансии
        try:
            employer_profile = request.user.employer_profile
            job = get_object_or_404(Job, pk=pk, employer=employer_profile)
        except EmployerProfile.DoesNotExist:
            messages.error(request, _("Iltimos, avval ish beruvchi profilingizni to'ldiring."))
            return redirect("accounts:employer_profile_update")
    elif request.user.is_student or request.user.is_alumni:
        # Студенты и выпускники видят только активные вакансии
        job = get_object_or_404(Job, pk=pk, is_active=True)
    else:
        # Гости не имеют доступа
        messages.error(request, _("Sizda bu vakansiyani ko'rish huquqi yo'q."))
        return redirect("accounts:login")

    # Увеличиваем счетчик просмотров
    job.views_count += 1
    job.save()

    # Проверяем, подавал ли пользователь заявку
    has_applied = False
    application = None
    if request.user.is_authenticated:
        try:
            application = JobApplication.objects.get(job=job, candidate=request.user)
            has_applied = True
        except JobApplication.DoesNotExist:
            pass

    # Проверяем, сохранена ли вакансия
    is_saved = False
    if request.user.is_authenticated:
        is_saved = SavedJob.objects.filter(job=job, user=request.user).exists()

    # Форма заявки (только для студентов и выпускников)
    application_form = None
    if request.user.is_student or request.user.is_employer:
        application_form = JobApplicationForm()

    # Похожие вакансии (только для опубликованных)
    similar_jobs = []
    if job.is_active:
        similar_jobs = Job.objects.filter(
            is_active=True, 
            experience_level=job.experience_level
        ).exclude(pk=job.pk)[:4]

    context = {
        "job": job,
        "has_applied": has_applied,
        "application": application,
        "is_saved": is_saved,
        "application_form": application_form,
        "similar_jobs": similar_jobs,
        "can_edit": (
            request.user.is_staff or 
            request.user.is_superuser or 
            (request.user.is_employer and hasattr(request.user, 'employer_profile') and job.employer == request.user.employer_profile)
        ),
    }
    return render(request, "jobs/job_detail.html", context)

@require_POST
def increment_job_views(request, pk):
    """Vakansiya ko'rishlar sonini oshirish (AJAX)"""
    job = get_object_or_404(Job, pk=pk)
    job.views_count += 1
    job.save()
    return JsonResponse({"success": True, "views_count": job.views_count})

@login_required
def apply_for_job(request, pk):
    """Vakansiyaga ariza topshirish"""
    # Проверяем, может ли пользователь подавать заявки
    if not (request.user.is_student or request.user.is_alumni):
        messages.error(request, _("Faqat talabalar va bitiruvchilar ariza topshira oladi."))
        return redirect("jobs:job_list")

    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Проверяем, не подавал ли уже заявку
    if JobApplication.objects.filter(job=job, candidate=request.user).exists():
        messages.warning(request, _("Siz ushbu vakansiyaga allaqachon ariza topshirgansiz."))
        return redirect("jobs:job_detail", pk=job.pk)

    # Проверяем, не истек ли срок вакансии
    if job.is_expired():
        messages.error(request, _("Ushbu vakansiyaning muddati tugagan."))
        return redirect("jobs:job_detail", pk=job.pk)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.candidate = request.user
            application.save()

            # Увеличиваем счетчик заявок
            job.applications_count += 1
            job.save()

            messages.success(
                request, _("Arizangiz muvaffaqiyatli yuborildi!")
            )
            return redirect("jobs:job_detail", pk=job.pk)
    else:
        form = JobApplicationForm(user=request.user)

    context = {
        "job": job,
        "form": form,
    }
    return render(request, "jobs/apply_for_job.html", context)

@login_required
def save_job(request, pk):
    """Vakansiyani saqlash"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    if request.method == "POST":
        saved_job, created = SavedJob.objects.get_or_create(job=job, user=request.user)

        if created:
            messages.success(request, _("Vakansiya muvaffaqiyatli saqlandi!"))
        else:
            messages.info(request, _("Vakansiya allaqachon saqlangan."))

    return redirect("jobs:job_detail", pk=job.pk)

@login_required
def unsave_job(request, pk):
    """Vakansiyani saqlanganlardan o'chirish"""
    job = get_object_or_404(Job, pk=pk)

    if request.method == "POST":
        SavedJob.objects.filter(job=job, user=request.user).delete()
        messages.success(request, _("Vakansiya saqlanganlardan o'chirildi."))

    return redirect("jobs:job_detail", pk=job.pk)

@login_required
def my_applications(request):
    """Mening arizalarim"""
    applications = (
        JobApplication.objects.filter(candidate=request.user)
        .select_related("job", "job__employer")
        .order_by("-created_at")
    )

    # Statistikalar
    stats = applications.aggregate(
        total=Count("id"),
        applied=Count("id", filter=Q(status="applied")),
        reviewed=Count("id", filter=Q(status="reviewed")),
        interview=Count("id", filter=Q(status="interview")),
        hired=Count("id", filter=Q(status="hired")),
    )

    context = {
        "applications": applications,
        "stats": stats,
    }
    return render(request, "jobs/my_applications.html", context)

# AJAX viewlar
@login_required
def update_application_status(request, pk):
    """Ariza statusini yangilash (AJAX)"""
    if (
        request.method == "POST"
        and request.headers.get("X-Requested-With") == "XMLHttpRequest"
    ):
        application = get_object_or_404(JobApplication, pk=pk, candidate=request.user)
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
def get_user_cvs(request):
    """Foydalanuvchi rezyumelarini olish (AJAX)"""
    from cvbuilder.models import CV

    cvs = CV.objects.filter(user=request.user, status="published")

    cv_list = [
        {
            "id": cv.id,
            "title": cv.title,
            "full_name": cv.full_name,
        }
        for cv in cvs
    ]

    return JsonResponse({"cvs": cv_list})

@login_required
def industries_list(request):
    """Tarmoqlar ro'yxati"""
    industries = Industry.objects.all().order_by("name")

    context = {
        "industries": industries,
    }
    return render(request, "jobs/industries_list.html", context)

@login_required
def application_detail(request, pk):
    """Ariza batafsil (AJAX uchun)"""
    application = get_object_or_404(JobApplication, pk=pk)

    # Ruxsatni tekshiramiz
    if not (
        application.candidate == request.user
        or application.job.employer.user == request.user
    ):
        return JsonResponse({"error": "Ruxsat rad etildi"}, status=403)

    context = {
        "application": application,
    }
    return render(request, "jobs/application_detail.html", context)

@login_required
@require_POST
def add_application_note(request, pk):
    """Arizaga izoh qo'shish (AJAX)"""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        application = get_object_or_404(JobApplication, pk=pk)

        # Faqat ish beruvchi uchun ruxsat
        if application.job.employer.user != request.user:
            return JsonResponse({"success": False, "error": "Ruxsat rad etildi"})

        note = request.POST.get("note")
        if note:
            # Izohni saqlash logikasi
            return JsonResponse({"success": True})

        return JsonResponse({"success": False, "error": "Izoh kiritish majburiy"})

    return JsonResponse({"success": False, "error": "Noto'g'ri so'rov"})