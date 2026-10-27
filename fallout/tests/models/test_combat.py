# coding: utf-8
from unittest.mock import patch

from fallout.enums import (
    ADD_KARMA,
    ADD_MONEY,
    DAMAGE_HUNGER,
    DAMAGE_NORMAL,
    DAMAGE_RADIATION,
    DAMAGE_RAW,
    DAMAGE_SLEEP,
    DAMAGE_THIRST,
    HEAL_HUNGER,
    HEAL_RADIATION,
    HEAL_SLEEP,
    HEAL_THIRST,
    ITEM_ARMOR,
    ITEM_HELMET,
    ITEM_WEAPON,
    MODE_MELEE,
    MODE_THROW,
    PART_HEAD,
    PART_TORSO,
    REMOVE_KARMA,
    REMOVE_MONEY,
    STATUS_NO_MORE_AMMO,
    STATUS_TARGET_DEAD,
    WEAPON_TYPE_SECONDARY,
    WEAPON_TYPE_UNARMED,
)
from fallout.models import CharacterEffect, DamageHistory, Effect, Equipment, FightHistory, Item, Loot
from fallout.tests.models.base import CoreTestCase


class DamageProtectionTests(CoreTestCase):
    def test_armor_absorbs_damage_and_degrades_according_to_prevented_damage(self):
        armor = Item.objects.create(
            name="Armor", type=ITEM_ARMOR, durability=100, normal_threshold=5, normal_resistance=50
        )
        equipment = Equipment.objects.create(character=self.hero, item=armor, slot=ITEM_ARMOR, condition=1.0)
        history = self.hero.damage(raw_damage=20, damage_type=DAMAGE_NORMAL, body_part=PART_TORSO)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual((history.armor_id, history.armor_threshold, history.armor_resistance), (armor.pk, 5, 50))
        self.assertEqual(history.real_damage, 8)
        self.assertAlmostEqual(history.armor_damage, 0.125)
        self.assertAlmostEqual(equipment.condition, 0.875)
        self.assertEqual(self.hero.health, 92)

    def test_head_damage_uses_helmet_instead_of_body_armor(self):
        for slot, threshold in ((ITEM_ARMOR, 10), (ITEM_HELMET, 4)):
            item = Item.objects.create(name=slot, type=slot, durability=100, normal_threshold=threshold)
            Equipment.objects.create(character=self.hero, item=item, slot=slot, condition=1.0)
        history = self.hero.damage(raw_damage=20, damage_type=DAMAGE_NORMAL, body_part=PART_HEAD)
        self.assertEqual(history.armor.type, ITEM_HELMET)
        self.assertEqual(history.real_damage, 16)

    def test_armor_simulation_preserves_condition_health_and_histories(self):
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100, normal_threshold=5)
        equipment = Equipment.objects.create(character=self.hero, item=armor, slot=ITEM_ARMOR, condition=1.0)
        result = self.hero.damage(raw_damage=20, damage_type=DAMAGE_NORMAL, body_part=PART_TORSO, simulation=True)
        self.assertEqual(result.real_damage, 15)
        equipment.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual((equipment.condition, self.hero.health), (1.0, 100))
        self.assertFalse(DamageHistory.objects.exists())

    def test_damage_can_change_radiation_money_and_karma_in_both_directions(self):
        self.hero.rads, self.hero.money, self.hero.karma = 20, 20, 20
        self.hero.thirst, self.hero.hunger, self.hero.sleep = 20, 20, 20
        self.hero.save()
        for damage_type, field, expected in (
            (DAMAGE_RADIATION, "rads", 25),
            (HEAL_RADIATION, "rads", 20),
            (ADD_MONEY, "money", 25),
            (REMOVE_MONEY, "money", 20),
            (ADD_KARMA, "karma", 25),
            (REMOVE_KARMA, "karma", 20),
            (DAMAGE_THIRST, "thirst", 25),
            (HEAL_THIRST, "thirst", 20),
            (DAMAGE_HUNGER, "hunger", 25),
            (HEAL_HUNGER, "hunger", 20),
            (DAMAGE_SLEEP, "sleep", 25),
            (HEAL_SLEEP, "sleep", 20),
        ):
            with self.subTest(damage_type=damage_type):
                self.hero.damage(raw_damage=5, damage_type=damage_type)
                self.hero.refresh_from_db()
                self.assertEqual(getattr(self.hero, field), expected)
                self.assertEqual(self.hero.health, 100)

    def test_damage_against_already_unconscious_character_has_no_history_or_changes(self):
        self.hero.health = 0
        self.hero.save()
        result = self.hero.damage(raw_damage=20, damage_type=DAMAGE_RAW)
        self.assertIsNone(result.pk)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 0)
        self.assertFalse(DamageHistory.objects.exists())


class CombatBranchTests(CoreTestCase):
    def test_missing_target_returns_no_result(self):
        self.assertIsNone(self.hero.fight(None))
        self.assertFalse(FightHistory.objects.exists())

    def test_target_id_is_resolved_and_dead_target_does_not_receive_damage(self):
        self.target.health = 0
        self.target.save()
        result = self.hero.fight(self.target.pk)
        self.assertEqual(result.status, STATUS_TARGET_DEAD)
        self.assertIsNone(result.damage)
        self.assertFalse(DamageHistory.objects.exists())

    def test_empty_clip_rejects_attack_without_consuming_stock(self):
        weapon, ammo = self.armed_inventory()
        weapon.clip_count = 0
        weapon.save()
        result = self.hero.fight(self.target)
        ammo.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual(result.status, STATUS_NO_MORE_AMMO)
        self.assertEqual((ammo.quantity, self.target.health), (10, 100))

    def test_empty_throwing_weapon_rejects_attack_without_creating_loot(self):
        knife = Item.objects.create(name="Empty knife", type=ITEM_WEAPON, attack_mode=MODE_THROW)
        Equipment.objects.create(character=self.hero, item=knife, slot=ITEM_WEAPON, quantity=0)
        result = self.hero.fight(self.target)
        self.assertEqual(result.status, STATUS_NO_MORE_AMMO)
        self.assertFalse(Loot.objects.exists())

    def test_secondary_melee_weapon_can_attack(self):
        knife = Item.objects.create(
            name="Knife", type=ITEM_WEAPON, attack_mode=MODE_MELEE, raw_damage=4, damage_type=DAMAGE_RAW, max_range=1
        )
        Equipment.objects.create(character=self.hero, item=knife, secondary=True)
        result = self.hero.fight(self.target, weapon_type=WEAPON_TYPE_SECONDARY, force_success=True)
        self.assertEqual(result.attacker_weapon_id, knife.pk)
        self.assertTrue(result.success)
        self.target.refresh_from_db()
        self.assertLess(self.target.health, 100)

    def test_forced_critical_raw_damage_bypasses_personal_protection(self):
        weapon, _ = self.armed_inventory()
        weapon.item.damage_type = DAMAGE_NORMAL
        weapon.item.save()
        self.target.damage_threshold = 100
        self.target.normal_resistance = 100
        self.target.save()
        result = self.hero.fight(self.target, force_success=True, force_critical=True, force_raw_damage=True)
        self.assertTrue(result.critical)
        self.assertEqual(result.damage.damage_type, DAMAGE_RAW)
        self.assertGreater(result.damage.real_damage, 0)

    def test_attack_outside_weapon_range_has_zero_hit_chance(self):
        result = self.hero.fight(self.target, weapon_type=WEAPON_TYPE_UNARMED, target_range=2)
        self.assertEqual(result.hit_chance, 0)
        self.assertFalse(result.success)
        self.target.refresh_from_db()
        self.assertEqual(self.target.health, 100)

    def test_fight_experience_uses_target_reward_and_damage_fraction(self):
        self.armed_inventory()
        self.target.reward = 100
        self.target.save()
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            result = self.hero.fight(self.target, force_success=True, target_part=PART_TORSO)
        self.assertEqual(result.experience, int(100 * result.damage.damage_rate))
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.experience, result.experience)

    def test_burst_experience_sums_target_rewards_for_each_hit(self):
        weapon, _ = self.armed_inventory()
        weapon.clip_count = 3
        weapon.save()
        self.target.reward = 100
        self.target.save()
        with patch("fallout.models.randint", side_effect=lambda low, high: low):
            results = self.hero.burst([(self.target, 1)], force_success=True, is_action=False, target_part=PART_TORSO)
        self.assertEqual(len(results), 3)
        self.assertTrue(all(result.experience == int(100 * result.damage.damage_rate) for result in results))
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.experience, sum(result.experience for result in results))

    def test_critical_failure_hits_failure_target_but_only_consumes_one_round(self):
        weapon, ammo = self.armed_inventory()
        self.hero.small_guns = 0
        self.hero.save()
        with patch("fallout.models.randint", side_effect=lambda low, high: high):
            result = self.hero.fight(self.target, fail_target=self.hero)
        self.assertFalse(result.success)
        self.assertTrue(result.critical)
        self.assertIsNotNone(result.fail)
        self.assertEqual(result.fail.defender_id, self.hero.pk)
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual((weapon.clip_count, ammo.quantity), (0, 10))
        self.assertEqual(FightHistory.objects.count(), 2)

    def test_thrown_weapon_is_consumed_and_becomes_loot(self):
        knife = Item.objects.create(
            name="Throwing knife",
            type=ITEM_WEAPON,
            attack_mode=MODE_THROW,
            raw_damage=2,
            damage_type=DAMAGE_RAW,
            max_range=10,
        )
        equipment = Equipment.objects.create(character=self.hero, item=knife, slot=ITEM_WEAPON, quantity=2)
        self.hero.fight(self.target, force_success=True)
        equipment.refresh_from_db()
        self.assertEqual(equipment.quantity, 1)
        self.assertEqual(Loot.objects.get(campaign=self.campaign, item=knife).quantity, 1)

    def test_weapon_effect_is_applied_on_successful_hit_without_crashing(self):
        weapon, _ = self.armed_inventory()
        effect = Effect.objects.create(name="Burn", damage_type=DAMAGE_RAW, raw_damage=1)
        weapon.item.effects.add(effect)
        result = self.hero.fight(self.target, force_success=True)
        self.assertTrue(result.success)
        self.assertTrue(CharacterEffect.objects.filter(character=self.target, effect=effect).exists())
