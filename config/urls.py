from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("explorer/", include("explorer.urls")),
    # Django i18n endpoints (set language)
    path("i18n/", include("django.conf.urls.i18n")),
    path("", include(("core.urls", "core"), namespace="core")),
    path("jobs/", include(("jobs.urls", "jobs"), namespace="jobs")),
    path("alumni/", include(("alumni.urls", "alumni"), namespace="alumni")),
    path("resources/", include(("resources.urls", "resources"), namespace="resources")),
    path("events/", include(("events.urls", "events"), namespace="events")),
    path("employers/", include(("employers.urls", "employers"), namespace="employers")),
    path("cvbuilder/", include(("cvbuilder.urls", "cvbuilder"), namespace="cvbuilder")),
    path("accounts/", include(("accounts.urls", "accounts"), namespace="accounts")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers (optional)
# handler404 = 'core.views.handler404'
# handler500 = 'core.views.handler500'
