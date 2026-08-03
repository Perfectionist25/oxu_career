from typing import Any, Dict, Optional

from django import forms
from django.utils.translation import gettext_lazy as _

from accounts.models import (
    Company,
    EmployerProfile,
)
from jobs.models import (
    Job,
    JobApplication,
)
from jobs.forms import INDUSTRY_CHOICES
from employers.models import (
    CandidateNote,
    CompanyReview,
    Interview,
)


class CompanyForm(forms.ModelForm):
    """Форма для компании"""

    class Meta:
        model = Company
        fields = [
            "name",
            "company_type",
            "description",
            "website",
            "logo",
            "industry",
            "company_size",
            "founded_year",
            "address",
            "email",
            "phone",
            "linkedin",
            "facebook",
            "telegram",
            "instagram",
        ]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Company name")}
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Company description and activities..."),
                }
            ),
            "website": forms.URLInput(
                attrs={"class": "form-control", "placeholder": "https://example.com"}
            ),
            "company_type": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Legal structure, e.g. ООО")}
            ),
            "industry": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Industry or business activity")}
            ),
            "company_size": forms.Select(attrs={"class": "form-control"}),
            "founded_year": forms.NumberInput(
                attrs={"class": "form-control", "min": "1900", "max": "2024"}
            ),
            "address": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Company address"),
                }
            ),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://linkedin.com/company/...",
                }
            ),
            "facebook": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://facebook.com/...",
                }
            ),
            "telegram": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://t.me/...",
                }
            ),
            "instagram": forms.URLInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "https://instagram.com/...",
                }
            ),
        }
        labels = {
            "name": _("Company Name"),
            "company_type": _("Company Type"),
            "description": _("Description"),
            "website": _("Website"),
            "logo": _("Logo"),
            "industry": _("Industry"),
            "company_size": _("Company Size"),
            "founded_year": _("Founded Year"),
            "address": _("Address"),
            "email": _("Email"),
            "phone": _("Phone"),
            "linkedin": _("LinkedIn"),
            "facebook": _("Facebook"),
            "telegram": _("Telegram"),
            "instagram": _("Instagram"),
        }


class EmployerProfileForm(forms.ModelForm):
    """Форма для профиля работодателя"""

    class Meta:
        model = EmployerProfile
        fields = [
            "job_title",
            "professional_bio",
            "preferred_contact_method",
        ]
        widgets = {
            "job_title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Your position")}
            ),
            "professional_bio": forms.Textarea(
                attrs={"class": "form-control", "rows": 4, "placeholder": _("Professional background...")}
            ),
            "preferred_contact_method": forms.Select(attrs={"class": "form-select"}),
            "receive_company_notifications": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "job_title": _("Job Title"),
            "professional_bio": _("Professional Bio"),
            "preferred_contact_method": _("Preferred Contact Method"),
            "receive_company_notifications": _("Receive Notifications"),
        }


class JobApplicationForm(forms.ModelForm):
    """Форма для отклика на вакансию"""

    class Meta:
        model = JobApplication
        fields = ["cover_letter", "expected_salary", "cv"]
        widgets = {
            "cover_letter": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Write your cover letter..."),
                }
            ),
            "expected_salary": forms.NumberInput(
                attrs={"class": "form-control", "min": "0", "step": "100000"}
            ),
            "cv": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "cover_letter": _("Cover Letter"),
            "expected_salary": _("Expected Salary"),
            "cv": _("Resume/CV"),
        }


class CandidateNoteForm(forms.ModelForm):
    """Форма для заметок о кандидате"""

    class Meta:
        model = CandidateNote
        fields = ["note", "is_private", "job"]
        widgets = {
            "note": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _("Add notes about the candidate..."),
                }
            ),
            "is_private": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "job": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "note": _("Note"),
            "is_private": _("Private Note"),
            "job": _("Related Job"),
        }


class InterviewForm(forms.ModelForm):
    """Форма для собеседования"""

    class Meta:
        model = Interview
        fields = ["scheduled_date", "duration", "location", "notes", "interviewer"]
        widgets = {
            "scheduled_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "duration": forms.NumberInput(
                attrs={"class": "form-control", "min": "15", "max": "480"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Interview location or Zoom link"),
                }
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "interviewer": forms.Select(attrs={"class": "form-control"}),
        }
        labels = {
            "scheduled_date": _("Scheduled Date"),
            "duration": _("Duration (minutes)"),
            "location": _("Location"),
            "notes": _("Notes"),
            "interviewer": _("Interviewer"),
        }


class CompanyReviewForm(forms.ModelForm):
    """Форма для отзыва о компании"""

    class Meta:
        model = CompanyReview
        fields = ["rating", "title", "review", "pros", "cons", "is_anonymous"]
        widgets = {
            "rating": forms.Select(attrs={"class": "form-control"}),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Review title")}
            ),
            "review": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": _(
                        "Share your experience working at this company..."
                    ),
                }
            ),
            "pros": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("What did you like about working here?"),
                }
            ),
            "cons": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("What could be improved?"),
                }
            ),
            "is_anonymous": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "rating": _("Rating"),
            "title": _("Title"),
            "review": _("Review"),
            "pros": _("Pros"),
            "cons": _("Cons"),
            "is_anonymous": _("Post Anonymously"),
        }


class JobSearchForm(forms.Form):
    """Форма поиска вакансий"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Job title, company, or keywords..."),
            }
        ),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Tashkent, Samarkand...")}
        ),
    )
    employment_type = forms.MultipleChoiceField(
        required=False,
        choices=Job.EMPLOYMENT_TYPE_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    experience_level = forms.MultipleChoiceField(
        required=False,
        choices=Job.EXPERIENCE_LEVEL_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    industry = forms.MultipleChoiceField(
        required=False,
        choices=INDUSTRY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={"class": "form-check-input"}),
    )
    remote_work = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )


class ApplicationStatusForm(forms.Form):
    """Форма изменения статуса отклика"""

    status = forms.ChoiceField(
        choices=JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Additional notes..."),
            }
        ),
    )
