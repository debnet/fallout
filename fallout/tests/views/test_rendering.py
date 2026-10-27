# coding: utf-8
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import messages
from django.urls import reverse

from fallout.models import Character
from fallout.tests.views.base import HtmlViewTests


class ThumbnailPathTests(HtmlViewTests):
    def setUp(self):
        super().setUp()
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.root = self.directory / "static/fallout/img/thumbnails"
        (self.root / "characters").mkdir(parents=True)
        (self.root / "characters/hero.png").touch()
        self.outside = self.directory / "outside"
        self.outside.mkdir()
        (self.outside / "private-marker.png").touch()
        self.settings_override = self.settings(STATIC_ROOT=str(self.directory / "static"), DEBUG=False)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.url = reverse("fallout:thumbnails")

    def test_root_and_relative_subdirectory_remain_accessible(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "?dir=characters")
        response = self.client.get(self.url, {"dir": "characters"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "thumbnails/characters/hero.png")

    def test_absolute_path_is_rejected(self):
        for directory in (self.outside, self.root / "characters"):
            with self.subTest(directory=directory):
                response = self.client.get(self.url, {"dir": str(directory)})
                self.assertEqual(response.status_code, 404)
                self.assertNotContains(response, "private-marker", status_code=404)

    def test_parent_traversal_and_missing_directory_are_rejected(self):
        for directory in ("../outside", "characters/../../outside", "missing", "characters/hero.png"):
            with self.subTest(directory=directory):
                self.assertEqual(self.client.get(self.url, {"dir": directory}).status_code, 404)

    def test_symlink_cannot_escape_thumbnail_root(self):
        (self.root / "escape").symlink_to(self.outside, target_is_directory=True)
        self.assertEqual(self.client.get(self.url, {"dir": "escape"}).status_code, 404)

    def test_debug_fallback_remains_confined_to_source_thumbnail_directory(self):
        base = self.directory / "source"
        source_root = base / "fallout/static/fallout/img/thumbnails"
        (source_root / "items").mkdir(parents=True)
        (source_root / "items/tool.png").touch()
        (source_root / "escape").symlink_to(self.outside, target_is_directory=True)
        with self.settings(DEBUG=True, BASE_DIR=str(base)):
            response = self.client.get(self.url, {"dir": "items"})
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "thumbnails/items/tool.png")
            self.assertEqual(self.client.get(self.url, {"dir": "escape"}).status_code, 404)


class MessageEscapingTests(HtmlViewTests):
    def setUp(self):
        super().setUp()
        self.client.force_login(self.gm)

    def test_error_message_escapes_input_but_preserves_strong_markup(self):
        payload = '<img src=x onerror="alert(1)">'
        for url in (self.character_url, reverse("fallout:campaign", args=(self.campaign.pk,))):
            with self.subTest(url=url):
                response = self.client.post(url, {"type": "money", "money": payload})
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, "<strong>Erreur</strong>")
                self.assertContains(response, "&lt;img src=x")
                self.assertNotContains(response, payload)
                self.assertNotContains(response, "&lt;strong&gt;Erreur&lt;/strong&gt;")

    def test_game_message_escapes_labels_but_preserves_strong_markup(self):
        result = SimpleNamespace(
            message_level=messages.SUCCESS,
            pre_label="Hero <b>name</b>",
            long_label="Result <script>alert(1)</script>",
        )
        with patch.object(Character, "roll", return_value=result):
            response = self.client.post(self.character_url, {"type": "stats", "roll": "strength"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Hero &lt;b&gt;name&lt;/b&gt;</strong>")
        self.assertContains(response, "Result &lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertNotContains(response, "<script>alert(1)</script>")

    def test_burst_summary_preserves_counts_and_escapes_character_names(self):
        defender = Character.objects.create(
            name="Enemy <em>name</em>", campaign=self.campaign, is_player=True, has_stats=False
        )
        results = [
            SimpleNamespace(
                attacker=self.character, defender=defender, success=True, damage=SimpleNamespace(real_damage=8)
            ),
            SimpleNamespace(attacker=self.character, defender=defender, success=False, damage=None),
        ]
        with patch.object(Character, "burst", return_value=results):
            response = self.client.post(
                self.character_url,
                {"type": "burst", "targets": [defender.pk], "ranges": [1], "weapon_type": "primary"},
            )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<strong>Hero vs Enemy &lt;em&gt;name&lt;/em&gt;</strong>")
        self.assertContains(response, "1 coups ratés et 1 coups au but pour 8 dégâts")
