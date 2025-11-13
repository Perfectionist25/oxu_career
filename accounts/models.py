
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    """Модель пользователя с разными ролями"""

    USER_TYPE_CHOICES = [
        ("guest", _("Mehmon")),
        ("student", _("O`quvchi yoki bitiruvchi")),
        ("employer", _("Ish beruvchi")),
        ("admin", _("Admin")),
        ("main_admin", _("Bosh Admin")),
    ]

    # Основная информация
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="guest",
        verbose_name=_("Foydalanuvchi turi"),
    )

    # Hemis API данные для студентов
    # hemis_id = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     unique=True,
    #     null=True,
    #     verbose_name=_("Hemis ID")
    # )

    hemis_data = models.JSONField(
        blank=True, null=True, verbose_name=_("Hemis ma'lumotlari")
    )

    # Контактная информация
    phone_number = PhoneNumberField(
        blank=True, null=True, verbose_name=_("Telefon raqam")
    )
    date_of_birth = models.DateField(
        null=True, blank=True, verbose_name=_("Tug'ilgan sana")
    )

    # Профиль
    bio = models.TextField(max_length=500, blank=True, verbose_name=_("Bio"))
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/%d/", null=True, blank=True, verbose_name=_("Avatar")
    )

    # Локация
    country = CountryField(blank=True, verbose_name=_("Davlat"))
    city = models.CharField(max_length=100, blank=True, verbose_name=_("Shahar"))
    address = models.CharField(max_length=255, blank=True, verbose_name=_("Manzil"))

    # Социальные сети
    website = models.URLField(blank=True, verbose_name=_("Veb sayt"))
    linkedin = models.URLField(blank=True, verbose_name=_("LinkedIn"))
    github = models.URLField(blank=True, verbose_name=_("GitHub"))
    telegram = models.URLField(blank=True, verbose_name=_("Telegram"))

    # Настройки
    email_notifications = models.BooleanField(
        default=True, verbose_name=_("Email xabarnomalari")
    )
    job_alerts = models.BooleanField(
        default=True, verbose_name=_("Ish ogohlantirishlari")
    )
    newsletter = models.BooleanField(default=False, verbose_name=_("Yangiliklar"))

    # Статусы
    is_verified = models.BooleanField(default=False, verbose_name=_("Tasdiqlangan"))
    is_active_employer = models.BooleanField(
        default=False, verbose_name=_("Faol ish beruvchi")
    )

    # Статистика
    profile_views = models.PositiveIntegerField(
        default=0, verbose_name=_("Profil ko'rishlar")
    )
    last_activity = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Oxirgi faollik")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Foydalanuvchi")
        verbose_name_plural = _("Foydalanuvchilar")
        ordering = ["-date_joined"]

    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}"
        return full_name.strip() or self.username

    def get_absolute_url(self):
        return reverse("accounts:profile_detail", kwargs={"pk": self.pk})

    @property
    def unread_notifications_count(self):
        return self.notification_set.filter(is_read=False).count()

    # Свойства для проверки ролей
    @property
    def is_guest(self):
        return self.user_type == "guest"

    @property
    def is_student(self):
        return self.user_type == "student"

    @property
    def is_employer(self):
        return self.user_type == "employer"

    @property
    def is_admin(self):
        return self.user_type == "admin"

    @property
    def is_main_admin(self):
        return self.user_type == "main_admin"

    @property
    def can_create_resume(self):
        """Может ли пользователь создавать резюме"""
        return self.user_type in ["student", "admin", "main_admin"]

    @property
    def can_create_jobs(self):
        """Может ли пользователь создавать вакансии"""
        return (
            self.user_type in ["employer", "admin", "main_admin"]
            and self.is_active_employer
        )

    @property
    def can_manage_users(self):
        """Может ли пользователь управлять другими пользователями"""
        return self.user_type in ["admin", "main_admin"]


class EmployerProfile(models.Model):
    """Профиль работодателя"""

    COMPANY_SIZE_CHOICES = [
        ("1-10", _("1-10 xodim")),
        ("11-50", _("11-50 xodim")),
        ("51-200", _("51-200 xodim")),
        ("201-500", _("201-500 xodim")),
        ("501-1000", _("501-1000 xodim")),
        ("1000+", _("1000+ xodim")),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="employer_profile",
        verbose_name=_("Foydalanuvchi"),
    )

    # Основная информация компании
    company_name = models.CharField(max_length=255, verbose_name=_("Kompaniya nomi"))
    company_logo = models.ImageField(
        upload_to="company_logos/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Kompaniya logotipi"),
    )
    company_description = models.TextField(verbose_name=_("Kompaniya haqida"))

    # Контактная информация компании
    company_email = models.EmailField(blank=True, verbose_name=_("Kompaniya emaili"))
    company_phone = PhoneNumberField(
        blank=True, null=True, verbose_name=_("Kompaniya telefoni")
    )
    company_website = models.URLField(blank=True, verbose_name=_("Kompaniya veb sayti"))

    # Социальные сети компании
    company_linkedin = models.URLField(blank=True, verbose_name=_("Kompaniya LinkedIn"))
    company_telegram = models.URLField(blank=True, verbose_name=_("Kompaniya Telegram"))

    # Дополнительная информация
    company_size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True,
        verbose_name=_("Kompaniya hajmi"),
    )
    industry = models.ForeignKey(
        'jobs.Industry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Soha")
    )
    founded_year = models.IntegerField(
        null=True, blank=True, verbose_name=_("Tashkil etilgan yil")
    )
    headquarters = models.CharField(
        max_length=255, blank=True, verbose_name=_("Bosh qarorgoh")
    )

    # Статистика
    jobs_posted = models.PositiveIntegerField(
        default=0, verbose_name=_("E'lon qilingan ishlar")
    )
    total_views = models.PositiveIntegerField(
        default=0, verbose_name=_("Jami ko'rishlar")
    )

    is_verified = models.BooleanField(
        default=False, verbose_name=_("Tasdiqlangan kompaniya")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Ish beruvchi profili")
        verbose_name_plural = _("Ish beruvchi profillari")

    def __str__(self):
        return f"{self.company_name} - {self.user.username}"

    def get_absolute_url(self):
        return reverse("accounts:employer_profile", kwargs={"pk": self.pk})


class StudentProfile(models.Model):
    """Профиль студента/выпускника"""

    EDUCATION_LEVEL_CHOICES = [
        ("bachelor", _("Bakalavr")),
        ("master", _("Magistr")),
        ("phd", _("PhD")),
        ("college", _("Kollej")),
        ("school", _("Maktab")),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("Foydalanuvchi"),
    )

    # Образовательная информация из Hemis
    student_id = models.CharField(
        max_length=50, blank=True, verbose_name=_("Talaba ID")
    )
    faculty = models.CharField(max_length=255, blank=True, verbose_name=_("Fakultet"))
    specialty = models.CharField(
        max_length=255, blank=True, verbose_name=_("Mutaxassislik")
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        verbose_name=_("Ta'lim darajasi"),
    )
    graduation_year = models.IntegerField(
        null=True, blank=True, verbose_name=_("Bitirgan yili")
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("O'rtacha baho"),
    )

    # Карьерные предпочтения
    desired_position = models.CharField(
        max_length=255, blank=True, verbose_name=_("Istagan lavozim")
    )
    desired_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Istagan maosh"),
    )
    work_type = models.CharField(
        max_length=50,
        choices=[
            ("full_time", _("To`liq kunlik")),
            ("part_time", _("Yarim kunlik")),
            ("remote", _("Uzoq ish")),
            ("internship", _("Stajirovka")),
        ],
        blank=True,
        verbose_name=_("Ish turi"),
    )

    # Статистика
    resumes_created = models.PositiveIntegerField(
        default=0, verbose_name=_("Yaratilgan rezyumelar")
    )
    jobs_applied = models.PositiveIntegerField(
        default=0, verbose_name=_("Ariza berilgan ishlar")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Talaba profili")
        verbose_name_plural = _("Talaba profillari")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialty}"

    def get_absolute_url(self):
        return reverse("accounts:student_profile", kwargs={"pk": self.pk})


class AdminProfile(models.Model):
    """Профиль администратора"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        verbose_name=_("Foydalanuvchi"),
    )

    # Права администратора
    can_manage_students = models.BooleanField(
        default=True, verbose_name=_("Talabalarni boshqarish")
    )
    can_manage_employers = models.BooleanField(
        default=True, verbose_name=_("Ish beruvchilarni boshqarish")
    )
    can_manage_jobs = models.BooleanField(
        default=True, verbose_name=_("Ishlarni boshqarish")
    )
    can_manage_resumes = models.BooleanField(
        default=True, verbose_name=_("Rezyumelarni boshqarish")
    )
    can_view_statistics = models.BooleanField(
        default=True, verbose_name=_("Statistikalarni ko'rish")
    )

    # Статистика администрирования
    students_managed = models.PositiveIntegerField(
        default=0, verbose_name=_("Boshqarilgan talabalar")
    )
    employers_created = models.PositiveIntegerField(
        default=0, verbose_name=_("Yaratilgan ish beruvchilar")
    )
    jobs_approved = models.PositiveIntegerField(
        default=0, verbose_name=_("Tasdiqlangan ishlar")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Admin profili")
        verbose_name_plural = _("Admin profillari")

    def __str__(self):
        return f"Admin: {self.user.username}"


# accounts/models.py - часть с HemisAuth
class HemisAuth(models.Model):
    """Модель для аутентификации через Hemis API"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="hemis_auth",
        verbose_name=_("Foydalanuvchi"),
    )

    # Убедитесь что это поле существует (или добавьте его)
    hemis_user_id = models.CharField(  # Добавьте это поле если нужно
        max_length=100, blank=True, null=True, verbose_name=_("Hemis User ID")
    )

    access_token = models.TextField(verbose_name=_("Access Token"))
    refresh_token = models.TextField(verbose_name=_("Refresh Token"))
    token_expires = models.DateTimeField(verbose_name=_("Token muddati"))

    hemis_user_data = models.JSONField(
        verbose_name=_("Hemis foydalanuvchi ma'lumotlari")
    )

    last_sync = models.DateTimeField(
        auto_now=True, verbose_name=_("Oxirgi sinxronizatsiya")
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Hemis autentifikatsiya")
        verbose_name_plural = _("Hemis autentifikatsiyalar")

    def __str__(self):
        return f"Hemis auth for {self.user.username}"

    def is_token_valid(self):
        """Проверка валидности токена"""
        from django.utils import timezone

        return timezone.now() < self.token_expires


class UserActivity(models.Model):
    """Модель для отслеживания активности пользователей"""

    ACTIVITY_TYPES = [
        ("login", _("Kirish")),
        ("profile_view", _("Profil ko`rish")),
        ("job_apply", _("Ishga ariza")),
        ("resume_create", _("Rezyume yaratish")),
        ("job_create", _("Ish yaratish")),
        ("profile_update", _("Profil yangilash")),
        ("password_change", _("Parol o`zgartirish")),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, verbose_name=_("Foydalanuvchi")
    )

    activity_type = models.CharField(
        max_length=50, choices=ACTIVITY_TYPES, verbose_name=_("Faollik turi")
    )

    description = models.TextField(blank=True, verbose_name=_("Tavsif"))

    ip_address = models.GenericIPAddressField(
        null=True, blank=True, verbose_name=_("IP manzil")
    )

    user_agent = models.TextField(blank=True, verbose_name=_("User Agent"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Yaratilgan vaqt")
    )

    class Meta:
        verbose_name = _("Foydalanuvchi faolligi")
        verbose_name_plural = _("Foydalanuvchi faolliklari")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.get_activity_type_display()} — {self.created_at}"

    def save(self, *args, **kwargs):
        """Обновляем last_activity пользователя при сохранении активности"""
        super().save(*args, **kwargs)
        if self.user:
            self.user.last_activity = self.created_at
            self.user.save(update_fields=["last_activity"])


class Notification(models.Model):
    """Модель для уведомлений пользователей"""

    NOTIFICATION_TYPES = [
        ("job_alert", _("Ish ogohlantirishi")),
        ("application_update", _("Ariza yangilanishi")),
        ("message", _("Xabar")),
        ("system", _("Tizim xabari")),
        ("event", _("Tadbir xabari")),
        ("security", _("Xavfsizlik xabari")),
    ]

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, verbose_name=_("Foydalanuvchi")
    )

    notification_type = models.CharField(
        max_length=50, choices=NOTIFICATION_TYPES, verbose_name=_("Xabar turi")
    )

    title = models.CharField(max_length=255, verbose_name=_("Sarlavha"))

    message = models.TextField(verbose_name=_("Xabar"))

    is_read = models.BooleanField(default=False, verbose_name=_("O`qilgan"))

    related_url = models.URLField(blank=True, verbose_name=_("Bog`langan URL"))

    created_at = models.DateTimeField(
        auto_now_add=True, verbose_name=_("Yaratilgan vaqt")
    )

    class Meta:
        verbose_name = _("Xabar")
        verbose_name_plural = _("Xabarlar")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.user.username}"

    def mark_as_read(self):
        """Пометить уведомление как прочитанное"""
        self.is_read = True
        self.save()


# Signal handlers


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Создать соответствующий профиль при создании пользователя"""
    if created:
        if instance.is_student:
            StudentProfile.objects.create(user=instance)
        elif instance.is_employer:
            EmployerProfile.objects.create(user=instance)
        elif instance.is_admin or instance.is_main_admin:
            AdminProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def create_user_activity_on_signup(sender, instance, created, **kwargs):
    """Создать запись активности при регистрации пользователя"""
    if created:
        UserActivity.objects.create(
            user=instance,
            activity_type="profile_update",
            description=str(_("Foydalanuvchi ro`yxatdan o`tdi")),
        )


@receiver(post_save, sender=EmployerProfile)
def activate_employer_user(sender, instance, created, **kwargs):
    """Активировать пользователя работодателя при создании профиля"""
    if created:
        instance.user.is_active_employer = True
        instance.user.save()
