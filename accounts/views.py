# accounts/views.py - ИСПРАВЛЕННАЯ ВЕРСИЯ
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
from django.conf import settings

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
    return user.is_authenticated and hasattr(user, 'is_student') and user.is_student

def is_employer(user):
    return user.is_authenticated and hasattr(user, 'is_employer') and user.is_employer and user.is_active_employer

def is_admin(user):
    return user.is_authenticated and hasattr(user, 'is_admin') and user.is_admin

def is_main_admin(user):
    return user.is_authenticated and hasattr(user, 'is_main_admin') and user.is_main_admin

def can_manage_users(user):
    return user.is_authenticated and hasattr(user, 'user_type') and user.user_type in ['admin', 'main_admin']

def create_user_activity(user, activity_type, description='', ip_address=None, user_agent=''):
    """Создание записи активности пользователя"""
    UserActivity.objects.create(
        user=user,
        activity_type=activity_type,
        description=description,
        ip_address=ip_address,
        user_agent=user_agent
    )

# Hemis API Integration (ЗАГЛУШКА - временно отключаем)
class HemisAPI:
    BASE_URL = "https://hemis.uz/api/v1"
    
    @staticmethod
    def get_auth_url():
        """Заглушка для Hemis авторизации"""
        return "/"  # Временно возвращаем на главную
    
    @staticmethod
    def get_token(code):
        return None
    
    @staticmethod
    def get_user_info(access_token):
        return None

# Authentication Views
def hemis_login(request):
    """Временная заглушка для Hemis авторизации"""
    messages.info(request, _("Hemis tizimi hozircha ishlamayapti. Iltimos, boshqa login usulidan foydalaning."))
    return redirect('home')

@csrf_exempt
def hemis_callback(request):
    """Временная заглушка для Hemis callback"""
    messages.info(request, _("Hemis tizimi hozircha ishlamayapti."))
    return redirect('home')

# ВРЕМЕННЫЙ ВХОД ДЛЯ ТЕСТИРОВАНИЯ - УДАЛИТЕ ПОСЛЕ НАСТРОЙКИ HEMIS
def temp_student_login(request):
    """Временный вход для студентов (тестирование)"""
    if request.method == 'POST':
        # Создаем тестового студента если нет
        student, created = CustomUser.objects.get_or_create(
            username='test_student',
            defaults={
                'email': 'student@test.uz',
                'first_name': 'Test',
                'last_name': 'Student',
                'user_type': 'student'
            }
        )
        if created:
            student.set_password('test123')
            student.save()
            StudentProfile.objects.create(user=student)
        
        user = authenticate(request, username='test_student', password='test123')
        if user:
            login(request, user)
            messages.success(request, _("Test student sifatida kirdingiz"))
            return redirect('student_dashboard')
    
    return render(request, 'accounts/temp_login.html', {'user_type': 'student'})

def employer_login(request):
    """Вход для работодателей - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and hasattr(user, 'is_employer') and user.is_employer:
            if hasattr(user, 'is_active_employer') and user.is_active_employer:
                login(request, user)
                create_user_activity(
                    user=user,
                    activity_type='login',
                    description='Ish beruvchi sifatida tizimga kirish',
                    ip_address=get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                messages.success(request, _("Xush kelibsiz!"))
                return redirect('accounts:employer_dashboard')
            else:
                messages.error(request, _("Sizning hisobingiz faol emas"))
        else:
            messages.error(request, _("Login yoki parol noto'g'ri yoki sizda kirish huquqi yo'q"))
    
    return render(request, 'accounts/employer_login.html')

def admin_login(request):
    """Вход для администраторов - ИСПРАВЛЕННАЯ ВЕРСИЯ"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None and (hasattr(user, 'is_admin') and user.is_admin or 
                               hasattr(user, 'is_main_admin') and user.is_main_admin):
            login(request, user)
            create_user_activity(
                user=user,
                activity_type='login',
                description='Admin sifatida tizimga kirish',
                ip_address=get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            messages.success(request, _("Xush kelibsiz!"))
            return redirect('accounts:admin_dashboard')
        else:
            messages.error(request, _("Login yoki parol noto'g'ri yoki sizda admin huquqlari yo'q"))
    
    return render(request, 'accounts/admin_login.html')

def logout_view(request):
    """Выход из системы"""
    if request.user.is_authenticated:
        create_user_activity(
            user=request.user,
            activity_type='logout',
            description='Tizimdan chiqish',
            ip_address=get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
    
    logout(request)
    messages.success(request, _("Siz tizimdan chiqdingiz"))
    return redirect('accounts:home')

# Employer Views
@login_required
@user_passes_test(is_employer, login_url='accounts:employer_login')
def employer_dashboard(request):
    """Дашборд работодателя"""
    try:
        employer_profile = EmployerProfile.objects.get(user=request.user)
    except EmployerProfile.DoesNotExist:
        employer_profile = EmployerProfile.objects.create(user=request.user)
        messages.info(request, _("Sizning profilingiz yaratildi. Iltimos, ma'lumotlaringizni to'ldiring."))
    
    stats = {
        'active_jobs': 0,  # Пока заглушка
        'total_applications': 0,
        'profile_views': employer_profile.total_views,
        'jobs_posted': employer_profile.jobs_posted,
    }
    
    context = {
        'employer_profile': employer_profile,
        'stats': stats,
    }
    
    return render(request, 'accounts/employer_dashboard.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='accounts:admin_login')
def create_employer_account(request):
    """Создание аккаунта работодателя"""
    if request.method == 'POST':
        user_form = EmployerRegistrationForm(request.POST)
        profile_form = EmployerProfileForm(request.POST, request.FILES)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save(commit=False)
            user.user_type = 'employer'
            user.set_password(user_form.cleaned_data['password1'])
            user.save()
            
            employer_profile = profile_form.save(commit=False)
            employer_profile.user = user
            employer_profile.save()
            
            create_user_activity(
                user=request.user,
                activity_type='user_create',
                description=f"Yangi ish beruvchi yaratildi: {employer_profile.company_name}"
            )
            
            messages.success(request, _("Ish beruvchi akkaunti muvaffaqiyatli yaratildi!"))
            return redirect('accounts:user_management')
    else:
        user_form = EmployerRegistrationForm()
        profile_form = EmployerProfileForm()
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/create_employer_account.html', context)

# Student Views  
@login_required
@user_passes_test(is_student, login_url='accounts:hemis_login')
def student_dashboard(request):
    """Дашборд студента"""
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = StudentProfile.objects.create(user=request.user)
        messages.info(request, _("Sizning profilingiz yaratildi. Iltimos, ma'lumotlaringizni to'ldiring."))
    
    stats = {
        'resumes_created': getattr(student_profile, 'resumes_created', 0),
        'jobs_applied': getattr(student_profile, 'jobs_applied', 0),
        'profile_views': getattr(request.user, 'profile_views', 0),
    }
    
    context = {
        'student_profile': student_profile,
        'stats': stats,
    }
    
    return render(request, 'accounts/student_dashboard.html', context)

# Admin Views
@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_dashboard(request):
    """Дашборд администратора"""
    try:
        admin_profile = AdminProfile.objects.get(user=request.user)
    except AdminProfile.DoesNotExist:
        admin_profile = AdminProfile.objects.create(user=request.user)
    
    today = datetime.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_users': CustomUser.objects.count(),
        'total_students': CustomUser.objects.filter(user_type='student').count(),
        'total_employers': CustomUser.objects.filter(user_type='employer').count(),
        'active_today': UserActivity.objects.filter(
            created_at__date=today
        ).values('user').distinct().count(),
        'total_jobs': 0,  # Заглушка
        'total_resumes': 0,  # Заглушка
        'new_this_week': CustomUser.objects.filter(date_joined__gte=week_ago).count(),
    }
    
    recent_activities = UserActivity.objects.select_related('user').order_by('-created_at')[:10]
    
    context = {
        'admin_profile': admin_profile,
        'stats': stats,
        'recent_activities': recent_activities,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)

# Остальные функции остаются без изменений...
# (user_management, user_detail, toggle_user_status, profile_view, notifications и т.д.)

# ДОБАВИМ НЕДОСТАЮЩИЕ VIEWS ДЛЯ ССЫЛОК В ШАБЛОНЕ
@login_required
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_management(request):
    """Управление администраторами (только для главного админа)"""
    if not request.user.is_main_admin:
        messages.error(request, _("Sizda bu sahifaga kirish huquqi yo'q"))
        return redirect('accounts:admin_dashboard')
    
    admins = CustomUser.objects.filter(user_type__in=['admin', 'main_admin'])
    
    context = {
        'admins': admins,
    }
    return render(request, 'accounts/admin_management.html', context)

@login_required  
@user_passes_test(is_admin, login_url='accounts:admin_login')
def admin_employer_management(request):
    """Управление работодателями"""
    employers = CustomUser.objects.filter(user_type='employer')
    
    context = {
        'employers': employers,
    }
    return render(request, 'accounts/admin_employer_management.html', context)

# Utility functions
def get_client_ip(request):
    """Получить IP адрес клиента"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

# Home views
def home_redirect(request):
    """Перенаправление на соответствующую домашнюю страницу"""
    if request.user.is_authenticated:
        if hasattr(request.user, 'is_student') and request.user.is_student:
            return redirect('accounts:student_dashboard')
        elif hasattr(request.user, 'is_employer') and request.user.is_employer:
            return redirect('accounts:employer_dashboard')
        elif (hasattr(request.user, 'is_admin') and request.user.is_admin or 
              hasattr(request.user, 'is_main_admin') and request.user.is_main_admin):
            return redirect('accounts:admin_dashboard')
    
    return redirect('accounts:home')

def home(request):
    """Главная страница для гостей"""
    if request.user.is_authenticated:
        return home_redirect(request)
    
    return render(request, 'home.html')

@login_required
def profile_view(request, user_id=None):
    """Просмотр профиля пользователя"""
    if user_id:
        user = get_object_or_404(CustomUser, id=user_id)
        is_own_profile = False
    else:
        user = request.user
        is_own_profile = True
    
    # Увеличиваем счетчик просмотров если смотрим чужой профиль
    if user != request.user:
        user.profile_views = getattr(user, 'profile_views', 0) + 1
        user.save()
        
        create_user_activity(
            user=request.user,
            activity_type='profile_view',
            description=f"{user.username} profilini ko'rdi"
        )
    
    # Получаем соответствующий профиль
    profile = None
    template_name = 'accounts/profile_base.html'
    context = {
        'profile_user': user,
        'is_own_profile': is_own_profile,
    }
    
    if hasattr(user, 'is_student') and user.is_student:
        try:
            profile = StudentProfile.objects.get(user=user)
            template_name = 'accounts/student_profile.html'
            context.update({
                'profile': profile,
                'stats': {
                    'resumes_created': getattr(profile, 'resumes_created', 0),
                    'jobs_applied': getattr(profile, 'jobs_applied', 0),
                }
            })
        except StudentProfile.DoesNotExist:
            profile = StudentProfile.objects.create(user=user)
            
    elif hasattr(user, 'is_employer') and user.is_employer:
        try:
            profile = EmployerProfile.objects.get(user=user)
            template_name = 'accounts/employer_profile.html'
            context.update({
                'profile': profile,
                'active_jobs_count': 0,  # Заглушка
                'total_applications': 0,  # Заглушка
            })
        except EmployerProfile.DoesNotExist:
            profile = EmployerProfile.objects.create(user=user)
            
    elif (hasattr(user, 'is_admin') and user.is_admin or 
          hasattr(user, 'is_main_admin') and user.is_main_admin):
        try:
            profile = AdminProfile.objects.get(user=user)
            template_name = 'accounts/admin_profile.html'
            context.update({
                'profile': profile,
                'admin_activities': UserActivity.objects.filter(
                    user=user, 
                    activity_type__in=['user_management', 'system_management']
                )[:5],
            })
        except AdminProfile.DoesNotExist:
            profile = AdminProfile.objects.create(user=user)
    
    context['profile'] = profile
    return render(request, template_name, context)

# Добавьте эти функции в конец файла views.py

@login_required
@user_passes_test(is_student, login_url='accounts:hemis_login')
def student_profile_update(request):
    """Редактирование профиля студента"""
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        student_profile = StudentProfile.objects.create(user=request.user)
    
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
            return redirect('accounts:student_dashboard')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = StudentProfileForm(instance=student_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/student_profile_update.html', context)

@login_required
@user_passes_test(is_employer, login_url='accounts:employer_login')
def employer_profile_update(request):
    """Редактирование профиля работодателя"""
    try:
        employer_profile = EmployerProfile.objects.get(user=request.user)
    except EmployerProfile.DoesNotExist:
        employer_profile = EmployerProfile.objects.create(user=request.user)
    
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
            return redirect('accounts:employer_dashboard')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = EmployerProfileForm(instance=employer_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
    }
    
    return render(request, 'accounts/employer_profile_update.html', context)

@login_required
@user_passes_test(is_main_admin, login_url='accounts:admin_login')
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
                can_manage_students=form.cleaned_data.get('can_manage_students', True),
                can_manage_employers=form.cleaned_data.get('can_manage_employers', True),
                can_manage_jobs=form.cleaned_data.get('can_manage_jobs', True),
                can_manage_resumes=form.cleaned_data.get('can_manage_resumes', True),
                can_view_statistics=form.cleaned_data.get('can_view_statistics', True),
            )
            
            create_user_activity(
                user=request.user,
                activity_type='user_create',
                description=f"Yangi admin yaratildi: {user.username}"
            )
            
            messages.success(request, _("Admin akkaunti muvaffaqiyatli yaratildi!"))
            return redirect('accounts:admin_management')
    else:
        form = AdminProfileForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'accounts/create_admin_account.html', context)

@login_required
@user_passes_test(can_manage_users, login_url='accounts:admin_login')
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
@user_passes_test(can_manage_users, login_url='accounts:admin_login')
def user_detail(request, user_id):
    """Детальная информация о пользователе"""
    user = get_object_or_404(CustomUser, id=user_id)
    
    # Получаем соответствующий профиль
    profile = None
    if hasattr(user, 'is_student') and user.is_student:
        profile = get_object_or_404(StudentProfile, user=user)
    elif hasattr(user, 'is_employer') and user.is_employer:
        profile = get_object_or_404(EmployerProfile, user=user)
    elif (hasattr(user, 'is_admin') and user.is_admin or 
          hasattr(user, 'is_main_admin') and user.is_main_admin):
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
@user_passes_test(can_manage_users, login_url='accounts:admin_login')
def toggle_user_status(request, user_id):
    """Активация/деактивация пользователя"""
    if request.method == 'POST':
        user = get_object_or_404(CustomUser, id=user_id)
        
        # Главный админ не может быть деактивирован
        if hasattr(user, 'is_main_admin') and user.is_main_admin:
            messages.error(request, _("Bosh adminni deaktiv qilib bo'lmaydi"))
            return redirect('accounts:user_management')
        
        user.is_active = not user.is_active
        user.save()
        
        action = "faollashtirildi" if user.is_active else "deaktiv qilindi"
        create_user_activity(
            user=request.user,
            activity_type='user_management',
            description=f"Foydalanuvchi {action}: {user.username}"
        )
        
        messages.success(request, _(f"Foydalanuvchi {action}"))
    
    return redirect('accounts:user_management')

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
    notification.is_read = True
    notification.save()
    
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
    if not (hasattr(request.user, 'is_admin') and request.user.is_admin or 
            hasattr(request.user, 'is_main_admin') and request.user.is_main_admin):
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