from celery import shared_task
from django.utils import timezone


@shared_task(bind=True)
def debug_task(self):
    return f"Core debug task executed at {timezone.now().isoformat()}"


@shared_task
def ping():
    return "pong"
