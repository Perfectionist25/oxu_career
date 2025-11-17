from modeltranslation.translator import translator, TranslationOptions
from .models import CustomUser, EmployerProfile, StudentProfile, Notification

class CustomUserTranslationOptions(TranslationOptions):
    fields = ('bio', 'city', 'address')

class EmployerProfileTranslationOptions(TranslationOptions):
    fields = ('company_name', 'company_description', 'headquarters')

class StudentProfileTranslationOptions(TranslationOptions):
    fields = ('faculty', 'specialty', 'desired_position')

class NotificationTranslationOptions(TranslationOptions):
    fields = ('title', 'message')

translator.register(CustomUser, CustomUserTranslationOptions)
translator.register(EmployerProfile, EmployerProfileTranslationOptions)
translator.register(StudentProfile, StudentProfileTranslationOptions)
translator.register(Notification, NotificationTranslationOptions)
