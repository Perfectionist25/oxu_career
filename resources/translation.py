from modeltranslation.translator import translator, TranslationOptions
from .models import Resource, ResourceCategory

class ResourceCategoryTranslationOptions(TranslationOptions):
    fields = ('name', 'description')

class ResourceTranslationOptions(TranslationOptions):
    fields = ('title', 'description')

translator.register(ResourceCategory, ResourceCategoryTranslationOptions)
translator.register(Resource, ResourceTranslationOptions)
