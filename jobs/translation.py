from modeltranslation.translator import translator, TranslationOptions
from .models import Job, Industry, JobApplication, SavedJob, JobAlert

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

class JobApplicationTranslationOptions(TranslationOptions):
    fields = ('cover_letter',)

class SavedJobTranslationOptions(TranslationOptions):
    fields = ()  # No text fields to translate

class JobAlertTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'keywords',
        'location',
    )

translator.register(Industry, IndustryTranslationOptions)
translator.register(Job, JobTranslationOptions)
translator.register(JobApplication, JobApplicationTranslationOptions)
translator.register(SavedJob, SavedJobTranslationOptions)
translator.register(JobAlert, JobAlertTranslationOptions)
