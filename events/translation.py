from modeltranslation.translator import translator, TranslationOptions
from .models import (
    EventCategory,
    Event
)


class EventCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')


class EventTranslationOptions(TranslationOptions):
    fields = (
        'title',
        'description',
        'short_description',
        'location',
        'tags',
    )

class EventPhotoTranslationOptions(TranslationOptions):
    fields = ('caption',)

translator.register(EventCategory, EventCategoryTranslationOptions)
translator.register(Event, EventTranslationOptions)
translator.register(EventPhoto, EventPhotoTranslationOptions)
