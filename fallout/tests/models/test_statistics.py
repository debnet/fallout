# coding: utf-8
from unittest.mock import patch

from django.test import SimpleTestCase

from fallout.enums import ITEM_ARMOR, ITEM_HELMET, ITEM_TOOL, ITEM_WEAPON, LIST_SKILLS
from fallout.models import Character, Equipment, Item, ItemModifier, Statistics, Stats
from fallout.tests.models.base import CoreTestCase


class StatCalculationTests(SimpleTestCase):
    def test_computed_modifiers_accumulate_without_replacing_base(self):
        stats = Stats()
        stats.change_stats("max_health", 3)
        stats.change_stats("max_health", 2)
        self.assertEqual(stats.raw, {"max_health": 5})
        self.assertEqual(stats.max_health, 0)

    def test_detached_stats_ignore_noncomputed_changes(self):
        stats = Stats()
        before = stats.strength
        stats.change_stats("strength", 3)
        self.assertEqual(stats.strength, before)

    def test_stat_limits_and_character_modifiers(self):
        stats = Stats()
        stats.character = Character(strength=5, health=10)
        stats.strength = 5
        stats.change_stats("strength", 20, mini=1, maxi=10, limit=True)
        self.assertEqual(stats.strength, 10)
        stats.change_stats("strength", -20, mini=1, maxi=10, limit=True)
        self.assertEqual(stats.strength, 1)
        stats.change_stats("health", 7)
        self.assertEqual(stats.character.health, 17)
        self.assertEqual(stats.character_modifiers, {"health": 17})


class CharacterStatisticsTests(CoreTestCase):
    def test_equipment_modifiers_apply_per_copy_and_invalidate_calculated_stats(self):
        character = Character.objects.create(name="Calculated", campaign=self.campaign, is_player=True, strength=5)
        before = character.stats.strength
        tool = Item.objects.create(name="Tool bonus", type=ITEM_TOOL, durability=10)
        ItemModifier.objects.create(item=tool, stats="strength", min_value=1, max_value=1)
        tool.give(character, quantity=2)
        self.assertEqual(character.stats.strength, before + 2)
        self.assertIn(("strength", 2), [(name, value) for name, label, value in character.modifiers])
        self.assertFalse(Statistics.objects.get(character=character).obsolete)

    def test_fixed_stats_charge_and_inventory_lookup(self):
        item = Item.objects.create(name="Heavy", type=ITEM_TOOL, weight=2.5)
        equipment = item.give(self.hero, quantity=3)
        self.assertEqual(self.hero.current_charge, 7.5)
        self.assertEqual(self.hero.get_from_inventory(many=True, item=item), equipment)
        self.assertIsNone(self.hero.get_from_inventory(slot=ITEM_ARMOR))

    def test_generating_fixed_stats_resets_or_keeps_existing_skill_investment(self):
        for reset in (False, True):
            with self.subTest(reset=reset):
                character = Character.objects.create(
                    name="Generated", has_stats=False, is_player=True, tag_skills=["small_guns"], small_guns=20
                )
                character.generate_stats(reset=reset)
                character.refresh_from_db()
                self.assertGreater(character.max_health, 0)
                self.assertEqual(character.health, character.max_health)
                self.assertEqual(character.action_points, character.max_action_points)
                self.assertEqual(character.skill_points, character.used_skill_points)
                self.assertGreater(character.small_guns, 0)

    def test_randomization_spends_budget_between_tagged_and_other_skills(self):
        character = Character.objects.create(
            name="Randomized",
            has_stats=False,
            is_player=True,
            max_health=100,
            skill_points=4,
            tag_skills=["small_guns"],
        )
        with patch(
            "fallout.models.choice", side_effect=lambda skills: "small_guns" if "small_guns" in skills else "unarmed"
        ):
            character.randomize_stats(level=1, balance=50)
        character.refresh_from_db()
        self.assertEqual((character.small_guns, character.unarmed, character.used_skill_points), (2, 1, 4))
        self.assertTrue(
            all(getattr(character, skill) == 0 for skill in LIST_SKILLS if skill not in ("small_guns", "unarmed"))
        )

    def test_quick_equipment_accepts_ids_and_reloads_without_action_cost(self):
        weapon, ammo = self.armed_inventory()
        weapon_id, ammo_id = weapon.item_id, ammo.item_id
        self.hero.equipments.all().delete()
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100)
        helmet = Item.objects.create(name="Helmet", type=ITEM_HELMET, durability=100)
        self.hero.equip(
            armor=armor, helmet=helmet.pk, weapon=weapon_id, ammo=str(ammo_id), ammo_min_count=10, ammo_max_count=10
        )
        equipment = {entry.slot: entry for entry in self.hero.equipments.all()}
        self.assertEqual(set(equipment), {ITEM_ARMOR, ITEM_HELMET, ITEM_WEAPON, "ammo"})
        self.assertEqual(equipment[ITEM_WEAPON].clip_count, 6)
        self.assertEqual(equipment["ammo"].quantity, 4)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.action_points, 10)

    def test_quick_equipment_preserves_requested_condition(self):
        armor = Item.objects.create(name="Worn armor", type=ITEM_ARMOR, durability=100)
        for percentage in (25, 40, 50, 75, 99, 100):
            with self.subTest(percentage=percentage):
                self.hero.equipments.all().delete()
                self.hero.equip(armor=armor, armor_min_condition=percentage, armor_max_condition=percentage)
                self.assertEqual(Equipment.objects.get(character=self.hero, item=armor).condition, percentage / 100.0)

    def test_working_and_resting_needs_have_different_rates(self):
        self.hero.has_needs = True
        self.hero.endurance = 5
        self.hero.sleep = 100
        self.hero.update_needs(hours=2, resting=False)
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.thirst, self.hero.hunger, self.hero.sleep), (30, 20, 110))
        self.hero.update_needs(hours=2, resting=True)
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.thirst, self.hero.hunger, self.hero.sleep), (52.5, 35, 95))

    def test_environmental_radiation_uses_resistance_without_recording_damage_history(self):
        self.hero.radiation_resistance = 25
        damages = self.hero.update_needs(hours=2, radiation=10, needs=False, resting=False)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.rads, 15)
        self.assertEqual(len(damages), 1)
        self.assertEqual(damages[0].real_damage, 15)
        self.assertIsNone(damages[0].pk)

    def test_clear_turn_restores_all_action_points_without_advancing_time(self):
        self.campaign.current_character = self.hero
        self.campaign.save()
        Character.objects.filter(campaign=self.campaign).update(action_points=0)
        before = self.campaign.current_game_date
        self.campaign.clear_turn()
        self.campaign.refresh_from_db()
        self.assertIsNone(self.campaign.current_character_id)
        self.assertEqual(self.campaign.current_game_date, before)
        self.assertEqual(
            list(Character.objects.filter(campaign=self.campaign).values_list("action_points", flat=True)), [10, 10]
        )
