from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Основные страницы
    path("", views.home, name="home"),
    path("about/", views.about, name="about"),
    path("contact/", views.contact, name="contact"),
    path("contact/success/", views.contact_success, name="contact_success"),
    path("privacy/", views.privacy_policy, name="privacy_policy"),
    path("terms/", views.terms_of_service, name="terms_of_service"),
    path("faq/", views.faq, name="faq"),
    # API endpoints
    path("api/stats/", views.api_stats, name="api_stats"),
    path("api/health/", views.health_check, name="health_check"),
    # Административные страницы (только для staff)
    path(
        "admin/contact-messages/",
        views.contact_messages_list,
        name="contact_messages_list",
    ),
    path(
        "admin/contact-messages/<int:pk>/",
        views.contact_message_detail,
        name="contact_message_detail",
    ),
]

# Обработчики ошибок (должны быть в корневом urls.py)
handler404 = "core.views.handler404"
handler500 = "core.views.handler500"
handler403 = "core.views.handler403"
handler400 = "core.views.handler400"
