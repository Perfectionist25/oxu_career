from modeltranslation.translator import translator, TranslationOptions
from .models import Skill

class CompanyTranslationOptions(TranslationOptions):
    fields = ('name', 'description', 'address')

class SkillTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class AlumniTranslationOptions(TranslationOptions):
    fields = ('name', 'faculty', 'specialization', 'current_position', 'profession', 'industry', 'city', 'bio', 'expertise_areas')

class ConnectionTranslationOptions(TranslationOptions):
    fields = ('message',)

class MentorshipTranslationOptions(TranslationOptions):
    fields = ('message', 'expected_duration', 'mentee_feedback', 'mentor_feedback')

class JobTranslationOptions(TranslationOptions):
    fields = ('title', 'location', 'description', 'requirements', 'benefits')

class JobApplicationTranslationOptions(TranslationOptions):
    fields = ('cover_letter',)

class EventTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'location')

class NewsTranslationOptions(TranslationOptions):
    fields = ('title', 'content', 'tags')

class MessageTranslationOptions(TranslationOptions):
    fields = ('subject', 'body')

# Company translation should be registered in the `accounts` app to avoid
# cross-app duplicate registrations. Skipping registration here.
# translator.register(Job, JobTranslationOptions)
translator.register(Skill, SkillTranslationOptions)
# Note: JobApplication and Event are registered in their canonical apps
# (jobs, events). Avoid duplicate registrations here.
