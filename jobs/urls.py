from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    # Public pages
    path("", views.job_list, name="list"),
    path("industries/", views.industries_list, name="industries_list"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs"),
    # Job creation and management
    path("create/", views.job_create, name="job_create"),
    path("<int:pk>/edit/", views.job_edit, name="job_edit"),
    path("<int:pk>/delete/", views.job_delete, name="job_delete"),
    # Job details and applications
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("<int:pk>/apply/", views.apply_for_job, name="apply_for_job"),
    path("<int:pk>/save/", views.save_job, name="save_job"),
    path("<int:pk>/unsave/", views.unsave_job, name="unsave_job"),
    path(
        "<int:pk>/increment-views/",
        views.increment_job_views,
        name="increment_job_views",
    ),
    # User applications and alerts
    path("applications/my/", views.my_applications, name="my_applications"),
    path(
        "employer/applications/",
        views.employer_applications,
        name="employer_applications",
    ),
    path("job-alerts/", views.job_alerts, name="job_alerts"),
    path(
        "job-alerts/<int:pk>/delete/", views.delete_job_alert, name="delete_job_alert"
    ),
    # AJAX endpoints
    path(
        "applications/<int:pk>/update-status/",
        views.update_application_status,
        name="update_application_status",
    ),
    path(
        "applications/<int:pk>/detail/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "applications/<int:pk>/add-note/",
        views.add_application_note,
        name="add_application_note",
    ),
    path("get-user-cvs/", views.get_user_cvs, name="get_user_cvs"),
]
