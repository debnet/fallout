# coding: utf-8
from common.admin import CommonAdmin, EntityAdmin, EntityTabularInline
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import ugettext as _

from rpg.fallout.models import *  # noqa


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (_("Fallout"), {'fields': ('phone_number', )}), )


class LootInline(admin.TabularInline):
    model = Loot
    extra = 1


@admin.register(Campaign)
class CampaignAdmin(CommonAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', ),
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
    list_display_links = ('name', )
    list_display = ('name', 'current_game_date', 'current_character', 'radiation', )
    list_editable = ('current_game_date', 'current_character', 'radiation', )
    ordering = ('name', )


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
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'race', 'level', 'is_player', 'is_active', ),
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
    list_display_links = ('name', )
    list_display = (
        'name', 'race', 'level', 'is_player', 'is_active',
        'health', '_max_health', 'action_points', '_max_action_points', 'experience', 'karma')
    list_editable = ('health', 'action_points', 'experience', 'karma')
    list_filter = ('campaign', 'user', 'race', 'is_player', 'is_active', )
    search_fields = ('name', 'title', 'description', )
    ordering = ('name', )

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
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'type', 'value', 'weight', 'is_quest', ),
            classes=('wide', ),
        )),
        (_("Armes uniquement"), dict(
            fields=(
                'is_melee', 'is_throwable', 'skill', 'min_strength', 'range', 'clip_size', 'burst_count',
                'hit_chance_modifier', 'threshold_modifier', 'resistance_modifier',
                'ap_cost_reload', 'ap_cost_normal', 'ap_cost_target', 'ap_cost_burst', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Dégâts"), dict(
            fields=(
                'damage_type', 'raw_damage', 'damage_dice_count', 'damage_dice_value',
                'damage_modifier', 'critical_modifier', 'critical_damage', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Protections uniquement"), dict(
            fields=(
                'armor_class', 'condition_modifier',
                'normal_threshold', 'normal_resistance',
                'laser_threshold', 'laser_resistance',
                'plasma_threshold', 'plasma_resistance',
                'explosive_threshold', 'explosive_resistance',
                'fire_threshold', 'fire_resistance',
            ),
            classes=('wide', 'collapse', ),
        )),
        (_("Effets et munitions"), dict(
            fields=('effects', 'ammunitions', ),
            classes=('wide', 'collapse', ),
        )),
    )
    filter_horizontal = ('effects', 'ammunitions', )
    inlines = [ItemModifierInline]
    list_display_links = ('name', )
    list_display = ('name', 'type', 'value', 'weight', 'is_quest', )
    list_editable = ()
    list_filter = ('type', 'is_quest', 'is_melee', 'is_throwable', )
    search_fields = ('name', 'title', 'description', )
    ordering = ('name', )

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
    ordering = ('character', 'item', )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('item')


class EffectModifierInline(admin.TabularInline):
    model = EffectModifier
    extra = 1


@admin.register(Effect)
class EffectAdmin(EntityAdmin):
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'chance', 'duration', ),
            classes=('wide', ),
        )),
        (_("Dégâts temporels"), dict(
            fields=('interval', 'damage_type', 'raw_damage', 'damage_dice_count', 'damage_dice_value', ),
            classes=('wide', 'collapse', ),
        )),
    )
    inlines = [EffectModifierInline]
    # TODO:
    list_display_links = ('name', )
    list_display = ('name', )
    list_editable = ()
    list_filter = ()
    ordering = ('name', )

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
    ordering = ('character', 'effect', )


class LootTemplateItemInline(EntityTabularInline):
    model = LootTemplateItem
    extra = 1


@admin.register(LootTemplate)
class LootTemplateAdmin(EntityAdmin):
    fieldsets = (
        (None, dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', ),
            classes=('wide', ),
        )),
    )
    inlines = [LootTemplateItemInline]
    # TODO: afficher un contenu potentiel du butin
    list_display_links = ('name', )
    list_display = ('name', )
    list_editable = ()
    list_filter = ()
    ordering = ('name', )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('items')


@admin.register(RollHistory)
class RollHistoryAdmin(CommonAdmin):
    fieldsets = (
        (_("Informations techniques"), dict(
            fields=('game_date', 'character', ),
            classes=('wide', ),
        )),
        (_("Jet"), dict(
            fields=('stats', 'value', 'modifier', 'roll', 'success', 'critical', ),
            classes=('wide', ),
        )),
    )
    list_display = ('date', 'game_date', 'character', 'stats', 'value', 'success', 'critical', )
    list_editable = ()
    list_filter = ('date', 'game_date', 'character', 'stats', 'success', 'critical', )
    ordering = ('-date', )
    date_hierarchy = 'date'


@admin.register(DamageHistory)
class DamageHistoryAdmin(CommonAdmin):
    fieldsets = (
        (_("Informations techniques"), dict(
            fields=('game_date', 'character', ),
            classes=('wide', ),
        )),
        (_("Dégâts de base"), dict(
            fields=('damage_type', 'raw_damage', 'damage_dice_count', 'damage_dice_value', 'base_damage', ),
            classes=('wide', ),
        )),
        (_("Etat de la protection"), dict(
            fields=('armor', 'armor_threshold', 'armor_resistance', 'armor_damage', ),
            classes=('wide', ),
        )),
        (_("Etat du personnage"), dict(
            fields=('damage_threshold', 'damage_resistance', 'real_damage', ),
            classes=('wide', ),
        )),
    )
    list_display = ('date', 'game_date', 'character', 'damage_type', 'base_damage', 'real_damage', )
    list_editable = ()
    list_filter = ('date', 'game_date', 'character', 'damage_type', )
    ordering = ('-date', )
    date_hierarchy = 'date'


class DamageHistoryInline(admin.StackedInline):
    model = DamageHistory


@admin.register(FightHistory)
class FightHistoryAdmin(CommonAdmin):
    fieldsets = (
        (_("Informations techniques"), dict(
            fields=('game_date', ),
            classes=('wide', ),
        )),
        (_("Attaquant"), dict(
            fields=('attacker', 'attacker_weapon', 'attacker_ammo', ),
            classes=('wide', ),
        )),
        (_("Défenseur"), dict(
            fields=('defender', 'defender_armor', 'range', 'body_part', ),
            classes=('wide', ),
        )),
        (_("Combat"), dict(
            fields=(
                'status', 'burst', 'hit_count', 'hit_modifier', 'hit_chance',
                'hit_roll', 'hit_success', 'hit_critical', 'damage', ),
            classes=('wide', ),
        )),
    )
    list_display = (
        'date', 'game_date', 'attacker', 'defender',
        'hit_success', 'hit_critical', 'status', 'real_damage', )
    list_editable = ()
    list_filter = (
        'date', 'game_date', 'attacker', 'defender',
        'hit_success', 'hit_critical', 'status', )
    ordering = ('-date', )
    date_hierarchy = 'date'

    def real_damage(self, obj):
        return getattr(obj.damage, 'real_damage', None)
    real_damage.short_description = _("dégâts")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('damage')
