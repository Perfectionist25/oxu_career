from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


from jobs.models import Job, JobApplication
from events.models import Event
from django.conf import settings
from django.utils import timezone


class Skill(models.Model):
    """Skill model for alumni professional competencies"""

    CATEGORY_CHOICES = [
        ("technical", _("Technical Skills")),
        ("soft", _("Soft Skills")),
        ("language", _("Language Skills")),
        ("professional", _("Professional Skills")),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name"),
        help_text=_("Name of the skill or competency"),
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Category"),
        help_text=_("Category of the skill"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description of the skill"),
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier"),
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Alumni(models.Model):
    """Alumni profile model (minimal fields required by forms)."""

    FACULTY_CHOICES = [
        ("science", "Science"),
        ("engineering", "Engineering"),
        ("business", "Business"),
        ("arts", "Arts"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alumni_profile"
    )
    name = models.CharField(max_length=255, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    graduation_year = models.IntegerField(null=True, blank=True)
    faculty = models.CharField(max_length=255, blank=True)
    degree = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=255, blank=True)
    current_position = models.CharField(max_length=255, blank=True)
    company = models.ForeignKey(
        "accounts.Company", null=True, blank=True, on_delete=models.SET_NULL
    )
    profession = models.CharField(max_length=255, blank=True)
    industry = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    linkedin = models.URLField(blank=True)
    github = models.URLField(blank=True)
    telegram = models.CharField(max_length=64, blank=True)
    website = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    facebook = models.URLField(blank=True)
    instagram = models.URLField(blank=True)
    photo = models.ImageField(upload_to="alumni_photos/", null=True, blank=True)
    resume = models.FileField(upload_to="resumes/", null=True, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    expertise_areas = models.TextField(blank=True)
    years_of_experience = models.IntegerField(null=True, blank=True)
    is_open_to_opportunities = models.BooleanField(default=False)
    country = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    is_mentor = models.BooleanField(default=False)
    is_visible = models.BooleanField(default=True)
    show_contact_info = models.BooleanField(default=False)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name or str(self.user)


class Connection(models.Model):
    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="connections_from", on_delete=models.CASCADE
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="connections_to", on_delete=models.CASCADE
    )
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class Mentorship(models.Model):
    mentor = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="mentorships_as_mentor", on_delete=models.CASCADE
    )
    mentee = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="mentorships_as_mentee", on_delete=models.CASCADE
    )
    message = models.TextField(blank=True)
    expected_duration = models.CharField(max_length=100, blank=True)
    communication_preference = models.CharField(max_length=100, blank=True)
    mentee_feedback = models.TextField(blank=True)
    mentor_feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)


class Message(models.Model):
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="sent_messages", on_delete=models.CASCADE
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="received_messages", on_delete=models.CASCADE
    )
    created_at = models.DateTimeField(default=timezone.now)


class News(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField(blank=True)
    category = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="event_photos/", null=True, blank=True)
    tags = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=255, blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
