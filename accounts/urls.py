# accounts/urls.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    # Authentication URLs
    path("hemis-login/", views.hemis_login, name="hemis_login"),
    path("hemis-callback/", views.hemis_callback, name="hemis_callback"),
    path("employer-login/", views.employer_login, name="employer_login"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("logout/", views.logout_view, name="logout"),
    # Временные URL для тестирования
    path("temp-student-login/", views.temp_student_login, name="temp_student_login"),
    # Home and redirects
    path("", views.home_redirect, name="home_redirect"),
    path("home/", views.home, name="home"),
    # Dashboard URLs
    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("employer/dashboard/", views.employer_dashboard, name="employer_dashboard"),
    path("student/search/", views.student_search, name="student_search"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    # Profile URLs
    path("profile/", views.profile_view, name="profile_view"),
    path("profile/<int:user_id>/", views.profile_view, name="profile_detail"),
    path(
        "student/profile/update/",
        views.student_profile_update,
        name="student_profile_update",
    ),
    path(
        "employer/profile/update/",
        views.employer_profile_update,
        name="employer_profile_update",
    ),
    # УДАЛИТЬ URL управления вакансиями - они теперь в jobs/urls.py
    # path('employer/jobs/', views.employer_jobs, name='employer_jobs'),
    # path('employer/jobs/create/', views.create_job, name='create_job'),
    # path('employer/jobs/<int:job_id>/edit/', views.edit_job, name='edit_job'),
    # path('employer/jobs/<int:job_id>/toggle-status/', views.toggle_job_status, name='toggle_job_status'),
    # Account Creation (Admin only)
    path(
        "admin/create-employer/",
        views.create_employer_account,
        name="create_employer_account",
    ),
    path(
        "admin/create-admin/", views.create_admin_account, name="create_admin_account"
    ),
    # Password change
    path(
        "password_change/",
        auth_views.PasswordChangeView.as_view(
            template_name="accounts/password_change.html",
            success_url="/accounts/password_change/done/",
        ),
        name="password_change",
    ),
    path(
        "password_change/done/",
        auth_views.PasswordChangeDoneView.as_view(
            template_name="accounts/password_change_done.html"
        ),
        name="password_change_done",
    ),
    # User Management (Admin only)
    path("admin/users/", views.user_management, name="user_management"),
    path("admin/users/<int:user_id>/", views.user_detail, name="user_detail"),
    path(
        "admin/users/<int:user_id>/toggle-status/",
        views.toggle_user_status,
        name="toggle_user_status",
    ),
    # Admin Management URLs
    path("admin/management/", views.admin_management, name="admin_management"),
    path(
        "admin/employers/",
        views.admin_employer_management,
        name="admin_employer_management",
    ),
    # Notification URLs
    path("notifications/", views.notifications, name="notifications"),
    path(
        "notifications/<int:notification_id>/read/",
        views.mark_notification_read,
        name="mark_notification_read",
    ),
    path(
        "notifications/mark-all-read/",
        views.mark_all_notifications_read,
        name="mark_all_notifications_read",
    ),
    # API URLs
    path("api/user-stats/", views.user_stats_api, name="user_stats_api"),
    # Legacy URLs
    path("login/", views.hemis_login, name="login"),
    path("register/", views.hemis_login, name="register"),
]
