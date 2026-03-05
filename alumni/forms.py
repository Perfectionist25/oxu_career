
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify

from .models import (
    Alumni,
    Connection,
    Mentorship,
    Message,
    News,
    Skill,
)
from accounts.models import Company
from jobs.models import Job
from events.models import Event
from accounts.forms import CompanyForm as AccountsCompanyForm, QuickCompanyForm as AccountsQuickCompanyForm
from jobs.forms import JobForm as JobsJobForm
from events.forms import EventForm as EventsEventForm

User = get_user_model()


phone_validator = RegexValidator(
    regex=r"^\+?1?\d{9,15}$",
    message=_("Telefon raqami formati: '+999999999'. 15 ta raqamgacha."),
)

telegram_validator = RegexValidator(
    regex=r"^@[a-zA-Z0-9_]{5,32}$",
    message=_("Telegram username @ bilan boshlanishi va 5-32 belgidan iborat bo'lishi kerak (a-z, 0-9, _)."),
)


class AlumniRegistrationForm(UserCreationForm):
    """Forma registratsii bitiruvchi"""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Emailingizni kiriting")}
        ),
    )
    name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("To'liq ismingiz")}
        ),
    )
    graduation_year = forms.IntegerField(
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": _("Bitirgan yilingiz")}
        ),
    )
    phone = forms.CharField(
        max_length=20,
        required=False,
        validators=[phone_validator],
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Telefon raqamingiz")}
        ),
    )


    user_type = forms.CharField(
        initial='student',
        widget=forms.HiddenInput(),
        required=False
    )

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "name",
            "graduation_year",
            "phone",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise ValidationError(_("Bu email bilan foydalanuvchi mavjud."))
        return email

    def clean_graduation_year(self):
        year = self.cleaned_data.get("graduation_year")
        if year is not None:
            if year < 1950 or year > 2030:
                raise ValidationError(_("To'g'ri bitirgan yilni kiriting."))
            return year
        return None

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.user_type = 'student'

        if commit:
            user.save()

            Alumni.objects.create(
                user=user,
                name=self.cleaned_data["name"],
                graduation_year=self.cleaned_data["graduation_year"],
                phone=self.cleaned_data.get("phone", ""),
            )
        return user


class AlumniProfileForm(forms.ModelForm):
    """Forma tahrirlash profili bitiruvchi"""

    class Meta:
        model = Alumni
        fields = [
            "name",
            "email",
            "phone",
            "graduation_year",
            "faculty",
            "degree",
            "specialization",
            "current_position",
            "company",
            "profession",
            "industry",
            "bio",
            "linkedin",
            "github",
            "telegram",
            "website",
            "twitter",
            "facebook",
            "instagram",
            "photo",
            "resume",
            "skills",
            "expertise_areas",
            "years_of_experience",
            "is_open_to_opportunities",
            "country",
            "city",
            "is_mentor",
            "is_visible",
            "show_contact_info",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "graduation_year": forms.NumberInput(attrs={"class": "form-control"}),
            "faculty": forms.Select(attrs={"class": "form-control"}),
            "degree": forms.Select(attrs={"class": "form-control"}),
            "specialization": forms.TextInput(attrs={"class": "form-control"}),
            "current_position": forms.TextInput(attrs={"class": "form-control"}),
            "company": forms.Select(attrs={"class": "form-control"}),
            "profession": forms.TextInput(attrs={"class": "form-control"}),
            "industry": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("O'zingiz, tajribangiz va yutuqlaringiz haqida..."),
                }
            ),
            "linkedin": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("https://linkedin.com/in/username"),
                }
            ),
            "github": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("https://github.com/username"),
                }
            ),
            "telegram": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("@username")}
            ),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "twitter": forms.URLInput(attrs={"class": "form-control"}),
            "facebook": forms.URLInput(attrs={"class": "form-control"}),
            "instagram": forms.URLInput(attrs={"class": "form-control"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "resume": forms.FileInput(attrs={"class": "form-control"}),
            "skills": forms.SelectMultiple(attrs={"class": "form-control"}),
            "expertise_areas": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Mutaxassislik sohalarini vergul bilan ajrating"),
                }
            ),
            "years_of_experience": forms.NumberInput(attrs={"class": "form-control"}),
            "country": forms.Select(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "is_open_to_opportunities": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_mentor": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "is_visible": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "show_contact_info": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make email field not required since it comes from User model
        self.fields["email"].required = False


        self.fields["company"].queryset = Company.objects.filter(is_active=True)



CompanyForm = AccountsCompanyForm
QuickCompanyForm = AccountsQuickCompanyForm
JobForm = JobsJobForm
EventForm = EventsEventForm


class NewsForm(forms.ModelForm):
    """Forma qo'shish yangilik"""

    class Meta:
        model = News
        fields = ["title", "content", "category", "image", "tags"]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "content": forms.Textarea(attrs={"class": "form-control", "rows": 6}),
            "category": forms.Select(attrs={"class": "form-control"}),
            "image": forms.FileInput(attrs={"class": "form-control"}),
            "tags": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("vergul bilan ajrating")}
            ),
        }

    def save(self, commit=True):
        news = super().save(commit=False)
        if not news.slug:
            news.slug = slugify(news.title)
        if commit:
            news.save()
        return news


class MentorshipRequestForm(forms.ModelForm):
    """Forma so'rov mentorlik"""

    class Meta:
        model = Mentorship
        fields = ["message", "expected_duration", "communication_preference"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Maqsadingizni, mentorlikdan nima kutayotganingizni tavsiflang..."),
                }
            ),
            "expected_duration": forms.TextInput(attrs={"class": "form-control"}),
            "communication_preference": forms.Select(attrs={"class": "form-control"}),
        }


class MessageForm(forms.ModelForm):
    """Forma xabar"""

    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "subject": forms.TextInput(attrs={"class": "form-control"}),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Xabaringizni yozing..."),
                }
            ),
        }


class ContactForm(forms.Form):
    """Forma aloqa"""

    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Ismingiz")}
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={"class": "form-control", "placeholder": _("Emailingiz")}
        )
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": _("Mavzu")}),
    )
    message = forms.CharField(
        widget=forms.Textarea(
            attrs={"class": "form-control", "rows": 5, "placeholder": _("Xabaringiz...")}
        )
    )


class SearchForm(forms.Form):
    """Forma qidiruv bitiruvchilar"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Ism, familiya, kompaniya bo'yicha qidiruv..."),
            }
        ),
    )
    faculty = forms.ChoiceField(
        required=False,
        choices=[("", _("--- Barcha fakultetlar ---"))] + list(Alumni.FACULTY_CHOICES),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    graduation_year_from = forms.IntegerField(
        required=False,
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": _("Bitirgan yildan")}
        ),
    )
    graduation_year_to = forms.IntegerField(
        required=False,
        min_value=1950,
        max_value=2030,
        widget=forms.NumberInput(
            attrs={"class": "form-control", "placeholder": _("Bitirgan yilgacha")}
        ),
    )
    skills = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )
    is_mentor = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )


class JobApplicationForm(forms.ModelForm):
    """Forma ariza ish"""

    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "subject": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Mavzu: [Lavozim nomi] uchun ariza"),
                }
            ),
            "body": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": _("O'zingiz va tajribangiz haqida..."),
                }
            ),
        }


class ConnectionRequestForm(forms.ModelForm):
    """Forma so'rov bog'lanish"""

    class Meta:
        model = Connection
        fields = ["message"]
        widgets = {
            "message": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _(
                        "Qisqacha o'zingiz haqingizda va nima maqsadda bog'lanmoqchi "
                        "ekanligingizni yozing..."
                    ),
                }
            ),
        }