from django import forms

from .models import CV, Education, Experience, Language, Skill


class CVForm(forms.ModelForm):
    """Минималистичная форма резюме в стиле HeadHunter"""

    class Meta:
        model = CV
        fields = [
            "full_name",
            "email",
            "phone",
            "location",
            "title",
            "salary_expectation",
            "summary",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Familiya Ism Otchestvo"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "example@email.com"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+998 (XX) XXX-XX-XX"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Toshkent shahri"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Istalgan lavozim"}
            ),
            "salary_expectation": forms.NumberInput(
                attrs={"class": "form-control", "placeholder": "So'm"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Asosiy ko'nikmalar va tajriba. "
                        "Qisqacha professional tajribangiz va kompetensiyalaringizni "
                        "tasvirlab bering."
                    ),
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Делаем поле зарплаты необязательным
        self.fields["salary_expectation"].required = False


class ExperienceForm(forms.ModelForm):
    """Форма опыта работы в стиле HH"""

    class Meta:
        model = Experience
        fields = [
            "company",
            "position",
            "start_date",
            "end_date",
            "is_current",
            "description",
        ]
        widgets = {
            "company": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Kompaniya nomi"}
            ),
            "position": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Lavozim"}
            ),
            "start_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "month",
                    "placeholder": "OO-YYYY",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "class": "form-control",
                    "type": "month",
                    "placeholder": "OO-YYYY",
                }
            ),
            "description": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Majburiyatlar va yutuqlar",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Если текущая работа, скрываем поле даты окончания
        if self.instance and self.instance.is_current:
            self.fields["end_date"].widget = forms.HiddenInput()


class EducationForm(forms.ModelForm):
    """Форма образования в стиле HH"""

    class Meta:
        model = Education
        fields = ["institution", "degree", "field_of_study", "graduation_year"]
        widgets = {
            "institution": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "O'quv muassasasi"}
            ),
            "degree": forms.Select(attrs={"class": "form-control"}),
            "field_of_study": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Mutaxassislik"}
            ),
            "graduation_year": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Bitirgan yili",
                    "min": 1950,
                    "max": 2030,
                }
            ),
        }


class SkillForm(forms.ModelForm):
    """Форма навыков в стиле HH"""

    class Meta:
        model = Skill
        fields = ["name", "level"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Masalan: Python, JavaScript, Loyiha boshqaruv",
                }
            ),
            "level": forms.Select(attrs={"class": "form-control"}),
        }


class LanguageForm(forms.ModelForm):
    """Форма языков"""

    class Meta:
        model = Language
        fields = ["name", "level"]
        widgets = {
            "name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Til"}
            ),
            "level": forms.Select(attrs={"class": "form-control"}),
        }


# Форма для быстрого создания всего резюме
class QuickCVForm(forms.ModelForm):
    """Быстрая форма для создания резюме"""

    skills_text = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": (
                    "Asosiy ko'nikmalaringizni vergul bilan ajratib sanab o'ting.\n"
                    "Masalan: Python, Django, PostgreSQL, Git, Docker"
                ),
            }
        ),
    )

    class Meta:
        model = CV
        fields = ["full_name", "title", "email", "phone", "location", "summary"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Familiya Ism Otchestvo"}
            ),
            "title": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Python dasturchi"}
            ),
            "email": forms.EmailInput(
                attrs={"class": "form-control", "placeholder": "example@email.com"}
            ),
            "phone": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "+998 (XX) XXX-XX-XX"}
            ),
            "location": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Toshkent shahri"}
            ),
            "summary": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 4,
                    "placeholder": (
                        "Ish tajribangiz, asosiy yutuqlar va professional "
                        "maqsadlaringizni tasvirlab bering..."
                    ),
                }
            ),
        }


# Inline formset для удобного управления связанными объектами
ExperienceFormSet = forms.inlineformset_factory(
    CV, Experience, form=ExperienceForm, extra=1, can_delete=True
)

EducationFormSet = forms.inlineformset_factory(
    CV, Education, form=EducationForm, extra=1, can_delete=True
)

SkillFormSet = forms.inlineformset_factory(
    CV, Skill, form=SkillForm, extra=3, can_delete=True
)

LanguageFormSet = forms.inlineformset_factory(
    CV, Language, form=LanguageForm, extra=1, can_delete=True
)
