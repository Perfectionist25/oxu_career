from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Industry(models.Model):
    """Represents industry sectors for job categorization"""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Industry Name"),
        help_text=_("Name of the industry sector")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the industry")
    )
    icon = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Icon"),
        help_text=_("Icon identifier for UI display")
    )

    class Meta:
        verbose_name = _("Industry")
        verbose_name_plural = _("Industries")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Job(models.Model):
    """Stores job vacancy information with multilingual support"""

    # Employment type choices
    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract")),
        ("internship", _("Internship")),
        ("remote", _("Remote")),
        ("freelance", _("Freelance")),
        ("shift", _("Shift Work")),
        ("flexible", _("Flexible Schedule")),
    ]

    # Experience level choices
    EXPERIENCE_LEVEL_CHOICES = [
        ("no_experience", _("No Experience Required")),
        ("intern", _("Intern")),
        ("junior", _("Junior")),
        ("middle", _("Middle")),
        ("senior", _("Senior")),
        ("lead", _("Lead")),
        ("manager", _("Manager")),
        ("director", _("Director")),
    ]

    # Education level choices
    EDUCATION_LEVEL_CHOICES = [
        ("school", _("High School")),
        ("college", _("College")),
        ("bachelor", _("Bachelor's Degree")),
        ("master", _("Master's Degree")),
        ("phd", _("PhD")),
        ("none", _("No Education Required")),
    ]

    # Currency choices
    CURRENCY_CHOICES = [
        ("UZS", _("UZS")),
        ("USD", _("USD")),
        ("EUR", _("EUR")),
    ]

    # Work type choices
    WORK_TYPE_CHOICES = [
        ("remote", _("Remote")),
        ("hybrid", _("Hybrid")),
        ("office", _("Office")),
    ]

    # Basic Information
    title = models.CharField(
        max_length=200,
        verbose_name=_("Job Title"),
        help_text=_("Enter the position title")
    )
    description = models.TextField(
        verbose_name=_("Job Description"),
        help_text=_("Detailed description of the job responsibilities")
    )
    short_description = models.CharField(
        max_length=300,
        verbose_name=_("Short Description"),
        help_text=_("Brief summary of the job")
    )

    # Company and Location
    employer = models.ForeignKey(
        "accounts.EmployerProfile",
        on_delete=models.CASCADE,
        related_name="jobs",
        verbose_name=_("Employer"),
        help_text=_("The employer posting this job")
    )

    location = models.CharField(
        max_length=100,
        verbose_name=_("Location"),
        blank=True,
        default="",
        help_text=_("Specific location or address")
    )
    district = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("District/City"),
        help_text=_("District or city name")
    )
    region = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Region"),
        help_text=_("Region or province")
    )
    
    # Work Type
    work_type = models.CharField(
        max_length=20,
        choices=WORK_TYPE_CHOICES,
        verbose_name=_("Work Type"),
        help_text=_("Type of work arrangement")
    )

    # Job Conditions
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name=_("Employment Type"),
        help_text=_("Type of employment contract")
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        verbose_name=_("Experience Level"),
        help_text=_("Required experience level")
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name=_("Education Level"),
        help_text=_("Required education level")
    )

    # Salary
    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Salary"),
        help_text=_("Minimum salary amount")
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary"),
        help_text=_("Maximum salary amount")
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="UZS",
        verbose_name=_("Currency"),
        help_text=_("Salary currency")
    )
    hide_salary = models.BooleanField(
        default=False,
        verbose_name=_("Hide Salary"),
        help_text=_("Hide salary information from public view")
    )
    salary_negotiable = models.BooleanField(
        default=False,
        verbose_name=_("Salary Negotiable"),
        help_text=_("Salary is open to negotiation")
    )
    
    # Additional Compensation
    bonus_system = models.BooleanField(
        default=False,
        verbose_name=_("Bonus System"),
        help_text=_("Company offers bonus system")
    )
    kpi_bonus = models.BooleanField(
        default=False,
        verbose_name=_("KPI Bonus"),
        help_text=_("Bonuses based on KPI performance")
    )
    performance_bonus = models.BooleanField(
        default=False,
        verbose_name=_("Performance Bonus"),
        help_text=_("Bonuses based on overall performance")
    )

    # Requirements
    requirements = models.TextField(
        verbose_name=_("Requirements"),
        help_text=_("Job requirements and qualifications")
    )
    responsibilities = models.TextField(
        verbose_name=_("Responsibilities"),
        help_text=_("Job duties and responsibilities")
    )
    benefits = models.TextField(
        blank=True,
        verbose_name=_("Benefits"),
        help_text=_("Employee benefits and perks")
    )

    # Skills
    skills_required = models.TextField(
        verbose_name=_("Required Skills"),
        help_text=_("List required skills separated by commas")
    )
    preferred_skills = models.TextField(
        blank=True,
        verbose_name=_("Preferred Skills"),
        help_text=_("List preferred skills separated by commas")
    )

    # Language Requirements
    language_requirements = models.TextField(
        blank=True,
        verbose_name=_("Language Requirements"),
        help_text=_("Required language proficiency levels")
    )

    # Contact Information
    contact_email = models.EmailField(
        verbose_name=_("Contact Email"),
        help_text=_("Email for job applications")
    )
    contact_phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Contact Phone"),
        help_text=_("Phone number for inquiries")
    )
    contact_person = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Contact Person"),
        help_text=_("Name of the contact person")
    )
    application_url = models.URLField(
        blank=True,
        verbose_name=_("Application URL"),
        help_text=_("Direct link to apply")
    )

    # Work Process
    work_schedule = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Work Schedule"),
        help_text=_("Working hours and days")
    )
    probation_period = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Probation Period"),
        help_text=_("Duration of probation period")
    )

    # Status and Statistics
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Job is currently active")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Featured"),
        help_text=_("Highlight this job in listings")
    )
    is_urgent = models.BooleanField(
        default=False,
        verbose_name=_("Urgent"),
        help_text=_("Mark as urgent hiring")
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name=_("Premium"),
        help_text=_("Premium job listing")
    )

    views_count = models.IntegerField(
        default=0,
        verbose_name=_("Views Count"),
        help_text=_("Number of views")
    )
    applications_count = models.IntegerField(
        default=0,
        verbose_name=_("Applications Count"),
        help_text=_("Number of applications received")
    )
    favorites_count = models.IntegerField(
        default=0,
        verbose_name=_("Favorites Count"),
        help_text=_("Number of times saved as favorite")
    )

    # Dates
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At"),
        help_text=_("Job posting expiration date")
    )
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Created By"),
        related_name="jobs_created",
        help_text=_("User who created this job")
    )

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
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
            return _("Salary is negotiable")
        if self.salary_negotiable:
            return _("Negotiable")
        if self.salary_min and self.salary_max:
            return f"{self.salary_min:,.0f} - {self.salary_max:,.0f} {self.get_currency_display()}"
        elif self.salary_min:
            return _("from %(salary)s %(currency)s") % {
                "salary": f"{self.salary_min:,.0f}",
                "currency": self.get_currency_display(),
            }
        elif self.salary_max:
            return _("up to %(salary)s %(currency)s") % {
                "salary": f"{self.salary_max:,.0f}",
                "currency": self.get_currency_display(),
            }
        return _("Not specified")

    def days_since_posted(self):
        from django.utils import timezone
        return (timezone.now() - self.created_at).days

    def work_type_display(self):
        types = []
        if self.work_type == "remote":
            types.append(_("Remote work"))
        elif self.work_type == "hybrid":
            types.append(_("Hybrid"))
        elif self.work_type == "office":
            types.append(_("Office"))
        return ", ".join(types) if types else _("Not specified")

    def location_display(self):
        if self.district:
            return f"{self.region}, {self.district}"
        return self.region

    def short_requirements(self):
        if len(self.requirements) > 150:
            return self.requirements[:150] + "..."
        return self.requirements


class JobApplication(models.Model):
    """Stores job application information from candidates"""

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
        help_text=_("The job being applied for")
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("Candidate"),
        help_text=_("The user applying for the job")
    )

    # Resume and Cover Letter
    cv = models.ForeignKey(
        "cvbuilder.CV",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Resume"),
        help_text=_("Candidate's resume/CV")
    )
    cover_letter = models.TextField(
        verbose_name=_("Cover Letter"),
        help_text=_("Candidate's cover letter explaining their interest")
    )

    # Expectations
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Expected Salary"),
        help_text=_("Candidate's expected salary")
    )
    notice_period = models.IntegerField(
        default=0,
        verbose_name=_("Notice Period"),
        help_text=_("Days required for notice period")
    )
    available_from = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Available From"),
        help_text=_("Date when candidate can start work")
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied",
        verbose_name=_("Status"),
        help_text=_("Current application status")
    )
    status_changed_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Status Changed"),
        help_text=_("When status was last updated")
    )

    # Additional Information
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Read by Employer"),
        help_text=_("Whether employer has read this application")
    )
    source = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Application Source"),
        help_text=_("How the candidate found this job")
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
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        unique_together = ["job", "candidate"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application from {self.candidate.username} for {self.job.title}"


class SavedJob(models.Model):
    """Stores user's saved job bookmarks"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_jobs",
        verbose_name=_("User"),
        help_text=_("User who saved the job")
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="saved_by",
        verbose_name=_("Job"),
        help_text=_("The saved job")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Saved At"),
        help_text=_("When the job was saved")
    )

    class Meta:
        verbose_name = _("Saved Job")
        verbose_name_plural = _("Saved Jobs")
        unique_together = ["user", "job"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"


class JobAlert(models.Model):
    """Stores job alert subscriptions for email notifications"""

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
        help_text=_("User who created the alert")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Alert Name"),
        help_text=_("Name for this job alert")
    )

    # Search Parameters
    keywords = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Keywords"),
        help_text=_("Keywords to search for in jobs")
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Location"),
        help_text=_("Preferred job location")
    )
    industry = models.ForeignKey(
        Industry,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Industry"),
        help_text=_("Preferred industry")
    )
    employment_type = models.CharField(
        max_length=20,
        choices=Job.EMPLOYMENT_TYPE_CHOICES,
        blank=True,
        verbose_name=_("Employment Type"),
        help_text=_("Preferred employment type")
    )
    experience_level = models.CharField(
        max_length=20,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        blank=True,
        verbose_name=_("Experience Level"),
        help_text=_("Preferred experience level")
    )

    # Settings
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this alert is active")
    )
    frequency = models.CharField(
        max_length=10,
        choices=FREQUENCY_CHOICES,
        default="daily",
        verbose_name=_("Frequency"),
        help_text=_("How often to send notifications")
    )
    last_sent = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Sent"),
        help_text=_("When the last notification was sent")
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
        verbose_name = _("Job Alert")
        verbose_name_plural = _("Job Alerts")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} - {self.user.username}"