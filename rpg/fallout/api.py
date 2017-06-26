# coding: utf-8
from common.api.base import SERIALIZERS_BASE
from common.api.serializers import BaseCustomSerializer, CommonModelSerializer
from common.api.utils import (
    create_api, disable_relation_fields, api_view_with_serializer,
    create_model_serializer, to_model_serializer)
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from rpg.fallout.enums import BODY_PARTS, DAMAGES_TYPES, LIST_EDITABLE_STATS, ROLL_STATS
from rpg.fallout.models import MODELS, Campaign, Character, DamageHistory, FightHistory, RollHistory


# Affichage des statistiques calculées sur le personnage
characters_attributes = {}
for stats in LIST_EDITABLE_STATS:
    characters_attributes[stats] = serializers.SerializerMethodField()
    characters_attributes['get_' + stats] = lambda self, obj, stats=stats: getattr(obj, '_' + stats)
CharacterSerializer = create_model_serializer(Character, attributes=characters_attributes)
SERIALIZERS_BASE.update({Character: (CharacterSerializer, )})

# Serializer sans statistiques pour le personnage
SimpleCharacterSerializer = create_model_serializer(Character, exclude=LIST_EDITABLE_STATS)

# Désactive les listes déroulantes sur les champs de relations
disable_relation_fields(*MODELS)

# Création des APIs REST standard pour les modèles de cette application
router, all_serializers, all_viewsets = create_api(*MODELS)


class NextTurnInputSerializer(BaseCustomSerializer):
    seconds = serializers.IntegerField(default=0, initial=0, label=_("secondes"))
    apply = serializers.BooleanField(default=True, initial=True, label=_("valider ?"))


@api_view_with_serializer(['POST'], input_serializer=NextTurnInputSerializer, serializer=SimpleCharacterSerializer)
def campaign_next_turn(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    return campaign.next_turn(**request.validated_data)


@api_view_with_serializer(['POST'])
def campaign_clear_loot(request, campaign_id):
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    return campaign.clear_loot()


class RollInputSerializer(BaseCustomSerializer):
    stats = serializers.ChoiceField(choices=ROLL_STATS, label=_("statistique"))
    modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


@to_model_serializer(RollHistory)
class RollHistorySerializer(CommonModelSerializer):
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@api_view_with_serializer(['POST'], input_serializer=RollInputSerializer, serializer=RollHistorySerializer)
def campaign_roll(request, campaign_id):
    filters = dict(campaign_id=campaign_id) if campaign_id else dict(campaign__isnull=True)
    return [character.roll(**request.validated_data) for character in Character.objects.filter(**filters)]


@api_view_with_serializer(['POST'], input_serializer=RollInputSerializer, serializer=RollHistorySerializer)
def character_roll(request, character_id):
    character = get_object_or_404(Character, pk=character_id)
    return character.roll(**request.validated_data)


class BaseFightInputSerializer(BaseCustomSerializer):
    target = serializers.PrimaryKeyRelatedField(queryset=Character.objects.order_by('name'), label=_("cible"))
    target_range = serializers.IntegerField(default=1, initial=0, label=_("distance"))


class FightInputSerializer(BaseFightInputSerializer):
    target_part = serializers.ChoiceField(choices=BODY_PARTS, allow_blank=True, label=_("partie du corps ciblée"))
    hit_modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        character_id = getattr(self.context.get('view'), 'kwargs', {}).get('character_id')
        if character_id:
            defender_field = self.fields['defender']
            defender_field.queryset = defender_field.queryset.exclude(id=character_id).filter(
                campaign_id=Character.objects.values_list('campaign_id', flat=True).get(id=character_id))


class BurstInputSerializer(BaseCustomSerializer):
    targets = BaseFightInputSerializer(many=True, label=_("cibles"))
    hit_modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


@to_model_serializer(FightHistory)
class FightHistorySerializer(CommonModelSerializer):
    attacker = SimpleCharacterSerializer(read_only=True, label=_("attaquant"))
    defender = SimpleCharacterSerializer(read_only=True, label=_("défenseur"))
    damage = create_model_serializer(DamageHistory)(read_only=True, label=_("dégâts"))


@api_view_with_serializer(['POST'], input_serializer=FightInputSerializer, serializer=FightHistorySerializer)
def character_fight(request, character_id):
    attacker = get_object_or_404(Character, pk=character_id)
    return attacker.fight(**request.validated_data)


@api_view_with_serializer(['POST'], input_serializer=BurstInputSerializer, serializer=FightHistorySerializer)
def character_burst(request, character_id):
    attacker = get_object_or_404(Character, pk=character_id)
    targets = [(t.get('target'), t.get('target_range')) for t in request.validated_data.get('targets', {})]
    return attacker.burst(targets=targets, hit_modifier=request.validated_data.get('hit_modifier'))


class DamageInputSerializer(BaseCustomSerializer):
    raw_damage = serializers.IntegerField(default=0, initial=0, label=_("dégâts bruts"))
    dice_count = serializers.IntegerField(default=0, initial=0, label=_("nombre de dés"))
    dice_value = serializers.IntegerField(default=0, initial=0, label=_("valeur de dé"))
    damage_type = serializers.ChoiceField(choices=DAMAGES_TYPES, label=_("type de dégâts"))
    threshold_modifier = serializers.FloatField(default=1.0, initial=1.0, label=_("modificateur de seuil"))
    resistance_modifier = serializers.FloatField(default=1.0, initial=1.0, label=_("modificateur de resistance"))


@to_model_serializer(DamageHistory)
class DamageHistorySerializer(CommonModelSerializer):
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@api_view_with_serializer(['POST'], input_serializer=DamageInputSerializer, serializer=DamageHistorySerializer)
def character_damage(request, character_id):
    character = get_object_or_404(Character, pk=character_id)
    return character.damage(**request.validated_data)
