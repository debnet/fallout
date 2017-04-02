# coding: utf-8
from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class FalloutConfig(AppConfig):
    name = 'rpg.fallout'
    verbose_name = _("Fallout RPG")
