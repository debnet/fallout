# coding: utf-8
from django import forms
from django.utils.translation import gettext_lazy as _

from fallout.models import *  # noqa
from fallout.enums import ROLL_STATS, BODY_PARTS


class DuplicateCharacterForm(forms.Form):
    """
    Formulaire pour dupliquer un ou plusieurs personnages
    """
    count = forms.IntegerField(min_value=0, initial=1, label=_("Nombre"))
    campaign = forms.ModelChoiceField(required=False, queryset=Campaign.objects.order_by('name'), label=_("Campagne"))


class RandomizeCharacterForm(forms.Form):
    """
    Formulaire pour randomiser les compétences d'un personnage
    """
    level = forms.IntegerField(min_value=0, initial=0, label=_("Niveau"))
    rate = forms.FloatField(min_value=0.0, max_value=1.0, initial=0.0, label=_("Ratio"))


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
    target = forms.ModelChoiceField(queryset=Character.objects.order_by('name'), label=_("Personnage"))
    target_range = forms.IntegerField(min_value=1, initial=1, label=_("Distance"))
    target_part = forms.ChoiceField(choices=BODY_PARTS, label=_("Cible"))
    hit_modifier = forms.IntegerField(min_value=0, initial=0, label=_("Modificateur"))
    is_action = forms.BooleanField(initial=False, label=_("Action ?"))
