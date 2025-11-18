
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from django.db.models.signals import post_save
from django.dispatch import receiver


class CustomUser(AbstractUser):
    """Custom user model with different roles and extended profile information"""

    USER_TYPE_CHOICES = [
        ("guest", _("Guest")),
        ("student", _("Student or Graduate")),
        ("employer", _("Employer")),
        ("admin", _("Admin")),
        ("main_admin", _("Main Admin")),
    ]

    # Basic Information
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default="guest",
        verbose_name=_("User Type"),
        help_text=_("Type of user account (guest, student, employer, admin)")
    )

    # Hemis API data for students
    # hemis_id = models.CharField(
    #     max_length=100,
    #     blank=True,
    #     unique=True,
    #     null=True,
    #     verbose_name=_("Hemis ID")
    # )

    hemis_data = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_("Hemis Data"),
        help_text=_("JSON data from Hemis API integration")
    )

    # Contact Information
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

    # Profile
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
    address = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Address"),
        help_text=_("Full address")
    )

    # Social Media
    website = models.URLField(
        blank=True,
        verbose_name=_("Website"),
        help_text=_("Personal or professional website")
    )
    linkedin = models.URLField(
        blank=True,
        verbose_name=_("LinkedIn"),
        help_text=_("LinkedIn profile URL")
    )
    github = models.URLField(
        blank=True,
        verbose_name=_("GitHub"),
        help_text=_("GitHub profile URL")
    )
    telegram = models.URLField(
        blank=True,
        verbose_name=_("Telegram"),
        help_text=_("Telegram username or link")
    )

    # Preferences
    email_notifications = models.BooleanField(
        default=True,
        verbose_name=_("Email Notifications"),
        help_text=_("Receive email notifications")
    )
    job_alerts = models.BooleanField(
        default=True,
        verbose_name=_("Job Alerts"),
        help_text=_("Receive job alert notifications")
    )
    newsletter = models.BooleanField(
        default=False,
        verbose_name=_("Newsletter"),
        help_text=_("Subscribe to newsletter")
    )

    # Status
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

    # Statistics
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
    """Profile for employer users with company information"""

    COMPANY_SIZE_CHOICES = [
        ("1-10", _("1-10 employees")),
        ("11-50", _("11-50 employees")),
        ("51-200", _("51-200 employees")),
        ("201-500", _("201-500 employees")),
        ("501-1000", _("501-1000 employees")),
        ("1000+", _("1000+ employees")),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="employer_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )

    # Company Basic Information
    company_name = models.CharField(
        max_length=255,
        verbose_name=_("Company Name"),
        help_text=_("Official company name")
    )
    company_logo = models.ImageField(
        upload_to="company_logos/%Y/%m/%d/",
        null=True,
        blank=True,
        verbose_name=_("Company Logo"),
        help_text=_("Company logo image")
    )
    company_description = models.TextField(
        verbose_name=_("Company Description"),
        help_text=_("Detailed description of the company")
    )

    # Company Contact Information
    company_email = models.EmailField(
        blank=True,
        verbose_name=_("Company Email"),
        help_text=_("Primary company email address")
    )
    company_phone = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_("Company Phone"),
        help_text=_("Company phone number")
    )
    company_website = models.URLField(
        blank=True,
        verbose_name=_("Company Website"),
        help_text=_("Official company website")
    )

    # Company Social Media
    company_linkedin = models.URLField(
        blank=True,
        verbose_name=_("Company LinkedIn"),
        help_text=_("Company LinkedIn page URL")
    )
    company_telegram = models.URLField(
        blank=True,
        verbose_name=_("Company Telegram"),
        help_text=_("Company Telegram channel or group")
    )

    # Additional Company Information
    company_size = models.CharField(
        max_length=20,
        choices=COMPANY_SIZE_CHOICES,
        blank=True,
        verbose_name=_("Company Size"),
        help_text=_("Number of employees in the company")
    )
    industry = models.ForeignKey(
        'jobs.Industry',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Industry"),
        help_text=_("Primary industry or sector")
    )
    founded_year = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Founded Year"),
        help_text=_("Year the company was founded")
    )
    headquarters = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Headquarters"),
        help_text=_("Location of company headquarters")
    )

    # Statistics
    jobs_posted = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Jobs Posted"),
        help_text=_("Number of job postings created")
    )
    total_views = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Total Views"),
        help_text=_("Total profile views")
    )

    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verified Company"),
        help_text=_("Whether the company is verified")
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
        return f"{self.company_name} - {self.user.username}"

    def get_absolute_url(self):
        return reverse("accounts:employer_profile", kwargs={"pk": self.pk})


class StudentProfile(models.Model):
    """Profile for student/graduate users with educational and career information"""

    EDUCATION_LEVEL_CHOICES = [
        ("bachelor", _("Bachelor")),
        ("master", _("Master")),
        ("phd", _("PhD")),
        ("college", _("College")),
        ("school", _("School")),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="student_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )

    # Educational Information from Hemis
    student_id = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("Student ID"),
        help_text=_("Student identification number")
    )
    faculty = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Faculty"),
        help_text=_("Academic faculty or department")
    )
    specialty = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Specialty"),
        help_text=_("Field of study or specialization")
    )
    education_level = models.CharField(
        max_length=20,
        choices=EDUCATION_LEVEL_CHOICES,
        blank=True,
        verbose_name=_("Education Level"),
        help_text=_("Current or completed education level")
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
        help_text=_("Grade Point Average (0.00-4.00)")
    )

    # Career Preferences
    desired_position = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("Desired Position"),
        help_text=_("Preferred job position or title")
    )
    desired_salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("Desired Salary"),
        help_text=_("Preferred salary range")
    )
    work_type = models.CharField(
        max_length=50,
        choices=[
            ("full_time", _("Full Time")),
            ("part_time", _("Part Time")),
            ("remote", _("Remote")),
            ("internship", _("Internship")),
        ],
        blank=True,
        verbose_name=_("Work Type"),
        help_text=_("Preferred type of employment")
    )

    # Statistics
    resumes_created = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Resumes Created"),
        help_text=_("Number of resumes created")
    )
    jobs_applied = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Jobs Applied"),
        help_text=_("Number of job applications submitted")
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
        verbose_name = _("Student Profile")
        verbose_name_plural = _("Student Profiles")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.specialty}"

    def get_absolute_url(self):
        return reverse("accounts:student_profile", kwargs={"pk": self.pk})


class AdminProfile(models.Model):
    """Profile for admin users with management permissions"""

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name="admin_profile",
        verbose_name=_("User"),
        help_text=_("Associated user account")
    )

    # Admin Permissions
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
    can_manage_jobs = models.BooleanField(
        default=True,
        verbose_name=_("Manage Jobs"),
        help_text=_("Permission to manage job postings")
    )
    can_manage_resumes = models.BooleanField(
        default=True,
        verbose_name=_("Manage Resumes"),
        help_text=_("Permission to manage resumes and CVs")
    )
    can_view_statistics = models.BooleanField(
        default=True,
        verbose_name=_("View Statistics"),
        help_text=_("Permission to view system statistics and analytics")
    )

    # Administration Statistics
    students_managed = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Students Managed"),
        help_text=_("Number of student accounts managed")
    )
    employers_created = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Employers Created"),
        help_text=_("Number of employer accounts created")
    )
    jobs_approved = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Jobs Approved"),
        help_text=_("Number of job postings approved")
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


# accounts/models.py - часть с HemisAuth
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
        ("profile_view", _("Profile View")),
        ("job_apply", _("Job Application")),
        ("resume_create", _("Resume Creation")),
        ("job_create", _("Job Creation")),
        ("profile_update", _("Profile Update")),
        ("password_change", _("Password Change")),
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


# Signal handlers


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """Create corresponding profile when user is created"""
    if created:
        if instance.is_student:
            StudentProfile.objects.create(user=instance)
        elif instance.is_employer:
            EmployerProfile.objects.create(user=instance)
        elif instance.is_admin or instance.is_main_admin:
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


@receiver(post_save, sender=EmployerProfile)
def activate_employer_user(sender, instance, created, **kwargs):
    """Activate employer user when profile is created"""
    if created:
        instance.user.is_active_employer = True
        instance.user.save()
