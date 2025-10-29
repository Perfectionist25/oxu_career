from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Resource, ResourceCategory, ResourceReview, StudyPlan, CareerPath, LearningTrack

class ResourceCategoryForm(forms.ModelForm):
    """Форма для категорий ресурсов"""
    
    class Meta:
        model = ResourceCategory
        fields = ['name', 'description', 'icon', 'color', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Category name')}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fa fa-book'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'name': _('Category Name'),
            'description': _('Description'),
            'icon': _('Icon'),
            'color': _('Color'),
            'order': _('Display Order'),
        }

class ResourceForm(forms.ModelForm):
    """Форма для создания/редактирования ресурсов"""
    
    class Meta:
        model = Resource
        fields = [
            'title', 'short_description', 'description', 'category', 'resource_type',
            'content', 'external_url', 'file', 'thumbnail', 'author', 'publisher',
            'language', 'level', 'duration', 'tags', 'keywords', 'is_published',
            'is_featured', 'is_free', 'requires_login', 'meta_description'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Resource title')
            }),
            'short_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Brief description...')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Detailed description...')
            }),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'resource_type': forms.Select(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': _('Resource content (for articles/tutorials)...')
            }),
            'external_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/resource'
            }),
            'author': forms.TextInput(attrs={'class': 'form-control'}),
            'publisher': forms.TextInput(attrs={'class': 'form-control'}),
            'language': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('2 hours, 30 minutes')
            }),
            'tags': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('programming, python, web-development')
            }),
            'keywords': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('python django web framework')
            }),
            'meta_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('SEO meta description...')
            }),
            'is_published': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_free': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'requires_login': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'title': _('Title'),
            'short_description': _('Short Description'),
            'description': _('Description'),
            'category': _('Category'),
            'resource_type': _('Resource Type'),
            'content': _('Content'),
            'external_url': _('External URL'),
            'file': _('File'),
            'thumbnail': _('Thumbnail'),
            'author': _('Author'),
            'publisher': _('Publisher'),
            'language': _('Language'),
            'level': _('Level'),
            'duration': _('Duration'),
            'tags': _('Tags'),
            'keywords': _('Keywords'),
            'is_published': _('Published'),
            'is_featured': _('Featured'),
            'is_free': _('Free Resource'),
            'requires_login': _('Requires Login'),
            'meta_description': _('Meta Description'),
        }

class ResourceReviewForm(forms.ModelForm):
    """Форма для отзывов о ресурсах"""
    
    class Meta:
        model = ResourceReview
        fields = ['rating', 'comment', 'pros', 'cons']
        widgets = {
            'rating': forms.Select(attrs={'class': 'form-control'}, choices=[
                (1, '1 - Poor'),
                (2, '2 - Fair'),
                (3, '3 - Good'),
                (4, '4 - Very Good'),
                (5, '5 - Excellent'),
            ]),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Share your experience with this resource...')
            }),
            'pros': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('What did you like about this resource?')
            }),
            'cons': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('What could be improved?')
            }),
        }
        labels = {
            'rating': _('Rating'),
            'comment': _('Comment'),
            'pros': _('Pros'),
            'cons': _('Cons'),
        }

class StudyPlanForm(forms.ModelForm):
    """Форма для учебных планов"""
    
    class Meta:
        model = StudyPlan
        fields = ['name', 'description', 'is_public', 'color', 'estimated_duration']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('My Python Learning Plan')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description of your learning goals...')
            }),
            'is_public': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'estimated_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('3 months, 6 weeks, etc.')
            }),
        }
        labels = {
            'name': _('Plan Name'),
            'description': _('Description'),
            'is_public': _('Public Plan'),
            'color': _('Color'),
            'estimated_duration': _('Estimated Duration'),
        }

class CareerPathForm(forms.ModelForm):
    """Форма для карьерных путей"""
    
    class Meta:
        model = CareerPath
        fields = [
            'name', 'description', 'industry', 'required_skills', 
            'average_salary', 'growth_outlook', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Frontend Developer')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Description of this career path...')
            }),
            'industry': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('IT, Healthcare, Finance, etc.')
            }),
            'required_skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('JavaScript, React, HTML, CSS, ...')
            }),
            'average_salary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('$50,000 - $80,000')
            }),
            'growth_outlook': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('High growth, Stable, etc.')
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _('Career Path Name'),
            'description': _('Description'),
            'industry': _('Industry'),
            'required_skills': _('Required Skills'),
            'average_salary': _('Average Salary'),
            'growth_outlook': _('Growth Outlook'),
            'is_active': _('Active'),
        }

class LearningTrackForm(forms.ModelForm):
    """Форма для обучающих треков"""
    
    class Meta:
        model = LearningTrack
        fields = ['name', 'description', 'career_path', 'level', 'estimated_duration', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Web Development Fundamentals')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Description of this learning track...')
            }),
            'career_path': forms.Select(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'estimated_duration': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('8 weeks, 3 months, etc.')
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'name': _('Track Name'),
            'description': _('Description'),
            'career_path': _('Career Path'),
            'level': _('Level'),
            'estimated_duration': _('Estimated Duration'),
            'is_active': _('Active'),
        }

class ResourceSearchForm(forms.Form):
    """Форма поиска ресурсов"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search resources...')
        })
    )
    category = forms.ModelChoiceField(
        queryset=ResourceCategory.objects.all(),
        required=False,
        empty_label=_('All Categories'),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    resource_type = forms.ChoiceField(
        choices=[('', _('All Types'))] + Resource.RESOURCE_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    level = forms.ChoiceField(
        choices=[('', _('All Levels'))] + Resource.LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    language = forms.ChoiceField(
        choices=[('', _('All Languages'))] + Resource.LANGUAGE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    free_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    featured_only = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

class StudyPlanItemForm(forms.Form):
    """Форма для добавления ресурсов в учебный план"""
    resource = forms.ModelChoiceField(
        queryset=Resource.objects.filter(is_published=True),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    order = forms.IntegerField(
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 2,
            'placeholder': _('Notes about this resource...')
        })
    )