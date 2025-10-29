from django import forms
from .models import CV, Education, Experience, Skill, Project, Language, Certificate, CVSettings

class CVForm(forms.ModelForm):
    """Форма для создания/редактирования резюме"""
    
    class Meta:
        model = CV
        fields = [
            'title', 'template', 'full_name', 'email', 'phone', 'location', 
            'photo', 'summary', 'show_photo', 'show_email', 'show_phone'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Название вашего резюме'}),
            'template': forms.Select(attrs={'class': 'form-control'}),
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 4,
                'placeholder': 'Кратко опишите ваши профессиональные качества и цели...'
            }),
            'show_photo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_email': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'show_phone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class EducationForm(forms.ModelForm):
    """Форма для образования"""
    
    class Meta:
        model = Education
        fields = ['institution', 'degree', 'field_of_study', 'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'institution': forms.TextInput(attrs={'class': 'form-control'}),
            'degree': forms.TextInput(attrs={'class': 'form-control'}),
            'field_of_study': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ExperienceForm(forms.ModelForm):
    """Форма для опыта работы"""
    
    class Meta:
        model = Experience
        fields = ['company', 'position', 'location', 'start_date', 'end_date', 'is_current', 'description']
        widgets = {
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class SkillForm(forms.ModelForm):
    """Форма для навыков"""
    
    class Meta:
        model = Skill
        fields = ['name', 'level', 'category', 'years_of_experience']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.TextInput(attrs={'class': 'form-control'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control'}),
        }

class ProjectForm(forms.ModelForm):
    """Форма для проектов"""
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'technologies', 'start_date', 'end_date', 'url', 'is_current']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'technologies': forms.TextInput(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_current': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class LanguageForm(forms.ModelForm):
    """Форма для языков"""
    
    class Meta:
        model = Language
        fields = ['name', 'level']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'level': forms.Select(attrs={'class': 'form-control'}),
        }

class CertificateForm(forms.ModelForm):
    """Форма для сертификатов"""
    
    class Meta:
        model = Certificate
        fields = ['name', 'issuing_organization', 'issue_date', 'expiration_date', 'credential_id', 'credential_url']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'issuing_organization': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'credential_id': forms.TextInput(attrs={'class': 'form-control'}),
            'credential_url': forms.URLInput(attrs={'class': 'form-control'}),
        }

class CVSettingsForm(forms.ModelForm):
    """Форма для настроек резюме"""
    
    class Meta:
        model = CVSettings
        fields = ['font_family', 'font_size', 'primary_color', 'secondary_color', 'margin', 'line_spacing']
        widgets = {
            'font_family': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('Arial', 'Arial'),
                ('Helvetica', 'Helvetica'),
                ('Times New Roman', 'Times New Roman'),
                ('Georgia', 'Georgia'),
                ('Verdana', 'Verdana'),
            ]),
            'font_size': forms.NumberInput(attrs={'class': 'form-control', 'min': '8', 'max': '18'}),
            'primary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'secondary_color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
            'margin': forms.NumberInput(attrs={'class': 'form-control', 'min': '10', 'max': '50'}),
            'line_spacing': forms.NumberInput(attrs={'class': 'form-control', 'min': '1.0', 'max': '2.0', 'step': '0.1'}),
        }

class CVImportForm(forms.Form):
    """Форма для импорта резюме"""
    import_file = forms.FileField(
        label='Файл резюме',
        help_text='Поддерживаемые форматы: PDF, DOC, DOCX',
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    source = forms.ChoiceField(
        choices=[
            ('linkedin', 'LinkedIn'),
            ('hh', 'HeadHunter'),
            ('other', 'Другое'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )