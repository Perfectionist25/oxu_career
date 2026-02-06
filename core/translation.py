from modeltranslation.translator import translator, TranslationOptions
from .models import ContactMessage

class ContactMessageTranslationOptions(TranslationOptions):
    fields = (
        'name',
        'subject',
        'message',
        'admin_notes',
    )

translator.register(ContactMessage, ContactMessageTranslationOptions)
