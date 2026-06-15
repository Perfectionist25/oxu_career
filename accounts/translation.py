from modeltranslation.translator import translator, TranslationOptions
from .models import EmployerProfile, StudentProfile, Notification

class EmployerProfileTranslationOptions(TranslationOptions):
    fields = ('professional_bio', 'job_title')

class StudentProfileTranslationOptions(TranslationOptions):
    fields = ('faculty', 'specialty', 'desired_position')

class NotificationTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

translator.register(EmployerProfile, EmployerProfileTranslationOptions)
translator.register(StudentProfile, StudentProfileTranslationOptions)
translator.register(Notification, NotificationTranslationOptions)