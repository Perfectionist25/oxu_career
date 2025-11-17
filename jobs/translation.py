from modeltranslation.translator import translator, TranslationOptions
from .models import Job, Industry

class IndustryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class JobTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'short_description',
        'location',
        'district',
        'region',
        'requirements',
        'responsibilities',
        'benefits',
        'skills_required',
        'preferred_skills',
        'language_requirements',
        'work_schedule',
        'probation_period',
        'contact_person',
    )

translator.register(Industry, IndustryTranslationOptions)
translator.register(Job, JobTranslationOptions)
