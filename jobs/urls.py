from django.urls import path

from . import views

app_name = "jobs"

urlpatterns = [
    # Umumiy sahifalar
    path("", views.job_list, name="list"),
    path("tarmoqlar/", views.industries_list, name="industries_list"),
    path("mening-ishlarim/", views.my_jobs, name="my_jobs"),
    path("saqlanganlar/", views.saved_jobs, name="saved_jobs"),
    
    # Vakansiya yaratish va boshqarish
    path("yaratish/", views.job_create, name="job_create"),
    path("<int:pk>/tahrirlash/", views.job_edit, name="job_edit"),
    path("<int:pk>/ochirish/", views.job_delete, name="job_delete"),
    
    # Vakansiya tafsilotlari va arizalar
    path("<int:pk>/", views.job_detail, name="job_detail"),
    path("<int:pk>/ariza-berish/", views.apply_for_job, name="apply_for_job"),
    path("<int:pk>/saqlash/", views.save_job, name="save_job"),
    path("<int:pk>/saqlanganlardan-olish/", views.unsave_job, name="unsave_job"),
    path(
        "<int:pk>/korishlar-soni/",
        views.increment_job_views,
        name="increment_job_views",
    ),
    
    # Foydalanuvchi arizalari va ogohlantirishlar
    path("mening-arizalarim/", views.my_applications, name="my_applications"),
    path(
        "ish-beruvchi/arizalar/",
        views.employer_applications,
        name="employer_applications",
    ),

    
    # AJAX endpointlar
    path(
        "arizalar/<int:pk>/status-yangilash/",
        views.update_application_status,
        name="update_application_status",
    ),
    path(
        "arizalar/<int:pk>/batafsil/",
        views.application_detail,
        name="application_detail",
    ),
    path(
        "arizalar/<int:pk>/izoh-qoshish/",
        views.add_application_note,
        name="add_application_note",
    ),
    path("rezyume-olish/", views.get_user_cvs, name="get_user_cvs"),
]