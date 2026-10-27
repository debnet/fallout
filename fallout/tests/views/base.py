# coding: utf-8
from django.test import TestCase, override_settings
from django.urls import reverse

from fallout.models import Campaign, Character, Player


@override_settings(COMPRESS_ENABLED=False, INTERNAL_IPS=[])
class HtmlViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gm = Player.objects.create_user("view-gm")
        cls.player = Player.objects.create_user("view-player")
        cls.other = Player.objects.create_user("view-other")
        cls.campaign = Campaign.objects.create(name="Views", game_master=cls.gm, needs=False)
        cls.character = Character.objects.create(
            name="Hero",
            campaign=cls.campaign,
            player=cls.player,
            is_player=True,
            has_stats=False,
            has_needs=False,
            max_health=100,
            max_action_points=10,
            enable_logs=True,
        )

    def setUp(self):
        self.client.force_login(self.player)
        self.character_url = reverse("fallout:character", args=(self.character.pk,))
