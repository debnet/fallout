# coding: utf-8
from common.admin import CommonAdmin, EntityAdmin, EntityTabularInline
from django.contrib import admin, messages
from django.contrib.admin.helpers import ACTION_CHECKBOX_NAME
from django.contrib.auth.admin import UserAdmin
from django.db.models import Count, Q
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from fallout.constants import *  # noqa
from fallout.enums import *  # noqa
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

    list_display = ("id",) + UserAdmin.list_display + ("nickname",)
    list_display_links = ("username",)
    fieldsets = UserAdmin.fieldsets + ((_("Fallout"), {"fields": ("nickname",)}),)
    filter_horizontal = (
        "groups",
        "user_permissions",
    )
    search_fields = UserAdmin.search_fields + ("nickname",)


class LootInline(admin.TabularInline):
    """
    Administration intégrée des butins
    """

    model = Loot
    extra = 1
    autocomplete_fields = ("item",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("campaign", "item")


class CampaignEffectInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des effets actifs
    """

    model = CampaignEffect
    extra = 1
    autocomplete_fields = ("effect",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("campaign", "effect")


@admin.register(Campaign)
class CampaignAdmin(CommonAdmin):
    """
    Administration des campagnes
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "name",
                    "title",
                    "description",
                    "image",
                    "game_master",
                    "view_pc",
                    "view_npc",
                    "view_rolls",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Informations techniques"),
            dict(
                fields=(
                    "start_game_date",
                    "current_game_date",
                    "current_character",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Traductions"),
            dict(
                fields=(("name_fr", "name_en"), ("title_fr", "title_en"), ("description_fr", "description_en")),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Effets"),
            dict(
                fields=(
                    "needs",
                    "radiation",
                ),
                classes=("wide",),
            ),
        ),
    )
    inlines = [LootInline, CampaignEffectInlineAdmin]
    list_display_links = ("name",)
    list_display = (
        "name",
        "title",
        "current_game_date",
        "current_character",
        "needs",
        "radiation",
    )
    list_editable = (
        "current_character",
        "needs",
        "radiation",
    )
    list_filter = (
        "needs",
        "game_master",
        "view_pc",
        "view_npc",
        "view_rolls",
    )
    search_fields = (
        "name",
        "title",
        "description",
    )
    ordering = (
        "name",
        "title",
    )
    autocomplete_fields = (
        "game_master",
        "current_character",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(game_master=request.user)
        return queryset


class EquipmentInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des équipements
    """

    model = Equipment
    extra = 1
    autocomplete_fields = ("item",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("character", "item")


class CharacterEffectInlineAdmin(EntityTabularInline):
    """
    Administration intégrée des effets actifs
    """

    model = CharacterEffect
    extra = 1
    autocomplete_fields = ("effect",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("character", "effect")


@admin.register(Statistics)
class StatsAdmin(CommonAdmin):
    """
    Administration des statistiques
    """

    fieldsets = tuple(
        [
            (
                _("Informations générales"),
                dict(
                    fields=("character",),
                    classes=("wide",),
                ),
            ),
            (
                _("Autres"),
                dict(
                    fields=(
                        "charge",
                        "modifiers",
                    ),
                    classes=(
                        "wide",
                        "collapse",
                    ),
                ),
            ),
            *(
                (
                    title,
                    dict(
                        fields=tuple(a for a, b in fields),
                        classes=(
                            "wide",
                            "collapse",
                        ),
                    ),
                )
                for title, fields in ALL_EDITABLE_STATS
            ),
        ]
    )
    date_hierarchy = "date"
    list_display_links = ("character_name",)
    list_filter = (
        "character__campaign",
        "obsolete",
    )
    ordering = ("character__name",)
    autocomplete_fields = ("character",)

    def character_name(self, obj):
        return obj.character.name

    character_name.short_description = _("personnage")
    character_name.admin_order_field = "character__name"

    def campaign_name(self, obj):
        return obj.character.campaign.name if obj.character.campaign else None

    campaign_name.short_description = _("campagne")
    campaign_name.admin_order_field = "character__campaign__name"

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("character__campaign")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset

    def get_list_display(self, request):
        return "character_name", "campaign_name", "charge", "date", "obsolete"


@admin.register(Character)
class CharacterAdmin(EntityAdmin):
    """
    Administration des personnages
    """

    fieldsets = tuple(
        [
            (
                _("Informations générales"),
                dict(
                    fields=(
                        "name",
                        "title",
                        ("description", "background"),
                        "image",
                        "thumbnail",
                        "race",
                        "level",
                        "is_active",
                        "is_player",
                        "is_resting",
                        "has_stats",
                        "has_needs",
                    ),
                    classes=("wide",),
                ),
            ),
            (
                _("Informations techniques"),
                dict(
                    fields=(
                        "player",
                        "campaign",
                        "extra_data",
                    ),
                    classes=("wide",),
                ),
            ),
            (
                _("Traductions"),
                dict(
                    fields=(("name_fr", "name_en"), ("title_fr", "title_en"), ("description_fr", "description_en")),
                    classes=(
                        "wide",
                        "collapse",
                    ),
                ),
            ),
            (
                _("Spécialités"),
                dict(
                    fields=("tag_skills",),
                    classes=("collapse",),
                ),
            ),
            *(
                (
                    title,
                    dict(
                        fields=tuple(a for a, b in fields),
                        classes=(
                            "wide",
                            "collapse",
                        ),
                    ),
                )
                for title, fields in ALL_STATS
            ),
        ]
    )
    inlines = [EquipmentInlineAdmin, CharacterEffectInlineAdmin]
    list_display_links = ("name",)
    list_display = (
        "name",
        "title",
        "race",
        "level",
        "is_player",
        "is_active",
        "health",
        "current_max_health",
        "action_points",
        "current_max_action_points",
        "experience",
        "karma",
    )
    list_editable = (
        "health",
        "action_points",
        "experience",
        "karma",
        "is_active",
    )
    list_filter = (
        "campaign",
        "is_player",
        "is_active",
        "has_stats",
        "has_needs",
        "race",
        "player",
    )
    search_fields = (
        "name",
        "title",
        "description",
        "background",
    )
    ordering = (
        "name",
        "title",
    )
    actions = EntityAdmin.actions + [
        "duplicate",
        "heal",
        "damage",
        "roll",
        "fight",
        "equip",
        "loot",
        "move",
        "randomize",
        "randomize_special",
        "randomize_stats",
        "generate_stats",
    ]
    autocomplete_fields = (
        "campaign",
        "player",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_form(self, request, obj=None, **kwargs):
        """
        Surcharge du formulaire pour afficher les données réelles des statistiques pour chaque champ
        """
        form = super().get_form(request, obj, **kwargs)
        if obj and obj.has_stats:
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
        Action spécifique pour dupliquer les personnages sélectionnés
        """
        if "duplicate" in request.POST:
            form = DuplicateCharacterForm(request.POST)
            if form.is_valid():
                name = form.cleaned_data["name"]
                count = form.cleaned_data["count"]
                campaign = form.cleaned_data["campaign"]
                for character in queryset.order_by("name", "title"):
                    character_name = character.name
                    for nb in range(count):
                        new_name = f"{name or character_name} {nb + 1}" if count > 1 else name
                        character.duplicate(name=new_name, campaign=campaign)
                self.message_user(
                    request, message=_("Les personnages sélectionnés ont été dupliqués."), level=messages.SUCCESS
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DuplicateCharacterForm()
        return render(
            request,
            "fallout/character/admin/duplicate.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    duplicate.short_description = _("Dupliquer les personnages sélectionnés")

    def roll(self, request, queryset):
        """
        Action spécifique pour effectuer un lancer de compétence
        """
        if "roll" in request.POST:
            form = RollCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by("name", "title"):
                    result = character.roll(**form.cleaned_data)
                    self.message_user(request, str(result), level=result.message_level)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RollCharacterForm()
        return render(
            request,
            "fallout/character/admin/roll.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    roll.short_description = _("Faire un jet de compétence")

    def damage(self, request, queryset):
        """
        Action spécifique pour infliger des dégâts aux personnages sélectionnés
        """
        if "damage" in request.POST:
            form = DamageCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by("name", "title"):
                    result = character.damage(**form.cleaned_data)
                    self.message_user(request, str(result), level=result.message_level)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = DamageCharacterForm()
        return render(
            request,
            "fallout/character/admin/damage.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    damage.short_description = _("Infliger des dégâts aux personnages sélectionnés")

    def fight(self, request, queryset):
        """
        Action spécifique pour attaquer un autre personnage
        """
        if "fight" in request.POST:
            form = FightCharacterForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by("name", "title"):
                    try:
                        result = character.fight(**form.cleaned_data)
                        self.message_user(request, str(result), level=result.message_level)
                    except Exception as error:
                        self.message_user(
                            request,
                            _("{character} : {error}").format(character=character, error=str(error)),
                            level=messages.ERROR,
                        )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = FightCharacterForm()
        return render(
            request,
            "fallout/character/admin/fight.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    fight.short_description = _("Attaquer un autre personnage")

    def randomize(self, request, queryset):
        """
        Action spécifique pour générer complètement et aléatoirement les personnages sélectionnés
        """
        if "randomize" in request.POST:
            form = RandomizeCharacterForm(request.POST)
            if form.is_valid():
                Equipment.objects.filter(character__in=queryset).exclude(slot="").delete()
                for character in queryset.order_by("name", "title"):
                    character.randomize_special(**form.cleaned_data, save=False)
                    if not character.has_stats:
                        character.generate_stats(save=False)
                    character.randomize_stats(**form.cleaned_data, save=False)
                    Character.reset_stats(character)
                    character.heal(save=True)
                    character.equip(**form.cleaned_data)
                self.message_user(
                    request,
                    message=_("Les personnages sélectionnés ont été générés aléatoirement avec succès."),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RandomizeCharacterForm()
        return render(
            request,
            "fallout/character/admin/randomize.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    randomize.short_description = _("Générer complètement les personnages")

    def randomize_special(self, request, queryset):
        """
        Action spécifique pour randomiser le SPECIAL des personnages sélectionnés
        """
        if "randomize_special" in request.POST:
            form = RandomizeCharacterSpecialForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by("name", "title"):
                    character.randomize_special(**form.cleaned_data)
                self.message_user(
                    request,
                    message=_("Le S.P.E.C.I.A.L. des personnages sélectionnés ont été générées avec succès."),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RandomizeCharacterSpecialForm()
        return render(
            request,
            "fallout/character/admin/randomize_special.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    randomize_special.short_description = _("Générer aléatoirement le S.P.E.C.I.A.L.")

    def randomize_stats(self, request, queryset):
        """
        Action spécifique pour randomiser les compétences des personnages sélectionnés
        """
        if "randomize_stats" in request.POST:
            form = RandomizeCharacterStatsForm(request.POST)
            if form.is_valid():
                for character in queryset.order_by("name", "title"):
                    character.randomize_stats(**form.cleaned_data)
                self.message_user(
                    request,
                    message=_("Les compétences des personnages sélectionnés ont été générées avec succès."),
                    level=messages.SUCCESS,
                )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = RandomizeCharacterStatsForm()
        return render(
            request,
            "fallout/character/admin/randomize_stats.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    randomize_stats.short_description = _("Générer aléatoirement les compétences")

    def equip(self, request, queryset):
        """
        Action spécifique pour équiper aléatoirement les personnages sélectionnés
        """
        if "randomize_equipment" in request.POST:
            form = EquipCharacterForm(request.POST)
            if form.is_valid():
                Equipment.objects.filter(character__in=queryset).exclude(slot="").delete()
                for character in queryset.order_by("name", "title"):
                    try:
                        character.equip(**form.cleaned_data)
                    except Exception as error:
                        self.message_user(
                            request,
                            _("{character} : {error}").format(character=character, error=str(error)),
                            level=messages.ERROR,
                        )
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = EquipCharacterForm()
        return render(
            request,
            "fallout/character/admin/equip.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    equip.short_description = _("Equiper les personnages sélectionnés")

    def generate_stats(self, request, queryset):
        """
        Action pour générer les statistiques des personnages sélectionnés
        """
        for character in queryset:
            character.generate_stats()

    generate_stats.short_description = _("Générer les statistiques secondaires")

    def heal(self, request, queryset):
        """
        Action pour soigner les personnages sélectionnés
        """
        for character in queryset:
            character.heal()

    heal.short_description = _("Soigner les personnages sélectionnés")

    def loot(self, request, queryset):
        """
        Action spécifique pour looter les personnages sélectionnés
        """
        for character in queryset:
            character.loot(empty=True)

    loot.short_description = _("Lâcher tous les équipements")

    def move(self, request, queryset):
        """
        Action spécifique pour déplacer les personnages sélectionnés
        """
        if "move" in request.POST:
            form = CampaignForm(request.POST)
            if form.is_valid():
                queryset.update(**form.cleaned_data)
                return HttpResponseRedirect(request.get_full_path())
        else:
            form = CampaignForm()
        return render(
            request,
            "fallout/character/admin/move.html",
            {"form": form, "characters": queryset, "targets": request.POST.getlist(ACTION_CHECKBOX_NAME)},
        )

    move.short_description = _("Déplacer les personnages sélectionnés")

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("statistics")
        if not request.user.is_superuser:
            queryset = queryset.filter(campaign__game_master=request.user)
        return queryset


class ItemModifierInline(admin.TabularInline):
    """
    Administration intégrée des modificateurs d'objets
    """

    model = ItemModifier
    extra = 1

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("item")


@admin.register(Item)
class ItemAdmin(EntityAdmin):
    """
    Administration des objets
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "name",
                    "title",
                    "description",
                    "image",
                    "thumbnail",
                    "type",
                    "value",
                    "weight",
                    "durability",
                    "condition_modifier",
                    "is_quest",
                    "is_droppable",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Traductions"),
            dict(
                fields=(("name_fr", "name_en"), ("title_fr", "title_en"), ("description_fr", "description_en")),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Armes uniquement"),
            dict(
                fields=(
                    "attack_mode",
                    "skill",
                    "min_skill",
                    "min_strength",
                    "hands",
                    "min_range",
                    "min_burst_range",
                    "max_range",
                    "max_burst_range",
                    "clip_size",
                    "burst_count",
                    "hit_chance_modifier",
                    "armor_class_modifier",
                    "threshold_modifier",
                    "threshold_rate_modifier",
                    "resistance_modifier",
                    "ap_cost_reload",
                    "ap_cost_normal",
                    "ap_cost_target",
                    "ap_cost_burst",
                    "is_single_charge",
                ),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Dégâts"),
            dict(
                fields=(
                    "body_part",
                    "damage_type",
                    "raw_damage",
                    "min_damage",
                    "max_damage",
                    "damage_modifier",
                    "critical_modifier",
                    "critical_raw_modifier",
                    "critical_damage",
                    "critical_damage_modifier",
                ),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Protections uniquement"),
            dict(
                fields=(
                    "armor_class",
                    *LIST_ALL_RESISTANCES,
                ),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Effets et munitions"),
            dict(
                fields=(
                    "effects",
                    "ammunitions",
                ),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
    )
    inlines = [ItemModifierInline]
    list_display_links = ("name",)
    list_display = (
        "name",
        "title",
        "type",
        "value",
        "weight",
        "is_quest",
    )
    list_editable = ()
    list_filter = (
        "type",
        "hands",
        "attack_mode",
        "skill",
        "is_quest",
        "is_droppable",
    )
    search_fields = (
        "name",
        "title",
        "description",
    )
    ordering = (
        "name",
        "title",
    )
    actions = EntityAdmin.actions + [
        "duplicate",
    ]
    autocomplete_fields = (
        "effects",
        "ammunitions",
    )
    save_on_top = True
    actions_on_bottom = True

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=_("Les objets sélectionnés ont été dupliqués."))

    duplicate.short_description = _("Dupliquer les objets sélectionnés")


@admin.register(Equipment)
class EquipmentAdmin(CommonAdmin):
    """
    Administration des équipements
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "character",
                    "item",
                    "slot",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Etats"),
            dict(
                fields=(
                    "quantity",
                    "condition",
                    "clip_count",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "character",
        "item",
        "slot",
        "quantity",
        "condition",
        "clip_count",
    )
    list_editable = (
        "slot",
        "quantity",
        "condition",
        "clip_count",
    )
    list_filter = (
        "character__campaign",
        "character__is_player",
        "slot",
    )
    ordering = (
        "character",
        "item",
    )
    autocomplete_fields = (
        "character",
        "item",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("character", "item")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset


class EffectModifierInline(admin.TabularInline):
    """
    Administration intégrée des modificateurs d'effets
    """

    model = EffectModifier
    extra = 1

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("effect")


@admin.register(Effect)
class EffectAdmin(EntityAdmin):
    """
    Administration des effets
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "name",
                    "title",
                    "description",
                    "image",
                    "thumbnail",
                    "character",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Traductions"),
            dict(
                fields=(("name_fr", "name_en"), ("title_fr", "title_en"), ("description_fr", "description_en")),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
        (
            _("Effet"),
            dict(
                fields=(
                    "chance",
                    "duration",
                    "next_effect",
                    "cancel_effect",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Dégâts temporels"),
            dict(
                fields=(
                    "apply",
                    "interval",
                    "body_part",
                    "damage_type",
                    "raw_damage",
                    "min_damage",
                    "max_damage",
                    "damage_chance",
                ),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
    )
    inlines = [EffectModifierInline]
    list_display_links = ("name",)
    list_display = (
        "name",
        "title",
        "character",
        "chance",
        "duration",
        "next_effect",
        "cancel_effect",
        "has_damage",
    )
    list_editable = ()
    list_filter = ()
    search_fields = (
        "name",
        "title",
        "description",
    )
    ordering = (
        "name",
        "title",
    )
    autocomplete_fields = (
        "character",
        "next_effect",
        "cancel_effect",
    )
    actions = EntityAdmin.actions + [
        "duplicate",
    ]
    save_on_top = True
    actions_on_bottom = True

    def has_damage(self, obj):
        return bool(obj.damage_type and (obj.apply or obj.interval))

    has_damage.boolean = True
    has_damage.short_description = _("Dégâts ?")

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=_("Les effets sélectionnés ont été dupliqués."))

    duplicate.short_description = _("Dupliquer les effets sélectionnés")

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("next_effect", "cancel_effect")


@admin.register(CampaignEffect)
class CampaignEffectAdmin(CommonAdmin):
    """
    Administration des effets actifs sur les campagnes
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "campaign",
                    "effect",
                    "start_date",
                    "end_date",
                    "next_date",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "campaign",
        "effect",
        "start_date",
        "end_date",
        "next_date",
    )
    list_editable = ()
    list_filter = ("campaign",)
    ordering = (
        "campaign",
        "effect",
    )
    autocomplete_fields = (
        "campaign",
        "effect",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("campaign", "effect")
        if not request.user.is_superuser:
            queryset = queryset.filter(campaign__game_master=request.user)
        return queryset


@admin.register(CharacterEffect)
class CharacterEffectAdmin(CommonAdmin):
    """
    Administration des effets actifs sur les personnages
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "character",
                    "effect",
                    "start_date",
                    "end_date",
                    "next_date",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "character",
        "effect",
        "start_date",
        "end_date",
        "next_date",
    )
    list_editable = ()
    list_filter = (
        "character__campaign",
        "character__is_player",
    )
    ordering = (
        "character",
        "effect",
    )
    autocomplete_fields = (
        "character",
        "effect",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("character", "effect")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset


@admin.register(Loot)
class Loot(CommonAdmin):
    """
    Administration des butins
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "campaign",
                    "item",
                    "quantity",
                    "condition",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "campaign",
        "item",
        "quantity",
        "condition",
    )
    list_editable = ()
    list_filter = ("campaign",)
    ordering = (
        "campaign",
        "item",
    )
    autocomplete_fields = (
        "campaign",
        "item",
    )
    save_on_top = True
    actions_on_bottom = True

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("campaign", "item")
        if not request.user.is_superuser:
            queryset = queryset.filter(campaign__game_master=request.user)
        return queryset


class LootTemplateItemInline(EntityTabularInline):
    """
    Administration intégrée des templates de butins
    """

    model = LootTemplateItem
    extra = 1
    autocomplete_fields = ("item",)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("template", "item")


@admin.register(LootTemplate)
class LootTemplateAdmin(CommonAdmin):
    """
    Administration des butins
    """

    fieldsets = (
        (
            _("Informations générales"),
            dict(
                fields=(
                    "name",
                    "title",
                    "description",
                    "image",
                    "thumbnail",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Traductions"),
            dict(
                fields=(("name_fr", "name_en"), ("title_fr", "title_en"), ("description_fr", "description_en")),
                classes=(
                    "wide",
                    "collapse",
                ),
            ),
        ),
    )
    inlines = [LootTemplateItemInline]
    list_display_links = ("name",)
    list_display = (
        "name",
        "title",
        "count",
    )
    list_editable = ()
    list_filter = ()
    ordering = (
        "name",
        "title",
    )
    search_fields = (
        "name",
        "title",
        "description",
    )
    actions = CommonAdmin.actions + ("duplicate",)
    save_on_top = True
    actions_on_bottom = True

    def duplicate(self, request, queryset):
        """
        Action de duplication
        """
        for element in queryset:
            element.duplicate()
        self.message_user(request, message=_("Les modèles de butins sélectionnés ont été dupliqués."))

    duplicate.short_description = _("Dupliquer les butins sélectionnés")

    def count(self, obj):
        """
        Nombre d'objets dans le butin
        """
        return obj.count

    count.short_description = _("nombre")
    count.admin_order_field = "count"

    def get_queryset(self, request):
        return super().get_queryset(request).annotate(count=Count("items"))


@admin.register(RollHistory)
class RollHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de jets de compétences
    """

    fieldsets = (
        (
            _("Informations techniques"),
            dict(
                fields=(
                    "game_date",
                    "character",
                    "level",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Jet"),
            dict(
                fields=(
                    "stats",
                    "value",
                    "modifier",
                    "roll",
                    "success",
                    "critical",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "date",
        "character",
        "stats",
        "roll",
        "value",
        "success",
        "critical",
    )
    list_editable = ()
    list_filter = (
        "character__campaign",
        "character__is_player",
        "stats",
        "success",
        "critical",
        "date",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
    autocomplete_fields = ("character",)

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("character")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset


@admin.register(DamageHistory)
class DamageHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de dégâts
    """

    fieldsets = (
        (
            _("Informations techniques"),
            dict(
                fields=(
                    "game_date",
                    "character",
                    "level",
                    "source",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Dégâts de base"),
            dict(
                fields=(
                    "body_part",
                    "damage_type",
                    "raw_damage",
                    "min_damage",
                    "max_damage",
                    "base_damage",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Etat de la protection"),
            dict(
                fields=(
                    "armor",
                    "armor_threshold",
                    "armor_resistance",
                    "armor_damage",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Etat du personnage"),
            dict(
                fields=(
                    "damage_threshold",
                    "damage_resistance",
                    "real_damage",
                    "damage_rate",
                ),
                classes=("wide",),
            ),
        ),
    )
    search_fields = ("character",)
    list_display = (
        "date",
        "character",
        "body_part",
        "damage_type",
        "base_damage",
        "real_damage",
    )
    list_editable = ()
    list_filter = (
        "character__campaign",
        "character__is_player",
        "body_part",
        "damage_type",
        "date",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
    autocomplete_fields = (
        "character",
        "armor",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("character")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset


@admin.register(FightHistory)
class FightHistoryAdmin(CommonAdmin):
    """
    Administration des historiques de combats
    """

    fieldsets = (
        (
            _("Informations techniques"),
            dict(
                fields=("game_date",),
                classes=("wide",),
            ),
        ),
        (
            _("Attaquant"),
            dict(
                fields=(
                    "attacker",
                    "attacker_level",
                    "attacker_weapon",
                    "attacker_ammo",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Défenseur"),
            dict(
                fields=(
                    "defender",
                    "defender_level",
                    "defender_armor",
                    "range",
                    "body_part",
                ),
                classes=("wide",),
            ),
        ),
        (
            _("Combat"),
            dict(
                fields=(
                    "status",
                    "burst",
                    "hit_count",
                    "hit_modifier",
                    "hit_chance",
                    "hit_roll",
                    "success",
                    "critical",
                    "damage",
                ),
                classes=("wide",),
            ),
        ),
    )
    list_display = (
        "date",
        "attacker",
        "defender",
        "success",
        "critical",
        "status",
        "hit_roll",
        "hit_chance",
        "real_damage",
    )
    list_editable = ()
    list_filter = (
        "attacker__campaign",
        "attacker__is_player",
        "defender__is_player",
        "success",
        "critical",
        "status",
        "body_part",
        "date",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
    autocomplete_fields = (
        "attacker",
        "attacker_weapon",
        "attacker_ammo",
        "defender",
        "defender_armor",
        "damage",
    )

    def real_damage(self, obj):
        """
        Dégâts réels
        """
        return getattr(obj.damage, "real_damage", None)

    real_damage.short_description = _("dégâts")
    real_damage.admin_order_field = "damage__real_damage"

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("attacker", "defender")
        if not request.user.is_superuser:
            queryset = queryset.filter(
                Q(attacker__campaign__game_master=request.user) | Q(defender__campaign__game_master=request.user)
            )
        return queryset


@admin.register(Log)
class LogAdmin(CommonAdmin):
    """
    Administration des journaux
    """

    fields = (
        "game_date",
        "player",
        "character",
        "text",
        "private",
    )
    list_display = (
        "date",
        "game_date",
        "character",
        "player",
        "private",
    )
    list_editable = ()
    list_filter = (
        "character__campaign",
        "player",
    )
    ordering = ("-date",)
    date_hierarchy = "date"
    autocomplete_fields = (
        "player",
        "character",
    )

    def get_queryset(self, request):
        queryset = super().get_queryset(request).select_related("player", "character")
        if not request.user.is_superuser:
            queryset = queryset.filter(character__campaign__game_master=request.user)
        return queryset
