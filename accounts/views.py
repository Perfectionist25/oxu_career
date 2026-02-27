import json
from datetime import datetime, timedelta
import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q, Count, F, Case, When, Value, IntegerField, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, gettext
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.contrib.auth import update_session_auth_hash
from django.core.cache import cache

from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from rest_framework.response import Response

from accounts.models import (
    CustomUser, StudentProfile, EmployerProfile, AdminProfile,
    Company, CompanyDocument, UserActivity, Notification, CompanyAdditionalInfo
)

from jobs.models import Job, JobApplication
from cvbuilder.models import CV
from events.models import Event
from .middleware import BruteForceProtectionMiddleware
from .forms import (
    UserUpdateForm, StudentProfileForm, EmployerProfileForm,
    AdminProfileForm, CompanyForm, CompanyDocumentForm,
    EmployerRegistrationForm, AdminCompanyForm, AdminEmployerProfileForm, StudentUserReadonlyNameForm
)
# ============ SIMPLE JWT VIEWS ============
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from urllib.parse import urlencode
from django.conf import settings
from django.shortcuts import redirect
from django.utils.crypto import get_random_string


def oauth_login(request):
    state = get_random_string(40)
    request.session["oauth_state"] = state
    request.session["oauth_next"] = request.GET.get("next", settings.OAUTH_SUCCESS_REDIRECT)
    request.session.set_expiry(getattr(settings, "OAUTH_STATE_TTL", 600))

    params = {
        "response_type": "code",
        "client_id": settings.OAUTH_CLIENT_ID,
        "redirect_uri": settings.OAUTH_REDIRECT_URI,
        "scope": settings.OAUTH_SCOPE,
        "state": state,
    }
    url = settings.OAUTH_AUTHORIZE_URL + "?" + urlencode(params)
    return redirect(url)




class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор токенов с проверкой типа пользователя.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Проверяем тип пользователя
        user = self.user
        
        # Если студент пытается получить токен через пароль - запрещаем
        if user.user_type == 'student':
            raise serializers.ValidationError({
                "detail": "Студенты должны использовать OAuth авторизацию через /oauth/login/"
            })
        
        # Добавляем информацию о пользователе
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



# ============ UTILITY FUNCTIONS ============
def is_student(user):
    return user.is_authenticated and getattr(user, "user_type", None) == "student"


def is_employer(user):
    return user.is_authenticated and getattr(user, "user_type", None) == "employer"


def is_admin(user):
    return user.is_authenticated and getattr(user, "user_type", None) in ["admin", "main_admin"]


def is_main_admin(user):
    return user.is_authenticated and getattr(user, "user_type", None) == "main_admin"


def can_manage_users(user):
    return is_admin(user)


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


def get_client_ip(request=None):
    if request is None:
        return None
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============ AUTHENTICATION VIEWS ============
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
        
        if user_type == "student":
            return redirect("accounts:student_dashboard")
        elif user_type == "employer":
            return redirect("accounts:employer_dashboard")
        elif user_type in ["admin", "main_admin"]:
            return redirect("accounts:admin_dashboard")
    
    return redirect("home")


def employer_login(request):
    if request.user.is_authenticated and request.user.user_type == "employer":
        return redirect("accounts:employer_dashboard")
    
    ip_address = get_client_ip(request)
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        status = BruteForceProtectionMiddleware.get_block_status(ip_address, username or None)
        if status["is_blocked"]:
            return BruteForceProtectionMiddleware.blocked_response(
                request,
                ip_address=ip_address,
                username=username,
                reason=status["reason"],
                remaining_seconds=status["remaining_seconds"],
            )
        
        user = authenticate(request, username=username, password=password)
        
        if user and user.is_employer:
            if not user.is_active:
                messages.error(request, "Ваш аккаунт деактивирован. Обратитесь к администратору.")
                return render(request, "accounts/employer_login.html")
            
            login(request, user)
            
            BruteForceProtectionMiddleware.clear_attempts(ip_address, username)
            
            create_user_activity(user, "login", "Employer logged in", ip_address, 
                               request.META.get("HTTP_USER_AGENT", ""))
            
            messages.success(request, "Добро пожаловать!")
            return redirect("accounts:employer_dashboard")
        else:
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
                messages.error(request, "Неверные учетные данные или вы не авторизованы как работодатель")
    
    return render(request, "accounts/employer_login.html")


def admin_login(request):
    """Admin login page with brute force protection"""
    # Если пользователь уже аутентифицирован и является админом, перенаправляем
    if request.user.is_authenticated and request.user.user_type in ["admin", "main_admin"]:
        return redirect("accounts:admin_dashboard")
    
    ip_address = get_client_ip(request)
    
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        
        # Валидация ввода
        if not username or not password:
            messages.error(request, "Пожалуйста, введите имя пользователя и пароль")
            return render(request, "accounts/admin_login.html")
        
        status = BruteForceProtectionMiddleware.get_block_status(ip_address, username or None)
        if status["is_blocked"]:
            return BruteForceProtectionMiddleware.blocked_response(
                request,
                ip_address=ip_address,
                username=username,
                reason=status["reason"],
                remaining_seconds=status["remaining_seconds"],
            )
        
        # Аутентификация пользователя
        user = authenticate(request, username=username, password=password)
        
        if user is None:
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
                messages.error(request, "Неверное имя пользователя или пароль")
            return render(request, "accounts/admin_login.html")
        
        # Проверка, что пользователь является администратором
        if not user.user_type in ["admin", "main_admin"]:
            messages.error(request, "Вы не авторизованы для доступа к админ-панели")
            return render(request, "accounts/admin_login.html")
        
        # Проверка активности аккаунта
        if not user.is_active:
            messages.error(request, "Ваш аккаунт деактивирован. Обратитесь к главному администратору.")
            return render(request, "accounts/admin_login.html")
        
        # Все проверки пройдены - выполняем вход
        login(request, user)
        
        # Очищаем счетчики при успешном входе
        BruteForceProtectionMiddleware.clear_attempts(ip_address, username)
        
        # Создание записи об активности
        create_user_activity(
            user, 
            "login", 
            f"Admin logged in: {username}",
            ip_address,
            request.META.get("HTTP_USER_AGENT", "")
        )
        
        messages.success(request, "Добро пожаловать в админ-панель!")
        return redirect("accounts:admin_dashboard")
    
    return render(request, "accounts/admin_login.html")


def admin_logout(request):
    """Admin logout with enhanced security"""
    if request.user.is_authenticated:
        # Логируем выход
        create_user_activity(
            request.user, 
            "logout", 
            f"Admin logged out: {request.user.username}",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")
        )
    
    logout(request)
    
    # Очистка сессии
    request.session.flush()
    
    messages.success(request, _("You have been logged out successfully"))
    return redirect("accounts:admin_login")


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_change_password(request):
    """Admin change password page"""
    if request.method == "POST":
        old_password = request.POST.get("old_password")
        new_password1 = request.POST.get("new_password1")
        new_password2 = request.POST.get("new_password2")
        
        # Валидация
        if not all([old_password, new_password1, new_password2]):
            messages.error(request, _("All fields are required"))
            return render(request, "accounts/admin_change_password.html")
        
        if new_password1 != new_password2:
            messages.error(request, _("New passwords don't match"))
            return render(request, "accounts/admin_change_password.html")
        
        if len(new_password1) < 8:
            messages.error(request, _("Password must be at least 8 characters long"))
            return render(request, "accounts/admin_change_password.html")
        
        # Проверка старого пароля
        if not request.user.check_password(old_password):
            messages.error(request, _("Current password is incorrect"))
            return render(request, "accounts/admin_change_password.html")
        
        # Изменение пароля
        request.user.set_password(new_password1)
        request.user.save()
        
        # Обновление сессии после смены пароля
        update_session_auth_hash(request, request.user)
        
        # Логирование
        create_user_activity(
            request.user, 
            "password_change", 
            "Admin changed password",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")
        )
        
        messages.success(request, _("Password changed successfully!"))
        return redirect("accounts:admin_dashboard")
    
    return render(request, "accounts/admin_change_password.html")


@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def admin_session_management(request):
    """View and manage admin sessions (main admin only)"""
    # Получаем все активные сессии администраторов
    from django.contrib.sessions.models import Session
    from django.utils import timezone
    
    active_sessions = []
    now = timezone.now()
    
    # Получаем всех админов
    admins = CustomUser.objects.filter(user_type__in=["admin", "main_admin"])
    
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
    # Здесь можно реализовать настройку 2FA
    # Например, используя django-otp или другой пакет
    
    context = {
        'two_factor_enabled': False,  # Заменить на реальную проверку
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
    ).order_by('-created_at')[:50]  # Последние 50 записей
    
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
            or f"{user_data.get('first_name', '')} {user_data.get('last_name', '')}".strip()
        )

        first_name = ""
        last_name = ""

        if full_name:
            parts = full_name.split()
            first_name = parts[0]
            last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

        user, created = CustomUser.objects.update_or_create(
            username=local_username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "user_type": "student",
                "is_active": True,
                "oauth_provider": "hemis",   # ← важно
            },
        )

        student_profile, _profile_created = StudentProfile.objects.get_or_create(user=user)

        for field in ["faculty", "specialty", "graduation_year", "phone", "bio", "gpa"]:
            if field in user_data:
                setattr(student_profile, field, user_data[field])
        student_profile.save()

        login(request, user)
        create_user_activity(user, "login", "Student logged in via OAuth", 
                           get_client_ip(request), request.META.get("HTTP_USER_AGENT", ""))
        messages.success(request, _("Logged in successfully"))
        return redirect("accounts:student_dashboard")

    return render(request, "accounts/hemis_login.html")


def hemis_callback(request):
    """OAuth callback from HEMIS/external service (if using redirect flow)"""
    # This would handle callback from OAuth provider if using authorization code flow
    # For now, redirect to hemis_login if accessed directly
    messages.info(request, _("Please use the login form to authenticate"))
    return redirect("accounts:hemis_login")


def temp_student_login_view(request):
    """Temporary endpoint for testing student login without OAuth microservice"""
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        if not username or not password:
            messages.error(request, _("Please provide username and password"))
            return render(request, "accounts/temp_student_login.html")

        # Try to authenticate with Django's auth system
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
    """Logout user"""
    if request.user.is_authenticated:
        try:
            create_user_activity(request.user, "logout", "User logged out")
        except Exception as e:
            # Log error but don't fail logout
            print(f"Error creating user activity: {e}")
    
    logout(request)
    messages.success(request, _("You have been logged out"))

    response = redirect("core:home")
    access_cookie = getattr(settings, "OAUTH_ACCESS_COOKIE_NAME", "student_access")
    refresh_cookie = getattr(settings, "OAUTH_REFRESH_COOKIE_NAME", "student_refresh")
    response.delete_cookie(access_cookie)
    response.delete_cookie(refresh_cookie)
    return response


# ============ STUDENT VIEWS ============
@login_required
@user_passes_test(is_student, login_url="accounts:employer_login")
def student_dashboard(request):
    """Student dashboard"""
    # Получаем или создаем профиль студента
    student_profile, created = StudentProfile.objects.get_or_create(user=request.user)
    
    # ФИЛЬТРУЕМ по student_profile, так как модель CV имеет ForeignKey к StudentProfile
    resumes = CV.objects.filter(user=student_profile)
    
    applications = JobApplication.objects.filter(user=request.user)
    
    context = {
        "student_profile": student_profile,
        "stats": {
            "resumes_created": resumes.count(),
            "active_resumes": resumes.filter(status='published').count(),
            "jobs_applied": applications.count(),
            "pending_applications": applications.filter(status="applied").count(),
            "accepted_applications": applications.filter(status="hired").count(),
            "profile_views": request.user.profile_views or 0,
        },
        "recent_applications": applications.select_related('job', 'job__company').order_by('-created_at')[:5],
        "recommended_jobs": Job.objects.filter(
            is_active=True, expires_at__gte=timezone.now()
        ).filter(
            Q(title__icontains=student_profile.specialty) | Q(description__icontains=student_profile.specialty)
        )[:5] if student_profile.specialty else Job.objects.none(),
        "recent_activity": UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        "recent_activities": UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        "recent_notifications": Notification.objects.filter(user=request.user).order_by("-created_at")[:5],
        "resumes": resumes,  # Добавляем в контекст
    }
    
    return render(request, "accounts/student_dashboard.html", context)


@login_required
@user_passes_test(is_student, login_url="accounts:employer_login")
def student_profile_update(request):
    """Update student profile"""
    student_profile, _profile_created = StudentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        user_form = StudentUserReadonlyNameForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, request.FILES, instance=student_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            updated_profile = profile_form.save()

            # Keep student avatar in sync with the main user avatar used across templates.
            request.user.avatar = updated_profile.avatar
            request.user.save(update_fields=["avatar", "updated_at"])

            create_user_activity(request.user, "profile_update", "Student profile updated")
            messages.success(request, _("Profile updated successfully!"))
            return redirect("accounts:student_dashboard")
    else:
        user_form = StudentUserReadonlyNameForm(instance=request.user)
        profile_form = StudentProfileForm(instance=student_profile)

    return render(request, "accounts/student_profile_update.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })




@login_required
@user_passes_test(is_student, login_url="accounts:hemis_login")
def student_search(request):
    """Student job search view"""
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


# ============ EMPLOYER VIEWS ============
@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_dashboard(request):
    """Employer dashboard"""
    employer_profile, gettext = EmployerProfile.objects.get_or_create(user=request.user)
    owned_companies = Company.objects.filter(owner=request.user, is_active=True)
    
    primary_company = None
    company_id = request.GET.get('company_id')
    
    if company_id:
        try:
            primary_company = owned_companies.get(id=company_id)
        except Company.DoesNotExist:
            pass
    
    if not primary_company:
        if employer_profile.primary_company_id and employer_profile.primary_company_id in owned_companies:
            primary_company = employer_profile.primary_company_id
        elif owned_companies.exists():
            primary_company = owned_companies.first()
    
    # Если primary_company - это удаленная компания, очищаем ее
    if primary_company and not primary_company.is_active:
        employer_profile.primary_company_id = None
        employer_profile.save()
        primary_company = None
        if owned_companies.exists():
            primary_company = owned_companies.first()
    
    # Calculate statistics
    if primary_company:
        # Stats for selected company
        active_jobs = Job.objects.filter(
            company=primary_company,
            is_active=True
        ).count()
        total_applications = JobApplication.objects.filter(
            job__company=primary_company
        ).count()
        # Profile views from the company model
        profile_views = primary_company.total_views or 0
    else:
        # Stats for all companies
        active_jobs = Job.objects.filter(
            company__owner=request.user,
            is_active=True
        ).count()
        total_applications = JobApplication.objects.filter(
            job__company__owner=request.user
        ).count()
        # Total profile views across all companies
        profile_views = Company.objects.filter(
            owner=request.user
        ).aggregate(total=Sum('total_views'))['total'] or 0
    
    stats = {
        'active_jobs': active_jobs,
        'total_applications': total_applications,
        'profile_views': profile_views,
    }
    
    context = {
        'employer_profile': employer_profile,
        'primary_company': primary_company,
        'owned_companies': owned_companies,
        'stats': stats,
        'recent_jobs': Job.objects.filter(
            company__owner=request.user
        ).order_by('-created_at')[:5],
        'recent_applications': JobApplication.objects.filter(
            job__company__owner=request.user
        ).select_related('user', 'job').order_by('-created_at')[:5],
        'recent_activity': UserActivity.objects.filter(user=request.user).order_by('-created_at')[:10],
        'notifications': Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:5],
    }
    
    return render(request, 'accounts/employer_dashboard.html', context)


@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_profile_update(request):
    """Update employer profile"""
    employer_profile, gettext = EmployerProfile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            create_user_activity(request.user, "profile_update", "Employer profile updated")
            messages.success(request, gettext("Profile updated successfully!"))
            return redirect("accounts:employer_dashboard")
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = EmployerProfileForm(instance=employer_profile)
    
    return render(request, "accounts/employer_profile_update.html", {
        "user_form": user_form,
        "profile_form": profile_form,
    })


@login_required
@user_passes_test(is_employer, login_url="accounts:employer_login")
def employer_stats(request):
    """Employer statistics view"""
    companies = Company.objects.filter(owner=request.user, is_active=True)
    
    # Calculate statistics
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
    """Set primary company for employer"""
    if not is_employer(request.user):
        return redirect("accounts:employer_login")
    
    try:
        company = Company.objects.get(pk=pk, owner=request.user)
        employer_profile, gettext = EmployerProfile.objects.get_or_create(user=request.user)
        employer_profile.primary_company = company
        employer_profile.save()
        messages.success(request, _("Primary company set successfully"))
    except Company.DoesNotExist:
        messages.error(request, _("Company not found"))
    
    return redirect("accounts:employer_dashboard")


# ============ COMPANY VIEWS ============
class CompanyListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all companies owned by employer"""
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

        try:
            context['primary_company'] = self.request.user.employer_profile.primary_company_id
        except EmployerProfile.DoesNotExist:
            context['primary_company'] = None

        return context


class CompanyCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """Create a new company"""
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
                employer_profile.primary_company = company
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
    """View company details"""
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
                is_primary = employer_profile.primary_company_id == company
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
    """Update company information"""
    model = Company
    template_name = 'accounts/company_form.html'
    form_class = CompanyForm
    
    def test_func(self):
        company = self.get_object()
        return company.owner == self.request.user
    
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
    """Delete company (soft delete)"""
    model = Company
    template_name = 'accounts/company_confirm_delete.html'
    
    def test_func(self):
        company = self.get_object()
        return company.owner == self.request.user
    
    def post(self, request, *args, **kwargs):
        """Handle POST request for deletion"""
        self.object = self.get_object()
        company_name = self.object.name
        
        # ОЧИСТИТЬ primary_company_id у всех employer профилей
        EmployerProfile.objects.filter(primary_company_id=self.object).update(primary_company_id=None)
        
        try:
            employer_profile = request.user.employer_profile
            if employer_profile.primary_company_id == self.object:
                other_companies = Company.objects.filter(
                    owner=request.user, is_active=True
                ).exclude(id=self.object.id)
                if other_companies.exists():
                    employer_profile.primary_company_id = other_companies.first()
                else:
                    employer_profile.primary_company_id = None
                employer_profile.save()
        except EmployerProfile.DoesNotExist:
            pass
        
        # Soft delete
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
    """Set a company as primary"""
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
    """Manage company documents"""
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
    """Company statistics view"""
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


# ============ ADMIN VIEWS ============
@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_dashboard(request):
    """Admin dashboard"""
    admin_profile, gettext = AdminProfile.objects.get_or_create(user=request.user)
    today = timezone.now().date()
    
    context = {
        "admin_profile": admin_profile,
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
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def admin_management(request):
    """Manage administrators"""
    if not is_main_admin(request.user):
        messages.error(request, _("Access denied"))
        return redirect("accounts:admin_dashboard")
    
    return render(request, "accounts/admin_management.html", {
        "admins": CustomUser.objects.filter(user_type__in=["admin", "main_admin"]),
    })


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_company_management(request):
    """Manage companies"""
    search_query = request.GET.get("q", "")
    verification_filter = request.GET.get("verification", "all")
    active_filter = request.GET.get("active", "all")
    
    companies = Company.objects.all()
    
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
    })


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def toggle_company_verification(request, pk):
    """Toggle company verification status"""
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
@user_passes_test(is_admin, login_url="accounts:admin_login")
def toggle_company_status(request, pk):
    """Toggle company active status"""
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
@user_passes_test(is_admin, login_url="accounts:admin_login")
def company_detail_admin(request, pk):
    """View company details (admin version)"""
    company = get_object_or_404(Company, pk=pk)
    
    return render(request, "accounts/admin_company_detail.html", {
        "company": company,
        "jobs": Job.objects.filter(company=company),
        "active_jobs": Job.objects.filter(company=company, is_active=True),
        "total_applications": JobApplication.objects.filter(job__company=company).count(),
        "documents": company.documents.all(),
        "activities": UserActivity.objects.filter(related_company=company).order_by("-created_at")[:20],
    })


@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
def create_admin_account(request):
    """Create admin account (main admin only)"""
    if request.method == "POST":
        form = AdminProfileForm(request.POST)
        if form.is_valid():
            try:
                # Проверка существования пользователя с таким email или username
                if CustomUser.objects.filter(email=form.cleaned_data["email"]).exists():
                    messages.error(request, "Пользователь с таким email уже существует")
                    return render(request, "accounts/create_admin_account.html", {"form": form})
                
                if CustomUser.objects.filter(username=form.cleaned_data["username"]).exists():
                    messages.error(request, "Пользователь с таким именем уже существует")
                    return render(request, "accounts/create_admin_account.html", {"form": form})
                
                # Создаем пользователя
                user = CustomUser.objects.create_user(
                    username=form.cleaned_data["username"],
                    email=form.cleaned_data["email"],
                    first_name=form.cleaned_data["first_name"],
                    last_name=form.cleaned_data["last_name"],
                    user_type="admin",
                )
                user.set_password(form.cleaned_data["password1"])
                user.save()
                
                # Даем время сигналу отработать (если он включен)
                import time
                time.sleep(0.1)
                
                # Используем update_or_create для профиля администратора
                # Это безопаснее, чем get_or_create, так как обновит существующий профиль
                admin_profile, created = AdminProfile.objects.update_or_create(
                    user=user,
                    defaults={
                        "can_manage_students": form.cleaned_data.get("can_manage_students", True),
                        "can_manage_employers": form.cleaned_data.get("can_manage_employers", True),
                        "can_manage_companies": form.cleaned_data.get("can_manage_companies", True),
                        "can_manage_jobs": form.cleaned_data.get("can_manage_jobs", True),
                        "can_manage_resumes": form.cleaned_data.get("can_manage_resumes", True),
                        "can_view_statistics": form.cleaned_data.get("can_view_statistics", True),
                    }
                )
                
                create_user_activity(request.user, "user_create", f"Created admin account: {user.username}")
                messages.success(request, _("Admin account created successfully!"))
                return redirect("accounts:admin_management")
                
            except Exception as e:
                messages.error(request, f"Ошибка при создании администратора: {str(e)}")
                return render(request, "accounts/create_admin_account.html", {"form": form})
    else:
        form = AdminProfileForm()
    
    return render(request, "accounts/create_admin_account.html", {"form": form})


# ============ PROFILE VIEWS ============
# @login_required
# def profile_view(request, user_id=None):
#     """View user profile"""
#     user = request.user if not user_id else get_object_or_404(CustomUser, id=user_id)
#     is_own_profile = (user == request.user)
    
#     if not is_own_profile:
#         session_key = f"profile_viewed_{user.id}"
#         if not request.session.get(session_key):
#             user.profile_views = F('profile_views') + 1
#             user.save()
#             user.refresh_from_db()
#             request.session[session_key] = True
#             request.session.set_expiry(86400)
#             create_user_activity(request.user, "profile_view", f"Viewed {user.username}'s profile")
    
#     context = {
#         "profile_user": user,
#         "is_own_profile": is_own_profile,
#     }
    
#     if user.is_student:
#         profile, _ = StudentProfile.objects.get_or_create(user=user)
#         resumes = CV.objects.filter(user=user, is_active=True)
#         context.update({
#             "profile": profile,
#             "resumes": resumes,
#             "applications_count": JobApplication.objects.filter(user=user).count(),
#         })
#         template_name = "accounts/student_profile.html"
#     elif user.is_employer:
#         profile, _ = EmployerProfile.objects.get_or_create(user=user)
#         owned_companies = Company.objects.filter(owner=user, is_active=True)
#         context.update({
#             "profile": profile,
#             "owned_companies": owned_companies,
#             "total_companies": owned_companies.count(),
#         })
#         template_name = "accounts/employer_profile.html"
#     elif user.is_admin:
#         profile, _ = AdminProfile.objects.get_or_create(user=user)
#         context["profile"] = profile
#         template_name = "accounts/admin_profile.html"
#     else:
#         template_name = "accounts/profile_base.html"
    
#     return render(request, template_name, context)

@login_required
def profile_view(request, user_id=None):
    """View user profile"""
    user = request.user if not user_id else get_object_or_404(CustomUser, id=user_id)
    is_own_profile = (user == request.user)
    
    if not is_own_profile:
        session_key = f"profile_viewed_{user.id}"
        if not request.session.get(session_key):
            user.profile_views = F('profile_views') + 1
            user.save()
            user.refresh_from_db()
            request.session[session_key] = True
            request.session.set_expiry(86400)
            create_user_activity(request.user, "profile_view", f"Viewed {user.username}'s profile")
    
    context = {
        "profile_user": user,
        "is_own_profile": is_own_profile,
    }
    
    if user.is_student:
        profile, created = StudentProfile.objects.get_or_create(user=user)
        # ИСПРАВЛЕНО: фильтруем по student_profile, а не по user
        resumes = CV.objects.filter(user=profile, status='published')
        context.update({
            "profile": profile,
            "resumes": resumes,
            "applications_count": JobApplication.objects.filter(user=user).count(),
        })
        template_name = "accounts/student_profile.html"
    elif user.is_employer:
        profile, created = EmployerProfile.objects.get_or_create(user=user)
        # ФИЛЬТРУЕМ ТОЛЬКО АКТИВНЫЕ КОМПАНИИ
        owned_companies = Company.objects.filter(owner=user, is_active=True)
        
        # Получаем первичную компанию, только если она активна
        primary_company = None
        if profile.primary_company_id and profile.primary_company_id.is_active:
            primary_company = profile.primary_company_id
        elif owned_companies.exists():
            primary_company = owned_companies.first()
        
        # Активные вакансии только активных компаний
        if primary_company:
            active_jobs = Job.objects.filter(
                company=primary_company,
                is_active=True
            ).select_related('company')
            active_jobs_count = active_jobs.count()
            
            # Статистика для боковой панели
            jobs_posted = Job.objects.filter(company=primary_company).count()
            total_views = primary_company.total_views or 0
            total_applications = JobApplication.objects.filter(
                job__company=primary_company
            ).count()
        else:
            active_jobs = Job.objects.none()
            active_jobs_count = 0
            jobs_posted = 0
            total_views = 0
            total_applications = 0
        
        context.update({
            "profile": profile,
            "owned_companies": owned_companies,
            "total_companies": owned_companies.count(),
            "primary_company": primary_company,
            "active_jobs": active_jobs[:5],  # Ограничиваем количество
            "active_jobs_count": active_jobs_count,
            "jobs_posted": jobs_posted,
            "total_views": total_views,
            "total_applications": total_applications,
        })
        template_name = "accounts/employer_profile.html"
    elif user.is_admin:
        profile, created = AdminProfile.objects.get_or_create(user=user)
        context["profile"] = profile
        template_name = "accounts/admin_profile.html"
    else:
        template_name = "accounts/profile_base.html"
    
    return render(request, template_name, context)

# ============ NOTIFICATION VIEWS ============
@login_required
def notifications(request):
    """User notifications"""
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
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()
    
    next_url = request.GET.get('next', 'accounts:notifications')
    return redirect(next_url)


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read for current user"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    messages.success(request, _("All notifications marked as read"))
    
    next_url = request.GET.get('next', 'accounts:notifications')
    return redirect(next_url)


# ============ API ENDPOINTS ============
@login_required
@require_http_methods(["GET"])
def user_stats_api(request):
    """
    API endpoint to get authenticated user statistics.
    
    Returns user stats based on their role (student/employer/admin).
    Requires authentication.
    
    Returns JSON with:
    - user_id: User's ID
    - username: User's username
    - email: User's email
    - user_type: Type of user (student/employer/admin/main_admin)
    - is_staff: Whether user is staff
    - is_superuser: Whether user is superuser
    - role-specific statistics based on user type
    """
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
    
    # Add role-specific statistics
    if user_type == "student":
        try:
            profile = StudentProfile.objects.get(user=user)
            stats.update({
                "role": "student",
                "full_name": profile.full_name if hasattr(profile, 'full_name') else user.get_full_name(),
                "phone_number": str(profile.phone_number) if hasattr(profile, 'phone_number') else None,
                "university": getattr(profile, 'university', None),
                "applications_count": JobApplication.objects.filter(user=user).count(),
                "cv_count": CV.objects.filter(user=user).count(),
            })
        except StudentProfile.DoesNotExist:
            stats["role"] = "student"
            stats["error"] = "Student profile not found"
            
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
            
    elif user_type in ["admin", "main_admin"]:
        stats.update({
            "role": user_type,
            "full_name": user.get_full_name() or user.username,
        })
    
    return JsonResponse(stats, status=200)


# ============ ADDITIONAL ADMIN VIEWS ============
@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def admin_employer_management(request):
    """Manage employers and their accounts"""
    employers = CustomUser.objects.filter(user_type="employer").select_related('employerprofile')
    
    search_query = request.GET.get('search', '')
    if search_query:
        employers = employers.filter(
            Q(username__icontains=search_query) | 
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    paginator = Paginator(employers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, "accounts/admin_employer_management.html", {
        "page_obj": page_obj,
        "search_query": search_query,
        "total_employers": CustomUser.objects.filter(user_type="employer").count(),
    })


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def user_management(request):
    """Manage user accounts"""
    users = CustomUser.objects.all().order_by("-date_joined")
    
    # Support both legacy `type` and canonical `user_type` query params.
    user_type_filter = request.GET.get("user_type") or request.GET.get("type", "")
    user_type_mapping = {
        "all": "",
        "students": "student",
        "employers": "employer",
    }
    normalized_filter = user_type_mapping.get(user_type_filter, user_type_filter)
    if normalized_filter == "admins":
        users = users.filter(user_type__in=["admin", "main_admin"])
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
        "total_users": CustomUser.objects.count(),
    })


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def user_detail(request, user_id):
    """View user details"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Check access: only admin, main_admin or the user themselves can view
    if not (request.user.is_admin or request.user.is_main_admin or request.user.id == user_id):
        messages.error(request, _("You don't have permission to view this profile"))
        return redirect("accounts:user_management")
    
    # Get profile based on user type
    profile = None
    if user.user_type == "student":
        try:
            profile = StudentProfile.objects.get(user=user)
        except StudentProfile.DoesNotExist:
            pass
    elif user.user_type == "employer":
        try:
            profile = EmployerProfile.objects.get(user=user)
        except EmployerProfile.DoesNotExist:
            pass
    elif user.user_type in ["admin", "main_admin"]:
        try:
            profile = AdminProfile.objects.get(user=user)
        except AdminProfile.DoesNotExist:
            pass
    
    context = {
        "profile_user": user,
        "profile": profile,
        "activities": UserActivity.objects.filter(user=user).order_by("-created_at")[:20],
    }
    
    if user.user_type == "student":
        student_profile = StudentProfile.objects.filter(user=user).first()
        context.update({
            "applications": JobApplication.objects.filter(user=user).count(),
            "cvs": CV.objects.filter(user=student_profile).count() if student_profile else 0,
        })
    elif user.user_type == "employer":
        context.update({
            "companies": Company.objects.filter(owner=user).count(),
            "jobs": Job.objects.filter(company__owner=user).distinct().count(),
        })
    
    return render(request, "accounts/user_detail.html", context)


@login_required
@user_passes_test(is_admin, login_url="accounts:admin_login")
def toggle_user_status(request, user_id):
    """Toggle user active/inactive status"""
    if request.method == "POST":
        user = get_object_or_404(CustomUser, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        status_str = "activated" if user.is_active else "deactivated"
        create_user_activity(request.user, "user_update", f"User {status_str}: {user.username}")
        
        messages.success(request, _(f"User {status_str}"))
    
    return redirect("accounts:user_detail", user_id=user_id)


@login_required
@user_passes_test(is_main_admin, login_url="accounts:admin_login")
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
            profile.primary_company = company
            profile.save()

            # ---- LOG ----
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
    
    if user_type == "student":
        return redirect("accounts:student_dashboard")
    elif user_type == "employer":
        return redirect("accounts:employer_dashboard")
    elif user_type in ["admin", "main_admin"]:
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
            can_manage_students=True,
            can_manage_employers=True,
            can_manage_companies=True,
            can_manage_jobs=True,
            can_manage_resumes=True,
            can_view_statistics=True,
        )
        
        login(request, admin_user)
        messages.success(request, _("System setup completed successfully!"))
        return redirect("accounts:admin_dashboard")
    
    return render(request, "accounts/initial_setup.html")


# ============ ACTIVITY LOG VIEW ============
@login_required(login_url='accounts:employer_login')
def activity_log(request):
    """Display user activity log with pagination and filtering"""
    # Get the current user's activities
    activities = UserActivity.objects.filter(user=request.user).order_by('-created_at')
    
    # Optional filtering by activity type
    activity_type = request.GET.get('type')
    if activity_type:
        activities = activities.filter(activity_type=activity_type)
    
    # Pagination
    paginator = Paginator(activities, 20)  # Show 20 activities per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all activity types for filter dropdown
    activity_types = UserActivity.ACTIVITY_TYPES
    
    context = {
        'page_obj': page_obj,
        'activities': page_obj.object_list,
        'activity_types': activity_types,
        'selected_type': activity_type,
    }
    
    return render(request, 'accounts/activity_log.html', context)


# ============ OAUTH AUTHENTICATION VIEWS ============

def student_oauth_login(request):
    """
    Перенаправление на страницу авторизации OAuth сервиса.
    
    Этапы:
    1. Генерация state параметра для защиты от CSRF
    2. Формирование URL для перенаправления
    3. Сохранение state в сессии
    4. Redirect к OAuth провайдеру
    """
    from django.utils.crypto import get_random_string
    from urllib.parse import urlencode
    
    try:
        oauth_config = settings.OAUTH_PROVIDER
        
        # Генерация уникального state
        state = get_random_string(length=32)
        
        # Сохранение state в сессии
        request.session['oauth_state'] = state
        request.session.set_expiry(600)  # 10 минут
        
        # Формирование параметров запроса
        params = {
            'client_id': oauth_config['CLIENT_ID'],
            'redirect_uri': oauth_config['REDIRECT_URI'],
            'response_type': 'code',
            'scope': oauth_config.get('SCOPE', 'profile email'),
            'state': state,
        }
        
        # Создание URL для перенаправления
        authorize_url = f"{oauth_config['AUTHORIZE_URL']}?{urlencode(params)}"
        
        return redirect(authorize_url)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth login error: {str(e)}")
        messages.error(request, _("Failed to start OAuth authentication. Please try again."))
        return redirect("accounts:hemis_login")


def oauth_callback(request):
    """
    Callback endpoint для обработки ответа от OAuth сервиса.
    
    Этапы:
    1. Проверка наличия ошибок
    2. Проверка state параметра
    3. Извлечение authorization code
    4. Аутентификация через бэкенд
    5. Вход пользователя в систему
    6. Перенаправление на dashboard
    """
    from django.contrib.auth import authenticate
    
    try:
        # Проверка параметра error
        error = request.GET.get('error')
        if error:
            error_description = request.GET.get('error_description', 'Unknown error')
            messages.error(request, _("OAuth error: %(error)s") % {'error': error_description})
            return redirect("accounts:hemis_login")
        
        # Проверка state на соответствие сохраненному
        state = request.GET.get('state')
        session_state = request.session.get('oauth_state')
        
        if not state or not session_state or state != session_state:
            messages.error(request, _("Invalid state parameter. Please try again."))
            return redirect("accounts:hemis_login")
        
        # Очистка state из сессии
        del request.session['oauth_state']
        
        # Извлечение code из GET параметров
        code = request.GET.get('code')
        if not code:
            messages.error(request, _("No authorization code received. Please try again."))
            return redirect("accounts:hemis_login")
        
        # Вызов authenticate() с передачей code и state
        user = authenticate(request, code=code, state=state)
        
        if user is None:
            messages.error(request, _("Failed to authenticate. Please try again."))
            return redirect("accounts:hemis_login")
        
        # Если пользователь найден - login()
        login(request, user)
        
        # Создание UserActivity записи
        create_user_activity(
            user,
            "login",
            "Student logged in via OAuth",
            get_client_ip(request),
            request.META.get("HTTP_USER_AGENT", "")
        )
        
        messages.success(request, _("Successfully logged in!"))
        
        # Перенаправление на dashboard
        return redirect("accounts:student_dashboard")
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"OAuth callback error: {str(e)}")
        messages.error(request, _("An error occurred during authentication. Please try again."))
        return redirect("accounts:hemis_login")
    


def check_bruteforce_protection(ip_address, username=None):
    """
    Проверка защиты от брутфорс-атак.
    Возвращает (is_allowed, error_message, remaining_time)
    """
    # Проверка блокировки по IP
    ip_block_key = f'ip_blocked_{ip_address}'
    if cache.get(ip_block_key):
        # Получаем время окончания блокировки
        ttl = cache.ttl(ip_block_key)
        remaining_minutes = max(1, ttl // 60)
        return False, f"IP адрес заблокирован на {remaining_minutes} минут", remaining_minutes
    
    # Проверка блокировки по пользователю
    if username:
        user_block_key = f'user_blocked_{username}'
        if cache.get(user_block_key):
            ttl = cache.ttl(user_block_key)
            remaining_minutes = max(1, ttl // 60)
            return False, f"Аккаунт заблокирован на {remaining_minutes} минут", remaining_minutes
    
    # Проверка количества попыток
    ip_attempts_key = f'login_attempts_ip_{ip_address}'
    attempts_ip = cache.get(ip_attempts_key, 0)
    
    if username:
        user_attempts_key = f'login_attempts_user_{username}'
        attempts_user = cache.get(user_attempts_key, 0)
    else:
        attempts_user = 0
    
    max_attempts = 10
    warning_threshold = 5
    
    # Если превышено максимальное количество попыток
    if attempts_ip >= max_attempts or attempts_user >= max_attempts:
        # Автоматически блокируем
        block_time = 900  # 15 минут
        cache.set(ip_block_key, True, block_time)
        if username:
            cache.set(user_block_key, True, block_time)
        
        return False, "Слишком много неудачных попыток. Доступ заблокирован на 15 минут.", 15
    
    # Если близко к лимиту - предупреждение
    if attempts_ip >= warning_threshold or attempts_user >= warning_threshold:
        remaining = max_attempts - max(attempts_ip, attempts_user)
        return True, f"Внимание: осталось {remaining} попыток", None
    
    return True, None, None

def record_failed_login_attempt(ip_address, username=None):
    """Запись неудачной попытки входа"""
    ip_key = f'login_attempts_ip_{ip_address}'
    attempts = cache.get(ip_key, 0) + 1
    cache.set(ip_key, attempts, 300)  # Храним 5 минут
    
    if username:
        user_key = f'login_attempts_user_{username}'
        user_attempts = cache.get(user_key, 0) + 1
        cache.set(user_key, user_attempts, 300)
    
    # Логирование для мониторинга
    print(f"Failed login attempt: IP={ip_address}, User={username}, Attempts={attempts}")

def clear_login_attempts(ip_address, username=None):
    """Очистка счетчиков при успешном входе"""
    cache.delete(f'login_attempts_ip_{ip_address}')
    cache.delete(f'ip_blocked_{ip_address}')
    
    if username:
        cache.delete(f'login_attempts_user_{username}')
        cache.delete(f'user_blocked_{username}')

def get_login_attempts_info(ip_address, username=None):
    """Получение информации о попытках входа"""
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



class CustomTokenObtainSerializer(TokenObtainPairSerializer):
    """
    Кастомный сериализатор токенов с проверкой типа пользователя.
    """
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Проверяем тип пользователя
        user = self.user
        
        # Если студент пытается получить токен через пароль - запрещаем
        if user.user_type == 'student':
            raise serializers.ValidationError({
                "detail": "Студенты должны использовать OAuth авторизацию через /accounts/oauth/login/"
            })
        
        # Добавляем информацию о пользователе
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
    """
    Получение JWT токенов ТОЛЬКО для работодателей и администраторов.
    Студентам запрещено использовать этот endpoint.
    """
    serializer_class = CustomTokenObtainSerializer
