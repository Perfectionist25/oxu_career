from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import (
    CustomUser,
    StudentProfile,
    AdminProfile,
)


@receiver(post_save, sender=CustomUser)
def create_profile(sender, instance, created, **kwargs):
    """Create a simple profile record after a CustomUser is created.

    We only auto-create profiles that don't require many mandatory fields.
    StudentProfile and AdminProfile are safe to create with defaults. Employer
    profiles usually require company data, so we skip creating them here.
    """
    if not created:
        return

    if instance.user_type == "student":
        StudentProfile.objects.create(user=instance)
    elif instance.user_type in ("admin", "main_admin"):
        AdminProfile.objects.create(user=instance)
