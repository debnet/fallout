# coding: utf-8
from common.api.serializers import BaseCustomSerializer
from common.api.utils import create_api, disable_relation_fields, api_view_with_serializer
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from rpg.fallout.enums import ROLL_STATS
from rpg.fallout.models import MODELS, Character, RollHistory


# Désactive les listes déroulantes sur les champs de relations
disable_relation_fields(*MODELS)

# Création des APIs REST standard pour les modèles de cette application
router, all_serializers, all_viewsets = create_api(*MODELS)


class RollSerializer(BaseCustomSerializer):
    stats = serializers.ChoiceField(choices=ROLL_STATS, label=_("statistique"))
    modifier = serializers.IntegerField(default=0, label=_("modificateur"))


RollHistorySerializer = all_serializers.get(RollHistory)


@api_view_with_serializer(['POST'], input_serializer=RollSerializer, serializer=RollHistorySerializer)
def multi_roll(request, campaign_id):
    return [character.roll(**request.validated_data) for character in Character.objects.filter(campaign_id=campaign_id)]


@api_view_with_serializer(['POST'], input_serializer=RollSerializer, serializer=RollHistorySerializer)
def roll(request, character_id):
    character_id = get_object_or_404(Character, pk=character_id)
    return character_id.roll(**request.validated_data)

