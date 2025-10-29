from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth import get_user_model
User = get_user_model()

class EventCategory(models.Model):
    """Категории мероприятий"""
    name = models.CharField(max_length=100, verbose_name=_("Category Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    color = models.CharField(max_length=7, default='#007cba', verbose_name=_("Color"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon"))
    
    class Meta:
        verbose_name = _("Event Category")
        verbose_name_plural = _("Event Categories")
        ordering = ['name']

    def __str__(self):
        return self.name

class Event(models.Model):
    """Мероприятие"""
    EVENT_TYPE_CHOICES = [
        ('conference', _('Conference')),
        ('workshop', _('Workshop')),
        ('seminar', _('Seminar')),
        ('networking', _('Networking')),
        ('career_fair', _('Career Fair')),
        ('hackathon', _('Hackathon')),
        ('webinar', _('Webinar')),
        ('social', _('Social Event')),
        ('training', _('Training')),
        ('other', _('Other')),
    ]
    
    EVENT_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('cancelled', _('Cancelled')),
        ('completed', _('Completed')),
    ]
    
    REGISTRATION_TYPE_CHOICES = [
        ('open', _('Open Registration')),
        ('approval', _('Approval Required')),
        ('invite_only', _('Invitation Only')),
        ('paid', _('Paid Registration')),
    ]

    # Основная информация
    title = models.CharField(max_length=200, verbose_name=_("Event Title"))
    description = models.TextField(verbose_name=_("Description"))
    short_description = models.TextField(max_length=300, verbose_name=_("Short Description"))
    category = models.ForeignKey(EventCategory, on_delete=models.SET_NULL, null=True, verbose_name=_("Category"))
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES, verbose_name=_("Event Type"))
    
    # Даты и время
    start_date = models.DateTimeField(verbose_name=_("Start Date"))
    end_date = models.DateTimeField(verbose_name=_("End Date"))
    
    # Местоположение
    location = models.CharField(max_length=200, verbose_name=_("Location"))
    venue = models.CharField(max_length=200, blank=True, verbose_name=_("Venue"))
    online_event = models.BooleanField(default=False, verbose_name=_("Online Event"))
    online_link = models.URLField(blank=True, verbose_name=_("Online Meeting Link"))
    address = models.TextField(blank=True, verbose_name=_("Full Address"))
    
    # Организатор
    organizer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organized_events', verbose_name=_("Organizer"))
    co_organizers = models.ManyToManyField(User, blank=True, related_name='co_organized_events', verbose_name=_("Co-organizers"))
    
    # Изображения
    banner_image = models.ImageField(upload_to='event_banners/', null=True, blank=True, verbose_name=_("Banner Image"))
    thumbnail = models.ImageField(upload_to='event_thumbnails/', null=True, blank=True, verbose_name=_("Thumbnail"))
    
    # Регистрация
    registration_required = models.BooleanField(default=True, verbose_name=_("Registration Required"))
    registration_type = models.CharField(max_length=20, choices=REGISTRATION_TYPE_CHOICES, default='open', verbose_name=_("Registration Type"))
    registration_deadline = models.DateTimeField(null=True, blank=True, verbose_name=_("Registration Deadline"))
    max_participants = models.IntegerField(null=True, blank=True, verbose_name=_("Maximum Participants"))
    waitlist_enabled = models.BooleanField(default=False, verbose_name=_("Waitlist Enabled"))
    
    # Стоимость
    is_free = models.BooleanField(default=True, verbose_name=_("Free Event"))
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name=_("Price"))
    currency = models.CharField(max_length=3, choices=[('UZS', 'UZS'), ('USD', 'USD')], default='UZS', verbose_name=_("Currency"))
    
    # Настройки
    status = models.CharField(max_length=20, choices=EVENT_STATUS_CHOICES, default='draft', verbose_name=_("Status"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Event"))
    show_attendee_list = models.BooleanField(default=True, verbose_name=_("Show Attendee List"))
    allow_comments = models.BooleanField(default=True, verbose_name=_("Allow Comments"))
    
    # SEO и дополнительные поля
    slug = models.SlugField(unique=True, verbose_name=_("Slug"))
    tags = models.CharField(max_length=500, blank=True, verbose_name=_("Tags"))
    
    # Статистика
    views_count = models.IntegerField(default=0, verbose_name=_("Views Count"))
    registration_count = models.IntegerField(default=0, verbose_name=_("Registration Count"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ['-start_date']

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('events:event_detail', kwargs={'slug': self.slug})

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
    """Регистрация на мероприятие"""
    STATUS_CHOICES = [
        ('registered', _('Registered')),
        ('waiting', _('Waiting List')),
        ('cancelled', _('Cancelled')),
        ('attended', _('Attended')),
        ('no_show', _('No Show')),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations', verbose_name=_("Event"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='event_registrations', verbose_name=_("User"))
    
    # Информация о регистрации
    registration_date = models.DateTimeField(auto_now_add=True, verbose_name=_("Registration Date"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='registered', verbose_name=_("Status"))
    
    # Дополнительная информация
    dietary_restrictions = models.TextField(blank=True, verbose_name=_("Dietary Restrictions"))
    special_requirements = models.TextField(blank=True, verbose_name=_("Special Requirements"))
    comments = models.TextField(blank=True, verbose_name=_("Comments"))
    
    # Для платных мероприятий
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('refunded', _('Refunded')),
    ], default='pending', verbose_name=_("Payment Status"))
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Payment Amount"))
    
    # QR код для проверки
    qr_code = models.ImageField(upload_to='event_qr_codes/', null=True, blank=True, verbose_name=_("QR Code"))
    check_in_time = models.DateTimeField(null=True, blank=True, verbose_name=_("Check-in Time"))
    
    class Meta:
        verbose_name = _("Event Registration")
        verbose_name_plural = _("Event Registrations")
        unique_together = ['event', 'user']
        ordering = ['-registration_date']

    def __str__(self):
        return f"{self.user.username} - {self.event.title}"

    def has_attended(self):
        return self.status == 'attended'

class EventSpeaker(models.Model):
    """Спикеры мероприятий"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='speakers', verbose_name=_("Event"))
    name = models.CharField(max_length=100, verbose_name=_("Speaker Name"))
    title = models.CharField(max_length=200, verbose_name=_("Speaker Title"))
    organization = models.CharField(max_length=200, blank=True, verbose_name=_("Organization"))
    bio = models.TextField(blank=True, verbose_name=_("Biography"))
    photo = models.ImageField(upload_to='speaker_photos/', null=True, blank=True, verbose_name=_("Photo"))
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    website = models.URLField(blank=True, verbose_name=_("Website"))
    linkedin = models.URLField(blank=True, verbose_name=_("LinkedIn"))
    twitter = models.URLField(blank=True, verbose_name=_("Twitter"))
    
    # Порядок отображения
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Event Speaker")
        verbose_name_plural = _("Event Speakers")
        ordering = ['order', 'name']

    def __str__(self):
        return f"{self.name} - {self.event.title}"

class EventSession(models.Model):
    """Сессии/доклады в рамках мероприятия"""
    SESSION_TYPE_CHOICES = [
        ('keynote', _('Keynote')),
        ('workshop', _('Workshop')),
        ('panel', _('Panel Discussion')),
        ('presentation', _('Presentation')),
        ('qna', _('Q&A Session')),
        ('networking', _('Networking')),
        ('break', _('Break')),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='sessions', verbose_name=_("Event"))
    title = models.CharField(max_length=200, verbose_name=_("Session Title"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    session_type = models.CharField(max_length=20, choices=SESSION_TYPE_CHOICES, verbose_name=_("Session Type"))
    
    # Время проведения
    start_time = models.DateTimeField(verbose_name=_("Start Time"))
    end_time = models.DateTimeField(verbose_name=_("End Time"))
    
    # Местоположение (для больших мероприятий)
    location = models.CharField(max_length=100, blank=True, verbose_name=_("Location"))
    
    # Спикеры сессии
    speakers = models.ManyToManyField(EventSpeaker, blank=True, related_name='sessions', verbose_name=_("Speakers"))
    
    # Материалы
    presentation_url = models.URLField(blank=True, verbose_name=_("Presentation URL"))
    materials_url = models.URLField(blank=True, verbose_name=_("Materials URL"))
    
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Event Session")
        verbose_name_plural = _("Event Sessions")
        ordering = ['start_time', 'order']

    def __str__(self):
        return f"{self.title} - {self.event.title}"

    def duration(self):
        duration = self.end_time - self.start_time
        hours = duration.total_seconds() // 3600
        minutes = (duration.total_seconds() % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m"

class EventComment(models.Model):
    """Комментарии к мероприятиям"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='comments', verbose_name=_("Event"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    parent_comment = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies', verbose_name=_("Parent Comment"))
    
    comment = models.TextField(verbose_name=_("Comment"))
    is_approved = models.BooleanField(default=True, verbose_name=_("Approved"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Event Comment")
        verbose_name_plural = _("Event Comments")
        ordering = ['-created_at']

    def __str__(self):
        return f"Comment by {self.user.username} on {self.event.title}"

class EventPhoto(models.Model):
    """Фотографии с мероприятий"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='photos', verbose_name=_("Event"))
    image = models.ImageField(upload_to='event_photos/', verbose_name=_("Image"))
    caption = models.CharField(max_length=200, blank=True, verbose_name=_("Caption"))
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("Uploaded By"))
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Uploaded At"))
    
    # Для сортировки
    order = models.IntegerField(default=0, verbose_name=_("Display Order"))
    
    class Meta:
        verbose_name = _("Event Photo")
        verbose_name_plural = _("Event Photos")
        ordering = ['order', '-uploaded_at']

    def __str__(self):
        return f"Photo for {self.event.title}"

class EventRating(models.Model):
    """Оценки мероприятий"""
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ratings', verbose_name=_("Event"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name=_("User"))
    
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Rating")
    )
    comment = models.TextField(blank=True, verbose_name=_("Comment"))
    
    # Категории оценки
    content_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Content Rating")
    )
    organization_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_("Organization Rating")
    )
    venue_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True, blank=True, verbose_name=_("Venue Rating")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Event Rating")
        verbose_name_plural = _("Event Ratings")
        unique_together = ['event', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"Rating {self.rating} by {self.user.username} for {self.event.title}"

    def overall_rating(self):
        ratings = [self.content_rating, self.organization_rating]
        if self.venue_rating:
            ratings.append(self.venue_rating)
        return sum(ratings) / len(ratings)