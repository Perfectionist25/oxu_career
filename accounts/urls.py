# accounts/urls.py - ФИНАЛЬНАЯ ВЕРСИЯ с OAuth для студентов
from django.contrib.auth import views as auth_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views
from .api_views import (
    oauth_callback, 
    oauth_user_info,
    oauth_refresh_token,
    oauth_logout,
    StudentDashboardAPI,
)

app_name = "accounts"

urlpatterns = [
    # ============ OAUTH ДЛЯ СТУДЕНТОВ ============
    path("oauth/login/", views.oauth_login, name="oauth_login"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
    path("oauth/user-info/", oauth_user_info, name="oauth_user_info"),
    path("oauth/refresh/", oauth_refresh_token, name="oauth_refresh"),
    path("oauth/logout/", oauth_logout, name="oauth_logout"),
    
    # ============ JWT ДЛЯ EMPLOYER/ADMIN (С ПРОВЕРКОЙ) ============
    # Используем кастомную view которая проверяет что это не студент
    path("api/token/", views.CustomTokenObtainView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    
    # ============ HTML ЛОГИН СТРАНИЦЫ (EMPLOYER/ADMIN ONLY) ============
    path("employer-login/", views.employer_login, name="employer_login"),
    path("login/", views.employer_login, name="login"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("logout/", views.logout_view, name="logout"),
    
    # ============ API ENDPOINTS ============
    
    # API дашборд для студентов (ТОЛЬКО ДЛЯ СТУДЕНТОВ)
    path("api/student/dashboard/", StudentDashboardAPI.as_view(), name="api_student_dashboard"),
    
    # API статистики пользователя
    path("api/user-stats/", views.user_stats_api, name="user_stats_api"),
    
    # ============ DASHBOARD VIEWS ============
    
    # Домашняя страница и редиректы
    path("", views.home_redirect, name="home_redirect"),
    path("home/", views.home, name="home"),
    
    # Дашборды
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("employer/dashboard/", views.employer_dashboard, name="employer_dashboard"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    
    # Поиск вакансий для студентов
    path("student/search/", views.student_search, name="student_search"),
    
    # ============ ПРОФИЛИ ПОЛЬЗОВАТЕЛЕЙ ============
    
    # Просмотр профилей
    path("profile/", views.profile_view, name="profile_view"),
    path("profile/<int:user_id>/", views.profile_view, name="profile_detail"),
    
    # Обновление профилей
    path("student/profile/update/", views.student_profile_update, name="student_profile_update"),
    path("employer/profile/update/", views.employer_profile_update, name="employer_profile_update"),
    
    # ============ УПРАВЛЕНИЕ КОМПАНИЯМИ (EMPLOYER) ============
    
    # Список компаний работодателя
    path("companies/", views.CompanyListView.as_view(), name="company_list"),
    
    # Создание новой компании
    path("companies/create/", views.CompanyCreateView.as_view(), name="company_create"),
    
    # Просмотр деталей компании
    path("companies/<int:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    
    # Обновление компании
    path("companies/<int:pk>/update/", views.CompanyUpdateView.as_view(), name="company_update"),
    
    # Удаление компании
    path("companies/<int:pk>/delete/", views.CompanyDeleteView.as_view(), name="company_delete"),
    
    # Документы компании
    path("companies/<int:pk>/documents/", views.company_documents, name="company_documents"),
    
    # Статистика компании
    path("companies/<int:pk>/statistics/", views.company_statistics, name="company_statistics"),
    
    # Установка основной компании
    path("set-primary-company/<int:pk>/", views.set_primary_company, name="set_primary_company"),
    
    # Статистика работодателя
    path("employer/stats/", views.employer_stats, name="employer_stats"),
    
    # ============ УПРАВЛЕНИЕ АДМИНИСТРАТОРАМИ ============
    
    # Управление администраторами (ТОЛЬКО ДЛЯ MAIN_ADMIN)
    path("admin/management/", views.admin_management, name="admin_management"),
    
    # Создание аккаунта администратора
    path("admin/create-admin/", views.create_admin_account, name="create_admin_account"),
    
    # Создание аккаунта работодателя
    path("admin/create-employer/", views.create_employer_account, name="create_employer_account"),
    
    # ============ АДМИН ПАНЕЛЬ ============
    
    # Управление пользователями
    path("admin/users/", views.user_management, name="user_management"),
    path("admin/users/<int:user_id>/", views.user_detail, name="user_detail"),
    path("admin/users/<int:user_id>/toggle-status/", views.toggle_user_status, name="toggle_user_status"),
    
    # Управление работодателями
    path("admin/employers/", views.admin_employer_management, name="admin_employer_management"),
    
    # Управление компаниями
    path("admin/companies/", views.admin_company_management, name="admin_company_management"),
    path("admin/companies/<int:pk>/", views.company_detail_admin, name="company_detail_admin"),
    path("admin/companies/<int:pk>/verify/", views.toggle_company_verification, name="toggle_company_verification"),
    path("admin/companies/<int:pk>/toggle-status/", views.toggle_company_status, name="toggle_company_status"),
    
    # ============ СИСТЕМНЫЕ ФУНКЦИИ ============
    
    # Журнал активности
    path("activity-log/", views.activity_log, name="activity_log"),
    
    # Уведомления
    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),
    
    # Смена пароля (НЕ ДЛЯ СТУДЕНТОВ)
    path("password_change/", views.admin_change_password, name="password_change"),
    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html"
    ), name="password_change_done"),
    
    # Сброс пароля (НЕ ДЛЯ СТУДЕНТОВ)
    path("password_reset/", auth_views.PasswordResetView.as_view(
        template_name="accounts/password_reset.html",
        email_template_name="accounts/password_reset_email.html",
        subject_template_name="accounts/password_reset_subject.txt",
        success_url="/accounts/password_reset/done/"
    ), name="password_reset"),
    
    path("password_reset/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="accounts/password_reset_done.html"
    ), name="password_reset_done"),
    
    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="accounts/password_reset_confirm.html",
        success_url="/accounts/reset/done/"
    ), name="password_reset_confirm"),
    
    path("reset/done/", auth_views.PasswordResetCompleteView.as_view(
        template_name="accounts/password_reset_complete.html"
    ), name="password_reset_complete"),
    
    # ============ ДОПОЛНИТЕЛЬНЫЕ СТРАНИЦЫ ============
    
    path("help/", views.help_center, name="help_center"),
    path("contact/", views.contact_us, name="contact_us"),
    path("about/", views.about_us, name="about_us"),
    path("terms/", views.terms_of_service, name="terms_of_service"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    
    # ============ СИСТЕМНЫЕ НАСТРОЙКИ (MAIN_ADMIN) ============
    
    path("admin/sessions/", views.admin_session_management, name="admin_session_management"),
    path("admin/sessions/<str:session_key>/terminate/", views.terminate_admin_session, name="terminate_admin_session"),
    path("admin/two-factor/", views.admin_two_factor_setup, name="admin_two_factor_setup"),
    path("admin/login-history/", views.admin_login_history, name="admin_login_history"),
    path("admin/initial-setup/", views.initial_setup, name="initial_setup"),
]
