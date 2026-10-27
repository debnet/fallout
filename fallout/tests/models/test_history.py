# coding: utf-8
from django.conf import settings

from fallout.enums import DAMAGE_NORMAL, PART_TORSO, STATUS_HIT_FAILED, STATUS_HIT_SUCCEED
from fallout.models import DamageHistory, FightHistory, RollHistory
from fallout.tests.models.base import CoreTestCase


class HistoryAggregationTests(CoreTestCase):
    def test_roll_statistics_group_levels_results_and_characters(self):
        self.hero.level = 2
        RollHistory.objects.create(character=self.hero, level=1, stats="small_guns", success=True)
        RollHistory.objects.create(character=self.hero, level=2, stats="small_guns", success=False, critical=True)
        RollHistory.objects.create(character=self.target, level=2, stats="small_guns", success=True)
        stats = {stat.code: stat for stat in RollHistory.get_stats(self.hero)}["small_guns"]
        self.assertEqual((stats.total_count, stats.total_success, stats.success_rate), (2, 1, 50))
        self.assertEqual((stats.previous_total, stats.current_total), (1, 1))
        self.assertEqual(sum(row[0] for row in stats.all), 2)
        self.assertEqual(sum(row[0] for row in stats.previous_stats), 1)
        self.assertEqual(sum(row[0] for row in stats.current_stats), 1)

    def test_fight_statistics_separate_given_and_received_damage(self):
        self.hero.level = 2
        damage = DamageHistory.objects.create(character=self.target, real_damage=8)
        FightHistory.objects.create(
            attacker=self.hero,
            defender=self.target,
            attacker_level=1,
            status=STATUS_HIT_SUCCEED,
            success=True,
            damage=damage,
        )
        FightHistory.objects.create(
            attacker=self.hero,
            defender=self.target,
            attacker_level=2,
            status=STATUS_HIT_FAILED,
            success=False,
        )
        FightHistory.objects.create(
            attacker=self.target,
            defender=self.hero,
            defender_level=2,
            status=STATUS_HIT_SUCCEED,
            success=True,
        )
        attacker, defender = FightHistory.get_stats(self.hero)
        self.assertEqual((attacker.total_count, attacker.total_success, attacker.total_damage), (2, 1, 8))
        self.assertEqual((attacker.success_rate, attacker.damage_rate), (50, 8))
        self.assertEqual((attacker.previous_total, attacker.current_total), (1, 1))
        self.assertEqual(sum(row[0] for row in attacker.all), 2)
        self.assertEqual(sum(row[0] for row in attacker.previous_stats), 1)
        self.assertEqual(sum(row[0] for row in attacker.current_stats), 1)
        self.assertEqual((defender.total_count, defender.total_success), (1, 1))

    def test_fight_statistics_count_all_attacks_in_a_group(self):
        self.hero.level = 2
        for _ in range(3):
            FightHistory.objects.create(
                attacker=self.hero,
                defender=self.target,
                attacker_level=2,
                status=STATUS_HIT_SUCCEED,
                success=True,
            )
        attacker, _ = FightHistory.get_stats(self.hero)
        self.assertEqual(attacker.total_count, 3)
        self.assertEqual(attacker.current_total, 3)

    def test_fight_statistics_damage_per_level_counts_damage_not_attacks(self):
        self.hero.level = 2
        damage = DamageHistory.objects.create(character=self.target, real_damage=8)
        FightHistory.objects.create(
            attacker=self.hero,
            defender=self.target,
            attacker_level=1,
            status=STATUS_HIT_SUCCEED,
            success=True,
            damage=damage,
        )
        attacker, _ = FightHistory.get_stats(self.hero)
        self.assertEqual(attacker.previous_damage, 8)
        self.assertEqual(attacker.current_damage, 0)

    def test_history_labels_include_modifier_body_part_and_combat_details(self):
        weapon, _ = self.armed_inventory()
        roll = RollHistory(character=self.hero, stats="small_guns", value=60, roll=20, modifier=-5, success=True)
        self.assertIn("-5", roll.long_label)
        self.assertIn("Hero", str(roll))
        self.assertEqual(roll.message_level, settings.MESSAGE_INFOS[True, False])
        damage = DamageHistory(
            character=self.target, damage_type=DAMAGE_NORMAL, body_part=PART_TORSO, real_damage=5, base_damage=8
        )
        self.assertIn(str(damage.get_body_part_display()), damage.long_label)
        self.assertIn("Target", str(damage))
        fight = FightHistory(
            attacker=self.hero,
            defender=self.target,
            attacker_weapon=weapon.item,
            body_part=PART_TORSO,
            status=STATUS_HIT_SUCCEED,
            success=True,
            damage=damage,
        )
        self.assertIn("Gun", fight.description)
        self.assertIn("Hero", fight.description)
        self.assertIn("Target", str(fight))
        self.assertIn("5", fight.damage_label)
        self.assertEqual(fight.message_level, settings.MESSAGE_INFOS[True, False])
        fight.damage = None
        self.assertEqual(fight.damage_label, "")
        self.assertIn("Gun", fight.description)
