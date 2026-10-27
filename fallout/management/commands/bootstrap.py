"""Initialize a new installation without replaying fixtures over existing data."""

import os

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management import BaseCommand, CommandError, call_command
from django.db import transaction

from fallout.models import Character, Item


class Command(BaseCommand):
    help = "Load admin, items and creatures on a fresh database and replace the fixture admin password."

    @transaction.atomic
    def handle(self, *args, **options):
        player = get_user_model()
        if player.objects.exists():
            self.stdout.write("Existing users found: initial fixtures skipped (no data or password overwritten).")
            return
        if Item.objects.exists() or Character.objects.exists():
            raise CommandError("Existing catalogue data found: refusing to overwrite it with initial fixtures.")
        password = os.environ.get("FALLOUT_ADMIN_PASSWORD", "")
        if not password:
            raise CommandError("Set FALLOUT_ADMIN_PASSWORD for the first initialization.")
        try:
            validate_password(password, user=player(username="admin"))
        except ValidationError as error:
            raise CommandError(" ".join(error.messages)) from error
        call_command("loaddata", "admin", "items", "creatures", verbosity=options["verbosity"])
        admin = player.objects.get(username="admin")
        admin.set_password(password)
        admin.save(update_fields=["password"])
        self.stdout.write(self.style.SUCCESS("Initial fixtures loaded; admin password replaced."))
