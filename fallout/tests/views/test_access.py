# coding: utf-8
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib import messages
from django.test import Client, override_settings
from django.urls import reverse

from fallout.enums import DAMAGE_RAW, ITEM_FOOD, ITEM_MISC, STATUS_HIT_SUCCEED
from fallout.models import (
    Campaign,
    CampaignEffect,
    Character,
    CharacterEffect,
    DamageHistory,
    Effect,
    Equipment,
    FightHistory,
    Item,
    Log,
    Loot,
    LootTemplate,
    Player,
    RollHistory,
)
from fallout.tests.views.base import HtmlViewTests


class CharacterVisibilityTests(HtmlViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.peer = Player.objects.create_user("character-peer")
        cls.admin = Player.objects.create_superuser("character-admin", password=None)
        cls.pc = Character.objects.create(
            name="Other PC", campaign=cls.campaign, player=cls.peer, is_player=True, has_stats=False, max_health=100
        )
        cls.npc = Character.objects.create(
            name="Other NPC", campaign=cls.campaign, is_player=False, has_stats=False, max_health=100
        )
        cls.other_campaign = Campaign.objects.create(name="Other campaign", game_master=cls.other)
        cls.campaignless = Character.objects.create(
            name="Unassigned owner", player=cls.player, is_player=True, has_stats=False, max_health=100
        )

    def character_response(self, character, **kwargs):
        return self.client.get(reverse("fallout:character", args=(character.pk,)), **kwargs)

    def test_outsider_cannot_read_pc_or_npc_even_when_all_visibility_options_are_enabled(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True, view_npc=True)
        Character.objects.filter(pk__in=(self.pc.pk, self.npc.pk)).update(is_visible=True)
        self.client.force_login(self.other)
        for character in (self.pc, self.npc):
            with self.subTest(character=character.name):
                self.assertEqual(self.character_response(character).status_code, 404)

    def test_member_can_read_pc_when_view_pc_is_enabled(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True)
        self.assertEqual(self.character_response(self.pc).status_code, 200)
        self.assertEqual(self.character_response(self.npc).status_code, 404)

    def test_member_can_read_npc_when_view_npc_is_enabled(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_npc=True)
        self.assertEqual(self.character_response(self.npc).status_code, 200)
        self.assertEqual(self.character_response(self.pc).status_code, 404)

    def test_member_cannot_read_hidden_characters(self):
        for character in (self.pc, self.npc):
            with self.subTest(character=character.name):
                self.assertEqual(self.character_response(character).status_code, 404)

    def test_member_can_read_explicitly_visible_characters(self):
        Character.objects.filter(pk__in=(self.pc.pk, self.npc.pk)).update(is_visible=True)
        for character in (self.pc, self.npc):
            with self.subTest(character=character.name):
                self.assertEqual(self.character_response(character).status_code, 200)

    def test_owner_keeps_access_without_campaign_visibility_flags(self):
        self.assertEqual(self.character_response(self.character).status_code, 200)
        self.client.force_login(self.peer)
        self.assertEqual(self.character_response(self.pc).status_code, 200)

    def test_character_without_campaign_renders_without_campaign_link(self):
        response = self.character_response(self.campaignless)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.campaignless.name)
        self.assertNotContains(response, f'href="{reverse("fallout:campaign", args=(self.campaign.pk,))}"')

    def test_game_master_and_superuser_keep_access_to_hidden_characters(self):
        for user in (self.gm, self.admin):
            self.client.force_login(user)
            for character in (self.pc, self.npc):
                with self.subTest(user=user.username, character=character.name):
                    self.assertEqual(self.character_response(character).status_code, 200)

    def test_multiple_owned_characters_do_not_duplicate_the_requested_character(self):
        Character.objects.create(
            name="Second member", campaign=self.campaign, player=self.player, is_player=True, has_stats=False
        )
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True)
        response = self.character_response(self.pc)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["character"].pk, self.pc.pk)
        characters = list(response.context["characters"])
        self.assertEqual(len(characters), len({character.pk for character in characters}))

    def test_inactive_character_remains_inaccessible(self):
        Character.objects.filter(pk=self.pc.pk).update(is_active=False)
        for user in (self.peer, self.gm, self.admin):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                self.assertEqual(self.character_response(self.pc).status_code, 404)

    def test_outsider_cannot_use_visible_character_page_to_add_a_journal_entry(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True)
        self.client.force_login(self.other)
        response = self.client.post(
            reverse("fallout:character", args=(self.pc.pk,)),
            {"type": "log", "method": "add", "text": "Unauthorized note"},
        )
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Log.objects.filter(character=self.pc).exists())


class JournalDeletionTests(HtmlViewTests):
    def setUp(self):
        super().setUp()
        self.note = Log.objects.create(character=self.character, player=self.player, text="Own note")
        self.data = {"type": "log", "method": "delete", "log": self.note.pk}

    def test_get_cannot_delete_even_for_game_master(self):
        for user in (self.player, self.gm):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.character_url, {"delete": self.note.pk})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(Log.objects.filter(pk=self.note.pk).exists())

    def test_author_can_delete_using_post_with_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.player)
        response = client.get(self.character_url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, f"?delete={self.note.pk}")
        self.assertContains(response, 'name="method" value="delete"')
        self.assertContains(response, f'name="log" value="{self.note.pk}"')
        token = client.cookies["csrftoken"].value
        response = client.post(self.character_url, self.data, HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Log.objects.filter(pk=self.note.pk).exists())

    def test_post_without_csrf_token_is_rejected(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.player)
        response = client.post(self.character_url, self.data)
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Log.objects.filter(pk=self.note.pk).exists())

    def test_player_cannot_delete_another_authors_note(self):
        note = Log.objects.create(character=self.character, player=self.other, text="Other author's note")
        response = self.client.post(self.character_url, {**self.data, "log": note.pk})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Log.objects.filter(pk=note.pk).exists())

    def test_game_master_can_delete_another_authors_note(self):
        self.client.force_login(self.gm)
        response = self.client.post(self.character_url, self.data)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Log.objects.filter(pk=self.note.pk).exists())

    def test_deletion_is_scoped_to_displayed_character(self):
        other_character = Character.objects.create(
            name="Other character", campaign=self.campaign, player=self.player, is_player=True, has_stats=False
        )
        note = Log.objects.create(character=other_character, player=self.player, text="Note outside this character")
        response = self.client.post(self.character_url, {**self.data, "log": note.pk})
        self.assertEqual(response.status_code, 404)
        self.assertTrue(Log.objects.filter(pk=note.pk).exists())

    def test_add_and_edit_still_work(self):
        response = self.client.post(self.character_url, {"type": "log", "method": "add", "text": "New note"})
        self.assertEqual(response.status_code, 200)
        note = Log.objects.get(character=self.character, text="New note")
        response = self.client.post(
            self.character_url, {"type": "log", "method": "edit", "log": note.pk, "text": "Edited note"}
        )
        self.assertEqual(response.status_code, 200)
        note.refresh_from_db()
        self.assertEqual(note.text, "Edited note")

    def test_edit_cannot_target_another_authors_note(self):
        note = Log.objects.create(character=self.character, player=self.other, text="Unchanged")
        response = self.client.post(
            self.character_url, {"type": "log", "method": "edit", "log": note.pk, "text": "Changed"}
        )
        self.assertEqual(response.status_code, 404)
        note.refresh_from_db()
        self.assertEqual(note.text, "Unchanged")


@override_settings(IGNORE_LOG=True, NOTIFY_CHANGES=False)
class ScopedMutationTests(HtmlViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.other_campaign = Campaign.objects.create(name="Other campaign", game_master=cls.other, needs=False)
        cls.ally = Character.objects.create(
            name="Ally", campaign=cls.campaign, is_player=True, has_stats=False, max_health=100, luck=5
        )
        cls.outsider = Character.objects.create(
            name="Outsider", campaign=cls.other_campaign, is_player=True, has_stats=False, max_health=100
        )
        cls.item = Item.objects.create(name="Shared item", type=ITEM_MISC)
        cls.own_equipment = cls.item.give(cls.character, quantity=3)
        cls.ally_equipment = cls.item.give(cls.ally, quantity=3)
        cls.other_equipment = cls.item.give(cls.outsider, quantity=3)
        cls.own_loot = Loot.objects.create(campaign=cls.campaign, item=cls.item, quantity=3)
        cls.other_loot = Loot.objects.create(campaign=cls.other_campaign, item=cls.item, quantity=3)
        cls.effect = Effect.objects.create(name="Shared effect")
        cls.own_effect = cls.effect.affect(cls.character, force=True)
        cls.ally_effect = cls.effect.affect(cls.ally, force=True)
        cls.other_effect = cls.effect.affect(cls.outsider, force=True)
        cls.own_campaign_effect = cls.effect.affect(cls.campaign, force=True)
        cls.other_campaign_effect = cls.effect.affect(cls.other_campaign, force=True)
        cls.template = LootTemplate.objects.create(name="Shared loot template", min_money=100, max_money=100)

    def setUp(self):
        super().setUp()
        self.client.force_login(self.gm)
        self.campaign_url = reverse("fallout:campaign", args=(self.campaign.pk,))
        self.dashboard_url = reverse("fallout:dashboard", args=(self.campaign.pk,))

    def assert_rejected_without_changes(self, url, data):
        models = (
            Campaign,
            Character,
            Equipment,
            Loot,
            CharacterEffect,
            CampaignEffect,
            Log,
            DamageHistory,
            FightHistory,
        )
        before = {model: list(model.objects.order_by("pk").values()) for model in models}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)
        for model in models:
            self.assertEqual(list(model.objects.order_by("pk").values()), before[model], model.__name__)

    def test_money_cannot_target_other_campaign_or_missing_character(self):
        for character_id in (self.outsider.pk, 999999):
            with self.subTest(character_id=character_id):
                self.assert_rejected_without_changes(
                    self.campaign_url, {"type": "money", "character-id": character_id, "money": 10}
                )

    def test_money_can_target_character_in_displayed_campaign(self):
        response = self.client.post(self.campaign_url, {"type": "money", "character-id": self.ally.pk, "money": 10})
        self.assertEqual(response.status_code, 200)
        self.ally.refresh_from_db()
        self.assertEqual(self.ally.money, 10)

    def test_scope_is_enforced_even_when_user_manages_both_campaigns(self):
        self.other_campaign.game_master = self.gm
        self.other_campaign.save()
        self.assert_rejected_without_changes(
            self.campaign_url, {"type": "money", "character-id": self.outsider.pk, "money": 10}
        )

    def test_superuser_must_also_use_the_objects_own_page(self):
        admin = Player.objects.create_superuser("view-admin", password=None)
        self.client.force_login(admin)
        self.assert_rejected_without_changes(
            self.character_url, {"type": "item", "method": "drop", "item-id": self.other_equipment.pk, "quantity": 1}
        )

    def test_loot_deletion_cannot_target_other_campaign_or_missing_loot(self):
        for loot_id in (self.other_loot.pk, 999999):
            with self.subTest(loot_id=loot_id):
                self.assert_rejected_without_changes(
                    self.campaign_url, {"type": "loot", "method": f"delete-{loot_id}", f"quantity-{loot_id}": 1}
                )

    def test_loot_transfer_validates_both_loot_and_recipient_before_changes(self):
        for loot_id, character_id in (
            (self.other_loot.pk, self.outsider.pk),
            (self.other_loot.pk, self.character.pk),
            (self.own_loot.pk, self.outsider.pk),
            (self.own_loot.pk, 999999),
            (999999, self.character.pk),
        ):
            with self.subTest(loot_id=loot_id, character_id=character_id):
                self.assert_rejected_without_changes(
                    self.campaign_url,
                    {
                        "type": "loot",
                        "method": f"take-{loot_id}",
                        f"quantity-{loot_id}": 1,
                        "character-id": character_id,
                    },
                )

    def test_loot_deletion_and_transfer_still_work_in_displayed_campaign(self):
        response = self.client.post(
            self.campaign_url,
            {"type": "loot", "method": f"delete-{self.own_loot.pk}", f"quantity-{self.own_loot.pk}": 1},
        )
        self.assertEqual(response.status_code, 200)
        self.own_loot.refresh_from_db()
        self.assertEqual(self.own_loot.quantity, 2)
        response = self.client.post(
            self.campaign_url,
            {
                "type": "loot",
                "method": f"take-{self.own_loot.pk}",
                f"quantity-{self.own_loot.pk}": 1,
                "character-id": self.ally.pk,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.own_loot.refresh_from_db()
        self.ally_equipment.refresh_from_db()
        self.assertEqual(self.own_loot.quantity, 1)
        self.assertEqual(self.ally_equipment.quantity, 4)

    def test_money_loot_cannot_be_transferred_to_another_campaign(self):
        self.campaign.money_loot = 20
        self.campaign.save()
        self.assert_rejected_without_changes(
            self.campaign_url,
            {"type": "loot", "method": "take-money", "character-id": self.outsider.pk, "money": 10},
        )

    def test_money_loot_can_be_transferred_within_campaign(self):
        self.campaign.money_loot = 20
        self.campaign.save()
        response = self.client.post(
            self.campaign_url,
            {"type": "loot", "method": "take-money", "character-id": self.ally.pk, "money": 10},
        )
        self.assertEqual(response.status_code, 200)
        self.campaign.refresh_from_db()
        self.ally.refresh_from_db()
        self.assertEqual((self.campaign.money_loot, self.ally.money), (10, 10))

    def test_opening_loot_template_rejects_outside_recipient(self):
        with patch.object(LootTemplate, "create") as create:
            self.assert_rejected_without_changes(
                self.campaign_url,
                {"type": "loot", "method": "open", "loot-id": self.template.pk, "character-id": self.outsider.pk},
            )
            create.assert_not_called()

    def test_shared_loot_template_accepts_local_recipient(self):
        response = self.client.post(
            self.campaign_url,
            {"type": "loot", "method": "open", "loot-id": self.template.pk, "character-id": self.ally.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.campaign.refresh_from_db()
        self.assertGreater(self.campaign.money_loot, 0, [str(message) for message in response.context["messages"]])

    def test_equipment_actions_reject_other_characters_even_within_same_campaign(self):
        for method in ("equip", "reload", "use", "repair", "drop", "secondary"):
            for equipment_id in (self.ally_equipment.pk, self.other_equipment.pk, 999999):
                with self.subTest(method=method, equipment_id=equipment_id):
                    self.assert_rejected_without_changes(
                        self.character_url, {"type": "item", "method": method, "item-id": equipment_id}
                    )

    def test_own_equipment_can_still_be_dropped(self):
        response = self.client.post(
            self.character_url, {"type": "item", "method": "drop", "item-id": self.own_equipment.pk, "quantity": 1}
        )
        self.assertEqual(response.status_code, 200)
        self.own_equipment.refresh_from_db()
        self.assertEqual(self.own_equipment.quantity, 2)

    def test_campaign_effect_actions_reject_outside_active_effects(self):
        for method, scope, effect_id in (
            ("remove", "character", self.other_effect.pk),
            ("remove", "campaign", self.other_campaign_effect.pk),
            ("enable", "campaign", self.other_campaign_effect.pk),
            ("remove", "character", 999999),
            ("remove", "campaign", 999999),
            ("enable", "campaign", 999999),
        ):
            with self.subTest(method=method, scope=scope, effect_id=effect_id):
                self.assert_rejected_without_changes(
                    self.campaign_url, {"type": "effect", "method": method, "scope": scope, "effect-id": effect_id}
                )

    def test_campaign_page_can_remove_its_own_global_and_character_effects(self):
        for scope, active in (("character", self.ally_effect), ("campaign", self.own_campaign_effect)):
            with self.subTest(scope=scope):
                response = self.client.post(
                    self.campaign_url, {"type": "effect", "method": "remove", "scope": scope, "effect-id": active.pk}
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(type(active).objects.filter(pk=active.pk).exists())

    def test_character_effect_actions_reject_other_characters_and_campaigns(self):
        for method in ("remove", "enable"):
            for active_id in (self.ally_effect.pk, self.other_effect.pk, 999999):
                with self.subTest(method=method, active_id=active_id):
                    self.assert_rejected_without_changes(
                        self.character_url,
                        {"type": "effect", "method": method, "scope": "character", "effect-id": active_id},
                    )
        self.assert_rejected_without_changes(
            self.character_url,
            {"type": "effect", "method": "remove", "scope": "campaign", "effect-id": self.other_campaign_effect.pk},
        )

    def test_character_page_can_remove_own_effect_and_its_campaign_effect(self):
        for scope, active in (("character", self.own_effect), ("campaign", self.own_campaign_effect)):
            with self.subTest(scope=scope):
                response = self.client.post(
                    self.character_url, {"type": "effect", "method": "remove", "scope": scope, "effect-id": active.pk}
                )
                self.assertEqual(response.status_code, 200)
                self.assertFalse(type(active).objects.filter(pk=active.pk).exists())

    def test_enabling_local_effects_still_works(self):
        for url, active in ((self.character_url, self.own_effect), (self.campaign_url, self.own_campaign_effect)):
            with self.subTest(url=url):
                response = self.client.post(url, {"type": "effect", "method": "enable", "effect-id": active.pk})
                self.assertEqual(response.status_code, 200)
                self.assertTrue(type(active).objects.filter(pk=active.pk).exists())

    def test_fight_validates_target_and_failure_target_before_engine_call(self):
        for target_id, fail_id in ((self.outsider.pk, ""), (self.ally.pk, self.outsider.pk), (999999, "")):
            with self.subTest(target_id=target_id, fail_id=fail_id), patch.object(Character, "fight") as fight:
                self.assert_rejected_without_changes(
                    self.character_url,
                    {"type": "fight", "target": target_id, "fail_target": fail_id, "target_range": 1},
                )
                fight.assert_not_called()

    def test_fight_passes_local_target_and_failure_target_to_engine(self):
        result = SimpleNamespace(message_level=messages.SUCCESS, pre_label="Fight", long_label="Success", fail=None)
        with patch.object(Character, "fight", return_value=result) as fight:
            response = self.client.post(
                self.character_url,
                {"type": "fight", "target": self.ally.pk, "fail_target": self.character.pk, "target_range": 1},
            )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(fight.call_args.kwargs["target"].pk, self.ally.pk)
        self.assertEqual(fight.call_args.kwargs["fail_target"].pk, self.character.pk)

    def test_burst_validates_all_targets_before_engine_call(self):
        for targets in ((self.ally.pk, self.outsider.pk), (self.ally.pk, 999999)):
            with self.subTest(targets=targets), patch.object(Character, "burst") as burst:
                self.assert_rejected_without_changes(
                    self.character_url,
                    {"type": "burst", "targets": targets, "ranges": [1, 1], "weapon_type": "primary"},
                )
                burst.assert_not_called()

    def test_burst_passes_local_targets_to_engine(self):
        with patch.object(Character, "burst", return_value=[]) as burst:
            response = self.client.post(
                self.character_url,
                {"type": "burst", "targets": [self.ally.pk], "ranges": [1], "weapon_type": "primary"},
            )
        self.assertEqual(response.status_code, 200)
        target, distance = burst.call_args.kwargs["targets"][0]
        self.assertEqual((target.pk, distance), (self.ally.pk, "1"))

    def test_dashboard_rejects_outside_or_missing_character(self):
        for character_id in (self.outsider.pk, 999999):
            for data in ({"rest": character_id}, {"roll": "strength", "character": character_id}):
                with self.subTest(data=data):
                    self.assert_rejected_without_changes(self.dashboard_url, data)

    def test_dashboard_rest_still_works_for_local_character(self):
        response = self.client.post(self.dashboard_url, {"rest": self.character.pk})
        self.assertEqual(response.status_code, 200)
        self.character.refresh_from_db()
        self.assertTrue(self.character.is_resting)

    def test_npc_duplication_cannot_copy_another_campaigns_character(self):
        with patch.object(Character, "duplicate") as duplicate:
            self.assert_rejected_without_changes(
                self.campaign_url,
                {"type": "npc", "character-id": self.outsider.pk, "campaign-id": self.campaign.pk, "number": 1},
            )
            duplicate.assert_not_called()

    def test_npc_duplication_preserves_local_and_campaignless_templates(self):
        template = Character.objects.create(name="Shared NPC", is_player=False, has_stats=False)
        for source in (self.ally, template):
            with self.subTest(source=source.name):
                before = Character.objects.filter(campaign=self.campaign).count()
                response = self.client.post(
                    self.campaign_url,
                    {"type": "npc", "character-id": source.pk, "campaign-id": self.campaign.pk, "number": 2},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(Character.objects.filter(campaign=self.campaign).count(), before + 2)

    def test_shared_item_and_effect_catalogs_remain_usable(self):
        food = Item.objects.create(name="Shared food", type=ITEM_FOOD)
        response = self.client.post(
            self.character_url, {"type": "item", "method": "add", "item-id": food.pk, "quantity": 2}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Equipment.objects.get(character=self.character, item=food).quantity, 2)
        effect = Effect.objects.create(name="Another shared effect")
        for url in (self.character_url, self.campaign_url):
            response = self.client.post(url, {"type": "effect", "method": "add", "effect-id": effect.pk})
            self.assertEqual(response.status_code, 200)
        self.assertTrue(CharacterEffect.objects.filter(character=self.character, effect=effect).exists())
        self.assertTrue(CampaignEffect.objects.filter(campaign=self.campaign, effect=effect).exists())


class SimulationPermissionTests(HtmlViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.ally = Character.objects.create(
            name="Simulation target", campaign=cls.campaign, is_player=True, has_stats=False, max_health=100
        )
        cls.other_campaign = Campaign.objects.create(name="Other simulation campaign", game_master=cls.other)
        cls.outsider = Character.objects.create(
            name="Other target", campaign=cls.other_campaign, is_player=True, has_stats=False, max_health=100
        )
        cls.admin = Player.objects.create_superuser("simulation-admin", password=None)
        cls.staff = Player.objects.create_user("simulation-staff", is_staff=True)

    def setUp(self):
        super().setUp()
        self.url = reverse("fallout:simulation")
        self.data = {"type": "fight", "character": self.character.pk, "target": self.ally.pk, "target_range": 1}

    def test_anonymous_user_must_log_in(self):
        self.client.logout()
        with patch.object(Character, "fight") as fight:
            response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, 302)
        fight.assert_not_called()

    def test_owner_other_game_master_and_staff_cannot_simulate_this_campaign(self):
        for user in (self.player, self.other, self.staff):
            for mode, method in (("fight", "fight"), ("burst", "burst")):
                with self.subTest(user=user.username, mode=mode), patch.object(Character, method) as engine:
                    self.client.force_login(user)
                    response = self.client.post(
                        self.url, {**self.data, "type": mode, "targets": [self.ally.pk], "ranges": [1]}
                    )
                    self.assertEqual(response.status_code, 404)
                    engine.assert_not_called()

    def test_game_master_and_superuser_can_simulate_a_fight(self):
        result = SimpleNamespace(to_dict=lambda **kwargs: {"description": "Simulated fight"}, fail=None)
        for user in (self.gm, self.admin):
            with self.subTest(user=user.username), patch.object(Character, "fight", return_value=result) as fight:
                self.client.force_login(user)
                response = self.client.post(self.url, {**self.data, "fail_target": self.character.pk})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), {"description": "Simulated fight", "fail": None})
                self.assertTrue(fight.call_args.kwargs["simulation"])
                self.assertEqual(fight.call_args.kwargs["target"].pk, self.ally.pk)
                self.assertEqual(fight.call_args.kwargs["fail_target"].pk, self.character.pk)

    def test_game_master_and_superuser_can_simulate_a_burst(self):
        result = SimpleNamespace(to_dict=lambda **kwargs: {"description": "Simulated burst"})
        for user in (self.gm, self.admin):
            with self.subTest(user=user.username), patch.object(Character, "burst", return_value=[result]) as burst:
                self.client.force_login(user)
                response = self.client.post(
                    self.url,
                    {"type": "burst", "character": self.character.pk, "targets": [self.ally.pk], "ranges": [1]},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json(), [{"description": "Simulated burst"}])
                self.assertTrue(burst.call_args.kwargs["simulation"])
                target, distance = burst.call_args.kwargs["targets"][0]
                self.assertEqual((target.pk, distance), (self.ally.pk, "1"))

    def test_attacker_must_belong_to_game_masters_campaign(self):
        self.client.force_login(self.gm)
        with patch.object(Character, "fight") as fight:
            response = self.client.post(self.url, {**self.data, "character": self.outsider.pk})
        self.assertEqual(response.status_code, 404)
        fight.assert_not_called()

    def test_fight_rejects_outside_and_missing_target_or_failure_target(self):
        self.client.force_login(self.gm)
        for overrides in (
            {"target": self.outsider.pk},
            {"target": 999999},
            {"fail_target": self.outsider.pk},
            {"fail_target": 999999},
        ):
            with self.subTest(overrides=overrides), patch.object(Character, "fight") as fight:
                response = self.client.post(self.url, {**self.data, **overrides})
                self.assertEqual(response.status_code, 404)
                fight.assert_not_called()

    def test_burst_checks_all_targets_and_failure_target_before_simulation(self):
        self.client.force_login(self.gm)
        data = {"type": "burst", "character": self.character.pk, "targets": [self.ally.pk], "ranges": [1, 1]}
        for overrides in (
            {"targets": [self.ally.pk, self.outsider.pk]},
            {"targets": [self.ally.pk, 999999]},
            {"fail_target": self.outsider.pk},
        ):
            with self.subTest(overrides=overrides), patch.object(Character, "burst") as burst:
                response = self.client.post(self.url, {**data, **overrides})
                self.assertEqual(response.status_code, 404)
                burst.assert_not_called()

    def test_superuser_cannot_mix_campaigns_in_a_simulation(self):
        self.client.force_login(self.admin)
        with patch.object(Character, "fight") as fight:
            response = self.client.post(self.url, {**self.data, "target": self.outsider.pk})
        self.assertEqual(response.status_code, 404)
        fight.assert_not_called()

    def test_authorized_real_simulation_returns_result_without_persisting_changes(self):
        self.client.force_login(self.gm)
        before = list(Character.objects.order_by("pk").values())
        response = self.client.post(
            self.url, {**self.data, "weapon_type": "unarmed", "force_success": "on", "force_raw_damage": "on"}
        )
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertIsInstance(result, dict)
        self.assertIn("description", result)
        self.assertEqual(list(Character.objects.order_by("pk").values()), before)
        self.assertFalse(FightHistory.objects.exists())
        self.assertFalse(DamageHistory.objects.exists())


class CampaignRollVisibilityTests(HtmlViewTests):
    @classmethod
    def setUpTestData(cls):
        super().setUpTestData()
        cls.campaign.view_rolls = True
        cls.campaign.save()
        cls.peer = Player.objects.create_user("history-peer")
        cls.external_gm = Player.objects.create_user("history-external-gm")
        cls.admin = Player.objects.create_superuser("history-admin", password=None)
        cls.visible = Character.objects.create(
            name="Visible NPC", campaign=cls.campaign, is_player=False, is_visible=True, has_stats=False
        )
        cls.hidden_pc = Character.objects.create(
            name="Hidden PC", campaign=cls.campaign, player=cls.peer, is_player=True, has_stats=False
        )
        cls.hidden_npc = Character.objects.create(
            name="Hidden NPC", campaign=cls.campaign, is_player=False, has_stats=False
        )
        cls.other_campaign = Campaign.objects.create(
            name="Foreign history", game_master=cls.external_gm, view_pc=True, view_npc=True, view_rolls=True
        )
        cls.foreign = Character.objects.create(
            name="Foreign character", campaign=cls.other_campaign, player=cls.other, is_player=True, has_stats=False
        )
        cls.rolls = {}
        cls.damages = {}
        for character in (cls.character, cls.visible, cls.hidden_pc, cls.hidden_npc, cls.foreign):
            cls.rolls[character.pk] = RollHistory.objects.create(
                character=character, stats="strength", value=5, roll=3, success=True
            )
            cls.damages[character.pk] = DamageHistory.objects.create(
                character=character, damage_type=DAMAGE_RAW, base_damage=5, real_damage=5
            )
        cls.visible_fight = FightHistory.objects.create(
            attacker=cls.character, defender=cls.visible, success=True, status=STATUS_HIT_SUCCEED
        )
        cls.hidden_defender_fight = FightHistory.objects.create(
            attacker=cls.character, defender=cls.hidden_npc, success=True, status=STATUS_HIT_SUCCEED
        )
        cls.hidden_attacker_fight = FightHistory.objects.create(
            attacker=cls.hidden_npc, defender=cls.character, success=True, status=STATUS_HIT_SUCCEED
        )
        cls.foreign_defender_fight = FightHistory.objects.create(
            attacker=cls.character, defender=cls.foreign, success=True, status=STATUS_HIT_SUCCEED
        )

    def setUp(self):
        super().setUp()
        self.url = reverse("fallout:campaign_rolls", args=(self.campaign.pk,))

    def history_for(self, *characters):
        return {entry for character in characters for entry in (self.rolls[character.pk], self.damages[character.pk])}

    def test_player_cannot_bypass_disabled_history_by_calling_endpoint(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_rolls=False)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 404)

    def test_game_master_and_superuser_can_read_hidden_history_when_disabled(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_rolls=False)
        expected = self.history_for(self.character, self.visible, self.hidden_pc, self.hidden_npc) | {
            self.visible_fight,
            self.hidden_defender_fight,
            self.hidden_attacker_fight,
        }
        for user in (self.gm, self.admin):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.url, {"limit": 100})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(set(response.context["rolls"]), expected)

    def test_outsiders_cannot_read_even_when_all_visibility_options_are_enabled(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True, view_npc=True)
        for user in (self.other, self.external_gm):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(self.url)
                self.assertEqual(response.status_code, 404)

    def test_member_cannot_read_another_campaigns_history(self):
        url = reverse("fallout:campaign_rolls", args=(self.other_campaign.pk,))
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_individual_rolls_and_standalone_damage_still_respect_visibility(self):
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["rolls"]),
            self.history_for(self.character, self.visible)
            | {self.visible_fight, self.hidden_defender_fight, self.hidden_attacker_fight},
        )
        self.assertNotContains(response, self.hidden_pc.name)
        self.assertContains(response, self.hidden_npc.name)
        self.assertNotContains(response, self.foreign.name)

    def test_view_pc_reveals_other_players_but_not_hidden_npcs(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_pc=True)
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["rolls"]),
            self.history_for(self.character, self.visible, self.hidden_pc)
            | {self.visible_fight, self.hidden_defender_fight, self.hidden_attacker_fight},
        )

    def test_view_npc_reveals_individual_npc_history(self):
        Campaign.objects.filter(pk=self.campaign.pk).update(view_npc=True)
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.context["rolls"]),
            self.history_for(self.character, self.visible, self.hidden_npc)
            | {self.visible_fight, self.hidden_defender_fight, self.hidden_attacker_fight},
        )

    def test_combats_ignore_participant_visibility_but_remain_within_campaign(self):
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        entries = set(response.context["rolls"])
        self.assertIn(self.visible_fight, entries)
        self.assertIn(self.hidden_defender_fight, entries)
        self.assertIn(self.hidden_attacker_fight, entries)
        self.assertNotIn(self.foreign_defender_fight, entries)

    def test_hidden_player_can_appear_in_combat_without_revealing_individual_rolls(self):
        fight = FightHistory.objects.create(
            attacker=self.character, defender=self.hidden_pc, success=True, status=STATUS_HIT_SUCCEED
        )
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertIn(fight, response.context["rolls"])
        self.assertNotIn(self.rolls[self.hidden_pc.pk], response.context["rolls"])
        self.assertNotIn(self.damages[self.hidden_pc.pk], response.context["rolls"])

    def test_combat_damage_does_not_reappear_as_standalone_damage(self):
        damage = DamageHistory.objects.create(character=self.character, damage_type=DAMAGE_RAW, real_damage=5)
        self.hidden_attacker_fight.damage = damage
        self.hidden_attacker_fight.save()
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(damage, response.context["rolls"])
        self.assertIn(self.hidden_attacker_fight, response.context["rolls"])

    def test_membership_with_multiple_characters_does_not_duplicate_results(self):
        Character.objects.create(
            name="Second owned character", campaign=self.campaign, player=self.player, is_player=True, has_stats=False
        )
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["rolls"]), 7)

    def test_visible_inactive_characters_keep_their_history(self):
        self.visible.is_active = False
        self.visible.save()
        response = self.client.get(self.url, {"limit": 100})
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.rolls[self.visible.pk], response.context["rolls"])
        self.assertIn(self.visible_fight, response.context["rolls"])

    def test_history_remains_sorted_and_limited_after_filtering(self):
        response = self.client.get(self.url, {"limit": 2})
        self.assertEqual(response.status_code, 200)
        expected = sorted(
            self.history_for(self.character, self.visible)
            | {self.visible_fight, self.hidden_defender_fight, self.hidden_attacker_fight},
            key=lambda entry: entry.date,
            reverse=True,
        )[:2]
        self.assertEqual(response.context["rolls"], expected)

    def test_unknown_campaign_returns_404(self):
        self.assertEqual(self.client.get(reverse("fallout:campaign_rolls", args=(999999,))).status_code, 404)
