# coding: utf-8
from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from common.excel import ImportExport
from fallout.models import MODELS


class Command(BaseCommand):
    help = _("Exporte les données de l'application vers un document Excel")
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument('--all', action='store_true', dest='_all', help=_("Tous les champs"))
        parser.add_argument('filename', type=str, help=_("Chemin du fichier"))

    def handle(self, _all=False, filename=None, *args, **options):
        handler = ImportExport(models=MODELS, non_editables=_all)
        handler.exporter(filename)
