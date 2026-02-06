from django.urls import path

from . import views
from .feeds import AllUpdatesFeed, LatestJobsFeed, LatestNewsFeed, UpcomingEventsFeed

app_name = "alumni"

urlpatterns = [
    # Основные маршруты
    path("", views.alumni_list, name="list"),
    path("profile/", views.alumni_profile, name="profile"),
    path("profile/edit/", views.alumni_profile_edit, name="profile_edit"),
    path("dashboard/", views.dashboard, name="dashboard"),
    # Выпускники
    path("alumni/<slug:slug>/", views.alumni_detail, name="alumni_detail"),
    # Вакансии
    path("jobs/", views.job_list, name="job_list"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/apply/", views.job_apply, name="job_apply"),
    # Мероприятия
    path("events/", views.event_list, name="event_list"),
    path("events/<int:pk>/", views.event_detail, name="event_detail"),
    path("events/<int:pk>/register/", views.event_register, name="event_register"),
    # Новости
    path("news/", views.news_list, name="news_list"),
    path("news/<slug:slug>/", views.news_detail, name="news_detail"),
    # Менторство
    path(
        "mentorship/<slug:alumni_slug>/request/",
        views.mentorship_request,
        name="mentorship_request",
    ),
    # Соединения
    path(
        "connection/<slug:alumni_slug>/request/",
        views.connection_request,
        name="connection_request",
    ),
    # RSS feeds
    path("feeds/news/", LatestNewsFeed(), name="news_feed"),
    path("feeds/jobs/", LatestJobsFeed(), name="jobs_feed"),
    path("feeds/events/", UpcomingEventsFeed(), name="events_feed"),
    path("feeds/all/", AllUpdatesFeed(), name="all_updates_feed"),
]
