
from django import forms
from django.contrib.admin.forms import AdminAuthenticationForm
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
import re

from .captcha import ensure_login_captcha, rotate_login_captcha, validate_login_captcha
from .models import *


def build_login_captcha_field(widget_attrs=None):
    attrs = {
        "class": "form-control",
        "placeholder": _("Enter the answer"),
        "autocomplete": "off",
    }
    if widget_attrs:
        attrs.update(widget_attrs)

    return forms.IntegerField(
        label=_("Security question"),
        min_value=0,
        widget=forms.NumberInput(attrs=attrs),
        error_messages={
            "required": _("Please solve the security question."),
            "invalid": _("Enter a valid number."),
        },
    )


class LoginCaptchaMixin:
    captcha_widget_attrs = None

    def __init__(self, *args, request=None, **kwargs):
        if request is None and args and hasattr(args[0], "session") and hasattr(args[0], "META"):
            request = args[0]
        self.request = request
        super().__init__(*args, **kwargs)
        if "captcha_answer" not in self.fields:
            self.fields["captcha_answer"] = build_login_captcha_field(self.captcha_widget_attrs)
        question = ensure_login_captcha(self.request)
        self.fields["captcha_answer"].label = question

    def _rotate_captcha_field(self):
        question = rotate_login_captcha(self.request)
        self.fields["captcha_answer"].label = question
        self.data = self.data.copy()
        self.data.pop("captcha_answer", None)

    def clean_captcha_answer(self):
        answer = self.cleaned_data.get("captcha_answer")
        if not validate_login_captcha(self.request, answer):
            raise forms.ValidationError(_("Incorrect answer to the security question."))
        return answer


class EmployerLoginForm(LoginCaptchaMixin, forms.Form):
    captcha_answer = build_login_captcha_field()
    username = forms.CharField(
        label=_("Login or Email"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": _("Username"),
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control form-control-lg",
                "placeholder": _("Your password"),
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password")

        if not username or not password:
            return cleaned_data

        user = authenticate(self.request, username=username, password=password)
        if user is None or not user.is_employer:
            self._rotate_captcha_field()
            raise forms.ValidationError(
                _("Invalid credentials or you are not authorized as an employer.")
            )

        self.user = user
        return cleaned_data


class AdminLoginForm(LoginCaptchaMixin, forms.Form):
    captcha_answer = build_login_captcha_field()
    username = forms.CharField(
        label=_("Username"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your username"),
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Enter your password"),
            }
        ),
    )
    remember = forms.BooleanField(
        label=_("Remember me"),
        required=False,
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"}),
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get("username", "").strip()
        password = cleaned_data.get("password")

        if not username or not password:
            raise forms.ValidationError(_("Please enter your username and password."))

        user = authenticate(self.request, username=username, password=password)
        if user is None:
            self._rotate_captcha_field()
            raise forms.ValidationError(_("Invalid username or password."))

        if user.user_type not in ["admin", "main_admin"]:
            self._rotate_captcha_field()
            raise forms.ValidationError(_("You are not authorized to access the admin panel."))

        self.user = user
        return cleaned_data


class CaptchaAdminAuthenticationForm(LoginCaptchaMixin, AdminAuthenticationForm):
    captcha_widget_attrs = {
        "class": "vIntegerField",
        "placeholder": _("Enter the answer"),
        "autocomplete": "off",
    }
    captcha_answer = build_login_captcha_field(captcha_widget_attrs)

    def __init__(self, request=None, *args, **kwargs):
        AdminAuthenticationForm.__init__(self, request=request, *args, **kwargs)
        self.request = request
        if "captcha_answer" not in self.fields:
            self.fields["captcha_answer"] = build_login_captcha_field(self.captcha_widget_attrs)
        question = ensure_login_captcha(self.request)
        self.fields["captcha_answer"].label = question

    def clean(self):
        try:
            return AdminAuthenticationForm.clean(self)
        except forms.ValidationError:
            self._rotate_captcha_field()
            raise


class CustomUserCreationForm(UserCreationForm):
    """Базовая форма создания пользователя"""
    email = forms.EmailField(required=True, help_text=_('Required. Enter a valid email address.'))
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    class Meta:
        model = CustomUser
        fields = ["username", "email", "first_name", "last_name", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_('A user with this email already exists.'))
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(_('A user with this username already exists.'))
        return username


class EmployerRegistrationForm(CustomUserCreationForm):
    """Форма регистрации работодателя для админа"""
    terms_accept = forms.BooleanField(
        required=True,
        label=_("I accept the terms and conditions"),
        error_messages={'required': _("You must accept the terms and conditions.")},
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    phone_number = forms.CharField(
        max_length=32,
        required=True,
        label=_("Phone Number"),
        help_text=_("Phone number with country code (e.g., +998901234567)"),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta(CustomUserCreationForm.Meta):
        fields = CustomUserCreationForm.Meta.fields + ["phone_number"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            if field_name not in ['terms_accept']:
                if hasattr(field, 'widget') and hasattr(field.widget, 'attrs'):
                    if field_name in ['password1', 'password2']:
                        field.widget.attrs.update({'class': 'form-control'})
                    elif field_name != 'terms_accept':
                        field.widget.attrs.update({'class': 'form-control'})

    def clean_phone_number(self):
        phone = self.cleaned_data.get('phone_number')

        if phone and not re.match(r'^\+?[1-9]\d{1,14}$', phone):
            raise forms.ValidationError(_('Enter a valid phone number with country code.'))
        return phone


class CompanyForm(forms.ModelForm):
    """Форма для создания/редактирования компании"""

    class Meta:
        model = Company
        fields = [
            'name',
            'company_type',
            'company_size',
            'description',
            'short_description',
            'logo',
            'email',
            'phone',
            'website',
            'region',
            'city',
            'address',
            'linkedin',
            'telegram',
            'facebook',
            'instagram',
            'industry',
            'tags',
            'founded_year',
            'mission',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Company name...')
            }),
            'company_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('LLC, Corporation, Startup, etc.')
            }),
            'company_size': forms.Select(attrs={
                'class': 'form-select'
            }),
            'description': forms.Textarea(attrs={
                'rows': 5,
                'class': 'form-control',
                'placeholder': _('Detailed company description...')
            }),
            'short_description': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Brief company description for listings...')
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'region': forms.Select(attrs={
                'class': 'form-select'
            }),
            'city': forms.Select(attrs={
                'class': 'form-select'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'telegram': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control'
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Technology, Education, Finance, etc.')
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('tech, startup, education, etc.')
            }),
            'founded_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': 2100
            }),
            'mission': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Company mission and values...')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['region'].choices = [('', _('Select region...'))] + REGIONS
        self.fields['city'].choices = [('', _('Select city...'))] + CITIES


        for field_name in ['company_size', 'description', 'short_description', 'logo',
                          'email', 'phone', 'website', 'region', 'city', 'address',
                          'linkedin', 'telegram', 'facebook', 'instagram', 'industry',
                          'tags', 'founded_year', 'mission']:
            self.fields[field_name].required = False

    def clean(self):
        cleaned_data = super().clean()
        name = cleaned_data.get('name')


        if name:
            query = Company.objects.filter(name__iexact=name)
            if self.instance.pk:
                query = query.exclude(pk=self.instance.pk)
            if query.exists():
                self.add_error('name', _('A company with this name already exists'))


        year = cleaned_data.get('founded_year')
        if year:
            current_year = timezone.now().year
            if year < 1800 or year > current_year:
                self.add_error('founded_year', _('Please enter a valid year'))

        return cleaned_data


class AdminCompanyForm(CompanyForm):

    legal_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    tax_id = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    cover_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': 'form-control'}))
    sub_industry = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    vision = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}))
    country = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta(CompanyForm.Meta):

        fields = CompanyForm.Meta.fields

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['legal_name'].widget.attrs.update({'class': 'form-control'})
        self.fields['tax_id'].widget.attrs.update({'class': 'form-control'})
        self.fields['cover_image'].widget.attrs.update({'class': 'form-control'})
        self.fields['sub_industry'].widget.attrs.update({'class': 'form-control'})
        self.fields['vision'].widget.attrs.update({'class': 'form-control', 'rows': 3})
        self.fields['country'].widget.attrs.update({'class': 'form-control'})


class AdminEmployerProfileForm(forms.ModelForm):
    """Форма профиля работодателя для админа (расширенная)"""
    verification_document = forms.FileField(
        required=False,
        label=_("Verification Document"),
        widget=forms.FileInput(attrs={
            'class': 'form-control'
        }),
        help_text=_("Document proving employment/ownership")
    )
    receive_company_notifications = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Receive Company Notifications"),
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    department = forms.CharField(
        required=False,
        max_length=100,
        label=_("Department"),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Department or division')
        })
    )

    class Meta:
        model = EmployerProfile
        fields = [
            "job_title", "professional_bio", "phone_number",
            "preferred_contact_method", "verification_document",
            "receive_company_notifications", "department"
        ]
        widgets = {
            'job_title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Current professional position')
            }),
            'professional_bio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': _('Professional background and experience')
            }),
            'phone_number': forms.TextInput(attrs={
                'class': 'form-control'
            }),
            'preferred_contact_method': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name in ['job_title', 'professional_bio', 'phone_number',
                          'preferred_contact_method', 'verification_document',
                          'receive_company_notifications', 'department']:
            self.fields[field_name].required = False


class QuickCompanyForm(forms.ModelForm):
    """Упрощенная форма для быстрого создания компании"""

    class Meta:
        model = Company
        fields = ['name', 'description', 'industry', 'region', 'city']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Company name...')}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': _('Company description...')}),
            'industry': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Industry...')}),
            'region': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['region'].choices = [('', _('Select region...'))] + REGIONS
        self.fields['city'].choices = [('', _('Select city...'))] + CITIES


        for field_name in self.fields:
            self.fields[field_name].required = False


class CompanyDocumentForm(forms.ModelForm):
    """Форма для загрузки документов компании"""
    class Meta:
        model = CompanyDocument
        fields = ['document_type', 'title', 'file']
        widgets = {
            'document_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Document title or description')
            }),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudentProfileForm(forms.ModelForm):
    """Форма профиля студента"""
    class Meta:
        model = StudentProfile
        fields = [
            "student_id",
            "avatar",
            "faculty",
            "specialty",
            "education_level",
            "graduation_year",
            "desired_position",
            "desired_salary",
            "work_type",
            "website",
            "linkedin",
            "github",
            "bio",
        ]
        widgets = {
            'student_id': forms.TextInput(attrs={'class': 'form-control'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'faculty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Faculty or department')
            }),
            'specialty': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Field of study or specialization')
            }),
            'education_level': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Bachelor, Master, PhD, etc.')
            }),
            'work_type': forms.Select(attrs={'class': 'form-select'}),
            'desired_salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Expected salary')
            }),
            'bio': forms.Textarea(attrs={
                'rows': 4,
                'class': 'form-control',
                'placeholder': _('About yourself, skills, experience...')
            }),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1900,
                'max': 2100
            }),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'linkedin': forms.URLInput(attrs={'class': 'form-control'}),
            'github': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Student ID is provided externally and must remain read-only for students.
        self.fields["student_id"].disabled = True


class AdminProfileForm(forms.ModelForm):
    """Форма создания администратора"""
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        label=_("Password")
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        required=True,
        label=_("Confirm Password")
    )
    user_type = forms.ChoiceField(
        choices=[('admin', _('Admin')), ('main_admin', _('Main Admin'))],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='admin',
        required=True
    )

    class Meta:
        model = AdminProfile
        fields = [
            "can_manage_students",
            "can_manage_employers",
            "can_manage_companies",
            "can_manage_jobs",
            "can_manage_resumes",
            "can_view_statistics",
        ]
        widgets = {
            'can_manage_students': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_employers': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_companies': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_jobs': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_manage_resumes': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'can_view_statistics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(_("Passwords don't match"))
        return password2

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username and CustomUser.objects.filter(username=username).exists():
            raise forms.ValidationError(_("This username already exists"))
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError(_("This email already exists"))
        return email


class UserUpdateForm(forms.ModelForm):
    """Форма обновления данных пользователя"""


    full_name = forms.CharField(
        label=_("Full name"),
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = [

            "avatar",
            "email",
            "phone_number",
            "date_of_birth",
            "bio",
            "city",
            "address",
            "telegram",
        ]
        widgets = {
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'telegram': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        if self.instance and hasattr(self.instance, "full_name"):
            self.fields["full_name"].initial = self.instance.full_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_('This email is already in use by another user.'))
        return email


class PasswordChangeFormCustom(forms.Form):
    """Кастомная форма смены пароля"""
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label=_("Current Password")
    )
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label=_("New Password"),
        min_length=8
    )
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label=_("Confirm New Password")
    )

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get("new_password1")
        new_password2 = cleaned_data.get("new_password2")

        if new_password1 and new_password2 and new_password1 != new_password2:
            self.add_error('new_password2', _("Passwords don't match"))

        return cleaned_data


class EmployerProfileForm(forms.ModelForm):
    """Форма для личного профиля работодателя"""
    class Meta:
        model = EmployerProfile
        fields = ["job_title", "professional_bio", "phone_number", "preferred_contact_method"]
        widgets = {
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'professional_bio': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'preferred_contact_method': forms.Select(attrs={'class': 'form-select'}),
        }


class StudentUserReadonlyNameForm(forms.ModelForm):
    """
    Форма для обновления данных пользователя студентом.
    ФИО (full_name) показываем, но не даём менять.
    Остальные поля можно добавлять позже, если нужно.
    """
    full_name = forms.CharField(
        label=_("Full name"),
        required=False,
        disabled=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = CustomUser
        fields = ["email", "phone_number"]
        widgets = {
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["full_name"].initial = getattr(self.instance, "full_name", "") or self.instance.get_full_name()

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError(_("This email is already in use by another user."))
        return email
