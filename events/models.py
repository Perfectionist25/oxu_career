from django.contrib.auth import get_user_model
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class EventCategory(models.Model):
    """Represents categories for organizing events"""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Category Name"),
        help_text=_("Name of the event category")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the category")
    )
    color = models.CharField(
        max_length=7,
        default="#007cba",
        verbose_name=_("Color"),
        help_text=_("Hex color code for UI display")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icon"),
        help_text=_("Icon identifier for UI display")
    )

    class Meta:
        verbose_name = _("Event Category")
        verbose_name_plural = _("Event Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    """Stores event information with multilingual support"""

    EVENT_TYPE_CHOICES = [
        ("conference", _("Conference")),
        ("workshop", _("Workshop")),
        ("seminar", _("Seminar")),
        ("networking", _("Networking")),
        ("career_fair", _("Career Fair")),
        ("hackathon", _("Hackathon")),
        ("webinar", _("Webinar")),
        ("social", _("Social Event")),
        ("training", _("Training")),
        ("other", _("Other")),
    ]

    EVENT_STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("published", _("Published")),
        ("cancelled", _("Cancelled")),
        ("completed", _("Completed")),
    ]

    # Basic Information
    title = models.CharField(
        max_length=200,
        verbose_name=_("Event Title"),
        help_text=_("Title of the event")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed description of the event")
    )
    short_description = models.TextField(
        max_length=300,
        verbose_name=_("Short Description"),
        help_text=_("Brief summary of the event")
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Category"),
        help_text=_("Event category for organization")
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name=_("Event Type"),
        help_text=_("Type of event")
    )

    # Dates and Time
    start_date = models.DateTimeField(
        verbose_name=_("Start Date"),
        help_text=_("Event start date and time")
    )
    end_date = models.DateTimeField(
        verbose_name=_("End Date"),
        help_text=_("Event end date and time")
    )

    # Location
    location = models.CharField(
        max_length=200,
        verbose_name=_("Location"),
        help_text=_("General location of the event")
    )

    # Images
    banner_image = models.ImageField(
        upload_to="event_banners/",
        null=True,
        blank=True,
        verbose_name=_("Banner Image"),
        help_text=_("Main banner image for the event")
    )
    thumbnail = models.ImageField(
        upload_to="event_thumbnails/",
        null=True,
        blank=True,
        verbose_name=_("Thumbnail"),
        help_text=_("Small thumbnail image")
    )

    # Settings
    status = models.CharField(
        max_length=20,
        choices=EVENT_STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
        help_text=_("Current status of the event")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Featured Event"),
        help_text=_("Whether to feature this event prominently")
    )

    # SEO and Additional Fields
    slug = models.SlugField(
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier")
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for the event")
    )

    # Statistics
    views_count = models.IntegerField(
        default=0,
        verbose_name=_("Views Count"),
        help_text=_("Number of times the event was viewed")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["-start_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.title) or 'event'
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("events:event_detail", kwargs={"slug": self.slug})

    def is_upcoming(self):
        from django.utils import timezone

        return self.start_date > timezone.now()

    def is_ongoing(self):
        from django.utils import timezone

        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def is_past(self):
        from django.utils import timezone

        return self.end_date < timezone.now()


class EventPhoto(models.Model):
    """Stores photos from events"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="photos",
        verbose_name=_("Event"),
        help_text=_("The event this photo belongs to")
    )
    image = models.ImageField(
        upload_to="event_photos/",
        verbose_name=_("Image"),
        help_text=_("The photo file")
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Caption"),
        help_text=_("Optional caption for the photo")
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Uploaded By"),
        help_text=_("User who uploaded this photo")
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At"),
        help_text=_("When the photo was uploaded")
    )

    # For Sorting
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which to display this photo")
    )

    class Meta:
        verbose_name = _("Event Photo")
        verbose_name_plural = _("Event Photos")
        ordering = ["order", "-uploaded_at"]

    def __str__(self):
        return f"Photo for {self.event.title}"
