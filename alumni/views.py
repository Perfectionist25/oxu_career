from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AlumniProfileForm,
    JobApplicationForm,
    MentorshipRequestForm,
)
from .models import (
    Alumni,
    Company,
    Connection,
    Event,
    Job,
    Mentorship,
    News,
)


def alumni_list(request):
    """Список всех выпускников"""
    alumni_list = Alumni.objects.filter(is_visible=True)

    # Фильтрация
    faculty = request.GET.get("faculty")
    graduation_year = request.GET.get("graduation_year")
    search_query = request.GET.get("search")

    if faculty:
        alumni_list = alumni_list.filter(faculty=faculty)
    if graduation_year:
        alumni_list = alumni_list.filter(graduation_year=graduation_year)
    if search_query:
        alumni_list = alumni_list.filter(
            Q(name__icontains=search_query)
            | Q(profession__icontains=search_query)
            | Q(company__name__icontains=search_query)
            | Q(specialization__icontains=search_query)
        )

    # Пагинация
    paginator = Paginator(alumni_list, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "faculties": Alumni.FACULTY_CHOICES,
        "graduation_years": sorted(
            set(Alumni.objects.values_list("graduation_year", flat=True)), reverse=True
        ),
    }
    return render(request, "alumni/alumni_list.html", context)


def alumni_detail(request, slug):
    """Детальная страница выпускника"""
    alumni = get_object_or_404(Alumni, slug=slug, is_visible=True)

    # Увеличиваем счетчик просмотров
    if request.user != alumni.user:
        alumni.profile_views += 1
        alumni.save()

    context = {
        "alumni": alumni,
    }
    return render(request, "alumni/alumni_detail.html", context)


@login_required
def alumni_profile_edit(request):
    """Редактирование профиля выпускника"""
    try:
        alumni = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        alumni = None

    if request.method == "POST":
        form = AlumniProfileForm(request.POST, request.FILES, instance=alumni)
        if form.is_valid():
            alumni_profile = form.save(commit=False)
            if not alumni_profile.user:
                alumni_profile.user = request.user
            alumni_profile.save()
            form.save_m2m()  # Для ManyToMany полей
            messages.success(request, "Profil muvaffaqiyatli yangilandi!")
            return redirect("alumni:profile")
    else:
        form = AlumniProfileForm(instance=alumni)

    context = {
        "form": form,
        "alumni": alumni,
    }
    return render(request, "alumni/profile_edit.html", context)


@login_required
def alumni_profile(request):
    """Профиль текущего пользователя"""
    try:
        alumni = Alumni.objects.get(user=request.user)
        return render(request, "alumni/profile.html", {"alumni": alumni})
    except Alumni.DoesNotExist:
        messages.info(request, "Iltimos, profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")


def job_list(request):
    """Список вакансий"""
    job_list = Job.objects.filter(is_active=True)

    # Фильтрация
    employment_type = request.GET.get("employment_type")
    company = request.GET.get("company")
    search_query = request.GET.get("search")

    if employment_type:
        job_list = job_list.filter(employment_type=employment_type)
    if company:
        job_list = job_list.filter(company__id=company)
    if search_query:
        job_list = job_list.filter(
            Q(title__icontains=search_query)
            | Q(description__icontains=search_query)
            | Q(company__name__icontains=search_query)
        )

    paginator = Paginator(job_list, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "companies": Company.objects.all(),
        "employment_types": Job.EMPLOYMENT_TYPES,
    }
    return render(request, "alumni/job_list.html", context)


def job_detail(request, pk):
    """Детальная страница вакансии"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    # Увеличиваем счетчик просмотров
    job.views += 1
    job.save()

    # Проверяем, подавал ли текущий пользователь заявку
    has_applied = False
    if request.user.is_authenticated:
        try:
            alumni = Alumni.objects.get(user=request.user)
            has_applied = job.jobapplication_set.filter(applicant=alumni).exists()
        except Alumni.DoesNotExist:
            pass

    context = {
        "job": job,
        "has_applied": has_applied,
    }
    return render(request, "alumni/job_detail.html", context)


@login_required
def job_apply(request, pk):
    """Подача заявки на вакансию"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    try:
        alumni = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        messages.error(request, "Iltimos, avval profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")

    # Проверяем, не подавал ли уже заявку
    if job.jobapplication_set.filter(applicant=alumni).exists():
        messages.warning(request, "Siz bu vakansiyaga allaqachon ariza yuborgansiz.")
        return redirect("alumni:job_detail", pk=pk)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.applicant = alumni
            application.save()
            messages.success(request, "Arizangiz muvaffaqiyatli yuborildi!")
            return redirect("alumni:job_detail", pk=pk)
    else:
        form = JobApplicationForm()

    context = {
        "form": form,
        "job": job,
    }
    return render(request, "alumni/job_apply.html", context)


def event_list(request):
    """Список мероприятий"""
    event_list = Event.objects.filter(is_active=True)

    # Фильтрация
    event_type = request.GET.get("event_type")
    search_query = request.GET.get("search")

    if event_type:
        event_list = event_list.filter(event_type=event_type)
    if search_query:
        event_list = event_list.filter(
            Q(title__icontains=search_query) | Q(description__icontains=search_query)
        )

    # Разделение на предстоящие и прошедшие
    from datetime import date

    upcoming_events = event_list.filter(date__gte=date.today()).order_by("date")
    past_events = event_list.filter(date__lt=date.today()).order_by("-date")

    context = {
        "upcoming_events": upcoming_events,
        "past_events": past_events,
        "event_types": Event.EVENT_TYPES,
    }
    return render(request, "alumni/event_list.html", context)


def event_detail(request, pk):
    """Детальная страница мероприятия"""
    event = get_object_or_404(Event, pk=pk, is_active=True)

    # Проверяем, зарегистрирован ли пользователь
    is_registered = False
    if request.user.is_authenticated:
        try:
            alumni = Alumni.objects.get(user=request.user)
            is_registered = event.participants.filter(id=alumni.id).exists()
        except Alumni.DoesNotExist:
            pass

    context = {
        "event": event,
        "is_registered": is_registered,
    }
    return render(request, "alumni/event_detail.html", context)


@login_required
def event_register(request, pk):
    """Регистрация на мероприятие"""
    event = get_object_or_404(Event, pk=pk, is_active=True)

    try:
        alumni = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        messages.error(request, "Iltimos, avval profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")

    if event.participants.filter(id=alumni.id).exists():
        messages.warning(request, "Siz ushbu tadbirga allaqachon ro'yxatdan o'tgansiz.")
    else:
        if (
            event.max_participants
            and event.participants.count() >= event.max_participants
        ):
            messages.error(request, "Afsuski, barcha joylar band qilingan.")
        else:
            event.participants.add(alumni)
            messages.success(
                request, "Siz tadbirga muvaffaqiyatli ro'yxatdan o'tdingiz!"
            )

    return redirect("alumni:event_detail", pk=pk)


@login_required
def mentorship_request(request, alumni_slug):
    """Запрос на менторство"""
    mentor = get_object_or_404(Alumni, slug=alumni_slug, is_mentor=True)

    try:
        mentee = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        messages.error(request, "Iltimos, avval profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")

    if mentor == mentee:
        messages.error(request, "Siz o'zingizga mentorlik so'rab bo'lmaysiz.")
        return redirect("alumni:alumni_detail", slug=alumni_slug)

    # Проверяем, есть ли уже активный запрос
    existing_request = Mentorship.objects.filter(
        mentor=mentor, mentee=mentee, status__in=["pending", "active"]
    ).exists()

    if existing_request:
        messages.warning(request, "Siz ushbu mentorga allaqachon so'rov yuborgansiz.")
        return redirect("alumni:alumni_detail", slug=alumni_slug)

    if request.method == "POST":
        form = MentorshipRequestForm(request.POST)
        if form.is_valid():
            mentorship = form.save(commit=False)
            mentorship.mentor = mentor
            mentorship.mentee = mentee
            mentorship.save()
            messages.success(request, "Mentorlik so'rovingiz yuborildi!")
            return redirect("alumni:alumni_detail", slug=alumni_slug)
    else:
        form = MentorshipRequestForm()

    context = {
        "form": form,
        "mentor": mentor,
    }
    return render(request, "alumni/mentorship_request.html", context)


@login_required
def connection_request(request, alumni_slug):
    """Запрос на соединение"""
    to_alumni = get_object_or_404(Alumni, slug=alumni_slug, is_visible=True)

    try:
        from_alumni = Alumni.objects.get(user=request.user)
    except Alumni.DoesNotExist:
        messages.error(request, "Iltimos, avval profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")

    if from_alumni == to_alumni:
        messages.error(request, "Siz o'zingiz bilan bog'lana olmaysiz.")
        return redirect("alumni:alumni_detail", slug=alumni_slug)

    # Проверяем, есть ли уже запрос
    existing_connection = Connection.objects.filter(
        from_user=from_alumni, to_user=to_alumni
    ).exists()

    if existing_connection:
        messages.warning(
            request, "Siz ushbu bitiruvchiga allaqachon so'rov yuborgansiz."
        )
        return redirect("alumni:alumni_detail", slug=alumni_slug)

    if request.method == "POST":
        message = request.POST.get("message", "")
        Connection.objects.create(
            from_user=from_alumni, to_user=to_alumni, message=message
        )
        messages.success(request, "Bog'lanish so'rovi yuborildi!")
        return redirect("alumni:alumni_detail", slug=alumni_slug)

    return redirect("alumni:alumni_detail", slug=alumni_slug)


def news_list(request):
    """Список новостей"""
    news_list = News.objects.filter(is_published=True)

    # Фильтрация по категории
    category = request.GET.get("category")
    if category:
        news_list = news_list.filter(category=category)

    paginator = Paginator(news_list, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "categories": News.CATEGORY_CHOICES,
    }
    return render(request, "alumni/news_list.html", context)


def news_detail(request, slug):
    """Детальная страница новости"""
    news = get_object_or_404(News, slug=slug, is_published=True)

    # Увеличиваем счетчик просмотров
    news.views += 1
    news.save()

    context = {
        "news": news,
    }
    return render(request, "alumni/news_detail.html", context)


@login_required
def dashboard(request):
    """Дашборд пользователя"""
    try:
        alumni = Alumni.objects.get(user=request.user)

        # Получаем relevant данные для дашборда
        mentorship_requests = Mentorship.objects.filter(mentee=alumni, status="pending")
        connection_requests = Connection.objects.filter(
            to_user=alumni, status="pending"
        )
        recent_jobs = Job.objects.filter(is_active=True).order_by("-created_at")[:5]
        upcoming_events = Event.objects.filter(is_active=True).order_by("date")[:5]

        context = {
            "alumni": alumni,
            "mentorship_requests": mentorship_requests,
            "connection_requests": connection_requests,
            "recent_jobs": recent_jobs,
            "upcoming_events": upcoming_events,
        }
        return render(request, "alumni/dashboard.html", context)

    except Alumni.DoesNotExist:
        messages.info(request, "Iltimos, profilingizni to'ldiring.")
        return redirect("alumni:profile_edit")
