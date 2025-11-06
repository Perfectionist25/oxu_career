from django import forms
from django.utils.translation import gettext_lazy as _
from .models import *

class JobForm(forms.ModelForm):
    """Форма для создания/редактирования вакансий"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'short_description', 'description', 'location',
            'remote_work', 'hybrid_work', 'employment_type', 'experience_level',
            'education_level', 'salary_min', 'salary_max', 'currency', 
            'hide_salary', 'salary_negotiable', 'requirements', 'responsibilities',
            'benefits', 'skills_required', 'preferred_skills', 'contact_email',
            'contact_person', 'application_url', 'expires_at'
        ]
        
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Senior Software Developer')
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Brief description of the job...')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': _('Detailed job description...')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Tashkent, Uzbekistan')
            }),
            'remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'hybrid_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'education_level': forms.Select(attrs={'class': 'form-control'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'hide_salary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'salary_negotiable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Required qualifications and experience...')
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Daily responsibilities and tasks...')
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Company benefits and perks...')
            }),
            'skills_required': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Python, Django, JavaScript, SQL...')
            }),
            'preferred_skills': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('React, Docker, AWS, MongoDB...')
            }),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'application_url': forms.URLInput(attrs={'class': 'form-control'}),
            'expires_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            })
        }
        labels = {
            'title': _('Job Title'),
            'short_description': _('Short Description'),
            'description': _('Job Description'),
            'location': _('Location'),
            'remote_work': _('Remote Work Available'),
            'hybrid_work': _('Hybrid Work Available'),
            'employment_type': _('Employment Type'),
            'experience_level': _('Experience Level'),
            'education_level': _('Education Level'),
            'salary_min': _('Minimum Salary'),
            'salary_max': _('Maximum Salary'),
            'currency': _('Currency'),
            'hide_salary': _('Hide Salary'),
            'salary_negotiable': _('Salary Negotiable'),
            'requirements': _('Requirements'),
            'responsibilities': _('Responsibilities'),
            'benefits': _('Benefits'),
            'skills_required': _('Required Skills'),
            'preferred_skills': _('Preferred Skills'),
            'contact_email': _('Contact Email'),
            'contact_person': _('Contact Person'),
            'application_url': _('Application URL'),
            'expires_at': _('Expires At'),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set required fields
        self.fields['title'].required = True
        self.fields['location'].required = True
        self.fields['employment_type'].required = True
        self.fields['experience_level'].required = True
        self.fields['education_level'].required = True
        self.fields['short_description'].required = True
        self.fields['description'].required = True
        self.fields['responsibilities'].required = True
        self.fields['requirements'].required = True
        self.fields['skills_required'].required = True
        self.fields['currency'].required = True
        self.fields['contact_email'].required = True
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        remote_work = cleaned_data.get('remote_work')
        hybrid_work = cleaned_data.get('hybrid_work')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(_('Minimum salary cannot be greater than maximum salary.'))
        
        # Проверка режима работы
        if remote_work and hybrid_work:
            raise forms.ValidationError(_('Cannot select both remote and hybrid work.'))
        
        return cleaned_data

class JobSearchForm(forms.Form):
    """Форма поиска вакансий"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Job title, company, or keywords...')
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Tashkent, Samarkand...')
        })
    )
    industry = forms.ModelChoiceField(
        queryset=Industry.objects.all(),
        required=False,
        empty_label=_('All Industries'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    employment_type = forms.MultipleChoiceField(
        required=False,
        choices=Job.EMPLOYMENT_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    experience_level = forms.MultipleChoiceField(
        required=False,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    education_level = forms.MultipleChoiceField(
        required=False,
        choices=Job.EDUCATION_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    remote_work = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    salary_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Min salary'),
            'min': '0'
        })
    )

class JobApplicationForm(forms.ModelForm):
    """Форма для отклика на вакансию"""
    
    class Meta:
        model = JobApplication
        fields = ['cv', 'cover_letter', 'expected_salary', 'notice_period', 'available_from']
        widgets = {
            'cv': forms.Select(attrs={'class': 'form-control'}),
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': _('Write your cover letter explaining why you are a good fit for this position...')
            }),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'notice_period': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'available_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'cv': _('Resume/CV'),
            'cover_letter': _('Cover Letter'),
            'expected_salary': _('Expected Salary'),
            'notice_period': _('Notice Period (days)'),
            'available_from': _('Available From'),
        }

class JobAlertForm(forms.ModelForm):
    """Форма для оповещений о вакансиях"""
    
    class Meta:
        model = JobAlert
        fields = ['name', 'keywords', 'location', 'industry', 'employment_type', 'experience_level', 'frequency']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('My Job Alert')
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Python, Django, Developer')
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Tashkent, Remote')
            }),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': _('Alert Name'),
            'keywords': _('Keywords'),
            'location': _('Location'),
            'industry': _('Industry'),
            'employment_type': _('Employment Type'),
            'experience_level': _('Experience Level'),
            'frequency': _('Frequency'),
        }

class ApplicationStatusForm(forms.Form):
    """Форма изменения статуса отклика"""
    status = forms.ChoiceField(
        choices=JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': _('Internal notes...')
        })
    )