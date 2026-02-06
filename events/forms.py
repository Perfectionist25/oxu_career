# events/forms.py
from typing import Any, Dict

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models

from django_ckeditor_5.widgets import CKEditor5Widget
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
    """Форма для создания/редактирования мероприятий с CKEditor 5"""
    
    # Используем CKEditor5Widget для полей с HTML
    description = forms.CharField(
        widget=CKEditor5Widget(
            config_name='extends',
            attrs={
                "class": "form-control django-ckeditor-5",
                "placeholder": _("Detailed event description..."),
            }
        )
    )
    
    short_description = forms.CharField(
        widget=CKEditor5Widget(
            config_name='default',
            attrs={
                "class": "form-control django-ckeditor-5",
                "placeholder": _("Brief description (max 300 characters)"),
            }
        )
    )
    
    banner_image = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'style': 'padding: 10px;'
        })
    )
    
    thumbnail = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*',
            'style': 'padding: 10px;'
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
            "status",
        ]
        
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Event title"),
                    "autocomplete": "off",
                    "style": "font-size: 1.2rem; padding: 12px;"
                }
            ),
            "category": forms.Select(
                attrs={
                    "class": "form-select form-control",
                    "style": "padding: 10px;"
                }
            ),
            "event_type": forms.Select(
                attrs={
                    "class": "form-select form-control",
                    "style": "padding: 10px;"
                }
            ),
            "start_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                    "style": "padding: 10px;"
                }
            ),
            "end_date": forms.DateTimeInput(
                attrs={
                    "class": "form-control",
                    "type": "datetime-local",
                    "style": "padding: 10px;"
                }
            ),
            "location": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Tashkent, Uzbekistan"),
                    "autocomplete": "off",
                    "style": "padding: 10px;"
                }
            ),
            "tags": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("technology, workshop, networking"),
                    "autocomplete": "off",
                    "style": "padding: 10px;"
                }
            ),
        }
        
        if hasattr(Event, 'status'):
            widgets["status"] = forms.Select(
                attrs={
                    "class": "form-select form-control",
                    "style": "padding: 10px;"
                }
            )
        
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
        
        if hasattr(Event, 'status'):
            labels["status"] = _("Status")
        
        help_texts = {
            "short_description": _("Brief summary that appears in listings"),
            "description": _("Full event details with formatting"),
            "tags": _("Separate with commas, e.g., technology, workshop"),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Настраиваем queryset для категорий
        self.fields['category'].queryset = EventCategory.objects.all()
        
        # Устанавливаем текущее время как значение по умолчанию для дат
        if not self.instance.pk:  # Только для создания нового
            now = timezone.now()
            now_formatted = now.strftime('%Y-%m-%dT%H:%M')
            self.fields['start_date'].initial = now_formatted
            self.fields['end_date'].initial = now_formatted
        
        # Убираем поле status если его нет
        if 'status' in self.fields and not hasattr(Event, 'status'):
            del self.fields['status']
        elif 'status' in self.fields and not self.instance.pk:
            self.fields['status'].initial = 'draft'  # или 'published'
    
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
        
        # Убираем HTML теги для подсчета символов
        from django.utils.html import strip_tags
        plain_text = strip_tags(short_description).strip()
        
        if len(plain_text) > 300:
            raise ValidationError(_("Short description cannot exceed 300 characters."))
        return short_description.strip()
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '')
        if not description or description.strip() == '':
            raise ValidationError(_("Description is required."))
        
        from django.utils.html import strip_tags
        plain_text = strip_tags(description).strip()
        
        if len(plain_text) > 5000:
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
            # Разделяем по запятым
            tags_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
            
            # Проверяем каждый тег
            for tag in tags_list:
                if len(tag) > 50:
                    raise ValidationError(_(f"Tag '{tag}' is too long (max 50 characters)."))
            
            if len(tags_list) > 10:
                raise ValidationError(_("Maximum 10 tags allowed."))
            
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
    """Форма поиска мероприятий - только с существующими полями"""
    
    query = forms.CharField(
        required=False,
        label=_("Search"),
        widget=forms.TextInput(
            attrs={
                "class": "form-control",
                "placeholder": _("Search events..."),
                "autocomplete": "off",
                "style": "padding: 10px;"
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
                "class": "form-select",
                "style": "padding: 10px;"
            }
        )
    )
    
    event_type = forms.ChoiceField(
        choices=[("", _("All Types"))] + Event.EVENT_TYPE_CHOICES,
        required=False,
        label=_("Event Type"),
        widget=forms.Select(
            attrs={
                "class": "form-select",
                "style": "padding: 10px;"
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
                "class": "form-select",
                "style": "padding: 10px;"
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
                "autocomplete": "off",
                "style": "padding: 10px;"
            }
        )
    )
    
    # УБРАНО: online_only (нет поля online_event в модели)
    # УБРАНО: free_only (нет поля is_free или price в модели)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Фильтруем только активные категории
        self.fields['category'].queryset = EventCategory.objects.all()
    
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
        if not self.is_valid():
            return queryset.none()
            
        query = self.cleaned_data.get('query')
        category = self.cleaned_data.get('category')
        event_type = self.cleaned_data.get('event_type')
        date_range = self.cleaned_data.get('date_range')
        location = self.cleaned_data.get('location')
        
        # Фильтр по статусу (если есть)
        if hasattr(Event, 'status'):
            queryset = queryset.filter(status='published')
        
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
        
        # Сортировка по дате по умолчанию
        queryset = queryset.order_by('-start_date')
        
        return queryset


# Простая форма для загрузки фото (если нужно)
class EventPhotoForm(forms.ModelForm):
    class Meta:
        model = EventPhoto
        fields = ['image', 'caption']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Photo caption...')
            }),
        }
        labels = {
            'image': _('Photo'),
            'caption': _('Caption'),
        }