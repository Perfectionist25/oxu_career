from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Company, EmployerProfile, Job, JobApplication, CandidateNote, Interview, CompanyReview

class CompanyForm(forms.ModelForm):
    """Форма для компании"""
    
    class Meta:
        model = Company
        fields = [
            'name', 'description', 'website', 'logo', 'industry', 
            'company_size', 'founded_year', 'headquarters',
            'contact_email', 'contact_phone', 'linkedin', 'twitter', 'facebook'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Company name')}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Company description and activities...')
            }),
            'website': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com'}),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'company_size': forms.Select(attrs={'class': 'form-control'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control', 'min': '1900', 'max': '2024'}),
            'headquarters': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Headquarters location')}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://linkedin.com/company/...'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://twitter.com/...'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://facebook.com/...'}),
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
        }

class EmployerProfileForm(forms.ModelForm):
    """Форма для профиля работодателя"""
    
    class Meta:
        model = EmployerProfile
        fields = ['position', 'department', 'phone']
        widgets = {
            'position': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Your position')}),
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Department')}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+998 XX XXX-XX-XX'}),
        }
        labels = {
            'position': _('Position'),
            'department': _('Department'),
            'phone': _('Phone'),
        }

class JobForm(forms.ModelForm):
    """Форма для вакансии"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'responsibilities', 'benefits',
            'employment_type', 'experience_level', 'location', 'remote_work',
            'salary_min', 'salary_max', 'currency', 'hide_salary',
            'application_url', 'contact_email', 'skills_required', 'expires_at'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Job title')}),
            'description': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Detailed job description...')
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Candidate requirements...')
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Job responsibilities...')
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3,
                'placeholder': _('Benefits and perks...')
            }),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Tashkent, Uzbekistan')}),
            'remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '100000'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '100000'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'hide_salary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'application_url': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://...'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'skills_required': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Python, Django, JavaScript, ...')
            }),
            'expires_at': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }
        labels = {
            'title': _('Job Title'),
            'description': _('Job Description'),
            'requirements': _('Requirements'),
            'responsibilities': _('Responsibilities'),
            'benefits': _('Benefits'),
            'employment_type': _('Employment Type'),
            'experience_level': _('Experience Level'),
            'location': _('Location'),
            'remote_work': _('Remote Work Available'),
            'salary_min': _('Minimum Salary'),
            'salary_max': _('Maximum Salary'),
            'currency': _('Currency'),
            'hide_salary': _('Hide Salary'),
            'application_url': _('Application URL'),
            'contact_email': _('Contact Email'),
            'skills_required': _('Required Skills'),
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
        fields = ['cover_letter', 'expected_salary', 'cv']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 5,
                'placeholder': _('Write your cover letter...')
            }),
            'expected_salary': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '100000'}),
            'cv': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'cover_letter': _('Cover Letter'),
            'expected_salary': _('Expected Salary'),
            'cv': _('Resume/CV'),
        }

class CandidateNoteForm(forms.ModelForm):
    """Форма для заметок о кандидате"""
    
    class Meta:
        model = CandidateNote
        fields = ['note', 'is_private', 'job']
        widgets = {
            'note': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Add notes about the candidate...')
            }),
            'is_private': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'job': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'note': _('Note'),
            'is_private': _('Private Note'),
            'job': _('Related Job'),
        }

class InterviewForm(forms.ModelForm):
    """Форма для собеседования"""
    
    class Meta:
        model = Interview
        fields = ['scheduled_date', 'duration', 'location', 'notes', 'interviewer']
        widgets = {
            'scheduled_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration': forms.NumberInput(attrs={'class': 'form-control', 'min': '15', 'max': '480'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Interview location or Zoom link')}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'interviewer': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'scheduled_date': _('Scheduled Date'),
            'duration': _('Duration (minutes)'),
            'location': _('Location'),
            'notes': _('Notes'),
            'interviewer': _('Interviewer'),
        }

class CompanyReviewForm(forms.ModelForm):
    """Форма для отзыва о компании"""
    
    class Meta:
        model = CompanyReview
        fields = ['rating', 'title', 'review', 'pros', 'cons', 'is_anonymous']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Review title')}),
            'review': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': _('Share your experience working at this company...')
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
            'is_anonymous': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'rating': _('Rating'),
            'title': _('Title'),
            'review': _('Review'),
            'pros': _('Pros'),
            'cons': _('Cons'),
            'is_anonymous': _('Post Anonymously'),
        }

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
    industry = forms.MultipleChoiceField(
        required=False,
        choices=Company.INDUSTRY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    remote_work = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

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
            'placeholder': _('Additional notes...')
        })
    )