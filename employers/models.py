from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class Company(models.Model):
    """Компания работодателя"""

    COMPANY_SIZE_CHOICES = [
        ("1-10", _("1-10 employees")),
        ("11-50", _("11-50 employees")),
        ("51-200", _("51-200 employees")),
        ("201-500", _("201-500 employees")),
        ("501-1000", _("501-1000 employees")),
        ("1000+", _("More than 1000 employees")),
    ]

    INDUSTRY_CHOICES = [
        ("it", _("IT & Technology")),
        ("finance", _("Finance & Banking")),
        ("healthcare", _("Healthcare")),
        ("education", _("Education")),
        ("manufacturing", _("Manufacturing")),
        ("retail", _("Retail")),
        ("consulting", _("Consulting")),
        ("tourism", _("Tourism & Hospitality")),
        ("construction", _("Construction")),
        ("energy", _("Energy")),
        ("telecom", _("Telecommunications")),
        ("other", _("Other")),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_("Company Name"),
        help_text=_("Official company name")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Brief description of the company and its activities")
    )
    website = models.URLField(
        verbose_name=_("Website"),
        help_text=_("Company website URL")
    )
    logo = models.ImageField(
        upload_to="company_logos/",
        null=True,
        blank=True,
        verbose_name=_("Logo"),
        help_text=_("Company logo image")
    )
    industry = models.CharField(
        max_length=50,
        choices=INDUSTRY_CHOICES,
        verbose_name=_("Industry"),
        help_text=_("Primary industry sector")
    )
    company_size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        verbose_name=_("Company Size"),
        help_text=_("Number of employees")
    )
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Founded Year"),
        help_text=_("Year the company was founded")
    )
    headquarters = models.CharField(
        max_length=100,
        verbose_name=_("Headquarters"),
        help_text=_("e.g., Tashkent, Uzbekistan"),
    )

    # Contact Information
    contact_email = models.EmailField(
        verbose_name=_("Contact Email"),
        help_text=_("Primary contact email address")
    )
    contact_phone = models.CharField(
        max_length=20,
        verbose_name=_("Contact Phone"),
        help_text=_("Primary contact phone number")
    )

    # Social Media
    linkedin = models.URLField(
        blank=True,
        verbose_name=_("LinkedIn"),
        help_text=_("Company LinkedIn profile URL")
    )
    twitter = models.URLField(
        blank=True,
        verbose_name=_("Twitter"),
        help_text=_("Company Twitter profile URL")
    )
    facebook = models.URLField(
        blank=True,
        verbose_name=_("Facebook"),
        help_text=_("Company Facebook page URL")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Company"),
        help_text=_("Whether the company profile has been verified")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether the company profile is active")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the company profile was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the company profile")
    )

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("employers:company_detail", kwargs={"pk": self.pk})

    def job_count(self):
        return self.jobs.filter(is_active=True).count()

    def active_jobs(self):
        return self.jobs.filter(is_active=True)


class EmployerProfile(models.Model):
    """Employer profile model linking users to companies"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User account associated with this employer profile")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="employers",
        verbose_name=_("Company"),
        help_text=_("Company this employer represents")
    )
    position = models.CharField(
        max_length=100,
        verbose_name=_("Position"),
        help_text=_("Job title or position within the company")
    )
    department = models.CharField(
        max_length=100,
        verbose_name=_("Department"),
        help_text=_("Department or team within the company")
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_("Phone"),
        help_text=_("Direct contact phone number")
    )

    # Access Rights
    can_post_jobs = models.BooleanField(
        default=False,
        verbose_name=_("Can Post Jobs"),
        help_text=_("Permission to create new job postings")
    )
    can_manage_jobs = models.BooleanField(
        default=False,
        verbose_name=_("Can Manage Jobs"),
        help_text=_("Permission to edit and manage job postings")
    )
    can_view_candidates = models.BooleanField(
        default=False,
        verbose_name=_("Can View Candidates"),
        help_text=_("Permission to view applicant information")
    )
    can_contact_candidates = models.BooleanField(
        default=False,
        verbose_name=_("Can Contact Candidates"),
        help_text=_("Permission to contact applicants directly")
    )

    is_primary_contact = models.BooleanField(
        default=False,
        verbose_name=_("Primary Contact"),
        help_text=_("Main contact person for the company")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Profile"),
        help_text=_("Whether this employer profile is active")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the employer profile was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the employer profile")
    )

    class Meta:
        verbose_name = _("Employer Profile")
        verbose_name_plural = _("Employer Profiles")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"


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

    CURRENCY_CHOICES = [
        ("UZS", _("Uzbek Sum (UZS)")),
        ("USD", _("US Dollar (USD)")),
        ("EUR", _("Euro (EUR)")),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="jobs",
        verbose_name=_("Company"),
        help_text=_("Company posting this job")
    )
    posted_by = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        verbose_name=_("Posted By"),
        help_text=_("Employer who posted this job")
    )

    title = models.CharField(
        max_length=200,
        verbose_name=_("Job Title"),
        help_text=_("Position title for this job posting")
    )
    description = models.TextField(
        verbose_name=_("Job Description"),
        help_text=_("Detailed description of the job and company")
    )
    requirements = models.TextField(
        verbose_name=_("Requirements"),
        help_text=_("Skills, experience, and qualifications required")
    )
    responsibilities = models.TextField(
        verbose_name=_("Responsibilities"),
        help_text=_("Key responsibilities and duties")
    )
    benefits = models.TextField(
        blank=True,
        verbose_name=_("Benefits"),
        help_text=_("Benefits and perks offered (optional)")
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        verbose_name=_("Employment Type"),
        help_text=_("Type of employment (full-time, part-time, etc.)")
    )
    experience_level = models.CharField(
        max_length=20,
        choices=EXPERIENCE_LEVEL_CHOICES,
        verbose_name=_("Experience Level"),
        help_text=_("Required experience level")
    )

    location = models.CharField(
        max_length=100,
        verbose_name=_("Location"),
        help_text=_("e.g., Tashkent, Samarkand, Remote"),
    )
    remote_work = models.BooleanField(
        default=False,
        verbose_name=_("Remote Work Available"),
        help_text=_("Whether remote work is an option")
    )

    salary_min = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Salary"),
        help_text=_("Minimum salary offered")
    )
    salary_max = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary"),
        help_text=_("Maximum salary offered")
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="UZS",
        verbose_name=_("Currency"),
        help_text=_("Currency for salary information")
    )
    hide_salary = models.BooleanField(
        default=False,
        verbose_name=_("Hide Salary"),
        help_text=_("Whether to hide salary information from public view")
    )

    application_url = models.URLField(
        blank=True,
        verbose_name=_("Application URL"),
        help_text=_("External URL for job applications (optional)")
    )
    contact_email = models.EmailField(
        verbose_name=_("Contact Email"),
        help_text=_("Email address for job inquiries")
    )

    skills_required = models.TextField(
        verbose_name=_("Required Skills"),
        help_text=_("Skills required for this position")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Job"),
        help_text=_("Whether this job posting is active")
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_("Featured Job"),
        help_text=_("Whether this job is featured/promoted")
    )
    views_count = models.IntegerField(
        default=0,
        verbose_name=_("View Count"),
        help_text=_("Number of times this job has been viewed")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the job was posted")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the job posting")
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At"),
        help_text=_("When this job posting expires")
    )

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_absolute_url(self):
        return reverse("employers:job_detail", kwargs={"pk": self.pk})

    def application_count(self):
        return self.applications.count()

    def is_expired(self):
        from django.utils import timezone

        if self.expires_at:
            return timezone.now() > self.expires_at
        return False

    def salary_range(self):
        if self.hide_salary:
            return _("Salary negotiable")
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


class JobApplication(models.Model):
    """Job application model for tracking candidate applications"""

    STATUS_CHOICES = [
        ("new", _("New")),
        ("reviewed", _("Reviewed")),
        ("interview", _("Interview")),
        ("rejected", _("Rejected")),
        ("hired", _("Hired")),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        related_name="applications",
        verbose_name=_("Job"),
        help_text=_("Job position being applied for")
    )
    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employer_applications",
        verbose_name=_("Candidate"),
        help_text=_("User applying for the job")
    )
    cv = models.ForeignKey(
        "cvbuilder.CV",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employer_applications",
        verbose_name=_("Resume"),
        help_text=_("CV submitted with the application")
    )

    cover_letter = models.TextField(
        verbose_name=_("Cover Letter"),
        help_text=_("Candidate's cover letter or motivation")
    )
    expected_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Expected Salary"),
        help_text=_("Candidate's expected salary")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="new",
        verbose_name=_("Status"),
        help_text=_("Current status of the application")
    )
    status_changed_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Status Changed"),
        help_text=_("When the status was last changed")
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Read"),
        help_text=_("Whether the application has been read by employer")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the application was submitted")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the application")
    )

    class Meta:
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        unique_together = ["job", "candidate"]
        ordering = ["-created_at"]

    def __str__(self):
        return f"Application from {self.candidate.username} for {self.job.title}"


class CandidateNote(models.Model):
    """Employer notes about candidates"""

    candidate = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employer_notes",
        verbose_name=_("Candidate"),
        help_text=_("Candidate this note is about")
    )
    employer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        verbose_name=_("Employer"),
        help_text=_("Employer who wrote this note")
    )
    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("Job"),
        help_text=_("Job application this note relates to (optional)")
    )

    note = models.TextField(
        verbose_name=_("Note"),
        help_text=_("Content of the note about the candidate")
    )
    is_private = models.BooleanField(
        default=True,
        verbose_name=_("Private Note"),
        help_text=_("Whether this note is private to the employer")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the note was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the note")
    )

    class Meta:
        verbose_name = _("Candidate Note")
        verbose_name_plural = _("Candidate Notes")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Note about {self.candidate.username}"


class Interview(models.Model):
    """Interview scheduling and tracking model"""

    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
        ("no_show", _("No Show")),
    ]

    application = models.ForeignKey(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="interviews",
        verbose_name=_("Application"),
        help_text=_("Job application this interview is for")
    )
    interviewer = models.ForeignKey(
        EmployerProfile,
        on_delete=models.CASCADE,
        verbose_name=_("Interviewer"),
        help_text=_("Employer conducting the interview")
    )

    scheduled_date = models.DateTimeField(
        verbose_name=_("Scheduled Date"),
        help_text=_("Date and time when the interview is scheduled")
    )
    duration = models.IntegerField(
        verbose_name=_("Duration"),
        help_text=_("Expected duration of the interview in minutes")
    )
    location = models.TextField(
        verbose_name=_("Location"),
        help_text=_("Interview location or meeting details")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about the interview")
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
        verbose_name=_("Status"),
        help_text=_("Current status of the interview")
    )
    feedback = models.TextField(
        blank=True,
        verbose_name=_("Feedback"),
        help_text=_("Interview feedback and evaluation")
    )
    rating = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating"),
        help_text=_("Overall rating of the candidate")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the interview was scheduled")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the interview record")
    )

    class Meta:
        verbose_name = _("Interview")
        verbose_name_plural = _("Interviews")
        ordering = ["scheduled_date"]

    def __str__(self):
        return f"Interview for {self.application.candidate.username}"


class CompanyReview(models.Model):
    """Company review and rating model"""

    RATING_CHOICES = [
        (1, _("1 - Very Poor")),
        (2, _("2 - Poor")),
        (3, _("3 - Average")),
        (4, _("4 - Good")),
        (5, _("5 - Excellent")),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name=_("Company"),
        help_text=_("Company being reviewed")
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="employer_reviews",
        verbose_name=_("Author"),
        help_text=_("User who wrote the review")
    )

    rating = models.IntegerField(
        choices=RATING_CHOICES,
        verbose_name=_("Rating"),
        help_text=_("Overall rating from 1 to 5")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        help_text=_("Review title or headline")
    )
    review = models.TextField(
        verbose_name=_("Review"),
        help_text=_("Detailed review content")
    )

    pros = models.TextField(
        verbose_name=_("Pros"),
        help_text=_("Positive aspects of the company")
    )
    cons = models.TextField(
        verbose_name=_("Cons"),
        help_text=_("Negative aspects of the company")
    )

    is_anonymous = models.BooleanField(
        default=False,
        verbose_name=_("Anonymous Review"),
        help_text=_("Whether the review is posted anonymously")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Review"),
        help_text=_("Whether the reviewer is verified (e.g., former employee)")
    )
    is_published = models.BooleanField(
        default=False,
        verbose_name=_("Published"),
        help_text=_("Whether the review is published and visible")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the review was submitted")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the review")
    )

    class Meta:
        verbose_name = _("Company Review")
        verbose_name_plural = _("Company Reviews")
        ordering = ["-created_at"]
        unique_together = ["company", "author"]

    def __str__(self):
        return f"Review by {self.author.username} for {self.company.name}"
