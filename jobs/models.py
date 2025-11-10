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
    """Вакансия"""

    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract")),
        ("internship", _("Internship")),
        ("remote", _("Remote Work")),
        ("freelance", _("Freelance")),
    ]

    EXPERIENCE_LEVEL_CHOICES = [
        ("intern", _("Intern")),
        ("junior", _("Junior")),
        ("middle", _("Middle")),
        ("senior", _("Senior")),
        ("lead", _("Lead")),
        ("manager", _("Manager")),
        ("director", _("Director")),
    ]

    EDUCATION_LEVEL_CHOICES = [
        ("school", _("High School")),
        ("college", _("College")),
        ("bachelor", _("Bachelor's Degree")),
        ("master", _("Master's Degree")),
        ("phd", _("PhD")),
        ("none", _("No Formal Education Required")),
    ]

    CURRENCY_CHOICES = [
        ("UZS", _("Uzbek Sum (UZS)")),
        ("USD", _("US Dollar (USD)")),
        ("EUR", _("Euro (EUR)")),
    ]

    # Основная информация
    title = models.CharField(max_length=200, verbose_name=_("Job Title"))
    description = models.TextField(verbose_name=_("Job Description"))
    short_description = models.CharField(
        max_length=300, verbose_name=_("Short Description")
    )

    # Компания и локация
    employer = models.ForeignKey(
        "accounts.EmployerProfile",
        on_delete=models.CASCADE,
        related_name="jobs",
        verbose_name=_("Ish beruvchi"),
    )

    location = models.CharField(max_length=100, verbose_name=_("Location"))
    remote_work = models.BooleanField(
        default=False, verbose_name=_("Remote Work Available")
    )
    hybrid_work = models.BooleanField(
        default=False, verbose_name=_("Hybrid Work Available")
    )

    # Тип занятости и уровень
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name=_("Employment Type"),
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        verbose_name=_("Experience Level"),
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name=_("Education Level"),
    )

    # Зарплата
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Salary"),
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary"),
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="UZS",
        verbose_name=_("Currency"),
    )
    hide_salary = models.BooleanField(default=False, verbose_name=_("Hide Salary"))
    salary_negotiable = models.BooleanField(
        default=False, verbose_name=_("Salary Negotiable")
    )

    # Требования
    requirements = models.TextField(verbose_name=_("Requirements"))
    responsibilities = models.TextField(verbose_name=_("Responsibilities"))
    benefits = models.TextField(blank=True, verbose_name=_("Benefits"))

    # Навыки
    skills_required = models.TextField(
        help_text=_("List skills separated by commas"),
        verbose_name=_("Required Skills"),
    )
    preferred_skills = models.TextField(blank=True, verbose_name=_("Preferred Skills"))

    # Контактная информация
    contact_email = models.EmailField(verbose_name=_("Contact Email"))
    contact_person = models.CharField(
        max_length=100, blank=True, verbose_name=_("Contact Person")
    )
    application_url = models.URLField(blank=True, verbose_name=_("Application URL"))

    # Статус и даты
    is_active = models.BooleanField(default=True, verbose_name=_("Active Job"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Job"))
    is_urgent = models.BooleanField(default=False, verbose_name=_("Urgent Hiring"))

    views_count = models.IntegerField(default=0, verbose_name=_("Views Count"))
    applications_count = models.IntegerField(
        default=0, verbose_name=_("Applications Count")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True, blank=True, verbose_name=_("Expires At")
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Created by"),
        related_name="jobs_created",
    )

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ["-created_at"]

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
            return _("Salary negotiable")
        if self.salary_negotiable:
            return _("Negotiable")
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.currency}"
        elif self.salary_min:
            return _("from %(salary)s %(currency)s") % {
                "salary": f"{self.salary_min:,.0f}",
                "currency": self.currency,
            }
        elif self.salary_max:
            return _("up to %(salary)s %(currency)s") % {
                "salary": f"{self.salary_max:,.0f}",
                "currency": self.currency,
            }
        return _("Not specified")

    def days_since_posted(self):
        from django.utils import timezone

        return (timezone.now() - self.created_at).days


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
