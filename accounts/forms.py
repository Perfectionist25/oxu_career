from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import *

class EmployerRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

class EmployerProfileForm(forms.ModelForm):
    class Meta:
        model = EmployerProfile
        fields = [
            'company_name', 'company_logo', 'company_description',
            'company_email', 'company_phone', 'company_website',
            'company_linkedin', 'company_telegram', 'company_size',
            'industry', 'founded_year', 'headquarters'
        ]

class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'desired_position', 'desired_salary', 'work_type'
        ]

class AdminProfileForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    email = forms.EmailField()
    first_name = forms.CharField(max_length=30)
    last_name = forms.CharField(max_length=30)
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = AdminProfile
        fields = [
            'username', 'email', 'first_name', 'last_name', 'password1', 'password2',
            'can_manage_students', 'can_manage_employers', 'can_manage_jobs',
            'can_manage_resumes', 'can_view_statistics'
        ]

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Parollar mos kelmadi"))
        return password2

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'phone_number', 'email', 'bio', 'avatar']



class JobForm(forms.ModelForm):
    """Форма для создания/редактирования вакансии"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'responsibilities',
            'job_type', 'experience_level', 'location', 'is_remote',
            'salary_min', 'salary_max', 'salary_currency',
            'skills_required', 'application_deadline'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: Python Dasturchi'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ishning umumiy tavsifi...'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Nomzodga qo\'yiladigan talablar...'
            }),
            'responsibilities': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Ishchi majburiyatlari...'
            }),
            'job_type': forms.Select(attrs={'class': 'form-control'}),
            'experience_level': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Masalan: Toshkent shahri'
            }),
            'salary_min': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minimal maosh'
            }),
            'salary_max': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Maksimal maosh'
            }),
            'salary_currency': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('UZS', 'Soʻm'),
                ('USD', 'USD'),
            ]),
            'skills_required': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Ko\'nikmalarni vergul bilan ajrating. Masalan: Python, Django, PostgreSQL'
            }),
            'application_deadline': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
        labels = {
            'title': _('Lavozim nomi'),
            'description': _('Ish tavsifi'),
            'requirements': _('Talablar'),
            'responsibilities': _('Majburiyatlar'),
            'job_type': _('Ish turi'),
            'experience_level': _('Tajriba darajasi'),
            'location': _('Manzil'),
            'is_remote': _('Uzoq ish'),
            'salary_min': _('Minimal maosh'),
            'salary_max': _('Maksimal maosh'),
            'salary_currency': _('Valyuta'),
            'skills_required': _('Talab qilinadigan ko\'nikmalar'),
            'application_deadline': _('Ariza muddati'),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(_("Minimal maosh maksimal maoshdan katta bo'lishi mumkin emas"))
        
        return cleaned_data
