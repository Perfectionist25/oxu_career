from modeltranslation.translator import translator, TranslationOptions
from .models import Event, EventCategory, EventSpeaker, EventSession

class EventCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class EventTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'short_description',
        'location',
        'venue',
        'address',
        'tags'
    )

class EventSpeakerTranslationOptions(TranslationOptions):
    fields = ('name', 'title', 'organization', 'bio')

class EventSessionTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'location')

translator.register(EventCategory, EventCategoryTranslationOptions)
translator.register(Event, EventTranslationOptions)
translator.register(EventSpeaker, EventSpeakerTranslationOptions)
translator.register(EventSession, EventSessionTranslationOptions)
