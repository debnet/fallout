# coding: utf-8
from unittest.mock import patch

from django.urls import reverse
from rest_framework.test import APITestCase

from fallout import api
from fallout.models import (
    Campaign,
    Character,
    DamageHistory,
    Effect,
    Player,
)
from fallout.tests.api.base import ApiTestCase


class LevelupApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.player = Player.objects.create_user("player")
        cls.gm = Player.objects.create_user("gm")
        cls.stranger = Player.objects.create_user("stranger")
        cls.admin = Player.objects.create_superuser("admin", password=None)
        campaign = Campaign.objects.create(name="Campaign", game_master=cls.gm)
        cls.character = Character.objects.create(
            name="Hero",
            campaign=campaign,
            player=cls.player,
            is_player=True,
            has_stats=False,
            max_health=10,
            max_action_points=5,
            small_guns=1,
            skill_points=4,
            enable_levelup=True,
        )

    def setUp(self):
        self.url = reverse("fallout-api:character_levelup", args=(self.character.pk,))
        self.client.force_authenticate(self.player)

    def test_owner_can_improve_skill_with_default_increment(self):
        response = self.client.post(self.url, {"stats": "small_guns"})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            response.data,
            {
                "stats": "small_guns",
                "value": 2,
                "skill_points": 4,
                "used_skill_points": 4,
            },
        )
        self.character.refresh_from_db()
        self.assertEqual(self.character.small_guns, 2)

    def test_disabled_levelup_forbids_owner(self):
        Character.objects.filter(pk=self.character.pk).update(enable_levelup=False)
        self.assertEqual(self.client.post(self.url, {"stats": "small_guns"}).status_code, 403)

    def test_master_and_superuser_can_levelup_even_when_disabled(self):
        for user in (self.gm, self.admin):
            with self.subTest(user=user.username):
                Character.objects.filter(pk=self.character.pk).update(enable_levelup=False, small_guns=1)
                self.client.force_authenticate(user)
                response = self.client.post(self.url, {"stats": "small_guns"})
                self.assertEqual(response.status_code, 200, response.data)

    def test_other_player_is_forbidden(self):
        self.client.force_authenticate(self.stranger)
        self.assertEqual(self.client.post(self.url, {"stats": "small_guns"}).status_code, 403)

    def test_invalid_input_and_insufficient_budget_do_not_change_skill(self):
        for data in (
            {},
            {"stats": "strength"},
            {"stats": "unknown"},
            {"stats": "small_guns", "value": 0},
            {"stats": "small_guns", "value": -1},
            {"stats": "small_guns", "value": 1.5},
            {"stats": "small_guns", "value": 2},
        ):
            with self.subTest(data=data):
                self.assertEqual(self.client.post(self.url, data).status_code, 400)
                self.character.refresh_from_db()
                self.assertEqual(self.character.small_guns, 1)

    def test_positive_custom_increment(self):
        Character.objects.filter(pk=self.character.pk).update(skill_points=10)
        response = self.client.post(self.url, {"stats": "small_guns", "value": 3})
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data["value"], 4)
        self.assertEqual(response.data["used_skill_points"], 8)

    def test_anonymous_is_forbidden(self):
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url, {"stats": "small_guns"}).status_code, 401)

    def test_missing_character_returns_404(self):
        url = reverse("fallout-api:character_levelup", args=(0,))
        self.assertEqual(self.client.post(url, {"stats": "small_guns"}).status_code, 404)


class CommandPermissionTests(ApiTestCase):
    def test_player_can_read_own_calculated_stats(self):
        response = api.character_stats(self.request(user=self.player), character_id=self.hero.pk)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data)
        response = api.character_stats(self.request(user=self.player), character_id=self.stranger.pk)
        self.assertEqual(response.status_code, 404)

    def test_cross_campaign_targets_and_fail_targets_are_rejected(self):
        for data in ({"target": self.stranger.pk}, {"target": self.ally.pk, "fail_target": self.stranger.pk}):
            with self.subTest(data=data), patch.object(Character, "fight") as fight:
                response = api.character_fight(self.request("post", self.gm, data), character_id=self.hero.pk)
                self.assertEqual(response.status_code, 400)
                fight.assert_not_called()

    def test_burst_nested_target_is_restricted(self):
        with patch.object(Character, "burst") as burst:
            response = api.character_burst(
                self.request(
                    "post",
                    self.gm,
                    {
                        "targets": [{"target": self.stranger.pk, "target_range": 1}],
                    },
                ),
                character_id=self.hero.pk,
            )
            self.assertEqual(response.status_code, 400)
            burst.assert_not_called()

    def test_same_campaign_target_is_accepted(self):
        with patch.object(Character, "fight", return_value=None) as fight:
            response = api.character_fight(
                self.request("post", self.gm, {"target": self.ally.pk}), character_id=self.hero.pk
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(fight.call_args.kwargs["target"].pk, self.ally.pk)
            self.assertEqual(fight.call_args.kwargs["target_range"], 1)

    def test_burst_target_range_defaults_to_one_and_preserves_explicit_value(self):
        for target_data, distance in (({}, 1), ({"target_range": 5}, 5)):
            with self.subTest(distance=distance), patch.object(Character, "burst", return_value=[]) as burst:
                response = api.character_burst(
                    self.request("post", self.gm, {"targets": [{"target": self.ally.pk, **target_data}]}),
                    character_id=self.hero.pk,
                )
                self.assertEqual(response.status_code, 200, response.data)
                target, target_range = burst.call_args.kwargs["targets"][0]
                self.assertEqual(target.pk, self.ally.pk)
                self.assertEqual(target_range, distance)

    def test_fail_target_can_be_the_attacker_in_same_campaign(self):
        with patch.object(Character, "fight", return_value=None) as fight:
            response = api.character_fight(
                self.request(
                    "post",
                    self.gm,
                    {
                        "target": self.ally.pk,
                        "fail_target": self.hero.pk,
                    },
                ),
                character_id=self.hero.pk,
            )
            self.assertEqual(response.status_code, 200)
            fight.assert_called_once()

    def test_private_effect_from_another_campaign_cannot_be_applied(self):
        effect = Effect.objects.create(name="Private trait", character=self.stranger)
        with patch.object(Effect, "affect") as affect:
            response = api.character_effect(
                self.request("post", self.gm, {"effect": effect.pk}), character_id=self.hero.pk
            )
            self.assertEqual(response.status_code, 400)
            affect.assert_not_called()

    def test_copy_private_source_is_rejected_and_template_is_allowed(self):
        with patch.object(Character, "duplicate", return_value=self.template) as duplicate:
            response = api.character_copy(
                self.request("post", self.gm, {"campaign": self.a.pk}), character_id=self.stranger.pk
            )
            self.assertEqual(response.status_code, 404)
            duplicate.assert_not_called()
            response = api.character_copy(
                self.request("post", self.gm, {"campaign": self.a.pk}), character_id=self.template.pk
            )
            self.assertEqual(response.status_code, 200)
            duplicate.assert_called_once()

    def test_campaign_damage_accepts_real_characters_and_rejects_foreign_ones(self):
        response = api.campaign_damage(
            self.request(
                "post",
                self.gm,
                {
                    "characters": [self.hero.pk],
                    "raw_damage": 1,
                },
            ),
            campaign_id=self.a.pk,
        )
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(DamageHistory.objects.filter(character=self.hero).count(), 1)
        response = api.campaign_damage(
            self.request(
                "post",
                self.gm,
                {
                    "characters": [self.stranger.pk],
                    "raw_damage": 1,
                },
            ),
            campaign_id=self.a.pk,
        )
        self.assertEqual(response.status_code, 400)

    def test_nonexistent_campaign_is_not_a_successful_empty_roll(self):
        response = api.campaign_roll(
            self.request("post", self.player, {"stats": "luck", "group": 0}), campaign_id=99999
        )
        self.assertEqual(response.status_code, 404)
