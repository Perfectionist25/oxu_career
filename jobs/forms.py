# jobs/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Job, JobApplication, JobAlert


class JobForm(forms.ModelForm):
    """Form for creating/editing jobs with comprehensive validation"""

    # Добавляем поле для принятия условий
    terms_accept = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("I accept the terms and conditions"),
        error_messages={'required': _('You must accept the terms and conditions.')}
    )

    class Meta:
        model = Job
        fields = [
            # Basic Information
            "title", "short_description", "description",
            
            # Company and Location
            "employer", "location", "region", "district",
            
            # Work Type and Conditions
            "work_type", "employment_type", "experience_level", "education_level",
            
            # Salary Information
            "salary_min", "salary_max", "currency", "hide_salary", "salary_negotiable",
            
            # Additional Compensation
            "bonus_system", "kpi_bonus", "performance_bonus",
            
            # Requirements and Responsibilities
            "requirements", "responsibilities", "benefits",
            
            # Skills and Languages
            "skills_required", "preferred_skills", "language_requirements",
            
            # Contact Information
            "contact_email", "contact_phone", "contact_person", "application_url",
            
            # Work Process
            "work_schedule", "probation_period",
            
            # Status and Visibility
            "is_active", "is_featured", "is_urgent", "is_premium",
            
            # Duration
            "expires_at",
        ]

        widgets = {
            # Basic Information
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("e.g., Senior Frontend Developer"),
                "maxlength": "200"
            }),
            "short_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "maxlength": "300",
                "placeholder": _("Brief, engaging summary of the role..."),
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Detailed description of responsibilities, company culture, and opportunities..."),
            }),

            # Location
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Specific address or location"),
            }),
            "region": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Region or province"),
            }),
            "district": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("District or city"),
            }),

            # Select Fields
            "work_type": forms.Select(attrs={"class": "form-select"}),
            "employment_type": forms.Select(attrs={"class": "form-select"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "education_level": forms.Select(attrs={"class": "form-select"}),
            "currency": forms.Select(attrs={"class": "form-select"}),
            "employer": forms.Select(attrs={"class": "form-select"}),

            # Salary Fields
            "salary_min": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "1",
                "placeholder": _("Minimum salary"),
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "1",
                "placeholder": _("Maximum salary"),
            }),

            # Checkboxes
            "hide_salary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "salary_negotiable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "bonus_system": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "kpi_bonus": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "performance_bonus": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_featured": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_urgent": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_premium": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            # Text Areas
            "requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("• Bachelor's degree in relevant field\n• 3+ years of experience\n• Strong communication skills..."),
            }),
            "responsibilities": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("• Develop and maintain applications\n• Collaborate with team members\n• Participate in code reviews..."),
            }),
            "benefits": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("• Health insurance\n• Flexible working hours\n• Professional development\n• Team events..."),
            }),
            "language_requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("• English: Intermediate+\n• Russian: Fluent\n• Uzbek: Native"),
            }),

            # Skills
            "skills_required": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Python, Django, JavaScript, React, SQL"),
            }),
            "preferred_skills": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Docker, AWS, GraphQL, TypeScript"),
            }),

            # Contact Information
            "contact_email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": _("hr@company.com"),
            }),
            "contact_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("+998 XX XXX XX XX"),
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("John Doe"),
            }),
            "application_url": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": _("https://company.com/careers/apply"),
            }),

            # Work Process
            "work_schedule": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("9:00-18:00, Monday-Friday"),
            }),
            "probation_period": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("3 months"),
            }),

            # Dates
            "expires_at": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }

        labels = {
            "title": _("Job Title"),
            "short_description": _("Short Description"),
            "description": _("Detailed Description"),
            "employer": _("Company"),
            "location": _("Location"),
            "region": _("Region"),
            "district": _("District/City"),
            "work_type": _("Work Type"),
            "employment_type": _("Employment Type"),
            "experience_level": _("Experience Level"),
            "education_level": _("Education Level"),
            "salary_min": _("Minimum Salary"),
            "salary_max": _("Maximum Salary"),
            "currency": _("Currency"),
            "hide_salary": _("Hide Salary from Candidates"),
            "salary_negotiable": _("Salary is Negotiable"),
            "bonus_system": _("Bonus System Available"),
            "kpi_bonus": _("KPI-based Bonuses"),
            "performance_bonus": _("Performance Bonuses"),
            "requirements": _("Job Requirements"),
            "responsibilities": _("Key Responsibilities"),
            "benefits": _("Benefits & Perks"),
            "skills_required": _("Required Skills"),
            "preferred_skills": _("Preferred Skills"),
            "language_requirements": _("Language Requirements"),
            "contact_email": _("Contact Email"),
            "contact_phone": _("Contact Phone"),
            "contact_person": _("Contact Person"),
            "application_url": _("Application URL"),
            "work_schedule": _("Work Schedule"),
            "probation_period": _("Probation Period"),
            "is_active": _("Publish Job"),
            "is_featured": _("Feature Job"),
            "is_urgent": _("Urgent Hiring"),
            "is_premium": _("Premium Listing"),
            "expires_at": _("Application Deadline"),
        }

        help_texts = {
            "short_description": _("Brief summary that appears in search results (max 300 characters)"),
            "skills_required": _("Separate skills with commas"),
            "preferred_skills": _("Skills that are nice to have but not mandatory"),
            "hide_salary": _("Salary information will not be visible to candidates"),
            "salary_negotiable": _("Candidates can negotiate salary during interview"),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        required_fields = [
            'title', 'short_description', 'description', 'employer',
            'location', 'work_type', 'employment_type', 'experience_level', 
            'education_level', 'requirements', 'responsibilities', 
            'skills_required', 'contact_email'
        ]
        
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True

        # Filter employer choices for the current user
        if self.user and hasattr(self.user, 'employer_profile'):
            from accounts.models import EmployerProfile
            self.fields['employer'].queryset = EmployerProfile.objects.filter(user=self.user)
        else:
            self.fields['employer'].queryset = self.fields['employer'].queryset.none()
            if self.user and self.user.is_authenticated:
                self.fields['employer'].help_text = _("You need to create an employer profile first.")

        # Add empty labels to select fields
        select_fields = ['work_type', 'employment_type', 'experience_level', 'education_level', 'currency']
        for field in select_fields:
            if field in self.fields:
                self.fields[field].empty_label = _("Please select...")

        # Set initial values
        if self.user and not self.instance.pk:
            self.fields['contact_email'].initial = self.user.email
            if hasattr(self.user, 'get_full_name') and self.user.get_full_name():
                self.fields['contact_person'].initial = self.user.get_full_name()

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        hide_salary = cleaned_data.get('hide_salary')
        salary_negotiable = cleaned_data.get('salary_negotiable')

        # Salary validation
        if salary_min and salary_max:
            if salary_min > salary_max:
                self.add_error('salary_max', _("Maximum salary must be greater than minimum salary."))
        
        # If salary is hidden, it should be negotiable or have some indication
        if hide_salary and not salary_negotiable:
            self.add_error('salary_negotiable', 
                         _("If salary is hidden, it should be marked as negotiable."))

        # Validate skills format
        skills_required = cleaned_data.get('skills_required', '')
        if skills_required:
            skills_list = [skill.strip() for skill in skills_required.split(',') if skill.strip()]
            if len(skills_list) < 1:  # Changed from 2 to 1 to be less strict
                self.add_error('skills_required', 
                             _("Please provide at least 1 required skill."))

        return cleaned_data

    def clean_short_description(self):
        short_description = self.cleaned_data.get('short_description', '')
        if len(short_description.strip()) < 10:  # Changed from 50 to 10 to be less strict
            raise forms.ValidationError(
                _("Short description should be at least 10 characters long.")
            )
        return short_description

    def clean_contact_email(self):
        email = self.cleaned_data.get('contact_email')
        if email and self.user and email == self.user.email:
            # It's okay to use personal email as contact
            return email
        return email

    def save(self, commit=True):
        """Save method that sets the created_by user"""
        instance = super().save(commit=False)
        if self.user and not instance.created_by:
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class JobSearchForm(forms.Form):
    """Advanced job search form"""
    
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Job title, company, or keywords..."),
        }),
        label=_("Search")
    )
    
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("City, region, or district..."),
        }),
        label=_("Location")
    )
    
    employment_type = forms.MultipleChoiceField(
        required=False,
        choices=Job.EMPLOYMENT_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label=_("Employment Type")
    )
    
    experience_level = forms.MultipleChoiceField(
        required=False,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label=_("Experience Level")
    )
    
    education_level = forms.MultipleChoiceField(
        required=False,
        choices=Job.EDUCATION_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label=_("Education Level")
    )
    
    work_type = forms.MultipleChoiceField(
        required=False,
        choices=Job.WORK_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
        label=_("Work Type")
    )
    
    salary_min = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": _("Min salary"),
            "min": "0"
        }),
        label=_("Minimum Salary")
    )
    
    salary_max = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": _("Max salary"),
            "min": "0"
        }),
        label=_("Maximum Salary")
    )
    
    currency = forms.ChoiceField(
        required=False,
        choices=Job.CURRENCY_CHOICES,
        initial="UZS",
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Currency")
    )
    
    is_featured = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Featured Jobs Only")
    )
    
    is_urgent = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Urgent Hiring Only")
    )
    
    has_salary = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Jobs with Salary Info")
    )
    
    remote_ok = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Remote Work Available")
    )

    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            self.add_error('salary_max', _("Maximum salary should be greater than minimum salary."))
        
        return cleaned_data


class JobApplicationForm(forms.ModelForm):
    """Form for applying to jobs"""
    
    agree_to_terms = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("I agree to the terms and conditions"),
        error_messages={'required': _('You must agree to the terms and conditions to apply.')}
    )

    class Meta:
        model = JobApplication
        fields = ["cv", "cover_letter", "expected_salary", "available_from", "notice_period"]
        
        widgets = {
            "cv": forms.Select(attrs={
                "class": "form-select",
                "required": "required"
            }),
            "cover_letter": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Explain why you're a good fit for this position..."),
                "required": "required"
            }),
            "expected_salary": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "step": "100000",
                "placeholder": _("Your expected salary (optional)"),
            }),
            "available_from": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
            "notice_period": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "max": "90",
                "placeholder": _("Days required before starting (optional)"),
            }),
        }
        
        labels = {
            "cv": _("Select Resume"),
            "cover_letter": _("Cover Letter"),
            "expected_salary": _("Expected Salary"),
            "available_from": _("Available Start Date"),
            "notice_period": _("Notice Period (days)"),
        }
        
        help_texts = {
            "cover_letter": _("Customize your cover letter for this specific job application."),
            "expected_salary": _("Leave empty if you want to discuss during interview."),
            "notice_period": _("How many days notice you need to give your current employer."),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.job = kwargs.pop('job', None)
        super().__init__(*args, **kwargs)
        
        # Filter CVs for the current user
        if self.user:
            from cvbuilder.models import CV
            self.fields['cv'].queryset = CV.objects.filter(user=self.user, status='published')
        
        # Make cover letter and CV required
        self.fields['cover_letter'].required = True
        self.fields['cv'].required = True

    def clean_expected_salary(self):
        expected_salary = self.cleaned_data.get('expected_salary')
        if expected_salary and expected_salary < 0:
            raise forms.ValidationError(_("Expected salary cannot be negative."))
        return expected_salary

    def clean_notice_period(self):
        notice_period = self.cleaned_data.get('notice_period')
        if notice_period and (notice_period < 0 or notice_period > 90):
            raise forms.ValidationError(_("Notice period should be between 0 and 90 days."))
        return notice_period


class ApplicationStatusForm(forms.Form):
    """Form for employers to update application status"""
    
    status = forms.ChoiceField(
        choices=JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
        label=_("Update Status")
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": _("Add notes about this application..."),
        }),
        label=_("Internal Notes")
    )
    
    send_email = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("Notify candidate via email")
    )


class JobAlertForm(forms.ModelForm):
    """Form for creating job alerts"""
    
    class Meta:
        model = JobAlert
        fields = [
            "name", "keywords", "location", "industry", 
            "employment_type", "experience_level", "frequency"
        ]
        
        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("e.g., Python Developer Jobs in Tashkent"),
            }),
            "keywords": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Python, Django, JavaScript..."),
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Tashkent, Uzbekistan"),
            }),
            "industry": forms.Select(attrs={"class": "form-select"}),
            "employment_type": forms.Select(attrs={"class": "form-select"}),
            "experience_level": forms.Select(attrs={"class": "form-select"}),
            "frequency": forms.Select(attrs={"class": "form-select"}),
        }
        
        labels = {
            "name": _("Alert Name"),
            "keywords": _("Keywords"),
            "location": _("Location"),
            "industry": _("Industry"),
            "employment_type": _("Employment Type"),
            "experience_level": _("Experience Level"),
            "frequency": _("Notification Frequency"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add empty labels
        self.fields['industry'].empty_label = _("Any Industry")
        self.fields['employment_type'].empty_label = _("Any Type")
        self.fields['experience_level'].empty_label = _("Any Level")