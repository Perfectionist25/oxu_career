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

    REGISTRATION_TYPE_CHOICES = [
        ("open", _("Open Registration")),
        ("approval", _("Approval Required")),
        ("invite_only", _("Invitation Only")),
        ("paid", _("Paid Registration")),
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
    venue = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Venue"),
        help_text=_("Specific venue name")
    )
    online_event = models.BooleanField(
        default=False,
        verbose_name=_("Online Event"),
        help_text=_("Whether this is an online event")
    )
    online_link = models.URLField(
        blank=True,
        verbose_name=_("Online Meeting Link"),
        help_text=_("Link for online participation")
    )
    address = models.TextField(
        blank=True,
        verbose_name=_("Full Address"),
        help_text=_("Complete address of the venue")
    )

    # Organizer
    organizer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="organized_events",
        verbose_name=_("Organizer"),
        help_text=_("Primary organizer of the event")
    )
    co_organizers = models.ManyToManyField(
        User,
        blank=True,
        related_name="co_organized_events",
        verbose_name=_("Co-organizers"),
        help_text=_("Additional organizers of the event")
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

    # Registration
    registration_required = models.BooleanField(
        default=True,
        verbose_name=_("Registration Required"),
        help_text=_("Whether registration is required to attend")
    )
    registration_type = models.CharField(
        max_length=20,
        choices=REGISTRATION_TYPE_CHOICES,
        default="open",
        verbose_name=_("Registration Type"),
        help_text=_("Type of registration process")
    )
    registration_deadline = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Registration Deadline"),
        help_text=_("Deadline for registration")
    )
    max_participants = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Maximum Participants"),
        help_text=_("Maximum number of participants allowed")
    )
    waitlist_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Waitlist Enabled"),
        help_text=_("Whether waitlist is available when full")
    )

    # Cost
    is_free = models.BooleanField(
        default=True,
        verbose_name=_("Free Event"),
        help_text=_("Whether the event is free")
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name=_("Price"),
        help_text=_("Event price if not free")
    )
    currency = models.CharField(
        max_length=3,
        choices=[("UZS", "UZS"), ("USD", "USD")],
        default="UZS",
        verbose_name=_("Currency"),
        help_text=_("Currency for the price")
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
    show_attendee_list = models.BooleanField(
        default=True,
        verbose_name=_("Show Attendee List"),
        help_text=_("Whether to show list of registered attendees")
    )
    allow_comments = models.BooleanField(
        default=True,
        verbose_name=_("Allow Comments"),
        help_text=_("Whether to allow comments on the event")
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
    registration_link = models.URLField(
        blank=True,
        verbose_name=_("Registration Link"),
        help_text=_("External registration link")
    )
    materials_link = models.URLField(
        blank=True,
        verbose_name=_("Materials Link"),
        help_text=_("Link to event materials")
    )

    # Statistics
    views_count = models.IntegerField(
        default=0,
        verbose_name=_("Views Count"),
        help_text=_("Number of times the event was viewed")
    )
    registration_count = models.IntegerField(
        default=0,
        verbose_name=_("Registration Count"),
        help_text=_("Number of registered participants")
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

    def available_spots(self):
        if self.max_participants:
            return self.max_participants - self.registration_count
        return None

    def is_registration_open(self):
        from django.utils import timezone

        if not self.registration_required:
            return False
        if self.registration_deadline:
            return timezone.now() <= self.registration_deadline
        return self.is_upcoming()

    def registration_full(self):
        if self.max_participants:
            return self.registration_count >= self.max_participants
        return False


class EventRegistration(models.Model):
    """Stores event registration information"""

    STATUS_CHOICES = [
        ("registered", _("Registered")),
        ("waiting", _("Waiting List")),
        ("cancelled", _("Cancelled")),
        ("attended", _("Attended")),
        ("no_show", _("No Show")),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="registrations",
        verbose_name=_("Event"),
        help_text=_("The event being registered for")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="event_registrations",
        verbose_name=_("User"),
        help_text=_("User registering for the event")
    )

    # Registration Information
    registration_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Registration Date"),
        help_text=_("When the registration was made")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="registered",
        verbose_name=_("Status"),
        help_text=_("Current registration status")
    )

    # Additional Information
    dietary_restrictions = models.TextField(
        blank=True,
        verbose_name=_("Dietary Restrictions"),
        help_text=_("Any dietary restrictions for catering")
    )
    special_requirements = models.TextField(
        blank=True,
        verbose_name=_("Special Requirements"),
        help_text=_("Any special requirements or accommodations")
    )
    comments = models.TextField(
        blank=True,
        verbose_name=_("Comments"),
        help_text=_("Additional comments from the registrant")
    )

    # For Paid Events
    payment_status = models.CharField(
        max_length=20,
        choices=[
            ("pending", _("Pending")),
            ("paid", _("Paid")),
            ("refunded", _("Refunded")),
        ],
        default="pending",
        verbose_name=_("Payment Status"),
        help_text=_("Status of payment for the event")
    )
    payment_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Payment Amount"),
        help_text=_("Amount paid for the event")
    )

    # QR Code for Check-in
    qr_code = models.ImageField(
        upload_to="event_qr_codes/",
        null=True,
        blank=True,
        verbose_name=_("QR Code"),
        help_text=_("QR code for event check-in")
    )
    check_in_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Check-in Time"),
        help_text=_("Time when the user checked in")
    )

    class Meta:
        verbose_name = _("Event Registration")
        verbose_name_plural = _("Event Registrations")
        unique_together = ["event", "user"]
        ordering = ["-registration_date"]

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    def has_attended(self):
        return self.status == "attended"


class EventSpeaker(models.Model):
    """Stores speaker information for events"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="speakers",
        verbose_name=_("Event"),
        help_text=_("The event this speaker is associated with")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Speaker Name"),
        help_text=_("Full name of the speaker")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Speaker Title"),
        help_text=_("Professional title or position")
    )
    organization = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Organization"),
        help_text=_("Organization or company affiliation")
    )
    bio = models.TextField(
        blank=True,
        verbose_name=_("Biography"),
        help_text=_("Brief biography of the speaker")
    )
    photo = models.ImageField(
        upload_to="speaker_photos/",
        null=True,
        blank=True,
        verbose_name=_("Photo"),
        help_text=_("Profile photo of the speaker")
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Contact email for the speaker")
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Personal or professional website")
    )
    linkedin = models.URLField(
        blank=True,
        verbose_name=_("LinkedIn"),
        help_text=_("LinkedIn profile URL")
    )
    twitter = models.URLField(
        blank=True,
        verbose_name=_("Twitter"),
        help_text=_("Twitter profile URL")
    )

    # Display Order
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which to display this speaker")
    )

    class Meta:
        verbose_name = _("Event Speaker")
        verbose_name_plural = _("Event Speakers")
        ordering = ["order", "name"]

    def __str__(self):
        return f"{self.name} - {self.event.title}"


class EventSession(models.Model):
    """Stores session information within events"""

    SESSION_TYPE_CHOICES = [
        ("keynote", _("Keynote")),
        ("workshop", _("Workshop")),
        ("panel", _("Panel Discussion")),
        ("presentation", _("Presentation")),
        ("qna", _("Q&A Session")),
        ("networking", _("Networking")),
        ("break", _("Break")),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="sessions",
        verbose_name=_("Event"),
        help_text=_("The event this session belongs to")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Session Title"),
        help_text=_("Title of the session")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description of the session")
    )
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPE_CHOICES,
        verbose_name=_("Session Type"),
        help_text=_("Type of session")
    )

    # Timing
    start_time = models.DateTimeField(
        verbose_name=_("Start Time"),
        help_text=_("When the session starts")
    )
    end_time = models.DateTimeField(
        verbose_name=_("End Time"),
        help_text=_("When the session ends")
    )

    # Location (for large events)
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Location"),
        help_text=_("Specific location within the venue")
    )

    # Session Speakers
    speakers = models.ManyToManyField(
        EventSpeaker,
        blank=True,
        related_name="sessions",
        verbose_name=_("Speakers"),
        help_text=_("Speakers for this session")
    )

    # Materials
    presentation_url = models.URLField(
        blank=True,
        verbose_name=_("Presentation URL"),
        help_text=_("Link to presentation slides or materials")
    )
    materials_url = models.URLField(
        blank=True,
        verbose_name=_("Materials URL"),
        help_text=_("Link to additional session materials")
    )

    order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which to display this session")
    )

    class Meta:
        verbose_name = _("Event Session")
        verbose_name_plural = _("Event Sessions")
        ordering = ["start_time", "order"]

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    def duration(self):
        duration = self.end_time - self.start_time
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"


class EventComment(models.Model):
    """Stores comments on events"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name=_("Event"),
        help_text=_("The event being commented on")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who made the comment")
    )
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Parent Comment"),
        help_text=_("Parent comment for nested replies")
    )

    comment = models.TextField(
        verbose_name=_("Comment"),
        help_text=_("The comment text")
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_("Approved"),
        help_text=_("Whether this comment is approved for display")
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
        verbose_name = _("Event Comment")
        verbose_name_plural = _("Event Comments")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"


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


class EventRating(models.Model):
    """Stores user ratings for events"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="ratings",
        verbose_name=_("Event"),
        help_text=_("The event being rated")
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who provided the rating")
    )

    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating"),
        help_text=_("Overall rating (1-5)")
    )
    comment = models.TextField(
        blank=True,
        verbose_name=_("Comment"),
        help_text=_("Optional comment with the rating")
    )

    # Rating Categories
    content_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Content Rating"),
        help_text=_("Rating for event content quality")
    )
    organization_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Organization Rating"),
        help_text=_("Rating for event organization")
    )
    venue_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        verbose_name=_("Venue Rating"),
        help_text=_("Rating for venue quality (optional)")
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
        verbose_name = _("Event Rating")
        verbose_name_plural = _("Event Ratings")
        unique_together = ["event", "user"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Rating {self.rating} by {self.user.username} for {self.event.title}"

    def overall_rating(self):
        ratings = [self.content_rating, self.organization_rating]
        if self.venue_rating:
            ratings.append(self.venue_rating)
        return sum(ratings) / len(ratings)
