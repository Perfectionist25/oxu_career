import json
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, JsonResponse
from django.db.models import Q, Count, F, Case, When, Value, IntegerField, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth import update_session_auth_hash
from django.core.cache import cache
from django.contrib.auth.forms import UserCreationForm
from django import forms
from django.utils.crypto import get_random_string
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.response import Response

from accounts.models import (
    ADMIN_USER_TYPES,
    CustomUser,
    StudentProfile,
    StudentCertificate,
    EmployerProfile,
    AdminProfile,
    Company,
    CompanyDocument,
    UserActivity,
    Notification,
    CompanyAdditionalInfo,
    is_admin_user,
    is_main_admin_user,
    user_has_admin_permission,
)
from .certificates import (
    can_user_view_student_certificate,
    get_viewable_student_certificates_queryset,
)
from .oauth_utils import remember_oauth_redirect_uri

from jobs.models import Job, JobApplication, SavedJob, ViewedJob
from cvbuilder.models import CV
from events.models import Event, EventParticipation
from resources.models import Resource
from .middleware import BruteForceProtectionMiddleware
from .forms import (
    StudentProfileForm, EmployerProfileForm,
    AdminProfileForm, CompanyForm, CompanyDocumentForm,
    EmployerRegistrationForm, AdminCompanyForm, AdminEmployerProfileForm,
    StudentCertificateForm, StudentUserReadonlyNameForm,
    EmployerLoginForm, AdminLoginForm, SelfEmployerRegisterForm,
)

import logging
from django.db import transaction

logger = logging.getLogger(__name__)

ORGINFO_BASE_URL = "https://orginfo.uz"
ORGINFO_SEARCH_URL = "https://orginfo.uz/ru/search/organizations/?q="


def _normalize_text(value):
    return " ".join(value.split()).strip() if value else ""


def _find_pair(parts, key):
    try:
        index = parts.index(key)
        return parts[index + 1].strip()
    except (ValueError, IndexError):
        return None


def _parse_orginfo_search(html):
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for link in soup.select('a.og-card[href^="/ru/organization/"]'):
        inn_tag = link.select_one("span.bg-success")
        inn = _normalize_text(inn_tag.get_text()) if inn_tag else None
        title_tag = link.select_one("h6.card-title")
        name = _normalize_text(title_tag.get_text()) if title_tag else _normalize_text(link.get_text())
        address_tag = link.select_one("p.text-body-tertiary")
        address = _normalize_text(address_tag.get_text()) if address_tag else None
        date_tag = link.select_one("span.text-body-tertiary")
        created_at = _normalize_text(date_tag.get_text()) if date_tag else None
        detail_url = urljoin(ORGINFO_BASE_URL, link["href"])
        results.append({
            "name": name,
            "inn": inn,
            "address": address,
            "created_at": created_at,
            "detail_url": detail_url,
        })
    return results


def _parse_orginfo_company(html):
    soup = BeautifulSoup(html, "html.parser")
    parsed = {
        "name": "",
        "company_type": "",
        "description": "",
        "short_description": "",
        "industry": "",
        "founded_year": None,
        "address": "",
        "email": "",
        "phone": "",
        "website": "",
    }
    name_tag = soup.find("h1")
    if name_tag:
        parsed["name"] = _normalize_text(name_tag.get_text())

    first_block = None
    for div in soup.select("div.card-body"):
        if "Официальное название организации" in div.get_text():
            first_block = div
            break
    if first_block:
        text = _normalize_text(first_block.get_text(separator="|"))
        parts = [part.strip() for part in text.split("|") if part.strip()]
        parsed["description"] = _find_pair(parts, "Официальное название организации") or parsed["name"]
        parsed["short_description"] = _find_pair(parts, "Краткое название организации") or parsed["short_description"]
        parsed["company_type"] = _find_pair(parts, "ОПФ") or parsed["company_type"]
        parsed["industry"] = _find_pair(parts, "Деятельность в области компьютерного программирования") or _find_pair(parts, "ОКЭД") or parsed["industry"]
        registration = _find_pair(parts, "Дата регистрации")
        if registration:
            import re
            match = re.search(r"(\d{2})\.(\d{2})\.(\d{4})", registration)
            if match:
                parsed["founded_year"] = int(match.group(3))
        if not parsed["company_type"] and parsed["name"]:
            if "ООО" in parsed["name"]:
                parsed["company_type"] = "ООО"

    contact_block = None
    for div in soup.select("div.card-body.py-3"):
        if "Контактные данные" in div.get_text():
            contact_block = div
            break
    if contact_block:
        contact_text = _normalize_text(contact_block.get_text(separator="|"))
        parts = [part.strip() for part in contact_text.split("|") if part.strip()]
        parsed["email"] = _find_pair(parts, "Электронная почта") or parsed["email"]
        parsed["phone"] = _find_pair(parts, "Номер телефона") or parsed["phone"]
        parsed["address"] = _find_pair(parts, "Адрес") or parsed["address"]
        parsed["website"] = _find_pair(parts, "Веб-сайт") or _find_pair(parts, "Интернет сайт") or parsed["website"]

    if not parsed["short_description"]:
        parsed["short_description"] = parsed["description"]
    return parsed


def _orginfo_error_response(message, status=502):
    return JsonResponse({"success": False, "message": message}, status=status)


@login_required
@require_http_methods(["GET"])
def search_orginfo_company(request):
    inn = request.GET.get("inn", "").strip()
    if not inn:
        return _orginfo_error_response("INN is required", 400)
    try:
        response = requests.get(
            f"{ORGINFO_SEARCH_URL}{requests.utils.quote(inn)}",
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OxuCareerBot/1.0)"},
        )
        response.raise_for_status()
        results = _parse_orginfo_search(response.text)
        return JsonResponse({"success": True, "companies": results})
    except requests.RequestException:
        return _orginfo_error_response("Unable to query orginfo.uz.")


@login_required
@require_http_methods(["GET"])
def fetch_orginfo_company_details(request):
    detail_url = request.GET.get("detail_url", "").strip()
    if not detail_url:
        return _orginfo_error_response("Detail URL is required", 400)
    if not detail_url.startswith("http"):
        detail_url = urljoin(ORGINFO_BASE_URL, detail_url)
    try:
        response = requests.get(
            detail_url,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0 (compatible; OxuCareerBot/1.0)"},
        )
        response.raise_for_status()
        company = _parse_orginfo_company(response.text)
        company["detail_url"] = detail_url
        return JsonResponse({"success": True, "company": company})
    except requests.RequestException:
        return _orginfo_error_response("Unable to fetch organization details.")

# ------------------------------------------------------------------------------
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ------------------------------------------------------------------------------
def get_client_ip(request=None):
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def create_user_activity(user, activity_type, description="", ip_address=None,
                        user_agent="", related_company=None):
    try:
        activity = UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address or get_client_ip(),
            user_agent=user_agent or "",
        )
        if related_company:
            activity.related_company = related_company
            activity.save()
        return activity
    except Exception as e:
        print(f"Error creating activity: {e}")
        return None

def employer_register(request):
    if request.user.is_authenticated:
        return redirect("accounts:home_redirect")

    if request.method == "POST":
        form = SelfEmployerRegisterForm(request.POST, request=request)
        if form.is_valid():
            user = form.save()
            user.backend = settings.AUTHENTICATION_BACKENDS[0]
            login(request, user)

            create_user_activity(
                user,
                "profile_update",
                _("Employer registered via self-service form"),
                get_client_ip(request),
                request.META.get("HTTP_USER_AGENT", "")
            )

            messages.success(request, _("Registration successful! You are now logged in."))
            return redirect("accounts:employer_dashboard")
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SelfEmployerRegisterForm(request=request)

    return render(request, "accounts/employer_register.html", {"form": form})


def handle_oauth_user_login(request, oauth_data):
    """
    Синхронизирует данные из OAuth payload с моделями CustomUser и StudentProfile.
    """
    oauth_uid = oauth_data.get("uid") or oauth_data.get("id")
    username = oauth_data.get("username") or f"user_{oauth_uid}"
    email = oauth_data.get("email")

    if not oauth_uid:
        raise ValueError("OAuth payload does not contain a unique user identifier.")

    with transaction.atomic():
        user, created = CustomUser.objects.get_or_create(
            oauth_uid=oauth_uid,
            defaults={
                "username": username,
                "email": email,
                "user_type": "student",
            }
        )

        # Обновляем базовые данные пользователя, если не заблокировано
        if not user.oauth_data_locked:
            user.oauth_provider = "university_oauth"
            user.oauth_last_synced = timezone.now()

            raw_gender = str(oauth_data.get("gender", "")).lower()
            if raw_gender in ["male", "1", "m"]:
                user.gender = "male"
            elif raw_gender in ["female", "2", "f"]:
                user.gender = "female"

            user.phone_number = oauth_data.get("phone_number")
            user.save()

        # Синхронизация StudentProfile
        profile, profile_created = StudentProfile.objects.get_or_create(user=user)

        profile.student_id = oauth_data.get("student_id", "")
        profile.university = oauth_data.get("university_name", "")
        profile.faculty = oauth_data.get("faculty_name", "")
        profile.specialty = oauth_data.get("specialty_name", "")
        profile.specialty_code = oauth_data.get("specialty_code", "")
        profile.course_year = oauth_data.get("course_level", "")
        profile.education_level = oauth_data.get("education_level", "")
        profile.status = oauth_data.get("status", "student")
        profile.graduation_year = int(oauth_data.get("graduation_year")) if oauth_data.get("graduation_year") else None
        profile.father_name = oauth_data.get("patronymic", "")
        profile.phone_number = user.phone_number

        # OAuth‑специфичные поля
        profile.oauth_university = oauth_data.get("university_name", "")
        profile.oauth_degree = oauth_data.get("degree_name", "")
        profile.oauth_specialization = oauth_data.get("specialty_name", "")
        raw_gpa = oauth_data.get("gpa")
        profile.oauth_gpa = float(raw_gpa) if raw_gpa else None
        if oauth_data.get("enrollment_year"):
            profile.oauth_enrollment_year = int(oauth_data.get("enrollment_year"))
        profile.oauth_last_synced = timezone.now()

        profile.save()

    return user


def oauth_login(request):
    state = get_random_string(40)
    request.session["oauth_state"] = state
    request.session["oauth_next"] = request.GET.get("next", settings.OAUTH_SUCCESS_REDIRECT)
    request.session.set_expiry(getattr(settings, "OAUTH_STATE_TTL", 600))
    redirect_uri = remember_oauth_redirect_uri(request)

    params = {
        "response_type": "code",
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "scope": settings.OAUTH_SCOPE,
        "state": state,
    }
    url = settings.OAUTH_AUTHORIZE_URL + "?" + urlencode(params)
    return redirect(url)


class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        if user.user_type == 'student':
            raise serializers.ValidationError({
                "detail": "Студенты должны использовать OAuth авторизацию через /oauth/login/"
            })

        data.update({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'user_type': user.user_type,
            'first_name': user.first_name,
            'last_name': user.last_name,
        })
        return data


class CustomTokenObtainView(TokenObtainPairView):
    serializer_class = CustomTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        ip_address = get_client_ip(request)
        username = str(request.data.get("username", "")).strip() if hasattr(request, "data") else ""

        status = BruteForceProtectionMiddleware.get_block_status(ip_address, username or None)
        if status["is_blocked"]:
            return Response(
                {
                    "detail": _("Too many login attempts. Try again later."),
                    "blocked_until": status["blocked_until"].isoformat() if status["blocked_until"] else None,
                    "remaining_seconds": status["remaining_seconds"],
                },
                status=429,
            )

        response = super().post(request, *args, **kwargs)

        if response.status_code == 200 and username:
            BruteForceProtectionMiddleware.clear_attempts(ip_address, username)
        elif username and response.status_code >= 400:
            result = BruteForceProtectionMiddleware.record_failed_attempt(ip_address, username)
            if not result["allowed"]:
                return Response(
                    {
                        "detail": _("Too many login attempts. Try again later."),
                        "remaining_seconds": result["remaining_seconds"],
                    },
                    status=429,
                )

        return response


# ------------------------------------------------------------------------------
# Вспомогательные проверки прав
# ------------------------------------------------------------------------------
def is_student(user):
    return user.is_authenticated and getattr(user, "user_type", None) == "student"

def is_student_or_alumni(user):
    return user.is_authenticated and getattr(user, "user_type", None) in ["student", "alumni"]

def is_employer(user):
    return user.is_authenticated and getattr(user, "user_type", None) == "employer"

def is_admin(user):
    return is_admin_user(user)

def is_main_admin(user):
    return is_main_admin_user(user)

def can_manage_employers(user):
    return user_has_admin_permission(user, "can_manage_employers")

def can_create_employers(user):
    return user_has_admin_permission(user, "can_create_employers")

def can_change_user_status(user):
    return user_has_admin_permission(user, "can_change_user_status")

def can_manage_students(user):
    return user_has_admin_permission(user, "can_manage_students")

def can_manage_companies(user):
    return user_has_admin_permission(user, "can_manage_companies")

def can_view_company_details(user):
    return user_has_admin_permission(user, "can_view_company_details")

def can_verify_companies(user):
    return user_has_admin_permission(user, "can_verify_companies")

def can_change_company_status(user):
    return user_has_admin_permission(user, "can_change_company_status")

def can_manage_jobs(user):
    return user_has_admin_permission(user, "can_manage_jobs")

def can_create_jobs(user):
    return user_has_admin_permission(user, "can_create_jobs")

def can_manage_resumes(user):
    return user_has_admin_permission(user, "can_manage_resumes")

def can_manage_events(user):
    return user_has_admin_permission(user, "can_manage_events")

def can_view_statistics(user):
    return user_has_admin_permission(user, "can_view_statistics")

def managed_user_types_for_admin(user):
    if not is_admin(user):
        return set()

    if is_main_admin(user):
        return set(ADMIN_USER_TYPES) | {"student", "employer"}

    managed_types = set()
    if can_manage_students(user):
        managed_types.add("student")
    if (
        can_manage_employers(user)
        or can_create_employers(user)
        or can_manage_companies(user)
        or can_view_company_details(user)
        or can_verify_companies(user)
        or can_change_company_status(user)
    ):
        managed_types.add("employer")

    return managed_types

def can_view_managed_user(user, target_user):
    if not getattr(user, "is_authenticated", False):
        return False

    if user.id == target_user.id:
        return True

    if is_main_admin(user):
        return True

    if not is_admin(user):
        return False

    return target_user.user_type in managed_user_types_for_admin(user)

def can_change_managed_user_status(user, target_user):
    if not can_change_user_status(user):
        return False

    if target_user.user_type in ADMIN_USER_TYPES:
        return False

    return can_view_managed_user(user, target_user)

def can_manage_users(user):
    return bool(managed_user_types_for_admin(user) or is_main_admin(user))


# ------------------------------------------------------------------------------
# Основные представления
# ------------------------------------------------------------------------------
def home(request):
    if request.user.is_authenticated:
        return home_redirect(request)

    context = {
        "total_companies": Company.objects.filter(is_active=True, is_verified=True).count(),
        "active_jobs": Job.objects.filter(is_active=True, expires_at__gte=timezone.now()).count(),
        "total_resumes": CV.objects.filter(status='published').count(),
        "featured_companies": Company.objects.filter(is_active=True, is_verified=True).order_by('-views')[:6],
        "recent_jobs": Job.objects.filter(is_active=True, expires_at__gte=timezone.now()).order_by('-created_at')[:6],
        "upcoming_events": Event.objects.filter(event_date__gte=timezone.now()).order_by('event_date')[:3],
    }

    return render(request, "home.html", context)


def home_redirect(request):
    if request.user.is_authenticated:
        user_type = getattr(request.user, "user_type", None)

        if user_type in ["student", "alumni"]:
            return redirect("accounts:student_dashboard")
        elif user_type == "employer":
            return redirect("accounts:employer_dashboard")
        elif user_type in ADMIN_USER_TYPES:
            return redirect("accounts:admin_dashboard")

    return redirect("home")


def employer_login(request):
    if request.user.is_authenticated and request.user.user_type == "employer":
        return redirect("accounts:employer_dashboard")

    ip_address = get_client_ip(request)
    form = EmployerLoginForm(request=request, data=request.POST or None)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        status = BruteForceProtectionMiddleware.get_block_status(ip_address, username or None)
        if status["is_blocked"]:
            return BruteForceProtectionMiddleware.blocked_response(
                request,
                ip_address=ip_address,
                username=username,
                reason=status["reason"],
                remaining_seconds=status["remaining_seconds"],
            )

        if form.is_valid():
            user = form.user
            if not user.is_active:
                messages.error(request, "Ваш аккаунт деактивирован. Обратитесь к администратору.")
                return render(request, "accounts/employer_login.html", {"form": form})

            login(request, user)

            BruteForceProtectionMiddleware.clear_attempts(ip_address, username)

            create_user_activity(user, "login", "Employer logged in", ip_address,
                               request.META.get("HTTP_USER_AGENT", ""))

            messages.success(request, "Добро пожаловать!")
            return redirect("accounts:employer_dashboard")
        attempt_result = BruteForceProtectionMiddleware.record_failed_attempt(ip_address, username or None)
        if not attempt_result["allowed"]:
            return BruteForceProtectionMiddleware.blocked_response(
                request,
                ip_address=ip_address,
                username=username,
                reason="ip_blocked",
                remaining_seconds=attempt_result["remaining_seconds"],
            )
        if attempt_result["warning_message"]:
            messages.warning(request, attempt_result["warning_message"])
        else:
            for error in form.non_field_errors():
                messages.error(request, error)

    return render(request, "accounts/employer_login.html", {"form": form})


def admin_login(request):
    """Admin login page with brute force protection"""

    if request.user.is_authenticated and request.user.user_type in ADMIN_USER_TYPES:
        return redirect("accounts:admin_dashboard")

    ip_address = get_client_ip(request)
    form = AdminLoginForm(request=request, data=request.POST or None)

    if request.method == "POST":
        username = request.POST.get("username", "").strip()

        status = BruteForceProtectionMiddleware.get_block_status(ip_address, username or None)
        if status["is_blocked"]:
            return BruteForceProtectionMiddleware.blocked_response(
                request,
                ip_address=ip_address,
                username=username,
                reason=status["reason"],
                remaining_seconds=status["remaining_seconds"],
            )

        if not form.is_valid():
            attempt_result = BruteForceProtectionMiddleware.record_failed_attempt(ip_address, username or None)
            if not attempt_result["allowed"]:
                return BruteForceProtectionMiddleware.blocked_response(
                    request,
                    ip_address=ip_address,
                    username=username,
                    reason="ip_blocked",
                    remaining_seconds=attempt_result["remaining_seconds"],
                )
            if attempt_result["warning_message"]:
                messages.warning(request, attempt_result["warning_message"])
            else:
                for error in form.non_field_errors():
                    messages.error(request, error)
            return render(request, "accounts/admin_login.html", {"form": form})

        user = form.user

        if not user.is_active:
            messages.error(request, "Ваш аккаунт деактивирован. Обратитесь к главному администратору.")
            return render(request, "accounts/admin_login.html", {"form": form})

        login(request, user)

        BruteForceProtectionMiddleware.clear_attempts(ip_address, username)

        create_user_activity(
            user,
            "login",
            f"Admin logged in: {username}",
            ip_address,
            request.META.get("HTTP_USER_AGENT", "")
        )

        messages.success(request, "Добро пожаловать в админ-панель!")
        return redirect("accounts:admin_dashboard")

    return render(request, "accounts/admin_login.html", {"form": form})


def admin_logout(request):
    """Admin logout with enhanced security"""
    if request.user.is_authenticated:
        create_user_activity(
            request.user,
            "logout",
            f"Admin logged out: {request.user.username}",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")
        )

    logout(request)

    request.session.flush()

    messages.success(request, _("You have been logged out successfully"))
    return redirect("accounts:admin_login")


@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def admin_session_management(request):
    """View and manage admin sessions (main admin only)"""

    from django.contrib.sessions.models import Session
    from django.utils import timezone

    active_sessions = []
    now = timezone.now()

    admins = CustomUser.objects.filter(user_type__in=ADMIN_USER_TYPES)

    for session in Session.objects.filter(expire_date__gt=now):
        session_data = session.get_decoded()
        user_id = session_data.get('_auth_user_id')

        if user_id:
            try:
                user = CustomUser.objects.get(id=user_id)
                if user in admins:
                    active_sessions.append({
                        'user': user,
                        'session_key': session.session_key,
                        'expire_date': session.expire_date,
                        'last_activity': session_data.get('last_activity', 'Unknown'),
                    })
            except CustomUser.DoesNotExist:
                pass

    context = {
        'active_sessions': active_sessions,
        'total_sessions': len(active_sessions),
    }

    return render(request, "accounts/admin_session_management.html", context)


@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def terminate_admin_session(request, session_key):
    """Terminate specific admin session (main admin only)"""
    try:
        session = Session.objects.get(session_key=session_key)
        session.delete()
        messages.success(request, _("Session terminated successfully"))
    except Session.DoesNotExist:
        messages.error(request, _("Session not found"))

    return redirect("accounts:admin_session_management")

@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_two_factor_setup(request):
    """Setup two-factor authentication for admin"""

    context = {
        'two_factor_enabled': False,
        'setup_complete': False,
    }

    return render(request, "accounts/admin_two_factor_setup.html", context)

@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_login_history(request):
    """View admin login history"""
    login_activities = UserActivity.objects.filter(
        user=request.user,
        activity_type__in=["login", "failed_login", "logout"]
    ).order_by('-created_at')[:50]

    return render(request, "accounts/admin_login_history.html", {
        'activities': login_activities,
        'total_logins': UserActivity.objects.filter(
            user=request.user,
            activity_type="login"
        ).count(),
        'failed_logins': UserActivity.objects.filter(
            user=request.user,
            activity_type="failed_login"
        ).count(),
    })



def hemis_login(request):
    """Student login via external OAuth microservice"""
    def normalize_gender(value):
        if value is None:
            return None
        normalized = str(value).strip().lower()
        if normalized in {"female", "f", "1", "true", "qw" , "qiz"}:
            return "female"
        if normalized in {"male", "m", "0", "false", "erkak"}:
            return "male"
        return None

    def normalize_status(value):
        if value is None:
            return "student"
        normalized = str(value).strip().lower()
        if normalized in {"1", "true", "yes", "bitiruvchi", "graduate", "graduated", "alumni"}:
            return "graduate"
        return "student"

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, _("Please provide username and password"))
            return render(request, "accounts/hemis_login.html")

        try:
            url = settings.OAUTH_MICROSERVICE_URL.rstrip('/') + '/authenticate/'
            headers = {'Authorization': f"Bearer {settings.OAUTH_SERVICE_TOKEN}"} if settings.OAUTH_SERVICE_TOKEN else {}
            resp = requests.post(url, json={"username": username, "password": password},
                                 headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
        except Exception:
            messages.error(request, _("Authentication service is temporarily unavailable."))
            return render(request, "accounts/hemis_login.html")

        if not data.get("success"):
            messages.error(request, _("Invalid username or password"))
            return render(request, "accounts/hemis_login.html")

        user_data = data.get("user", {})
        allowed = getattr(settings, 'OAUTH_ALLOWED_UNIVERSITIES', [])
        university = user_data.get("university")

        if allowed and university and university not in allowed:
            messages.error(request, _("Your university is not allowed to register/login here."))
            return render(request, "accounts/hemis_login.html")

        full_name = (
            user_data.get("full_name")
            or user_data.get("fio")
            or f"{user_data.get('ism', '')} {user_data.get('fam', '')}".strip()
            or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        )

        first_name = ""
        last_name = ""
        if full_name:
            parts = full_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        oauth_uid = user_data.get("user_id") or user_data.get("login") or username
        raw_username = user_data.get("login") or f"hemis_{oauth_uid}"
        local_username = raw_username
        counter = 1
        while CustomUser.objects.filter(username=local_username).exclude(oauth_uid=oauth_uid).exists():
            local_username = f"{raw_username}_{counter}"
            counter += 1

        email = user_data.get("email", "") or ""
        gender = normalize_gender(user_data.get("jinsi") or user_data.get("gender"))
        
        bitiruvchi_value = user_data.get("bitiruvchi")
        if bitiruvchi_value is not None:
            try:
                bitiruvchi_int = int(bitiruvchi_value)
                user_type = "alumni" if bitiruvchi_int == 1 else "student"
            except (TypeError, ValueError):
                user_type = "student"
        else:
            user_type = "student"

        # Создание/обновление пользователя
        user, created = CustomUser.objects.update_or_create(
            oauth_uid=str(oauth_uid),
            defaults={
                "username": local_username,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "user_type": user_type,
                "is_active": True,
                "oauth_provider": "hemis",
                "oauth_data_locked": True,
                "gender": gender,
                "phone_number": user_data.get("phone_number") or None,
            },
        )

        # Обновление StudentProfile
        profile, _ = StudentProfile.objects.get_or_create(user=user)
        profile.student_id = user_data.get("student_id") or user_data.get("login") or ""
        profile.university = user_data.get("university") or user_data.get("universitetining_nomi") or ""
        profile.faculty = user_data.get("fakultet") or user_data.get("faculty") or ""
        profile.specialty = user_data.get("yunalish_nomi") or user_data.get("specialty") or ""
        profile.education_level = user_data.get("education_level") or ""
        profile.status = normalize_status(user_data.get("status") or user_data.get("bitiruvchi"))
        if user_data.get("graduation_year"):
            try:
                profile.graduation_year = int(user_data.get("graduation_year"))
            except (TypeError, ValueError):
                pass
        profile.father_name = user_data.get("patronymic") or ""
        profile.phone_number = user.phone_number

        # OAuth‑поля
        profile.oauth_university = profile.university
        profile.oauth_degree = user_data.get("degree") or user_data.get("darajasi") or ""
        profile.oauth_specialization = user_data.get("specialty") or user_data.get("yunalish_nomi") or ""
        gpa_value = user_data.get("gpa") or user_data.get("o'rtacha") or user_data.get("ortacha")
        if gpa_value:
            try:
                profile.oauth_gpa = float(gpa_value)
            except (TypeError, ValueError):
                pass
        enrollment_value = user_data.get("enrollment_year") or user_data.get("yilga_qabul_qilingan")
        if enrollment_value:
            try:
                profile.oauth_enrollment_year = int(enrollment_value)
            except (TypeError, ValueError):
                pass
        profile.oauth_last_synced = timezone.now()
        profile.save()

        login(request, user)
        create_user_activity(user, "login", "Student logged in via OAuth",
                             get_client_ip(request), request.META.get("HTTP_USER_AGENT", ""))
        messages.success(request, _("Logged in successfully"))
        return redirect("accounts:student_dashboard")

    return render(request, "accounts/hemis_login.html")



def hemis_callback(request):
    messages.info(request, _("Please use the login form to authenticate"))
    return redirect("accounts:hemis_login")

def temp_student_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, _("Please provide username and password"))
            return render(request, "accounts/temp_student_login.html")

        user = authenticate(request, username=username, password=password)

        if user is not None and getattr(user, "user_type", None) == "student":
            login(request, user)
            create_user_activity(user, "login", "Student logged in (temp)",
                               get_client_ip(request), request.META.get("HTTP_USER_AGENT", ""))
            messages.success(request, _("Logged in successfully"))
            return redirect("accounts:student_dashboard")
        else:
            messages.error(request, _("Invalid credentials or not authorized as student"))
            return render(request, "accounts/temp_student_login.html")

    return render(request, "accounts/temp_student_login.html")


@require_http_methods(["GET", "POST"])
def logout_view(request):
    if request.user.is_authenticated:
        try:
            create_user_activity(request.user, "logout", "User logged out")
        except Exception as e:
            print(f"Error creating user activity: {e}")

    logout(request)
    messages.success(request, _("You have been logged out"))

    response = redirect("core:home")
    access_cookie = getattr(settings, "OAUTH_ACCESS_COOKIE_NAME", "student_access")
    refresh_cookie = getattr(settings, "OAUTH_REFRESH_COOKIE_NAME", "student_refresh")
    response.delete_cookie(access_cookie)
    response.delete_cookie(refresh_cookie)
    return response


@login_required
@user_passes_test(is_student_or_alumni, login_url="accounts:employer_login")
def student_dashboard(request):
    resumes = CV.objects.filter(user=request.user)
    student_profile = StudentProfile.objects.filter(user=request.user).first()
    applications = JobApplication.objects.filter(user=request.user)
    saved_jobs = SavedJob.objects.filter(user=request.user).select_related("job", "job__company")
    viewed_jobs = ViewedJob.objects.filter(user=request.user).select_related("job", "job__company")
    certificates = request.user.certificates.order_by("-uploaded_at")
    recent_event_participations = EventParticipation.objects.filter(
        user=request.user
    ).select_related("event").order_by("-registered_at")[:5]
    saved_job_ids = set(saved_jobs.values_list("job_id", flat=True))
    recent_viewed_jobs = list(
        viewed_jobs.filter(job__is_active=True).order_by("-last_viewed_at")[:5]
    )

    for item in recent_viewed_jobs:
        item.job.is_saved = item.job_id in saved_job_ids

    # Рекомендованные вакансии на основе специальности из профиля
    specialty = student_profile.specialty if student_profile else ""
    recommended_jobs = Job.objects.filter(
        is_active=True, expires_at__gte=timezone.now()
    ).filter(
        Q(title__icontains=specialty) | Q(description__icontains=specialty)
    )[:5] if specialty else Job.objects.none()

    context = {
        "student_profile": student_profile,          # <-- добавили
        "stats": {
            "resumes_created": resumes.count(),
            "active_resumes": resumes.filter(status='published').count(),
            "jobs_applied": applications.count(),
            "pending_applications": applications.filter(status="applied").count(),
            "accepted_applications": applications.filter(status="hired").count(),
            "profile_views": student_profile.profile_views if student_profile else 0,
            "certificates_uploaded": certificates.count(),
            "saved_jobs": saved_jobs.count(),
            "viewed_jobs": viewed_jobs.count(),
        },
        "recent_applications": applications.select_related('job', 'job__company').order_by('-created_at')[:5],
        "recommended_jobs": recommended_jobs,
        "recent_activity": UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        "recent_activities": UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        "recent_notifications": Notification.objects.filter(user=request.user).order_by("-created_at")[:5],
        "resumes": resumes,
        "recent_event_participations": recent_event_participations,
        "recent_certificates": certificates[:3],
        "recent_viewed_jobs": recent_viewed_jobs,
    }

    return render(request, "accounts/student_dashboard.html", context)


@login_required
def student_profile_update(request):
    if request.user.user_type not in ["student", "alumni"]:
        return redirect("accounts:login")

    student_profile = StudentProfile.objects.get_or_create(user=request.user)[0]

    if request.method == "POST":
        user_form = StudentUserReadonlyNameForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()

            create_user_activity(request.user, "profile_update", "Student profile updated")
            messages.success(request, _("Profile updated successfully!"))
            return redirect("accounts:student_profile_update")
    else:
        user_form = StudentUserReadonlyNameForm(instance=request.user)
        profile_form = StudentProfileForm(instance=student_profile)

    return render(request, "accounts/student_profile_update.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })

@login_required
@user_passes_test(is_student_or_alumni, login_url="accounts:employer_login")
def student_certificate_list(request):
    certificates = request.user.certificates.order_by("-uploaded_at")
    return render(request, "accounts/student_certificate_list.html", {"certificates": certificates})

@login_required
@user_passes_test(is_student_or_alumni, login_url="accounts:employer_login")
def student_certificate_create(request):
    if request.method == "POST":
        form = StudentCertificateForm(request.POST, request.FILES)
        if form.is_valid():
            certificate = form.save(commit=False)
            certificate.student = request.user
            certificate.save()
            create_user_activity(request.user, "certificate_upload", f"Uploaded certificate: {certificate.title}", ip_address=get_client_ip(request))
            messages.success(request, _("Certificate uploaded successfully."))
            return redirect("accounts:student_certificate_list")
    else:
        form = StudentCertificateForm()
    return render(request, "accounts/student_certificate_form.html", {
        "form": form,
        "page_title": _("Upload Certificate"),
        "submit_label": _("Save Certificate"),
        "is_edit": False,
    })



@login_required
@user_passes_test(is_student_or_alumni, login_url="accounts:employer_login")
def student_certificate_update(request, pk):
    certificate = get_object_or_404(StudentCertificate, pk=pk, student=request.user)
    if request.method == "POST":
        form = StudentCertificateForm(request.POST, request.FILES, instance=certificate)
        if form.is_valid():
            certificate = form.save()
            create_user_activity(request.user, "certificate_update", f"Updated certificate: {certificate.title}", ip_address=get_client_ip(request))
            messages.success(request, _("Certificate updated successfully."))
            return redirect("accounts:student_certificate_list")
    else:
        form = StudentCertificateForm(instance=certificate)
    return render(request, "accounts/student_certificate_form.html", {
        "form": form,
        "certificate": certificate,
        "page_title": _("Edit Certificate"),
        "submit_label": _("Update Certificate"),
        "is_edit": True,
    })



@login_required
@user_passes_test(is_student_or_alumni, login_url="accounts:employer_login")
@require_http_methods(["POST"])
def student_certificate_delete(request, pk):
    certificate = get_object_or_404(StudentCertificate, pk=pk, student=request.user)
    certificate_title = certificate.title
    certificate.delete()
    create_user_activity(request.user, "certificate_delete", f"Deleted certificate: {certificate_title}", ip_address=get_client_ip(request))
    messages.success(request, _("Certificate deleted successfully."))
    next_url = request.POST.get("next")
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return redirect(next_url)
    return redirect("accounts:student_certificate_list")


@login_required
def student_certificate_file(request, pk):
    certificate = get_object_or_404(StudentCertificate.objects.select_related("student"), pk=pk)
    if not certificate.student:
        raise Http404(_("Certificate owner not found."))
    if not can_user_view_student_certificate(request.user, certificate):
        raise PermissionDenied
    if not certificate.file or not certificate.file.storage.exists(certificate.file.name):
        raise Http404(_("Certificate file not found."))
    download = request.GET.get("download") in {"1", "true", "yes"}
    try:
        certificate_handle = certificate.file.open("rb")
    except FileNotFoundError as exc:
        raise Http404(_("Certificate file not found.")) from exc
    response = FileResponse(certificate_handle, as_attachment=download, filename=certificate.download_filename, content_type=certificate.content_type)
    if not download:
        response["Content-Disposition"] = f'inline; filename="{certificate.download_filename}"'
    return response


@login_required
@user_passes_test(is_student, login_url="accounts:hemis_login")
def student_search(request):
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    salary_min = request.GET.get('salary_min', '')

    jobs = Job.objects.filter(is_active=True, expires_at__gte=timezone.now())

    if query:
        jobs = jobs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if location:
        jobs = jobs.filter(Q(location__icontains=location) | Q(company__location__icontains=location))

    if salary_min:
        try:
            jobs = jobs.filter(salary_min__gte=int(salary_min))
        except ValueError:
            pass

    paginator = Paginator(jobs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'accounts/student_search.html', {
        'page_obj': page_obj,
        'query': query,
        'location': location,
        'salary_min': salary_min,
    })



@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_dashboard(request):
    employer_profile, created = EmployerProfile.objects.get_or_create(user=request.user)
    owned_companies = Company.objects.filter(owner=request.user, is_active=True)

    # Теперь первичная компания хранится в employer_profile.company (ForeignKey)
    primary_company = None
    company_id = request.GET.get('company_id')

    if company_id:
        try:
            primary_company = owned_companies.get(id=company_id)
        except Company.DoesNotExist:
            pass

    if not primary_company:
        # используем company (или свойство primary_company)
        if employer_profile.company and employer_profile.company in owned_companies:
            primary_company = employer_profile.company
        elif owned_companies.exists():
            primary_company = owned_companies.first()

    # Если текущая первичная компания неактивна, сбрасываем её
    if primary_company and not primary_company.is_active:
        employer_profile.company = None
        employer_profile.save()
        primary_company = None
        if owned_companies.exists():
            primary_company = owned_companies.first()

    if primary_company:
        active_jobs = Job.objects.filter(company=primary_company, is_active=True).count()
        total_applications = JobApplication.objects.filter(job__company=primary_company).count()
        profile_views = primary_company.total_views or 0
    else:
        active_jobs = Job.objects.filter(company__owner=request.user, is_active=True).count()
        total_applications = JobApplication.objects.filter(job__company__owner=request.user).count()
        profile_views = Company.objects.filter(owner=request.user).aggregate(total=Sum('total_views'))['total'] or 0

    stats = {
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'profile_views': profile_views,
    }

    recent_event_participations = EventParticipation.objects.filter(
        user=request.user
    ).select_related("event").order_by("-registered_at")[:5]

    context = {
        'employer_profile': employer_profile,
        'primary_company': primary_company,
        'owned_companies': owned_companies,
        'stats': stats,
        'recent_jobs': Job.objects.filter(company__owner=request.user).order_by('-created_at')[:5],
        'recent_applications': JobApplication.objects.filter(job__company__owner=request.user).select_related('user', 'job').order_by('-created_at')[:5],
        'recent_activity': UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5],
        'recent_event_participations': recent_event_participations,
    }

    return render(request, 'accounts/employer_dashboard.html', context)



@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_profile_update(request):
    """Update employer profile"""
    employer_profile, created = EmployerProfile.objects.get_or_create(user=request.user)

    # Простая форма для базовых полей CustomUser
    class BasicUserForm(forms.ModelForm):
        class Meta:
            model = CustomUser
            fields = ["email", "phone_number", "date_of_birth"]
            widgets = {
                "email": forms.EmailInput(attrs={'class': 'form-control'}),
                "phone_number": forms.TextInput(attrs={'class': 'form-control'}),
                "date_of_birth": forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            }

    if request.method == "POST":
        user_form = BasicUserForm(request.POST, instance=request.user)
        profile_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            create_user_activity(request.user, "profile_update", "Employer profile updated")
            messages.success(request, _("Profile updated successfully!"))
            return redirect("accounts:employer_dashboard")
    else:
        user_form = BasicUserForm(instance=request.user)
        profile_form = EmployerProfileForm(instance=employer_profile)

    return render(request, "accounts/employer_profile_update.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })

@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_stats(request):
    companies = Company.objects.filter(owner=request.user, is_active=True)
    total_jobs = Job.objects.filter(company__in=companies).count()
    active_jobs = Job.objects.filter(company__in=companies, is_active=True).count()
    total_applications = JobApplication.objects.filter(job__company__in=companies).count()

    context = {
        'companies': companies,
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'total_companies': companies.count(),
    }

    return render(request, 'accounts/employer_stats.html', context)

@login_required
def set_primary_company(request, pk):
    if not is_employer(request.user):
        return redirect("accounts:employer_login")
    try:
        company = Company.objects.get(pk=pk, owner=request.user)
        employer_profile, created = EmployerProfile.objects.get_or_create(user=request.user)
        employer_profile.company = company          # <-- было employer_profile.primary_company_id = company
        employer_profile.save()
        messages.success(request, _("Primary company set successfully"))
    except Company.DoesNotExist:
        messages.error(request, _("Company not found"))
    return redirect("accounts:employer_dashboard")

class CompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = Company
    template_name = 'accounts/company_list.html'
    context_object_name = 'owned_companies'

    def test_func(self):
        return is_employer(self.request.user)

    def get_queryset(self):
        return Company.objects.filter(
            owner=self.request.user,
            is_active=True
        ).annotate(
            job_count=Count('jobs'),
            active_job_count=Count('jobs', filter=Q(jobs__is_active=True))
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['total_jobs'] = Job.objects.filter(company__owner=self.request.user).count()
        context['active_jobs_count'] = Job.objects.filter(
            company__owner=self.request.user, is_active=True
        ).count()
        context['pending_applications'] = JobApplication.objects.filter(
            job__company__owner=self.request.user, status='pending'
        ).count()

        # В get_context_data():
        try:
            context['primary_company'] = self.request.user.employer_profile.company
        except EmployerProfile.DoesNotExist:
            context['primary_company'] = None

        return context



class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Company
    template_name = 'accounts/company_form.html'
    form_class = CompanyForm

    def test_func(self):
        return is_employer(self.request.user)

    def form_valid(self, form):
        had_companies_before = Company.objects.filter(owner=self.request.user).exists()
        form.instance.owner = self.request.user
        form.instance.is_verified = True
        form.instance.is_active = True

        company = form.save()

        if not had_companies_before:
            try:
                employer_profile = self.request.user.employer_profile
                employer_profile.company = company
                employer_profile.save()
            except EmployerProfile.DoesNotExist:
                pass

        create_user_activity(self.request.user, "company_create", f"Created company: {company.name}",
                           related_company=company)
        messages.success(self.request, _("Company created successfully!"))
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('accounts:employer_dashboard')


class CompanyDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Company
    template_name = 'accounts/company_detail.html'
    context_object_name = 'company'

    def test_func(self):
        company = self.get_object()
        return company.owner == self.request.user or is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        company = self.get_object()

        jobs = Job.objects.filter(company=company).annotate(
            application_count=Count('applications')
        ).order_by('-created_at')

        total_applications = JobApplication.objects.filter(job__company=company).count()
        pending_applications = JobApplication.objects.filter(
            job__company=company, status='pending'
        ).count()

        is_primary = False
        if self.request.user.user_type == 'employer':
            try:
                employer_profile = self.request.user.employer_profile
                is_primary = (employer_profile.company == company)
            except EmployerProfile.DoesNotExist:
                pass

        context.update({
            'jobs': jobs,
            'active_jobs': jobs.filter(is_active=True).count(),
            'total_jobs': jobs.count(),
            'total_applications': total_applications,
            'pending_applications': pending_applications,
            'documents': company.documents.filter(is_verified=True),
            'is_owner': company.owner == self.request.user,
            'is_primary': is_primary,
            'tags_list': [tag.strip() for tag in company.tags.split(',') if tag.strip()] if company.tags else [],
        })

        return context


class CompanyUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Company
    template_name = 'accounts/company_form.html'
    form_class = CompanyForm

    def test_func(self):
        company = self.get_object()
        return (
            company.owner == self.request.user
            or user_has_admin_permission(self.request.user, "can_manage_companies")
        )

    def form_valid(self, form):
        response = super().form_valid(form)
        company = self.object
        create_user_activity(self.request.user, "company_update", f"Updated company: {company.name}",
                           related_company=company)
        messages.success(self.request, _("Company updated successfully!"))
        return response

    def get_success_url(self):
        return reverse_lazy('accounts:company_detail', kwargs={'pk': self.object.pk})


class CompanyDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Company
    template_name = 'accounts/company_confirm_delete.html'

    def test_func(self):
        company = self.get_object()
        return (
            company.owner == self.request.user
            or user_has_admin_permission(self.request.user, "can_manage_companies")
        )

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        company_name = self.object.name

        EmployerProfile.objects.filter(company=self.object).update(company=None)

        try:
            employer_profile = request.user.employer_profile
            if employer_profile.company == self.object:
                other_companies = Company.objects.filter(
                    owner=request.user, is_active=True
                ).exclude(id=self.object.id)
                if other_companies.exists():
                    employer_profile.company = other_companies.first()
                else:
                    employer_profile.primary_company_id = None
                employer_profile.save()
        except EmployerProfile.DoesNotExist:
            pass

        self.object.is_active = False
        self.object.save()

        create_user_activity(request.user, "company_delete", f"Deleted company: {company_name}",
                           related_company=self.object)
        messages.success(request, _('Company "%(name)s" has been deleted.') % {'name': company_name})

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy('accounts:company_list')



@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def set_primary_company(request, pk):
    company = get_object_or_404(Company, pk=pk, owner=request.user, is_active=True)

    try:
        employer_profile = request.user.employer_profile
        employer_profile.primary_company_id = company
        employer_profile.save()

        create_user_activity(request.user, "company_update", f"Set {company.name} as primary company",
                           related_company=company)
        messages.success(request, f'{company.name} is now your primary company.')
    except EmployerProfile.DoesNotExist:
        messages.error(request, 'Employer profile not found.')

    return redirect('accounts:company_detail', pk=pk)


@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def company_documents(request, pk):
    company = get_object_or_404(Company, pk=pk, owner=request.user)

    if request.method == "POST":
        form = CompanyDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.company = company
            document.uploaded_by = request.user
            document.save()
            messages.success(request, _("Document uploaded successfully!"))
            return redirect("accounts:company_documents", pk=company.pk)
    else:
        form = CompanyDocumentForm()

    return render(request, "accounts/company_documents.html", {
        "company": company,
        "form": form,
        "documents": company.documents.all(),
    })


@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def company_statistics(request, pk):
    company = get_object_or_404(Company, pk=pk, owner=request.user)

    jobs = Job.objects.filter(company=company)
    applications = JobApplication.objects.filter(job__company=company)

    context = {
        'company': company,
        'active_jobs': jobs.filter(is_active=True).count(),
        'expired_jobs': jobs.filter(expires_at__lt=timezone.now()).count(),
        'total_jobs': jobs.count(),
        'application_stats': {
            'total': applications.count(),
            'pending': applications.filter(status='pending').count(),
            'reviewed': applications.filter(status='reviewed').count(),
            'shortlisted': applications.filter(status='shortlisted').count(),
            'rejected': applications.filter(status='rejected').count(),
            'accepted': applications.filter(status='accepted').count(),
        },
        'total_views': getattr(company, 'total_views', 0) or 0,
    }

    return render(request, 'accounts/company_statistics.html', context)


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_dashboard(request):
    admin_profile, _ = AdminProfile.objects.get_or_create(user=request.user)
    today = timezone.now().date()
    permissions = {
        "can_create_admins": request.user.is_main_admin,
        "can_manage_user_directory": can_manage_users(request.user),
        "can_manage_employers": can_manage_employers(request.user),
        "can_create_employers": can_create_employers(request.user),
        "can_manage_companies": any(
            (
                can_manage_companies(request.user),
                can_view_company_details(request.user),
                can_verify_companies(request.user),
                can_change_company_status(request.user),
            )
        ),
        "can_manage_jobs": can_manage_jobs(request.user),
        "can_create_jobs": can_create_jobs(request.user),
        "can_manage_resumes": can_manage_resumes(request.user),
        "can_manage_events": can_manage_events(request.user),
        "can_view_statistics": can_view_statistics(request.user),
    }

    context = {
        "admin_profile": admin_profile,
        "permissions": permissions,
        "stats": {
            "total_users": CustomUser.objects.count(),
            "total_students": CustomUser.objects.filter(user_type="student").count(),
            "total_employers": CustomUser.objects.filter(user_type="employer").count(),
            "total_companies": Company.objects.filter(is_active=True).count(),
            "verified_companies": Company.objects.filter(is_verified=True, is_active=True).count(),
            "active_today": UserActivity.objects.filter(
                created_at__date=today, activity_type="login"
            ).values("user").distinct().count(),
            "total_jobs": Job.objects.count(),
            "active_jobs": Job.objects.filter(is_active=True).count(),
        },
        "recent_activities": UserActivity.objects.select_related("user", "related_company").order_by("-created_at")[:10],
        "companies_pending": Company.objects.filter(is_verified=False, is_active=True).order_by("-created_at")[:5],
        "recent_applications": JobApplication.objects.select_related("user", "job", "job__company").order_by("-created_at")[:5],
    }

    return render(request, "accounts/admin_dashboard.html", context)


@login_required
@user_passes_test(can_view_statistics, login_url="accounts:admin_login")
def admin_statistics(request):
    now = timezone.now()
    period_starts = {
        "day": now - timedelta(days=1),
        "week": now - timedelta(days=7),
        "month": now - timedelta(days=30),
        "quarter": now - timedelta(days=90),
    }

    users_qs = CustomUser.objects.all()
    users_total = users_qs.count()
    users_students = users_qs.filter(user_type="student").count()
    users_alumni = users_qs.filter(user_type="alumni").count()
    users_employers = users_qs.filter(user_type="employer").count()
    users_admins = users_qs.filter(user_type="admin").count()
    users_international_admins = users_qs.filter(user_type="international_admin").count()
    users_main_admins = users_qs.filter(user_type="main_admin").count()
    users_guests = users_qs.filter(user_type="guest").count()
    users_other = users_total - (
        users_students
        + users_alumni
        + users_employers
        + users_admins
        + users_international_admins
        + users_main_admins
        + users_guests
    )

    resources_qs = Resource.objects.all()
    events_qs = Event.objects.all()
    jobs_qs = Job.objects.all()
    cvs_qs = CV.objects.all()

    context = {
        "generated_at": now,
        "users": {
            "total": users_total,
            "students": users_students,
            "alumni": users_alumni,
            "employers": users_employers,
            "admins": users_admins,
            "international_admins": users_international_admins,
            "main_admins": users_main_admins,
            "guests": users_guests,
            "other": users_other,
            "new": {
                key: users_qs.filter(date_joined__gte=start).count()
                for key, start in period_starts.items()
            },
        },
        "resources": {
            "total": resources_qs.count(),
            "published": resources_qs.filter(is_published=True).count(),
            "unpublished": resources_qs.filter(is_published=False).count(),
            "new": {
                key: resources_qs.filter(created_at__gte=start).count()
                for key, start in period_starts.items()
            },
        },
        "events": {
            "total": events_qs.count(),
            "published": events_qs.filter(status="published").count(),
            "draft": events_qs.filter(status="draft").count(),
            "cancelled": events_qs.filter(status="cancelled").count(),
            "completed": events_qs.filter(status="completed").count(),
            "upcoming": events_qs.filter(start_date__gt=now).count(),
            "ongoing": events_qs.filter(start_date__lte=now, end_date__gte=now).count(),
            "past": events_qs.filter(end_date__lt=now).count(),
            "new": {
                key: events_qs.filter(created_at__gte=start).count()
                for key, start in period_starts.items()
            },
        },
        "jobs": {
            "total": jobs_qs.count(),
            "active": jobs_qs.filter(is_active=True).count(),
            "new": {
                key: jobs_qs.filter(created_at__gte=start).count()
                for key, start in period_starts.items()
            },
        },
        "cvs": {
            "total": cvs_qs.count(),
            "published": cvs_qs.filter(status="published").count(),
            "draft": cvs_qs.filter(status="draft").count(),
            "archived": cvs_qs.filter(status="archived").count(),
            "new": {
                key: cvs_qs.filter(created_at__gte=start).count()
                for key, start in period_starts.items()
            },
        },
    }

    return render(request, "accounts/admin_statistics.html", context)

@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def admin_management(request):
    if not is_main_admin(request.user):
        messages.error(request, _("Access denied"))
        return redirect("accounts:admin_dashboard")

    admins = CustomUser.objects.filter(user_type__in=ADMIN_USER_TYPES).order_by("-date_joined")
    return render(request, "accounts/admin_management.html", {
        "admins": admins,
        "total_admins": admins.count(),
        "international_admins_count": admins.filter(user_type="international_admin").count(),
        "main_admins_count": admins.filter(user_type="main_admin").count(),
    })

@login_required
@user_passes_test(can_manage_companies, login_url="accounts:admin_login")
def admin_company_management(request):
    search_query = request.GET.get("q", "")
    verification_filter = request.GET.get("verification", "all")
    active_filter = request.GET.get("active", "all")

    companies = Company.objects.select_related("owner").all()

    if search_query:
        companies = companies.filter(
            Q(name__icontains=search_query) |
            Q(owner__username__icontains=search_query) |
            Q(owner__email__icontains=search_query)
        )

    if verification_filter == "verified":
        companies = companies.filter(is_verified=True)
    elif verification_filter == "pending":
        companies = companies.filter(is_verified=False)

    if active_filter == "active":
        companies = companies.filter(is_active=True)
    elif active_filter == "inactive":
        companies = companies.filter(is_active=False)

    company_stats = []
    for company in companies:
        company_stats.append({
            "company": company,
            "jobs_count": Job.objects.filter(company=company).count(),
            "active_jobs": Job.objects.filter(company=company, is_active=True).count(),
        })

    paginator = Paginator(company_stats, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/admin_company_management.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "verification_filter": verification_filter,
        "active_filter": active_filter,
        "total_companies": companies.count(),
        "can_view_company_details": can_view_company_details(request.user),
        "can_verify_companies": can_verify_companies(request.user),
        "can_change_company_status": can_change_company_status(request.user),
    })

@login_required
@user_passes_test(can_verify_companies, login_url="accounts:admin_login")
def toggle_company_verification(request, pk):
    if request.method == "POST":
        company = get_object_or_404(Company, pk=pk)
        company.is_verified = not company.is_verified
        company.save()

        action = "verified" if company.is_verified else "unverified"
        create_user_activity(request.user, "company_update", f"Company {action}: {company.name}",
                           related_company=company)

        Notification.objects.create(
            user=company.owner,
            notification_type="company_verification",
            title=f"Company {action}",
            message=f"Your company {company.name} has been {action}.",
            related_company=company,
        )
        messages.success(request, _(f"Company {action}"))

    return redirect("accounts:admin_company_management")

@login_required
@user_passes_test(can_change_company_status, login_url="accounts:admin_login")
def toggle_company_status(request, pk):
    if request.method == "POST":
        company = get_object_or_404(Company, pk=pk)
        company.is_active = not company.is_active
        company.save()

        action = "activated" if company.is_active else "deactivated"
        create_user_activity(request.user, "company_update", f"Company {action}: {company.name}",
                           related_company=company)

        Notification.objects.create(
            user=company.owner,
            notification_type="company_update",
            title=f"Company {action}",
            message=f"Your company {company.name} has been {action}.",
            related_company=company,
        )
        messages.success(request, _(f"Company {action}"))

    return redirect("accounts:admin_company_management")

@login_required
@user_passes_test(can_view_company_details, login_url="accounts:admin_login")
def company_detail_admin(request, pk):
    company = get_object_or_404(Company, pk=pk)

    return render(request, "accounts/admin_company_detail.html", {
        "company": company,
        "jobs": Job.objects.filter(company=company),
        "active_jobs": Job.objects.filter(company=company, is_active=True),
        "total_applications": JobApplication.objects.filter(job__company=company).count(),
        "documents": company.documents.all(),
        "activities": UserActivity.objects.filter(related_company=company).order_by("-created_at")[:20],
        "can_verify_companies": can_verify_companies(request.user),
        "can_change_company_status": can_change_company_status(request.user),
    })

@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def create_admin_account(request):
    if request.method == "POST":
        form = AdminProfileForm(request.POST)
        if form.is_valid():
            try:
                if CustomUser.objects.filter(email=form.cleaned_data["email"]).exists():
                    messages.error(request, "Пользователь с таким email уже существует")
                    return render(request, "accounts/create_admin_account.html", {"form": form})

                if CustomUser.objects.filter(username=form.cleaned_data["username"]).exists():
                    messages.error(request, "Пользователь с таким именем уже существует")
                    return render(request, "accounts/create_admin_account.html", {"form": form})

                user = CustomUser.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    user_type=form.cleaned_data["user_type"],
                )
                user.set_password(form.cleaned_data["password1"])
                user.save()

                admin_profile, created = AdminProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        field_name: form.cleaned_data.get(field_name, False)
                        for field_name in AdminProfile.PERMISSION_FIELDS
                    },
                )

                create_user_activity(
                    request.user,
                    "user_create",
                    f"Created admin account: {user.username} ({user.get_user_type_display()})",
                )
                messages.success(
                    request,
                    _("Administrator account created successfully!"),
                )
                return redirect("accounts:admin_management")

            except Exception as e:
                messages.error(request, f"Ошибка при создании администратора: {str(e)}")
                return render(request, "accounts/create_admin_account.html", {"form": form})
    else:
        form = AdminProfileForm()

    return render(request, "accounts/create_admin_account.html", {"form": form})



@login_required
def profile_view(request, user_id=None):
    user = request.user if not user_id else get_object_or_404(CustomUser, id=user_id)
    is_own_profile = (user == request.user)

    if not is_own_profile:
        # Увеличиваем счетчик просмотров в соответствующем профиле
        if user.is_student_or_alumni:
            StudentProfile.objects.filter(user=user).update(profile_views=F('profile_views') + 1)
        elif user.is_employer:
            EmployerProfile.objects.filter(user=user).update(profile_views=F('profile_views') + 1)
        create_user_activity(request.user, "profile_view", f"Viewed {user.username}'s profile")

    student_profile = None
    employer_profile = None
    admin_profile = None

    if user.is_student_or_alumni:
        student_profile = StudentProfile.objects.filter(user=user).first()
    elif user.is_employer:
        employer_profile = EmployerProfile.objects.filter(user=user).first()
    elif user.is_admin:
        admin_profile, _ = AdminProfile.objects.get_or_create(user=user)

    # Вычисляем количество просмотров для отображения
    profile_views = 0
    if student_profile:
        profile_views = student_profile.profile_views
    elif employer_profile:
        profile_views = employer_profile.profile_views

    # Город из профиля для отображения в контактах
    location = None
    if student_profile and student_profile.city:
        location = student_profile.city
    elif employer_profile and employer_profile.city:
        location = employer_profile.city

    # Получаем ссылки из профиля (если профиль существует)
    website = None
    instagram = None
    linkedin = None
    facebook = None
    twitter = None
    github = None
    telegram = None

    if student_profile:
        website = student_profile.website
        instagram = student_profile.instagram
        linkedin = student_profile.linkedin
        facebook = student_profile.facebook
        twitter = student_profile.twitter
        github = student_profile.github
        telegram = student_profile.telegram
    elif employer_profile:
        website = employer_profile.website
        instagram = employer_profile.instagram
        linkedin = employer_profile.linkedin
        facebook = employer_profile.facebook
        twitter = employer_profile.twitter
        github = employer_profile.github
        telegram = employer_profile.telegram

    context = {
        "profile_user": user,
        "is_own_profile": is_own_profile,
        "profile_views": profile_views,
        "location": location,
        "website": website,
        "instagram": instagram,
        "linkedin": linkedin,
        "facebook": facebook,
        "twitter": twitter,
        "github": github,
        "telegram": telegram,
        "event_participations": EventParticipation.objects.filter(user=user).select_related("event").order_by("-registered_at")[:6],
    }

    if student_profile:
        profile_certificates = get_viewable_student_certificates_queryset(request.user, user)
        resumes = CV.objects.filter(user=user, status='published')
        context.update({
            "student_profile": student_profile,
            "resumes": resumes,
            "applications_count": JobApplication.objects.filter(user=user).count(),
            "profile_certificates": profile_certificates[:6],
            "profile_certificates_count": profile_certificates.count(),
            "can_manage_certificates": is_own_profile,
        })
        template_name = "accounts/student_profile.html"
    elif employer_profile:
        owned_companies = Company.objects.filter(owner=user, is_active=True)
        primary_company = (
            employer_profile.company
            if employer_profile.company and employer_profile.company.is_active
            else (owned_companies.first() if owned_companies.exists() else None)
        )

        if primary_company:
            active_jobs = Job.objects.filter(company=primary_company, is_active=True).select_related('company')
            active_jobs_count = active_jobs.count()
            jobs_posted = Job.objects.filter(company=primary_company).count()
            total_views = primary_company.total_views or 0
            total_applications = JobApplication.objects.filter(job__company=primary_company).count()
        else:
            active_jobs = Job.objects.none()
            active_jobs_count = 0
            jobs_posted = 0
            total_views = 0
            total_applications = 0

        context.update({
            "employer_profile": employer_profile,
            "owned_companies": owned_companies,
            "total_companies": owned_companies.count(),
            "primary_company": primary_company,
            "active_jobs": active_jobs[:5],
            "active_jobs_count": active_jobs_count,
            "jobs_posted": jobs_posted,
            "total_views": total_views,
            "total_applications": total_applications,
        })
        template_name = "accounts/employer_profile.html"
    elif admin_profile:
        context["profile"] = admin_profile
        template_name = "accounts/admin_profile.html"
    else:
        template_name = "accounts/profile_base.html"

    return render(request, template_name, context)



@login_required
def notifications(request):
    notifications_list = Notification.objects.filter(user=request.user).order_by("-created_at")
    notification_type = request.GET.get("type", "")

    if notification_type:
        notifications_list = notifications_list.filter(notification_type=notification_type)

    paginator = Paginator(notifications_list, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/notifications.html", {
        "notifications": page_obj,
        "page_obj": page_obj,
        "notification_type": notification_type,
        "unread_count": Notification.objects.filter(user=request.user, is_read=False).count(),
        "type_stats": {
            "system": Notification.objects.filter(user=request.user, notification_type="system").count(),
            "job_alert": Notification.objects.filter(user=request.user, notification_type="job_alert").count(),
            "application_update": Notification.objects.filter(user=request.user, notification_type="application_update").count(),
            "event": Notification.objects.filter(user=request.user, notification_type="event").count(),
            "company_update": Notification.objects.filter(user=request.user, notification_type="company_update").count(),
            "company_verification": Notification.objects.filter(user=request.user, notification_type="company_verification").count(),
        },
    })

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    next_url = request.GET.get('next', 'accounts:notifications')
    return redirect(next_url)

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, _("All notifications marked as read"))

    next_url = request.GET.get('next', 'accounts:notifications')
    return redirect(next_url)

@login_required
@require_http_methods(["GET"])
def user_stats_api(request):
    user = request.user
    user_type = getattr(user, "user_type", None)

    stats = {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "user_type": user_type,
        "is_staff": user.is_staff,
        "is_superuser": user.is_superuser,
    }

    if user_type in ["student", "alumni"]:
        stats.update({
            "role": user_type,
            "full_name": user.get_full_name(),
            "phone_number": str(user.phone_number) if user.phone_number else None,
            "university": getattr(user, 'university', None),
            "applications_count": JobApplication.objects.filter(user=user).count(),
            "cv_count": CV.objects.filter(user=user).count(),
        })

    elif user_type == "employer":
        try:
            profile = EmployerProfile.objects.get(user=user)
            company_count = profile.companies.count() if hasattr(profile, 'companies') else 0
            stats.update({
                "role": "employer",
                "full_name": profile.full_name if hasattr(profile, 'full_name') else user.get_full_name(),
                "phone_number": str(profile.phone_number) if hasattr(profile, 'phone_number') else None,
                "company_count": company_count,
                "active_jobs": Job.objects.filter(company__employerprofile__user=user, is_active=True).count(),
            })
        except EmployerProfile.DoesNotExist:
            stats["role"] = "employer"
            stats["error"] = "Employer profile not found"

    elif user_type in ADMIN_USER_TYPES:
        stats.update({
            "role": user_type,
            "full_name": user.get_full_name() or user.username,
        })

    return JsonResponse(stats, status=200)

@login_required
@user_passes_test(can_manage_employers, login_url="accounts:admin_login")
def admin_employer_management(request):
    employers = (
        CustomUser.objects.filter(user_type="employer")
        .select_related("employer_profile")
        .prefetch_related("companies_owned")
        .annotate(company_count=Count("companies_owned", distinct=True))
        .order_by("-date_joined")
    )

    search_query = request.GET.get('search', '')
    if search_query:
        employers = employers.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(companies_owned__name__icontains=search_query)
        ).distinct()

    paginator = Paginator(employers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/admin_employer_management.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "total_employers": CustomUser.objects.filter(user_type="employer").count(),
    })

@login_required
@user_passes_test(can_manage_users, login_url="accounts:admin_login")
def user_management(request):
    allowed_user_types = managed_user_types_for_admin(request.user)
    if request.user.is_main_admin:
        allowed_user_types = set(ADMIN_USER_TYPES) | {"student", "alumni", "employer"}

    users = CustomUser.objects.filter(user_type__in=allowed_user_types).order_by("-date_joined")
    total_visible_users = users.count()

    user_type_filter = request.GET.get("user_type") or request.GET.get("type", "")
    user_type_mapping = {
        "all": "",
        "students": "student",
        "alumni": "alumni",
        "employers": "employer",
    }
    normalized_filter = user_type_mapping.get(user_type_filter, user_type_filter)
    if normalized_filter == "admins":
        if request.user.is_main_admin:
            users = users.filter(user_type__in=ADMIN_USER_TYPES)
        else:
            users = users.none()
    elif normalized_filter:
        users = users.filter(user_type=normalized_filter)

    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )

    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, "accounts/user_management.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "user_type_filter": normalized_filter,
        "total_users": total_visible_users,
        "can_view_admin_users": request.user.is_main_admin,
        "allowed_user_types": sorted(allowed_user_types),
        "can_change_user_status": can_change_user_status(request.user),
    })

@login_required
@user_passes_test(can_manage_users, login_url="accounts:admin_login")
def user_detail(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if not can_view_managed_user(request.user, user):
        messages.error(request, _("You don't have permission to view this profile"))
        return redirect("accounts:user_management")

    profile = None
    if user.user_type in ["student", "alumni"]:
        profile = user
    elif user.user_type == "employer":
        try:
            profile = EmployerProfile.objects.get(user=user)
        except EmployerProfile.DoesNotExist:
            pass
    elif user.user_type in ADMIN_USER_TYPES:
        try:
            profile = AdminProfile.objects.get(user=user)
        except AdminProfile.DoesNotExist:
            pass

    context = {
        "profile_user": user,
        "profile": profile,
        "activities": UserActivity.objects.filter(user=user).order_by("-created_at")[:20],
        "can_toggle_status": can_change_managed_user_status(request.user, user),
    }

    if user.user_type in ["student", "alumni"]:
        context.update({
            "applications": JobApplication.objects.filter(user=user).count(),
            "cvs": CV.objects.filter(user=user).count(),
        })
    elif user.user_type == "employer":
        context.update({
            "companies": Company.objects.filter(owner=user).count(),
            "jobs": Job.objects.filter(company__owner=user).distinct().count(),
        })

    return render(request, "accounts/user_detail.html", context)

@login_required
@user_passes_test(can_manage_users, login_url="accounts:admin_login")
def toggle_user_status(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)

    if not can_change_managed_user_status(request.user, user):
        messages.error(request, _("You don't have permission to change this user's status."))
        return redirect("accounts:user_detail", user_id=user_id)

    if request.method == "POST":
        user.is_active = not user.is_active
        user.save()

        status_str = "activated" if user.is_active else "deactivated"
        create_user_activity(request.user, "user_update", f"User {status_str}: {user.username}")

        messages.success(request, _(f"User {status_str}"))

    return redirect("accounts:user_detail", user_id=user_id)

@login_required
@user_passes_test(can_create_employers, login_url="accounts:admin_login")
def create_employer_account(request):
    if request.method == 'POST':
        user_form = EmployerRegistrationForm(request.POST, prefix='user')
        company_form = AdminCompanyForm(request.POST, request.FILES, prefix='company')
        profile_form = AdminEmployerProfileForm(request.POST, request.FILES, prefix='profile')

        if user_form.is_valid() and company_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = "employer"
            user.save()

            company = company_form.save(commit=False)
            company.owner = user
            company.save()

            CompanyAdditionalInfo.objects.create(
                company=company,
                legal_name=company_form.cleaned_data.get("legal_name", ""),
                tax_id=company_form.cleaned_data.get("tax_id", ""),
                cover_image=company_form.cleaned_data.get("cover_image"),
                sub_industry=company_form.cleaned_data.get("sub_industry", ""),
                vision=company_form.cleaned_data.get("vision", ""),
                country=company_form.cleaned_data.get("country", ""),
            )

            profile, created = EmployerProfile.objects.get_or_create(user=user)

            profile_form = AdminEmployerProfileForm(
                request.POST,
                request.FILES,
                instance=profile,
                prefix='profile'
            )

            profile = profile_form.save(commit=False)
            profile.company = company
            profile.save()

            create_user_activity(
                request.user,
                "user_create",
                f"Created employer account: {user.username}"
            )

            messages.success(request, _("Employer account created successfully!"))
            return redirect('accounts:admin_dashboard')
    else:
        user_form = EmployerRegistrationForm(prefix='user')
        company_form = AdminCompanyForm(prefix='company')
        profile_form = AdminEmployerProfileForm(prefix='profile')

    return render(request, 'accounts/create_employer_account.html', {
        'user_form': user_form,
        'company_form': company_form,
        'profile_form': profile_form
    })

def handler403(request, exception=None):
    return render(request, 'errors/403.html', status=403)

def handler404(request, exception=None):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)

def help_center(request):
    return render(request, "accounts/help_center.html")

def contact_us(request):
    if request.method == "POST":
        messages.success(request, _("Your message has been sent. We'll get back to you soon!"))
        return redirect("accounts:contact_us")
    return render(request, "accounts/contact_us.html")

def about_us(request):
    return render(request, "accounts/about_us.html")

def terms_of_service(request):
    return render(request, "accounts/terms_of_service.html")

def privacy_policy(request):
    return render(request, "accounts/privacy_policy.html")

def dashboard_redirect(request):
    if not request.user.is_authenticated:
        return redirect("accounts:employer_login")

    user_type = getattr(request.user, "user_type", None)

    if user_type in ["student", "alumni"]:
        return redirect("accounts:student_dashboard")
    elif user_type == "employer":
        return redirect("accounts:employer_dashboard")
    elif user_type in ADMIN_USER_TYPES:
        return redirect("accounts:admin_dashboard")

    return redirect("home")

@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def initial_setup(request):
    if CustomUser.objects.filter(user_type="main_admin").exists():
        messages.warning(request, _("System is already set up"))
        return redirect("accounts:admin_dashboard")

    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, _("Passwords do not match"))
            return redirect("accounts:initial_setup")

        admin_user = CustomUser.objects.create_user(
            username=username,
            email=email,
            user_type="main_admin",
            is_staff=True,
            is_superuser=True,
        )
        admin_user.set_password(password)
        admin_user.save()

        AdminProfile.objects.create(
            user=admin_user,
            **{field_name: True for field_name in AdminProfile.PERMISSION_FIELDS},
        )

        login(request, admin_user)
        messages.success(request, _("System setup completed successfully!"))
        return redirect("accounts:admin_dashboard")

    return render(request, "accounts/initial_setup.html")

@login_required(login_url='accounts:employer_login')
def activity_log(request):
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')

    activity_type = request.GET.get('type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)

    paginator = Paginator(activities, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    activity_types = UserActivity.ACTIVITY_TYPES

    context = {
        'page_obj': page_obj,
        'activities': page_obj.object_list,
        'activity_types': activity_types,
        'selected_type': activity_type,
    }

    return render(request, 'accounts/activity_log.html', context)

def student_oauth_login(request):
    from django.utils.crypto import get_random_string
    from urllib.parse import urlencode

    try:
        oauth_config = settings.OAUTH_PROVIDER

        state = get_random_string(length=32)

        request.session['oauth_state'] = state
        request.session.set_expiry(600)

        params = {
            'client_id': oauth_config['CLIENT_ID'],
            'redirect_uri': oauth_config['REDIRECT_URI'],
            'response_type': 'code',
            'scope': oauth_config.get('SCOPE', 'profile email'),
            'state': state,
        }

        authorize_url = f"{oauth_config['AUTHORIZE_URL']}?{urlencode(params)}"

        return redirect(authorize_url)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth login error: {str(e)}")
        messages.error(request, _("Failed to start OAuth authentication. Please try again."))
        return redirect("accounts:hemis_login")

def oauth_callback(request):
    from django.contrib.auth import authenticate

    try:
        error = request.GET.get('error')
        if error:
            error_description = request.GET.get('error_description', 'Unknown error')
            messages.error(request, _("OAuth error: %(error)s") % {'error': error_description})
            return redirect("accounts:hemis_login")

        state = request.GET.get('state')
        session_state = request.session.get('oauth_state')

        if not state or not session_state or state != session_state:
            messages.error(request, _("Invalid state parameter. Please try again."))
            return redirect("accounts:hemis_login")

        del request.session['oauth_state']

        code = request.GET.get('code')
        if not code:
            messages.error(request, _("No authorization code received. Please try again."))
            return redirect("accounts:hemis_login")

        user = authenticate(request, code=code, state=state)

        if user is None:
            messages.error(request, _("Failed to authenticate. Please try again."))
            return redirect("accounts:hemis_login")

        login(request, user)

        create_user_activity(
            user,
            "login",
            "Student logged in via OAuth",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")
        )

        messages.success(request, _("Successfully logged in!"))

        return redirect("accounts:student_dashboard")

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth callback error: {str(e)}")
        messages.error(request, _("An error occurred during authentication. Please try again."))
        return redirect("accounts:hemis_login")

def check_bruteforce_protection(ip_address, username=None):
    ip_block_key = f'ip_blocked_{ip_address}'
    if cache.get(ip_block_key):
        ttl = cache.ttl(ip_block_key)
        remaining_minutes = max(1, ttl // 60)
        return False, f"IP адрес заблокирован на {remaining_minutes} минут", remaining_minutes

    if username:
        user_block_key = f'user_blocked_{username}'
        if cache.get(user_block_key):
            ttl = cache.ttl(user_block_key)
            remaining_minutes = max(1, ttl // 60)
            return False, f"Аккаунт заблокирован на {remaining_minutes} минут", remaining_minutes

    ip_attempts_key = f'login_attempts_ip_{ip_address}'
    attempts_ip = cache.get(ip_attempts_key, 0)

    if username:
        user_attempts_key = f'login_attempts_user_{username}'
        attempts_user = cache.get(user_attempts_key, 0)
    else:
        attempts_user = 0

    max_attempts = 10
    warning_threshold = 5

    if attempts_ip >= max_attempts or attempts_user >= max_attempts:
        block_time = 900
        cache.set(ip_block_key, True, block_time)
        if username:
            cache.set(user_block_key, True, block_time)

        return False, "Слишком много неудачных попыток. Доступ заблокирован на 15 минут.", 15

    if attempts_ip >= warning_threshold or attempts_user >= warning_threshold:
        remaining = max_attempts - max(attempts_ip, attempts_user)
        return True, f"Внимание: осталось {remaining} попыток", None

    return True, None, None

def record_failed_login_attempt(ip_address, username=None):
    ip_key = f'login_attempts_ip_{ip_address}'
    attempts = cache.get(ip_key, 0) + 1
    cache.set(ip_key, attempts, 300)

    if username:
        user_key = f'login_attempts_user_{username}'
        user_attempts = cache.get(user_key, 0) + 1
        cache.set(user_key, user_attempts, 300)

    print(f"Failed login attempt: IP={ip_address}, User={username}, Attempts={attempts}")

def clear_login_attempts(ip_address, username=None):
    cache.delete(f'login_attempts_ip_{ip_address}')
    cache.delete(f'ip_blocked_{ip_address}')

    if username:
        cache.delete(f'login_attempts_user_{username}')
        cache.delete(f'user_blocked_{username}')

def get_login_attempts_info(ip_address, username=None):
    ip_attempts = cache.get(f'login_attempts_ip_{ip_address}', 0)
    user_attempts = cache.get(f'login_attempts_user_{username}', 0) if username else 0

    ip_blocked = cache.get(f'ip_blocked_{ip_address}') is not None
    user_blocked = cache.get(f'user_blocked_{username}') is not None if username else False

    return {
        'ip_attempts': ip_attempts,
        'user_attempts': user_attempts,
        'ip_blocked': ip_blocked,
        'user_blocked': user_blocked,
        'ip_block_ttl': cache.ttl(f'ip_blocked_{ip_address}') if ip_blocked else None,
        'user_block_ttl': cache.ttl(f'user_blocked_{username}') if user_blocked else None,
    }