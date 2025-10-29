from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.db.models import Sum
from django.contrib.auth import get_user_model
User = get_user_model()

class Company(models.Model):
    """Компания работодателя"""
    COMPANY_SIZE_CHOICES = [
        ('1-10', _('1-10 employees')),
        ('11-50', _('11-50 employees')),
        ('51-200', _('51-200 employees')),
        ('201-500', _('201-500 employees')),
        ('501-1000', _('501-1000 employees')),
        ('1000+', _('More than 1000 employees')),
    ]
    
    INDUSTRY_CHOICES = [
        ('it', _('IT & Technology')),
        ('finance', _('Finance & Banking')),
        ('healthcare', _('Healthcare')),
        ('education', _('Education')),
        ('manufacturing', _('Manufacturing')),
        ('retail', _('Retail')),
        ('consulting', _('Consulting')),
        ('tourism', _('Tourism & Hospitality')),
        ('construction', _('Construction')),
        ('energy', _('Energy')),
        ('telecom', _('Telecommunications')),
        ('other', _('Other')),
    ]

    name = models.CharField(max_length=200, verbose_name=_("Company Name"))
    description = models.TextField(verbose_name=_("Description"))
    website = models.URLField(verbose_name=_("Website"))
    logo = models.ImageField(upload_to='company_logos/', null=True, blank=True, verbose_name=_("Logo"))
    industry = models.CharField(max_length=50, choices=INDUSTRY_CHOICES, verbose_name=_("Industry"))
    company_size = models.CharField(max_length=20, choices=COMPANY_SIZE_CHOICES, verbose_name=_("Company Size"))
    founded_year = models.IntegerField(null=True, blank=True, verbose_name=_("Founded Year"))
    headquarters = models.CharField(max_length=100, verbose_name=_("Headquarters"), 
                                   help_text=_("e.g., Tashkent, Uzbekistan"))
    
    # Контактная информация
    contact_email = models.EmailField(verbose_name=_("Contact Email"))
    contact_phone = models.CharField(max_length=20, verbose_name=_("Contact Phone"))
    
    # Социальные сети
    linkedin = models.URLField(blank=True, verbose_name=_("LinkedIn"))
    twitter = models.URLField(blank=True, verbose_name=_("Twitter"))
    facebook = models.URLField(blank=True, verbose_name=_("Facebook"))
    
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Company"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Company")
        verbose_name_plural = _("Companies")
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('employers:company_detail', kwargs={'pk': self.pk})

    def job_count(self):
        return self.jobs.filter(is_active=True).count()

    def active_jobs(self):
        return self.jobs.filter(is_active=True)

class EmployerProfile(models.Model):
    """Профиль работодателя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name=_("User"))
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employers', verbose_name=_("Company"))
    position = models.CharField(max_length=100, verbose_name=_("Position"))
    department = models.CharField(max_length=100, verbose_name=_("Department"))
    phone = models.CharField(max_length=20, verbose_name=_("Phone"))
    
    # Права доступа
    can_post_jobs = models.BooleanField(default=False, verbose_name=_("Can Post Jobs"))
    can_manage_jobs = models.BooleanField(default=False, verbose_name=_("Can Manage Jobs"))
    can_view_candidates = models.BooleanField(default=False, verbose_name=_("Can View Candidates"))
    can_contact_candidates = models.BooleanField(default=False, verbose_name=_("Can Contact Candidates"))
    
    is_primary_contact = models.BooleanField(default=False, verbose_name=_("Primary Contact"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active Profile"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Employer Profile")
        verbose_name_plural = _("Employer Profiles")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.company.name}"

class Job(models.Model):
    """Вакансия"""
    EMPLOYMENT_TYPE_CHOICES = [
        ('full_time', _('Full Time')),
        ('part_time', _('Part Time')),
        ('contract', _('Contract')),
        ('internship', _('Internship')),
        ('remote', _('Remote Work')),
        ('freelance', _('Freelance')),
    ]
    
    EXPERIENCE_LEVEL_CHOICES = [
        ('intern', _('Intern')),
        ('junior', _('Junior')),
        ('middle', _('Middle')),
        ('senior', _('Senior')),
        ('lead', _('Lead')),
        ('manager', _('Manager')),
        ('director', _('Director')),
    ]
    
    CURRENCY_CHOICES = [
        ('UZS', _('Uzbek Sum (UZS)')),
        ('USD', _('US Dollar (USD)')),
        ('EUR', _('Euro (EUR)')),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='jobs', verbose_name=_("Company"))
    posted_by = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, verbose_name=_("Posted By"))
    
    title = models.CharField(max_length=200, verbose_name=_("Job Title"))
    description = models.TextField(verbose_name=_("Job Description"))
    requirements = models.TextField(verbose_name=_("Requirements"))
    responsibilities = models.TextField(verbose_name=_("Responsibilities"))
    benefits = models.TextField(blank=True, verbose_name=_("Benefits"))
    
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPE_CHOICES, verbose_name=_("Employment Type"))
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVEL_CHOICES, verbose_name=_("Experience Level"))
    
    location = models.CharField(max_length=100, verbose_name=_("Location"), 
                               help_text=_("e.g., Tashkent, Samarkand, Remote"))
    remote_work = models.BooleanField(default=False, verbose_name=_("Remote Work Available"))
    
    salary_min = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Minimum Salary"))
    salary_max = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name=_("Maximum Salary"))
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='UZS', verbose_name=_("Currency"))
    hide_salary = models.BooleanField(default=False, verbose_name=_("Hide Salary"))
    
    application_url = models.URLField(blank=True, verbose_name=_("Application URL"))
    contact_email = models.EmailField(verbose_name=_("Contact Email"))
    
    skills_required = models.TextField(help_text=_("List skills separated by commas"), verbose_name=_("Required Skills"))
    
    is_active = models.BooleanField(default=True, verbose_name=_("Active Job"))
    is_featured = models.BooleanField(default=False, verbose_name=_("Featured Job"))
    views_count = models.IntegerField(default=0, verbose_name=_("View Count"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, verbose_name=_("Expires At"))

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.company.name}"

    def get_absolute_url(self):
        return reverse('employers:job_detail', kwargs={'pk': self.pk})

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
            return _("from %(salary)s %(currency)s") % {'salary': f"{self.salary_min:,.0f}", 'currency': self.currency}
        elif self.salary_max:
            return _("up to %(salary)s %(currency)s") % {'salary': f"{self.salary_max:,.0f}", 'currency': self.currency}
        return _("Not specified")

class JobApplication(models.Model):
    """Отклик на вакансию"""
    STATUS_CHOICES = [
        ('new', _('New')),
        ('reviewed', _('Reviewed')),
        ('interview', _('Interview')),
        ('rejected', _('Rejected')),
        ('hired', _('Hired')),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='employer_applications', verbose_name=_("Job"))
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employer_applications', verbose_name=_("Candidate"))
    cv = models.ForeignKey('cvbuilder.CV', on_delete=models.SET_NULL, null=True, blank=True, related_name='employer_applications', verbose_name=_("Resume"))
    
    cover_letter = models.TextField(verbose_name=_("Cover Letter"))
    expected_salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name=_("Expected Salary"))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name=_("Status"))
    status_changed_at = models.DateTimeField(auto_now=True, verbose_name=_("Status Changed"))
    
    is_read = models.BooleanField(default=False, verbose_name=_("Read"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Job Application")
        verbose_name_plural = _("Job Applications")
        unique_together = ['job', 'candidate']
        ordering = ['-created_at']

    def __str__(self):
        return f"Application from {self.candidate.username} for {self.job.title}"

class CandidateNote(models.Model):
    """Заметки работодателя о кандидате"""
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employer_notes', verbose_name=_("Candidate"))
    employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, verbose_name=_("Employer"))
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_("Job"))
    
    note = models.TextField(verbose_name=_("Note"))
    is_private = models.BooleanField(default=True, verbose_name=_("Private Note"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Candidate Note")
        verbose_name_plural = _("Candidate Notes")
        ordering = ['-created_at']

    def __str__(self):
        return f"Note about {self.candidate.username}"

class Interview(models.Model):
    """Собеседование"""
    STATUS_CHOICES = [
        ('scheduled', _('Scheduled')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
        ('no_show', _('No Show')),
    ]

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name='interviews', verbose_name=_("Application"))
    interviewer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE, verbose_name=_("Interviewer"))
    
    scheduled_date = models.DateTimeField(verbose_name=_("Scheduled Date"))
    duration = models.IntegerField(help_text=_("Duration in minutes"), verbose_name=_("Duration"))
    location = models.TextField(verbose_name=_("Location"))
    notes = models.TextField(blank=True, verbose_name=_("Notes"))
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled', verbose_name=_("Status"))
    feedback = models.TextField(blank=True, verbose_name=_("Feedback"))
    rating = models.IntegerField(null=True, blank=True, help_text=_("Rating from 1 to 5"), verbose_name=_("Rating"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Interview")
        verbose_name_plural = _("Interviews")
        ordering = ['scheduled_date']

    def __str__(self):
        return f"Interview for {self.application.candidate.username}"

class CompanyReview(models.Model):
    """Отзывы о компании"""
    RATING_CHOICES = [
        (1, _('1 - Very Poor')),
        (2, _('2 - Poor')),
        (3, _('3 - Average')),
        (4, _('4 - Good')),
        (5, _('5 - Excellent')),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='employer_reviews', verbose_name=_("Company"))
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='employer_reviews', verbose_name=_("Author"))
    
    rating = models.IntegerField(choices=RATING_CHOICES, verbose_name=_("Rating"))
    title = models.CharField(max_length=200, verbose_name=_("Title"))
    review = models.TextField(verbose_name=_("Review"))
    
    pros = models.TextField(verbose_name=_("Pros"))
    cons = models.TextField(verbose_name=_("Cons"))
    
    is_anonymous = models.BooleanField(default=False, verbose_name=_("Anonymous Review"))
    is_verified = models.BooleanField(default=False, verbose_name=_("Verified Review"))
    is_published = models.BooleanField(default=False, verbose_name=_("Published"))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Company Review")
        verbose_name_plural = _("Company Reviews")
        ordering = ['-created_at']
        unique_together = ['company', 'author']

    def __str__(self):
        return f"Review by {self.author.username} for {self.company.name}"