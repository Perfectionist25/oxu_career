from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CustomUser, EmployerProfile, StudentProfile, AdminProfile

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