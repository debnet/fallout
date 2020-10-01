# coding: utf-8
from modeltranslation.translator import translator, TranslationOptions
from fallout.models import Campaign, Character, Effect, Item, LootTemplate


class BaseTranslationOptions(TranslationOptions):
    fields = ('name', 'title', 'description')


translator.register(Campaign, BaseTranslationOptions)
translator.register(Character, BaseTranslationOptions)
translator.register(Effect, BaseTranslationOptions)
translator.register(Item, BaseTranslationOptions)
translator.register(LootTemplate, BaseTranslationOptions)
