# coding: utf-8
from common.excel import ImportExport
from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from fallout.models import MODELS


class Command(BaseCommand):
    help = _("Importe les données de l'application depuis un document Excel")
    leave_locale_alone = True

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", dest="_all", help=_("Tous les champs"))
        parser.add_argument("--clean", action="store_true", dest="_clean", help=_("Validation"))
        parser.add_argument("--force", action="store_true", dest="_force", help=_("Forcé"))
        parser.add_argument("filename", type=str, help=_("Chemin du fichier"))

    def handle(self, _all=False, _clean=False, _force=False, filename=None, *args, **options):
        handler = ImportExport(models=MODELS, clean=_clean, force=_force, non_editables=_all)
        handler.importer(filename)
