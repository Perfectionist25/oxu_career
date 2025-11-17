from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Industry(models.Model):
    """Отрасли промышленности/сферы деятельности"""

    name = models.CharField(max_length=100, verbose_name=_("Industry Name"))
    description = models.TextField(blank=True, verbose_name=_("Description"))
    icon = models.CharField(max_length=50, blank=True, verbose_name=_("Icon"))

    class Meta:
        verbose_name = _("Industry")
        verbose_name_plural = _("Industries")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Job(models.Model):
    """Ish o'rinlari (Vakansiya)"""

    # Ish turi tanlovlari
    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", _("To'liq ish kuni")),
        ("part_time", _("Yarim ish kuni")),
        ("contract", _("Kontrakt asosida")),
        ("internship", _("Stajyorlik")),
        ("remote", _("Masofaviy ish")),
        ("freelance", _("Frilans")),
        ("shift", _("Smenali ish")),
        ("flexible", _("Moslashuvchan grafik")),
    ]

    # Tajriba darajasi
    EXPERIENCE_LEVEL_CHOICES = [
        ("no_experience", _("Tajriba talab qilinmaydi")),
        ("intern", _("Stajyor")),
        ("junior", _("Yosh mutaxassis")),
        ("middle", _("O'rta daraja")),
        ("senior", _("Katta mutaxassis")),
        ("lead", _("Lid")),
        ("manager", _("Menejer")),
        ("director", _("Rahbar")),
    ]

    # Ma'lumot darajasi
    EDUCATION_LEVEL_CHOICES = [
        ("school", _("O'rta ma'lumot")),
        ("college", _("O'rta maxsus")),
        ("bachelor", _("Bakalavr")),
        ("master", _("Magistr")),
        ("phd", _("PhD")),
        ("none", _("Ma'lumot talab qilinmaydi")),
    ]

    # Valyuta tanlovlari
    CURRENCY_CHOICES = [
        ("UZS", _("So'm")),
        ("USD", _("AQSH dollari")),
        ("EUR", _("Yevro")),
    ]

    # Ish turlari - ИСПРАВЛЕНО: убраны лишние поля и исправлены опечатки
    WORK_TYPE_CHOICES = [  # ИСПРАВЛЕНО: переименовано и исправлены опечатки
        ("remote", _("Uydan ishlash")),
        ("hybrid", _("Gibrid ishlash")),
        ("office", _("Ishxonada ishlash")),
    ]

    # ASOSIY MA'LUMOTLAR
    title = models.CharField(max_length=200, verbose_name=_("Lavozim nomi"))
    description = models.TextField(verbose_name=_("Ish haqida batafsil"))
    short_description = models.CharField(max_length=300, verbose_name=_("Qisqacha tavsif"))

    # KORXONA VA MANZIL
    employer = models.ForeignKey("accounts.EmployerProfile", on_delete=models.CASCADE, related_name="jobs", verbose_name=_("Ish beruvchi"))

    location = models.CharField(max_length=100, verbose_name=_("Ish joyi manzili"), blank=True, default=_('Kiritilmagan'))
    district = models.CharField(max_length=100, blank=True, verbose_name=_("Tuman/Shahar"))
    region = models.CharField(max_length=100, default=_("Kiritilmagan"), verbose_name=_("Viloyat"), blank=True)
    
    # Ish turi - ИСПРАВЛЕНО: используется исправленный choices
    work_type = models.CharField(max_length=20, choices=WORK_TYPE_CHOICES, verbose_name=_('Ish tipi'))

    # ISH SHARTLARI
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, verbose_name=_("Ish turi"))
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, verbose_name=_("Tajriba darajasi"))
    education_level = models.CharField(max_length=20, choices=EDUCATION_LEVEL_CHOICES, verbose_name=_("Ma'lumot darajasi"))

    # MAOSH
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Minimal maosh"))
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Maksimal maosh"))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default="UZS", verbose_name=_("Valyuta"))
    hide_salary = models.BooleanField(default=False, verbose_name=_("Maoshnni yashirish"))
    salary_negotiable = models.BooleanField(default=False, verbose_name=_("Maosh kelishilgan holda"))
    
    # QO'SHIMCHA TO'LOVLAR
    bonus_system = models.BooleanField(default=False, verbose_name=_("Bonus tizimi"))
    kpi_bonus = models.BooleanField(default=False, verbose_name=_("KPI asosida bonus"))
    performance_bonus = models.BooleanField(default=False, verbose_name=_("Ish natijasiga ko'ra bonus"))

    # TALABLAR
    requirements = models.TextField(verbose_name=_("Talablar"))
    responsibilities = models.TextField(verbose_name=_("Majburiyatlar"))
    benefits = models.TextField(blank=True, verbose_name=_("Ish shartlari va imtiyozlar"))

    # KO'NIKMALAR
    skills_required = models.TextField(help_text=_("Ko'nikmalarni vergul bilan ajrating"), verbose_name=_("Talab qilinadigan ko'nikmalar"))
    preferred_skills = models.TextField(blank=True, verbose_name=_("Qo'shimcha ko'nikmalar"))

    # TIL BILISH
    language_requirements = models.TextField(blank=True, verbose_name=_("Til bilish darajasi"), help_text=_("Masalan: Ingliz tili - O'rta daraja"))

    # KONTAKT MA'LUMOTLARI
    contact_email = models.EmailField(verbose_name=_("Aloqa uchun email"))
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name=_("Telefon raqam"))
    contact_person = models.CharField(max_length=100, blank=True, verbose_name=_("Mas'ul shaxs"))
    application_url = models.URLField(blank=True, verbose_name=_("Ariza topshirish havolasi"))

    # ISH JARAYONI
    work_schedule = models.CharField(max_length=100, blank=True, verbose_name=_("Ish jadvali"), help_text=_("Masalan: 09:00 - 18:00, dam olish kunlari: Shanba, Yakshanba"))
    probation_period = models.CharField(max_length=50, blank=True, verbose_name=_("Sinov muddati"), help_text=_("Masalan: 3 oy"))

    # STATISTIKA VA HOLAT
    is_active = models.BooleanField(default=True, verbose_name=_("Faol vakansiya"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Tavsiya etilgan"))
    is_urgent = models.BooleanField(default=False, verbose_name=_("Shoshilinch"))
    is_premium = models.BooleanField(default=False, verbose_name=_("Premium vakansiya"))

    views_count = models.IntegerField(default=0, verbose_name=_("Ko'rishlar soni"))
    applications_count = models.IntegerField(default=0, verbose_name=_("Arizalar soni"))
    favorites_count = models.IntegerField(default=0, verbose_name=_("Saqlanganlar soni"))

    # SANALAR
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Yaratilgan sana"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Yangilangan sana"))
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Muddati tugaydigan sana"))
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Yaratgan foydalanuvchi"), related_name="jobs_created")

    # ДОБАВЛЕНЫ ОТСУТСТВУЮЩИЕ ПОЛЯ ДЛЯ work_type_display метода
    remote_work = models.BooleanField(default=False, verbose_name=_("Uzoq ish"))
    hybrid_work = models.BooleanField(default=False, verbose_name=_("Gibrid ish"))
    office_work = models.BooleanField(default=False, verbose_name=_("Ofisda ish"))

    class Meta:
        verbose_name = _("Ish o'rini")
        verbose_name_plural = _("Ish o'rinlari")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['employment_type', 'experience_level']),
            models.Index(fields=['region', 'district']),
        ]

    def __str__(self):
        return f"{self.title} - {self.employer.company_name}"

    def get_absolute_url(self):
        return reverse("jobs:job_detail", kwargs={"pk": self.pk})

    def is_expired(self):
        from django.utils import timezone
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def salary_range(self):
        if self.hide_salary:
            return _("Maosh kelishilgan holda")
        if self.salary_negotiable:
            return _("Kelishilgan holda")
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.get_currency_display()}"
        elif self.salary_min:
            return _("dan %(salary)s %(currency)s") % {
                "salary": f"{self.salary_min:,.0f}",
                "currency": self.get_currency_display(),
            }
        elif self.salary_max:
            return _("gacha %(salary)s %(currency)s") % {
                "salary": f"{self.salary_max:,.0f}",
                "currency": self.get_currency_display(),
            }
        return _("Ko'rsatilmagan")

    def days_since_posted(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).days

    def work_type_display(self):
        types = []
        if self.remote_work:
            types.append(_("Uydan ishlash"))
        if self.hybrid_work:
            types.append(_("Gibrid"))
        if self.office_work:
            types.append(_("Ofisda"))
        return ", ".join(types) if types else _("Ko'rsatilmagan")

    def location_display(self):
        if self.district:
            return f"{self.region}, {self.district}"
        return self.region

    def short_requirements(self):
        if len(self.requirements) > 150:
            return self.requirements[:150] + "..."
        return self.requirements


class JobApplication(models.Model):
    """Отклик на вакансию"""

    STATUS_CHOICES = [
        ("applied", _("Applied")),
        ("reviewed", _("Under Review")),
        ("shortlisted", _("Shortlisted")),
        ("interview", _("Interview")),
        ("rejected", _("Rejected")),
        ("hired", _("Hired")),
        ("withdrawn", _("Withdrawn")),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Job"),
    )
    candidate = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name=_("Candidate")
    )

    # Резюме и сопроводительное письмо
    cv = models.ForeignKey(
        "cvbuilder.CV",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Resume"),
    )
    cover_letter = models.TextField(verbose_name=_("Cover Letter"))

    # Ожидания
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Expected Salary"),
    )
    notice_period = models.IntegerField(
        default=0, help_text=_("Days"), verbose_name=_("Notice Period")
    )
    available_from = models.DateField(
        null=True, blank=True, verbose_name=_("Available From")
    )

    # Статус
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied",
        verbose_name=_("Status"),
    )
    status_changed_at = models.DateTimeField(
        auto_now=True, verbose_name=_("Status Changed")
    )

    # Дополнительная информация
    is_read = models.BooleanField(default=False, verbose_name=_("Read by Employer"))
    source = models.CharField(
        max_length=50, blank=True, verbose_name=_("Application Source")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        unique_together = ["job", "candidate"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application from {self.candidate.username} for {self.job.title}"


class SavedJob(models.Model):
    """Сохраненные вакансии"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_jobs",
        verbose_name=_("User"),
    )
    job = models.ForeignKey(
        Job, on_delete=models.CASCADE, related_name="saved_by", verbose_name=_("Job")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Saved At"))

    class Meta:
        verbose_name = _("Saved Job")
        verbose_name_plural = _("Saved Jobs")
        unique_together = ["user", "job"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


class JobAlert(models.Model):
    """Оповещения о вакансиях"""

    FREQUENCY_CHOICES = [
        ("daily", _("Daily")),
        ("weekly", _("Weekly")),
        ("monthly", _("Monthly")),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="job_alert_subscriptions",
        verbose_name=_("User"),
    )
    name = models.CharField(max_length=100, verbose_name=_("Alert Name"))

    # Параметры поиска
    keywords = models.CharField(max_length=200, blank=True, verbose_name=_("Keywords"))
    location = models.CharField(max_length=100, blank=True, verbose_name=_("Location"))
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Industry"),
    )
    employment_type = models.CharField(
        max_length=20,
        choices=Job.EMPLOYMENT_TYPE_CHOICES,
        blank=True,
        verbose_name=_("Employment Type"),
    )
    experience_level = models.CharField(
        max_length=20,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        blank=True,
        verbose_name=_("Experience Level"),
    )

    # Настройки
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default="daily",
        verbose_name=_("Frequency"),
    )
    last_sent = models.DateTimeField(null=True, blank=True, verbose_name=_("Last Sent"))

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Job Alert")
        verbose_name_plural = _("Job Alerts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.user.username}"