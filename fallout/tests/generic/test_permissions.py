# coding: utf-8
from django.contrib.auth.models import Permission

from fallout import api
from fallout.models import Character, Log, Player
from fallout.tests.api.base import ApiTestCase


class CrudPermissionTests(ApiTestCase):
    def test_crud_requires_model_permission_to_read(self):
        response = self.crud(Character, url="/?fields=id&all=true")
        self.assertEqual(response.status_code, 403)

    def test_crud_keeps_the_native_unfiltered_queryset(self):
        self.player.user_permissions.add(Permission.objects.get(codename="view_character"))
        response = self.crud(Character, url="/?fields=id")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            {row["id"] for row in response.data["results"]}, set(Character.objects.values_list("pk", flat=True))
        )

    def test_unpaginated_results_require_administrator_even_with_model_permission(self):
        self.player.user_permissions.add(Permission.objects.get(codename="view_character"))
        response = self.crud(Character, url="/?fields=id&all=true")
        self.assertEqual(response.status_code, 403)

    def test_anonymous_cannot_read(self):
        view = api.all_viewsets[Character].as_view({"get": "list"})
        self.assertEqual(view(self.request()).status_code, 401)

    def test_crud_write_uses_native_model_permission(self):
        self.player.user_permissions.add(Permission.objects.get(codename="change_character"))
        response = self.crud(Character, "partial_update", "patch", data={"money": 100}, pk=self.hero.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.money, 100)

    def test_crud_aggregation_keeps_the_native_queryset(self):
        self.gm.user_permissions.add(Permission.objects.get(codename="view_character"))
        response = self.crud(Character, user=self.gm, url="/?count=id")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"count__id": Character.objects.count()})

    def test_common_query_options_are_preserved(self):
        self.gm.user_permissions.add(
            Permission.objects.get(codename="view_character"),
            Permission.objects.get(codename="view_campaign"),
        )
        response = self.crud(Character, user=self.gm, url="/?min=campaign.name")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, {"min__campaign__name": "A"})
        response = self.crud(Character, user=self.gm, url="/?count=id|total")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(response.data, {"total": Character.objects.count()})

    def test_aggregate_requires_permission_on_related_model(self):
        self.gm.user_permissions.add(Permission.objects.get(codename="view_character"))
        response = self.crud(Character, user=self.gm, url="/?min=campaign.name")
        self.assertEqual(response.status_code, 403, response.data)
        self.assertIn("view_campaign", response.data)

    def test_player_cannot_aggregate_game_master_password_even_when_silent(self):
        self.player.user_permissions.add(
            Permission.objects.get(codename="view_character"),
            Permission.objects.get(codename="view_campaign"),
        )
        for silent in ("false", "true"):
            with self.subTest(silent=silent):
                response = self.crud(Character, url=f"/?min=campaign.game_master.password&silent={silent}")
                self.assertEqual(response.status_code, 403, response.data)
                self.assertIn("view_player", response.data)

    def test_common_viewsets_are_not_overridden(self):
        from common.api.base import router
        from common.api.viewsets import CommonModelViewSet

        for prefix, viewset, _ in router.registry:
            with self.subTest(model=prefix):
                self.assertIs(viewset.get_queryset, CommonModelViewSet.get_queryset)
        for model, viewset in api.all_viewsets.items():
            with self.subTest(model=model.__name__):
                self.assertIs(viewset.get_queryset, CommonModelViewSet.get_queryset)
                self.assertIs(viewset.create, CommonModelViewSet.create)
                self.assertIs(viewset.update, CommonModelViewSet.update)
                self.assertIs(viewset.destroy, CommonModelViewSet.destroy)

    def test_plain_own_account_update_remains_available(self):
        response = self.crud(Player, "partial_update", "patch", data={"nickname": "Vault dweller"}, pk=self.player.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.player.refresh_from_db()
        self.assertEqual(self.player.nickname, "Vault dweller")

    def test_safe_filters_and_aggregates_still_work(self):
        self.player.user_permissions.add(Permission.objects.get(codename="view_character"))
        response = self.crud(Character, url="/?fields=id&is_player=True")
        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual({row["id"] for row in response.data["results"]}, {self.hero.pk, self.ally.pk})

    def test_master_still_needs_model_permission_to_write(self):
        response = self.crud(Character, "partial_update", "patch", user=self.gm, data={"money": 12}, pk=self.hero.pk)
        self.assertEqual(response.status_code, 403)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.money, 0)

    def test_crud_does_not_add_campaign_restrictions_to_model_permissions(self):
        self.gm.user_permissions.add(Permission.objects.get(codename="change_character"))
        response = self.crud(Character, "partial_update", "patch", user=self.gm, data={"money": 12}, pk=self.hero.pk)
        self.assertEqual(response.status_code, 200, response.data)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.money, 12)
        response = self.crud(
            Character, "partial_update", "patch", user=self.gm, data={"money": 12}, pk=self.stranger.pk
        )
        self.assertEqual(response.status_code, 200, response.data)

    def test_journal_crud_has_no_special_permission_exception(self):
        self.assertEqual(self.crud(Log).status_code, 403)
        self.assertEqual(
            self.crud(
                Log,
                "create",
                "post",
                data={
                    "character": self.hero.pk,
                    "text": "new",
                },
            ).status_code,
            403,
        )
        self.assertEqual(
            self.crud(Log, "partial_update", "patch", data={"text": "edited"}, pk=self.note.pk).status_code, 403
        )
        self.assertEqual(self.crud(Log, "destroy", "delete", pk=self.note.pk).status_code, 403)
