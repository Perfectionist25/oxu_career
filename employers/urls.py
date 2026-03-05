from django.urls import path

from . import views

app_name = "employers"

urlpatterns = [

    path("", views.employer_dashboard, name="dashboard"),
    path(
        "profile/create/", views.create_employer_profile, name="create_employer_profile"
    ),

    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/apply/", views.apply_for_job, name="apply_for_job"),
    path("jobs/post/", views.post_job, name="post_job"),
    path("jobs/manage/", views.manage_jobs, name="manage_jobs"),

    path("applications/", views.my_applications, name="my_applications"),
    path(
        "applications/<int:pk>/update-status/",
        views.update_application_status,
        name="update_application_status",
    ),

    path("companies/", views.company_list, name="company_list"),
    path("companies/<int:pk>/", views.company_detail, name="company_detail"),
    path("<int:employer_id>/companies/", views.employer_companies, name="employer_companies"),

    path(
        "candidate/<int:user_id>/cvs/",
        views.get_candidate_cvs,
        name="get_candidate_cvs",
    ),
]
