# coding: utf-8
import os
from unittest import TestCase
from unittest.mock import patch

from fallout_cli import main


class ManagementEntryPointTests(TestCase):
    def test_default_settings_are_selected_before_management_command_runs(self):
        with (
            patch.dict(os.environ, {}, clear=True),
            patch("sys.argv", ["fallout-rpg", "check"]),
            patch("configurations.management.execute_from_command_line") as execute,
        ):
            main()
            self.assertEqual(os.environ["DJANGO_SETTINGS_MODULE"], "rpg.settings")
            self.assertEqual(os.environ["DJANGO_CONFIGURATION"], "Test")
            self.assertNotIn("DJANGO_SECRET_KEY", os.environ)
            execute.assert_called_once_with(["fallout-rpg", "check"])

    def test_explicit_settings_and_secret_key_are_preserved(self):
        environment = {
            "DJANGO_SETTINGS_MODULE": "custom.settings",
            "DJANGO_CONFIGURATION": "Prod",
            "DJANGO_SECRET_KEY": "existing-test-key",
        }
        with (
            patch.dict(os.environ, environment, clear=True),
            patch("sys.argv", ["fallout-rpg", "migrate", "--plan"]),
            patch("configurations.management.execute_from_command_line") as execute,
        ):
            main()
            self.assertEqual(dict(os.environ), environment)
            execute.assert_called_once_with(["fallout-rpg", "migrate", "--plan"])
