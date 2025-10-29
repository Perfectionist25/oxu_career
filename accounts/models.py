from django.db import models
from django.contrib.auth.models import AbstractUser
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings

class CustomUser(AbstractUser):
    """Унифицированная кастомная модель пользователя для OXU University"""
    
    USER_TYPE_CHOICES = [
        ('student', _('Student')),
        ('alumni', _('Alumni')),
        ('employer', _('Employer')),
        ('staff', _('Staff')),
        ('faculty', _('Faculty')),
        ('mentor', _('Mentor')),
    ]
    
    user_type = models.CharField(
        max_length=20, 
        choices=USER_TYPE_CHOICES, 
        default='student',
        verbose_name=_("User Type")
    )
    
    # Контактная информация
    phone_number = PhoneNumberField(
        blank=True, 
        null=True,
        verbose_name=_("Phone Number")
    )
    
    date_of_birth = models.DateField(
        null=True, 
        blank=True, 
        verbose_name=_("Date of Birth")
    )
    
    # Профиль
    bio = models.TextField(
        max_length=500,
        blank=True, 
        verbose_name=_("Bio")
    )
    
    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/%d/', 
        null=True, 
        blank=True,
        verbose_name=_("Avatar")
    )
    
    # Локация
    country = CountryField(
        blank=True, 
        verbose_name=_("Country")
    )
    
    city = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name=_("City")
    )
    
    address = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("Address")
    )
    
    # Профессиональная информация
    organization = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("Organization")
    )
    
    position = models.CharField(
        max_length=255, 
        blank=True, 
        verbose_name=_("Position")
    )
    
    website = models.URLField(
        blank=True, 
        verbose_name=_("Website")
    )
    
    linkedin = models.URLField(
        blank=True, 
        verbose_name=_("LinkedIn")
    )
    
    github = models.URLField(
        blank=True, 
        verbose_name=_("GitHub")
    )
    
    # Документы
    resume = models.FileField(
        upload_to='resumes/%Y/%m/%d/', 
        blank=True, 
        null=True, 
        verbose_name=_("Resume")
    )
    
    # Настройки уведомлений
    email_notifications = models.BooleanField(
        default=True, 
        verbose_name=_("Email Notifications")
    )
    
    job_alerts = models.BooleanField(
        default=True, 
        verbose_name=_("Job Alerts")
    )
    
    newsletter = models.BooleanField(
        default=False, 
        verbose_name=_("Newsletter")
    )
    
    # Верификация и статистика
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified")
    )
    
    verification_token = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name=_("Verification Token")
    )
    
    profile_views = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Profile Views")
    )
    
    resume_views = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Resume Views")
    )
    
    last_activity = models.DateTimeField(
        null=True, 
        blank=True, 
        verbose_name=_("Last Activity")
    )
    
    # Даты
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ['-date_joined']

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.username

    def get_absolute_url(self):
        return reverse('accounts:profile_detail', kwargs={'pk': self.pk})

    @property
    def is_student(self):
        return self.user_type == 'student'

    @property
    def is_employer(self):
        return self.user_type == 'employer'

    @property
    def is_alumni(self):
        return self.user_type == 'alumni'

    @property
    def is_mentor(self):
        return self.user_type == 'mentor'

    @property
    def is_staff_member(self):
        return self.user_type == 'staff'

    @property
    def is_faculty(self):
        return self.user_type == 'faculty'

    def send_verification_email(self):
        """Отправка email для верификации"""
        if not self.verification_token:
            import secrets
            self.verification_token = secrets.token_urlsafe(32)
            self.save()
        
        verification_url = f"{settings.SITE_URL}{reverse('accounts:verify_email', kwargs={'token': self.verification_token})}"
        
        send_mail(
            _("Verify your email for OXU University"),
            _(f"Please verify your email by clicking the following link: {verification_url}"),
            settings.DEFAULT_FROM_EMAIL,
            [self.email],
            fail_silently=False,
        )


class EmailVerification(models.Model):
    """Модель для верификации email"""
    
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_("User")
    )
    
    token = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name=_("Token")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Created At")
    )
    
    expires_at = models.DateTimeField(
        verbose_name=_("Expires At")
    )

    class Meta:
        verbose_name = _("Email Verification")
        verbose_name_plural = _("Email Verifications")
        ordering = ['-created_at']

    def __str__(self):
        return f"Email verification for {self.user.email}"

    def is_expired(self):
        from django.utils import timezone
        return timezone.now() > self.expires_at


class UserActivity(models.Model):
    """Модель для отслеживания активности пользователей"""
    
    ACTIVITY_TYPES = [
        ('login', _('Login')),
        ('profile_view', _('Profile View')),
        ('resume_view', _('Resume View')),
        ('job_apply', _('Job Application')),
        ('resource_download', _('Resource Download')),
        ('event_register', _('Event Registration')),
        ('profile_update', _('Profile Update')),
        ('password_change', _('Password Change')),
    ]

    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_("User")
    )
    
    activity_type = models.CharField(
        max_length=50, 
        choices=ACTIVITY_TYPES, 
        verbose_name=_("Activity Type")
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description")
    )
    
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True, 
        verbose_name=_("IP Address")
    )
    
    user_agent = models.TextField(
        blank=True, 
        verbose_name=_("User Agent")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Created At")
    )

    class Meta:
        verbose_name = _("User Activity")
        verbose_name_plural = _("User Activities")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} — {self.get_activity_type_display()} — {self.created_at}"

    def save(self, *args, **kwargs):
        """Обновляем last_activity пользователя при сохранении активности"""
        super().save(*args, **kwargs)
        if self.user:
            self.user.last_activity = self.created_at
            self.user.save(update_fields=['last_activity'])


class Notification(models.Model):
    """Модель для уведомлений пользователей"""
    
    NOTIFICATION_TYPES = [
        ('job_alert', _('Job Alert')),
        ('application_update', _('Application Update')),
        ('message', _('Message')),
        ('system', _('System Notification')),
        ('event', _('Event Notification')),
        ('security', _('Security Notification')),
    ]

    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_("User")
    )
    
    notification_type = models.CharField(
        max_length=50, 
        choices=NOTIFICATION_TYPES, 
        verbose_name=_("Notification Type")
    )
    
    title = models.CharField(
        max_length=255, 
        verbose_name=_("Title")
    )
    
    message = models.TextField(
        verbose_name=_("Message")
    )
    
    is_read = models.BooleanField(
        default=False, 
        verbose_name=_("Read")
    )
    
    related_url = models.URLField(
        blank=True, 
        verbose_name=_("Related URL")
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Created At")
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} — {self.user.username}"

    def mark_as_read(self):
        """Пометить уведомление как прочитанное"""
        self.is_read = True
        self.save()

    def send_email_notification(self):
        """Отправить уведомление по email если пользователь разрешил"""
        if self.user.email_notifications:
            send_mail(
                self.title,
                self.message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=True,
            )


class Skill(models.Model):
    """Модель для навыков"""
    
    SKILL_CATEGORIES = [
        ('technical', _('Technical Skills')),
        ('soft', _('Soft Skills')),
        ('language', _('Languages')),
        ('certification', _('Certifications')),
    ]

    name = models.CharField(
        max_length=100, 
        verbose_name=_("Skill Name")
    )
    
    category = models.CharField(
        max_length=50, 
        choices=SKILL_CATEGORIES, 
        verbose_name=_("Category")
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description")
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_category_display()})"


class UserSkill(models.Model):
    """Модель для связи пользователей и навыков"""
    
    PROFICIENCY_LEVELS = [
        ('beginner', _('Beginner')),
        ('intermediate', _('Intermediate')),
        ('advanced', _('Advanced')),
        ('expert', _('Expert')),
    ]

    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        verbose_name=_("User")
    )
    
    skill = models.ForeignKey(
        Skill, 
        on_delete=models.CASCADE, 
        verbose_name=_("Skill")
    )
    
    proficiency = models.CharField(
        max_length=20, 
        choices=PROFICIENCY_LEVELS, 
        default='intermediate', 
        verbose_name=_("Proficiency Level")
    )
    
    years_of_experience = models.PositiveIntegerField(
        default=0, 
        verbose_name=_("Years of Experience")
    )
    
    is_primary = models.BooleanField(
        default=False, 
        verbose_name=_("Primary Skill")
    )

    class Meta:
        verbose_name = _("User Skill")
        verbose_name_plural = _("User Skills")
        unique_together = ['user', 'skill']

    def __str__(self):
        return f"{self.user.username} — {self.skill.name} ({self.get_proficiency_display()})"


# Signal handlers
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=CustomUser)
def create_user_activity_on_signup(sender, instance, created, **kwargs):
    """Создать запись активности при регистрации пользователя"""
    if created:
        UserActivity.objects.create(
            user=instance,
            activity_type='profile_update',
            description=_('User registration completed')
        )

@receiver(post_save, sender=CustomUser)
def send_welcome_email(sender, instance, created, **kwargs):
    """Отправить приветственное письмо новому пользователю"""
    if created and instance.email:
        send_mail(
            _("Welcome to OXU University!"),
            _("Thank you for registering with OXU University. We're excited to have you on board!"),
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=True,
        )