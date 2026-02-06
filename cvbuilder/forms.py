from __future__ import annotations

from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import (
    CV,
    Experience,
    Education,
    Skill,
    Language,
    CVTemplate
)


# ---------- helpers ----------

BOOTSTRAP_CONTROL = "form-control"
BOOTSTRAP_SELECT = "form-select"
BOOTSTRAP_CHECK = "form-check-input"


def _add_class(field: forms.Field, css_class: str) -> None:
    existing = field.widget.attrs.get("class", "")
    field.widget.attrs["class"] = (existing + " " + css_class).strip()


def _set_placeholder(field: forms.Field, text: str) -> None:
    field.widget.attrs.setdefault("placeholder", text)


# ---------- CV ----------

class CVForm(forms.ModelForm):
    """Полная форма резюме под твою модель CV."""

    class Meta:
        model = CV
        fields = [
            # meta
            "title",
            "template",
            "status",

            # personal
            "full_name",
            "photo",
            "birth_date",
            "gender",
            "marital_status",
            "nationality",

            # contacts
            "email",
            "phone",
            "phone_secondary",
            "region",
            "city",
            "address",

            # career
            "desired_position",
            "employment_type",
            "salary_expectation",
            "salary_currency",
            "summary",

            # documents
            "driver_license",
            "driver_license_category",
            "military_service",

            # links
            "linkedin",
            "github",
            "portfolio",
        ]

        widgets = {
            "title": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "template": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),

            "full_name": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "photo": forms.ClearableFileInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "birth_date": forms.DateInput(attrs={"class": BOOTSTRAP_CONTROL, "type": "date"}),
            "gender": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "marital_status": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "nationality": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),

            "email": forms.EmailInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "phone": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "phone_secondary": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            # IMPORTANT: region is choices -> Select
            "region": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "city": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "address": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 2}),

            "desired_position": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "employment_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "salary_expectation": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "min": "0"}),
            "salary_currency": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "summary": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 4}),

            "passport_series": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "passport_number": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "tin": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "driver_license": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "driver_license_category": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "military_service": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 3}),

            "linkedin": forms.URLInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "github": forms.URLInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "portfolio": forms.URLInput(attrs={"class": BOOTSTRAP_CONTROL}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "template" in self.fields:
            self.fields["template"].queryset = CVTemplate.objects.filter(is_active=True)

        # placeholders (чтобы красиво выглядело)
        _set_placeholder(self.fields["title"], _("My Resume / Backend Developer"))
        _set_placeholder(self.fields["full_name"], _("Full Name"))
        _set_placeholder(self.fields["email"], _("name@example.com"))
        _set_placeholder(self.fields["phone"], _("+998 XX XXX XX XX"))
        _set_placeholder(self.fields["phone_secondary"], _("Optional"))
        _set_placeholder(self.fields["city"], _("City"))
        _set_placeholder(self.fields["address"], _("Street, house, etc."))
        _set_placeholder(self.fields["desired_position"], _("Desired Position"))
        _set_placeholder(self.fields["salary_expectation"], _("Salary in UZS"))
        _set_placeholder(self.fields["salary_currency"], _("UZS"))
        _set_placeholder(self.fields["summary"], _("Short professional summary..."))
        _set_placeholder(self.fields["driver_license_category"], _("B"))
        _set_placeholder(self.fields["linkedin"], _("https://linkedin.com/in/..."))
        _set_placeholder(self.fields["github"], _("https://github.com/..."))
        _set_placeholder(self.fields["portfolio"], _("https://..."))

        optional = [
            "template",
            "photo",
            "birth_date",
            "gender",
            "marital_status",
            "phone_secondary",
            "salary_expectation",
            "driver_license_category",
            "military_service",
            "linkedin",
            "github",
            "portfolio",
        ]
        for name in optional:
            if name in self.fields:
                self.fields[name].required = False

        # salary_currency: оставим default UZS если пусто
        self.fields["salary_currency"].required = False

        # driver_license_category логично требовать только если driver_license=True
        self.fields["driver_license_category"].required = False

    def clean_birth_date(self):
        birth_date = self.cleaned_data.get("birth_date")
        if birth_date and birth_date > timezone.localdate():
            raise ValidationError(_("Birth date cannot be in the future."))
        return birth_date

    def clean(self):
        cleaned = super().clean()
        driver_license = cleaned.get("driver_license")
        driver_license_category = cleaned.get("driver_license_category")

        if driver_license and not driver_license_category:
            self.add_error("driver_license_category", _("Please specify license category (e.g., B)."))

        # Если currency пустая — ставим UZS
        if cleaned.get("salary_currency"):
            cleaned["salary_currency"] = cleaned["salary_currency"].upper().strip()

        return cleaned


# ---------- Experience ----------

class ExperienceForm(forms.ModelForm):
    """Опыт работы (Experience) с логикой дат."""

    class Meta:
        model = Experience
        fields = [
            "company",
            "position",
            "employment_type",
            "start_date",
            "end_date",
            "is_current",
            "company_location",
            "description",
            "technologies",
            "achievements",
        ]
        widgets = {
            "company": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "position": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "employment_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "start_date": forms.DateInput(attrs={"class": BOOTSTRAP_CONTROL, "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": BOOTSTRAP_CONTROL, "type": "date"}),
            "is_current": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
            "company_location": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "description": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 3}),
            "technologies": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "achievements": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _set_placeholder(self.fields["company"], _("Company/Organization"))
        _set_placeholder(self.fields["position"], _("Position"))
        _set_placeholder(self.fields["company_location"], _("City, Country"))
        _set_placeholder(self.fields["technologies"], _("Django, PostgreSQL, Docker..."))

        # optional в модели
        for name in ["end_date", "company_location", "technologies", "achievements"]:
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("start_date")
        end = cleaned.get("end_date")
        is_current = cleaned.get("is_current")

        if start and start > timezone.localdate():
            self.add_error("start_date", _("Start date cannot be in the future."))

        if is_current:
            # если текущая работа — end_date должен быть пустой
            if end:
                self.add_error("end_date", _("End date must be empty for current position."))
        else:
            # если не текущая — end_date обязателен
            if start and not end:
                self.add_error("end_date", _("Please set an end date or mark as current."))
            if start and end and end < start:
                self.add_error("end_date", _("End date cannot be earlier than start date."))

        return cleaned


# ---------- Education ----------

class EducationForm(forms.ModelForm):
    """Образование (Education) под твою модель с годами."""

    class Meta:
        model = Education
        fields = [
            "institution",
            "degree",
            "education_level",
            "field_of_study",
            "faculty",
            "start_year",
            "graduation_year",
            "gpa",
            "honors",
            "diploma_number",
            "description",
        ]
        widgets = {
            "institution": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "degree": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "education_level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "field_of_study": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "faculty": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "start_year": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "min": "1900", "max": "2100"}),
            "graduation_year": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "min": "1900", "max": "2100"}),
            "gpa": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "step": "0.01", "min": "0", "max": "5"}),
            "honors": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "diploma_number": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "description": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        _set_placeholder(self.fields["institution"], _("University/College"))
        _set_placeholder(self.fields["degree"], _("Bachelor / Master / Diploma"))
        _set_placeholder(self.fields["field_of_study"], _("Major / Specialty"))
        _set_placeholder(self.fields["faculty"], _("Optional"))
        _set_placeholder(self.fields["honors"], _("Optional"))
        _set_placeholder(self.fields["diploma_number"], _("Optional"))

        # optional в модели
        for name in ["faculty", "graduation_year", "gpa", "honors", "diploma_number", "description"]:
            self.fields[name].required = False

    def clean(self):
        cleaned = super().clean()
        start_year = cleaned.get("start_year")
        grad_year = cleaned.get("graduation_year")

        current_year = timezone.localdate().year

        if start_year and (start_year < 1900 or start_year > current_year + 1):
            self.add_error("start_year", _("Start year looks invalid."))

        if grad_year:
            if grad_year < 1900 or grad_year > current_year + 10:
                self.add_error("graduation_year", _("Graduation year looks invalid."))
            if start_year and grad_year < start_year:
                self.add_error("graduation_year", _("Graduation year cannot be earlier than start year."))

        return cleaned


# ---------- Skill ----------

class SkillForm(forms.ModelForm):
    """Навыки (Skill) под твою модель."""

    class Meta:
        model = Skill
        fields = ["name", "category", "level", "years_of_experience", "description", "last_used"]
        widgets = {
            "name": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "category": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "years_of_experience": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "min": "0", "max": "50"}),
            "description": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 2}),
            "last_used": forms.NumberInput(attrs={"class": BOOTSTRAP_CONTROL, "min": "1900", "max": "2100"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_placeholder(self.fields["name"], _("Skill name"))
        _set_placeholder(self.fields["category"], _("technical / soft / language"))
        _set_placeholder(self.fields["years_of_experience"], _("Optional"))
        _set_placeholder(self.fields["last_used"], _("Optional, year"))

        # optional в модели
        for name in ["years_of_experience", "description", "last_used"]:
            self.fields[name].required = False

    def clean_last_used(self):
        last_used = self.cleaned_data.get("last_used")
        if last_used:
            current_year = timezone.localdate().year
            if last_used > current_year:
                raise ValidationError(_("Last used cannot be in the future."))
        return last_used


# ---------- Language ----------

class LanguageForm(forms.ModelForm):
    """Языки (Language) под твою модель."""

    class Meta:
        model = Language
        fields = ["name", "level", "certificate_type", "certificate_score", "is_native"]
        widgets = {
            "name": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "level": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "certificate_type": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),
            "certificate_score": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "is_native": forms.CheckboxInput(attrs={"class": BOOTSTRAP_CHECK}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_placeholder(self.fields["name"], _("English / Russian / Uzbek"))
        _set_placeholder(self.fields["certificate_score"], _("IELTS 7.0, TOEFL 95..."))

        # optional в модели
        self.fields["certificate_score"].required = False

    def clean(self):
        cleaned = super().clean()
        cert_type = cleaned.get("certificate_type")
        cert_score = cleaned.get("certificate_score")

        # если сертификата нет — score должен быть пустой
        if cert_type == "none" and cert_score:
            self.add_error("certificate_score", _("Remove score if you have no certificate."))

        # если есть сертификат — score желательно указать (не обязательно, но полезно)
        # хочешь сделать обязательным — скажи, добавлю строгое правило

        return cleaned


# ---------- Quick CV ----------

class QuickCVForm(forms.ModelForm):
    """Быстрое создание CV: минимальные поля + skills_text."""

    skills_text = forms.CharField(
        required=False,
        label=_("Skills (comma separated)"),
        widget=forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 3}),
    )

    class Meta:
        model = CV
        fields = ["full_name", "title", "email", "phone", "region", "city", "summary"]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "title": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "email": forms.EmailInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "phone": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "region": forms.Select(attrs={"class": BOOTSTRAP_SELECT}),  # choices!
            "city": forms.TextInput(attrs={"class": BOOTSTRAP_CONTROL}),
            "summary": forms.Textarea(attrs={"class": BOOTSTRAP_CONTROL, "rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        _set_placeholder(self.fields["full_name"], _("Full Name"))
        _set_placeholder(self.fields["title"], _("My Resume"))
        _set_placeholder(self.fields["email"], _("name@example.com"))
        _set_placeholder(self.fields["phone"], _("+998 XX XXX XX XX"))
        _set_placeholder(self.fields["city"], _("City"))
        _set_placeholder(self.fields["summary"], _("Short professional summary..."))
        _set_placeholder(self.fields["skills_text"], _("Python, Django, PostgreSQL, Docker"))

        # Тут summary по модели обязательный — оставляем required=True
        # city по модели обязательный — оставляем required=True

    def clean(self):
        cleaned = super().clean()
        # Можно добавить простую чистку навыков (не создаём Skill тут, это лучше делать в view)
        skills_text = cleaned.get("skills_text") or ""
        cleaned["skills_text"] = ", ".join([s.strip() for s in skills_text.split(",") if s.strip()])
        return cleaned
