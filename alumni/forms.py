from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import Alumni, Company, Job, Event, News, Mentorship, Skill, Connection, Message
from django.core.validators import RegexValidator
from django.contrib.auth import get_user_model

User = get_user_model()

# Валидаторы для полей
phone_validator = RegexValidator(
    regex=r'^\+?1?\d{9,15}$',
    message="Telefon raqami formati: '+999999999'. 15 ta raqamgacha."
)

telegram_validator = RegexValidator(
    regex=r'^@[a-zA-Z0-9_]{5,32}$',
    message="Telegram username @ bilan boshlanishi va 5-32 belgidan iborat bo'lishi kerak (a-z, 0-9, _)."
)

class AlumniRegistrationForm(UserCreationForm):
    """Forma registratsii bitiruvchi"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emailingizni kiriting'
        })
    )
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'To\'liq ismingiz'
        })
    )
    graduation_year = forms.IntegerField(
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bitirgan yilingiz'
        })
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Telefon raqamingiz'
        })
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'name', 'graduation_year', 'phone', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Bu email bilan foydalanuvchi mavjud.')
        return email

    def clean_graduation_year(self):
        year = self.cleaned_data.get('graduation_year')
        if year < 1950 or year > 2030:
            raise ValidationError('To\'g\'ri bitirgan yilni kiriting.')
        return year

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            # Create alumni profile
            Alumni.objects.create(
                user=user,
                name=self.cleaned_data['name'],
                graduation_year=self.cleaned_data['graduation_year'],
                phone=self.cleaned_data.get('phone', '')
            )
        return user

class AlumniProfileForm(forms.ModelForm):
    """Forma tahrirlash profili bitiruvchi"""
    
    class Meta:
        model = Alumni
        fields = [
            'name', 'email', 'phone', 'graduation_year', 'faculty', 'degree',
            'specialization', 'current_position', 'company', 'profession',
            'industry', 'bio', 'linkedin', 'github', 'telegram', 'website',
            'twitter', 'facebook', 'instagram', 'photo', 'resume',
            'skills', 'expertise_areas', 'years_of_experience',
            'is_open_to_opportunities', 'country', 'city',
            'is_mentor', 'is_visible', 'show_contact_info'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'faculty': forms.Select(attrs={'class': 'form-control'}),
            'degree': forms.Select(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'current_position': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'profession': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'O\'zingiz, tajribangiz va yutuqlaringiz haqida...'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'telegram': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '@username'
            }),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'twitter': forms.URLInput(attrs={'class': 'form-control'}),
            'facebook': forms.URLInput(attrs={'class': 'form-control'}),
            'instagram': forms.URLInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
            'resume': forms.FileInput(attrs={'class': 'form-control'}),
            'skills': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'expertise_areas': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Mutaxassislik sohalarini vergul bilan ajrating'
            }),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
            'country': forms.Select(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'is_open_to_opportunities': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_mentor': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_contact_info': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field not required since it comes from User model
        self.fields['email'].required = False

class CompanyForm(forms.ModelForm):
    """Forma qo'shish/tahrirlash kompaniya"""
    
    class Meta:
        model = Company
        fields = ['name', 'industry', 'website', 'description', 'logo', 'email', 'phone', 'address', 'employees_count', 'founded_year']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'industry': forms.Select(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Kompaniya haqida...'
            }),
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employees_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'founded_year': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class JobForm(forms.ModelForm):
    """Forma qo'shish vakansiya"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'company', 'employment_type', 'location', 'remote_work',
            'salary_min', 'salary_max', 'currency', 'description', 'requirements',
            'benefits', 'contact_email', 'application_url', 'expires_at'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'employment_type': forms.Select(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'remote_work': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'salary_min': forms.NumberInput(attrs={'class': 'form-control'}),
            'salary_max': forms.NumberInput(attrs={'class': 'form-control'}),
            'currency': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Vakansiya haqida...'
            }),
            'requirements': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Nomzodga qo\'yiladigan talablar...'
            }),
            'benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Shartlar va bonuslar...'
            }),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'application_url': forms.URLInput(attrs={'class': 'form-control'}),
            'expires_at': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        salary_min = cleaned_data.get('salary_min')
        salary_max = cleaned_data.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise ValidationError('Minimal maosh maksimal maoshdan katta bo\'lmasligi kerak.')
        
        return cleaned_data

class EventForm(forms.ModelForm):
    """Forma qo'shish tadbir"""
    
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'event_type', 'date', 'time', 'location',
            'registration_required', 'max_participants'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5
            }),
            'event_type': forms.Select(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'time': forms.TimeInput(attrs={
                'class': 'form-control',
                'type': 'time'
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_date(self):
        from django.utils import timezone
        date = self.cleaned_data.get('date')
        if date and date < timezone.now().date():
            raise ValidationError('Tadbir sanasi o\'tmishda bo\'lmasligi kerak.')
        return date

class NewsForm(forms.ModelForm):
    """Forma qo'shish yangilik"""
    
    class Meta:
        model = News
        fields = ['title', 'content', 'category', 'image', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'vergul bilan ajrating'
            }),
        }

    def save(self, commit=True):
        news = super().save(commit=False)
        if not news.slug:
            from django.utils.text import slugify
            news.slug = slugify(news.title)
        if commit:
            news.save()
        return news

class MentorshipRequestForm(forms.ModelForm):
    """Forma so'rov mentorlik"""
    
    class Meta:
        model = Mentorship
        fields = ['message', 'expected_duration', 'communication_preference']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Maqsadingizni, mentorlikdan nima kutayotganingizni tavsiflang...'
            }),
            'expected_duration': forms.TextInput(attrs={'class': 'form-control'}),
            'communication_preference': forms.Select(attrs={'class': 'form-control'}),
        }

class MessageForm(forms.ModelForm):
    """Forma xabar"""
    
    class Meta:
        model = Message
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Xabaringizni yozing...'
            }),
        }

class ContactForm(forms.Form):
    """Forma aloqa"""
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ismingiz'
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Emailingiz'
        })
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mavzu'
        })
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 5,
            'placeholder': 'Xabaringiz...'
        })
    )

class SearchForm(forms.Form):
    """Forma qidiruv bitiruvchilar"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ism, familiya, kompaniya bo\'yicha qidiruv...'
        })
    )
    faculty = forms.ChoiceField(
        required=False,
        choices=[('', '--- Barcha fakultetlar ---')] + Alumni.FACULTY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    graduation_year_from = forms.IntegerField(
        required=False,
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bitirgan yildan'
        })
    )
    graduation_year_to = forms.IntegerField(
        required=False,
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Bitirgan yilgacha'
        })
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control'})
    )
    is_mentor = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class JobApplicationForm(forms.ModelForm):
    """Forma ariza ish"""
    
    class Meta:
        model = Message  # Using Message model for job applications temporarily
        fields = ['subject', 'body']
        widgets = {
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Mavzu: [Lavozim nomi] uchun ariza'
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
                'placeholder': 'O\'zingiz va tajribangiz haqida...'
            }),
        }

class ConnectionRequestForm(forms.ModelForm):
    """Forma so'rov bog'lanish"""
    
    class Meta:
        model = Connection
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Qisqacha o\'zingiz haqingizda va nima maqsadda bog\'lanmoqchi ekanligingizni yozing...'
            }),
        }