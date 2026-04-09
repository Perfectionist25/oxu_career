
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import uuid
from django.core.exceptions import ValidationError


from accounts.models import CustomUser

User = get_user_model()

REGIONS = [
    ("Tashkent", _("Tashkent")),
    ("Samarkand", _("Samarkand")),
    ("Bukhara", _("Bukhara")),
    ("Fergana", _("Fergana")),
    ("Andijan", _("Andijan")),
    ("Namangan", _("Namangan")),
    ("Khorezm", _("Khorezm")),
    ("Kashkadarya", _("Kashkadarya")),
    ("Surkhandarya", _("Surkhandarya")),
    ("Jizzakh", _("Jizzakh")),
    ("Sirdarya", _("Sirdarya")),
    ("Navoi", _("Navoi")),
    ("Gulistan", _("Gulistan")),
    ("Qarshi", _("Qarshi")),
    ("Urganch", _("Urganch")),
]

class CV(models.Model):
    """Model for user resumes and CVs - Uzbekistan standards"""

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("published", _("Published")),
        ("archived", _("Archived")),
    ]

    MARITAL_STATUS_CHOICES = [
        ("single", _("Single")),
        ("married", _("Married")),
        ("divorced", _("Divorced")),
        ("widowed", _("Widowed")),
    ]

    GENDER_CHOICES = [
        ("male", _("Male")),
        ("female", _("Female")),
    ]

    EMPLOYMENT_TYPE_CHOICES = [
        ("full_time", _("Full-time")),
        ("part_time", _("Part-time")),
        ("contract", _("Contract")),
        ("freelance", _("Freelance")),
        ("internship", _("Internship")),
        ("remote", _("Remote")),
    ]


    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("User"),
        help_text=_("User who owns this CV"),
        related_name="cvs"
    )


    cv_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_("CV ID")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Resume Title"),
        default=_("My Resume"),
        help_text=_("Title or name of the resume")
    )

    template = models.ForeignKey(
        "CVTemplate",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="cvs",
        verbose_name=_("Template"),
        help_text=_("Template used for rendering the CV"),
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
        help_text=_("Current status of the resume")
    )


    full_name = models.CharField(
        max_length=200,
        verbose_name=_("Full Name"),
        help_text=_("Complete name as it should appear on the resume")
    )


    photo = models.ImageField(
        upload_to='cv_photos/',
        null=True,
        blank=True,
        verbose_name=_("Photo"),
        help_text=_("Professional photo (recommended size: 3x4 cm)")
    )

    birth_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth"),
        help_text=_("Date of birth (DD.MM.YYYY)")
    )

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Gender")
    )

    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        null=True,
        blank=True,
        verbose_name=_("Marital Status")
    )

    nationality = models.CharField(
        max_length=100,
        default="Uzbekistan",
        verbose_name=_("Nationality"),
        help_text=_("Citizenship")
    )


    email = models.EmailField(
        verbose_name=_("Email Address"),
        help_text=_("Professional email address")
    )

    phone = models.CharField(
        max_length=20,
        verbose_name=_("Phone Number"),
        help_text=_("Contact phone number in format: +998 XX XXX XX XX")
    )

    phone_secondary = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        verbose_name=_("Secondary Phone"),
        help_text=_("Additional contact number")
    )

    region = models.CharField(
        choices=REGIONS,
        max_length=100,
        verbose_name=_("Region"),
        help_text=_("Region of Uzbekistan (e.g., Tashkent, Samarkand)")
    )

    city = models.CharField(
        max_length=100,
        verbose_name=_("City"),
        help_text=_("City of residence")
    )

    address = models.TextField(
        verbose_name=_("Full Address"),
        help_text=_("Complete residential address")
    )


    desired_position = models.CharField(
        max_length=200,
        verbose_name=_("Desired Position"),
        help_text=_("Position you are applying for")
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPE_CHOICES,
        default="full_time",
        verbose_name=_("Employment Type")
    )

    salary_expectation = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Salary Expectation"),
        help_text=_("Expected salary in UZS")
    )

    salary_currency = models.CharField(
        max_length=3,
        default="UZS",
        verbose_name=_("Currency"),
        help_text=_("Currency code (UZS, USD, EUR)")
    )


    summary = models.TextField(
        verbose_name=_("Professional Summary"),
        help_text=_("Brief professional summary and career objectives")
    )


























    driver_license = models.BooleanField(
        default=False,
        verbose_name=_("Driver's License"),
        help_text=_("Do you have a driver's license?")
    )

    driver_license_category = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("License Category"),
        help_text=_("Driver's license category (e.g., B, C)")
    )

    military_service = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Military Service"),
        help_text=_("Information about military service (for male candidates)")
    )


    linkedin = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("LinkedIn Profile")
    )

    github = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("GitHub Profile")
    )

    portfolio = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Portfolio Website")
    )


    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the CV was created")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
        help_text=_("Last update to the CV")
    )

    published_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Published Date")
    )

    class Meta:
        verbose_name = _("Resume")
        verbose_name_plural = _("Resumes")
        ordering = ["-updated_at", "-created_at"]
        indexes = [
            models.Index(fields=['status', 'user']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.full_name} - {self.desired_position} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse("cvbuilder:cv_detail", kwargs={"pk": self.pk})

    @property
    def location(self):
        """Возвращает объединенный адрес для удобства"""
        if self.city and self.region:
            return f"{self.city}, {self.region}"
        elif self.city:
            return self.city
        elif self.region:
            return self.region
        return ""

    @property
    def full_phone(self):
        """Format phone number for Uzbekistan"""
        if self.phone.startswith('+998'):
            return self.phone
        return f"+998{self.phone.lstrip('0')}"

    @property
    def age(self):
        """Calculate age from birth date"""
        if self.birth_date:
            from datetime import date
            today = date.today()
            return today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        return None


class Experience(models.Model):
    """Work experience model for CVs"""

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="experiences",
        verbose_name=_("CV"),
        help_text=_("CV this experience belongs to")
    )

    company = models.CharField(
        max_length=200,
        verbose_name=_("Company/Organization"),
        help_text=_("Name of the company or organization")
    )

    position = models.CharField(
        max_length=200,
        verbose_name=_("Position"),
        help_text=_("Job title or position held")
    )

    employment_type = models.CharField(
        max_length=20,
        choices=CV.EMPLOYMENT_TYPE_CHOICES,
        default="full_time",
        verbose_name=_("Employment Type")
    )

    start_date = models.DateField(
        verbose_name=_("Start Date"),
        help_text=_("When you started this position")
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("When you left this position")
    )

    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Current Position"),
        help_text=_("Check if this is your current job")
    )

    company_location = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Location"),
        help_text=_("City and country of the company")
    )

    description = models.TextField(
        verbose_name=_("Responsibilities and Achievements"),
        help_text=_("Key responsibilities, achievements, and skills used")
    )

    technologies = models.CharField(
        max_length=300,
        null=True,
        blank=True,
        verbose_name=_("Technologies Used"),
        help_text=_("Technologies, tools, and methodologies used")
    )

    achievements = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Key Achievements"),
        help_text=_("Specific achievements with measurable results")
    )

    class Meta:
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")
        ordering = ["-start_date"]
        indexes = [
            models.Index(fields=['cv', 'start_date']),
        ]

    def __str__(self):
        return f"{self.position} at {self.company}"

    @property
    def duration(self):
        """Calculate duration of employment"""
        from datetime import date
        end = self.end_date or date.today()
        delta = end - self.start_date
        years = delta.days // 365
        months = (delta.days % 365) // 30
        return f"{years}y {months}m" if years > 0 else f"{months}m"


class Education(models.Model):
    """Education entries linked to a CV"""

    EDUCATION_LEVEL_CHOICES = [
        ("secondary", _("Secondary Education")),
        ("specialized_secondary", _("Specialized Secondary")),
        ("incomplete_higher", _("Incomplete Higher")),
        ("bachelor", _("Bachelor's Degree")),
        ("master", _("Master's Degree")),
        ("phd", _("PhD/Doctorate")),
        ("professional", _("Professional Training")),
    ]

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="educations",
        verbose_name=_("CV")
    )

    institution = models.CharField(
        max_length=255,
        verbose_name=_("Educational Institution"),
        help_text=_("Name of university, college, or school")
    )

    degree = models.CharField(
        max_length=100,
        verbose_name=_("Degree/Diploma"),
        help_text=_("Name of the degree or diploma")
    )

    education_level = models.CharField(
        max_length=50,
        choices=EDUCATION_LEVEL_CHOICES,
        verbose_name=_("Education Level"),
        help_text=_("Level of education")
    )

    field_of_study = models.CharField(
        max_length=100,
        verbose_name=_("Field of Study/Specialty"),
        help_text=_("Your major or specialty")
    )

    faculty = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name=_("Faculty"),
        help_text=_("Faculty or department")
    )

    start_year = models.IntegerField(
        verbose_name=_("Start Year"),
        help_text=_("Year when studies began")
    )

    graduation_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Graduation Year"),
        help_text=_("Year of graduation")
    )

    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("GPA"),
        help_text=_("Grade Point Average")
    )

    honors = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Honors"),
        help_text=_("Honors, awards, or distinctions")
    )

    diploma_number = models.CharField(
        max_length=50,
        null=True,
        blank=True,
        verbose_name=_("Diploma Number"),
        help_text=_("Diploma or certificate number")
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Additional Information"),
        help_text=_("Projects, thesis, or additional information")
    )

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Education")
        ordering = ["-graduation_year", "-start_year"]

    def __str__(self):
        return f"{self.degree} in {self.field_of_study} at {self.institution}"


class Certificate(models.Model):
    """Certificates, diplomas, and professional certifications"""

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
        verbose_name=_("CV")
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Certificate Name"),
        help_text=_("Name of certificate or certification")
    )

    issuing_organization = models.CharField(
        max_length=200,
        verbose_name=_("Issuing Organization"),
        help_text=_("Organization that issued the certificate")
    )

    issue_date = models.DateField(
        verbose_name=_("Issue Date"),
        help_text=_("Date when certificate was issued")
    )

    expiration_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Expiration Date"),
        help_text=_("Date when certificate expires (if applicable)")
    )

    certificate_id = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name=_("Certificate ID"),
        help_text=_("Certificate identification number")
    )

    certificate_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Verification URL"),
        help_text=_("Link to verify certificate online")
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Skills or knowledge acquired")
    )


    certificate_file = models.FileField(
        upload_to='certificates/',
        null=True,
        blank=True,
        verbose_name=_("Certificate File"),
        help_text=_("Upload scanned certificate (PDF, JPG, PNG)")
    )

    class Meta:
        verbose_name = _("Certificate")
        verbose_name_plural = _("Certificates")
        ordering = ["-issue_date"]

    def __str__(self):
        return f"{self.name} - {self.issuing_organization}"

    @property
    def is_expired(self):
        """Check if certificate is expired"""
        if self.expiration_date:
            from datetime import date
            return date.today() > self.expiration_date
        return False


class Skill(models.Model):
    """Skill entries linked to a CV"""

    SKILL_LEVEL_CHOICES = [
        ("beginner", _("Beginner")),
        ("intermediate", _("Intermediate")),
        ("advanced", _("Advanced")),
        ("expert", _("Expert")),
    ]

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="skills",
        verbose_name=_("CV")
    )

    name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name"),
        help_text=_("Name of the skill")
    )

    category = models.CharField(
        max_length=50,
        default="general",
        verbose_name=_("Category"),
        help_text=_("Skill category (e.g., technical, soft, language)")
    )

    level = models.CharField(
        max_length=20,
        choices=SKILL_LEVEL_CHOICES,
        verbose_name=_("Proficiency Level"),
        help_text=_("Your proficiency level in this skill")
    )

    years_of_experience = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Years of Experience"),
        help_text=_("Number of years using this skill")
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Examples of how you used this skill")
    )

    last_used = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Last Used"),
        help_text=_("Year when you last used this skill professionally")
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        ordering = ["category", "-years_of_experience"]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Language(models.Model):
    """Languages model for CVs"""

    LANGUAGE_LEVELS = [
        ("a1", _("A1 - Beginner")),
        ("a2", _("A2 - Elementary")),
        ("b1", _("B1 - Intermediate")),
        ("b2", _("B2 - Upper Intermediate")),
        ("c1", _("C1 - Advanced")),
        ("c2", _("C2 - Proficient")),
        ("native", _("Native")),
    ]

    LANGUAGE_CERTIFICATES = [
        ("ielts", _("IELTS")),
        ("toefl", _("TOEFL")),
        ("cefr", _("CEFR Certificate")),
        ("none", _("No Certificate")),
    ]

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="languages",
        verbose_name=_("CV"),
        help_text=_("CV this language belongs to")
    )

    name = models.CharField(
        max_length=50,
        verbose_name=_("Language"),
        help_text=_("Name of the language")
    )

    level = models.CharField(
        max_length=20,
        choices=LANGUAGE_LEVELS,
        verbose_name=_("Proficiency Level"),
        help_text=_("Your level of proficiency in this language")
    )

    certificate_type = models.CharField(
        max_length=20,
        choices=LANGUAGE_CERTIFICATES,
        default="none",
        verbose_name=_("Certificate Type"),
        help_text=_("Language proficiency certificate")
    )

    certificate_score = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name=_("Certificate Score"),
        help_text=_("Test score (e.g., IELTS 7.5, TOEFL 100)")
    )

    is_native = models.BooleanField(
        default=False,
        verbose_name=_("Native Language"),
        help_text=_("Is this your native language?")
    )

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ["-is_native", "level"]

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"


class Project(models.Model):
    """Personal or professional projects"""

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="projects",
        verbose_name=_("CV")
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Project Name"),
        help_text=_("Name of the project")
    )

    role = models.CharField(
        max_length=100,
        verbose_name=_("Your Role"),
        help_text=_("Your role in the project")
    )

    description = models.TextField(
        verbose_name=_("Project Description"),
        help_text=_("Brief description of the project")
    )

    technologies = models.CharField(
        max_length=300,
        verbose_name=_("Technologies Used"),
        help_text=_("Technologies and tools used in the project")
    )

    start_date = models.DateField(
        verbose_name=_("Start Date")
    )

    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date")
    )

    project_url = models.URLField(
        null=True,
        blank=True,
        verbose_name=_("Project URL"),
        help_text=_("Link to live project or repository")
    )

    is_personal = models.BooleanField(
        default=False,
        verbose_name=_("Personal Project"),
        help_text=_("Is this a personal project?")
    )

    class Meta:
        verbose_name = _("Project")
        verbose_name_plural = _("Projects")
        ordering = ["-start_date"]

    def __str__(self):
        return self.name


class Reference(models.Model):
    """Professional references"""

    cv = models.ForeignKey(
        CV,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="references",
        verbose_name=_("CV")
    )

    name = models.CharField(
        max_length=200,
        verbose_name=_("Reference Name"),
        help_text=_("Full name of the reference")
    )

    position = models.CharField(
        max_length=200,
        verbose_name=_("Position"),
        help_text=_("Position of the reference")
    )

    company = models.CharField(
        max_length=200,
        verbose_name=_("Company"),
        help_text=_("Company where reference works")
    )

    email = models.EmailField(
        verbose_name=_("Email"),
        help_text=_("Email address of the reference")
    )

    phone = models.CharField(
        max_length=20,
        verbose_name=_("Phone"),
        help_text=_("Phone number of the reference")
    )

    relationship = models.CharField(
        max_length=100,
        verbose_name=_("Relationship"),
        help_text=_("Your relationship with the reference")
    )

    class Meta:
        verbose_name = _("Reference")
        verbose_name_plural = _("References")

    def __str__(self):
        return f"{self.name} - {self.position} at {self.company}"


class CVTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [
        ("classic", _("Classic")),
        ("modern", _("Modern")),
        ("creative", _("Creative")),
        ("minimalist", _("Minimalist")),
        ("executive", _("Executive")),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name=_("Template Name")
    )

    template_type = models.CharField(
        max_length=20,
        choices=TEMPLATE_TYPE_CHOICES,
        default="classic",
        verbose_name=_("Template Type")
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Template description and features")
    )

    thumbnail = models.ImageField(
        upload_to='cv_templates/thumbnails/',
        null=True,
        blank=True,
        verbose_name=_("Thumbnail")
    )

    template_file = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("Template File"),
        help_text=_("Path to template file")
    )

    css_file = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_("CSS File"),
        help_text=_("Path to CSS file for styling")
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active")
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
        verbose_name = _("CV Template")
        verbose_name_plural = _("CV Templates")
        ordering = ["-is_active", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_template_type_display()})"

    def clean(self):

        if self.template_file and (".." in self.template_file or self.template_file.startswith("/")):
            raise ValidationError("Invalid template_file path")

    def save(self, *args, **kwargs):

        if not self.template_file:
            self.template_file = f"cv_render/{self.template_type}.html"
        if not self.css_file:
            self.css_file = f"cv_css/{self.template_type}.css"
        super().save(*args, **kwargs)