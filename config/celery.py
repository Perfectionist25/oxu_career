import os

from celery import Celery
from django.conf import settings

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("oxu_career")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

app.conf.beat_scheduler = "django_celery_beat.schedulers:DatabaseScheduler"
app.conf.task_track_started = True
app.conf.task_time_limit = 300
app.conf.worker_redirect_stdouts = True
app.conf.worker_redirect_stdouts_level = "INFO"


@app.task(bind=True)
def debug_task(self):
    return f"Celery is running: {self.request!r}"
