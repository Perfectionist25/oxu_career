from modeltranslation.translator import translator, TranslationOptions
from .models import CVTemplate, CV, Experience, Education, Skill, Language

class CVTemplateTranslationOptions(TranslationOptions):
    fields = ('name',)

class CVTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'full_name',
        'location',
        'summary',
    )

class ExperienceTranslationOptions(TranslationOptions):
    fields = (
        'company',
        'position',
        'description',
    )

class EducationTranslationOptions(TranslationOptions):
    fields = (
        'institution',
        'field_of_study',
    )

class SkillTranslationOptions(TranslationOptions):
    fields = ('name',)

class LanguageTranslationOptions(TranslationOptions):
    fields = ('name',)

translator.register(CVTemplate, CVTemplateTranslationOptions)
translator.register(CV, CVTranslationOptions)
translator.register(Experience, ExperienceTranslationOptions)
translator.register(Education, EducationTranslationOptions)
translator.register(Skill, SkillTranslationOptions)
translator.register(Language, LanguageTranslationOptions)
