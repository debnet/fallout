# coding: utf-8
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from fallout import api
from fallout.models import Campaign, Character, Log, Player


class ApiTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.gm = Player.objects.create_user("gm")
        cls.other_gm = Player.objects.create_user("other-gm")
        cls.player = Player.objects.create_user("player")
        cls.other_player = Player.objects.create_user("other-player")
        cls.a = Campaign.objects.create(name="A", game_master=cls.gm)
        cls.b = Campaign.objects.create(name="B", game_master=cls.other_gm)
        cls.hero = Character.objects.create(name="Hero", campaign=cls.a, player=cls.player, is_player=True)
        cls.ally = Character.objects.create(name="Ally", campaign=cls.a, is_player=True, is_visible=True)
        cls.hidden = Character.objects.create(name="Hidden", campaign=cls.a)
        cls.stranger = Character.objects.create(name="Stranger", campaign=cls.b, player=cls.other_player)
        cls.template = Character.objects.create(name="Template")
        cls.note = Log.objects.create(character=cls.hero, player=cls.player, text="own")
        cls.private = Log.objects.create(character=cls.hero, player=cls.gm, private=True, text="MJ")
        cls.secret = Log.objects.create(character=cls.stranger, player=cls.other_player, text="B")

    def request(self, method="get", user=None, data=None, url="/"):
        request = getattr(APIRequestFactory(), method)(url, data or {}, format="json")
        if user:
            force_authenticate(request, user=user)
        return request

    def crud(self, model, action="list", method="get", user=None, data=None, pk=None, url="/"):
        view = api.all_viewsets[model].as_view({method: action})
        return view(self.request(method, user or self.player, data, url), **({"pk": pk} if pk else {}))
