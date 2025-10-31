from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
from django.db.models import Count, Q
from django.core.paginator import Paginator
import requests
import json
from datetime import datetime, timedelta

from .models import (
    CustomUser, EmployerProfile, StudentProfile, AdminProfile, 
    HemisAuth, UserActivity, Notification
)
from .forms import (
    EmployerRegistrationForm, EmployerProfileForm, 
    StudentProfileForm, AdminProfileForm, UserUpdateForm
)

# Utility functions
def is_student(user):
    return user.is_authenticated and user.is_student

def is_employer(user):
    return user.is_authenticated and user.is_employer and user.is_active_employer

def is_admin(user):
    return user.is_authenticated and user.is_admin

def is_main_admin(user):
    return user.is_authenticated and user.is_main_admin

def can_manage_users(user):
    return user.is_authenticated and user.user_type in ['admin', 'main_admin']

def create_user_activity(user, activity_type, description='', ip_address=None, user_agent=''):
    """Создание записи активности пользователя"""
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )

# Hemis API Integration
class HemisAPI:
    BASE_URL = "https://hemis.uz/api/v1"  # Замените на реальный URL Hemis API
    
    @staticmethod
    def get_auth_url():
        """Получить URL для авторизации через Hemis"""
        return f"{HemisAPI.BASE_URL}/oauth/authorize"
    
    @staticmethod
    def get_token(code):
        """Получить access token по коду"""
        try:
            response = requests.post(
                f"{HemisAPI.BASE_URL}/oauth/token",
                data={
                    'code': code,
                    'grant_type': 'authorization_code',
                    'client_id': settings.HEMIS_CLIENT_ID,
                    'client_secret': settings.HEMIS_CLIENT_SECRET
                }
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None
    
    @staticmethod
    def get_user_info(access_token):
        """Получить информацию о пользователе"""
        try:
            response = requests.get(
                f"{HemisAPI.BASE_URL}/user",
                headers={'Authorization': f'Bearer {access_token}'}
            )
            return response.json() if response.status_code == 200 else None
        except:
            return None

# Authentication Views
def hemis_login(request):
    """Перенаправление на Hemis для авторизации"""
    hemis_auth_url = HemisAPI.get_auth_url()
    return redirect(hemis_auth_url)

@csrf_exempt
def hemis_callback(request):
    """Callback от Hemis после авторизации"""
    code = request.GET.get('code')
    if not code:
        messages.error(request, _("Hemis autentifikatsiyada xatolik yuz berdi"))
        return redirect('accounts:login')
    
    # Получаем токен
    token_data = HemisAPI.get_token(code)
    if not token_data:
        messages.error(request, _("Token olishda xatolik"))
        return redirect('accounts:login')
    
    # Получаем информацию о пользователе
    user_info = HemisAPI.get_user_info(token_data['access_token'])
    if not user_info:
        messages.error(request, _("Foydalanuvchi ma'lumotlarini olishda xatolik"))
        return redirect('accounts:login')
    
    # Проверяем существует ли пользователь
    try:
        hemis_auth = HemisAuth.objects.get(hemis_id=user_info['id'])
        user = hemis_auth.user
        
        # Обновляем токены
        hemis_auth.access_token = token_data['access_token']
        hemis_auth.refresh_token = token_data['refresh_token']
        hemis_auth.token_expires = datetime.now() + timedelta(seconds=token_data['expires_in'])
        hemis_auth.hemis_user_data = user_info
        hemis_auth.save()
        
    except HemisAuth.DoesNotExist:
        # Создаем нового пользователя
        username = f"hemis_{user_info['id']}"
        email = user_info.get('email', '')
        
        # Создаем пользователя
        user = CustomUser.objects.create_user(
            username=username,
            email=email,
            first_name=user_info.get('first_name', ''),
            last_name=user_info.get('last_name', ''),
            user_type='student'
        )
        
        # Создаем Hemis auth запись
        hemis_auth = HemisAuth.objects.create(
            user=user,
            hemis_id=user_info['id'],
            access_token=token_data['access_token'],
            refresh_token=token_data['refresh_token'],
            token_expires=datetime.now() + timedelta(seconds=token_data['expires_in']),
            hemis_user_data=user_info
        )
        
        # Создаем студенческий профиль
        StudentProfile.objects.create(
            user=user,
            student_id=user_info.get('student_id', ''),
            faculty=user_info.get('faculty', ''),
            specialty=user_info.get('specialty', ''),
            education_level=user_info.get('education_level', 'bachelor')
        )
        
        messages.success(request, _("Muvaffaqiyatli ro'yxatdan o'tdingiz!"))
    
    # Логиним пользователя
    login(request, user)
    
    # Создаем запись активности
    create_user_activity(
        user=user,
        activity_type='login',
        description='Hemis orqali tizimga kirish',
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', '')
    )
    
    messages.success(request, _("Xush kelibsiz!"))
    return redirect('home')

def employer_login(request):
    """Вход для работодателей"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and user.is_employer and user.is_active_employer:
            login(request, user)
            
            # Создаем запись активности
            create_user_activity(
                user=user,
                activity_type='login',
                description='Ish beruvchi sifatida tizimga kirish',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, _("Xush kelibsiz!"))
            return redirect('employer_dashboard')
        else:
            messages.error(request, _("Login yoki parol noto'g'ri yoki sizda kirish huquqi yo'q"))
    
    return render(request, 'accounts/employer_login.html')

def admin_login(request):
    """Вход для администраторов"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and (user.is_admin or user.is_main_admin):
            login(request, user)
            
            # Создаем запись активности
            create_user_activity(
                user=user,
                activity_type='login',
                description='Admin sifatida tizimga kirish',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, _("Xush kelibsiz!"))
            return redirect('admin_dashboard.html')
        else:
            messages.error(request, _("Login yoki parol noto'g'ri yoki sizda admin huquqlari yo'q"))
    
    return render(request, 'accounts/admin_login.html')

def logout_view(request):
    """Выход из системы"""
    if request.user.is_authenticated:
        create_user_activity(
            user=request.user,
            activity_type='login',
            description='Tizimdan chiqish',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    logout(request)
    messages.success(request, _("Siz tizimdan chiqdingiz"))
    return redirect('home.html')

# Employer Views
@login_required
@user_passes_test(is_employer, login_url='employer_login')
def employer_dashboard(request):
    """Дашборд работодателя"""
    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    
    # Статистика работодателя
    stats = {
        'active_jobs': 10,  # Замените на реальные запросы к модели Job
        'total_applications': 25,
        'profile_views': employer_profile.total_views,
        'jobs_posted': employer_profile.jobs_posted,
    }
    
    context = {
        'employer_profile': employer_profile,
        'stats': stats,
    }
    
    return render(request, 'accounts/employer_dashboard.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='admin_login')
def create_employer_account(request):
    """Создание аккаунта работодателя (только для админов)"""
    if request.method == 'POST':
        user_form = EmployerRegistrationForm(request.POST)
        profile_form = EmployerProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            # Создаем пользователя
            user = user_form.save(commit=False)
            user.user_type = 'employer'
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            # Создаем профиль работодателя
            employer_profile = profile_form.save(commit=False)
            employer_profile.user = user
            employer_profile.save()
            
            # Создаем запись активности
            create_user_activity(
                user=request.user,
                activity_type='job_create',
                description=f"Yangi ish beruvchi yaratildi: {employer_profile.company_name}"
            )
            
            messages.success(request, _("Ish beruvchi akkaunti muvaffaqiyatli yaratildi!"))
            return redirect('admin_employer_management')
    else:
        user_form = EmployerRegistrationForm()
        profile_form = EmployerProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/create_employer_account.html', context)

@login_required
@user_passes_test(is_employer, login_url='employer_login')
def employer_profile_update(request):
    """Редактирование профиля работодателя"""
    employer_profile = get_object_or_404(EmployerProfile, user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = EmployerProfileForm(request.POST, request.FILES, instance=employer_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            create_user_activity(
                user=request.user,
                activity_type='profile_update',
                description='Ish beruvchi profili yangilandi'
            )
            
            messages.success(request, _("Profil muvaffaqiyatli yangilandi!"))
            return redirect('employer_dashboard')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = EmployerProfileForm(instance=employer_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/employer_profile_update.html', context)

# Student Views
@login_required
@user_passes_test(is_student, login_url='hemis_login')
def student_dashboard(request):
    """Дашборд студента"""
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Статистика студента
    stats = {
        'resumes_created': student_profile.resumes_created,
        'jobs_applied': student_profile.jobs_applied,
        'profile_views': request.user.profile_views,
    }
    
    context = {
        'student_profile': student_profile,
        'stats': stats,
    }
    
    return render(request, 'accounts/student_dashboard.html', context)

@login_required
@user_passes_test(is_student, login_url='hemis_login')
def student_profile_update(request):
    """Редактирование профиля студента"""
    student_profile = get_object_or_404(StudentProfile, user=request.user)
    
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = StudentProfileForm(request.POST, instance=student_profile)
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            
            create_user_activity(
                user=request.user,
                activity_type='profile_update',
                description='Talaba profili yangilandi'
            )
            
            messages.success(request, _("Profil muvaffaqiyatli yangilandi!"))
            return redirect('student_dashboard')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = StudentProfileForm(instance=student_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/student_profile_update.html', context)

# Admin Views
@login_required
@user_passes_test(is_admin, login_url='admin_login')
def admin_dashboard(request):
    """Дашборд администратора"""
    admin_profile = get_object_or_404(AdminProfile, user=request.user)
    
    # Статистика для админа
    today = datetime.now().date()
    
    stats = {
        'total_students': CustomUser.objects.filter(user_type='student').count(),
        'total_employers': CustomUser.objects.filter(user_type='employer').count(),
        'active_today': UserActivity.objects.filter(
            created_at__date=today,
            activity_type='login'
        ).values('user').distinct().count(),
        'total_jobs': 150,  # Замените на реальные запросы
        'total_resumes': 300,  # Замените на реальные запросы
    }
    
    # Последняя активность
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'admin_profile': admin_profile,
        'stats': stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@user_passes_test(is_main_admin, login_url='admin_login')
def create_admin_account(request):
    """Создание аккаунта администратора (только для главного админа)"""
    if request.method == 'POST':
        form = AdminProfileForm(request.POST)
        if form.is_valid():
            # Создаем пользователя
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                user_type='admin'
            )
            user.set_password(form.cleaned_data['password1'])
            user.save()
            
            # Создаем профиль администратора
            admin_profile = AdminProfile.objects.create(
                user=user,
                can_manage_students=form.cleaned_data['can_manage_students'],
                can_manage_employers=form.cleaned_data['can_manage_employers'],
                can_manage_jobs=form.cleaned_data['can_manage_jobs'],
                can_manage_resumes=form.cleaned_data['can_manage_resumes'],
                can_view_statistics=form.cleaned_data['can_view_statistics'],
            )
            
            create_user_activity(
                user=request.user,
                activity_type='profile_update',
                description=f"Yangi admin yaratildi: {user.username}"
            )
            
            messages.success(request, _("Admin akkaunti muvaffaqiyatli yaratildi!"))
            return redirect('admin_management')
    else:
        form = AdminProfileForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/create_admin_account.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='admin_login')
def user_management(request):
    """Управление пользователями"""
    user_type = request.GET.get('type', 'all')
    
    users = CustomUser.objects.all()
    
    if user_type == 'students':
        users = users.filter(user_type='student')
    elif user_type == 'employers':
        users = users.filter(user_type='employer')
    elif user_type == 'admins':
        users = users.filter(user_type__in=['admin', 'main_admin'])
    
    # Пагинация
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'user_type': user_type,
        'total_users': users.count(),
    }
    
    return render(request, 'accounts/user_management.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='admin_login')
def user_detail(request, user_id):
    """Детальная информация о пользователе"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Получаем соответствующий профиль
    profile = None
    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
    elif user.is_employer:
        profile = get_object_or_404(EmployerProfile, user=user)
    elif user.is_admin or user.is_main_admin:
        profile = get_object_or_404(AdminProfile, user=user)
    
    # Активность пользователя
    user_activities = UserActivity.objects.filter(user=user).order_by('-created_at')[:20]
    
    context = {
        'user': user,
        'profile': profile,
        'activities': user_activities,
    }
    
    return render(request, 'accounts/user_detail.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='admin_login')
def toggle_user_status(request, user_id):
    """Активация/деактивация пользователя"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Главный админ не может быть деактивирован
        if user.is_main_admin:
            messages.error(request, _("Bosh adminni deaktiv qilib bo'lmaydi"))
            return redirect('user_management')
        
        user.is_active = not user.is_active
        user.save()
        
        action = "faollashtirildi" if user.is_active else "deaktiv qilindi"
        create_user_activity(
            user=request.user,
            activity_type='profile_update',
            description=f"Foydalanuvchi {action}: {user.username}"
        )
        
        messages.success(request, _(f"Foydalanuvchi {action}"))
    
    return redirect('user_management')

# Profile Views
@login_required
def profile_view(request, user_id=None):
    """Просмотр профиля пользователя"""
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
    else:
        user = request.user
    
    # Увеличиваем счетчик просмотров если смотрим чужой профиль
    if user != request.user:
        user.profile_views += 1
        user.save()
        
        create_user_activity(
            user=request.user,
            activity_type='profile_view',
            description=f"{user.username} profilini ko'rdi"
        )
    
    # Получаем соответствующий профиль
    profile = None
    template_name = 'accounts/profile_base.html'
    
    if user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
        template_name = 'accounts/student_profile.html'
    elif user.is_employer:
        profile = get_object_or_404(EmployerProfile, user=user)
        template_name = 'accounts/employer_profile.html'
    elif user.is_admin or user.is_main_admin:
        profile = get_object_or_404(AdminProfile, user=user)
        template_name = 'accounts/admin_profile.html'
    
    context = {
        'profile_user': user,
        'profile': profile,
    }
    
    return render(request, template_name, context)

# Notification Views
@login_required
def notifications(request):
    """Список уведомлений пользователя"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'accounts/notifications.html', context)

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, notification_id):
    """Пометить уведомление как прочитанное"""
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.mark_as_read()
    
    return JsonResponse({'success': True})

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Пометить все уведомления как прочитанные"""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    
    return JsonResponse({'success': True})

# API Views
@login_required
def user_stats_api(request):
    """API для статистики пользователей"""
    if not request.user.is_admin and not request.user.is_main_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_users': CustomUser.objects.count(),
        'students_count': CustomUser.objects.filter(user_type='student').count(),
        'employers_count': CustomUser.objects.filter(user_type='employer').count(),
        'admins_count': CustomUser.objects.filter(user_type__in=['admin', 'main_admin']).count(),
        'active_today': UserActivity.objects.filter(
            created_at__date=today,
            activity_type='login'
        ).values('user').distinct().count(),
        'new_this_week': CustomUser.objects.filter(
            date_joined__gte=week_ago
        ).count(),
    }
    
    return JsonResponse(stats)

# Utility functions
def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Home views for different user types
def home_redirect(request):
    """Перенаправление на соответствующую домашнюю страницу"""
    if request.user.is_authenticated:
        if request.user.is_student:
            return redirect('student_dashboard')
        elif request.user.is_employer:
            return redirect('employer_dashboard')
        elif request.user.is_admin or request.user.is_main_admin:
            return redirect('admin_dashboard')
    
    # Для гостей - главная страница
    return redirect('home')

def home(request):
    """Главная страница для гостей"""
    if request.user.is_authenticated:
        return home_redirect(request)
    
    return render(request, 'home.html')