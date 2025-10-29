from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

User = get_user_model()

from .models import UserSkill


class UserRegistrationForm(UserCreationForm):
    """Form for user registration"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'elektron@pochta.uz'
        })
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ismingiz')
        })
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Familyangiz')
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPE_CHOICES if hasattr(User, 'USER_TYPE_CHOICES') else [],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label=_('Hisob turi'),
        initial='student'
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Foydalanuvchi nomi')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field not in ['user_type']:
                self.fields[field].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(_('Ushbu email allaqachon ro\'yxatdan o\'tgan.'))
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if hasattr(user, 'user_type'):
            user.user_type = self.cleaned_data.get('user_type', 'student')
        
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    """Form for updating user information"""
    
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = User
        fields = [
            'phone_number', 'bio', 'date_of_birth', 'country', 'city', 'address',
            'organization', 'position', 'website', 'linkedin', 'github',
            'avatar', 'resume', 'email_notifications', 'job_alerts', 'newsletter'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('O\'zingiz haqingizda qisqacha ma\'lumot...')
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+998 XX XXX XX XX'
            }),
            'country': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Shahar')
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('To\'liq manzil')
            }),
            'organization': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Tashkilot nomi')
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Lavozimingiz')
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.uz'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'email_notifications': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'job_alerts': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'newsletter': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'phone_number': _('Telefon raqami'),
            'bio': _('Bio'),
            'date_of_birth': _('Tug\'ilgan sana'),
            'country': _('Mamlakat'),
            'city': _('Shahar'),
            'address': _('Manzil'),
            'organization': _('Tashkilot'),
            'position': _('Lavozim'),
            'website': _('Veb sayt'),
            'linkedin': _('LinkedIn'),
            'github': _('GitHub'),
            'avatar': _('Profil rasmi'),
            'resume': _('Rezyume'),
            'email_notifications': _('Email bildirishnomalari'),
            'job_alerts': _('Ish bildirishnomalari'),
            'newsletter': _('Yangiliklar'),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        # Add phone number validation if needed
        return phone_number


class SkillForm(forms.ModelForm):
    """Form for user skills"""
    
    class Meta:
        model = UserSkill
        fields = ['skill', 'proficiency', 'years_of_experience', 'is_primary']
        widgets = {
            'skill': forms.Select(attrs={'class': 'form-select'}),
            'proficiency': forms.Select(attrs={'class': 'form-select'}),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 50
            }),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'skill': _('Ko\'nikma'),
            'proficiency': _('Bilim darajasi'),
            'years_of_experience': _('Tajriba yillari'),
            'is_primary': _('Asosiy ko\'nikma'),
        }
