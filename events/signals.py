from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Event, EventParticipation


@receiver(post_save, sender=EventParticipation)
def keep_attendance_state_consistent(sender, instance, **kwargs):
    """Normalize participation state after updates."""
    if instance.status == EventParticipation.STATUS_CANCELLED and instance.checked_in_at:
        instance.checked_in_at = None
        instance.checked_in_by = None
        instance.save(update_fields=["checked_in_at", "checked_in_by", "updated_at"])


@receiver(post_save, sender=Event)
def ensure_event_state_is_consistent(sender, instance, **kwargs):
    """Keep completed events marked consistently when the end date is in the past."""
    if instance.status == "published" and instance.end_date < instance.start_date:
        instance.status = "draft"
        instance.save(update_fields=["status", "updated_at"])
