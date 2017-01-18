# coding: utf-8
from django.contrib import admin
from django.utils.translation import ugettext as _

from common.admin import CommonAdmin, EntityAdmin, EntityStackedInline

from fallout.app.models import *  # noqa


class LootInline(admin.TabularInline):
    model = Loot
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(CommonAdmin):
    fieldsets = (
        (None, dict(
            fields=('name', 'game_date', 'current_character', 'active_effects', ),
            classes=('wide', ),
        )),
    )
    inlines = [LootInline]
    filter_horizontal = ('active_effects', )
    list_display = ('name', 'game_date', 'current_character', )
    list_editable = ('game_date', 'current_character', )


@admin.register(Character)
class CharacterAdmin(EntityAdmin):
    fieldsets = (
        (_("Informations techniques"), dict(
            fields=('user', 'campaign', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'race', 'level', 'is_player', ),
            classes=('wide', ),
        )),
    ) + tuple((title, dict(fields=[a for a, b in fields], classes=('wide', 'collapse'))) for title, fields in ALL_STATS)
    list_display = ('name', 'race', 'level', 'is_player', 'health', 'action_points', 'experience', 'karma')
    list_editable = ('health', 'action_points', 'experience', 'karma')
    list_filter = ('campaign', 'user', 'race', 'is_player')
    search_fields = ('name', 'title', 'description')


class ItemModifierInline(admin.TabularInline):
    model = ItemModifier
    extra = 1


@admin.register(Item)
class ItemAdmin(EntityAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'type', 'value', 'weight', 'is_quest', ),
            classes=('wide', ),
        )),
        (_("Armement"), dict(
            fields=('melee', 'throwable', 'damage_type', 'damage_dice_count', 'damage_dice_value', 'damage_bonus',
                    'range', 'clip_size', 'ap_cost_reload', 'ap_cost_normal', 'ap_cost_target', 'ap_cost_burst',
                    'burst_count', 'min_strength', 'skill', 'ammunition', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Modificateurs"), dict(
            fields=('hit_chance_modifier', 'armor_class_modifier', 'resistance_modifier', 'range_modifier',
                    'damage_modifier', 'critical_modifier', 'condition_modifier', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Effets"), dict(
            fields=('effects', ),
            classes=('wide', 'collapse', ),
        )),
    )
    filter_horizontal = ('ammunition', 'effects', )
    inlines = [ItemModifierInline]
    list_display = ('name', 'type', 'value', 'weight', 'is_quest', )
    list_editable = ()
    list_filter = ('type', 'is_quest', 'is_melee', 'is_throwable')
    search_fields = ('name', 'title', 'description')


@admin.register(Equipment)
class EquipmentAdmin(EntityAdmin):
    fieldsets = (
        (None, dict(
            fields=('character', 'item', 'slot', 'count', 'condition', 'clip_count', ),
            classes=('wide', ),
        )),
    )
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()


class EffectModifierInline(admin.TabularInline):
    model = EffectModifier
    extra = 1


@admin.register(Effect)
class EffectAdmin(EntityAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'chance', 'duration', 'statistic', ),
            classes=('wide', ),
        )),
        (_("Dégâts temporels"), dict(
            fields=('interval', 'damage_type', 'damage_dice_count', 'damage_dice_value', 'damage_bonus', ),
            classes=('wide', 'collapse', ),
        )),
    )
    inlines = [EffectModifierInline]
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()


@admin.register(ActiveEffect)
class ActiveEffectAdmin(EntityAdmin):
    fieldsets = (
        (None, dict(
            fields=('character', 'effect', 'start_date', 'end_date', 'next_date', ),
            classes=('wide', ),
        )),
    )
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()


class LootTemplateItemInline(EntityStackedInline):
    model = LootTemplateItem
    extra = 1


@admin.register(LootTemplate)
class LootTemplateAdmin(EntityAdmin):
    fieldsets = (
        (None, dict(
            fields=('name', 'title', 'description', 'image', ),
            classes=('wide', ),
        )),
    )
    inlines = [LootTemplateItemInline]
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()


@admin.register(RollHistory)
class RollHistoryAdmin(CommonAdmin):
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()


@admin.register(FightHistory)
class FightHistoryAdmin(CommonAdmin):
    # TODO:
    list_display = ()
    list_editable = ()
    list_filter = ()
