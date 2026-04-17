import uuid

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_ckeditor_5.fields import CKEditor5Field

User = get_user_model()


class EventCategory(models.Model):
    """Represents categories for organizing events."""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Category Name"),
        help_text=_("Name of the event category"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the category"),
    )
    color = models.CharField(
        max_length=7,
        default="#007cba",
        verbose_name=_("Color"),
        help_text=_("Hex color code for UI display"),
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icon"),
        help_text=_("Icon identifier for UI display"),
    )

    class Meta:
        verbose_name = _("Event Category")
        verbose_name_plural = _("Event Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class EventEmployerCategory(models.Model):
    """Allowed employer category for event participation rules."""

    name = models.CharField(
        max_length=150,
        unique=True,
        verbose_name=_("Category Name"),
        help_text=_("Employer business category name, for example Bank"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))

    class Meta:
        verbose_name = _("Event Employer Category")
        verbose_name_plural = _("Event Employer Categories")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Event(models.Model):
    """Stores event information with multilingual support."""

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

    title = models.CharField(
        max_length=200,
        verbose_name=_("Event Title"),
        help_text=_("Title of the event"),
    )
    description = CKEditor5Field(_("Description"), config_name="extends")
    short_description = models.TextField(
        max_length=300,
        verbose_name=_("Short Description"),
        help_text=_("Brief summary of the event"),
    )
    category = models.ForeignKey(
        EventCategory,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Category"),
        help_text=_("Event category for organization"),
    )
    event_type = models.CharField(
        max_length=20,
        choices=EVENT_TYPE_CHOICES,
        verbose_name=_("Event Type"),
        help_text=_("Type of event"),
    )
    start_date = models.DateTimeField(
        verbose_name=_("Start Date"),
        help_text=_("Event start date and time"),
    )
    end_date = models.DateTimeField(
        verbose_name=_("End Date"),
        help_text=_("Event end date and time"),
    )
    location = models.CharField(
        max_length=200,
        verbose_name=_("Location"),
        help_text=_("General location of the event"),
    )
    max_participants = models.PositiveIntegerField(
        default=100,
        verbose_name=_("Maximum Participants"),
        help_text=_("Maximum number of participants allowed for this event"),
    )
    allow_students = models.BooleanField(
        default=True,
        verbose_name=_("Allow Students"),
        help_text=_("Allow students to register for this event"),
    )
    allow_alumni = models.BooleanField(
        default=True,
        verbose_name=_("Allow Alumni"),
        help_text=_("Allow alumni to register for this event"),
    )
    allow_employers = models.BooleanField(
        default=True,
        verbose_name=_("Allow Employers"),
        help_text=_("Allow employers to register for this event"),
    )
    allow_admins = models.BooleanField(
        default=True,
        verbose_name=_("Allow Admins"),
        help_text=_("Allow admin users to register for this event"),
    )
    allowed_employer_categories = models.ManyToManyField(
        EventEmployerCategory,
        blank=True,
        related_name="events",
        verbose_name=_("Allowed Employer Categories"),
        help_text=_("Leave empty to allow employers from all business categories"),
    )
    banner_image = models.ImageField(
        upload_to="event_banners/",
        null=True,
        blank=True,
        verbose_name=_("Banner Image"),
        help_text=_("Main banner image for the event"),
    )
    thumbnail = models.ImageField(
        upload_to="event_thumbnails/",
        null=True,
        blank=True,
        verbose_name=_("Thumbnail"),
        help_text=_("Small thumbnail image"),
    )
    status = models.CharField(
        max_length=20,
        choices=EVENT_STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
        help_text=_("Current status of the event"),
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier"),
    )
    tags = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for the event"),
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_("Created By"),
        help_text=_("User who created the event"),
    )
    views_count = models.IntegerField(
        default=0,
        verbose_name=_("Views Count"),
        help_text=_("Number of times the event was viewed"),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["-start_date"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify

            max_length = self._meta.get_field("slug").max_length
            base_slug = slugify(self.title) or "event"
            if max_length:
                base_slug = base_slug[:max_length]
            slug = base_slug
            counter = 1
            while Event.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                suffix = f"-{counter}"
                if max_length:
                    slug = f"{base_slug[: max_length - len(suffix)]}{suffix}"
                else:
                    slug = f"{base_slug}{suffix}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.end_date <= self.start_date:
            raise ValidationError({"end_date": _("End date must be after start date.")})
        if self.max_participants < 1:
            raise ValidationError(
                {"max_participants": _("Maximum participants must be at least 1.")}
            )

    def get_absolute_url(self):
        return reverse("events:event_detail", kwargs={"slug": self.slug})

    def is_upcoming(self):
        return self.start_date > timezone.now()

    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date

    def is_past(self):
        return self.end_date < timezone.now()

    @property
    def seats_occupied(self):
        return self.participations.filter(status=EventParticipation.STATUS_REGISTERED).count()

    @property
    def seats_remaining(self):
        return max(self.max_participants - self.seats_occupied, 0)

    def has_available_seats(self):
        return self.seats_occupied < self.max_participants

    def has_started(self):
        return timezone.now() >= self.start_date

    def check_in_is_open(self):
        return timezone.now() <= self.end_date

    def employer_category_names(self):
        return list(self.allowed_employer_categories.values_list("name", flat=True))

    def matches_employer_category(self, user):
        if not user.is_employer:
            return False

        allowed_categories = {
            category.strip().lower()
            for category in self.employer_category_names()
            if category and category.strip()
        }
        if not allowed_categories:
            return True

        employer_profile = getattr(user, "employer_profile", None)
        candidate_values = []
        if employer_profile and employer_profile.primary_company_id:
            primary_company = employer_profile.primary_company_id
            candidate_values.extend(
                [primary_company.industry, getattr(primary_company.additional_info, "sub_industry", "")]
                if hasattr(primary_company, "additional_info")
                else [primary_company.industry]
            )

        for company in user.companies_owned.filter(is_active=True):
            candidate_values.append(company.industry)
            additional_info = getattr(company, "additional_info", None)
            if additional_info:
                candidate_values.append(additional_info.sub_industry)

        normalized_values = {
            value.strip().lower() for value in candidate_values if value and value.strip()
        }
        return bool(normalized_values & allowed_categories)

    def get_registration_role(self, user):
        if user.is_student:
            return EventParticipation.ROLE_STUDENT
        if user.is_alumni:
            return EventParticipation.ROLE_ALUMNI
        if user.is_employer:
            return EventParticipation.ROLE_EMPLOYER
        if user.is_admin or user.is_main_admin or user.is_staff:
            return EventParticipation.ROLE_ADMIN
        return ""

    def get_user_participation(self, user):
        if not user or not user.is_authenticated:
            return None
        return self.participations.filter(user=user).first()

    def get_participation_error(self, user):
        if not user or not user.is_authenticated:
            return _("Please log in to participate in this event.")
        if not (user.is_student or user.is_alumni or user.is_employer or user.is_admin or user.is_main_admin):
            return _("Your account is not eligible to register for events.")

        if user.is_student and not self.allow_students:
            return _("Students are not allowed to register for this event.")
        if user.is_alumni and not self.allow_alumni:
            return _("Alumni are not allowed to register for this event.")
        if user.is_employer and not self.allow_employers:
            return _("Employers are not allowed to register for this event.")
        if (user.is_admin or user.is_main_admin) and not self.allow_admins:
            return _("Admin users are not allowed to register for this event.")

        participation = self.get_user_participation(user)
        if participation and participation.status == EventParticipation.STATUS_REGISTERED:
            return _("You are already registered for this event.")
        if self.has_started():
            return _("This event has already started.")
        if not self.has_available_seats():
            return _("No seats left for this event.")
        if user.is_employer and self.allowed_employer_categories.exists() and not self.matches_employer_category(user):
            return _("Only eligible employers can register for this event.")
        return ""

    def can_user_participate(self, user):
        return self.get_participation_error(user) == ""


class EventParticipation(models.Model):
    """Participation record for a user and event."""

    ROLE_STUDENT = "student"
    ROLE_ALUMNI = "alumni"
    ROLE_EMPLOYER = "employer"
    ROLE_ADMIN = "admin"

    STATUS_REGISTERED = "registered"
    STATUS_CANCELLED = "cancelled"

    ATTENDANCE_REGISTERED = "registered"
    ATTENDANCE_ATTENDED = "attended"
    ATTENDANCE_ABSENT = "absent"

    ROLE_CHOICES = [
        (ROLE_STUDENT, _("Student")),
        (ROLE_ALUMNI, _("Alumni")),
        (ROLE_EMPLOYER, _("Employer")),
        (ROLE_ADMIN, _("Admin")),
    ]
    STATUS_CHOICES = [
        (STATUS_REGISTERED, _("Registered")),
        (STATUS_CANCELLED, _("Cancelled")),
    ]
    ATTENDANCE_STATUS_CHOICES = [
        (ATTENDANCE_REGISTERED, _("Registered")),
        (ATTENDANCE_ATTENDED, _("Attended")),
        (ATTENDANCE_ABSENT, _("Absent")),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="participations",
        verbose_name=_("Event"),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="event_participations",
        verbose_name=_("User"),
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name=_("Role"),
        help_text=_("User role at the moment of registration"),
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_REGISTERED,
        verbose_name=_("Participation Status"),
    )
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default=ATTENDANCE_REGISTERED,
        verbose_name=_("Attendance Status"),
    )
    registered_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Registered At"))
    cancelled_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Cancelled At"),
    )
    checked_in_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Checked In At"),
    )
    checked_in_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="checked_in_participations",
        verbose_name=_("Checked In By"),
    )
    qr_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        verbose_name=_("QR Token"),
    )
    attendance_code = models.CharField(
        max_length=24,
        unique=True,
        editable=False,
        verbose_name=_("Attendance Code"),
        help_text=_("Unique code used for QR check-in."),
    )
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        verbose_name = _("Event Participation")
        verbose_name_plural = _("Event Participations")
        ordering = ["-registered_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["event", "user"],
                name="unique_event_participation_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} - {self.event}"

    def save(self, *args, **kwargs):
        if not self.attendance_code:
            self.attendance_code = self._generate_attendance_code()
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.status == self.STATUS_CANCELLED and self.checked_in_at:
            raise ValidationError(_("Cancelled participation cannot be checked in."))

    @property
    def is_active(self):
        return self.status == self.STATUS_REGISTERED

    @property
    def can_cancel(self):
        return self.is_active and not self.event.has_started()

    @property
    def effective_attendance_status(self):
        if self.status == self.STATUS_CANCELLED:
            return self.STATUS_CANCELLED
        if self.attendance_status == self.ATTENDANCE_ATTENDED:
            return self.ATTENDANCE_ATTENDED
        if self.event.is_past():
            return self.ATTENDANCE_ABSENT
        return self.ATTENDANCE_REGISTERED

    def get_effective_attendance_status_display(self):
        status_display = {
            self.ATTENDANCE_REGISTERED: _("Registered"),
            self.ATTENDANCE_ATTENDED: _("Attended"),
            self.ATTENDANCE_ABSENT: _("Absent"),
            self.STATUS_CANCELLED: _("Cancelled"),
        }
        return status_display[self.effective_attendance_status]

    def cancel(self):
        if not self.can_cancel:
            raise ValidationError(_("Participation can no longer be cancelled."))
        self.status = self.STATUS_CANCELLED
        self.cancelled_at = timezone.now()
        if self.attendance_status != self.ATTENDANCE_ATTENDED:
            self.attendance_status = self.ATTENDANCE_ABSENT
        self.save(update_fields=["status", "cancelled_at", "attendance_status", "updated_at"])

    def mark_attended(self, checked_in_by=None):
        if self.status != self.STATUS_REGISTERED:
            raise ValidationError(_("This participation is no longer active."))
        if not self.event.check_in_is_open():
            raise ValidationError(_("Check-in is closed because the event has ended."))
        if self.attendance_status == self.ATTENDANCE_ATTENDED:
            raise ValidationError(_("QR code already used."))
        self.attendance_status = self.ATTENDANCE_ATTENDED
        self.checked_in_at = timezone.now()
        self.checked_in_by = checked_in_by
        self.save(
            update_fields=[
                "attendance_status",
                "checked_in_at",
                "checked_in_by",
                "updated_at",
            ]
        )

    @classmethod
    def _generate_attendance_code(cls):
        while True:
            code = f"EVT-{uuid.uuid4().hex[:10].upper()}"
            if not cls.objects.filter(attendance_code=code).exists():
                return code


class EventPhoto(models.Model):
    """Stores photos from events."""

    event = models.ForeignKey(
        Event,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="photos",
        verbose_name=_("Event"),
        help_text=_("The event this photo belongs to"),
    )
    image = models.ImageField(
        upload_to="event_photos/",
        verbose_name=_("Image"),
        help_text=_("The photo file"),
    )
    caption = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Caption"),
        help_text=_("Optional caption for the photo"),
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Uploaded By"),
        help_text=_("User who uploaded this photo"),
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At"),
        help_text=_("When the photo was uploaded"),
    )
    order = models.IntegerField(
        default=0,
        verbose_name=_("Display Order"),
        help_text=_("Order in which to display this photo"),
    )

    class Meta:
        verbose_name = _("Event Photo")
        verbose_name_plural = _("Event Photos")
        ordering = ["order", "-uploaded_at"]

    def __str__(self):
        return f"Photo for {self.event.title}"
