from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from accounts.api.views import oauth_callback
from accounts.views import oauth_login
from config.settings import PROTECTED_MEDIA_URL
from core import views as core_views
from django.views.generic import TemplateView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("explorer/", include("explorer.urls")),
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include(("core.urls", "core"), namespace="core")),
    path("jobs/", include(("jobs.urls", "jobs"), namespace="jobs")),
    path("resources/", include(("resources.urls", "resources"), namespace="resources")),
    path("events/", include(("events.urls", "events"), namespace="events")),
    path("employers/", include(("employers.urls", "employers"), namespace="employers")),
    path("cvbuilder/", include(("cvbuilder.urls", "cvbuilder"), namespace="cvbuilder")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
    path("oauth/login/", oauth_login, name="oauth_login"),
    path("oauth/callback/", oauth_callback, name="oauth_callback"),
    path("admin/stats/", core_views.admin_stats, name="admin_stats"),
    path('api/accounts/', include(('accounts.api.urls','accounts_api'), namespace='accounts_api')),

    path('manifest.json', TemplateView.as_view(template_name="manifest.json", content_type="application/json")),
    path('sw.js', TemplateView.as_view(template_name="sw.js", content_type="application/javascript")),
]

urlpatterns += [
    path('ckeditor5/', include('django_ckeditor_5.urls')),
]

protected_media_url = PROTECTED_MEDIA_URL.strip("/")
urlpatterns += [
    path(f"{protected_media_url}/<path:path>/", core_views.protected_media, name="protected_media"),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
