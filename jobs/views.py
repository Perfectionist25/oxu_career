from django.contrib import messages
from django.contrib.auth.decorators import login_required
import hmac
import html
import json
import logging
import re
from datetime import timedelta

import requests
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.core.exceptions import ValidationError

from accounts.models import EmployerProfile, Company, user_has_admin_permission
from accounts.certificates import get_viewable_student_certificates_queryset
from accounts.views import *

from .forms import *
from .models import *

logger = logging.getLogger(__name__)

MAX_IMAGE_DOWNLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_IMAGE_CONTENT_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}
PHOTO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def _get_request_token(request):
    return request.headers.get("X-App-Token") or request.META.get("HTTP_X_APP_TOKEN")


def _secure_compare_tokens(request_token, secret_token):
    if not request_token or not secret_token:
        return False
    # Приведение к str предотвращает TypeError в hmac.compare_digest
    return hmac.compare_digest(str(request_token), str(secret_token))


def _build_telegram_message(job):
    def escape(value):
        # На случай, если из Google Form или при экранировании кода прилетели сырые '\n'
        val = str(value or "").replace("\\n", "\n")
        return html.escape(val)

    title = escape(job.title)
    salary = escape(job.salary or "Maosh: ma'lumot kiritilmagan")
    work_time = escape(job.work_time or "Ish vaqti: ma'lumot kiritilmagan")
    description = escape(job.description)
    contacts = escape(job.contacts or "@OXU_HR")

    # Собираем сообщение с гарантированными переносами строк
    message = (
        "Osiyo Xalqaro Universitetida yangi vakansiyalar e'lon qilinadi!\n\n"
        "<blockquote>"
        f"<b>{title}</b>\n"
        f"{salary}\n"
        f"{work_time}\n"
        f"{description}"
        "</blockquote>\n\n"
        f"<b>Kontaktlar:</b> {contacts}"
    )
    return message


def _download_google_form_image(photo_id):
    if not photo_id or not PHOTO_ID_PATTERN.fullmatch(photo_id):
        logger.warning("Invalid Google Drive photo_id received: %s", photo_id)
        return None, None

    image_url = f"https://docs.google.com/uc?export=download&id={photo_id}"
    try:
        response = requests.get(
            image_url,
            stream=True,
            timeout=(5, 15),
            allow_redirects=True,
        )
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        file_ext = ALLOWED_IMAGE_CONTENT_TYPES.get(content_type)
        if not file_ext:
            logger.warning("Unsupported image content type: %s", content_type)
            return None, None

        content_length = response.headers.get("Content-Length")
        if content_length is not None:
            try:
                if int(content_length) > MAX_IMAGE_DOWNLOAD_SIZE:
                    logger.warning("Image content length too large: %s", content_length)
                    return None, None
            except ValueError:
                logger.warning("Invalid Content-Length header: %s", content_length)
                return None, None

        image_data = bytearray()
        for chunk in response.iter_content(chunk_size=8192):
            if not chunk:
                continue
            image_data.extend(chunk)
            if len(image_data) > MAX_IMAGE_DOWNLOAD_SIZE:
                logger.warning("Image exceeded maximum allowed size (%s bytes)", MAX_IMAGE_DOWNLOAD_SIZE)
                return None, None

        if not image_data:
            logger.warning("Downloaded image is empty for photo_id=%s", photo_id)
            return None, None

        filename = f"google_form_{photo_id}{file_ext}"
        return bytes(image_data), filename
    except requests.RequestException as exc:
        logger.warning("Failed to download Google Form image: %s", exc)
        return None, None


def _send_job_to_telegram(job):
    """Send a job announcement to the configured Telegram channel."""
    bot_token = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
    channel_id = getattr(settings, "TELEGRAM_CHANNEL_ID", None)

    if not bot_token or not channel_id:
        logger.warning("Telegram bot token or channel ID is not configured.")
        return

    message = _build_telegram_message(job)
    base_url = f"https://api.telegram.org/bot{bot_token}"

    try:
        if job.image:
            if len(message) <= 1024:
                # Для sendPhoto передаем ТОЛЬКО то, что он поддерживает
                payload = {
                    "chat_id": channel_id,
                    "caption": message,
                    "parse_mode": "HTML",
                }
                with job.image.open("rb") as image_file:
                    response = requests.post(
                        f"{base_url}/sendPhoto",
                        data=payload,
                        files={"photo": image_file},
                        timeout=(5, 15),
                    )
                response.raise_for_status()
            else:
                # Если текст > 1024 символов, шлем картинку отдельно, текст — отдельно
                with job.image.open("rb") as image_file:
                    response = requests.post(
                        f"{base_url}/sendPhoto",
                        data={"chat_id": channel_id},
                        files={"photo": image_file},
                        timeout=(5, 15),
                    )
                response.raise_for_status()

                message_payload = {
                    "chat_id": channel_id,
                    "text": message,
                    "parse_mode": "HTML",
                }
                response = requests.post(
                    f"{base_url}/sendMessage",
                    json=message_payload,  # Для обычного текста JSON надежнее form-data
                    timeout=(5, 15),
                )
                response.raise_for_status()
        else:
            # Отправка чистого текста без фото
            message_payload = {
                "chat_id": channel_id,
                "text": message,
                "parse_mode": "HTML",
            }
            response = requests.post(
                f"{base_url}/sendMessage",
                json=message_payload,
                timeout=(5, 15),
            )
            response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Failed to send job announcement to Telegram: %s", exc)


@csrf_exempt
@require_POST
def google_form_webhook(request):
    """Webhook для приема вакансий из Google Формы и отправки в Telegram."""
    request_token = _get_request_token(request)
    secret_token = getattr(settings, "SECRET_TOKEN", None)

    if not _secure_compare_tokens(request_token, secret_token):
        return JsonResponse({"detail": "Unauthorized"}, status=401)

    if not request.content_type or "application/json" not in request.content_type:
        return JsonResponse({"detail": "Content-Type must be application/json"}, status=415)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"detail": "Invalid JSON payload"}, status=400)

    title = str(payload.get("title", "")).strip()
    description = str(payload.get("description", "")).strip()
    if not title or not description:
        return JsonResponse(
            {"detail": "Both title and description are required."},
            status=400,
        )

    salary = str(payload.get("salary", "")).strip()
    work_time = str(payload.get("work_time", "")).strip()
    contacts = str(payload.get("contacts") or "@OXU_HR").strip()
    
    raw_photo_id = payload.get("photo_id")
    photo_id = str(raw_photo_id).strip() if raw_photo_id else ""

    try:
        job = Job.objects.create(
            title=title,
            description=description,
            short_description=description[:300],
            salary=salary,
            work_time=work_time,
            contacts=contacts,
            source="google_form",
            company=None,
            work_type="office",
            employment_type="full_time",
            experience_level="no_experience",
            education_level="none",
            contact_email=getattr(settings, "DEFAULT_JOB_CONTACT_EMAIL", "hr@oxu.uz"),
            requirements=description,
            responsibilities=description,
            skills_required="Not specified",
            preferred_skills="",
            language_requirements="",
            district="",
            region="",
            benefits="",
            contact_phone="",
            contact_person="",
            application_url="",
            work_schedule="",
            probation_period=""
        )
    except Exception as exc:
        logger.exception("Database error during Job creation from webhook: %s", exc)
        return JsonResponse({"detail": "Internal server database error"}, status=500)

    if photo_id and photo_id.lower() != "none":
        image_bytes, filename = _download_google_form_image(photo_id)
        if image_bytes and filename:
            try:
                job.image.save(filename, ContentFile(image_bytes), save=True)
            except Exception as exc:
                logger.warning("Failed to save Google Form image for job %s: %s", job.pk, exc)

    try:
        _send_job_to_telegram(job)
    except Exception as exc:
        logger.exception("Failed to process Telegram sending pipeline: %s", exc)

    return JsonResponse({"detail": "Job created", "job_id": job.pk}, status=201)


def _is_student_or_alumni(user):
    return user.is_authenticated and user.user_type in ["student", "alumni"]


def _attach_job_state(user, jobs):
    jobs = list(jobs)
    job_ids = [job.id for job in jobs]
    saved_job_ids = set()
    viewed_job_ids = set()

    if _is_student_or_alumni(user) and job_ids:
        saved_job_ids = set(
            SavedJob.objects.filter(user=user, job_id__in=job_ids).values_list("job_id", flat=True)
        )
        viewed_job_ids = set(
            ViewedJob.objects.filter(user=user, job_id__in=job_ids).values_list("job_id", flat=True)
        )

    for job in jobs:
        job.is_saved = job.id in saved_job_ids
        job.is_viewed = job.id in viewed_job_ids

    return jobs, saved_job_ids, viewed_job_ids


def _get_safe_next_url(request, default=None):
    next_url = (
        request.POST.get("next")
        or request.GET.get("next")
        or request.META.get("HTTP_REFERER")
    )
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return default


@login_required
def employer_applications(request):
    """Ish beruvchilar uchun arizalarni ko'rish"""
    if not request.user.is_employer:
        messages.error(request, _("Faqat ish beruvchilar bu sahifani ko'rishi mumkin."))
        return redirect("jobs:list")

    try:
        EmployerProfile.objects.get(user=request.user)
        owned_companies = Company.objects.filter(owner=request.user, is_active=True)
        user_companies = list(owned_companies)

        if not user_companies:
            messages.info(request, _("Hali hech qanday kompaniya yaratilmagan."))
            return redirect("accounts:company_create")

        employer_jobs = Job.objects.filter(company__in=user_companies)
    except EmployerProfile.DoesNotExist:
        messages.error(request, _("Ish beruvchi profili topilmadi."))
        return redirect("accounts:employer_profile_update")
    except Exception as e:
        logger.error("Error loading employer applications: %s", e)
        messages.error(request, _("Ma'lumotlarni yuklashda xatolik yuz berdi."))
        return redirect("accounts:company_list")

    if not employer_jobs.exists():
        messages.info(
            request, _("Arizalarni ko'rish uchun avval vakansiya yaratishingiz kerak.")
        )
        return redirect("jobs:job_create")

    applications = (
        JobApplication.objects.filter(job__in=employer_jobs)
        .select_related("job", "job__company", "user", "cv")
        .order_by("-created_at")
    )

    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)

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
        "user_companies": user_companies,
        "user_companies_count": len(user_companies),
    }

    return render(request, "jobs/applications.html", context)


@login_required
def job_create(request):
    """Yangi vakansiya yaratish"""
    is_admin_user = user_has_admin_permission(request.user, "can_create_jobs")

    if not (request.user.is_employer or is_admin_user):
        messages.error(request, _("Faqat ish beruvchilar yoki adminlar vakansiya yarata oladi."))
        return redirect("jobs:list")

    form_class = AdminJobForm if is_admin_user and not request.user.is_employer else JobForm
    template_name = "jobs/admin_job_form.html" if is_admin_user and not request.user.is_employer else "jobs/job_form.html"

    employer_profile = None
    if request.user.is_employer:
        try:
            employer_profile = EmployerProfile.objects.get(user=request.user)
        except EmployerProfile.DoesNotExist:
            messages.error(request, _("Ish beruvchi profili topilmadi. Iltimos, profilingizni to'ldiring."))
            return redirect("accounts:employer_profile_update")

    if is_admin_user and not request.user.is_employer:
        available_companies = Company.objects.filter(is_active=True)
    else:
        available_companies = Company.objects.filter(owner=request.user, is_active=True)

    if not available_companies.exists():
        if is_admin_user and not request.user.is_employer:
            messages.error(request, _("Faol kompaniyalar topilmadi. Avval kompaniya yarating."))
            return redirect("jobs:list")
        messages.error(request, _("Vakansiya yaratish uchun avval kompaniya yaratishingiz kerak."))
        return redirect("accounts:company_create")

    if request.method == "POST":
        form = form_class(request.POST, user=request.user)

        if form.is_valid():
            try:
                job = form.save(commit=False)
                selected_company = form.cleaned_data.get('company')

                if selected_company not in available_companies:
                    messages.error(request, _("Tanlangan kompaniyaga vakansiya yaratish huquqingiz yo'q."))
                    context = {
                        "form": form,
                        "owned_companies": available_companies,
                        "employer_profile": employer_profile,
                        "today": timezone.now().date(),
                    }
                    return render(request, template_name, context)

                if request.user.is_employer:
                    job.created_by = employer_profile
                else:
                    job.created_by = EmployerProfile.objects.filter(user=selected_company.owner).first()

                if 'save_draft' in request.POST:
                    job.is_active = False
                    save_message = _("Vakansiya qoralama sifatida saqlandi.")
                else:
                    job.is_active = True
                    save_message = _("Vakansiya muvaffaqiyatli e'lon qilindi!")

                job.save()
                messages.success(request, save_message)
                if request.user.is_employer:
                    return redirect("jobs:my_jobs")
                return redirect("jobs:list")

            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                logger.error("Error creating job: %s", e)
                messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        
        context = {
            "form": form,
            "owned_companies": available_companies,
            "employer_profile": employer_profile,
            "today": timezone.now().date(),
        }
        return render(request, template_name, context)
    else:
        initial_data = {
            'contact_email': request.user.email,
            'contact_person': request.user.get_full_name() or request.user.username,
        }
        form = form_class(initial=initial_data, user=request.user)
        form.fields['company'].queryset = available_companies.distinct()

        if available_companies and len(available_companies) == 1:
            form.fields['company'].initial = available_companies[0]

    context = {
        "form": form,
        "today": timezone.now().date(),
        "owned_companies": available_companies,
        "employer_profile": employer_profile,
    }
    return render(request, template_name, context)


@login_required
def job_edit(request, pk):
    """Mavjud vakansiyani tahrirlash"""
    job = get_object_or_404(Job, pk=pk)

    employer_profile = None
    is_job_admin = user_has_admin_permission(request.user, "can_manage_jobs")

    if request.user.is_employer:
        try:
            employer_profile = EmployerProfile.objects.get(user=request.user)
        except EmployerProfile.DoesNotExist:
            messages.error(request, _("Ish beruvchi profili topilmadi."))
            return redirect("accounts:employer_profile_update")
        available_companies = Company.objects.filter(owner=request.user, is_active=True)
        form_class = JobForm
        template_name = "jobs/job_form.html"
    elif is_job_admin:
        available_companies = Company.objects.filter(is_active=True)
        form_class = AdminJobForm
        template_name = "jobs/admin_job_form.html"
    else:
        messages.error(request, _("Sizda bu vakansiyani tahrirlash huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    if job.company not in available_companies:
        messages.error(request, _("Sizda bu vakansiyani tahrirlash huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    context = {
        "job": job,
        "employer_profile": employer_profile,
        "today": timezone.now().date(),
    }

    if request.method == "POST":
        form = form_class(request.POST, instance=job, user=request.user)
        if form.is_valid():
            try:
                selected_company = form.cleaned_data.get('company')
                if selected_company not in available_companies:
                    messages.error(request, _("Siz tanlagan kompaniyaga vakansiya tahrirlash huquqingiz yo'q."))
                    context["form"] = form
                    return render(request, template_name, context)

                job = form.save(commit=False)
                action = request.POST.get("action")
                if action == "draft":
                    job.is_active = False
                    save_message = _("Vakansiya qoralama sifatida saqlandi.")
                else:
                    job.is_active = True
                    save_message = _("Vakansiya muvaffaqiyatli yangilandi!")

                job.save()
                messages.success(request, save_message)
                if request.user.is_employer:
                    return redirect("jobs:my_jobs")
                return redirect("jobs:job_detail", pk=job.pk)

            except Exception as e:
                logger.error("Error editing job: %s", e)
                messages.error(request, f"Xatolik yuz berdi: {str(e)}")
        else:
            messages.error(request, _("Iltimos, xatolarni to'g'rilang."))
    else:
        form = form_class(instance=job, user=request.user)
        form.fields['company'].queryset = available_companies.distinct()

    context["form"] = form
    return render(request, template_name, context)


@login_required
def job_delete(request, pk):
    """Vakansiyani o'chirish"""
    job = get_object_or_404(Job, pk=pk)
    is_job_admin = user_has_admin_permission(request.user, "can_manage_jobs")

    if request.user.is_employer:
        try:
            EmployerProfile.objects.get(user=request.user)
        except EmployerProfile.DoesNotExist:
            messages.error(request, _("Ish beruvchi profili topilmadi."))
            return redirect("jobs:list")
        available_companies = Company.objects.filter(owner=request.user, is_active=True)
    elif is_job_admin:
        available_companies = Company.objects.filter(is_active=True)
    else:
        messages.error(request, _("Sizda bu vakansiyani o'chirish huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    if job.company not in available_companies:
        messages.error(request, _("Sizda bu vakansiyani o'chirish huquqi yo'q."))
        return redirect("jobs:job_detail", pk=pk)

    if request.method == "POST":
        job_title = job.title
        job.delete()
        messages.success(
            request, _(f"'{job_title}' vakansiyasi muvaffaqiyatli o'chirildi.")
        )
        if request.user.is_employer:
            return redirect("jobs:my_jobs")
        return redirect("jobs:list")

    return render(request, "jobs/job_confirm_delete.html", {"job": job})


@login_required
def my_jobs(request):
    """Мои вакансии (для работодателей) и мои заявки (для студентов)"""
    context = {}

    if request.user.is_employer:
        try:
            employer_profile = EmployerProfile.objects.get(user=request.user)
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
            jobs = Job.objects.filter(company__in=user_companies)

            company_id = request.GET.get('company_id')
            filtered_company = None
            if company_id:
                try:
                    filtered_company = Company.objects.get(id=company_id, owner=request.user)
                    jobs = jobs.filter(company=filtered_company)
                except Company.DoesNotExist:
                    pass
        except EmployerProfile.DoesNotExist:
            messages.error(request, _("Ish beruvchi profili topilmadi."))
            return redirect("accounts:employer_profile_update")
        except Exception as e:
            logger.error("Error in my_jobs view: %s", e)
            jobs = Job.objects.none()
            messages.error(request, _("Ma'lumotlarni yuklashda xatolik yuz berdi."))

        status_filter = request.GET.get('status')
        if status_filter == 'active':
            jobs = jobs.filter(is_active=True)
        elif status_filter == 'draft':
            jobs = jobs.filter(is_active=False)

        search_query = request.GET.get('q')
        if search_query:
            jobs = jobs.filter(title__icontains=search_query)

        sort_by = request.GET.get('sort_by')
        if sort_by == 'title_asc':
            jobs = jobs.order_by('title')
        elif sort_by == 'title_desc':
            jobs = jobs.order_by('-title')
        elif sort_by == 'date_asc':
            jobs = jobs.order_by('created_at')
        elif sort_by == 'date_desc':
            jobs = jobs.order_by('-created_at')
        elif sort_by == 'applications':
            jobs = jobs.annotate(app_count=Count('applications')).order_by('-app_count')
        elif sort_by == 'views':
            jobs = jobs.order_by('-views_count')
        else:
            jobs = jobs.order_by('-created_at')

        total_jobs = jobs.count()
        active_jobs = jobs.filter(is_active=True).count()
        draft_jobs = jobs.filter(is_active=False).count()
        total_views = jobs.aggregate(total=Sum('views_count'))['total'] or 0
        total_applications_count = JobApplication.objects.filter(job__company__in=user_companies).count()

        paginator = Paginator(jobs, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        for job in page_obj:
            job.applications_count = JobApplication.objects.filter(job=job).count()

        context.update({
            'jobs': page_obj,
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'draft_jobs': draft_jobs,
            'total_views': total_views,
            'total_applications_count': total_applications_count,
            'status_filter': status_filter,
            'sort_by': sort_by,
            'search_query': search_query,
            'is_employer_view': True,
            'user_companies': user_companies,
            'owned_companies': user_companies,
            'filtered_company': filtered_company,
            'employer_profile': employer_profile,
        })

    elif _is_student_or_alumni(request.user):
        applications = JobApplication.objects.filter(user=request.user).select_related('job', 'job__company').order_by('-created_at')

        sort_by = request.GET.get('sort_by')
        if sort_by == 'date_asc':
            applications = applications.order_by('created_at')
        elif sort_by == 'date_desc':
            applications = applications.order_by('-created_at')
        elif sort_by == 'job_title_asc':
            applications = applications.order_by('job__title')
        elif sort_by == 'job_title_desc':
            applications = applications.order_by('-job__title')

        total_applications = applications.count()
        pending_applications = applications.filter(status='applied').count()
        reviewed_applications = applications.filter(status='reviewed').count()
        interview_applications = applications.filter(status='interview').count()
        accepted_applications = applications.filter(status='hired').count()
        rejected_applications = applications.filter(status='rejected').count()

        paginator = Paginator(applications, 10)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)

        context.update({
            'applications': page_obj,
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'reviewed_applications': reviewed_applications,
            'interview_applications': interview_applications,
            'accepted_applications': accepted_applications,
            'rejected_applications': rejected_applications,
            'sort_by': sort_by,
            'is_employer_view': False,
        })
    else:
        messages.error(request, _("У вас нет доступа к этой странице"))
        return redirect('accounts:home')

    return render(request, 'jobs/my_jobs.html', context)


@login_required
def saved_jobs(request):
    """Saqlangan vakansiyalar"""
    if not _is_student_or_alumni(request.user):
        messages.error(request, _("Sizda bu sahifani ko'rish huquqi yo'q"))
        return redirect("accounts:home")

    saved_jobs_qs = (
        SavedJob.objects.filter(user=request.user)
        .select_related("job", "job__company")
        .order_by("-created_at")
    )

    paginator = Paginator(saved_jobs_qs, 12)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    saved_job_items = list(page_obj.object_list)
    saved_job_ids = [item.job_id for item in saved_job_items]
    viewed_job_ids = set(
        ViewedJob.objects.filter(user=request.user, job_id__in=saved_job_ids).values_list("job_id", flat=True)
    )

    for item in saved_job_items:
        item.job.is_viewed = item.job_id in viewed_job_ids

    context = {
        "saved_jobs": page_obj,
        "total_saved": saved_jobs_qs.count(),
        "viewed_jobs_count": ViewedJob.objects.filter(user=request.user).count(),
    }
    return render(request, "jobs/saved_jobs.html", context)


@login_required
def job_list(request):
    """Vakansiyalar ro'yxati"""
    form = JobSearchForm(request.GET or None)
    is_employer_user = getattr(request.user, "is_employer", False)
    is_admin_user = (
        user_has_admin_permission(request.user, "can_manage_jobs")
        or user_has_admin_permission(request.user, "can_create_jobs")
    )

    if is_admin_user or is_employer_user:
        jobs = Job.objects.all()
    else:
        jobs = Job.objects.filter(is_active=True)

    query = request.GET.get("query", "").strip()
    job_market = request.GET.get("job_market", "").strip()
    employment_type = request.GET.get("employment_type", "").strip()
    experience_level = request.GET.get("experience_level", "").strip()
    industry = request.GET.get("industry", "").strip()
    work_types = request.GET.getlist("work_type")
    salary_range = request.GET.get("salary_range", "").strip()
    date_posted = request.GET.get("date_posted", "").strip()

    valid_job_markets = {choice[0] for choice in Job.JOB_MARKET_CHOICES}
    if job_market in valid_job_markets:
        jobs = jobs.filter(job_market=job_market)

    if query:
        jobs = jobs.filter(
            Q(title__icontains=query)
            | Q(short_description__icontains=query)
            | Q(description__icontains=query)
            | Q(company__name__icontains=query)
            | Q(skills_required__icontains=query)
        )

    if employment_type:
        jobs = jobs.filter(employment_type=employment_type)

    if experience_level:
        jobs = jobs.filter(experience_level=experience_level)

    if industry:
        jobs = jobs.filter(industry__icontains=industry)

    if work_types:
        jobs = jobs.filter(work_type__in=work_types)

    if salary_range == "0-3000000":
        jobs = jobs.filter(Q(salary_min__lte=3000000) | Q(salary_max__lte=3000000))
    elif salary_range == "3000000-6000000":
        jobs = jobs.filter(
            Q(salary_min__gte=3000000, salary_min__lte=6000000)
            | Q(salary_max__gte=3000000, salary_max__lte=6000000)
        )
    elif salary_range == "6000000-10000000":
        jobs = jobs.filter(
            Q(salary_min__gte=6000000, salary_min__lte=10000000)
            | Q(salary_max__gte=6000000, salary_max__lte=10000000)
        )
    elif salary_range == "10000000+":
        jobs = jobs.filter(Q(salary_min__gte=10000000) | Q(salary_max__gte=10000000))

    if date_posted == "today":
        jobs = jobs.filter(created_at__date=timezone.now().date())
    elif date_posted == "week":
        jobs = jobs.filter(created_at__gte=timezone.now() - timedelta(days=7))
    elif date_posted == "month":
        jobs = jobs.filter(created_at__gte=timezone.now() - timedelta(days=30))

    sort = request.GET.get("sort", "newest")
    if sort in {"salary_high", "salary"}:
        jobs = jobs.order_by("-salary_max", "-salary_min")
    elif sort == "salary_low":
        jobs = jobs.order_by("salary_min", "salary_max")
    elif sort == "views":
        jobs = jobs.order_by("-views_count")
    elif sort == "applications":
        jobs = jobs.annotate(applications_count=Count("applications")).order_by("-applications_count")
    elif sort == "deadline":
        jobs = jobs.order_by("expires_at")
    else:
        jobs = jobs.order_by("-created_at")

    paginator = Paginator(jobs, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_jobs = jobs.count()

    featured_jobs = []
    is_student_or_alumni = _is_student_or_alumni(request.user)
    if is_student_or_alumni or request.user.is_staff:
        featured_jobs = Job.objects.filter(is_active=True, is_featured=True)[:5]

    page_jobs, _saved_job_ids, _viewed_job_ids = _attach_job_state(request.user, page_obj.object_list)
    page_obj.object_list = page_jobs

    all_industries = Job.objects.filter(
        is_active=True,
        industry__isnull=False
    ).exclude(industry='').values_list('industry', flat=True).distinct().order_by('industry')

    companies_count = Company.objects.filter(jobs__is_active=True, is_active=True).distinct().count()

    query_params = request.GET.copy()
    query_params.pop("page", None)

    context = {
        "jobs": page_obj,
        "page_obj": page_obj,
        "form": form,
        "total_jobs": total_jobs,
        "featured_jobs": featured_jobs,
        "employment_types": Job.EMPLOYMENT_TYPE_CHOICES,
        "industries": list(all_industries),
        "experience_levels": Job.EXPERIENCE_LEVEL_CHOICES,
        "stats": {
            "total_jobs": Job.objects.filter(is_active=True).count() if not is_admin_user else Job.objects.count(),
            "internships_count": Job.objects.filter(employment_type='internship', is_active=True).count(),
            "companies_count": companies_count,
            "success_stories": JobApplication.objects.filter(status='hired').count(),
        },
        "is_admin": is_admin_user,
        "is_employer": is_employer_user,
        "is_student": is_student_or_alumni,
        "saved_jobs_count": SavedJob.objects.filter(user=request.user).count() if is_student_or_alumni else 0,
        "viewed_jobs_count": ViewedJob.objects.filter(user=request.user).count() if is_student_or_alumni else 0,
        "filters": {
            "query": query,
            "job_market": job_market,
            "employment_type": employment_type,
            "experience_level": experience_level,
            "industry": industry,
            "work_types": work_types,
            "salary_range": salary_range,
            "date_posted": date_posted,
            "sort": sort,
        },
        "query_string": query_params.urlencode(),
    }
    return render(request, "jobs/job_list.html", context)


@login_required
def job_detail(request, pk):
    """Vakansiya batafsil sahifasi"""
    is_student_or_alumni = _is_student_or_alumni(request.user)
    is_admin_user = (
        request.user.is_staff
        or request.user.is_superuser
        or user_has_admin_permission(request.user, "can_manage_jobs")
        or user_has_admin_permission(request.user, "can_create_jobs")
    )

    job_queryset = Job.objects.select_related("company")
    if is_admin_user or request.user.is_employer:
        job = get_object_or_404(job_queryset, pk=pk)
    elif is_student_or_alumni:
        job = get_object_or_404(job_queryset, pk=pk, is_active=True)
    else:
        messages.error(request, _("Sizda bu vakansiyani ko'rish huquqi yo'q."))
        return redirect("accounts:login")

    is_viewed = False
    if request.user.is_authenticated:
        viewed_job, created = ViewedJob.objects.get_or_create(user=request.user, job=job)
        if created:
            job.views_count += 1
            job.save(update_fields=["views_count"])
        else:
            ViewedJob.objects.filter(pk=viewed_job.pk).update(last_viewed_at=timezone.now())
        is_viewed = True
    else:
        viewed_jobs = request.session.get('viewed_jobs', [])
        if pk not in viewed_jobs:
            job.views_count += 1
            job.save(update_fields=["views_count"])
            viewed_jobs.append(pk)
            request.session['viewed_jobs'] = viewed_jobs

    has_applied = False
    application = None
    if request.user.is_authenticated:
        try:
            application = JobApplication.objects.get(job=job, user=request.user)
            has_applied = True
        except JobApplication.DoesNotExist:
            pass

    is_saved = False
    if is_student_or_alumni:
        is_saved = SavedJob.objects.filter(job=job, user=request.user).exists()

    application_form = JobApplicationForm() if is_student_or_alumni else None

    similar_jobs = []
    if job.is_active:
        if job.industry:
            similar_jobs = Job.objects.filter(is_active=True, industry__icontains=job.industry).exclude(pk=job.pk)[:4]
        else:
            similar_jobs = Job.objects.filter(is_active=True, experience_level=job.experience_level).exclude(pk=job.pk)[:4]

    can_edit = False
    if request.user.is_authenticated:
        if user_has_admin_permission(request.user, "can_manage_jobs"):
            can_edit = True
        elif request.user.is_employer:
            try:
                EmployerProfile.objects.get(user=request.user)
                user_companies = Company.objects.filter(owner=request.user, is_active=True)
                can_edit = job.company in user_companies
            except EmployerProfile.DoesNotExist:
                can_edit = False

    company_additional_info = getattr(job.company, "additional_info", None)

    context = {
        "job": job,
        "has_applied": has_applied,
        "application": application,
        "is_saved": is_saved,
        "is_viewed": is_viewed,
        "is_student_or_alumni": is_student_or_alumni,
        "application_form": application_form,
        "similar_jobs": similar_jobs,
        "can_edit": can_edit,
        "company_additional_info": company_additional_info,
    }
    return render(request, "jobs/job_detail.html", context)


@require_POST
def increment_job_views(request, pk):
    """Vakansiya ko'rishlar sonini oshirish (AJAX)"""
    job = get_object_or_404(Job, pk=pk)

    if request.user.is_authenticated:
        viewed_job, created = ViewedJob.objects.get_or_create(user=request.user, job=job)
        if created:
            job.views_count += 1
            job.save(update_fields=["views_count"])
    else:
        viewed_jobs = request.session.get('viewed_jobs', [])
        if pk not in viewed_jobs:
            job.views_count += 1
            job.save(update_fields=["views_count"])
            viewed_jobs.append(pk)
            request.session['viewed_jobs'] = viewed_jobs

    return JsonResponse({"success": True, "views_count": job.views_count})


@login_required
def apply_for_job(request, pk):
    """Vakansiyaga ariza topshirish"""
    has_student_profile = request.user.user_type == "student"
    has_alumni_profile = request.user.user_type == "alumni"

    if not (has_student_profile or has_alumni_profile):
        messages.error(request, _("Faqat talabalar va bitiruvchilar ariza topshira oladi."))
        return redirect("jobs:list")

    job = get_object_or_404(Job, pk=pk, is_active=True)

    allowed, error = job.can_user_apply(request.user)
    if not allowed:
        messages.error(request, error)
        return redirect("jobs:job_detail", pk=job.pk)

    if JobApplication.objects.filter(job=job, user=request.user).exists():
        messages.warning(request, _("Siz ushbu vakansiyaga allaqachon ariza topshirgansiz."))
        return redirect("jobs:job_detail", pk=job.pk)

    if job.expires_at and job.expires_at < timezone.now():
        messages.error(request, _("This vacancy has expired."))
        return redirect("jobs:job_detail", pk=job.pk)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, user=request.user, job=job)
        if form.is_valid():
            try:
                with transaction.atomic():
                    application = form.save(commit=False)
                    application.job = job
                    application.user = request.user
                    application.save()

                    job.applications_count += 1
                    job.save()

                messages.success(request, _("Your application has been sent successfully!"))
                return redirect("jobs:job_detail", pk=job.pk)
            except Exception as e:
                logger.error("Application processing failed: %s", e)
                messages.error(request, f"An error occurred: {str(e)}")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = JobApplicationForm(user=request.user, job=job)

    return render(request, "jobs/apply_for_job.html", {"job": job, "form": form})


@login_required
@require_POST
def save_job(request, pk):
    """Vakansiyani saqlash"""
    job = get_object_or_404(Job, pk=pk, is_active=True)

    if not _is_student_or_alumni(request.user):
        return JsonResponse({"success": False, "error": "Permission denied"})

    _saved_job, created = SavedJob.objects.get_or_create(job=job, user=request.user)
    saved_jobs_count = SavedJob.objects.filter(user=request.user).count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "action": "saved" if created else "already_saved",
            "saved": True,
            "saved_jobs_count": saved_jobs_count,
        })

    if created:
        messages.success(request, _("Vacancy saved successfully!"))
    else:
        messages.info(request, _("The vacancy has already been saved."))

    next_url = _get_safe_next_url(request)
    if next_url:
        return redirect(next_url)

    return redirect("jobs:job_detail", pk=job.pk)


@login_required
@require_POST
def unsave_job(request, pk):
    """Vakansiyani saqlanganlardan o'chirish"""
    job = get_object_or_404(Job, pk=pk)

    if not _is_student_or_alumni(request.user):
        return JsonResponse({"success": False, "error": "Permission denied"})

    deleted_count, _ = SavedJob.objects.filter(job=job, user=request.user).delete()
    saved_jobs_count = SavedJob.objects.filter(user=request.user).count()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "success": True,
            "action": "unsaved",
            "saved": False,
            "saved_jobs_count": saved_jobs_count,
        })

    next_url = _get_safe_next_url(request, default=reverse("jobs:saved_jobs"))
    if next_url:
        return redirect(next_url)

    return redirect("jobs:job_detail", pk=job.pk)


@login_required
def my_applications(request):
    """Mening arizalarim"""
    applications = (
        JobApplication.objects.filter(user=request.user)
        .select_related("job", "job__company")
        .order_by("-created_at")
    )

    status_filter = request.GET.get("status")
    if status_filter in dict(JobApplication.STATUS_CHOICES):
        applications = applications.filter(status=status_filter)

    user_applications = JobApplication.objects.filter(user=request.user)
    stats = {
        'total': user_applications.count(),
        'applied': user_applications.filter(status="applied").count(),
        'reviewed': user_applications.filter(status="reviewed").count(),
        'shortlisted': user_applications.filter(status="shortlisted").count(),
        'interview': user_applications.filter(status="interview").count(),
        'hired': user_applications.filter(status="hired").count(),
        'rejected': user_applications.filter(status="rejected").count(),
    }

    context = {
        "applications": applications,
        "stats": stats,
        "status_filter": status_filter,
        "status_choices": JobApplication.STATUS_CHOICES,
    }
    return render(request, "jobs/my_applications.html", context)


@login_required
def update_application_status(request, pk):
    """Ariza statusini yangilash (AJAX)"""
    if request.method == "POST" and request.headers.get("X-Requested-With") == "XMLHttpRequest":
        application = get_object_or_404(JobApplication, pk=pk)

        try:
            EmployerProfile.objects.get(user=request.user)
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
        except EmployerProfile.DoesNotExist:
            return JsonResponse({"success": False, "error": "Permission denied"})

        if application.job.company not in user_companies and not request.user.is_staff:
            return JsonResponse({"success": False, "error": "Permission denied"})

        new_status = request.POST.get("status")
        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()

            return JsonResponse({
                "success": True,
                "new_status": application.get_status_display(),
                "status_class": new_status,
            })
    return JsonResponse({"success": False})


@login_required
def get_user_cvs(request):
    """Foydalanuvchi rezyumelarini olish (AJAX)"""
    from cvbuilder.models import CV

    has_student_profile = request.user.user_type == "student"
    has_alumni_profile = request.user.user_type == "alumni"

    if not (has_student_profile or has_alumni_profile):
        return JsonResponse({"error": "Permission denied"}, status=403)

    cvs = CV.objects.filter(user=request.user, status="published")
    cv_list = [{"id": cv.id, "title": cv.title, "full_name": cv.full_name} for cv in cvs]

    return JsonResponse({"cvs": cv_list})


@login_required
def application_detail(request, pk):
    """Ariza batafsil (AJAX uchun)"""
    application = get_object_or_404(JobApplication, pk=pk)
    is_owner = application.user == request.user
    is_employer_allowed = False

    if request.user.is_employer:
        try:
            EmployerProfile.objects.get(user=request.user)
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
            is_employer_allowed = application.job.company in user_companies
        except EmployerProfile.DoesNotExist:
            is_employer_allowed = False

    if not (is_owner or is_employer_allowed or request.user.is_staff):
        return JsonResponse({"error": "Ruxsat rad etildi"}, status=403)

    student_certificates = []
    student_profile = application.user
    if student_profile is not None:
        student_certificates = get_viewable_student_certificates_queryset(request.user, student_profile)

    context = {
        "application": application,
        "is_employer": is_employer_allowed,
        "student_certificates": student_certificates,
    }
    return render(request, "jobs/application_detail.html", context)


@login_required
@require_POST
def add_application_note(request, pk):
    """Arizaga izoh qo'shish (AJAX)"""
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        application = get_object_or_404(JobApplication, pk=pk)

        try:
            EmployerProfile.objects.get(user=request.user)
            # ИСПРАВЛЕНО: фильтрация по owner=request.user, а не по объекту профиля
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
        except EmployerProfile.DoesNotExist:
            return JsonResponse({"success": False, "error": "Ruxsat rad etildi"})

        if application.job.company not in user_companies and not request.user.is_staff:
            return JsonResponse({"success": False, "error": "Ruxsat rad etildi"})

        note = request.POST.get("note")
        if note:
            ApplicationNote.objects.create(
                application=application,
                author=request.user,
                note=note
            )
            return JsonResponse({"success": True})
        return JsonResponse({"success": False, "error": "Izoh kiritish majburiy"})

    return JsonResponse({"success": False, "error": "Noto'g'ri so'rov"})


@login_required
def job_settings(request, pk):
    """Get job settings for modal"""
    job = get_object_or_404(Job, pk=pk)
    can_edit = False

    if user_has_admin_permission(request.user, "can_manage_jobs"):
        can_edit = True
    elif request.user.is_employer:
        try:
            EmployerProfile.objects.get(user=request.user)
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
            can_edit = job.company in user_companies
        except EmployerProfile.DoesNotExist:
            can_edit = False

    if not can_edit:
        return JsonResponse({"success": False, "error": "Permission denied"})

    return JsonResponse({
        "success": True,
        "is_urgent": job.is_urgent,
        "is_active": job.is_active,
    })


@login_required
@require_POST
def update_job_settings(request, pk):
    """Update job settings from modal"""
    job = get_object_or_404(Job, pk=pk)
    can_edit = False

    if user_has_admin_permission(request.user, "can_manage_jobs"):
        can_edit = True
    elif request.user.is_employer:
        try:
            EmployerProfile.objects.get(user=request.user)
            user_companies = Company.objects.filter(owner=request.user, is_active=True)
            can_edit = job.company in user_companies
        except EmployerProfile.DoesNotExist:
            can_edit = False

    if not can_edit:
        return JsonResponse({"success": False, "error": "Permission denied"})

    job.is_urgent = request.POST.get('is_urgent') == 'on'
    job.is_active = request.POST.get('is_active') == 'on'
    job.save()

    return JsonResponse({
        "success": True,
        "is_urgent": job.is_urgent,
        "is_active": job.is_active,
    })


@login_required
def dashboard_statistics(request):
    """Dashboard statistikasi"""
    if not request.user.is_employer:
        return JsonResponse({"error": "Permission denied"}, status=403)

    try:
        EmployerProfile.objects.get(user=request.user)
    except EmployerProfile.DoesNotExist:
        return JsonResponse({"error": "Employer profile not found"}, status=403)

    user_companies = Company.objects.filter(owner=request.user, is_active=True)
    jobs = Job.objects.filter(company__in=user_companies)
    
    total_jobs = jobs.count()
    active_jobs = jobs.filter(is_active=True).count()
    draft_jobs = jobs.filter(is_active=False).count()

    applications = JobApplication.objects.filter(job__company__in=user_companies)
    total_applications = applications.count()
    application_status_stats = applications.values('status').annotate(count=Count('id'))
    total_views = jobs.aggregate(total=Sum('views_count'))['total'] or 0

    recent_applications = applications.select_related('user', 'job').order_by('-created_at')[:5]
    recent_applications_list = [
        {
            'id': app.id,
            'job_title': app.job.title,
            'applicant_name': app.user.get_full_name() or app.user.username,
            'status': app.status,
            'created_at': app.created_at.strftime('%d.%m.%Y %H:%M'),
        }
        for app in recent_applications
    ]

    return JsonResponse({
        'success': True,
        'stats': {
            'total_jobs': total_jobs,
            'active_jobs': active_jobs,
            'draft_jobs': draft_jobs,
            'total_applications': total_applications,
            'total_views': total_views,
            'companies_count': user_companies.count(),
        },
        'application_status_stats': list(application_status_stats),
        'recent_applications': recent_applications_list,
    })