# coding: utf-8
from common.admin import CommonAdmin, EntityAdmin, EntityTabularInline
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext as __, ugettext_lazy as _

from fallout.forms import *  # noqa
from fallout.models import *  # noqa


# Niveaux des messages en fonction du jet de compétence (success, critical)
ROLL_LEVELS = {
    (False, True): messages.ERROR,
    (False, False): messages.WARNING,
    (True, False): messages.SUCCESS,
    (True, True): messages.INFO,
}


@admin.register(Player)
class PlayerAdmin(UserAdmin):
    """
    Administration des joueurs
    """
    fieldsets = UserAdmin.fieldsets + (
        (_("Fallout"), {'fields': ('nickname', )}), )
    filter_horizontal = ('groups', 'user_permissions', )


class LootInline(admin.TabularInline):
    """
    Administration intégrée des butins
    """
    model = Loot
    extra = 1
    autocomplete_fields = ('item', )


class CampaignEffectInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des effets actifs
    """
    model = CampaignEffect
    extra = 1
    autocomplete_fields = ('effect', )


@admin.register(Campaign)
class CampaignAdmin(CommonAdmin):
    """
    Administration des campagnes
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'game_master', ),
            classes=('wide', ),
        )),
        (_("Effets"), dict(
            fields=('radiation', ),
            classes=('wide', ),
        )),
        (_("Informations techniques"), dict(
            fields=('start_game_date', 'current_game_date', 'current_character', ),
            classes=('wide', ),
        )),
    )
    inlines = [LootInline, CampaignEffectInlineAdmin]
    filter_horizontal = ()
    list_display_links = ('name', )
    list_display = ('name', 'current_game_date', 'current_character', 'radiation', )
    list_editable = ('current_game_date', 'current_character', 'radiation', )
    search_fields = ('name', 'title', 'description', )
    ordering = ('name', )
    autocomplete_fields = ('game_master', 'current_character', )
    save_on_top = True
    actions_on_bottom = True


class EquipmentInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des équipements
    """
    model = Equipment
    extra = 1
    autocomplete_fields = ('item', )


class CharacterEffectInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des effets actifs
    """
    model = CharacterEffect
    extra = 1
    autocomplete_fields = ('effect', )


@admin.register(Character)
class CharacterAdmin(EntityAdmin):
    """
    Administration des personnages
    """
    fieldsets = tuple([
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'race', 'level',
                    'is_player', 'is_active', 'is_resting', ),
            classes=('wide', ),
        )),
        (_("Informations techniques"), dict(
            fields=('user', 'campaign',),
            classes=('wide', 'collapse',),
        )),
        (_("Spécialités"), dict(
            fields=('tag_skills', ),
            classes=('collapse', ),
        )),
        *(
            (title, dict(fields=tuple(a for a, b in fields), classes=('wide', 'collapse', )))
            for title, fields in ALL_STATS
        )
    ])
    inlines = [EquipmentInlineAdmin, CharacterEffectInlineAdmin]
    list_display_links = ('name', )
    list_display = (
        'name', 'race', 'level', 'is_player', 'is_active',
        'health', '_max_health', 'action_points', '_max_action_points', 'experience', 'karma')
    list_editable = ('health', 'action_points', 'experience', 'karma', 'is_active',)
    list_filter = ('campaign', 'user', 'race', 'is_player', 'is_active', )
    search_fields = ('name', 'title', 'description', )
    ordering = ('name', )
    actions = ('duplicate', 'randomize', 'roll', 'fight', 'burst', )
    autocomplete_fields = ('campaign', 'user', )
    save_on_top = True
    actions_on_bottom = True

    def get_form(self, request, obj=None, **kwargs):
        """
        Surcharge du formulaire pour afficher les données réelles des statistiques pour chaque champ
        """
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

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=__("Les personnages sélectionnés ont été dupliqués."))
    duplicate.short_description = _("Dupliquer")

    def randomize(self, request, queryset):
        """
        Action spécifique pour randomiser les compétences d'un personnage
        """
        if 'randomize' in request.POST:
            form = RandomizeCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by('name'):
                    character.randomize(**form.cleaned_data)
                self.message_user(
                    request,
                    message=__("Les compétences des personnages sélectionnés ont été générées avec succès."),
                    level=messages.SUCCESS)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RandomizeCharacterForm()
        return render(request, 'fallout/character/admin/randomize.html', {
            'form': form, 'characters': queryset, 'targets': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
    randomize.short_description = _("Générer aléatoirement les compétences")

    def roll(self, request, queryset):
        """
        Action spécifique pour effectuer un lancer de compétence
        """
        if 'roll' in request.POST:
            form = RollCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by('name'):
                    result = character.roll(**form.cleaned_data)
                    self.message_user(
                        request, str(result),
                        level=ROLL_LEVELS[(result.success, result.critical)])
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RollCharacterForm()
        return render(request, 'fallout/character/admin/roll.html', {
            'form': form, 'characters': queryset, 'targets': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
    roll.short_description = _("Faire un jet de compétence")

    def fight(self, request, queryset):
        """
        Action spécifique pour attaquer un autre personnage
        """
        if 'fight' in request.POST:
            form = FightCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by('name'):
                    try:
                        result = character.fight(**form.cleaned_data)
                        self.message_user(
                            request, str(result),
                            level=ROLL_LEVELS[(result.success, result.critical)])
                    except Exception as error:
                        self.message_user(
                            request,
                            __("{character} : {error}").format(character=character, error=str(error)),
                            level=messages.ERROR)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = FightCharacterForm()
        return render(request, 'fallout/character/admin/fight.html', {
            'form': form, 'characters': queryset, 'targets': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})
    fight.short_description = _("Attaquer un autre personnage")

    def burst(self, request, queryset):
        pass  # TODO:
    burst.short_description = _("Attaquer en rafale plusieurs personnages")

    def loot(self, request, queryset):
        for character in queryset:
            character.loot(empty=True)
    loot.short_description = _("Lâcher tous les équipements")


class ItemModifierInline(admin.TabularInline):
    """
    Administration intégrée des modificateurs d'objets
    """
    model = ItemModifier
    extra = 1


@admin.register(Item)
class ItemAdmin(EntityAdmin):
    """
    Administration des objets
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'type', 'value', 'weight', 'is_quest', ),
            classes=('wide', ),
        )),
        (_("Armes uniquement"), dict(
            fields=(
                'is_melee', 'is_throwable', 'is_single_charge', 'skill', 'min_strength', 'range', 'clip_size',
                'burst_count', 'hit_chance_modifier', 'threshold_modifier', 'resistance_modifier',
                'ap_cost_reload', 'ap_cost_normal', 'ap_cost_target', 'ap_cost_burst', ),
            classes=('wide', 'collapse', ),
        )),
        (_("Dégâts"), dict(
            fields=(
                'damage_type', 'raw_damage', 'min_damage', 'max_damage',
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
    actions = ('duplicate', )
    save_on_top = True
    actions_on_bottom = True

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=__("Les objets sélectionnés ont été dupliqués."))
    duplicate.short_description = _("Dupliquer")


@admin.register(Equipment)
class EquipmentAdmin(CommonAdmin):
    """
    Administration des équipements
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('character', 'item', 'slot', ),
            classes=('wide', ),
        )),
        (_("Etats"), dict(
            fields=('quantity', 'condition', 'clip_count', ),
            classes=('wide', ),
        )),
    )
    list_display = ('character', 'item', 'slot', 'quantity', 'condition', 'clip_count', )
    list_editable = ('slot', 'quantity', 'condition', 'clip_count', )
    list_filter = ('character', 'slot', )
    ordering = ('character', 'item', )
    autocomplete_fields = ('character', 'item', )
    save_on_top = True
    actions_on_bottom = True


class EffectModifierInline(admin.TabularInline):
    """
    Administration intégrée des modificateurs d'effets
    """
    model = EffectModifier
    extra = 1


@admin.register(Effect)
class EffectAdmin(EntityAdmin):
    """
    Administration des effets
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', 'chance', 'duration', ),
            classes=('wide', ),
        )),
        (_("Dégâts temporels"), dict(
            fields=(
                'interval', 'damage_chance', 'damage_type', 'raw_damage',
                'min_damage', 'max_damage', 'next_effect', ),
            classes=('wide', 'collapse', ),
        )),
    )
    inlines = [EffectModifierInline]
    list_display_links = ('name', )
    list_display = ('name', )
    list_editable = ()
    list_filter = ()
    search_fields = ('name', 'title', 'description', )
    ordering = ('name', )
    actions = ('duplicate', )
    save_on_top = True
    actions_on_bottom = True

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=__("Les effets sélectionnés ont été dupliqués."))
    duplicate.short_description = _("Dupliquer")


@admin.register(CampaignEffect)
class CampaignEffectAdmin(CommonAdmin):
    """
    Administration des effets actifs sur les campagnes
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('campaign', 'effect', 'start_date', 'end_date', 'next_date', ),
            classes=('wide', ),
        )),
    )
    list_display = ('campaign', 'effect', 'start_date', 'end_date', 'next_date', )
    list_editable = ()
    list_filter = ()
    ordering = ('campaign', 'effect', )
    autocomplete_fields = ('campaign', 'effect', )
    save_on_top = True
    actions_on_bottom = True


@admin.register(CharacterEffect)
class CharacterEffectAdmin(CommonAdmin):
    """
    Administration des effets actifs sur les personnages
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('character', 'effect', 'start_date', 'end_date', 'next_date', ),
            classes=('wide', ),
        )),
    )
    list_display = ('character', 'effect', 'start_date', 'end_date', 'next_date', )
    list_editable = ()
    list_filter = ()
    ordering = ('character', 'effect', )
    autocomplete_fields = ('character', 'effect', )
    save_on_top = True
    actions_on_bottom = True


@admin.register(Loot)
class Loot(CommonAdmin):
    """
    Administration des butins
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('campaign', 'item', 'quantity', 'condition', ),
            classes=('wide', ),
        )),
    )
    list_display = ('campaign', 'item', 'quantity', 'condition', )
    list_editable = ()
    list_filter = ('campaign', )
    ordering = ('campaign', 'item', )
    autocomplete_fields = ('campaign', 'item', )
    save_on_top = True
    actions_on_bottom = True


class LootTemplateItemInline(EntityTabularInline):
    """
    Administration intégrée des templates de butins
    """
    model = LootTemplateItem
    extra = 1
    autocomplete_fields = ('item', )


@admin.register(LootTemplate)
class LootTemplateAdmin(CommonAdmin):
    """
    Administration des butins
    """
    fieldsets = (
        (_("Informations générales"), dict(
            fields=('name', 'title', 'description', 'image', 'thumbnail', ),
            classes=('wide', ),
        )),
    )
    inlines = [LootTemplateItemInline]
    list_display_links = ('name', )
    list_display = ('name', )
    list_editable = ()
    list_filter = ()
    ordering = ('name', )
    search_fields = ('name', 'title', 'description', )
    actions = ('duplicate', )
    save_on_top = True
    actions_on_bottom = True

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=__("Les modèles de butins sélectionnés ont été dupliqués."))
    duplicate.short_description = _("Dupliquer")


@admin.register(RollHistory)
class RollHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de jets de compétences
    """
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
    list_display = ('date', 'game_date', 'character', 'stats', 'roll', 'value', 'success', 'critical', )
    list_editable = ()
    list_filter = ('date', 'game_date', 'character', 'stats', 'success', 'critical', )
    ordering = ('-date', )
    date_hierarchy = 'date'
    autocomplete_fields = ('character', )


@admin.register(DamageHistory)
class DamageHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de dégâts
    """
    fieldsets = (
        (_("Informations techniques"), dict(
            fields=('game_date', 'character', ),
            classes=('wide', ),
        )),
        (_("Dégâts de base"), dict(
            fields=('damage_type', 'raw_damage', 'min_damage', 'max_damage', 'base_damage', ),
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
    autocomplete_fields = ('character', 'armor', )


@admin.register(FightHistory)
class FightHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de combats
    """
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
                'hit_roll', 'success', 'critical', 'damage', ),
            classes=('wide', ),
        )),
    )
    list_display = (
        'date', 'game_date', 'attacker', 'defender',
        'success', 'critical', 'status', 'real_damage', )
    list_editable = ()
    list_filter = (
        'date', 'game_date', 'attacker', 'defender',
        'success', 'critical', 'status', )
    ordering = ('-date', )
    date_hierarchy = 'date'
    autocomplete_fields = ('attacker', 'attacker_weapon', 'attacker_ammo', 'defender', 'defender_armor', )

    def real_damage(self, obj):
        """
        Dégâts réels
        """
        return getattr(obj.damage, 'real_damage', None)
    real_damage.short_description = _("dégâts")
