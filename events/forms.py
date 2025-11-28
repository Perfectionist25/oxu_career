from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import *


class EventCategoryForm(forms.ModelForm):
    """Форма для категории мероприятия"""

    class Meta:
        model = EventCategory
        fields = ["name", "description", "color", "icon"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Category name")}
            ),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "color": forms.TextInput(attrs={"class": "form-control", "type": "color"}),
            "icon": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "fa fa-calendar"}
            ),
        }
        labels = {
            "name": _("Category Name"),
            "description": _("Description"),
            "color": _("Color"),
            "icon": _("Icon"),
        }


class EventForm(forms.ModelForm):
    """Форма для создания/редактирования мероприятий"""

    class Meta:
        model = Event
        fields = [
            "title",
            "short_description",
            "description",
            "category",
            "event_type",
            "start_date",
            "end_date",
            "location",
            "banner_image",
            "thumbnail",
            "tags",
        ]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": _("Event title")}
            ),
            "short_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": _("Brief description (max 300 characters)"),
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Detailed event description..."),
                }
            ),
            "category": forms.Select(attrs={"class": "form-control"}),
            "event_type": forms.Select(attrs={"class": "form-control"}),
            "start_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_date": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tashkent, Uzbekistan"),
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("technology, workshop, networking"),
                }
            ),
        }
        labels = {
            "title": _("Event Title"),
            "short_description": _("Short Description"),
            "description": _("Description"),
            "category": _("Category"),
            "event_type": _("Event Type"),
            "start_date": _("Start Date"),
            "end_date": _("End Date"),
            "location": _("Location"),
            "banner_image": _("Banner Image"),
            "thumbnail": _("Thumbnail"),
            "tags": _("Tags"),
        }

    def clean(self):
        cleaned_data = super().clean() or {}
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        registration_deadline = cleaned_data.get("registration_deadline", None)

        if (
            start_date is not None
            and end_date is not None
            and start_date >= end_date
        ):
            raise forms.ValidationError(_("End date must be after start date."))

        if registration_deadline and start_date and registration_deadline > start_date:
            raise forms.ValidationError(
                _("Registration deadline cannot be after event start date.")
            )

        return cleaned_data

class EventSearchForm(forms.Form):
    """Форма поиска мероприятий"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Search events...")}
        ),
    )
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        empty_label=_("All Categories"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    event_type = forms.ChoiceField(
        choices=[("", _("All Types"))] + Event.EVENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    date_range = forms.ChoiceField(
        choices=[
            ("", _("Any Time")),
            ("today", _("Today")),
            ("week", _("This Week")),
            ("month", _("This Month")),
            ("upcoming", _("Upcoming")),
            ("past", _("Past Events")),
        ],
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(
            attrs={"class": "form-control", "placeholder": _("Location...")}
        ),
    )
    online_only = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
    free_only = forms.BooleanField(
        required=False, widget=forms.CheckboxInput(attrs={"class": "form-check-input"})
    )
