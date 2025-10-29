from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Job, JobApplication, SavedJob, JobAlert, CompanyReview, InterviewExperience, Industry, Company

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

class JobForm(forms.ModelForm):
    """Форма для создания/редактирования вакансий"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'short_description', 'description', 'company', 'location',
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
            'company': forms.Select(attrs={'class': 'form-control'}),
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
            'expires_at': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'title': _('Job Title'),
            'short_description': _('Short Description'),
            'description': _('Job Description'),
            'company': _('Company'),
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
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(_('Minimum salary cannot be greater than maximum salary.'))
        
        return cleaned_data

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

class CompanyForm(forms.ModelForm):
    """Форма для компаний"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'website', 'logo', 'industry', 'company_size',
            'founded_year', 'headquarters', 'contact_email', 'contact_phone',
            'linkedin', 'twitter', 'facebook'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'headquarters': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': _('Company Name'),
            'description': _('Description'),
            'website': _('Website'),
            'logo': _('Logo'),
            'industry': _('Industry'),
            'company_size': _('Company Size'),
            'founded_year': _('Founded Year'),
            'headquarters': _('Headquarters'),
            'contact_email': _('Contact Email'),
            'contact_phone': _('Contact Phone'),
            'linkedin': _('LinkedIn'),
            'twitter': _('Twitter'),
            'facebook': _('Facebook'),
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

class CompanyReviewForm(forms.ModelForm):
    """Форма для отзывов о компаниях"""
    
    class Meta:
        model = CompanyReview
        fields = [
            'job_title', 'overall_rating', 'work_life_balance', 'salary_benefits',
            'career_growth', 'management', 'title', 'pros', 'cons', 'advice',
            'employment_status', 'is_anonymous'
        ]
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'overall_rating': forms.Select(attrs={'class': 'form-control'}),
            'work_life_balance': forms.Select(attrs={'class': 'form-control'}),
            'salary_benefits': forms.Select(attrs={'class': 'form-control'}),
            'career_growth': forms.Select(attrs={'class': 'form-control'}),
            'management': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Summary of your experience')
            }),
            'pros': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('What did you like about working here?')
            }),
            'cons': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('What could be improved?')
            }),
            'advice': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Any advice for management?')
            }),
            'employment_status': forms.Select(attrs={'class': 'form-control'}),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'job_title': _('Job Title'),
            'overall_rating': _('Overall Rating'),
            'work_life_balance': _('Work/Life Balance'),
            'salary_benefits': _('Salary & Benefits'),
            'career_growth': _('Career Growth'),
            'management': _('Management'),
            'title': _('Review Title'),
            'pros': _('Pros'),
            'cons': _('Cons'),
            'advice': _('Advice to Management'),
            'employment_status': _('Employment Status'),
            'is_anonymous': _('Post Anonymously'),
        }

class InterviewExperienceForm(forms.ModelForm):
    """Форма для опыта собеседований"""
    
    class Meta:
        model = InterviewExperience
        fields = [
            'company', 'job_title', 'process_description', 'difficulty',
            'duration_days', 'interview_questions', 'offer_status', 'recommendations',
            'is_anonymous'
        ]
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'process_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Describe the interview process step by step...')
            }),
            'difficulty': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'max': '5'
            }),
            'duration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'interview_questions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('What questions were you asked during the interview?')
            }),
            'offer_status': forms.Select(attrs={'class': 'form-control'}),
            'recommendations': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Any recommendations for other candidates?')
            }),
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'company': _('Company'),
            'job_title': _('Job Title'),
            'process_description': _('Interview Process'),
            'difficulty': _('Difficulty Level (1-5)'),
            'duration_days': _('Process Duration (days)'),
            'interview_questions': _('Interview Questions'),
            'offer_status': _('Offer Status'),
            'recommendations': _('Recommendations'),
            'is_anonymous': _('Post Anonymously'),
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