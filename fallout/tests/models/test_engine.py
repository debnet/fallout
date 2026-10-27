# coding: utf-8
from datetime import timedelta
from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase, override_settings
from django.test.utils import CaptureQueriesContext

from fallout.constants import (
    AP_COST_DROP,
    AP_COST_EQUIP,
    AP_COST_TAKE,
    AP_COST_USE,
    BASE_XP,
    EXTRA_LUCK_MONEY_MULT,
    HEALING_RATE_RESTING_MULT,
)
from fallout.enums import (
    DAMAGE_NORMAL,
    DAMAGE_RAW,
    HEAL_HEALTH,
    ITEM_ARMOR,
    ITEM_FOOD,
    ITEM_GRENADE,
    ITEM_MISC,
    ITEM_TOOL,
    LIST_SPECIALS,
    PART_TORSO,
    STATUS_HIT_SUCCEED,
    STATUS_NOT_ENOUGH_AP,
    WEAPON_TYPE_GRENADE,
    WEAPON_TYPE_UNARMED,
)
from fallout.models import (
    Campaign,
    CampaignEffect,
    Character,
    CharacterEffect,
    DamageHistory,
    Effect,
    EffectModifier,
    Equipment,
    FightHistory,
    Item,
    ItemModifier,
    Loot,
    LootTemplate,
    LootTemplateItem,
    RollHistory,
)
from fallout.tests.models.base import CoreTestCase


class LevelupTests(SimpleTestCase):
    def test_can_spend_exactly_the_remaining_budget(self):
        for specialized, budget in ((False, 4), (True, 2)):
            with self.subTest(specialized=specialized):
                character = Character(
                    small_guns=1,
                    skill_points=budget,
                    tag_skills=["small_guns"] if specialized else [],
                )
                self.assertEqual(character.levelup("small_guns", 1, save=False), 2)
                self.assertEqual(character.used_skill_points, budget)
                self.assertEqual(character.skill_points, budget)

    def test_cannot_exceed_the_remaining_budget(self):
        for specialized, budget in ((False, 3), (True, 1)):
            with self.subTest(specialized=specialized):
                character = Character(
                    small_guns=1,
                    skill_points=budget,
                    tag_skills=["small_guns"] if specialized else [],
                )
                with self.assertRaises(AssertionError):
                    character.levelup("small_guns", 1, save=False)
                self.assertEqual(character.small_guns, 1)
                self.assertEqual(character.skill_points, budget)

    def test_special_cannot_be_improved_as_a_skill(self):
        character = Character(strength=5, skill_points=10)
        with self.assertRaises(AssertionError):
            character.levelup("strength", 1, save=False)
        self.assertEqual(character.strength, 5)


class CampaignCoreTests(CoreTestCase):
    def test_clear_loot_preserves_money_by_default(self):
        Loot.objects.create(campaign=self.campaign, item=self.ammunition, quantity=3)
        self.campaign.money_loot = 25
        self.campaign.save()
        self.campaign.clear_loot()
        self.campaign.refresh_from_db()
        self.assertFalse(self.campaign.loots.exists())
        self.assertEqual(self.campaign.money_loot, 25)

    def test_clear_loot_can_also_remove_money(self):
        self.campaign.money_loot = 25
        self.campaign.save()
        self.campaign.clear_loot(include_money=True)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.money_loot, 0)

    def test_next_turn_orders_characters_advances_time_and_restores_action_points(self):
        self.hero.action_points = 1
        self.hero.save()
        before = self.campaign.current_game_date
        character, damages = self.campaign.next_turn(seconds=6)
        self.campaign.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(character.pk, self.hero.pk)
        self.assertEqual(self.campaign.current_character_id, self.hero.pk)
        self.assertEqual(self.campaign.current_game_date, before + timedelta(seconds=6))
        self.assertEqual(self.hero.action_points, 10)
        self.assertEqual(damages, [])

    def test_next_turn_cycles_and_skips_inactive_characters(self):
        self.assertEqual(self.campaign.next_turn(seconds=0)[0].pk, self.hero.pk)
        self.assertEqual(self.campaign.next_turn(seconds=0)[0].pk, self.target.pk)
        self.assertEqual(self.campaign.next_turn(seconds=0)[0].pk, self.hero.pk)
        self.target.is_active = False
        self.target.save()
        self.assertEqual(self.campaign.next_turn(seconds=0)[0].pk, self.hero.pk)

    def test_next_turn_preview_does_not_persist(self):
        before = self.campaign.current_game_date
        character, _ = self.campaign.next_turn(seconds=60, apply=False)
        self.campaign.refresh_from_db()
        self.assertEqual(character.pk, self.hero.pk)
        self.assertEqual(self.campaign.current_game_date, before)
        self.assertIsNone(self.campaign.current_character_id)

    def test_time_advance_can_reset_turn_order(self):
        self.campaign.next_turn(seconds=0)
        before = self.campaign.current_game_date
        character, _ = self.campaign.next_turn(seconds=3600, reset=True)
        self.campaign.refresh_from_db()
        self.assertIsNone(character)
        self.assertIsNone(self.campaign.current_character_id)
        self.assertEqual(self.campaign.current_game_date, before + timedelta(hours=1))

    def test_resting_time_advance_applies_healing(self):
        self.hero.health = 50
        self.hero.healing_rate = 24
        self.hero.save()
        self.campaign.next_turn(seconds=3600, resting=True, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 50 + HEALING_RATE_RESTING_MULT)


class CharacterCoreTests(CoreTestCase):
    def test_experience_crossing_a_level_grants_skill_perk_and_health_points(self):
        level, remaining, level_up = self.hero.add_experience(BASE_XP)
        self.hero.refresh_from_db()
        self.assertTrue(level_up)
        self.assertEqual((level, self.hero.level, self.hero.experience), (2, 2, BASE_XP))
        self.assertEqual(remaining, self.hero.required_experience)
        self.assertEqual(self.hero.skill_points, 510)
        self.assertEqual(self.hero.perk_points, 1)
        self.assertEqual((self.hero.health, self.hero.max_health), (105, 105))

    def test_zero_experience_does_not_change_level(self):
        self.assertFalse(self.hero.add_experience(0)[2])
        self.hero.refresh_from_db()
        self.assertEqual((self.hero.experience, self.hero.level), (0, 1))

    def test_experience_without_save_stays_in_memory(self):
        self.hero.add_experience(7, save=False)
        self.assertEqual(self.hero.experience, 7)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.experience, 0)

    def test_successful_skill_roll_records_reason_and_game_date_without_optional_xp(self):
        with patch("fallout.models.randint", return_value=1):
            history = self.hero.roll("small_guns", modifier=2, xp=False, reason="Cover")
        self.hero.refresh_from_db()
        self.assertTrue(history.success)
        self.assertTrue(history.critical)
        self.assertEqual(history.reason, "Cover")
        self.assertEqual(history.game_date, self.campaign.current_game_date)
        self.assertEqual(history.value, 60)
        self.assertEqual(history.modifier, 2)
        self.assertEqual(self.hero.experience, 0)
        self.assertEqual(RollHistory.objects.get().pk, history.pk)

    def test_failed_skill_roll_awards_and_persists_its_experience(self):
        with patch("fallout.models.randint", return_value=100):
            history = self.hero.roll("small_guns")
        self.hero.refresh_from_db()
        self.assertFalse(history.success)
        self.assertTrue(history.critical)
        self.assertGreater(history.experience, 0)
        self.assertEqual(self.hero.experience, history.experience)

    def test_special_roll_uses_a_ten_sided_die(self):
        with patch("fallout.models.randint", return_value=10) as dice:
            history = self.hero.roll("strength", modifier=5, xp=False)
        dice.assert_called_once_with(1, 10)
        self.assertTrue(history.success)

    def test_roll_can_skip_history(self):
        history = self.hero.roll("strength", xp=False, log=False)
        self.assertIsNone(history.pk)
        self.assertFalse(RollHistory.objects.exists())

    def test_randomize_special_respects_requested_total_and_racial_bounds(self):
        for requested, expected in ((1, 7), (40, 40), (100, 70)):
            with self.subTest(points=requested):
                self.hero.randomize_special(points=requested)
                self.hero.refresh_from_db()
                values = [getattr(self.hero, stat) for stat in LIST_SPECIALS]
                self.assertEqual(sum(values), expected)
                self.assertTrue(all(1 <= value <= 10 for value in values))
                self.assertEqual((self.hero.health, self.hero.action_points), (100, 10))

    def test_randomize_special_without_save_does_not_persist(self):
        before = [getattr(self.hero, stat) for stat in LIST_SPECIALS]
        self.hero.randomize_special(points=7, save=False)
        self.assertEqual(sum(getattr(self.hero, stat) for stat in LIST_SPECIALS), 7)
        self.hero.refresh_from_db()
        self.assertEqual([getattr(self.hero, stat) for stat in LIST_SPECIALS], before)

    def test_randomize_stats_targets_level_and_distributes_budget_on_tag_skills(self):
        character = Character.objects.create(
            name="Random",
            has_stats=False,
            is_player=True,
            max_health=100,
            skill_points=10,
            skill_points_per_level=4,
            tag_skills=["small_guns"],
        )
        character.randomize_stats(level=2, balance=100)
        character.refresh_from_db()
        self.assertEqual(character.level, 2)
        self.assertEqual(character.experience, BASE_XP)
        self.assertEqual(character.small_guns, 14)
        self.assertEqual(character.used_skill_points, character.skill_points)

    def test_randomize_stats_also_supports_calculated_characters(self):
        character = Character.objects.create(name="Calculated", is_player=True, tag_skills=["small_guns"])
        character.randomize_stats(level=3, balance=100)
        character.refresh_from_db()
        self.assertEqual(character.level, 3)
        self.assertEqual(character.experience, 3 * BASE_XP)
        self.assertGreater(character.skill_points, 0)
        self.assertEqual(character.used_skill_points, character.skill_points)

    def test_duplicate_copies_inventory_and_effects_without_removing_source(self):
        equipment = self.ammunition.give(self.hero, quantity=3)
        effect = Effect.objects.create(name="Buff")
        active = effect.affect(self.hero, force=True)
        source_id = self.hero.pk
        destination = Campaign.objects.create(name="Destination")
        copied = self.hero.duplicate(campaign=destination, name="Copy")
        self.assertNotEqual(copied.pk, source_id)
        self.assertEqual(copied.campaign_id, destination.pk)
        self.assertEqual(Character.objects.get(pk=source_id).name, "Hero")
        copied_equipment = Equipment.objects.get(character=copied)
        self.assertNotEqual(copied_equipment.pk, equipment.pk)
        self.assertEqual(copied_equipment.quantity, 3)
        self.assertTrue(Equipment.objects.filter(pk=equipment.pk, character_id=source_id).exists())
        copied_effect = CharacterEffect.objects.get(character=copied)
        self.assertNotEqual(copied_effect.pk, active.pk)
        self.assertEqual(copied_effect.effect_id, effect.pk)

    def test_duplicate_can_skip_inventory_and_effects(self):
        self.ammunition.give(self.hero)
        Effect.objects.create(name="Buff").affect(self.hero, force=True)
        copied = self.hero.duplicate(equipments=False, effects=False)
        self.assertFalse(Equipment.objects.filter(character=copied).exists())
        self.assertFalse(CharacterEffect.objects.filter(character=copied).exists())

    def test_duplicate_preserves_requested_inactive_state(self):
        copied = self.hero.duplicate(is_active=False)
        copied.refresh_from_db()
        self.assertFalse(copied.is_active)

    def test_inactive_creation_restores_health_without_reactivation(self):
        character = Character.objects.create(
            name="Inactive",
            is_player=True,
            is_active=False,
            has_stats=False,
            max_health=50,
            max_action_points=5,
        )
        character.refresh_from_db()
        self.assertFalse(character.is_active)
        self.assertEqual((character.health, character.action_points), (50, 5))
        character.heal()
        character.refresh_from_db()
        self.assertTrue(character.is_active)

    def test_all_stats_exposes_calculated_values(self):
        character = Character.objects.create(name="Calculated", is_player=True)
        stats = {stat.code: stat for stat in character.all_stats}
        self.assertEqual(stats["small_guns"].lvalue, character.stats.small_guns)
        self.assertEqual(stats["strength"].lvalue, character.stats.strength)
        self.assertGreater(character.stats.max_health, 0)


class DamageAndFightCoreTests(CoreTestCase):
    def test_personal_threshold_preserves_base_and_applies_rate_modifier(self):
        self.hero.normal_threshold = 15
        self.hero.damage_threshold = 5
        for modifier, threshold, damage in ((0, 20, 10), (-50, 10, 20), (50, 30, 0), (-150, 0, 30)):
            with self.subTest(modifier=modifier):
                self.hero.health = 100
                history = self.hero.damage(
                    raw_damage=30,
                    damage_type=DAMAGE_NORMAL,
                    threshold_rate_modifier=modifier,
                    save=False,
                    log=False,
                )
                self.assertEqual(history.damage_threshold, threshold)
                self.assertEqual(history.real_damage, damage)
                self.assertEqual(self.hero.health, 100 - damage)

    def test_damage_applies_resistance_and_records_history(self):
        self.hero.normal_resistance = 50
        self.hero.save()
        history = self.hero.damage(raw_damage=20, damage_type=DAMAGE_NORMAL, body_part=PART_TORSO, reason="Trap")
        self.hero.refresh_from_db()
        self.assertEqual(history.real_damage, 10)
        self.assertEqual(self.hero.health, 90)
        self.assertEqual(history.reason, "Trap")
        self.assertEqual(DamageHistory.objects.get().pk, history.pk)

    def test_healing_is_limited_to_maximum_health(self):
        self.hero.health = 95
        self.hero.save()
        history = self.hero.damage(raw_damage=20, damage_type=HEAL_HEALTH)
        self.hero.refresh_from_db()
        self.assertTrue(history.is_heal)
        self.assertEqual(self.hero.health, self.hero.max_health)

    def test_invalid_damage_range_does_not_change_health(self):
        with self.assertRaises(AssertionError):
            self.hero.damage(min_damage=10, max_damage=5)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 100)
        self.assertFalse(DamageHistory.objects.exists())

    def test_damage_can_skip_history(self):
        self.hero.damage(raw_damage=5, damage_type=DAMAGE_RAW, log=False)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 95)
        self.assertFalse(DamageHistory.objects.exists())

    def test_damage_simulation_does_not_persist_health_or_history(self):
        history = self.hero.damage(raw_damage=5, damage_type=DAMAGE_RAW, simulation=True)
        self.assertEqual(history.real_damage, 5)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 100)
        self.assertFalse(DamageHistory.objects.exists())

    def test_fight_records_damage_experience_and_action_cost(self):
        weapon, _ = self.armed_inventory()
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            history = self.hero.fight(self.target, target_part=PART_TORSO, force_success=True, is_action=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        weapon.refresh_from_db()
        self.assertEqual(history.status, STATUS_HIT_SUCCEED)
        self.assertEqual(self.target.health, 100 - history.damage.real_damage)
        self.assertGreater(history.damage.real_damage, 0)
        self.assertEqual(self.hero.experience, history.experience)
        self.assertGreater(self.hero.experience, 0)
        self.assertEqual(weapon.clip_count, 0)
        self.assertEqual(FightHistory.objects.count(), 1)
        self.assertEqual(DamageHistory.objects.count(), 1)
        self.assertEqual(self.hero.action_points, 10 - weapon.item.ap_cost_target)

    def test_fight_without_enough_action_points_does_not_damage_target(self):
        self.hero.action_points = 0
        self.hero.save()
        history = self.hero.fight(self.target, weapon_type=WEAPON_TYPE_UNARMED, is_action=True)
        self.target.refresh_from_db()
        self.assertEqual(history.status, STATUS_NOT_ENOUGH_AP)
        self.assertEqual(self.target.health, 100)
        self.assertFalse(DamageHistory.objects.exists())

    def test_fight_simulation_does_not_consume_ammunition_or_change_characters(self):
        weapon, ammo = self.armed_inventory()
        before = list(Character.objects.order_by("pk").values())
        history = self.hero.fight(self.target, force_success=True, simulation=True, is_action=True)
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertTrue(history.success)
        self.assertEqual(weapon.clip_count, 1)
        self.assertEqual(ammo.quantity, 10)
        self.assertEqual(list(Character.objects.order_by("pk").values()), before)
        self.assertFalse(FightHistory.objects.exists())
        self.assertFalse(DamageHistory.objects.exists())

    def test_grenade_burst_hits_each_target_and_consumes_one_grenade(self):
        another = Character.objects.create(
            name="Another target",
            campaign=self.campaign,
            is_player=True,
            has_stats=False,
            max_health=100,
        )
        grenade = Item.objects.create(
            name="Grenade",
            type=ITEM_GRENADE,
            raw_damage=5,
            damage_type=DAMAGE_RAW,
            max_burst_range=10,
            ap_cost_normal=2,
        )
        equipment = Equipment.objects.create(character=self.hero, item=grenade, slot=ITEM_GRENADE, quantity=2)
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            histories = self.hero.burst(
                targets=[(self.target, 1), (another, 1)],
                weapon_type=WEAPON_TYPE_GRENADE,
                force_success=True,
                is_action=False,
                target_part=PART_TORSO,
            )
        self.target.refresh_from_db()
        another.refresh_from_db()
        equipment.refresh_from_db()
        self.assertEqual(len(histories), 2)
        self.assertTrue(all(history.success for history in histories))
        self.assertEqual((self.target.health, another.health), (95, 95))
        self.assertEqual(equipment.quantity, 1)
        self.assertEqual(FightHistory.objects.count(), 2)

    def test_weapon_burst_consumes_loaded_ammunition_not_inventory_stock(self):
        weapon, ammo = self.armed_inventory()
        weapon.clip_count = 6
        weapon.save()
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            histories = self.hero.burst(
                targets=[(self.target, 1)],
                force_success=True,
                is_action=False,
                target_part=PART_TORSO,
            )
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(len(histories), 3)
        self.assertEqual(weapon.clip_count, 3)
        self.assertEqual(self.target.health, 76)
        self.assertEqual(ammo.quantity, 10)

    def test_interrupted_burst_degrades_weapon_without_type_error(self):
        weapon, ammo = self.armed_inventory()
        weapon.clip_count = 6
        weapon.save()
        self.target.health = 5
        self.target.save()
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            histories = self.hero.burst(
                targets=[(self.target, 1)],
                force_success=True,
                is_action=False,
                target_part=PART_TORSO,
            )
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(len(histories), 1)
        self.assertEqual(self.target.health, 0)
        self.assertEqual(weapon.clip_count, 3)
        self.assertEqual(ammo.quantity, 10)
        self.assertAlmostEqual(weapon.condition, 0.97)

    def test_interrupted_burst_cannot_consume_more_than_loaded_ammunition(self):
        weapon, ammo = self.armed_inventory()
        self.target.health = 1
        self.target.save()
        self.hero.burst(targets=[(self.target, 1)], force_success=True, force_raw_damage=True, is_action=False)
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual(weapon.clip_count, 0)
        self.assertEqual(ammo.quantity, 10)
        self.assertAlmostEqual(weapon.condition, 0.99)

    def test_interrupted_burst_simulation_preserves_loaded_ammunition_and_stock(self):
        weapon, ammo = self.armed_inventory()
        weapon.clip_count = 6
        weapon.save()
        self.target.health = 1
        self.target.save()
        self.hero.burst(
            targets=[(self.target, 1)],
            force_success=True,
            force_raw_damage=True,
            is_action=False,
            simulation=True,
        )
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(weapon.clip_count, 6)
        self.assertEqual(ammo.quantity, 10)
        self.assertEqual(weapon.condition, 1.0)
        self.assertEqual(self.target.health, 1)

    def test_grenade_burst_simulation_preserves_inventory_and_target(self):
        grenade = Item.objects.create(
            name="Grenade",
            type=ITEM_GRENADE,
            raw_damage=5,
            damage_type=DAMAGE_RAW,
            max_burst_range=10,
        )
        equipment = Equipment.objects.create(character=self.hero, item=grenade, slot=ITEM_GRENADE, quantity=2)
        histories = self.hero.burst(
            targets=[(self.target, 1)],
            weapon_type=WEAPON_TYPE_GRENADE,
            force_success=True,
            is_action=False,
            simulation=True,
            target_part=PART_TORSO,
        )
        equipment.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(len(histories), 1)
        self.assertEqual(equipment.quantity, 2)
        self.assertEqual(self.target.health, 100)
        self.assertFalse(FightHistory.objects.exists())
        self.assertFalse(DamageHistory.objects.exists())

    def test_burst_requires_targets(self):
        with self.assertRaises(AssertionError):
            self.hero.burst([])
        self.assertFalse(FightHistory.objects.exists())


class EquipmentCoreTests(CoreTestCase):
    def test_give_stacks_non_repairable_items(self):
        first = self.ammunition.give(self.hero, quantity=3)
        second = self.ammunition.give(self.hero, quantity=2)
        self.assertEqual(first.pk, second.pk)
        first.refresh_from_db()
        self.assertEqual(first.quantity, 5)
        self.assertEqual(Equipment.objects.filter(character=self.hero).count(), 1)

    def test_give_creates_separate_repairable_items_with_condition(self):
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100)
        equipments = armor.give(self.hero, quantity=2, condition=0.75)
        self.assertEqual(len(equipments), 2)
        self.assertNotEqual(equipments[0].pk, equipments[1].pk)
        self.assertTrue(all(item.quantity == 1 and item.condition == 0.75 for item in equipments))

    def test_equip_and_unequip_consume_optional_action_points(self):
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100)
        equipment = armor.give(self.hero)
        equipment.equip(is_action=True)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(equipment.slot, ITEM_ARMOR)
        self.assertEqual(self.hero.action_points, 10 - AP_COST_EQUIP)
        equipment.equip(is_action=True)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(equipment.slot, "")
        self.assertEqual(self.hero.action_points, 10 - 2 * AP_COST_EQUIP)

    def test_equipping_another_item_replaces_the_existing_slot(self):
        first = Item.objects.create(name="Armor A", type=ITEM_ARMOR, durability=100).give(self.hero)
        second = Item.objects.create(name="Armor B", type=ITEM_ARMOR, durability=100).give(self.hero)
        first.equip()
        second.equip()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(first.slot, "")
        self.assertEqual(second.slot, ITEM_ARMOR)

    def test_equip_rejects_non_equippable_item(self):
        equipment = Item.objects.create(name="Misc", type=ITEM_MISC).give(self.hero)
        with self.assertRaises(AssertionError):
            equipment.equip()
        equipment.refresh_from_db()
        self.assertEqual(equipment.slot, "")

    def test_equip_rejects_insufficient_action_points(self):
        equipment = self.ammunition.give(self.hero)
        self.hero.action_points = AP_COST_EQUIP - 1
        self.hero.save()
        with self.assertRaises(AssertionError):
            equipment.equip(is_action=True)
        equipment.refresh_from_db()
        self.assertEqual(equipment.slot, "")

    def test_use_consumes_food_applies_modifiers_and_effects_and_spends_action_points(self):
        self.hero.health = 80
        self.hero.save()
        food = Item.objects.create(name="Food", type=ITEM_FOOD)
        modifier = ItemModifier.objects.create(item=food, stats="health", min_value=5, max_value=5)
        effect = Effect.objects.create(name="Fed")
        food.effects.add(effect)
        equipment = food.give(self.hero, quantity=2)
        effects, modifiers = equipment.use(is_action=True)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(equipment.quantity, 1)
        self.assertEqual(self.hero.health, 85)
        self.assertEqual(self.hero.action_points, 10 - AP_COST_USE)
        self.assertEqual([item.pk for item in modifiers], [modifier.pk])
        self.assertEqual([item.effect_id for item in effects], [effect.pk])
        self.assertTrue(CharacterEffect.objects.filter(character=self.hero, effect=effect).exists())

    def test_use_last_consumable_removes_inventory_entry(self):
        food = Item.objects.create(name="Food", type=ITEM_FOOD)
        equipment = food.give(self.hero)
        equipment_id = equipment.pk
        equipment.use()
        self.assertFalse(Equipment.objects.filter(pk=equipment_id).exists())

    def test_use_tool_degrades_condition_without_consuming_quantity(self):
        tool = Item.objects.create(name="Tool", type=ITEM_TOOL, durability=10)
        equipment = tool.give(self.hero)
        equipment.use()
        equipment.refresh_from_db()
        self.assertEqual(equipment.quantity, 1)
        self.assertAlmostEqual(equipment.condition, 0.9)

    def test_use_rejects_non_usable_item(self):
        equipment = self.ammunition.give(self.hero)
        with self.assertRaises(AssertionError):
            equipment.use()
        equipment.refresh_from_db()
        self.assertEqual(equipment.quantity, 1)

    def test_reload_fills_clip_consumes_stock_and_optional_action_points(self):
        weapon, ammo = self.armed_inventory()
        weapon.reload(is_action=True)
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(weapon.clip_count, 6)
        self.assertEqual(ammo.quantity, 5)
        self.assertEqual(self.hero.action_points, 8)

    def test_reload_rejects_incompatible_ammunition_without_consumption(self):
        weapon, ammo = self.armed_inventory()
        weapon.item.ammunitions.clear()
        with self.assertRaises(AssertionError):
            weapon.reload(is_action=True)
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual((weapon.clip_count, ammo.quantity), (1, 10))

    def test_reload_rejects_insufficient_action_points(self):
        weapon, ammo = self.armed_inventory()
        self.hero.action_points = 0
        self.hero.save()
        with self.assertRaises(AssertionError):
            weapon.reload(is_action=True)
        ammo.refresh_from_db()
        self.assertEqual(ammo.quantity, 10)

    def test_drop_transfers_requested_quantity_to_campaign_loot(self):
        equipment = self.ammunition.give(self.hero, quantity=5)
        loot = equipment.drop(quantity=2, is_action=True)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(equipment.quantity, 3)
        self.assertEqual((loot.campaign_id, loot.item_id, loot.quantity), (self.campaign.pk, self.ammunition.pk, 2))
        self.assertEqual(self.hero.action_points, 10 - AP_COST_DROP)

    def test_drop_rejects_more_than_available_quantity(self):
        equipment = self.ammunition.give(self.hero, quantity=2)
        with self.assertRaises(AssertionError):
            equipment.drop(quantity=3)
        equipment.refresh_from_db()
        self.assertEqual(equipment.quantity, 2)
        self.assertFalse(Loot.objects.exists())


class PeriodicEffectCatchUpTests(CoreTestCase):
    def periodic_effect(self, **kwargs):
        config = dict(
            name="Periodic catch-up",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            interval=timedelta(minutes=1),
            apply=False,
        )
        config.update(kwargs)
        return Effect.objects.create(**config)

    def assert_health_and_history(self, health, count):
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (health, health))
        self.assertEqual(DamageHistory.objects.filter(character=self.hero).count(), count)
        self.assertEqual(DamageHistory.objects.filter(character=self.target).count(), count)

    def test_interval_boundaries_and_repeated_application_do_not_duplicate_ticks(self):
        active = self.periodic_effect().affect(self.campaign, force=True)
        start = self.campaign.current_game_date
        for seconds, count in ((59, 0), (1, 1), (59, 1), (1, 2)):
            with self.subTest(elapsed_ticks=count, advance=seconds):
                self.campaign.next_turn(seconds=seconds, reset=True)
                self.assert_health_and_history(100 - count * 5, count)
                active.refresh_from_db()
                self.assertEqual(active.next_date, start + timedelta(minutes=count + 1))
                active.campaign = self.campaign
                self.assertEqual(active.apply_all(), [])
                self.assert_health_and_history(100 - count * 5, count)

    def test_indefinite_effect_catches_up_and_continues_on_next_time_step(self):
        active = self.periodic_effect().affect(self.campaign, force=True)
        start = self.campaign.current_game_date
        _, damages = self.campaign.next_turn(seconds=300, reset=True)
        self.assertEqual(len(damages), 10)
        self.assert_health_and_history(75, 5)
        active.refresh_from_db()
        self.assertIsNone(active.end_date)
        self.assertEqual(active.next_date, start + timedelta(minutes=6))
        self.campaign.next_turn(seconds=60, reset=True)
        self.assert_health_and_history(70, 6)
        active.refresh_from_db()
        self.assertEqual(active.next_date, start + timedelta(minutes=7))

    def test_immediate_application_is_not_counted_twice_during_catch_up(self):
        active = self.periodic_effect(apply=True).affect(self.campaign, force=True)
        self.assert_health_and_history(95, 1)
        self.campaign.next_turn(seconds=300, reset=True)
        self.assert_health_and_history(70, 6)
        active.refresh_from_db()
        self.assertEqual(active.next_date, self.campaign.current_game_date + timedelta(minutes=1))

    def test_catch_up_before_expiration_keeps_effect_and_future_schedule(self):
        active = self.periodic_effect(min_duration=timedelta(minutes=10)).affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=300, reset=True)
        self.assert_health_and_history(75, 5)
        active.refresh_from_db()
        self.assertEqual(active.next_date, self.campaign.current_game_date + timedelta(minutes=1))
        self.assertEqual(active.end_date, self.campaign.current_game_date + timedelta(minutes=5))

    def test_tick_exactly_at_end_date_is_applied_before_expiration(self):
        effect = self.periodic_effect(min_duration=timedelta(minutes=5))
        effect.affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=300, reset=True)
        self.assert_health_and_history(75, 5)
        self.assertFalse(CampaignEffect.objects.filter(campaign=self.campaign, effect=effect).exists())
        self.campaign.next_turn(seconds=60, reset=True)
        self.assert_health_and_history(75, 5)

    def test_advancing_past_end_date_does_not_apply_ticks_after_expiration(self):
        effect = self.periodic_effect(min_duration=timedelta(minutes=3))
        effect.affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=300, reset=True)
        self.assertEqual(len(damages), 6)
        self.assert_health_and_history(85, 3)
        self.assertFalse(CampaignEffect.objects.filter(campaign=self.campaign, effect=effect).exists())

    def test_end_date_between_ticks_does_not_create_an_extra_tick(self):
        effect = self.periodic_effect(min_duration=timedelta(seconds=150))
        effect.affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=300, reset=True)
        self.assert_health_and_history(90, 2)
        self.assertFalse(CampaignEffect.objects.filter(campaign=self.campaign, effect=effect).exists())

    def test_large_and_small_time_steps_produce_equivalent_isolated_periodic_effects(self):
        # Comparer PV, historiques et échéancier, pas les dates d'historique : celles-ci
        # utilisent la date courante du pas de temps, et non la date théorique du tick.
        for individual in (False, True):
            for immediate in (False, True):
                for duration in (None, timedelta(minutes=3), timedelta(minutes=5)):
                    with self.subTest(individual=individual, immediate=immediate, duration=duration):
                        outcomes = []
                        for steps in ((300,), (60,) * 5):
                            campaign = Campaign.objects.create(name="Equivalent catch-up", needs=False)
                            character = Character.objects.create(
                                name="Equivalent hero",
                                campaign=campaign,
                                is_player=True,
                                has_stats=False,
                                has_needs=False,
                                max_health=100,
                                max_action_points=10,
                            )
                            effect = self.periodic_effect(apply=immediate, min_duration=duration)
                            active = effect.affect(character if individual else campaign, force=True)
                            for seconds in steps:
                                campaign.next_turn(seconds=seconds, reset=True)
                            character.refresh_from_db()
                            history = DamageHistory.objects.filter(character=character)
                            state = type(active).objects.filter(pk=active.pk).first()
                            outcomes.append(
                                (
                                    character.health,
                                    list(history.order_by("pk").values_list("real_damage", flat=True)),
                                    state is not None,
                                    state.next_date - campaign.current_game_date if state else None,
                                    state.end_date - campaign.current_game_date if state and state.end_date else None,
                                )
                            )
                        ticks = (3 if duration == timedelta(minutes=3) else 5) + int(immediate)
                        self.assertEqual(outcomes[0], outcomes[1])
                        self.assertEqual(outcomes[0][0], 100 - ticks * 5)
                        self.assertEqual(outcomes[0][1], [5] * ticks)

    def test_expired_parent_and_indefinite_successor_catch_up_in_chain_order(self):
        successor = self.periodic_effect(raw_damage=3)
        parent = self.periodic_effect(raw_damage=2, min_duration=timedelta(minutes=2), next_effect=successor)
        parent.affect(self.campaign, force=True)
        start = self.campaign.current_game_date
        _, damages = self.campaign.next_turn(seconds=300, reset=True)
        self.assertEqual([damage.real_damage for damage in damages], [2] * 4 + [3] * 6)
        self.assert_health_and_history(87, 5)
        self.assertFalse(CampaignEffect.objects.filter(campaign=self.campaign, effect=parent).exists())
        active = CampaignEffect.objects.get(campaign=self.campaign, effect=successor)
        self.assertEqual(active.start_date, start + timedelta(minutes=2))
        self.assertEqual(active.next_date, start + timedelta(minutes=6))
        self.campaign.next_turn(seconds=60, reset=True)
        self.assert_health_and_history(84, 6)

    def test_death_during_catch_up_skips_later_ticks_for_dead_character(self):
        self.target.is_player = False
        self.target.loot_on_death = False
        self.target.health = 10
        self.target.save()
        active = self.periodic_effect().affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=300, reset=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (75, 0))
        self.assertFalse(self.target.is_active)
        self.assertEqual(sum(damage.character_id == self.hero.pk for damage in damages), 5)
        self.assertEqual(sum(damage.character_id == self.target.pk for damage in damages), 2)
        self.assertEqual(DamageHistory.objects.filter(character=self.target).count(), 2)
        active.refresh_from_db()
        self.assertEqual(active.next_date, self.campaign.current_game_date + timedelta(minutes=1))

    def test_periodic_healing_catches_up_without_exceeding_maximum_health(self):
        self.hero.health = 40
        self.hero.save()
        self.target.health = 90
        self.target.save()
        self.periodic_effect(damage_type=HEAL_HEALTH).affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=300, reset=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (65, 100))
        self.assertEqual(len(damages), 10)
        self.assertTrue(all(damage.is_heal for damage in damages))

    def test_effect_without_interval_does_not_repeat_its_initial_damage(self):
        active = self.periodic_effect(interval=None, apply=True).affect(self.campaign, force=True)
        self.assert_health_and_history(95, 1)
        for seconds in (300, 300):
            _, damages = self.campaign.next_turn(seconds=seconds, reset=True)
            self.assertEqual(damages, [])
            self.assert_health_and_history(95, 1)
        self.assertTrue(CampaignEffect.objects.filter(pk=active.pk).exists())

    def test_general_effect_without_interval_remains_active_without_damage(self):
        self.hero.has_stats = True
        self.hero.save()
        strength = self.hero.stats.strength
        effect = Effect.objects.create(name="Permanent strength", apply=False)
        EffectModifier.objects.create(effect=effect, stats="strength", min_value=2, max_value=2)
        active = effect.affect(self.campaign, force=True)
        for seconds in (300, 300):
            _, damages = self.campaign.next_turn(seconds=seconds, reset=True)
            self.assertEqual(damages, [])
            self.hero.refresh_from_db()
            self.assertEqual(self.hero.stats.strength, strength + 2)
        active.refresh_from_db()
        self.assertIsNone(active.next_date)
        self.assertIsNone(active.end_date)
        self.assertFalse(DamageHistory.objects.exists())

    @override_settings(IGNORE_LOG=True, NOTIFY_CHANGES=False)
    def test_multiple_ticks_keep_a_single_final_character_save(self):
        self.periodic_effect().affect(self.campaign, force=True)
        with CaptureQueriesContext(connection) as queries:
            self.campaign.next_turn(seconds=300, reset=True)
        sql = [query["sql"].lower() for query in queries]
        self.assertEqual(sum(query.startswith('update "fallout_character"') for query in sql), 2)
        self.assertEqual(sum(query.startswith("select ") and 'from "fallout_character"' in query for query in sql), 1)
        self.assert_health_and_history(75, 5)


class EffectAndLootCoreTests(CoreTestCase):
    def test_affect_character_creates_one_active_effect_and_applies_damage(self):
        effect = Effect.objects.create(name="Burn", damage_type=DAMAGE_RAW, raw_damage=5)
        active = effect.affect(self.hero, force=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 95)
        self.assertEqual(active.character_id, self.hero.pk)
        self.assertEqual(len(active.damages), 1)
        self.assertEqual(CharacterEffect.objects.filter(character=self.hero, effect=effect).count(), 1)

    def test_affect_campaign_applies_damage_to_its_characters(self):
        effect = Effect.objects.create(name="Heat", damage_type=DAMAGE_RAW, raw_damage=5)
        active = effect.affect(self.campaign, force=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (95, 95))
        self.assertEqual(CampaignEffect.objects.get().pk, active.pk)
        self.assertEqual(len(active.damages), 2)

    def test_affect_can_fail_by_chance_or_be_forced(self):
        effect = Effect.objects.create(name="Unlikely", chance=0)
        self.assertIsNone(effect.affect(self.hero))
        self.assertFalse(CharacterEffect.objects.exists())
        self.assertIsNotNone(effect.affect(self.hero, force=True))
        self.assertEqual(CharacterEffect.objects.count(), 1)

    def test_affect_cancels_previous_effect(self):
        previous = Effect.objects.create(name="Previous")
        previous.affect(self.hero, force=True)
        replacement = Effect.objects.create(name="Replacement", cancel_effect=previous)
        replacement.affect(self.hero, force=True)
        self.assertFalse(CharacterEffect.objects.filter(character=self.hero, effect=previous).exists())
        self.assertTrue(CharacterEffect.objects.filter(character=self.hero, effect=replacement).exists())

    def test_timed_effect_requires_a_campaign(self):
        effect = Effect.objects.create(name="Timed", min_duration=timedelta(minutes=1))
        with self.assertRaises(AssertionError):
            effect.affect(Character(has_stats=False), force=True)
        self.assertFalse(CharacterEffect.objects.exists())

    def test_effect_modifier_invalidates_and_recalculates_character_stats(self):
        character = Character.objects.create(name="Calculated", is_player=True, strength=5)
        before = character.stats.strength
        effect = Effect.objects.create(name="Strength")
        EffectModifier.objects.create(effect=effect, stats="strength", min_value=2, max_value=2)
        effect.affect(character, force=True)
        character.refresh_from_db()
        self.assertEqual(character.stats.strength, before + 2)

    def test_time_advance_applies_periodic_campaign_effect(self):
        effect = Effect.objects.create(
            name="Periodic",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            interval=timedelta(minutes=1),
        )
        effect.affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=60, reset=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(len(damages), 2)
        self.assertEqual(DamageHistory.objects.count(), 4)
        self.assertEqual((self.hero.health, self.target.health), (90, 90))

    @override_settings(IGNORE_LOG=True, NOTIFY_CHANGES=False)
    def test_time_advance_query_budget_and_single_final_save(self):
        for count, effect_count, calculated, budget in (
            (2, 1, False, 16),
            (2, 3, False, 28),
            (8, 1, False, 46),
            (8, 3, False, 82),
            (2, 3, True, 110),
            (8, 3, True, 410),
        ):
            with self.subTest(characters=count, effects=effect_count, calculated=calculated):
                campaign = Campaign.objects.create(name="Query budget", needs=False)
                ids = []
                for index in range(count):
                    character = Character.objects.create(
                        name=str(index),
                        campaign=campaign,
                        is_player=True,
                        has_stats=calculated,
                        has_needs=False,
                        max_health=100,
                        max_action_points=10,
                        luck=5,
                    )
                    ids.append(character.pk)
                for index in range(effect_count):
                    Effect.objects.create(
                        name=str(index),
                        damage_type=DAMAGE_RAW,
                        raw_damage=5,
                        interval=timedelta(minutes=1),
                        apply=False,
                    ).affect(campaign, force=True)
                initial_health = list(Character.objects.filter(pk__in=ids).values_list("health", flat=True))
                with CaptureQueriesContext(connection) as queries:
                    campaign.next_turn(seconds=60, reset=True)
                sql = [query["sql"].lower() for query in queries]
                self.assertLessEqual(len(sql), budget)
                self.assertEqual(sum(query.startswith('update "fallout_character"') for query in sql), count)
                self.assertEqual(
                    sum(query.startswith("select ") and 'from "fallout_character"' in query for query in sql), 1
                )
                self.assertEqual(
                    list(Character.objects.filter(pk__in=ids).values_list("health", flat=True)),
                    [health - effect_count * 5 for health in initial_health],
                )

    def test_global_effects_then_needs_then_individual_effects_then_final_save(self):
        for damage in (3, 7):
            Effect.objects.create(
                name=str(damage),
                damage_type=DAMAGE_RAW,
                raw_damage=damage,
                interval=timedelta(minutes=1),
                apply=False,
            ).affect(self.campaign, force=True)
        Effect.objects.create(
            name="Individual",
            damage_type=DAMAGE_RAW,
            raw_damage=11,
            interval=timedelta(minutes=1),
            apply=False,
        ).affect(self.hero, force=True)
        events = []
        update_needs, apply_effects, save = Character.update_needs, Character.apply_effects, Character.save

        def tracked_needs(character, *args, **kwargs):
            events.append(("needs", character.pk, character.health))
            return update_needs(character, *args, **kwargs)

        def tracked_effects(character, *args, **kwargs):
            events.append(("individual", character.pk, character.health))
            return apply_effects(character, *args, **kwargs)

        def tracked_save(character, *args, **kwargs):
            events.append(("save", character.pk, character.health))
            return save(character, *args, **kwargs)

        with (
            patch.object(Character, "update_needs", tracked_needs),
            patch.object(Character, "apply_effects", tracked_effects),
            patch.object(Character, "save", tracked_save),
        ):
            self.campaign.next_turn(seconds=60, reset=True)
        self.assertEqual(
            events,
            [
                ("needs", self.hero.pk, 90),
                ("individual", self.hero.pk, 90),
                ("save", self.hero.pk, 79),
                ("needs", self.target.pk, 90),
                ("individual", self.target.pk, 90),
                ("save", self.target.pk, 90),
            ],
        )

    def test_campaign_effect_chain_shares_instances_without_intermediate_saves(self):
        following = Effect.objects.create(name="Following", damage_type=DAMAGE_RAW, raw_damage=7)
        first = Effect.objects.create(
            name="First",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=following,
        )
        first.affect(self.campaign, force=True)
        with CaptureQueriesContext(connection) as queries:
            _, damages = self.campaign.next_turn(seconds=60, reset=True)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (88, 88))
        self.assertEqual([damage.real_damage for damage in damages], [5, 5, 7, 7])
        self.assertEqual(sum(query["sql"].lower().startswith('update "fallout_character"') for query in queries), 2)
        self.assertFalse(CampaignEffect.objects.filter(effect=first).exists())
        self.assertTrue(CampaignEffect.objects.filter(effect=following).exists())

    def test_multiple_expired_effects_are_processed_in_chain_order(self):
        last = Effect.objects.create(name="Last", damage_type=DAMAGE_RAW, raw_damage=7)
        middle = Effect.objects.create(
            name="Middle",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=last,
        )
        first = Effect.objects.create(
            name="First",
            damage_type=DAMAGE_RAW,
            raw_damage=3,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=middle,
        )
        first.affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=120, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 85)
        self.assertEqual([damage.real_damage for damage in damages], [3, 3, 5, 5, 7, 7])
        self.assertEqual(list(CampaignEffect.objects.values_list("effect_id", flat=True)), [last.pk])

    def test_individual_effect_chain_does_not_save_early_or_apply_successor_twice(self):
        following = Effect.objects.create(name="Following", damage_type=DAMAGE_RAW, raw_damage=7)
        first = Effect.objects.create(
            name="First",
            damage_type=DAMAGE_RAW,
            raw_damage=3,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=following,
        )
        first.affect(self.hero, force=True)
        with CaptureQueriesContext(connection) as queries:
            _, damages = self.campaign.next_turn(seconds=60, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 90)
        self.assertEqual([damage.real_damage for damage in damages], [3, 7])
        self.assertEqual(sum(query["sql"].lower().startswith('update "fallout_character"') for query in queries), 2)

    def test_effect_chain_can_cancel_an_effect_pending_in_the_same_time_step(self):
        cancelled = Effect.objects.create(
            name="Cancelled",
            damage_type=DAMAGE_RAW,
            raw_damage=50,
            interval=timedelta(minutes=1),
            apply=False,
        )
        following = Effect.objects.create(
            name="Following",
            damage_type=DAMAGE_RAW,
            raw_damage=3,
            cancel_effect=cancelled,
        )
        first = Effect.objects.create(
            name="First",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=following,
        )
        first.affect(self.campaign, force=True)
        cancelled.affect(self.campaign, force=True)
        _, damages = self.campaign.next_turn(seconds=60, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 92)
        self.assertEqual([damage.real_damage for damage in damages], [5, 5, 3, 3])

    def test_lethal_global_effect_skips_later_effects_and_needs_but_saves_death(self):
        self.target.is_player = False
        self.target.loot_on_death = False
        self.target.save()
        for damage in (150, 7):
            Effect.objects.create(
                name=str(damage),
                damage_type=DAMAGE_RAW,
                raw_damage=damage,
                interval=timedelta(minutes=1),
                apply=False,
            ).affect(self.campaign, force=True)
        with patch.object(Character, "update_needs") as needs:
            _, damages = self.campaign.next_turn(seconds=60, reset=True)
        needs.assert_not_called()
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual((self.hero.health, self.target.health), (0, 0))
        self.assertFalse(self.target.is_active)
        self.assertEqual(len(damages), 2)

    def test_global_effect_chain_invalidates_cached_calculated_stats_before_needs(self):
        self.hero.has_stats = True
        self.hero.save()
        following = Effect.objects.create(name="Strength")
        EffectModifier.objects.create(effect=following, stats="strength", min_value=2, max_value=2)
        first = Effect.objects.create(
            name="Damage then strength",
            damage_type=DAMAGE_RAW,
            raw_damage=3,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=1),
            next_effect=following,
        )
        first.affect(self.campaign, force=True)
        strengths = []
        update_needs = Character.update_needs

        def tracked_needs(character, *args, **kwargs):
            if character.pk == self.hero.pk:
                strengths.append(character.stats.strength)
            return update_needs(character, *args, **kwargs)

        with patch.object(Character, "update_needs", tracked_needs):
            self.campaign.next_turn(seconds=60, reset=True)
        self.assertEqual(strengths, [7])

    def test_empty_shared_character_list_does_not_reload_campaign_characters(self):
        effect = Effect.objects.create(
            name="Periodic",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            interval=timedelta(minutes=1),
            apply=False,
        )
        active = effect.affect(self.campaign, force=True)
        active.campaign.current_game_date += timedelta(minutes=1)
        with CaptureQueriesContext(connection) as queries:
            damages = active.apply_all(save=False, characters=[])
        self.assertEqual(damages, [])
        self.assertFalse(any('from "fallout_character"' in query["sql"].lower() for query in queries))
        self.assertFalse(DamageHistory.objects.exists())

    def test_successive_time_steps_use_current_active_effects(self):
        first = Effect.objects.create(
            name="First",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            interval=timedelta(minutes=1),
            apply=False,
        )
        first.affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=60, reset=True)
        CampaignEffect.objects.filter(campaign=self.campaign).delete()
        Effect.objects.create(
            name="Second",
            damage_type=DAMAGE_RAW,
            raw_damage=7,
            interval=timedelta(minutes=1),
            apply=False,
        ).affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=60, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 88)

    def test_take_loot_merges_inventory_and_decreases_remaining_stock(self):
        existing = self.ammunition.give(self.hero, quantity=2)
        loot = Loot.objects.create(campaign=self.campaign, item=self.ammunition, quantity=5)
        equipment = loot.take(self.hero, quantity=3, is_action=True)
        existing.refresh_from_db()
        loot.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(equipment.pk, existing.pk)
        self.assertEqual((existing.quantity, loot.quantity), (5, 2))
        self.assertEqual(self.hero.action_points, 10 - AP_COST_TAKE)

    def test_take_all_available_loot_removes_the_loot_entry(self):
        loot = Loot.objects.create(campaign=self.campaign, item=self.ammunition, quantity=2)
        loot_id = loot.pk
        equipment = loot.take(self.hero.pk, quantity=99)
        self.assertEqual(equipment.quantity, 2)
        self.assertFalse(Loot.objects.filter(pk=loot_id).exists())

    def test_take_rejects_character_from_another_campaign(self):
        self.target.campaign = Campaign.objects.create(name="Other")
        self.target.save()
        loot = Loot.objects.create(campaign=self.campaign, item=self.ammunition, quantity=2)
        with self.assertRaises(AssertionError):
            loot.take(self.target)
        loot.refresh_from_db()
        self.assertEqual(loot.quantity, 2)
        self.assertFalse(Equipment.objects.filter(character=self.target).exists())

    def test_take_rejects_insufficient_action_points(self):
        loot = Loot.objects.create(campaign=self.campaign, item=self.ammunition, quantity=2)
        self.hero.action_points = 0
        self.hero.save()
        with self.assertRaises(AssertionError):
            loot.take(self.hero, is_action=True)
        loot.refresh_from_db()
        self.assertEqual(loot.quantity, 2)
        self.assertFalse(Equipment.objects.exists())

    def test_create_loot_merges_stackable_items(self):
        first = Loot.create(self.campaign, self.ammunition, quantity=2)
        second = Loot.create(self.campaign, self.ammunition, quantity=3)
        self.assertEqual(first.pk, second.pk)
        first.refresh_from_db()
        self.assertEqual(first.quantity, 5)

    def test_template_creates_loot_with_quantities_conditions_and_money(self):
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100)
        excluded = Item.objects.create(name="Excluded", type=ITEM_MISC)
        template = LootTemplate.objects.create(name="Chest", min_money=100, max_money=100)
        LootTemplateItem.objects.create(template=template, item=self.ammunition, min_quantity=3, max_quantity=3)
        LootTemplateItem.objects.create(template=template, item=armor, min_condition=75, max_condition=75)
        LootTemplateItem.objects.create(template=template, item=excluded, chance=0)
        loots, money = template.create(self.campaign.pk, self.hero.pk)
        self.campaign.refresh_from_db()
        self.assertEqual({loot.item_id for loot in loots}, {self.ammunition.pk, armor.pk})
        self.assertEqual(Loot.objects.get(item=self.ammunition).quantity, 3)
        self.assertEqual(Loot.objects.get(item=armor).condition, 0.75)
        self.assertEqual(money, int(100 * EXTRA_LUCK_MONEY_MULT))
        self.assertEqual(self.campaign.money_loot, money)

    def test_template_rejects_character_from_another_campaign_before_creating_loot(self):
        self.target.campaign = Campaign.objects.create(name="Other")
        self.target.save()
        template = LootTemplate.objects.create(name="Chest", min_money=100, max_money=100)
        with self.assertRaises(AssertionError):
            template.create(self.campaign, self.target)
        self.campaign.refresh_from_db()
        self.assertEqual(self.campaign.money_loot, 0)
        self.assertFalse(Loot.objects.exists())
