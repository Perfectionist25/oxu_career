# jobs/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Job, JobApplication, JobAlert
from accounts.models import Company  # Добавлен импорт

# Определите список индустрий (можно расширить по мере необходимости)
INDUSTRY_CHOICES = [
    ('', _('Select Industry')),
    ('IT/Technology', _('IT/Technology')),
    ('Finance/Banking', _('Finance/Banking')),
    ('Healthcare/Medical', _('Healthcare/Medical')),
    ('Education/Training', _('Education/Training')),
    ('Marketing/Advertising', _('Marketing/Advertising')),
    ('Sales/Retail', _('Sales/Retail')),
    ('Manufacturing/Engineering', _('Manufacturing/Engineering')),
    ('Construction/Real Estate', _('Construction/Real Estate')),
    ('Hospitality/Tourism', _('Hospitality/Tourism')),
    ('Transportation/Logistics', _('Transportation/Logistics')),
    ('Government/Public Sector', _('Government/Public Sector')),
    ('Non-profit/NGO', _('Non-profit/NGO')),
    ('Media/Entertainment', _('Media/Entertainment')),
    ('Agriculture/Farming', _('Agriculture/Farming')),
    ('Other', _('Other')),
]


class JobForm(forms.ModelForm):
    """Form for creating/editing jobs with comprehensive validation"""

    terms_accept = forms.BooleanField(
        required=True,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
        label=_("I accept the terms and conditions"),
        error_messages={'required': _('You must accept the terms and conditions.')}
    )

    # Явно переопределяем поле industry как ChoiceField
    # Это нужно, чтобы Django не пытался создать ForeignKey
    industry = forms.ChoiceField(
        choices=INDUSTRY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_("Industry"),
        help_text=_("Select the industry that best describes this job")
    )

    class Meta:
        model = Job
        fields = [
            "title", "short_description", "description", "company", "location",  # ЗАМЕНА: employer -> company
            "region", "district", "work_type", "employment_type", "experience_level", 
            "education_level", "salary_min", "salary_max", "currency", "hide_salary", 
            "salary_negotiable", "bonus_system", "kpi_bonus", "performance_bonus",
            "requirements", "responsibilities", "benefits", "skills_required", 
            "preferred_skills", "language_requirements", "contact_email", 
            "contact_phone", "contact_person", "application_url", "work_schedule", 
            "probation_period", "expires_at", "industry"  # Добавлено industry
        ]
        # Removed: is_active, is_featured, is_urgent, is_premium - these should be set programmatically

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        required_fields = [
            'title', 'short_description', 'description', 'company',  # Добавлено company
            'location', 'work_type', 'employment_type', 'experience_level', 
            'education_level', 'requirements', 'responsibilities', 
            'skills_required', 'contact_email'
        ]
        
        # Make fields required
        for field in required_fields:
            if field in self.fields:
                self.fields[field].required = True
                # Add asterisk to label
                self.fields[field].label = f"{self.fields[field].label} *"

        # Filter companies for current user
        if self.user and self.user.is_authenticated:
            if self.user.is_employer:
                # Для работодателей показываем только их компании
                user_companies = Company.objects.filter(owner=self.user, is_active=True)
                self.fields['company'].queryset = user_companies
                
                if not self.instance.pk:  # Only for creation
                    user_company = user_companies.first()
                    if user_company:
                        self.fields['company'].initial = user_company
                
                # Make field read-only for regular employers
                if user_companies.count() == 1:
                    self.fields['company'].widget.attrs['readonly'] = True
                    self.fields['company'].widget.attrs['class'] = 'form-control bg-light'
                    self.fields['company'].help_text = _("Your company")
                else:
                    self.fields['company'].help_text = _("Select one of your companies")
            elif self.user.is_admin or self.user.is_main_admin:
                # Админы видят все активные компании
                self.fields['company'].queryset = Company.objects.filter(is_active=True)
                self.fields['company'].help_text = _("Select a company")
            else:
                # Для других пользователей скрываем поле
                self.fields['company'].widget = forms.HiddenInput()
                self.fields['company'].required = False
        else:
            self.fields['company'].widget = forms.HiddenInput()
            self.fields['company'].required = False

        # Add empty labels and styling for select fields
        select_fields = ['company', 'work_type', 'employment_type', 'experience_level', 
                        'education_level', 'currency', 'region', 'industry']  # Добавлено industry
        for field in select_fields:
            if field in self.fields:
                if field == 'industry':
                    # Для поля industry не нужно добавлять empty_label, так как оно уже есть в choices
                    self.fields[field].widget.attrs['class'] = 'form-select'
                elif field != 'company':  # Для company empty_label уже установлен
                    self.fields[field].empty_label = _("Please select...")
                    self.fields[field].widget.attrs['class'] = 'form-select'
                # Make required select fields more obvious
                if field in ['work_type', 'employment_type', 'experience_level', 'education_level']:
                    self.fields[field].widget.attrs['required'] = 'required'

        # Set initial values for contact information
        if self.user and not self.instance.pk:
            self.fields['contact_email'].initial = self.user.email
            if hasattr(self.user, 'get_full_name') and self.user.get_full_name():
                self.fields['contact_person'].initial = self.user.get_full_name()
            # Set phone if available
            if self.user.phone_number:
                self.fields['contact_phone'].initial = self.user.phone_number

        # Add help texts and placeholders
        self.fields['title'].widget.attrs['placeholder'] = _('e.g., Senior Software Engineer')
        self.fields['short_description'].widget.attrs['placeholder'] = _('Brief summary (max 300 characters)')
        self.fields['skills_required'].widget.attrs['placeholder'] = _('Python, Django, JavaScript, React, ...')
        self.fields['preferred_skills'].widget.attrs['placeholder'] = _('AWS, Docker, PostgreSQL, ...')
        self.fields['location'].widget.attrs['placeholder'] = _('Full address or location')
        self.fields['contact_email'].widget.attrs['placeholder'] = _('email@company.com')
        self.fields['contact_phone'].widget.attrs['placeholder'] = _('+998 XX XXX XX XX')
        
        # Set date input type for expires_at
        if 'expires_at' in self.fields:
            self.fields['expires_at'].widget = forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'}
            )
            # Set minimum date to tomorrow
            from django.utils import timezone
            import datetime
            tomorrow = (timezone.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
            self.fields['expires_at'].widget.attrs['min'] = tomorrow

    def clean(self):
        cleaned_data = super().clean()
        
        # Validate salary range
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            self.add_error('salary_max', _("Maximum salary should be greater than minimum salary."))
        
        # Ensure company is set for the current user
        if self.user and self.user.is_authenticated:
            company = cleaned_data.get('company')
            
            if self.user.is_employer:
                # Проверяем, что работодатель выбирает свою компанию
                if company and company not in self.user.companies.all():
                    self.add_error('company', _("You can only create jobs for your own companies."))
                
                # Если компания не выбрана, устанавливаем первую компанию пользователя
                if not company:
                    user_company = self.user.companies.first()
                    if user_company:
                        cleaned_data['company'] = user_company
                    else:
                        self.add_error('company', _("You don't have any companies. Please create a company first."))
        
        # Validate that at least one of region or district is provided if location is generic
        location = cleaned_data.get('location', '')
        region = cleaned_data.get('region')
        district = cleaned_data.get('district')
        
        if location and not region and not district:
            if 'Tashkent' in location or 'Toshkent' in location:
                cleaned_data['region'] = 'Tashkent'
            elif 'Samarkand' in location or 'Samarqand' in location:
                cleaned_data['region'] = 'Samarkand'
        
        return cleaned_data

    # def save(self, commit=True):
    #     """Save method that sets the created_by user"""
    #     instance = super().save(commit=False)
        
    #     if self.user:
    #         # Set created_by
    #         instance.created_by = self.user
            
    #         # Set company if not set and user is employer
    #         if not instance.company and self.user.is_employer:
    #             instance.company = self.user.companies.first()
        
    #     if commit:
    #         instance.save()
    #         # Save many-to-many relationships if any
    #         self.save_m2m()
        
    #     return instance


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
    
    # Добавлено: Поле для поиска по индустрии
    industry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("e.g., IT, Finance, Healthcare..."),
        }),
        label=_("Industry")
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

            student_profile = getattr(self.user, "student_profile", None)

            if student_profile:
                # CV.user = StudentProfile
                self.fields["cv"].queryset = CV.objects.filter(
                    user=student_profile,
                    status="published",
                )
            else:
                # нет student_profile (например alumni) — пусто, чтобы не падало
                self.fields["cv"].queryset = CV.objects.none()

        
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

    def save(self, commit=True):
        """Save method that sets the user and job"""
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if self.job:
            instance.job = self.job
        
        # ВАЖНО: Удаляем agree_to_terms из cleaned_data перед сохранением
        if hasattr(self, 'cleaned_data'):
            self.cleaned_data.pop('agree_to_terms', None)
        
        if commit:
            instance.save()
        return instance


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
    
    # Обновлено: поле индустрии как CharField
    industry = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("IT, Finance, Healthcare..."),
        }),
        label=_("Industry"),
        help_text=_("Leave empty for all industries")
    )

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
        # Добавляем пустые метки для выпадающих списков
        self.fields['employment_type'].empty_label = _("Any Type")
        self.fields['experience_level'].empty_label = _("Any Level")
        self.fields['frequency'].empty_label = _("Select frequency")
        
        # Удаляем стандартное поле industry из модели (если оно там есть как ForeignKey)
        # и используем наше новое CharField поле