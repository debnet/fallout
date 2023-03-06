# coding: utf-8
from django import forms
from django.utils.translation import gettext_lazy as _
from multiselectfield.forms.fields import MultiSelectFormField

from fallout.enums import *  # noqa
from fallout.models import *  # noqa


class CampaignForm(forms.Form):
    """
    Formulaire pour choisir une campagne
    """

    campaign = forms.ModelChoiceField(required=False, queryset=Campaign.objects.order_by("name"), label=_("Campagne"))


class DuplicateCharacterForm(CampaignForm):
    """
    Formulaire pour dupliquer un ou plusieurs personnages
    """

    count = forms.IntegerField(min_value=1, initial=1, label=_("Nombre"))
    name = forms.CharField(required=False, label=_("Nom"))
    is_active = forms.BooleanField(required=False, initial=True, label=_("Actif ?"))


class RollCharacterForm(forms.Form):
    """
    Formulaire pour effectuer un lancer de compétence sur un personnage
    """

    stats = forms.ChoiceField(choices=ROLL_STATS, label=_("Statistique"))
    modifier = forms.IntegerField(initial=0, label=_("Modificateur"))


class FightCharacterForm(forms.Form):
    """
    Formulaire pour attaquer un autre personnage
    """

    target = forms.ModelChoiceField(queryset=Character.objects.order_by("name"), label=_("Personnage"))
    target_range = forms.IntegerField(min_value=1, initial=1, label=_("Distance"))
    target_part = forms.ChoiceField(choices=BODY_PARTS, label=_("Partie du corps"))
    hit_modifier = forms.IntegerField(min_value=0, initial=0, label=_("Modificateur"))
    is_action = forms.BooleanField(initial=False, label=_("Action ?"))
    weapon_type = forms.ChoiceField(initial=WEAPON_TYPE_PRIMARY, choices=WEAPON_TYPES, label=_("Aucune arme ?"))


class DamageCharacterForm(forms.Form):
    """
    Formulaire pour infliger des dégâts à un personnage
    """

    raw_damage = forms.IntegerField(initial=0, label=_("dégâts bruts"))
    min_damage = forms.IntegerField(initial=0, label=_("dégâts min."))
    max_damage = forms.IntegerField(initial=0, label=_("dégâts max."))
    damage_type = forms.ChoiceField(choices=DAMAGES_TYPES, label=_("type de dégâts"))
    body_part = forms.ChoiceField(choices=BODY_PARTS, label=_("partie du corps"))
    threshold_modifier = forms.IntegerField(initial=0, label=_("modificateur d'absorption"))
    threshold_rate_modifier = forms.IntegerField(initial=0, label=_("modificateur taux d'absorption"))
    resistance_modifier = forms.IntegerField(initial=0, label=_("modificateur de résistance"))


class EquipCharacterForm(forms.Form):
    """
    Formulaire pour équiper un personnage
    """

    armor = forms.ModelChoiceField(
        required=False, queryset=Item.objects.filter(type=ITEM_ARMOR).order_by("name"), label=_("Armure")
    )
    armor_min_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition min. armure"))
    armor_max_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition max. armure"))
    helmet = forms.ModelChoiceField(
        required=False, queryset=Item.objects.filter(type=ITEM_HELMET).order_by("name"), label=_("Casque")
    )
    helmet_min_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition min. casque"))
    helmet_max_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition max. casque"))
    weapon = forms.ModelChoiceField(
        required=False, queryset=Item.objects.filter(type=ITEM_WEAPON).order_by("name"), label=_("Arme")
    )
    weapon_min_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition min. arme"))
    weapon_max_condition = forms.IntegerField(min_value=0, max_value=100, initial=100, label=_("Condition max. arme"))
    ammo = forms.ModelChoiceField(
        required=False, queryset=Item.objects.filter(type=ITEM_AMMO).order_by("name"), label=_("Munition")
    )
    ammo_min_count = forms.IntegerField(min_value=0, initial=10, label=_("Nombre min. de munitions"))
    ammo_max_count = forms.IntegerField(min_value=0, initial=20, label=_("Nombre max. de munitions"))


class RandomizeCharacterSpecialForm(forms.Form):
    """
    Formulaire pour randomiser le SPECIAL d'un personnage
    """

    points = forms.IntegerField(min_value=1, initial=40, required=False, label=_("Points"))


class RandomizeCharacterStatsForm(forms.Form):
    """
    Formulaire pour randomiser les compétences d'un personnage
    """

    level = forms.IntegerField(min_value=0, initial=0, label=_("Niveau"))
    rate = forms.FloatField(min_value=0.0, max_value=1.0, initial=0.5, label=_("Ratio"))


class RandomizeCharacterForm(EquipCharacterForm, RandomizeCharacterStatsForm, RandomizeCharacterSpecialForm):
    """
    Formulaire pour générer aléatoirement un nouveau personnage et son équipement
    """


class QuickCreateCharacterForm(RandomizeCharacterForm):
    """
    Formulaire pour créer rapidement un personnage
    """

    name = forms.CharField(label=_("Nom"))
    race = forms.ChoiceField(choices=RACES, label=_("Race"))
    strength = forms.IntegerField(min_value=1, required=False, label=_("Force"))
    perception = forms.IntegerField(min_value=1, required=False, label=_("Perception"))
    endurance = forms.IntegerField(min_value=1, required=False, label=_("Endurance"))
    charisma = forms.IntegerField(min_value=1, required=False, label=_("Charisme"))
    intelligence = forms.IntegerField(min_value=1, required=False, label=_("Intelligence"))
    agility = forms.IntegerField(min_value=1, required=False, label=_("Agilité"))
    luck = forms.IntegerField(min_value=1, required=False, label=_("Chance"))
    tag_skills = MultiSelectFormField(choices=SKILLS, required=False, label=_("Spécialités"))


__all__ = (
    "CampaignForm",
    "DuplicateCharacterForm",
    "RollCharacterForm",
    "FightCharacterForm",
    "DamageCharacterForm",
    "EquipCharacterForm",
    "RandomizeCharacterSpecialForm",
    "RandomizeCharacterStatsForm",
    "RandomizeCharacterForm",
    "QuickCreateCharacterForm",
)
