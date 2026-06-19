from django.contrib.auth import views as auth_views
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from . import views
from .api.views import oauth_callback, oauth_user_info
from .api_views import (
    oauth_refresh_token,
    oauth_logout,
    StudentDashboardAPI,
)

app_name = "accounts"

urlpatterns = [
    path("oauth/login/", views.oauth_login, name="oauth_login"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
    path("oauth/user-info/", oauth_user_info, name="oauth_user_info"),
    path("oauth/refresh/", oauth_refresh_token, name="oauth_refresh"),
    path("oauth/logout/", oauth_logout, name="oauth_logout"),

    path("api/token/", views.CustomTokenObtainView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/token/verify/", TokenVerifyView.as_view(), name="token_verify"),

    path("register/", views.employer_register, name="employer_register"),

    path("employer-login/", views.employer_login, name="employer_login"),
    path("login/", views.employer_login, name="login"),
    path("admin-login/", views.admin_login, name="admin_login"),
    path("logout/", views.logout_view, name="logout"),

    path("api/student/dashboard/", StudentDashboardAPI.as_view(), name="api_student_dashboard"),
    path("api/user-stats/", views.user_stats_api, name="user_stats_api"),

    path("", views.home_redirect, name="home_redirect"),
    path("home/", views.home, name="home"),

    path("student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("employer/dashboard/", views.employer_dashboard, name="employer_dashboard"),
    path("admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("admin/statistics/", views.admin_statistics, name="admin_statistics"),

    path("student/search/", views.student_search, name="student_search"),

    path("profile/", views.profile_view, name="profile_view"),
    path("profile/<int:user_id>/", views.profile_view, name="profile_detail"),

    path("student/profile/update/", views.student_profile_update, name="student_profile_update"),
    path("student/certificates/", views.student_certificate_list, name="student_certificate_list"),
    path("student/certificates/upload/", views.student_certificate_create, name="student_certificate_create"),
    path("student/certificates/<int:pk>/edit/", views.student_certificate_update, name="student_certificate_update"),
    path("student/certificates/<int:pk>/delete/", views.student_certificate_delete, name="student_certificate_delete"),
    path("student/certificates/<int:pk>/file/", views.student_certificate_file, name="student_certificate_file"),
    path("employer/profile/update/", views.employer_profile_update, name="employer_profile_update"),

    path("companies/", views.CompanyListView.as_view(), name="company_list"),
    path("companies/create/", views.CompanyCreateView.as_view(), name="company_create"),
    path("companies/<int:pk>/", views.CompanyDetailView.as_view(), name="company_detail"),
    path("companies/<int:pk>/update/", views.CompanyUpdateView.as_view(), name="company_update"),
    path("companies/<int:pk>/delete/", views.CompanyDeleteView.as_view(), name="company_delete"),
    path("companies/<int:pk>/documents/", views.company_documents, name="company_documents"),
    path("companies/<int:pk>/statistics/", views.company_statistics, name="company_statistics"),
    path("set-primary-company/<int:pk>/", views.set_primary_company, name="set_primary_company"),
    path("employer/stats/", views.employer_stats, name="employer_stats"),

    path("admin/management/", views.admin_management, name="admin_management"),
    path("admin/create-admin/", views.create_admin_account, name="create_admin_account"),
    path("admin/create-employer/", views.create_employer_account, name="create_employer_account"),

    path("admin/users/", views.user_management, name="user_management"),
    path("admin/users/<int:user_id>/", views.user_detail, name="user_detail"),
    path("admin/users/<int:user_id>/toggle-status/", views.toggle_user_status, name="toggle_user_status"),

    path("admin/employers/", views.admin_employer_management, name="admin_employer_management"),
    path("admin/companies/", views.admin_company_management, name="admin_company_management"),
    path("admin/companies/<int:pk>/", views.company_detail_admin, name="company_detail_admin"),
    path("admin/companies/<int:pk>/verify/", views.toggle_company_verification, name="toggle_company_verification"),
    path("admin/companies/<int:pk>/toggle-status/", views.toggle_company_status, name="toggle_company_status"),

    path("activity-log/", views.activity_log, name="activity_log"),

    path("notifications/", views.notifications, name="notifications"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/mark-all-read/", views.mark_all_notifications_read, name="mark_all_notifications_read"),

    path("password_change/done/", auth_views.PasswordChangeDoneView.as_view(
        template_name="accounts/password_change_done.html"
    ), name="password_change_done"),

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

    path("help/", views.help_center, name="help_center"),
    path("contact/", views.contact_us, name="contact_us"),
    path("about/", views.about_us, name="about_us"),
    path("terms/", views.terms_of_service, name="terms_of_service"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),

    path("admin/sessions/", views.admin_session_management, name="admin_session_management"),
    path("admin/sessions/<str:session_key>/terminate/", views.terminate_admin_session, name="terminate_admin_session"),
    path("admin/two-factor/", views.admin_two_factor_setup, name="admin_two_factor_setup"),
    path("admin/login-history/", views.admin_login_history, name="admin_login_history"),
    path("admin/initial-setup/", views.initial_setup, name="initial_setup"),
]