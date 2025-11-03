from django.urls import path
from django.utils.translation import gettext_lazy as _
from . import views

app_name = 'jobs'

urlpatterns = [
    # Public pages
    path('', views.job_list, name='list'),
    path('companies/', views.company_list, name='company_list'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    path('companies/<int:pk>/jobs/', views.CompanyJobsView.as_view(), name='company_jobs'),
    path('industries/', views.industries_list, name='industries_list'),
    path('my-jobs/', views.my_jobs, name='my_jobs'),
    path('saved-jobs/', views.saved_jobs, name='saved_jobs'),
    
    # Job creation and management
    path('create/', views.job_create, name='job_create'),
    path('<int:pk>/edit/', views.job_edit, name='job_edit'),
    path('<int:pk>/delete/', views.job_delete, name='job_delete'),
    
    # Job details and applications
    path('<int:pk>/', views.job_detail, name='job_detail'),
    path('<int:pk>/apply/', views.apply_for_job, name='apply_for_job'),
    path('<int:pk>/save/', views.save_job, name='save_job'),
    path('<int:pk>/unsave/', views.unsave_job, name='unsave_job'),
    path('<int:pk>/increment-views/', views.increment_job_views, name='increment_job_views'),
    
    # User applications and alerts
    path('applications/my/', views.my_applications, name='my_applications'),
    path('employer/applications/', views.employer_applications, name='employer_applications'),
    path('job-alerts/', views.job_alerts, name='job_alerts'),
    path('job-alerts/<int:pk>/delete/', views.delete_job_alert, name='delete_job_alert'),
    
    # Company reviews and interviews
    path('companies/<int:pk>/review/', views.create_company_review, name='create_company_review'),
    path('companies/<int:pk>/interview-experience/', views.create_interview_experience, name='create_interview_experience'),
    
    # AJAX endpoints
    path('applications/<int:pk>/update-status/', views.update_application_status, name='update_application_status'),
    path('get-user-cvs/', views.get_user_cvs, name='get_user_cvs'),
]