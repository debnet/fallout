# coding: utf-8
from datetime import timedelta

from django.contrib import messages
from django.test import SimpleTestCase
from django.urls import reverse

from fallout.enums import (
    DAMAGE_NORMAL,
    ITEM_ARMOR,
    ITEM_GRENADE,
    ITEM_WEAPON,
    MODE_MELEE,
    MODE_RANGED,
    MODE_THROW,
    PART_TORSO,
)
from fallout.models import (
    CampaignEffect,
    CharacterEffect,
    Effect,
    Equipment,
    Item,
    ItemModifier,
    Log,
    Loot,
    LootTemplate,
    LootTemplateItem,
    Statistics,
)
from fallout.tests.models.base import CoreTestCase


class ModifierPropertyTests(SimpleTestCase):
    def test_modifier_labels_support_fixed_random_positive_and_negative_values(self):
        for values, expected in (
            ({}, ""),
            ({"current_value": 3}, "+3"),
            ({"current_value": -3}, "-3"),
            ({"current_value": 0}, "0"),
            ({"min_value": 1, "max_value": 3}, "1-3"),
            ({"min_value": -5, "max_value": -1}, "-(1-5)"),
            ({"raw_value": 2}, "+2"),
            ({"min_value": 1, "max_value": 3, "raw_value": -2}, "1-3 (-2)"),
        ):
            with self.subTest(values=values):
                modifier = ItemModifier(
                    stats="strength", **{key: value for key, value in values.items() if key != "current_value"}
                )
                if "current_value" in values:
                    modifier.current_value = values["current_value"]
                self.assertEqual(modifier.label_modifier, expected)
                self.assertIn(expected, str(modifier))

    def test_reducing_needs_is_a_bonus_but_reducing_strength_is_a_penalty(self):
        for stat, amount, bonus in (
            ("thirst", -2, True),
            ("thirst", 2, False),
            ("strength", -2, False),
            ("strength", 2, True),
        ):
            with self.subTest(stat=stat, amount=amount):
                modifier = ItemModifier(stats=stat, min_value=amount, max_value=amount)
                self.assertEqual(modifier.is_bonus, bonus)
                self.assertEqual(modifier.message_level, messages.SUCCESS if bonus else messages.ERROR)

    def test_damage_labels_include_range_bonus_type_and_body_part(self):
        item = Item(damage_type=DAMAGE_NORMAL, min_damage=2, max_damage=4, raw_damage=3)
        self.assertEqual(item.label_damage, "2-4 (+3)")
        self.assertIn("2-4 (+3)", item.long_label_damage)
        item.body_part = PART_TORSO
        self.assertTrue(item.long_label_damage.endswith(f"({item.get_body_part_display()})"))
        item.min_damage = item.max_damage = item.raw_damage = 0
        item.body_part = ""
        self.assertEqual(item.long_label_damage, item.get_damage_type_display())

    def test_item_weapon_modes_and_resistances(self):
        for mode, ranged, melee, throwable in (
            (MODE_RANGED, True, False, False),
            (MODE_MELEE, False, True, False),
            (MODE_THROW, False, False, True),
        ):
            with self.subTest(mode=mode):
                item = Item(type=ITEM_WEAPON, attack_mode=mode)
                self.assertEqual((item.is_ranged, item.is_melee, item.is_throwable), (ranged, melee, throwable))
                self.assertFalse(item.is_burst)
        self.assertTrue(Item(type=ITEM_GRENADE).is_burst)
        armor = Item(type=ITEM_ARMOR, normal_threshold=5, normal_resistance=20)
        resistance = next(value for value in armor.resistances if value.code == DAMAGE_NORMAL)
        self.assertEqual((resistance.threshold, resistance.resistance), (5, 20))


class ModelRepresentationTests(CoreTestCase):
    def test_urls_names_and_elapsed_time(self):
        self.campaign.title = "Subtitle"
        self.hero.title = "Wanderer"
        self.assertEqual(str(self.campaign), "Campaign (Subtitle)")
        self.assertEqual(str(self.hero), "Hero (Wanderer)")
        self.assertEqual(self.campaign.get_absolute_url(), reverse("fallout:campaign", args=(self.campaign.pk,)))
        self.assertEqual(self.hero.get_absolute_url(), reverse("fallout:character", args=(self.hero.pk,)))
        self.campaign.current_game_date = self.campaign.start_game_date + timedelta(hours=2)
        self.assertEqual(self.campaign.elapsed_time, timedelta(hours=2))

    def test_catalog_and_related_model_representations(self):
        item = Item(name="Armor", title="Worn", type=ITEM_ARMOR)
        effect = Effect(name="Burn", title="Severe")
        template = LootTemplate(name="Chest", title="Locked")
        self.assertEqual(str(item), "Armor (Worn)")
        self.assertEqual(str(effect), "Burn (Severe)")
        self.assertEqual(str(template), "Chest (Locked)")
        self.assertEqual(str(LootTemplate(name="Chest")), "Chest")
        for instance in (
            Equipment(character=self.hero, item=item),
            Loot(campaign=self.campaign, item=item),
            LootTemplateItem(template=template, item=item),
        ):
            self.assertIn("Armor", str(instance))
        self.assertIn("Hero", str(Statistics(character=self.hero)))
        self.assertIn("Campaign", str(CampaignEffect(campaign=self.campaign, effect=effect)))
        self.assertIn("Hero", str(CharacterEffect(character=self.hero, effect=effect)))
        self.assertIn("Hero", str(Log(character=self.hero)))
