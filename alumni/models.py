from django.db import models
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.urls import reverse
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Company(models.Model):
    """Модель компании"""
    INDUSTRY_CHOICES = [
        ('it', _('IT va Texnologiya')),
        ('finance', _('Moliya va Bank')),
        ('education', _('Ta\'lim')),
        ('healthcare', _('Sog\'liqni saqlash')),
        ('manufacturing', _('Ishlab chiqarish')),
        ('retail', _('Chakana savdo')),
        ('energy', _('Energetika')),
        ('telecom', _('Telekommunikatsiya')),
        ('consulting', _('Konsalting')),
        ('other', _('Boshqa')),
    ]
    
    name = models.CharField(max_length=255, verbose_name=_("Kompaniya nomi"))
    industry = models.CharField(
        max_length=100, 
        choices=INDUSTRY_CHOICES,
        verbose_name=_("Soha")
    )
    description = models.TextField(blank=True, verbose_name=_("Tavsif"))
    website = models.URLField(blank=True, verbose_name=_("Veb sayt"))
    logo = models.ImageField(
        upload_to='company_logos/%Y/%m/%d/', 
        blank=True, 
        null=True,
        verbose_name=_("Logotip")
    )
    email = models.EmailField(blank=True, verbose_name=_("Email"))
    phone = PhoneNumberField(blank=True, null=True, verbose_name=_("Telefon"))
    address = models.TextField(blank=True, verbose_name=_("Manzil"))
    employees_count = models.PositiveIntegerField(default=0, verbose_name=_("Xodimlar soni"))
    founded_year = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Asos solingan yil"))
    
    is_verified = models.BooleanField(default=False, verbose_name=_("Tasdiqlangan"))
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Kompaniya")
        verbose_name_plural = _("Kompaniyalar")
        ordering = ['name']

    def __str__(self):
        return self.name

class Skill(models.Model):
    """Модель навыков"""
    CATEGORY_CHOICES = [
        ('technical', _('Texnik ko\'nikmalar')),
        ('soft', _('Yumshoq ko\'nikmalar')),
        ('language', _('Tillarni bilish')),
        ('professional', _('Kasbiy ko\'nikmalar')),
    ]
    
    name = models.CharField(max_length=100, verbose_name=_("Ko'nikma nomi"))
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,
        verbose_name=_("Kategoriya")
    )
    description = models.TextField(blank=True, verbose_name=_("Tavsif"))
    slug = models.SlugField(max_length=100, unique=True, blank=True)

    class Meta:
        verbose_name = _("Ko'nikma")
        verbose_name_plural = _("Ko'nikmalar")
        ordering = ['category', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

class Alumni(models.Model):
    FACULTY_CHOICES = [
        ('engineering', _('Dasturiy injiniring')),
        ('economics', _('Iqtisodiyot')),
        ('management', _('Boshqaruv')),
        ('law', _('Huquqshunoslik')),
        ('philology', _('Filologiya')),
        ('foreign_languages', _('Chet tillari')),
        ('journalism', _('Jurnalistika')),
        ('international_relations', _('Xalqaro munosabatlar')),
    ]
    
    DEGREE_CHOICES = [
        ('bachelor', _('Bakalavr')),
        ('master', _('Magistr')),
        ('phd', _('PhD')),
        ('doctorate', _('Doktorant')),
    ]

    # Basic Information
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        verbose_name=_("Foydalanuvchi")
    )
    name = models.CharField(max_length=255, verbose_name=_("To'liq ism"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name=_("Slug"))
    
    # Education Information
    graduation_year = models.IntegerField(
        verbose_name=_("Bitirgan yili"),
        help_text=_("YYYY formatida")
    )
    faculty = models.CharField(
        max_length=100, 
        choices=FACULTY_CHOICES,
        verbose_name=_("Fakultet")
    )
    degree = models.CharField(
        max_length=50, 
        choices=DEGREE_CHOICES,
        default='bachelor',
        verbose_name=_("Daraja")
    )
    specialization = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name=_("Mutaxassislik")
    )
    
    # Professional Information
    current_position = models.CharField(max_length=255, blank=True, verbose_name=_("Lavozim"))  # Исправлено: было position
    company = models.ForeignKey(  # Исправлено: было CharField
        Company, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name=_("Kompaniya")
    )
    profession = models.CharField(max_length=255, blank=True, verbose_name=_("Kasb"))  # Добавлено для совместимости
    industry = models.CharField(max_length=100, blank=True, verbose_name=_("Soha"))
    
    # Contact Information
    email = models.EmailField(blank=True, verbose_name=_("Elektron pochta"))
    phone = PhoneNumberField(blank=True, null=True, verbose_name=_("Telefon"))
    linkedin = models.URLField(blank=True, verbose_name=_("LinkedIn"))
    website = models.URLField(blank=True, verbose_name=_("Shaxsiy veb sayt"))
    
    # Location
    country = CountryField(blank=True, verbose_name=_("Mamlakat"))
    city = models.CharField(max_length=100, blank=True, verbose_name=_("Shahar"))
    
    # Bio and Media
    bio = models.TextField(blank=True, verbose_name=_("Bio"))
    photo = models.ImageField(
        upload_to='alumni_photos/%Y/%m/%d/', 
        blank=True, 
        null=True,
        verbose_name=_("Profil rasmi")
    )
    resume = models.FileField(
        upload_to='alumni_resumes/%Y/%m/%d/', 
        blank=True, 
        null=True,
        verbose_name=_("Rezyume")
    )
    
    # Status and Preferences
    is_mentor = models.BooleanField(default=False, verbose_name=_("Mentor"))
    is_visible = models.BooleanField(default=True, verbose_name=_("Profil ko'rinadi"))
    show_contact_info = models.BooleanField(default=False, verbose_name=_("Kontakt ma'lumotlarini ko'rsatish"))  # Добавлено для admin
    
    # Skills - ИСПРАВЛЕНО: связь ManyToMany вместо TextField
    skills = models.ManyToManyField(
        Skill, 
        blank=True,
        verbose_name=_("Ko'nikmalar")
    )
    expertise_areas = models.TextField(
        blank=True,
        help_text=_("Mutaxassislik sohalarini vergul bilan ajrating"),
        verbose_name=_("Mutaxassislik sohalari")
    )
    
    # Career Information
    years_of_experience = models.PositiveIntegerField(default=0, verbose_name=_("Tajriba yillari"))
    is_open_to_opportunities = models.BooleanField(default=False, verbose_name=_("Yangi imkoniyatlar qidirmoqda"))
    
    # Social Media
    telegram = models.CharField(max_length=100, blank=True, verbose_name=_("Telegram"))
    twitter = models.URLField(blank=True, verbose_name=_("Twitter"))
    facebook = models.URLField(blank=True, verbose_name=_("Facebook"))
    instagram = models.URLField(blank=True, verbose_name=_("Instagram"))
    github = models.URLField(blank=True, verbose_name=_("GitHub"))  # Добавлено для admin
    
    # Statistics
    profile_views = models.PositiveIntegerField(default=0, verbose_name=_("Profil ko'rishlar"))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Bitiruvchi")
        verbose_name_plural = _("Bitiruvchilar")
        ordering = ['-graduation_year', 'name']
        indexes = [
            models.Index(fields=['graduation_year']),
            models.Index(fields=['faculty']),
            models.Index(fields=['is_mentor']),
        ]

    def __str__(self):
        return f"{self.name} ({self.graduation_year})"

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.name}-{self.graduation_year}")
            slug = base_slug
            counter = 1
            while Alumni.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('alumni:detail', kwargs={'slug': self.slug})

    @property
    def full_name(self):
        return self.name

    @property
    def skills_list(self):
        """Return skills as list"""
        return list(self.skills.values_list('name', flat=True))

    @property
    def expertise_list(self):
        """Return expertise areas as list"""
        if self.expertise_areas:
            return [area.strip() for area in self.expertise_areas.split(',')]
        return []

    @property
    def is_recent_graduate(self):
        """Check if alumni graduated in last 3 years"""
        from django.utils import timezone
        current_year = timezone.now().year
        return current_year - self.graduation_year <= 3

    @property
    def is_experienced(self):
        """Check if alumni has more than 5 years experience"""
        return self.years_of_experience >= 5

class Connection(models.Model):
    """Модель для связей между выпускниками"""
    STATUS_CHOICES = [
        ('pending', _('Kutilmoqda')),
        ('accepted', _("Qabul qilindi")),
        ('rejected', _("Rad etildi")),
        ('blocked', _('Bloklangan')),
    ]
    
    from_user = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='sent_connections',
        verbose_name=_("Kimdan")
    )
    to_user = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='received_connections',
        verbose_name=_("Kimga")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Holat")
    )
    message = models.TextField(blank=True, verbose_name=_("Xabar"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    responded_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Javob berilgan sana"))

    class Meta:
        verbose_name = _("Bog'lanish")
        verbose_name_plural = _("Bog'lanishlar")
        unique_together = ['from_user', 'to_user']

    def __str__(self):
        return f"{self.from_user.name} → {self.to_user.name}"

class Mentorship(models.Model):
    """Модель менторства"""
    STATUS_CHOICES = [
        ('pending', _('Kutilmoqda')),
        ('active', _('Faol')),
        ('completed', _('Yakunlangan')),
        ('cancelled', _('Bekor qilingan')),
    ]
    
    COMMUNICATION_CHOICES = [
        ('email', _('Email')),
        ('video_call', _('Video qo\'ng\'iroq')),
        ('in_person', _('Shaxsan')),
        ('phone', _('Telefon')),
    ]
    
    mentor = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='mentor_relationships',
        verbose_name=_("Mentor")
    )
    mentee = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='mentee_relationships',
        verbose_name=_("Menti")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Holat")
    )
    message = models.TextField(blank=True, verbose_name=_("Xabar"))
    expected_duration = models.CharField(max_length=100, blank=True, verbose_name=_("Kutilayotgan davomiylik"))
    communication_preference = models.CharField(
        max_length=20,
        choices=COMMUNICATION_CHOICES,
        default='video_call',
        verbose_name=_("Muloqot usuli")
    )
    start_date = models.DateField(null=True, blank=True, verbose_name=_("Boshlanish sanasi"))
    end_date = models.DateField(null=True, blank=True, verbose_name=_("Tugash sanasi"))
    
    # Feedback
    mentee_feedback = models.TextField(blank=True, verbose_name=_("Menti fikri"))
    mentor_feedback = models.TextField(blank=True, verbose_name=_("Mentor fikri"))
    rating = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Reyting (1-5)"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Mentorlik")
        verbose_name_plural = _("Mentorliklar")
        unique_together = ['mentor', 'mentee']

    def __str__(self):
        return f"{self.mentor.name} → {self.mentee.name}"

class Job(models.Model):
    """Модель вакансий"""
    EMPLOYMENT_TYPES = [
        ('full_time', _('To\'liq stavka')),
        ('part_time', _('Yarim stavka')),
        ('contract', _('Kontrakt')),
        ('internship', _('Stajirovka')),
        ('remote', _('Masofaviy ish')),
    ]
    
    CURRENCY_CHOICES = [
        ('USD', 'USD'),
        ('EUR', 'EUR'),
        ('UZS', 'UZS'),
        ('RUB', 'RUB'),
    ]
    
    title = models.CharField(max_length=255, verbose_name=_("Lavozim"))
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_("Kompaniya")
    )
    posted_by = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("E'lon qilgan")
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        verbose_name=_("Ish turi")
    )
    location = models.CharField(max_length=255, verbose_name=_("Manzil"))
    remote_work = models.BooleanField(default=False, verbose_name=_("Masofaviy ish"))
    
    # Salary
    salary_min = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_("Minimal maosh")
    )
    salary_max = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        verbose_name=_("Maksimal maosh")
    )
    currency = models.CharField(
        max_length=3, 
        choices=CURRENCY_CHOICES, 
        default='USD',
        verbose_name=_("Valyuta")
    )
    
    # Description
    description = models.TextField(verbose_name=_("Tavsif"))
    requirements = models.TextField(verbose_name=_("Talablar"))
    benefits = models.TextField(blank=True, verbose_name=_("Afzalliklar"))
    
    # Contact
    contact_email = models.EmailField(verbose_name=_("Aloqa emaili"))
    application_url = models.URLField(blank=True, verbose_name=_("Ariza uchun havola"))
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    expires_at = models.DateField(null=True, blank=True, verbose_name=_("Muddati"))
    views = models.PositiveIntegerField(default=0, verbose_name=_("Ko'rishlar soni"))
    
    # Applicants
    applicants = models.ManyToManyField(
        Alumni,
        through='JobApplication',
        related_name='applied_jobs',
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Vakansiya")
        verbose_name_plural = _("Vakansiyalar")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} at {self.company.name}"

class JobApplication(models.Model):
    """Модель заявок на вакансии"""
    STATUS_CHOICES = [
        ('applied', _('Ariza yuborilgan')),
        ('reviewed', _('Ko\'rib chiqilgan')),
        ('interview', _('Intervyu')),
        ('rejected', _('Rad etilgan')),
        ('accepted', _('Qabul qilingan')),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, verbose_name=_("Vakansiya"))
    applicant = models.ForeignKey(Alumni, on_delete=models.CASCADE, verbose_name=_("Arizachi"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='applied',
        verbose_name=_("Holat")
    )
    cover_letter = models.TextField(blank=True, verbose_name=_("Xat"))
    resume = models.FileField(
        upload_to='job_applications/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name=_("Rezyume")
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Ariza vaqti"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Ish arizasi")
        verbose_name_plural = _("Ish arizalari")
        unique_together = ['job', 'applicant']

    def __str__(self):
        return f"{self.applicant.name} - {self.job.title}"

class Event(models.Model):
    """Модель мероприятий"""
    EVENT_TYPES = [
        ('networking', _('Tarmoq tadbiri')),
        ('workshop', _('Trening')),
        ('conference', _('Konferensiya')),
        ('seminar', _('Seminar')),
        ('career_fair', _('Karyera yarmarkasi')),
        ('reunion', _('Uchrashuv')),
    ]
    
    title = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    description = models.TextField(verbose_name=_("Tavsif"))
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name=_("Tadbir turi")
    )
    date = models.DateField(verbose_name=_("Sana"))
    time = models.TimeField(verbose_name=_("Vaqt"))
    location = models.CharField(max_length=255, verbose_name=_("Manzil"))
    organizer = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Tashkilotchi")
    )
    
    # Registration
    registration_required = models.BooleanField(default=False, verbose_name=_("Ro'yxatdan o'tish talab qilinadi"))
    max_participants = models.PositiveIntegerField(null=True, blank=True, verbose_name=_("Maksimal ishtirokchilar"))
    participants = models.ManyToManyField(
        Alumni,
        related_name='events',
        blank=True,
        verbose_name=_("Ishtirokchilar")
    )
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name=_("Faol"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Tadbir")
        verbose_name_plural = _("Tadbirlar")
        ordering = ['-date']

    def __str__(self):
        return self.title

class News(models.Model):
    """Модель новостей"""
    CATEGORY_CHOICES = [
        ('alumni', _('Bitiruvchilar yangiliklari')),
        ('career', _('Karyera yangiliklari')),
        ('education', _('Ta\'lim yangiliklari')),
        ('events', _('Tadbirlar')),
        ('opportunities', _('Imkoniyatlar')),
    ]
    
    title = models.CharField(max_length=255, verbose_name=_("Sarlavha"))
    slug = models.SlugField(max_length=255, unique=True, blank=True, verbose_name=_("Slug"))
    content = models.TextField(verbose_name=_("Mazmuni"))
    author = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Muallif")
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='alumni',
        verbose_name=_("Kategoriya")
    )
    image = models.ImageField(
        upload_to='news_images/%Y/%m/%d/',
        blank=True,
        null=True,
        verbose_name=_("Rasm")
    )
    tags = models.CharField(max_length=255, blank=True, verbose_name=_("Teglar"))  # Добавлено для admin
    
    # Status
    is_published = models.BooleanField(default=True, verbose_name=_("Nashr etilgan"))
    views = models.PositiveIntegerField(default=0, verbose_name=_("Ko'rishlar soni"))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))

    class Meta:
        verbose_name = _("Yangilik")
        verbose_name_plural = _("Yangiliklar")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

class Message(models.Model):
    """Модель сообщений"""
    sender = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='sent_messages',
        verbose_name=_("Yuboruvchi")
    )
    receiver = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name='received_messages',
        verbose_name=_("Qabul qiluvchi")
    )
    subject = models.CharField(max_length=255, verbose_name=_("Mavzu"))
    body = models.TextField(verbose_name=_("Xabar matni"))
    is_read = models.BooleanField(default=False, verbose_name=_("O'qilgan"))
    parent_message = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
        verbose_name=_("Asosiy xabar")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))

    class Meta:
        verbose_name = _("Xabar")
        verbose_name_plural = _("Xabarlar")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sender.name} to {self.receiver.name}: {self.subject}"

# Signal handlers
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=Alumni)
def create_mentor_profile(sender, instance, created, **kwargs):
    """Create mentor profile when alumni is marked as mentor"""
    if instance.is_mentor and not hasattr(instance, 'mentor_profile'):
        from .models import MentorProfile
        MentorProfile.objects.create(alumni=instance)

@receiver(post_save, sender=Alumni)
def update_user_profile(sender, instance, **kwargs):
    """Update user profile when alumni profile is updated"""
    if instance.user:
        # Sync basic information with user profile
        user = instance.user
        if not user.first_name and ' ' in instance.name:
            names = instance.name.split(' ', 1)
            user.first_name = names[0]
            if len(names) > 1:
                user.last_name = names[1]
            user.save()