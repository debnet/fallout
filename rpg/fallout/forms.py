# coding: utf-8
from django import forms
from django.utils.translation import ugettext_lazy as _


class RandomizeCharacterForm(forms.Form):
    level = forms.IntegerField(min_value=0, initial=0, label=_("Niveau"))
    rate = forms.FloatField(min_value=0.0, max_value=1.0, initial=0.0, label=_("Ratio"))
