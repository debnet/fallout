# coding: utf-8
from django.test import TestCase

from fallout.enums import DAMAGE_RAW, ITEM_AMMO, ITEM_WEAPON, MODE_RANGED
from fallout.models import Campaign, Character, Effect, Equipment, Item


class CoreTestCase(TestCase):
    def setUp(self):
        Character._stats.clear()
        Effect.damages.clear()
        self.addCleanup(Character._stats.clear)
        self.addCleanup(Effect.damages.clear)
        self.campaign = Campaign.objects.create(name="Campaign", needs=False)
        self.hero = Character.objects.create(
            name="Hero",
            campaign=self.campaign,
            is_player=True,
            has_stats=False,
            has_needs=False,
            max_health=100,
            max_action_points=10,
            sequence=20,
            luck=5,
            strength=5,
            small_guns=60,
            unarmed=60,
            throwing=60,
            melee_damage=5,
            skill_points=500,
            skill_points_per_level=10,
            hit_points_per_level=5,
            perk_rate=2,
        )
        self.target = Character.objects.create(
            name="Target",
            campaign=self.campaign,
            is_player=True,
            has_stats=False,
            has_needs=False,
            max_health=100,
            max_action_points=10,
            sequence=10,
            luck=5,
        )
        self.ammunition = Item.objects.create(name="Ammo", type=ITEM_AMMO)

    def armed_inventory(self):
        gun = Item.objects.create(
            name="Gun",
            type=ITEM_WEAPON,
            attack_mode=MODE_RANGED,
            skill="small_guns",
            durability=100,
            clip_size=6,
            burst_count=3,
            raw_damage=8,
            damage_type=DAMAGE_RAW,
            max_range=10,
            max_burst_range=10,
            ap_cost_normal=2,
            ap_cost_target=3,
            ap_cost_burst=3,
            ap_cost_reload=2,
        )
        gun.ammunitions.add(self.ammunition)
        weapon = Equipment.objects.create(
            character=self.hero,
            item=gun,
            slot=ITEM_WEAPON,
            condition=1.0,
            clip_count=1,
        )
        ammo = Equipment.objects.create(character=self.hero, item=self.ammunition, slot=ITEM_AMMO, quantity=10)
        return weapon, ammo
