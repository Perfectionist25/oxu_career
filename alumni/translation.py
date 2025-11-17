from modeltranslation.translator import translator, TranslationOptions
from .models import Company, Skill, Alumni, Connection, Mentorship, Job, JobApplication, Event, News, Message

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

translator.register(Company, CompanyTranslationOptions)
translator.register(Skill, SkillTranslationOptions)
translator.register(Alumni, AlumniTranslationOptions)
translator.register(Connection, ConnectionTranslationOptions)
translator.register(Mentorship, MentorshipTranslationOptions)
translator.register(Job, JobTranslationOptions)
translator.register(JobApplication, JobApplicationTranslationOptions)
translator.register(Event, EventTranslationOptions)
translator.register(News, NewsTranslationOptions)
translator.register(Message, MessageTranslationOptions)
