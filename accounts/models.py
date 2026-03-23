
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
import requests
import io
import uuid
from PIL import Image, ImageOps
from django.core.files.base import ContentFile

from .certificates import (
    CERTIFICATE_IMAGE_EXTENSIONS,
    StudentCertificateStorage,
    get_certificate_content_type,
    student_certificate_upload_to,
    validate_student_certificate_file,
)

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

CITIES = [
    ("Other", _("Other")),
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

ADMIN_USER_TYPES = ("admin", "international_admin", "main_admin")

class CustomUser(AbstractUser):
    """Custom user model with different roles and extended profile information"""

    USER_TYPE_CHOICES = [
        ("guest", _("Guest")),
        ("student", _("Student or Graduate")),
        ("employer", _("Employer")),
        ("admin", _("Admin")),
        ("international_admin", _("International Admin")),
        ("main_admin", _("Main Admin")),
    ]

    full_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Full name"),
        help_text=_("Full name received from OAuth (read-only)")
    )

    full_name_locked = models.BooleanField(
        default=False,
        verbose_name=_("Full name locked"),
        help_text=_("If True, full_name cannot be changed")
    )


    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="guest",
        verbose_name=_("User Type"),
        help_text=_("Type of user account (guest, student, employer, admin)")
    )


    phone_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Phone Number"),
        help_text=_("User's phone number with country code")
    )
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Date of Birth"),
        help_text=_("User's date of birth")
    )


    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_("Bio"),
        help_text=_("Short biography or description")
    )
    avatar = models.ImageField(
        upload_to="avatars/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Avatar"),
        help_text=_("Profile picture")
    )


    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("City"),
        help_text=_("City of residence")
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Full address")
    )


    telegram = models.URLField(
        blank=True,
        verbose_name=_("Telegram"),
        help_text=_("Telegram username or link")
    )


    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Account verification status")
    )
    is_active_employer = models.BooleanField(
        default=False,
        verbose_name=_("Active Employer"),
        help_text=_("Whether this employer account is active")
    )


    profile_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Profile Views"),
        help_text=_("Number of times profile was viewed")
    )
    last_activity = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Activity"),
        help_text=_("Timestamp of last user activity")
    )

    oauth_provider = models.CharField(
    max_length=50,
    blank=True,
    null=True,
    verbose_name=_("OAuth Provider")
    )

    oauth_uid = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        unique=True,
        verbose_name=_("OAuth UID")
    )

    last_login_ip = models.GenericIPAddressField(
        blank=True,
        null=True
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
        verbose_name = _("User")
        verbose_name_plural = _("Users")
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

    def get_full_name(self):

        if self.full_name:
            return self.full_name.strip()
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.username


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
        return self.user_type in ADMIN_USER_TYPES

    @property
    def is_international_admin(self):
        return self.user_type == "international_admin"

    @property
    def is_main_admin(self):
        return self.user_type == "main_admin"

    def has_admin_permission(self, permission_name):
        return user_has_admin_permission(self, permission_name)

    @property
    def can_create_resume(self):
        """Может ли пользователь создавать резюме"""
        return self.user_type in ["student"]

    @property
    def can_create_jobs(self):
        """Может ли пользователь создавать вакансии"""
        return (
            self.user_type in ["employer"]
            and self.is_active_employer
        )

    @property
    def can_manage_users(self):
        """Может ли пользователь управлять другими пользователями"""
        return self.is_main_admin or any(
            self.has_admin_permission(permission_name)
            for permission_name in (
                "can_manage_students",
                "can_manage_employers",
            )
        )

    @property
    def companies(self):
        return self.companies_owned.all() if self.is_employer else Company.objects.none()



class Company(models.Model):
    """Model representing a company that can be owned by employers"""

    COMPANY_SIZE_CHOICES = [
        ("1-10", _("1-10 employees")),
        ("11-50", _("11-50 employees")),
        ("51-200", _("51-200 employees")),
        ("201-500", _("201-500 employees")),
        ("501-1000", _("501-1000 employees")),
        ("1000+", _("1000+ employees")),
    ]


    name = models.CharField(
        max_length=255,
        verbose_name=_("Company Name"),
        help_text=_("Official company name")
    )


    company_type = models.CharField(
        max_length=50,
        verbose_name=_("Company Type"),
        help_text=_("Legal structure of the company")
    )
    company_size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True,
        verbose_name=_("Company Size"),
        help_text=_("Number of employees in the company")
    )


    description = models.TextField(
        blank=True,
        verbose_name=_("Company Description"),
        help_text=_("Detailed description of the company")
    )
    short_description = models.TextField(
        max_length=500,
        blank=True,
        verbose_name=_("Short Description"),
        help_text=_("Brief company description for listings")
    )


    logo = models.ImageField(
        upload_to="company_logos/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Company Logo"),
        help_text=_("Company logo image")
    )


    email = models.EmailField(
        blank=True,
        verbose_name=_("Company Email"),
        help_text=_("Primary company email address")
    )
    phone = PhoneNumberField(
        blank=True,
        verbose_name=_("Company Phone"),
        help_text=_("Company phone number")
    )
    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Company Website"),
        help_text=_("Official company website")
    )


    region = models.CharField(
        max_length=100,
        choices=REGIONS,
        blank=True,
        verbose_name=_("Region"),
        help_text=_("Region where company is located")
    )
    city = models.CharField(
        max_length=100,
        choices=CITIES,
        blank=True,
        verbose_name=_("City"),
        help_text=_("City where company is based")
    )
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Full company address")
    )


    linkedin = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("LinkedIn"),
        help_text=_("Company LinkedIn page URL")
    )
    telegram = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Telegram"),
        help_text=_("Company Telegram channel or group")
    )
    facebook = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Facebook"),
        help_text=_("Company Facebook page URL")
    )
    instagram = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Instagram"),
        help_text=_("Company Instagram profile URL")
    )


    industry = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Industry"),
        help_text=_("Main industry of the company")
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Tags"),
        help_text=_("Comma-separated tags for searching")
    )


    founded_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Founded Year"),
        help_text=_("Year the company was founded")
    )
    mission = models.TextField(
        blank=True,
        verbose_name=_("Mission Statement"),
        help_text=_("Company mission and values")
    )



    owner = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="companies_owned",
        verbose_name=_("Owner"),
        help_text=_("Primary owner/administrator of the company")
    )


    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Company"),
        help_text=_("Whether the company is verified by administration")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether the company is active and visible")
    )


    total_jobs = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Jobs"),
        help_text=_("Number of job postings created")
    )
    active_jobs = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Active Jobs"),
        help_text=_("Number of currently active job postings")
    )
    total_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Views"),
        help_text=_("Total company profile views")
    )
    applicants_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Applicants Count"),
        help_text=_("Total number of job applicants")
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
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=['owner', 'is_active']),
            models.Index(fields=['is_verified', 'is_active']),
            models.Index(fields=['industry']),
        ]

    def __str__(self):
        return f"{self.name} (Owner: {self.owner.username})"

    def get_absolute_url(self):
        return reverse("accounts:company_detail", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):
        """Generate short description if not provided"""
        if not self.short_description and self.description:
            self.short_description = self.description[:497] + "..."
        super().save(*args, **kwargs)

    @property
    def formatted_tags(self):
        """Get tags as list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []

    @property
    def rating(self):
        """Calculate company rating based on jobs and reviews"""
        return 0.0

    @property
    def is_deleted(self):
        """Check if company is soft deleted"""
        return not self.is_active


class EmployerProfile(models.Model):
    """Profile for employer users with personal information (separate from Company)"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="employer_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )


    job_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Job Title"),
        help_text=_("Current professional position")
    )


    professional_bio = models.TextField(
        blank=True,
        verbose_name=_("Professional Bio"),
        help_text=_("Professional background and experience")
    )


    preferred_contact_method = models.CharField(
        max_length=20,
        choices=[
            ("email", _("Email")),
            ("phone", _("Phone")),
            ("telegram", _("Telegram")),
        ],
        default="email",
        verbose_name=_("Preferred Contact Method"),
        help_text=_("Preferred way to be contacted")
    )


    phone_number = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_("Phone Number"),
        help_text=_("Employer contact phone number")
    )


    primary_company_id = models.ForeignKey(
        "Company",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employer_primary",
        verbose_name=_("Primary Company"),
        help_text=_("Primary company for this employer")
    )


    total_jobs_posted = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Jobs Posted"),
        help_text=_("Total number of job postings created across all companies")
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
        verbose_name = _("Employer Profile")
        verbose_name_plural = _("Employer Profiles")

    def __str__(self):
        return f"Employer Profile: {self.user.username}"

    def get_absolute_url(self):
        return reverse("accounts:employer_profile", kwargs={"pk": self.pk})

    @property
    def total_companies(self):
        return self.user.companies_owned.filter(is_active=True).count()

    @property
    def primary_company(self):
        """Property to access primary_company_id with a more readable name"""
        return self.primary_company_id

    @primary_company.setter
    def primary_company(self, value):
        """Setter for primary_company property"""
        self.primary_company_id = value

    @property
    def owned_companies(self):
        """Get all companies owned by this user"""
        return self.user.companies_owned.filter(is_active=True)


class StudentProfile(models.Model):
    """Profile for student/graduate users with educational and career information"""
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account"),
    )

    avatar = models.ImageField(
        upload_to='student_avatars/%Y/%m/%d/',
        blank=True, null=True
    )

    student_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Student ID"),
        help_text=_("University student identifier"),
    )

    faculty = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Faculty"),
        help_text=_("Faculty or department"),
    )

    specialty = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Specialty"),
        help_text=_("Field of study or specialization"),
    )

    education_level = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Education Level"),
        help_text=_("Bachelor, Master, PhD, etc."),
    )

    graduation_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Graduation Year"),
        help_text=_("Year of graduation or expected graduation"),
    )

    desired_position = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("Desired Position"),
        help_text=_("Position the student is seeking"),
    )

    desired_salary = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Desired Salary"),
        help_text=_("Expected salary"),
    )

    WORK_TYPE_CHOICES = [
        ("full_time", _("Full Time")),
        ("part_time", _("Part Time")),
        ("internship", _("Internship")),
        ("remote", _("Remote")),
    ]

    work_type = models.CharField(
        max_length=50,
        choices=WORK_TYPE_CHOICES,
        blank=True,
        verbose_name=_("Work Type"),
        help_text=_("Preferred work arrangement"),
    )

    website = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("Website"),
        help_text=_("Personal or portfolio website"),
    )

    linkedin = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("LinkedIn"),
        help_text=_("LinkedIn profile URL"),
    )

    github = models.URLField(
        blank=True,
        null=True,
        verbose_name=_("GitHub"),
        help_text=_("GitHub profile URL"),
    )

    bio = models.TextField(
        blank=True,
        verbose_name=_("Bio"),
        help_text=_("Short biography, skills and experience"),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    def get_education_level_display(self):
        """
        Keep template compatibility for a free-text education level field.
        """
        return (self.education_level or "").strip()

    class Meta:
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialty or ''}"

    def get_absolute_url(self):
        return reverse("accounts:student_profile", kwargs={"pk": self.pk})

    def save(self, *args, **kwargs):

        if not self.avatar:
            return super().save(*args, **kwargs)


        self.avatar.open()
        img = Image.open(self.avatar)


        img = ImageOps.exif_transpose(img)


        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")


        target_size = (512, 512)
        img = ImageOps.fit(img, target_size, method=Image.LANCZOS, centering=(0.5, 0.5))


        buffer = io.BytesIO()
        save_kwargs = {"format": "WEBP", "quality": 75, "method": 6}


        if img.mode == "RGBA":
            save_kwargs["lossless"] = False

        img.save(buffer, **save_kwargs)
        buffer.seek(0)


        new_name = f"{uuid.uuid4().hex}.webp"
        self.avatar.save(new_name, ContentFile(buffer.read()), save=False)

        super().save(*args, **kwargs)


class StudentCertificate(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="certificates",
        verbose_name=_("Student"),
        help_text=_("Student profile that owns this certificate"),
    )
    title = models.CharField(
        max_length=255,
        verbose_name=_("Certificate Title"),
        help_text=_("Certificate name shown to employers"),
    )
    file = models.FileField(
        upload_to=student_certificate_upload_to,
        storage=StudentCertificateStorage(),
        validators=[validate_student_certificate_file],
        verbose_name=_("Certificate File"),
        help_text=_("Upload a PDF or image certificate"),
    )
    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional certificate details"),
    )
    issuer = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Issuer"),
        help_text=_("Organization that issued the certificate"),
    )
    issue_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("Issue Date"),
        help_text=_("Date when the certificate was issued"),
    )
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Uploaded At"),
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At"),
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Visible to Employers"),
        help_text=_("Whether this certificate can be shown to employers"),
    )

    class Meta:
        verbose_name = _("Student Certificate")
        verbose_name_plural = _("Student Certificates")
        ordering = ["-uploaded_at"]
        indexes = [
            models.Index(fields=["student", "is_active"]),
            models.Index(fields=["-uploaded_at"]),
        ]

    def __str__(self):
        return f"{self.title} - {self.student.user.get_full_name()}"

    def clean(self):
        super().clean()

        if self.issue_date and self.issue_date > timezone.localdate():
            raise ValidationError({"issue_date": _("Issue date cannot be in the future.")})

        if self.file:
            validate_student_certificate_file(self.file)

    @property
    def extension(self):
        if not self.file:
            return ""
        return self.file.name.rsplit(".", 1)[-1].lower()

    @property
    def filename(self):
        if not self.file:
            return ""
        return self.file.name.rsplit("/", 1)[-1]

    @property
    def is_pdf(self):
        return self.extension == "pdf"

    @property
    def is_image(self):
        return self.extension in CERTIFICATE_IMAGE_EXTENSIONS

    @property
    def content_type(self):
        if not self.file:
            return "application/octet-stream"
        return get_certificate_content_type(self.file.name)

    @property
    def download_filename(self):
        base_name = slugify(self.title) or "certificate"
        extension = self.extension or "bin"
        return f"{base_name}.{extension}"

    def get_file_url(self):
        return reverse("accounts:student_certificate_file", kwargs={"pk": self.pk})

    def get_download_url(self):
        return f"{self.get_file_url()}?download=1"



class AdminProfile(models.Model):
    """Profile for admin users with management permissions"""

    PERMISSION_FIELDS = (
        "can_manage_students",
        "can_manage_employers",
        "can_create_employers",
        "can_change_user_status",
        "can_manage_companies",
        "can_view_company_details",
        "can_verify_companies",
        "can_change_company_status",
        "can_manage_jobs",
        "can_create_jobs",
        "can_manage_resumes",
        "can_manage_events",
        "can_view_statistics",
    )
    PERMISSION_GROUPS = (
        (
            _("Users and Employers"),
            "fas fa-users-cog",
            (
                "can_manage_students",
                "can_manage_employers",
                "can_create_employers",
                "can_change_user_status",
            ),
        ),
        (
            _("Companies and Jobs"),
            "fas fa-briefcase",
            (
                "can_manage_companies",
                "can_view_company_details",
                "can_verify_companies",
                "can_change_company_status",
                "can_manage_jobs",
                "can_create_jobs",
            ),
        ),
        (
            _("Content and Analytics"),
            "fas fa-chart-line",
            (
                "can_manage_resumes",
                "can_manage_events",
                "can_view_statistics",
            ),
        ),
    )

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )


    can_manage_students = models.BooleanField(
        default=True,
        verbose_name=_("Manage Students"),
        help_text=_("Permission to manage student accounts and profiles")
    )
    can_manage_employers = models.BooleanField(
        default=True,
        verbose_name=_("Manage Employers"),
        help_text=_("Permission to manage employer accounts and profiles")
    )
    can_create_employers = models.BooleanField(
        default=True,
        verbose_name=_("Create Employers"),
        help_text=_("Permission to create employer accounts")
    )
    can_change_user_status = models.BooleanField(
        default=True,
        verbose_name=_("Change User Status"),
        help_text=_("Permission to activate or deactivate managed users")
    )
    can_manage_companies = models.BooleanField(
        default=True,
        verbose_name=_("Manage Companies"),
        help_text=_("Permission to manage company profiles")
    )
    can_view_company_details = models.BooleanField(
        default=True,
        verbose_name=_("View Company Details"),
        help_text=_("Permission to view detailed company data in the admin area")
    )
    can_verify_companies = models.BooleanField(
        default=True,
        verbose_name=_("Verify Companies"),
        help_text=_("Permission to verify and unverify companies")
    )
    can_change_company_status = models.BooleanField(
        default=True,
        verbose_name=_("Change Company Status"),
        help_text=_("Permission to activate or deactivate companies")
    )
    can_manage_jobs = models.BooleanField(
        default=True,
        verbose_name=_("Manage Jobs"),
        help_text=_("Permission to manage job postings")
    )
    can_create_jobs = models.BooleanField(
        default=True,
        verbose_name=_("Create Jobs"),
        help_text=_("Permission to create jobs from the admin area")
    )
    can_manage_resumes = models.BooleanField(
        default=True,
        verbose_name=_("Manage Resumes"),
        help_text=_("Permission to manage resumes and CVs")
    )
    can_manage_events = models.BooleanField(
        default=True,
        verbose_name=_("Manage Events"),
        help_text=_("Permission to create, edit and moderate events")
    )
    can_view_statistics = models.BooleanField(
        default=True,
        verbose_name=_("View Statistics"),
        help_text=_("Permission to view system statistics and analytics")
    )


    employers_created = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Employers Created"),
        help_text=_("Number of employer accounts created")
    )
    companies_verified = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Companies Verified"),
        help_text=_("Number of company profiles verified")
    )
    resources_created = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Resources Created"),
        help_text=_("Number of resources or articles created")
    )
    events_created = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Events Created"),
        help_text=_("Number of events or announcements created")
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
        verbose_name = _("Admin Profile")
        verbose_name_plural = _("Admin Profiles")

    def __str__(self):
        return f"Admin: {self.user.username}"

    @property
    def permission_sections(self):
        sections = []
        for title, icon, field_names in self.PERMISSION_GROUPS:
            permissions = []
            for field_name in field_names:
                field = self._meta.get_field(field_name)
                permissions.append(
                    {
                        "name": field_name,
                        "label": field.verbose_name,
                        "help_text": field.help_text,
                        "granted": bool(getattr(self, field_name)),
                    }
                )
            sections.append(
                {
                    "title": title,
                    "icon": icon,
                    "permissions": permissions,
                }
            )
        return sections


def is_admin_user(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "user_type", None) in ADMIN_USER_TYPES
    )


def is_main_admin_user(user):
    return bool(
        user
        and getattr(user, "is_authenticated", False)
        and getattr(user, "user_type", None) == "main_admin"
    )


def user_has_admin_permission(user, permission_name):
    if not is_admin_user(user):
        return False

    if is_main_admin_user(user):
        return True

    try:
        admin_profile = user.admin_profile
    except AdminProfile.DoesNotExist:
        admin_profile, _ = AdminProfile.objects.get_or_create(user=user)

    return bool(getattr(admin_profile, permission_name, False))


class HemisAuth(models.Model):
    """Model for authentication through Hemis API integration"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="hemis_auth",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )

    hemis_user_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_("Hemis User ID"),
        help_text=_("User ID from Hemis system")
    )

    access_token = models.TextField(
        verbose_name=_("Access Token"),
        help_text=_("OAuth access token for Hemis API")
    )
    refresh_token = models.TextField(
        verbose_name=_("Refresh Token"),
        help_text=_("OAuth refresh token for Hemis API")
    )
    token_expires = models.DateTimeField(
        verbose_name=_("Token Expires"),
        help_text=_("Expiration date of the access token")
    )

    hemis_user_data = models.JSONField(
        verbose_name=_("Hemis User Data"),
        help_text=_("JSON data retrieved from Hemis API")
    )

    last_sync = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Last Sync"),
        help_text=_("Timestamp of last data synchronization")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )

    class Meta:
        verbose_name = _("Hemis Authentication")
        verbose_name_plural = _("Hemis Authentications")

    def __str__(self):
        return f"Hemis auth for {self.user.username}"

    def is_token_valid(self):
        """Check if the access token is still valid"""
        from django.utils import timezone
        return timezone.now() < self.token_expires


class UserActivity(models.Model):
    """Model for tracking user activities and interactions"""

    ACTIVITY_TYPES = [
        ("login", _("Login")),
        ("logout", _("Logout")),
        ("profile_view", _("Profile View")),
        ("job_apply", _("Job Application")),
        ("resume_create", _("Resume Creation")),
        ("job_create", _("Job Creation")),
        ("profile_update", _("Profile Update")),
        ("password_change", _("Password Change")),
        ("company_create", _("Company Creation")),
        ("company_update", _("Company Update")),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who performed the activity")
    )

    activity_type = models.CharField(
        max_length=50,
        choices=ACTIVITY_TYPES,
        verbose_name=_("Activity Type"),
        help_text=_("Type of user activity")
    )

    description = models.TextField(
        blank=True,
        verbose_name=_("Description"),
        help_text=_("Optional description of the activity")
    )

    related_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Company"),
        help_text=_("Company related to this activity")
    )

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_("IP Address"),
        help_text=_("IP address of the user at the time of activity")
    )

    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser or device information")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when the activity occurred")
    )

    class Meta:
        verbose_name = _("User Activity")
        verbose_name_plural = _("User Activities")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user.username} — {self.get_activity_type_display()} — {self.created_at}"

    def save(self, *args, **kwargs):
        """Update user's last_activity timestamp when saving activity"""
        super().save(*args, **kwargs)
        if self.user:
            self.user.last_activity = self.created_at
            self.user.save(update_fields=["last_activity"])


class Notification(models.Model):
    """Model for user notifications and system messages"""

    NOTIFICATION_TYPES = [
        ("job_alert", _("Job Alert")),
        ("application_update", _("Application Update")),
        ("message", _("Message")),
        ("system", _("System Message")),
        ("event", _("Event Message")),
        ("security", _("Security Message")),
        ("company_update", _("Company Update")),
        ("company_verification", _("Company Verification")),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("Recipient of the notification")
    )

    notification_type = models.CharField(
        max_length=50,
        choices=NOTIFICATION_TYPES,
        verbose_name=_("Notification Type"),
        help_text=_("Category of the notification")
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Title"),
        help_text=_("Notification title or subject")
    )

    message = models.TextField(
        verbose_name=_("Message"),
        help_text=_("Full notification content")
    )

    is_read = models.BooleanField(
        default=False,
        verbose_name=_("Is Read"),
        help_text=_("Whether the notification has been read")
    )

    related_url = models.URLField(
        blank=True,
        verbose_name=_("Related URL"),
        help_text=_("Optional link related to the notification")
    )

    related_company = models.ForeignKey(
        Company,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Related Company"),
        help_text=_("Company related to this notification")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("Timestamp when the notification was created")
    )

    class Meta:
        verbose_name = _("Notification")
        verbose_name_plural = _("Notifications")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} — {self.user.username}"

    def mark_as_read(self):
        """Mark the notification as read"""
        self.is_read = True
        self.save()


class CompanyDocument(models.Model):
    """Model for company verification documents and files"""

    DOCUMENT_TYPES = [
        ("license", _("Business License")),
        ("registration", _("Registration Certificate")),
        ("tax", _("Tax Certificate")),
        ("bank", _("Bank Statement")),
        ("other", _("Other Document")),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="documents",
        verbose_name=_("Company"),
        help_text=_("Company this document belongs to")
    )

    document_type = models.CharField(
        max_length=50,
        choices=DOCUMENT_TYPES,
        verbose_name=_("Document Type"),
        help_text=_("Type of document")
    )

    file = models.FileField(
        upload_to="company_documents/%Y/%m/%d/",
        verbose_name=_("Document File"),
        help_text=_("Upload document file")
    )

    title = models.CharField(
        max_length=255,
        verbose_name=_("Document Title"),
        help_text=_("Title or description of the document")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified"),
        help_text=_("Whether the document is verified by administration")
    )

    verified_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="verified_documents",
        verbose_name=_("Verified By"),
        help_text=_("Admin who verified the document")
    )

    verified_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Verified At"),
        help_text=_("When the document was verified")
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
        verbose_name = _("Company Document")
        verbose_name_plural = _("Company Documents")

    def __str__(self):
        return f"{self.title} - {self.company.name}"



@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create corresponding profile when user is created"""
    if created:
        if instance.user_type == "student":
            StudentProfile.objects.create(user=instance)
        elif instance.user_type == "employer":
            EmployerProfile.objects.create(user=instance)
        elif instance.user_type in ADMIN_USER_TYPES:
            AdminProfile.objects.create(user=instance)


@receiver(post_save, sender=CustomUser)
def create_user_activity_on_signup(sender, instance, created, **kwargs):
    """Create activity record when user signs up"""
    if created:
        UserActivity.objects.create(
            user=instance,
            activity_type="profile_update",
            description=str(_("User registered")),
        )


@receiver(post_save, sender=Company)
def update_employer_stats(sender, instance, created, **kwargs):
    """Update employer statistics when company is created/updated"""
    try:

        employer_profile = instance.owner.employer_profile


        employer_profile.total_companies = instance.owner.companies_owned.filter(is_active=True).count()


        from jobs.models import Job
        employer_profile.total_jobs_posted = Job.objects.filter(company__owner=instance.owner).count()

        employer_profile.save()
    except (EmployerProfile.DoesNotExist, AttributeError):

        pass


@receiver(post_save, sender=EmployerProfile)
def activate_employer_user(sender, instance, created, **kwargs):
    """Activate employer user when profile is created"""
    if created:
        instance.user.is_active_employer = True
        instance.user.save()




class OAuthToken(models.Model):
    """
    Модель для хранения OAuth токенов пользователей.

    Хранит:
    - Access token для API запросов
    - Refresh token для обновления access token
    - Срок действия токенов
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='oauth_token',
        verbose_name=_('Пользователь')
    )

    access_token = models.TextField(
        verbose_name=_("Access Token"),
        help_text=_("Токен для доступа к API")
    )

    refresh_token = models.TextField(
        verbose_name=_("Refresh Token"),
        blank=True,
        null=True,
        help_text=_("Токен для обновления access token")
    )

    token_type = models.CharField(
        max_length=50,
        default='Bearer',
        verbose_name=_("Тип токена")
    )

    expires_in = models.IntegerField(
        verbose_name=_("Срок действия (секунды)"),
        default=3600
    )

    expires_at = models.DateTimeField(
        verbose_name=_("Истекает в"),
        null=True,
        blank=True
    )

    scope = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Разрешения")
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Создан")
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Обновлен")
    )

    class Meta:
        verbose_name = _("OAuth Токен")
        verbose_name_plural = _("OAuth Токены")
        db_table = 'accounts_oauth_token'

    def __str__(self):
        return f"OAuth Token for {self.user.username}"

    def is_expired(self):
        """Проверка истечения срока действия токена."""
        from django.utils import timezone
        return timezone.now() >= self.expires_at

    def refresh_access_token(self):
        """
        Обновление access token с помощью refresh token.

        Returns:
            bool: True если успешно, False если ошибка
        """
        if not self.refresh_token:
            return False

        try:
            from django.conf import settings

            oauth_config = settings.OAUTH_PROVIDER

            payload = {
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token,
                'client_id': oauth_config['CLIENT_ID'],
                'client_secret': oauth_config['CLIENT_SECRET'],
            }

            response = requests.post(
                oauth_config['ACCESS_TOKEN_URL'],
                data=payload,
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()


            self.access_token = token_data.get('access_token')
            if 'refresh_token' in token_data:
                self.refresh_token = token_data['refresh_token']
            self.expires_in = token_data.get('expires_in', 3600)
            self.expires_at = timezone.now() + timedelta(seconds=self.expires_in)
            self.save()

            return True

        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error refreshing token: {str(e)}")
            return False




class CompanyAdditionalInfo(models.Model):
    """Модель для хранения дополнительной информации о компании"""
    company = models.OneToOneField(
        Company,
        on_delete=models.CASCADE,
        related_name='additional_info',
        verbose_name=_("Company"),
        help_text=_("Company additional information")
    )
    legal_name = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Legal Name"),
        help_text=_("Official legal name of the company")
    )
    tax_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Tax ID/INN"),
        help_text=_("Company tax identification number")
    )
    cover_image = models.ImageField(
        upload_to="company_covers/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Cover Image"),
        help_text=_("Company cover image")
    )
    sub_industry = models.CharField(
        max_length=150,
        blank=True,
        verbose_name=_("Sub-Industry"),
        help_text=_("Specific industry category")
    )
    vision = models.TextField(
        blank=True,
        verbose_name=_("Vision Statement"),
        help_text=_("Company vision and future goals")
    )
    country = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Country"),
        help_text=_("Country where company is located")
    )

    class Meta:
        verbose_name = _("Company Additional Information")
        verbose_name_plural = _("Company Additional Informations")

    def __str__(self):
        return f"Additional info for {self.company.name}"
