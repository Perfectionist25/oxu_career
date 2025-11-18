from django import forms
from django.utils.translation import gettext_lazy as _
from employers.models import Job, JobApplication

class JobForm(forms.ModelForm):
    """Form for creating/editing jobs"""

    class Meta:
        model = Job
        fields = [
            # Basic information
            "title",
            "description",

            # Location and work type
            "location",
            "remote_work",
            "employment_type",

            # Experience and education
            "experience_level",

            # Salary
            "salary_min",
            "salary_max",
            "currency",
            "hide_salary",

            # Requirements and responsibilities
            "requirements",
            "responsibilities",
            "benefits",

            # Skills
            "skills_required",

            # Contact information
            "contact_email",

            # Duration
            "expires_at",
        ]

        widgets = {
            # Basic information
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("e.g., Senior Developer"),
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("Detailed job description..."),
            }),

            # Location and work type
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Full address"),
            }),
            "remote_work": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "employment_type": forms.Select(attrs={"class": "form-control"}),

            # Experience and education
            "experience_level": forms.Select(attrs={"class": "form-control"}),

            # Salary
            "salary_min": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": _("Minimum salary"),
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": _("Maximum salary"),
            }),
            "currency": forms.Select(attrs={"class": "form-control"}),
            "hide_salary": forms.CheckboxInput(attrs={"class": "form-check-input"}),

            # Requirements and responsibilities
            "requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Required knowledge and skills..."),
            }),
            "responsibilities": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Main duties and responsibilities..."),
            }),
            "benefits": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Company benefits and perks..."),
            }),

            # Skills
            "skills_required": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Python, Django, JavaScript, SQL..."),
            }),

            # Contact information
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),

            # Duration
            "expires_at": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }
        
        labels = {
            "title": _("Job Title"),
            "description": _("Detailed Description"),
            "location": _("Full Address"),
            "remote_work": _("Remote Work"),
            "employment_type": _("Employment Type"),
            "experience_level": _("Experience Level"),
            "salary_min": _("Minimum Salary"),
            "salary_max": _("Maximum Salary"),
            "currency": _("Currency"),
            "hide_salary": _("Hide Salary"),
            "requirements": _("Requirements"),
            "responsibilities": _("Responsibilities"),
            "benefits": _("Benefits"),
            "skills_required": _("Required Skills"),
            "contact_email": _("Email Address"),
            "expires_at": _("Expiration Date"),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Required fields
        required_fields = [
            "title", "employment_type", "experience_level", 
            "description", "responsibilities", "requirements", "skills_required",
            "contact_email"
        ]
        
        for field in required_fields:
            self.fields[field].required = True
        
        # Location field required
        self.fields['location'].required = True

        # Add empty label to select fields
        self.fields['employment_type'].empty_label = _("Select employment type")
        self.fields['experience_level'].empty_label = _("Select experience level")
        self.fields['currency'].empty_label = _("Select currency")

    def clean(self):
        cleaned_data = super().clean() or {}
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")
        location = cleaned_data.get("location")

        # Salary validation
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(
                _("Minimum salary cannot be greater than maximum salary.")
            )

        # Location validation
        if not location:
            raise forms.ValidationError(
                _("Please fill in the location field.")
            )

        return cleaned_data


class JobSearchForm(forms.Form):
    """Job search form"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Position, company or keywords..."),
        }),
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
    
    remote_work = forms.BooleanField(
        required=False, 
        widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    
    salary_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            "class": "form-control",
            "placeholder": _("Minimum salary"),
            "min": "0"
        }),
    )


class JobApplicationForm(forms.ModelForm):
    """Form for applying to jobs"""

    class Meta:
        model = JobApplication
        fields = [
            "cv",
            "cover_letter",
            "expected_salary",
        ]
        
        widgets = {
            "cv": forms.Select(attrs={"class": "form-control"}),
            "cover_letter": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Why you are suitable for this position..."),
            }),
            "expected_salary": forms.NumberInput(attrs={
                "class": "form-control", 
                "min": "0",
                "placeholder": _("Expected salary"),
            }),
        }
        
        labels = {
            "cv": _("Resume"),
            "cover_letter": _("Cover Letter"),
            "expected_salary": _("Expected Salary"),
        }


class ApplicationStatusForm(forms.Form):
    """Form for changing application status"""

    status = forms.ChoiceField(
        choices=JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": _("Notes..."),
        }),
    )
