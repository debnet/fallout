# coding: utf-8
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class FalloutConfig(AppConfig):
    name = 'fallout'
    verbose_name = _("Fallout RPG")
    default_auto_field = 'django.db.models.AutoField'
