from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver

User = get_user_model()


class Company(models.Model):
    """Company model for alumni employment information"""

    INDUSTRY_CHOICES = [
        ("it", _("IT and Technology")),
        ("finance", _("Finance and Banking")),
        ("education", _("Education")),
        ("healthcare", _("Healthcare")),
        ("manufacturing", _("Manufacturing")),
        ("retail", _("Retail")),
        ("energy", _("Energy")),
        ("telecom", _("Telecommunications")),
        ("consulting", _("Consulting")),
        ("other", _("Other")),
    ]

    name = models.CharField(
        max_length=255,
        verbose_name=_("Company Name"),
        help_text=_("Official company name")
    )
    industry = models.CharField(
        max_length=100,
        choices=INDUSTRY_CHOICES,
        verbose_name=_("Industry"),
        help_text=_("Primary industry sector")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Company description and overview")
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Official company website")
    )
    logo = models.ImageField(
        upload_to="company_logos/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Logo"),
        help_text=_("Company logo image")
    )
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Primary company email")
    )
    phone = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone"),
        help_text=_("Company phone number")
    )
    address = models.TextField(
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Company address")
    )
    employees_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Employees Count"),
        help_text=_("Number of employees")
    )
    founded_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Founded Year"),
        help_text=_("Year the company was founded")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Whether the company is verified")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether the company is active")
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
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ["name"]

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Skill model for alumni professional competencies"""

    CATEGORY_CHOICES = [
        ("technical", _("Technical Skills")),
        ("soft", _("Soft Skills")),
        ("language", _("Language Skills")),
        ("professional", _("Professional Skills")),
    ]

    name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name"),
        help_text=_("Name of the skill or competency")
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        verbose_name=_("Category"),
        help_text=_("Category of the skill")
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Detailed description of the skill")
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier")
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["category", "name"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Alumni(models.Model):
    FACULTY_CHOICES = [
        ("engineering", _("Software Engineering")),
        ("economics", _("Economics")),
        ("management", _("Management")),
        ("law", _("Law")),
        ("philology", _("Philology")),
        ("foreign_languages", _("Foreign Languages")),
        ("journalism", _("Journalism")),
        ("international_relations", _("International Relations")),
    ]

    DEGREE_CHOICES = [
        ("bachelor", _("Bachelor")),
        ("master", _("Master")),
        ("phd", _("PhD")),
        ("doctorate", _("Doctorate")),
    ]

    # Basic Information
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )
    name = models.CharField(
        max_length=255,
        verbose_name=_("Full Name"),
        help_text=_("Alumni's full name")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier")
    )

    # Education Information
    graduation_year = models.IntegerField(
        verbose_name=_("Graduation Year"),
        help_text=_("Year of graduation (YYYY format)")
    )
    faculty = models.CharField(
        max_length=100,
        choices=FACULTY_CHOICES,
        verbose_name=_("Faculty"),
        help_text=_("Academic faculty or department")
    )
    degree = models.CharField(
        max_length=50,
        choices=DEGREE_CHOICES,
        default="bachelor",
        verbose_name=_("Degree"),
        help_text=_("Academic degree obtained")
    )
    specialization = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Specialization"),
        help_text=_("Field of specialization")
    )

    # Professional Information
    current_position = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Current Position"),
        help_text=_("Current job title or position")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Company"),
        help_text=_("Current or most recent employer")
    )
    profession = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Profession"),
        help_text=_("Professional field or occupation")
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Industry"),
        help_text=_("Industry sector")
    )

    # Contact Information
    email = models.EmailField(
        blank=True,
        verbose_name=_("Email"),
        help_text=_("Contact email address")
    )
    phone = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone"),
        help_text=_("Contact phone number")
    )
    linkedin = models.URLField(
        blank=True,
        verbose_name=_("LinkedIn"),
        help_text=_("LinkedIn profile URL")
    )
    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Personal or professional website")
    )

    # Location
    country = CountryField(
        blank=True,
        verbose_name=_("Country"),
        help_text=_("Country of residence")
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
        help_text=_("City of residence")
    )

    # Bio and Media
    bio = models.TextField(
        blank=True,
        verbose_name=_("Bio"),
        help_text=_("Professional biography or summary")
    )
    photo = models.ImageField(
        upload_to="alumni_photos/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Profile Photo"),
        help_text=_("Profile picture")
    )
    resume = models.FileField(
        upload_to="alumni_resumes/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Resume"),
        help_text=_("Resume or CV file")
    )

    # Status and Preferences
    is_mentor = models.BooleanField(
        default=False,
        verbose_name=_("Is Mentor"),
        help_text=_("Whether this alumni offers mentoring")
    )
    is_visible = models.BooleanField(
        default=True,
        verbose_name=_("Profile Visible"),
        help_text=_("Whether profile is publicly visible")
    )
    show_contact_info = models.BooleanField(
        default=False,
        verbose_name=_("Show Contact Info"),
        help_text=_("Whether to display contact information publicly")
    )

    # Skills
    skills = models.ManyToManyField(
        Skill,
        blank=True,
        verbose_name=_("Skills"),
        help_text=_("Professional skills and competencies")
    )
    expertise_areas = models.TextField(
        blank=True,
        help_text=_("Separate expertise areas with commas"),
        verbose_name=_("Expertise Areas")
    )

    # Career Information
    years_of_experience = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Years of Experience"),
        help_text=_("Total years of professional experience")
    )
    is_open_to_opportunities = models.BooleanField(
        default=False,
        verbose_name=_("Open to Opportunities"),
        help_text=_("Whether open to new career opportunities")
    )

    # Social Media
    telegram = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Telegram"),
        help_text=_("Telegram username or handle")
    )
    twitter = models.URLField(
        blank=True,
        verbose_name=_("Twitter"),
        help_text=_("Twitter profile URL")
    )
    facebook = models.URLField(
        blank=True,
        verbose_name=_("Facebook"),
        help_text=_("Facebook profile URL")
    )
    instagram = models.URLField(
        blank=True,
        verbose_name=_("Instagram"),
        help_text=_("Instagram profile URL")
    )
    github = models.URLField(
        blank=True,
        verbose_name=_("GitHub"),
        help_text=_("GitHub profile URL")
    )

    # Statistics
    profile_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Profile Views"),
        help_text=_("Number of profile views")
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Profile creation timestamp")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last profile update timestamp")
    )

    class Meta:
        verbose_name = _("Alumni")
        verbose_name_plural = _("Alumni")
        ordering = ["-graduation_year", "name"]
        indexes = [
            models.Index(fields=["graduation_year"]),
            models.Index(fields=["faculty"]),
            models.Index(fields=["is_mentor"]),
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
        return reverse("alumni:detail", kwargs={"slug": self.slug})

    @property
    def full_name(self):
        return self.name

    @property
    def skills_list(self):
        """Return skills as list"""
        return list(self.skills.values_list("name", flat=True))

    @property
    def expertise_list(self):
        """Return expertise areas as list"""
        if self.expertise_areas:
            return [area.strip() for area in self.expertise_areas.split(",")]
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
    """Model for networking connections between alumni"""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("accepted", _("Accepted")),
        ("rejected", _("Rejected")),
        ("blocked", _("Blocked")),
    ]

    from_user = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="sent_connections",
        verbose_name=_("From User"),
        help_text=_("User initiating the connection")
    )
    to_user = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="received_connections",
        verbose_name=_("To User"),
        help_text=_("User receiving the connection request")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
        help_text=_("Current status of the connection")
    )
    message = models.TextField(
        blank=True,
        verbose_name=_("Message"),
        help_text=_("Optional message with connection request")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the connection was initiated")
    )
    responded_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Responded At"),
        help_text=_("When the connection was responded to")
    )

    class Meta:
        verbose_name = _("Connection")
        verbose_name_plural = _("Connections")
        unique_together = ["from_user", "to_user"]

    def __str__(self):
        return f"{self.from_user.name} → {self.to_user.name}"


class Mentorship(models.Model):
    """Model for mentorship relationships between alumni"""

    STATUS_CHOICES = [
        ("pending", _("Pending")),
        ("active", _("Active")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    COMMUNICATION_CHOICES = [
        ("email", _("Email")),
        ("video_call", _("Video Call")),
        ("in_person", _("In Person")),
        ("phone", _("Phone")),
    ]

    mentor = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="mentor_relationships",
        verbose_name=_("Mentor"),
        help_text=_("Alumni acting as mentor")
    )
    mentee = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="mentee_relationships",
        verbose_name=_("Mentee"),
        help_text=_("Alumni seeking mentorship")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending",
        verbose_name=_("Status"),
        help_text=_("Current status of the mentorship")
    )
    message = models.TextField(
        blank=True,
        verbose_name=_("Message"),
        help_text=_("Initial message or request for mentorship")
    )
    expected_duration = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Expected Duration"),
        help_text=_("Expected duration of the mentorship program")
    )
    communication_preference = models.CharField(
        max_length=20,
        choices=COMMUNICATION_CHOICES,
        default="video_call",
        verbose_name=_("Communication Preference"),
        help_text=_("Preferred method of communication")
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Start Date"),
        help_text=_("When the mentorship began")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("When the mentorship ended")
    )

    # Feedback
    mentee_feedback = models.TextField(
        blank=True,
        verbose_name=_("Mentee Feedback"),
        help_text=_("Feedback from the mentee")
    )
    mentor_feedback = models.TextField(
        blank=True,
        verbose_name=_("Mentor Feedback"),
        help_text=_("Feedback from the mentor")
    )
    rating = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Rating (1-5)"),
        help_text=_("Overall rating of the mentorship experience")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the mentorship request was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the mentorship")
    )

    class Meta:
        verbose_name = _("Mentorship")
        verbose_name_plural = _("Mentorships")
        unique_together = ["mentor", "mentee"]

    def __str__(self):
        return f"{self.mentor.name} → {self.mentee.name}"


class Job(models.Model):
    """Model for job postings by alumni"""

    EMPLOYMENT_TYPES = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("contract", _("Contract")),
        ("internship", _("Internship")),
        ("remote", _("Remote")),
    ]

    CURRENCY_CHOICES = [
        ("USD", "USD"),
        ("EUR", "EUR"),
        ("UZS", "UZS"),
        ("RUB", "RUB"),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name=_("Job Title"),
        help_text=_("Position or job title")
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        verbose_name=_("Company"),
        help_text=_("Company offering the position")
    )
    posted_by = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Posted By"),
        help_text=_("Alumni who posted this job")
    )
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        verbose_name=_("Employment Type"),
        help_text=_("Type of employment offered")
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_("Location"),
        help_text=_("Job location or work location")
    )
    remote_work = models.BooleanField(
        default=False,
        verbose_name=_("Remote Work"),
        help_text=_("Whether remote work is allowed")
    )

    # Salary
    salary_min = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Minimum Salary"),
        help_text=_("Minimum salary offered")
    )
    salary_max = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Maximum Salary"),
        help_text=_("Maximum salary offered")
    )
    currency = models.CharField(
        max_length=3,
        choices=CURRENCY_CHOICES,
        default="USD",
        verbose_name=_("Currency"),
        help_text=_("Currency for salary figures")
    )

    # Description
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed job description")
    )
    requirements = models.TextField(
        verbose_name=_("Requirements"),
        help_text=_("Job requirements and qualifications")
    )
    benefits = models.TextField(
        blank=True,
        verbose_name=_("Benefits"),
        help_text=_("Job benefits and perks")
    )

    # Contact
    contact_email = models.EmailField(
        verbose_name=_("Contact Email"),
        help_text=_("Email for job applications")
    )
    application_url = models.URLField(
        blank=True,
        verbose_name=_("Application URL"),
        help_text=_("External URL for job applications")
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether the job posting is active")
    )
    expires_at = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expires At"),
        help_text=_("When the job posting expires")
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Views"),
        help_text=_("Number of times the job has been viewed")
    )

    # Applicants
    applicants = models.ManyToManyField(
        Alumni,
        through="JobApplication",
        related_name="applied_jobs",
        blank=True,
        verbose_name=_("Applicants"),
        help_text=_("Alumni who have applied for this job")
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

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} at {self.company.name}"


class JobApplication(models.Model):
    """Model for job applications submitted by alumni"""

    STATUS_CHOICES = [
        ("applied", _("Applied")),
        ("reviewed", _("Reviewed")),
        ("interview", _("Interview")),
        ("rejected", _("Rejected")),
        ("accepted", _("Accepted")),
    ]

    job = models.ForeignKey(
        Job,
        on_delete=models.CASCADE,
        verbose_name=_("Job"),
        help_text=_("Job being applied for")
    )
    applicant = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Applicant"),
        help_text=_("Alumni applying for the job")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="applied",
        verbose_name=_("Status"),
        help_text=_("Current status of the application")
    )
    cover_letter = models.TextField(
        blank=True,
        verbose_name=_("Cover Letter"),
        help_text=_("Applicant's cover letter")
    )
    resume = models.FileField(
        upload_to="job_applications/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Resume"),
        help_text=_("Applicant's resume file")
    )
    applied_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Applied At"),
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
        unique_together = ["job", "applicant"]

    def __str__(self):
        return f"{self.applicant.name} - {self.job.title}"


class Event(models.Model):
    """Model for alumni events and gatherings"""

    EVENT_TYPES = [
        ("networking", _("Networking")),
        ("workshop", _("Workshop")),
        ("conference", _("Conference")),
        ("seminar", _("Seminar")),
        ("career_fair", _("Career Fair")),
        ("reunion", _("Reunion")),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Event title or name")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Detailed event description")
    )
    event_type = models.CharField(
        max_length=50,
        choices=EVENT_TYPES,
        verbose_name=_("Event Type"),
        help_text=_("Type or category of the event")
    )
    date = models.DateField(
        verbose_name=_("Date"),
        help_text=_("Date when the event occurs")
    )
    time = models.TimeField(
        verbose_name=_("Time"),
        help_text=_("Time when the event starts")
    )
    location = models.CharField(
        max_length=255,
        verbose_name=_("Location"),
        help_text=_("Physical location of the event")
    )
    organizer = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Organizer"),
        help_text=_("Alumni organizing the event")
    )

    # Registration
    registration_required = models.BooleanField(
        default=False,
        verbose_name=_("Registration Required"),
        help_text=_("Whether registration is required to attend")
    )
    max_participants = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Max Participants"),
        help_text=_("Maximum number of participants allowed")
    )
    participants = models.ManyToManyField(
        Alumni,
        related_name="events",
        blank=True,
        verbose_name=_("Participants"),
        help_text=_("Alumni registered to attend the event")
    )

    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether the event is active and upcoming")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the event was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the event")
    )

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")
        ordering = ["-date"]

    def __str__(self):
        return self.title


class News(models.Model):
    """Model for alumni news and announcements"""

    CATEGORY_CHOICES = [
        ("alumni", _("Alumni News")),
        ("career", _("Career News")),
        ("education", _("Education News")),
        ("events", _("Events")),
        ("opportunities", _("Opportunities")),
    ]

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("News article title")
    )
    slug = models.SlugField(
        max_length=255,
        unique=True,
        blank=True,
        verbose_name=_("Slug"),
        help_text=_("URL-friendly identifier")
    )
    content = models.TextField(
        verbose_name=_("Content"),
        help_text=_("Full news article content")
    )
    author = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        verbose_name=_("Author"),
        help_text=_("Alumni who wrote the news article")
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default="alumni",
        verbose_name=_("Category"),
        help_text=_("News category or topic")
    )
    image = models.ImageField(
        upload_to="news_images/%Y/%m/%d/",
        blank=True,
        null=True,
        verbose_name=_("Image"),
        help_text=_("Featured image for the news article")
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for the article")
    )

    # Status
    is_published = models.BooleanField(
        default=True,
        verbose_name=_("Published"),
        help_text=_("Whether the news article is published")
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Views"),
        help_text=_("Number of times the article has been viewed")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the news article was created")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the news article")
    )

    class Meta:
        verbose_name = _("News")
        verbose_name_plural = _("News")
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Message(models.Model):
    """Model for internal messaging between alumni"""

    sender = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="sent_messages",
        verbose_name=_("Sender"),
        help_text=_("Alumni sending the message")
    )
    receiver = models.ForeignKey(
        Alumni,
        on_delete=models.CASCADE,
        related_name="received_messages",
        verbose_name=_("Receiver"),
        help_text=_("Alumni receiving the message")
    )
    subject = models.CharField(
        max_length=255,
        verbose_name=_("Subject"),
        help_text=_("Message subject line")
    )
    body = models.TextField(
        verbose_name=_("Body"),
        help_text=_("Message content")
    )
    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Read"),
        help_text=_("Whether the message has been read")
    )
    parent_message = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="replies",
        verbose_name=_("Parent Message"),
        help_text=_("Parent message for replies")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the message was sent")
    )

    class Meta:
        verbose_name = _("Message")
        verbose_name_plural = _("Messages")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.sender.name} to {self.receiver.name}: {self.subject}"


# Signal handlers


@receiver(post_save, sender=Alumni)
def create_mentor_profile(sender, instance, created, **kwargs):
    """Create mentor profile when alumni is marked as mentor"""
    if instance.is_mentor and not hasattr(instance, "mentor_profile"):
        # Resolve model dynamically to avoid import-time circular references
        from django.apps import apps

        MentorProfile = apps.get_model("alumni", "MentorProfile")
        if MentorProfile is not None:
            MentorProfile.objects.create(alumni=instance)


@receiver(post_save, sender=Alumni)
def update_user_profile(sender, instance, **kwargs):
    """Update user profile when alumni profile is updated"""
    if instance.user:
        # Sync basic information with user profile
        user = instance.user
        if not user.first_name and " " in instance.name:
            names = instance.name.split(" ", 1)
            user.first_name = names[0]
            if len(names) > 1:
                user.last_name = names[1]
            user.save()
