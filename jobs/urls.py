from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [

    path("", views.job_list, name="list"),
    path("my-jobs/", views.my_jobs, name="my_jobs"),
    path("my-applications/", views.my_applications, name="my_applications"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs"),


    path("create/", views.job_create, name="job_create"),
    path("<int:pk>/edit/", views.job_edit, name="job_edit"),
    path("<int:pk>/delete/", views.job_delete, name="job_delete"),
    path("<int:pk>/", views.job_detail, name="job_detail"),


    path("<int:pk>/apply/", views.apply_for_job, name="apply_for_job"),
    path("<int:pk>/save/", views.save_job, name="save_job"),
    path("<int:pk>/unsave/", views.unsave_job, name="unsave_job"),
    path('<int:pk>/settings/', views.job_settings, name='job_settings'),
    path('<int:pk>/update-settings/', views.update_job_settings, name='update_job_settings'),


    path(
        "employer/applications/",
        views.employer_applications,
        name="employer_applications",
    ),


    path(
        "<int:pk>/views/",
        views.increment_job_views,
        name="increment_job_views",
    ),
    path(
        "arizalar/<int:pk>/status-update/",
        views.update_application_status,
        name="update_application_status",
    ),
    path(
        "arizalar/<int:pk>/details/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "arizalar/<int:pk>/comment/",
        views.add_application_note,
        name="add_application_note",
    ),
    path("get-a-resume/", views.get_user_cvs, name="get_user_cvs"),
    # path("api/v1/vacancies/webhook/", views.google_form_webhook, name="google_form_webhook"),
]