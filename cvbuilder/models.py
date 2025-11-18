from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class CVTemplate(models.Model):
    """CV template models for different resume layouts"""

    name = models.CharField(
        max_length=100,
        verbose_name=_("Template Name"),
        help_text=_("Display name for the CV template")
    )
    thumbnail = models.ImageField(
        upload_to="cv_templates/",
        verbose_name=_("Thumbnail"),
        help_text=_("Preview image of the template")
    )
    template_file = models.CharField(
        max_length=100,
        verbose_name=_("Template File"),
        help_text=_("Path to the template file")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active"),
        help_text=_("Whether this template is available for use")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When the template was created")
    )

    class Meta:
        verbose_name = _("CV Template")
        verbose_name_plural = _("CV Templates")

    def __str__(self):
        return self.name


class CV(models.Model):
    """Model for user resumes and CVs"""

    STATUS_CHOICES = [
        ("draft", _("Draft")),
        ("published", _("Published")),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who owns this CV")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("Title"),
        default="My Resume",
        help_text=_("Title or name of the resume")
    )
    template = models.ForeignKey(
        CVTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_("Template"),
        help_text=_("CV template used for this resume")
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="draft",
        verbose_name=_("Status"),
        help_text=_("Current status of the resume")
    )

    # Personal Information
    full_name = models.CharField(
        max_length=200,
        verbose_name=_("Full Name"),
        help_text=_("Complete name as it should appear on the resume")
    )
    email = models.EmailField(
        verbose_name=_("Email"),
        help_text=_("Professional email address")
    )
    phone = models.CharField(
        max_length=20,
        verbose_name=_("Phone"),
        help_text=_("Contact phone number")
    )
    location = models.CharField(
        max_length=100,
        verbose_name=_("Location"),
        help_text=_("City or location")
    )
    salary_expectation = models.IntegerField(
        null=True,
        blank=True,
        verbose_name=_("Salary Expectation"),
        help_text=_("Expected salary range")
    )
    summary = models.TextField(
        verbose_name=_("Summary"),
        help_text=_("Professional summary or objective")
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

    class Meta:
        verbose_name = _("CV")
        verbose_name_plural = _("CVs")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.user.username}"

    def get_absolute_url(self):
        return reverse("cvbuilder:cv_detail", kwargs={"pk": self.pk})


class Experience(models.Model):
    """Work experience model for CVs"""

    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
        related_name="experiences",
        verbose_name=_("CV"),
        help_text=_("CV this experience belongs to")
    )
    company = models.CharField(
        max_length=200,
        verbose_name=_("Company"),
        help_text=_("Name of the company or organization")
    )
    position = models.CharField(
        max_length=200,
        verbose_name=_("Position"),
        help_text=_("Job title or position held")
    )
    start_date = models.DateField(
        verbose_name=_("Start Date"),
        help_text=_("When you started this position")
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_("End Date"),
        help_text=_("When you left this position (leave blank if current)")
    )
    is_current = models.BooleanField(
        default=False,
        verbose_name=_("Current Position"),
        help_text=_("Check if this is your current job")
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Responsibilities, achievements, and key accomplishments")
    )

    class Meta:
        verbose_name = _("Work Experience")
        verbose_name_plural = _("Work Experiences")
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.position} at {self.company}"


class Education(models.Model):
    """Education model for CVs"""

    DEGREE_CHOICES = [
        ("secondary", _("Secondary Education")),
        ("specialized_secondary", _("Specialized Secondary")),
        ("bachelor", _("Bachelor's Degree")),
        ("master", _("Master's Degree")),
        ("phd", _("PhD")),
        ("doctor", _("Doctorate")),
    ]

    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
        related_name="educations",
        verbose_name=_("CV"),
        help_text=_("CV this education belongs to")
    )
    institution = models.CharField(
        max_length=200,
        verbose_name=_("Institution"),
        help_text=_("Name of the educational institution")
    )
    degree = models.CharField(
        max_length=50,
        choices=DEGREE_CHOICES,
        verbose_name=_("Degree"),
        help_text=_("Level of education achieved")
    )
    field_of_study = models.CharField(
        max_length=100,
        verbose_name=_("Field of Study"),
        help_text=_("Major or field of specialization")
    )
    graduation_year = models.IntegerField(
        verbose_name=_("Graduation Year"),
        help_text=_("Year of graduation or completion")
    )

    class Meta:
        verbose_name = _("Education")
        verbose_name_plural = _("Educations")
        ordering = ["-graduation_year"]

    def __str__(self):
        return f"{self.institution} - {self.field_of_study}"


class Skill(models.Model):
    """Skills model for CVs"""

    SKILL_LEVELS = [
        ("beginner", _("Beginner")),
        ("intermediate", _("Intermediate")),
        ("advanced", _("Advanced")),
        ("expert", _("Expert")),
    ]

    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
        related_name="skills",
        verbose_name=_("CV"),
        help_text=_("CV this skill belongs to")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Skill Name"),
        help_text=_("Name of the skill or technology")
    )
    level = models.CharField(
        max_length=20,
        choices=SKILL_LEVELS,
        verbose_name=_("Proficiency Level"),
        help_text=_("Your level of expertise in this skill")
    )

    class Meta:
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")

    def __str__(self):
        return self.name


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

    cv = models.ForeignKey(
        CV,
        on_delete=models.CASCADE,
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

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")

    def __str__(self):
        return f"{self.name} ({self.get_level_display()})"
