# coding: utf-8
from unittest.mock import patch

from django.core.exceptions import ValidationError as ModelValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from fallout import api
from fallout.api_utils import api_view_with_serializer
from fallout.enums import ITEM_WEAPON, MODE_THROW
from fallout.models import Campaign, Character, DamageHistory, Equipment, FightHistory, Item, Loot, Statistics
from fallout.tests.api.base import ApiTestCase


class ApiTransactionTests(ApiTestCase):
    def test_business_failure_rolls_back_partial_writes(self):
        def fail(character, **kwargs):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            raise AssertionError("Action impossible")

        with patch.object(Character, "damage", fail):
            response = api.character_damage(self.request("post", self.gm, {"raw_damage": 1}), character_id=self.hero.pk)
        self.assertEqual(response.status_code, 400)
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_collective_damage_is_all_or_nothing(self):
        damage = Character.damage

        def fail_second(character, **kwargs):
            if character.pk == self.ally.pk:
                raise AssertionError("Second character failed")
            return damage(character, **kwargs)

        health = self.hero.health
        with patch.object(Character, "damage", fail_second):
            response = api.campaign_damage(
                self.request(
                    "post",
                    self.gm,
                    {
                        "characters": [self.hero.pk, self.ally.pk],
                        "raw_damage": 1,
                    },
                ),
                campaign_id=self.a.pk,
            )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(DamageHistory.objects.exists())
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, health)

    def test_unexpected_failure_is_hidden_and_rolled_back(self):
        def fail(character, **kwargs):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            raise RuntimeError("secret database details")

        with patch.object(Character, "damage", fail), self.assertLogs("fallout.api_utils", level="ERROR"):
            response = api.character_damage(self.request("post", self.gm, {"raw_damage": 1}), character_id=self.hero.pk)
        self.assertEqual(response.status_code, 500)
        self.assertNotIn("secret database details", str(response.data))
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_serialization_failure_rolls_back(self):
        class BrokenSerializer(serializers.Serializer):
            def to_representation(self, instance):
                raise ValidationError("Unserializable")

        @api_view_with_serializer(["POST"], serializer=BrokenSerializer)
        def operation(request):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            return self.a

        response = operation(self.request("post", self.gm))
        self.assertEqual(response.status_code, 400)
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_json_render_failure_rolls_back(self):
        @api_view_with_serializer(["POST"])
        def operation(request):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            return {"invalid": object()}

        # common prévalide le JSON et propage les erreurs serveur après rollback.
        with self.assertRaises(TypeError):
            operation(self.request("post", self.gm))
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_input_validation_has_context_and_rolls_back_its_writes(self):
        campaign_id = self.a.pk

        class InputSerializer(serializers.Serializer):
            def validate(serializer, data):
                self.assertIn("request", serializer.context)
                self.assertIn("view", serializer.context)
                Campaign.objects.filter(pk=campaign_id).update(money=123)
                raise ValidationError("Invalid input")

        @api_view_with_serializer(["POST"], input_serializer=InputSerializer)
        def operation(request):
            self.fail("A rejected input must not reach the operation")

        response = operation(self.request("post", self.gm))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data, {"non_field_errors": ["Invalid input"]})
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_django_validation_error_is_converted_by_common_after_rollback(self):
        @api_view_with_serializer(["POST"])
        def operation(request):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            raise ModelValidationError({"money": "Rejected"})

        response = operation(self.request("post", self.gm))
        self.assertEqual(response.status_code, 400)
        self.assertIn("money", response.data)
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_error_response_is_preserved_and_rolls_back(self):
        @api_view_with_serializer(["POST"])
        def operation(request):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            return Response({"error": "Rejected"}, status=409)

        response = operation(self.request("post", self.gm))
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data, {"error": "Rejected"})
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_simulation_rolls_back_writes_from_output_serialization(self):
        campaign_id = self.a.pk

        class InputSerializer(serializers.Serializer):
            simulation = serializers.BooleanField()

        class OutputSerializer(serializers.Serializer):
            def to_representation(serializer, instance):
                Campaign.objects.filter(pk=campaign_id).update(money=123)
                return {"id": instance.pk}

        @api_view_with_serializer(["POST"], input_serializer=InputSerializer, serializer=OutputSerializer)
        def operation(request):
            return self.a

        response = operation(self.request("post", self.gm, {"simulation": True}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"id": self.a.pk})
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_http_simulation_rolls_back_even_an_accidental_write(self):
        def simulate(character, **kwargs):
            Campaign.objects.filter(pk=self.a.pk).update(money=123)
            return None

        with patch.object(Character, "fight", simulate):
            response = api.character_fight(
                self.request(
                    "post",
                    self.gm,
                    {
                        "target": self.ally.pk,
                        "simulation": True,
                    },
                ),
                character_id=self.hero.pk,
            )
        self.assertEqual(response.status_code, 200)
        self.a.refresh_from_db()
        self.assertEqual(self.a.money, 0)

    def test_http_fight_simulation_returns_json_without_persisting_changes(self):
        models = (Character, Statistics, Equipment, Loot, DamageHistory, FightHistory)
        before = {model: list(model.objects.order_by("pk").values()) for model in models}
        response = api.character_fight(
            self.request(
                "post",
                self.gm,
                {
                    "target": self.ally.pk,
                    "weapon_type": "unarmed",
                    "force_success": True,
                    "simulation": True,
                },
            ),
            character_id=self.hero.pk,
        )
        self.assertEqual(response.status_code, 200, response.data)
        response.render()
        after = {model: list(model.objects.order_by("pk").values()) for model in models}
        self.assertEqual(before, after)

    def test_throwing_weapon_simulation_does_not_write(self):
        weapon = Item.objects.create(
            name="Throwing knife",
            type=ITEM_WEAPON,
            attack_mode=MODE_THROW,
            skill="throwing",
            min_range=0,
            max_range=10,
            raw_damage=1,
        )
        equipment = Equipment.objects.create(character=self.hero, item=weapon, slot=ITEM_WEAPON, quantity=2)
        models = (Character, Statistics, Equipment, Loot, DamageHistory, FightHistory)
        before = {model: list(model.objects.order_by("pk").values()) for model in models}
        result = self.hero.fight(self.ally, simulation=True, force_success=True, target_range=1)
        self.assertIsNotNone(result)
        after = {model: list(model.objects.order_by("pk").values()) for model in models}
        self.assertEqual(before, after)
        equipment.refresh_from_db()
        self.assertEqual(equipment.quantity, 2)
