# coding: utf-8
from unittest.mock import patch

from django.core.exceptions import ValidationError

from fallout.constants import AP_COST_REPAIR
from fallout.enums import ITEM_AMMO, ITEM_ARMOR, ITEM_MISC, ITEM_WEAPON, MODE_MELEE
from fallout.models import Effect, EffectModifier, Equipment, Item, ItemModifier, Loot, LootTemplate, LootTemplateItem
from fallout.tests.models.base import CoreTestCase


class InventoryOperationTests(CoreTestCase):
    def test_single_charge_reload_fills_clip_using_one_ammunition(self):
        weapon, ammo = self.armed_inventory()
        weapon.item.is_single_charge = True
        weapon.item.save()
        weapon.reload()
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual(weapon.clip_count, 6)
        self.assertEqual(ammo.quantity, 9)

    def test_unequipping_loaded_weapon_returns_clip_to_stock(self):
        weapon, ammo = self.armed_inventory()
        weapon.clip_count = 4
        weapon.save()
        weapon.equip()
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual((weapon.slot, weapon.clip_count, ammo.quantity), ("", 0, 14))

    def test_unequipping_ammunition_unloads_weapon_into_stock(self):
        weapon, ammo = self.armed_inventory()
        ammo.equip()
        weapon.refresh_from_db()
        ammo.refresh_from_db()
        self.assertEqual((weapon.clip_count, ammo.slot, ammo.quantity), (0, "", 11))

    def test_dropping_equipped_weapon_unloads_before_creating_loot(self):
        weapon, ammo = self.armed_inventory()
        weapon_id = weapon.pk
        loot = weapon.drop()
        ammo.refresh_from_db()
        self.assertFalse(Equipment.objects.filter(pk=weapon_id).exists())
        self.assertEqual(ammo.quantity, 11)
        self.assertEqual((loot.item_id, loot.campaign_id, loot.quantity), (weapon.item_id, self.campaign.pk, 1))

    def test_repair_accepts_percentage_and_fraction_and_spends_optional_ap(self):
        weapon, _ = self.armed_inventory()
        weapon.condition = 0.2
        weapon.save()
        weapon.repair(value=75, is_action=True)
        weapon.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(weapon.condition, 0.75)
        self.assertEqual(weapon.current_condition, 75)
        self.assertEqual(self.hero.action_points, 10 - AP_COST_REPAIR)
        weapon.repair(value=0.5)
        weapon.refresh_from_db()
        self.assertEqual(weapon.condition, 0.5)

    def test_repair_rejects_nonrepairable_items_and_insufficient_ap(self):
        ammo = self.ammunition.give(self.hero)
        with self.assertRaises(AssertionError):
            ammo.repair()
        weapon, _ = self.armed_inventory()
        self.hero.action_points = 0
        with self.assertRaises(AssertionError):
            weapon.repair(is_action=True)

    def test_secondary_weapon_replaces_previous_one(self):
        knife = Item.objects.create(name="Knife", type=ITEM_WEAPON, attack_mode=MODE_MELEE)
        first = Equipment.objects.create(character=self.hero, item=knife)
        second = Equipment.objects.create(character=self.hero, item=knife)
        first.set_secondary()
        second.set_secondary()
        first.refresh_from_db()
        second.refresh_from_db()
        self.assertFalse(first.secondary)
        self.assertTrue(second.secondary)

    def test_secondary_assignment_restores_previous_flag_if_save_fails(self):
        knife = Item.objects.create(name="Knife", type=ITEM_WEAPON, attack_mode=MODE_MELEE)
        first = Equipment.objects.create(character=self.hero, item=knife, secondary=True)
        second = Equipment.objects.create(character=self.hero, item=knife)
        with patch.object(Equipment, "save", side_effect=ValidationError("Rejected")):
            with self.assertRaises(ValidationError):
                second.set_secondary()
        first.refresh_from_db()
        self.assertTrue(first.secondary)
        self.assertFalse(Equipment.objects.get(pk=second.pk).secondary)

    def test_ammunition_compatibility_for_free_and_equipped_ammo(self):
        weapon, ammo = self.armed_inventory()
        self.assertIsNone(ammo.compatible_ammunition)
        free = Equipment(character=self.hero, item=self.ammunition)
        self.assertTrue(free.compatible_ammunition)
        other = Item.objects.create(name="Other ammo", type=ITEM_AMMO)
        self.assertFalse(Equipment(character=self.hero, item=other).compatible_ammunition)
        self.assertIsNone(weapon.compatible_ammunition)

    def test_loot_character_can_copy_then_empty_droppable_inventory_and_money(self):
        self.hero.money = 20
        self.hero.save()
        weapon, ammo = self.armed_inventory()
        quest = Item.objects.create(name="Quest", type=ITEM_MISC, is_droppable=False)
        quest.give(self.hero)
        loots = self.hero.loot(empty=False)
        self.hero.refresh_from_db()
        self.campaign.refresh_from_db()
        self.assertEqual({loot.item_id for loot in loots}, {weapon.item_id, ammo.item_id})
        self.assertEqual(self.campaign.money_loot, 20)
        self.assertEqual(self.hero.money, 20)
        self.assertEqual(self.hero.equipments.count(), 3)
        self.hero.loot(empty=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.money, 0)
        self.assertFalse(self.hero.equipments.exists())

    def test_loot_creation_keeps_repairable_items_separate(self):
        armor = Item.objects.create(name="Armor", type=ITEM_ARMOR, durability=100)
        first = Loot.create(self.campaign, armor.pk, condition=0.5)
        second = Loot.create(self.campaign, armor, condition=0.8)
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual((first.current_condition, second.current_condition), (50, 80))
        first.quantity = 0
        first.save()
        self.assertEqual(Loot.objects.filter(item=armor).count(), 1)


class CatalogDuplicationTests(CoreTestCase):
    def test_item_duplicate_copies_modifiers_effects_and_ammunition_without_altering_source(self):
        weapon, _ = self.armed_inventory()
        item = weapon.item
        source_id = item.pk
        effect = Effect.objects.create(name="Burn")
        item.effects.add(effect)
        modifier = ItemModifier.objects.create(item=item, stats="strength", min_value=1, max_value=1)
        copy = item.duplicate(name="Copy")
        self.assertNotEqual(copy.pk, source_id)
        self.assertEqual(Item.objects.get(pk=source_id).name, "Gun")
        self.assertEqual(list(copy.effects.values_list("pk", flat=True)), [effect.pk])
        self.assertEqual(list(copy.ammunitions.values_list("pk", flat=True)), [self.ammunition.pk])
        copied_modifier = copy.modifiers.get()
        self.assertNotEqual(copied_modifier.pk, modifier.pk)
        self.assertEqual(copied_modifier.min_value, 1)
        self.assertTrue(ItemModifier.objects.filter(pk=modifier.pk, item_id=source_id).exists())

    def test_effect_duplicate_copies_modifier_and_keeps_chain_references(self):
        next_effect = Effect.objects.create(name="Next")
        effect = Effect.objects.create(name="Original", next_effect=next_effect)
        source_id = effect.pk
        modifier = EffectModifier.objects.create(effect=effect, stats="strength", min_value=2, max_value=2)
        copy = effect.duplicate()
        self.assertNotEqual(copy.pk, source_id)
        self.assertEqual(copy.name, "* Original")
        self.assertEqual(copy.next_effect_id, next_effect.pk)
        self.assertNotEqual(copy.modifiers.get().pk, modifier.pk)
        self.assertTrue(EffectModifier.objects.filter(pk=modifier.pk, effect_id=source_id).exists())

    def test_loot_template_duplicate_copies_entries_and_keeps_original(self):
        template = LootTemplate.objects.create(name="Chest", min_money=10, max_money=20)
        source_id = template.pk
        entry = LootTemplateItem.objects.create(template=template, item=self.ammunition, min_quantity=2, max_quantity=4)
        copy = template.duplicate()
        self.assertNotEqual(copy.pk, source_id)
        self.assertEqual(copy.name, "* Chest")
        copied_entry = copy.items.get()
        self.assertNotEqual(copied_entry.pk, entry.pk)
        self.assertEqual(
            (copied_entry.item_id, copied_entry.min_quantity, copied_entry.max_quantity), (self.ammunition.pk, 2, 4)
        )
        self.assertEqual(LootTemplate.objects.get(pk=source_id).name, "Chest")

    def test_unsaved_catalog_entries_cannot_be_duplicated(self):
        for instance in (Item(name="Unsaved"), Effect(name="Unsaved"), LootTemplate(name="Unsaved")):
            with self.subTest(model=type(instance).__name__), self.assertRaises(AssertionError):
                instance.duplicate()
