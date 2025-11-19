from modeltranslation.translator import translator, TranslationOptions
from .models import (
    EventCategory,
    Event,
    EventRegistration,
    EventSpeaker,
    EventSession,
    EventComment,
    EventPhoto,
    EventRating,
)


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
        'tags',
    )


class EventRegistrationTranslationOptions(TranslationOptions):
    fields = ('dietary_restrictions', 'special_requirements', 'comments')


class EventSpeakerTranslationOptions(TranslationOptions):
    fields = ('name', 'title', 'organization', 'bio')


class EventSessionTranslationOptions(TranslationOptions):
    fields = ('title', 'description', 'location')


class EventCommentTranslationOptions(TranslationOptions):
    fields = ('comment',)


class EventPhotoTranslationOptions(TranslationOptions):
    fields = ('caption',)


class EventRatingTranslationOptions(TranslationOptions):
    fields = ('comment',)


translator.register(EventCategory, EventCategoryTranslationOptions)
translator.register(Event, EventTranslationOptions)
translator.register(EventRegistration, EventRegistrationTranslationOptions)
translator.register(EventSpeaker, EventSpeakerTranslationOptions)
translator.register(EventSession, EventSessionTranslationOptions)
translator.register(EventComment, EventCommentTranslationOptions)
translator.register(EventPhoto, EventPhotoTranslationOptions)
translator.register(EventRating, EventRatingTranslationOptions)
