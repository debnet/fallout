# coding: utf-8
from common.api.serializers import BaseCustomSerializer, CommonModelSerializer
from common.api.utils import (
    create_api, disable_relation_fields, api_view_with_serializer,
    create_model_serializer, to_model_serializer)
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from rpg.fallout.enums import BODY_PARTS, LIST_EDITABLE_STATS, ROLL_STATS
from rpg.fallout.models import MODELS, Campaign, Character, FightHistory, RollHistory


# Désactive les listes déroulantes sur les champs de relations
disable_relation_fields(*MODELS)

# Création des APIs REST standard pour les modèles de cette application
router, all_serializers, all_viewsets = create_api(*MODELS)

# Affichage des statistiques calculées sur le personnage
characters_attributes = {}
for stats in LIST_EDITABLE_STATS:
    characters_attributes[stats] = serializers.SerializerMethodField()
    characters_attributes['get_' + stats] = lambda self, obj, stats=stats: getattr(obj, '_' + stats)
all_serializers[Character] = create_model_serializer(Character, attributes=characters_attributes)

# Serializer sans statistiques pour le personnage
BasicCharacterSerializer = create_model_serializer(Character, exclude=LIST_EDITABLE_STATS)


class RollInputSerializer(BaseCustomSerializer):
    stats = serializers.ChoiceField(choices=ROLL_STATS, label=_("statistique"))
    modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


@to_model_serializer(RollHistory)
class RollHistorySerializer(CommonModelSerializer):
    character = all_serializers[Character](read_only=True)


@api_view_with_serializer(['POST'], input_serializer=RollInputSerializer, serializer=RollHistorySerializer)
def campaign_roll(request, campaign_id):
    filters = dict(campaign_id=campaign_id) if campaign_id else dict(campaign__isnull=True)
    return [character.roll(**request.validated_data) for character in Character.objects.filter(**filters)]


@api_view_with_serializer(['POST'], input_serializer=RollInputSerializer, serializer=RollHistorySerializer)
def character_roll(request, character_id):
    character = get_object_or_404(Character, pk=character_id)
    return character.roll(**request.validated_data)


class FightInputSerializer(BaseCustomSerializer):
    defender = serializers.PrimaryKeyRelatedField(queryset=Character.objects.order_by('name'), label=_("défenseur"))
    target_part = serializers.ChoiceField(choices=BODY_PARTS, allow_blank=True, label=_("cible"))
    target_range = serializers.IntegerField(default=1, initial=0, label=_("distance"))
    hit_modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        character_id = getattr(self.context.get('view'), 'kwargs', {}).get('character_id')
        if character_id:
            defender_field = self.fields['defender']
            defender_field.queryset = defender_field.queryset.exclude(id=character_id).filter(
                campaign_id=Character.objects.values_list('campaign_id', flat=True).get(id=character_id))


@to_model_serializer(FightHistory)
class FightHistorySerializer(CommonModelSerializer):
    attacker = all_serializers[Character](read_only=True)
    defender = all_serializers[Character](read_only=True)


@api_view_with_serializer(['POST'], input_serializer=FightInputSerializer, serializer=FightHistorySerializer)
def character_fight(request, character_id):
    attacker = get_object_or_404(Character, pk=character_id)
    return attacker.fight(**request.validated_data)
