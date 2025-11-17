from django import forms
from django.utils.translation import gettext_lazy as _
from .models import *

class JobForm(forms.ModelForm):
    """Vakansiya yaratish/tahrirlash formasi"""

    class Meta:
        model = Job
        fields = [
            # Asosiy ma'lumotlar
            "title",
            "short_description",
            "description",
            
            # Manzil va ish turi
            "region",
            "district", 
            "location",
            "remote_work",
            "hybrid_work",
            "office_work",
            "employment_type",
            
            # Tajriba va ma'lumot
            "experience_level",
            "education_level",
            
            # Maosh
            "salary_min",
            "salary_max", 
            "currency",
            "hide_salary",
            "salary_negotiable",
            "bonus_system",
            
            # Talablar va majburiyatlar
            "requirements",
            "responsibilities",
            "benefits",
            
            # Ko'nikmalar
            "skills_required",
            "preferred_skills",
            "language_requirements",
            
            # Ish jadvali
            "work_schedule",
            "probation_period",
            
            # Kontakt ma'lumotlari
            "contact_email",
            "contact_phone",
            "contact_person",
            
            # Muddati
            "expires_at",
        ]

        widgets = {
            # Asosiy ma'lumotlar
            "title": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Masalan: Senior Dasturchi"),
            }),
            "short_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": _("Ishning qisqacha tavsifi..."),
            }),
            "description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 5,
                "placeholder": _("Ishning batafsil tavsifi..."),
            }),
            
            # Manzil va ish turi
            "region": forms.Select(attrs={"class": "form-control"}),
            "district": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Masalan: Mirzo Ulug'bek tumani"),
            }),
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("To'liq manzil"),
            }),
            "remote_work": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "hybrid_work": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "office_work": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "employment_type": forms.Select(attrs={"class": "form-control"}),
            
            # Tajriba va ma'lumot
            "experience_level": forms.Select(attrs={"class": "form-control"}),
            "education_level": forms.Select(attrs={"class": "form-control"}),
            
            # Maosh
            "salary_min": forms.NumberInput(attrs={
                "class": "form-control",
                "min": "0",
                "placeholder": _("Minimal maosh"),
            }),
            "salary_max": forms.NumberInput(attrs={
                "class": "form-control", 
                "min": "0",
                "placeholder": _("Maksimal maosh"),
            }),
            "currency": forms.Select(attrs={"class": "form-control"}),
            "hide_salary": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "salary_negotiable": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "bonus_system": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            
            # Talablar va majburiyatlar
            "requirements": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Talab qilinadigan bilim va ko'nikmalar..."),
            }),
            "responsibilities": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": _("Asosiy vazifalar va majburiyatlar..."),
            }),
            "benefits": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": _("Kompaniya taklif qiladigan imtiyozlar..."),
            }),
            
            # Ko'nikmalar
            "skills_required": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Python, Django, JavaScript, SQL..."),
            }),
            "preferred_skills": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("React, Docker, AWS..."),
            }),
            "language_requirements": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Ingliz tili - O'rta daraja, Rus tili - Erkin..."),
            }),
            
            # Ish jadvali
            "work_schedule": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Masalan: 09:00 - 18:00, dam olish kunlari: Shanba, Yakshanba"),
            }),
            "probation_period": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Masalan: 3 oy"),
            }),
            
            # Kontakt ma'lumotlari
            "contact_email": forms.EmailInput(attrs={"class": "form-control"}),
            "contact_phone": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("+998 XX XXX XX XX"),
            }),
            "contact_person": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": _("Mas'ul shaxsning F.I.SH"),
            }),
            
            # Muddati
            "expires_at": forms.DateInput(attrs={
                "class": "form-control",
                "type": "date"
            }),
        }
        
        labels = {
            "title": _("Lavozim nomi"),
            "short_description": _("Qisqacha tavsif"),
            "description": _("Batafsil tavsif"),
            "region": _("Viloyat"),
            "district": _("Tuman/Shahar"),
            "location": _("To'liq manzil"),
            "remote_work": _("Uydan ishlash"),
            "hybrid_work": _("Gibrid ish"),
            "office_work": _("Ofisda ishlash"),
            "employment_type": _("Ish turi"),
            "experience_level": _("Tajriba darajasi"),
            "education_level": _("Ma'lumot darajasi"),
            "salary_min": _("Minimal maosh"),
            "salary_max": _("Maksimal maosh"),
            "currency": _("Valyuta"),
            "hide_salary": _("Maoshnni yashirish"),
            "salary_negotiable": _("Maosh kelishilgan holda"),
            "bonus_system": _("Bonus tizimi"),
            "requirements": _("Talablar"),
            "responsibilities": _("Majburiyatlar"),
            "benefits": _("Imtiyozlar"),
            "skills_required": _("Talab qilinadigan ko'nikmalar"),
            "preferred_skills": _("Qo'shimcha ko'nikmalar"),
            "language_requirements": _("Til bilish darajasi"),
            "work_schedule": _("Ish jadvali"),
            "probation_period": _("Sinov muddati"),
            "contact_email": _("Email manzili"),
            "contact_phone": _("Telefon raqam"),
            "contact_person": _("Mas'ul shaxs"),
            "expires_at": _("Muddati tugaydigan sana"),
        }

    def __init__(self, *args, **kwargs):
        kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        # Majburiy maydonlar - region olib tashlandi
        required_fields = [
            "title", "employment_type", "experience_level", 
            "education_level", "short_description", "description", 
            "responsibilities", "requirements", "skills_required",
            "contact_email", "contact_phone"
        ]
        
        for field in required_fields:
            self.fields[field].required = True

        # Region maydoni majburiy emas
        self.fields['region'].required = False
        self.fields['district'].required = False
        
        # Location maydoni majburiy qilish (agar region tanlanmagan bo'lsa)
        self.fields['location'].required = True

        # Select maydonlariga bo'sh variant qo'shish
        self.fields['region'].empty_label = _("Viloyatni tanlang")
        self.fields['employment_type'].empty_label = _("Ish turini tanlang")
        self.fields['experience_level'].empty_label = _("Tajriba darajasini tanlang")
        self.fields['education_level'].empty_label = _("Ma'lumot darajasini tanlang")
        self.fields['currency'].empty_label = _("Valyutani tanlang")

    def clean(self):
        cleaned_data = super().clean() or {}
        salary_min = cleaned_data.get("salary_min")
        salary_max = cleaned_data.get("salary_max")
        remote_work = cleaned_data.get("remote_work", False)
        hybrid_work = cleaned_data.get("hybrid_work", False)
        office_work = cleaned_data.get("office_work", False)
        region = cleaned_data.get("region")
        location = cleaned_data.get("location")

        # Maosh tekshiruvi
        if salary_min and salary_max and salary_min > salary_max:
            raise forms.ValidationError(
                _("Minimal maosh maksimal maoshdan katta bo'lishi mumkin emas.")
            )

        # Ish turi tekshiruvi
        work_types = [remote_work, hybrid_work, office_work]
        if not any(work_types):
            raise forms.ValidationError(
                _("Kamida bitta ish turini tanlang.")
            )

        # Manzil tekshiruvi - agar region tanlanmagan bo'lsa, location majburiy
        if not region and not location:
            raise forms.ValidationError(
                _("Iltimos, kamida bitta manzil maydonini to'ldiring (viloyat yoki to'liq manzil).")
            )

        return cleaned_data

    def clean_location(self):
        """Location maydoni uchun qo'shimcha tekshiruv"""
        location = self.cleaned_data.get('location')
        region = self.cleaned_data.get('region')
        
        # Agar region tanlanmagan bo'lsa, location majburiy
        if not region and not location:
            raise forms.ValidationError(
                _("Agar viloyat tanlanmagan bo'lsa, to'liq manzilni kiriting.")
            )
            
        return location


class JobSearchForm(forms.Form):
    """Ish qidirish formasi"""

    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Lavozim, kompaniya yoki kalit so'zlar..."),
        }),
    )
    
    region = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": _("Toshkent, Samarqand..."),
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
            "placeholder": _("Minimal maosh"),
            "min": "0"
        }),
    )


class JobApplicationForm(forms.ModelForm):
    """Vakansiyaga ariza topshirish formasi"""

    class Meta:
        model = JobApplication
        fields = [
            "cv",
            "cover_letter", 
            "expected_salary",
            "available_from",
        ]
        
        widgets = {
            "cv": forms.Select(attrs={"class": "form-control"}),
            "cover_letter": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 6,
                "placeholder": _("Nima uchun siz ushbu lavozimga mos kelasiz..."),
            }),
            "expected_salary": forms.NumberInput(attrs={
                "class": "form-control", 
                "min": "0",
                "placeholder": _("Kutilayotgan maosh"),
            }),
            "available_from": forms.DateInput(attrs={
                "class": "form-control", 
                "type": "date"
            }),
        }
        
        labels = {
            "cv": _("Rezyume"),
            "cover_letter": _("Xat"),
            "expected_salary": _("Kutilayotgan maosh"),
            "available_from": _("Ish boshlash sanasi"),
        }


class ApplicationStatusForm(forms.Form):
    """Ariza holatini o'zgartirish formasi"""

    status = forms.ChoiceField(
        choices=JobApplication.STATUS_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            "class": "form-control",
            "rows": 3,
            "placeholder": _("Izohlar..."),
        }),
    )