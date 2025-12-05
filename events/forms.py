from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models

from .models import *


class EventCategoryForm(forms.ModelForm):
    """Форма для категории мероприятия"""

    class Meta:
        model = EventCategory
        fields = ["name", "description", "color", "icon"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Category name"),
                    "autocomplete": "off"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": _("Optional description"),
                    "autocomplete": "off"
                }
            ),
            "color": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "type": "color",
                    "style": "width: 70px; height: 40px; padding: 5px;"
                }
            ),
            "icon": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "fas fa-calendar",
                    "autocomplete": "off"
                }
            ),
        }
        labels = {
            "name": _("Category Name"),
            "description": _("Description"),
            "color": _("Color"),
            "icon": _("Icon (Font Awesome class)"),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if not name or name.strip() == '':
            raise ValidationError(_("Category name is required."))
        if len(name) > 100:
            raise ValidationError(_("Category name cannot exceed 100 characters."))
        return name.strip()
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if description and len(description) > 500:
            raise ValidationError(_("Description cannot exceed 500 characters."))
        return description


class EventForm(forms.ModelForm):
    """Форма для создания/редактирования мероприятий"""
    
    banner_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    thumbnail = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )

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
                attrs={
                    "class": "form-control",
                    "placeholder": _("Event title"),
                    "autocomplete": "off"
                }
            ),
            "short_description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": _("Brief description (max 300 characters)"),
                    "autocomplete": "off"
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 5,
                    "placeholder": _("Detailed event description..."),
                    "autocomplete": "off"
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),
            "event_type": forms.Select(
                attrs={
                    "class": "form-control"
                }
            ),
            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local"
                }
            ),
            "end_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local"
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tashkent, Uzbekistan"),
                    "autocomplete": "off"
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("technology, workshop, networking"),
                    "autocomplete": "off"
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
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title or title.strip() == '':
            raise ValidationError(_("Event title is required."))
        if len(title) > 200:
            raise ValidationError(_("Title cannot exceed 200 characters."))
        return title.strip()
    
    def clean_short_description(self):
        short_description = self.cleaned_data.get('short_description', '')
        if not short_description or short_description.strip() == '':
            raise ValidationError(_("Short description is required."))
        if len(short_description) > 300:
            raise ValidationError(_("Short description cannot exceed 300 characters."))
        return short_description.strip()
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if not description or description.strip() == '':
            raise ValidationError(_("Description is required."))
        if len(description) > 5000:
            raise ValidationError(_("Description cannot exceed 5000 characters."))
        return description.strip()
    
    def clean_location(self):
        location = self.cleaned_data.get('location', '')
        if not location or location.strip() == '':
            raise ValidationError(_("Location is required."))
        if len(location) > 200:
            raise ValidationError(_("Location cannot exceed 200 characters."))
        return location.strip()
    
    def clean_tags(self):
        tags = self.cleaned_data.get('tags', '')
        if tags:
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            if len(tags) > 500:
                raise ValidationError(_("Tags text is too long."))
            return ', '.join(tags_list)
        return tags
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        
        # Проверка дат
        if start_date and start_date < timezone.now():
            self.add_error('start_date', _("Start date cannot be in the past."))
        
        if start_date and end_date:
            if start_date >= end_date:
                self.add_error('end_date', _("End date must be after start date."))
        
        return cleaned_data


class EventSearchForm(forms.Form):
    """Форма поиска мероприятий"""
    
    query = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search events..."),
                "autocomplete": "off"
            }
        )
    )
    
    category = forms.ModelChoiceField(
        queryset=EventCategory.objects.all(),
        required=False,
        label=_("Category"),
        empty_label=_("All Categories"),
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )
    
    event_type = forms.ChoiceField(
        choices=[("", _("All Types"))] + Event.EVENT_TYPE_CHOICES,
        required=False,
        label=_("Event Type"),
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
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
        label=_("Date Range"),
        widget=forms.Select(
            attrs={
                "class": "form-select"
            }
        )
    )
    
    location = forms.CharField(
        required=False,
        label=_("Location"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Location..."),
                "autocomplete": "off"
            }
        )
    )
    
    online_only = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Online Only"),
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input"
            }
        )
    )
    
    free_only = forms.BooleanField(
        required=False,
        initial=False,
        label=_("Free Only"),
        widget=forms.CheckboxInput(
            attrs={
                "class": "form-check-input"
            }
        )
    )
    
    def clean_query(self):
        query = self.cleaned_data.get('query', '').strip()
        if query and len(query) > 100:
            raise ValidationError(_("Search query is too long."))
        return query
    
    def clean_location(self):
        location = self.cleaned_data.get('location', '').strip()
        if location and len(location) > 100:
            raise ValidationError(_("Location is too long."))
        return location
    
    def get_filtered_queryset(self, queryset):
        """Применяет фильтры к queryset"""
        query = self.cleaned_data.get('query')
        category = self.cleaned_data.get('category')
        event_type = self.cleaned_data.get('event_type')
        date_range = self.cleaned_data.get('date_range')
        location = self.cleaned_data.get('location')
        online_only = self.cleaned_data.get('online_only')
        free_only = self.cleaned_data.get('free_only')
        
        # Поиск по тексту
        if query:
            queryset = queryset.filter(
                models.Q(title__icontains=query) |
                models.Q(short_description__icontains=query) |
                models.Q(description__icontains=query) |
                models.Q(location__icontains=query) |
                models.Q(tags__icontains=query)
            )
        
        # Фильтр по категории
        if category:
            queryset = queryset.filter(category=category)
        
        # Фильтр по типу события
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        # Фильтр по датам
        now = timezone.now()
        if date_range == 'today':
            today = now.date()
            queryset = queryset.filter(start_date__date=today)
        elif date_range == 'week':
            week_start = now - timezone.timedelta(days=now.weekday())
            week_end = week_start + timezone.timedelta(days=6)
            queryset = queryset.filter(
                start_date__date__gte=week_start.date(),
                start_date__date__lte=week_end.date()
            )
        elif date_range == 'month':
            month_start = now.replace(day=1)
            month_end = (month_start + timezone.timedelta(days=32)).replace(day=1) - timezone.timedelta(days=1)
            queryset = queryset.filter(
                start_date__date__gte=month_start.date(),
                start_date__date__lte=month_end.date()
            )
        elif date_range == 'upcoming':
            queryset = queryset.filter(start_date__gte=now)
        elif date_range == 'past':
            queryset = queryset.filter(start_date__lt=now)
        
        # Фильтр по локации
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Фильтр по онлайн событиям
        if online_only:
            queryset = queryset.filter(online_event=True)
        
        # Фильтр по бесплатным событиям
        if free_only:
            queryset = queryset.filter(price=0)
        
        # Сортировка по дате по умолчанию
        queryset = queryset.order_by('-start_date')
        
        return queryset