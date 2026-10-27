import os
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, override_settings

from fallout.models import Character, Item


class BootstrapTests(TestCase):
    def test_missing_password_does_not_import_data(self):
        with patch.dict(os.environ, {"FALLOUT_ADMIN_PASSWORD": ""}):
            with self.assertRaisesMessage(CommandError, "FALLOUT_ADMIN_PASSWORD"):
                call_command("bootstrap", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())
        self.assertFalse(Item.objects.exists())

    @override_settings(
        AUTH_PASSWORD_VALIDATORS=[{"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"}]
    )
    def test_weak_password_is_rejected(self):
        with patch.dict(os.environ, {"FALLOUT_ADMIN_PASSWORD": "short"}):
            with self.assertRaises(CommandError):
                call_command("bootstrap", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())

    def test_existing_catalogue_without_users_is_not_overwritten(self):
        item = Item.objects.create(name="Existing catalogue item")
        with self.assertRaisesMessage(CommandError, "Existing catalogue data"):
            call_command("bootstrap", stdout=StringIO())
        item.refresh_from_db()
        self.assertEqual(item.name, "Existing catalogue item")
        self.assertFalse(get_user_model().objects.exists())

    def test_fixtures_are_loaded_once_and_admin_password_is_replaced(self):
        password = "Isolated-bootstrap-password-83!"
        with patch.dict(os.environ, {"FALLOUT_ADMIN_PASSWORD": password}):
            call_command("bootstrap", stdout=StringIO(), verbosity=0)
        admin = get_user_model().objects.get(username="admin")
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.check_password(password))
        self.assertTrue(Item.objects.exists())
        self.assertTrue(Character.objects.exists())
        count = Item.objects.count()
        admin.set_password("Changed-after-install-123!")
        admin.save()
        with patch.dict(os.environ, {"FALLOUT_ADMIN_PASSWORD": ""}):
            with patch("fallout.management.commands.bootstrap.call_command") as load:
                call_command("bootstrap", stdout=StringIO())
                load.assert_not_called()
        admin.refresh_from_db()
        self.assertTrue(admin.check_password("Changed-after-install-123!"))
        self.assertEqual(Item.objects.count(), count)

    def test_fixture_failure_rolls_back_admin_creation(self):
        def failing_import(*args, **kwargs):
            get_user_model().objects.create(username="admin")
            raise CommandError("Fixture failure")

        with (
            patch.dict(os.environ, {"FALLOUT_ADMIN_PASSWORD": "Valid-bootstrap-password-83!"}),
            patch("fallout.management.commands.bootstrap.call_command", side_effect=failing_import),
        ):
            with self.assertRaisesMessage(CommandError, "Fixture failure"):
                call_command("bootstrap", stdout=StringIO())
        self.assertFalse(get_user_model().objects.exists())
