# coding: utf-8
from common.admin import CommonAdmin, EntityAdmin, EntityTabularInline
from django.contrib import admin
from django.utils.translation import ugettext as _

from rpg.fallout.models import *  # noqa


class LootInline(admin.TabularInline):
    model = Loot
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(CommonAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', ),
            classes=('wide', ),
        )),
        (_("Informations techniques"), dict(
            fields=('start_game_date', 'current_game_date', 'current_character', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Effets"), dict(
            fields=('active_effects', 'radiation', ),
            classes=('wide', 'collapse', ),
        )),
    )
    inlines = [LootInline]
    filter_horizontal = ('active_effects', )
    list_display = ('name', 'current_game_date', 'current_character', 'radiation', )
    list_editable = ('current_game_date', 'current_character', 'radiation', )


class EquipmentInlineAdmin(EntityTabularInline):
    model = Equipment
    extra = 1


class ActiveEffectInlineAdmin(EntityTabularInline):
    model = ActiveEffect
    extra = 1


@admin.register(Character)
class CharacterAdmin(EntityAdmin):
    fieldsets = tuple([
        (_("Informations techniques"), dict(
            fields=('user', 'campaign', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'race', 'level', 'is_player', 'is_active', ),
            classes=('wide', ),
        )),
        (_("Spécialités"), dict(
            fields=('tag_skills', ),
            classes=('collapse', ),
        )),
        *(
            (title, dict(
                fields=tuple(a for a, b in fields),
                classes=('wide', 'collapse', )))
            for title, fields in ALL_STATS
        )
    ])
    inlines = [EquipmentInlineAdmin, ActiveEffectInlineAdmin]
    list_display = (
        'name', 'race', 'level', 'is_player', 'is_active',
        'health', '_max_health', 'action_points', '_max_action_points', 'experience', 'karma')
    list_editable = ('health', 'action_points', 'experience', 'karma')
    list_filter = ('campaign', 'user', 'race', 'is_player', 'is_active')
    search_fields = ('name', 'title', 'description')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            for field_name, field in form.base_fields.items():
                value = getattr(obj.stats, field_name, None)
                if value is None:
                    continue
                field.help_text = _("Valeur actuelle : {}.").format(value)
                if field_name in obj.tag_skills:
                    field.help_text += _(" (Spécialité +{}) ").format(TAG_SKILL_BONUS)
        return form

    def get_queryset(self, request):
        return super().get_queryset(request)\
            .select_related('user', 'campaign')\
            .prefetch_related('equipments', 'active_effects')


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
            fields=(
                'is_melee', 'is_throwable', 'damage_type', 'damage_dice_count', 'damage_dice_value', 'damage_bonus',
                'range', 'clip_size', 'ap_cost_reload', 'ap_cost_normal', 'ap_cost_target', 'ap_cost_burst',
                'burst_count', 'min_strength', 'skill', 'ammunition', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Modificateurs"), dict(
            fields=(
                'hit_chance_modifier', 'armor_class_modifier', 'resistance_modifier', 'range_modifier',
                'damage_modifier', 'critical_modifier', 'condition_modifier', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Résistances"), dict(
            fields=(
                'normal_threshold', 'normal_resistance', 'laser_threshold', 'laser_resistance',
                'plasma_threshold', 'plasma_resistance', 'explosive_threshold', 'explosive_resistance',
                'fire_threshold', 'fire_resistance', ),
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('modifiers')


@admin.register(Equipment)
class EquipmentAdmin(EntityAdmin):
    fieldsets = (
        (None, dict(
            fields=('character', 'item', 'slot', 'count', 'condition', 'clip_count', ),
            classes=('wide', ),
        )),
    )
    # TODO:
    list_display = ('character', 'item', 'slot', 'count', 'condition', 'clip_count', )
    list_editable = ('slot', 'count', 'condition', 'clip_count', )
    list_filter = ('character', 'item', 'slot', )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')


class EffectModifierInline(admin.TabularInline):
    model = EffectModifier
    extra = 1


@admin.register(Effect)
class EffectAdmin(EntityAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'chance', 'duration', ),
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('modifiers')


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


class LootTemplateItemInline(EntityTabularInline):
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

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')


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
