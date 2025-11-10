from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Event,
    EventCategory,
    EventComment,
    EventRating,
    EventRegistration,
    EventSession,
    EventSpeaker,
)


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
            "venue",
            "online_event",
            "online_link",
            "address",
            "banner_image",
            "thumbnail",
            "registration_required",
            "registration_type",
            "registration_deadline",
            "max_participants",
            "waitlist_enabled",
            "is_free",
            "price",
            "currency",
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
            "venue": forms.TextInput(attrs={"class": "form-control"}),
            "online_event": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "online_link": forms.URLInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "registration_required": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "registration_type": forms.Select(attrs={"class": "form-control"}),
            "registration_deadline": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "max_participants": forms.NumberInput(attrs={"class": "form-control"}),
            "waitlist_enabled": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "is_free": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "price": forms.NumberInput(attrs={"class": "form-control"}),
            "currency": forms.Select(attrs={"class": "form-control"}),
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
            "venue": _("Venue"),
            "online_event": _("Online Event"),
            "online_link": _("Online Meeting Link"),
            "address": _("Full Address"),
            "banner_image": _("Banner Image"),
            "thumbnail": _("Thumbnail"),
            "registration_required": _("Registration Required"),
            "registration_type": _("Registration Type"),
            "registration_deadline": _("Registration Deadline"),
            "max_participants": _("Maximum Participants"),
            "waitlist_enabled": _("Enable Waitlist"),
            "is_free": _("Free Event"),
            "price": _("Price"),
            "currency": _("Currency"),
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


class EventRegistrationForm(forms.ModelForm):
    """Форма регистрации на мероприятие"""

    class Meta:
        model = EventRegistration
        fields = ["dietary_restrictions", "special_requirements", "comments"]
        widgets = {
            "dietary_restrictions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": _("Any dietary restrictions?"),
                }
            ),
            "special_requirements": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": _("Any special requirements?"),
                }
            ),
            "comments": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Additional comments..."),
                }
            ),
        }
        labels = {
            "dietary_restrictions": _("Dietary Restrictions"),
            "special_requirements": _("Special Requirements"),
            "comments": _("Comments"),
        }


class EventSpeakerForm(forms.ModelForm):
    """Форма для спикеров"""

    class Meta:
        model = EventSpeaker
        fields = [
            "name",
            "title",
            "organization",
            "bio",
            "photo",
            "email",
            "website",
            "linkedin",
            "twitter",
            "order",
        ]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "organization": forms.TextInput(attrs={"class": "form-control"}),
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "website": forms.URLInput(attrs={"class": "form-control"}),
            "linkedin": forms.URLInput(attrs={"class": "form-control"}),
            "twitter": forms.URLInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "name": _("Speaker Name"),
            "title": _("Speaker Title"),
            "organization": _("Organization"),
            "bio": _("Biography"),
            "photo": _("Photo"),
            "email": _("Email"),
            "website": _("Website"),
            "linkedin": _("LinkedIn"),
            "twitter": _("Twitter"),
            "order": _("Display Order"),
        }


class EventSessionForm(forms.ModelForm):
    """Форма для сессии мероприятия"""

    class Meta:
        model = EventSession
        fields = [
            "title",
            "description",
            "session_type",
            "start_time",
            "end_time",
            "location",
            "presentation_url",
            "materials_url",
            "order",
        ]
        widgets = {
            "title": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "session_type": forms.Select(attrs={"class": "form-control"}),
            "start_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "end_time": forms.DateTimeInput(
                attrs={"class": "form-control", "type": "datetime-local"}
            ),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "presentation_url": forms.URLInput(attrs={"class": "form-control"}),
            "materials_url": forms.URLInput(attrs={"class": "form-control"}),
            "order": forms.NumberInput(attrs={"class": "form-control"}),
        }
        labels = {
            "title": _("Session Title"),
            "description": _("Description"),
            "session_type": _("Session Type"),
            "start_time": _("Start Time"),
            "end_time": _("End Time"),
            "location": _("Location"),
            "presentation_url": _("Presentation URL"),
            "materials_url": _("Materials URL"),
            "order": _("Display Order"),
        }

    def clean(self) -> Dict[str, Any]:
        cleaned_data: Dict[str, Any] = super().clean() or {}
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError(_("End time must be after start time."))

        return cleaned_data


class EventCommentForm(forms.ModelForm):
    """Форма для комментариев"""

    class Meta:
        model = EventComment
        fields = ["comment"]
        widgets = {
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Share your thoughts about this event..."),
                }
            )
        }
        labels = {
            "comment": _("Comment"),
        }


class EventRatingForm(forms.ModelForm):
    """Форма для оценки мероприятия"""

    class Meta:
        model = EventRating
        fields = [
            "rating",
            "content_rating",
            "organization_rating",
            "venue_rating",
            "comment",
        ]
        widgets = {
            "rating": forms.Select(
                attrs={"class": "form-control"},
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very Good"),
                    (5, "5 - Excellent"),
                ],
            ),
            "content_rating": forms.Select(
                attrs={"class": "form-control"},
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very Good"),
                    (5, "5 - Excellent"),
                ],
            ),
            "organization_rating": forms.Select(
                attrs={"class": "form-control"},
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very Good"),
                    (5, "5 - Excellent"),
                ],
            ),
            "venue_rating": forms.Select(
                attrs={"class": "form-control"},
                choices=[
                    (1, "1 - Poor"),
                    (2, "2 - Fair"),
                    (3, "3 - Good"),
                    (4, "4 - Very Good"),
                    (5, "5 - Excellent"),
                ],
            ),
            "comment": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Share your experience..."),
                }
            ),
        }
        labels = {
            "rating": _("Overall Rating"),
            "content_rating": _("Content Quality"),
            "organization_rating": _("Organization"),
            "venue_rating": _("Venue"),
            "comment": _("Comment"),
        }


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


class BulkEmailForm(forms.Form):
    """Форма для массовой рассылки участникам"""

    subject = forms.CharField(
        max_length=200, widget=forms.TextInput(attrs={"class": "form-control"})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 5})
    )
    recipient_type = forms.ChoiceField(
        choices=[
            ("all", _("All Registered Participants")),
            ("confirmed", _("Confirmed Participants Only")),
            ("waiting", _("Waiting List Only")),
            ("attended", _("Attended Participants")),
        ],
        widget=forms.Select(attrs={"class": "form-control"}),
    )
