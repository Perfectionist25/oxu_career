from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Resource, ResourceCategory

class ResourceForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'category', 'description', 'image', 'url_youtube', 'is_published']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter resource title')
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Enter resource description')
            }),
            'url_youtube': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter YouTube URL (optional)')
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': _('Title'),
            'category': _('Category'),
            'description': _('Description'),
            'image': _('Image'),
            'url_youtube': _('YouTube URL'),
            'is_published': _('Publish immediately'),
        }
        help_texts = {
            'url_youtube': _('Optional: Add a YouTube video URL'),
            'is_published': _('Check to publish this resource immediately'),
        }

class ResourceCategoryForm(forms.ModelForm):
    class Meta:
        model = ResourceCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }