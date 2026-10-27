# coding: utf-8
from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from fallout.enums import ITEM_AMMO, ITEM_ARMOR, ITEM_MISC, ITEM_WEAPON, MODE_MELEE, MODE_RANGED
from fallout.models import Effect, EffectModifier, Equipment, Item, ItemModifier, LootTemplate, LootTemplateItem
from fallout.tests.models.base import CoreTestCase


class ModelValidationTests(SimpleTestCase):
    def test_item_rejects_inverted_ranges_and_damage(self):
        for values, field in (
            ({"min_range": 2, "max_range": 1}, "min_range"),
            ({"min_burst_range": 2, "max_burst_range": 1}, "min_burst_range"),
            ({"min_damage": 2, "max_damage": 1}, "min_damage"),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError) as error:
                Item(**values).clean()
            self.assertIn(field, error.exception.message_dict)
        Item(min_range=1, max_range=1, min_damage=2, max_damage=2).clean()

    def test_effect_rejects_inverted_duration_and_damage(self):
        for values, field in (
            ({"min_duration": timedelta(minutes=2), "max_duration": timedelta(minutes=1)}, "min_duration"),
            ({"min_damage": 2, "max_damage": 1}, "min_damage"),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError) as error:
                Effect(**values).clean()
            self.assertIn(field, error.exception.message_dict)
        Effect(min_duration=timedelta(minutes=1), max_duration=timedelta(minutes=1)).clean()

    def test_modifiers_reject_inverted_bounds_and_accept_equal_values(self):
        for model in (ItemModifier, EffectModifier):
            with self.subTest(model=model.__name__):
                with self.assertRaises(ValidationError) as error:
                    model(min_value=2, max_value=1).clean()
                self.assertIn("min_value", error.exception.message_dict)
                model(min_value=2, max_value=2).clean()

    def test_loot_template_rejects_inverted_money_bounds(self):
        with self.assertRaises(ValidationError) as error:
            LootTemplate(min_money=20, max_money=10).clean()
        self.assertIn("min_money", error.exception.message_dict)
        LootTemplate(min_money=0, max_money=0).clean()

    def test_loot_template_item_rejects_inverted_quantity_and_condition(self):
        for values, field in (
            ({"min_quantity": 2, "max_quantity": 1}, "min_quantity"),
            ({"min_condition": 90, "max_condition": 80}, "min_condition"),
        ):
            with self.subTest(field=field), self.assertRaises(ValidationError) as error:
                LootTemplateItem(**values).clean()
            self.assertIn(field, error.exception.message_dict)
        LootTemplateItem(min_quantity=1, max_quantity=1, min_condition=80, max_condition=80).clean()


class EquipmentValidationTests(CoreTestCase):
    def test_slot_must_match_item_type(self):
        with self.assertRaises(ValidationError) as error:
            Equipment(character=self.hero, item=self.ammunition, slot=ITEM_ARMOR).clean()
        self.assertIn("slot", error.exception.message_dict)

    def test_only_one_equipment_can_occupy_a_slot(self):
        self.armed_inventory()
        with self.assertRaises(ValidationError) as error:
            Equipment(character=self.hero, item=self.ammunition, slot=ITEM_AMMO).clean()
        self.assertIn("slot", error.exception.message_dict)

    def test_incompatible_weapon_or_ammo_cannot_be_equipped(self):
        weapon, ammo = self.armed_inventory()
        weapon.item.ammunitions.clear()
        for equipment in (weapon, ammo):
            with self.subTest(slot=equipment.slot), self.assertRaises(ValidationError) as error:
                equipment.clean()
            self.assertIn("item", error.exception.message_dict)

    def test_secondary_weapon_must_be_a_unique_melee_weapon(self):
        for item in (
            Item(name="Misc", type=ITEM_MISC),
            Item(name="Gun", type=ITEM_WEAPON, attack_mode=MODE_RANGED),
        ):
            with self.subTest(item=item.name), self.assertRaises(ValidationError) as error:
                Equipment(character=self.hero, item=item, secondary=True).clean()
            self.assertIn("item", error.exception.message_dict)
        knife = Item.objects.create(name="Knife", type=ITEM_WEAPON, attack_mode=MODE_MELEE)
        Equipment.objects.create(character=self.hero, item=knife, secondary=True)
        with self.assertRaises(ValidationError) as error:
            Equipment(character=self.hero, item=knife, secondary=True).clean()
        self.assertIn("secondary", error.exception.message_dict)
