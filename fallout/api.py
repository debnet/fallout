# coding: utf-8
from common.api.base import SERIALIZERS_BASE
from common.api.serializers import BaseCustomSerializer, CommonModelSerializer
from common.api.utils import (
    create_api, disable_relation_fields, api_view_with_serializer,
    create_model_serializer, to_model_serializer)
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.generics import get_object_or_404

from fallout.enums import BODY_PARTS, DAMAGES_TYPES, LIST_EDITABLE_STATS, ROLL_STATS
from fallout.models import (
    MODELS, Campaign, Character, Equipment, CampaignEffect, CharacterEffect,
    Loot, LootTemplate, DamageHistory, FightHistory, RollHistory)


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
    """
    Serializer d'entrée pour changer le tour des personnages dans une campagne
    """
    seconds = serializers.IntegerField(default=0, initial=0, label=_("secondes"))
    apply = serializers.BooleanField(default=True, initial=True, label=_("valider ?"))
    reset = serializers.BooleanField(default=False, initial=False, label=_("réinitialiser ?"))


@api_view_with_serializer(['POST'], input_serializer=NextTurnInputSerializer, serializer=SimpleCharacterSerializer)
def campaign_next_turn(request, campaign_id):
    """
    API pour changer le tour des personnages
    """
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    return campaign.next_turn(**request.validated_data)


@api_view_with_serializer(['POST'])
def campaign_clear_loot(request, campaign_id):
    """
    API pour supprimer tous les butins de la campagne
    """
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    return campaign.clear_loot()


class RollInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour les jets de compétence
    """
    stats = serializers.ChoiceField(choices=ROLL_STATS, label=_("statistique"))
    modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


class CampaignRollInputSerializer(RollInputSerializer):
    """
    Serializer d'entrée pour les jets de compétence multiples
    """
    GROUPS = (
        (0, _("Tous les personnages")),
        (1, _("Personnages joueurs uniquement")),
        (2, _("Personnages non joueurs uniquement")))
    group = serializers.ChoiceField(choices=GROUPS, label=_("groupe"))
    xp = serializers.BooleanField(default=False, initial=False, label=_("expérience"))


@to_model_serializer(RollHistory)
class RollHistorySerializer(CommonModelSerializer):
    """
    Serializer de sortie pour l'affichage des historiques de jets de compétence
    """
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@api_view_with_serializer(['POST'], input_serializer=CampaignRollInputSerializer, serializer=RollHistorySerializer)
def campaign_roll(request, campaign_id):
    """
    API pour effectuer un jet de compétence l'ensemble des personnages d'une campagne
    """
    group = request.validated_data.pop('group', None)
    filters = dict(campaign_id=campaign_id) if campaign_id else dict(campaign__isnull=True)
    filters.update(is_active=True)
    if group:
        filters.update(is_player=(group == 1))
    return [character.roll(**request.validated_data) for character in Character.objects.filter(**filters)]


@api_view_with_serializer(['POST'], input_serializer=RollInputSerializer, serializer=RollHistorySerializer)
def character_roll(request, character_id):
    """
    API pour effectuer un jet de compétence sur un personnage
    """
    character = get_object_or_404(Character, pk=character_id)
    return character.roll(**request.validated_data)


class BaseFightInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée de base pour les attaques
    """
    target = serializers.PrimaryKeyRelatedField(queryset=Character.objects.order_by('name'), label=_("cible"))
    target_range = serializers.IntegerField(default=1, initial=0, label=_("distance"))

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        character_id = int(getattr(self.context.get('view'), 'kwargs', {}).get('character_id', 0))
        if character_id:
            target_field = self.fields['target']
            target_field.queryset = target_field.queryset.exclude(id=character_id).filter(
                campaign_id=Character.objects.values_list('campaign_id', flat=True).get(id=character_id))


class FightInputSerializer(BaseFightInputSerializer):
    """
    Serializer d'entrée pour les attaques
    """
    target_part = serializers.ChoiceField(choices=BODY_PARTS, allow_blank=True, label=_("partie du corps ciblée"))
    hit_modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


class BurstInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour les attaques en rafales
    """
    targets = BaseFightInputSerializer(many=True, label=_("cibles"))
    hit_modifier = serializers.IntegerField(default=0, initial=0, label=_("modificateur"))


@to_model_serializer(FightHistory)
class FightHistorySerializer(CommonModelSerializer):
    """
    Serializer de sortie pour les attaques
    """
    attacker = SimpleCharacterSerializer(read_only=True, label=_("attaquant"))
    defender = SimpleCharacterSerializer(read_only=True, label=_("défenseur"))
    damage = create_model_serializer(DamageHistory)(read_only=True, label=_("dégâts"))


@api_view_with_serializer(['POST'], input_serializer=FightInputSerializer, serializer=FightHistorySerializer)
def character_fight(request, character_id):
    """
    API permettant d'attaquer un autre personnage
    """
    attacker = get_object_or_404(Character, pk=character_id)
    return attacker.fight(**request.validated_data)


@api_view_with_serializer(['POST'], input_serializer=BurstInputSerializer, serializer=FightHistorySerializer)
def character_burst(request, character_id):
    """
    API permettant d'effectuer une attaque en rafale sur un ou plusieurs personnages
    """
    attacker = get_object_or_404(Character, pk=character_id)
    targets = [(t.get('target'), t.get('target_range')) for t in request.validated_data.get('targets', {})]
    return attacker.burst(targets=targets, hit_modifier=request.validated_data.get('hit_modifier'))


class DamageInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour infliger des dégâts à un seul personnages
    """
    raw_damage = serializers.IntegerField(default=0, initial=0, label=_("dégâts bruts"))
    min_damage = serializers.IntegerField(default=0, initial=0, label=_("dégâts min."))
    max_damage = serializers.IntegerField(default=0, initial=0, label=_("dégâts max."))
    damage_type = serializers.ChoiceField(choices=DAMAGES_TYPES, label=_("type de dégâts"))
    body_part = serializers.ChoiceField(choices=BODY_PARTS, label=_("partie du corps"))
    threshold_modifier = serializers.FloatField(default=1.0, initial=1.0, label=_("modificateur de seuil"))
    resistance_modifier = serializers.FloatField(default=1.0, initial=1.0, label=_("modificateur de resistance"))


class MultiDamageInputSerializer(DamageInputSerializer):
    """
    Serializer d'entrée pour infliger des dégâts à de multiples personnages
    """
    characters = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.order_by('name'), many=True, label=_("personnages"))

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        campaign_id = int(getattr(self.context.get('view'), 'kwargs', {}).get('campaign_id', 0))
        characters_field = self.fields['characters']
        characters_field.child_relation.queryset = \
            characters_field.child_relation.queryset.filter(campaign_id=campaign_id or None)


@to_model_serializer(DamageHistory)
class DamageHistorySerializer(CommonModelSerializer):
    """
    Serializer de sortie des historiques de dégâts
    """
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@api_view_with_serializer(['POST'], input_serializer=MultiDamageInputSerializer, serializer=DamageHistorySerializer)
def campaign_damage(request, campaign_id):
    """
    API permettant d'infliger des dégâts à plusieurs personnages de la campagne
    """
    characters = Character.objects.filter(pk__in=request.validated_data.pop('characters', []))
    return [character.damage(**request.validated_data) for character in characters]


@api_view_with_serializer(['POST'], input_serializer=DamageInputSerializer, serializer=DamageHistorySerializer)
def character_damage(request, character_id):
    """
    API permettant d'infliger des dégâts à un seul personnage
    """
    character = get_object_or_404(Character, pk=character_id)
    return character.damage(**request.validated_data)


@to_model_serializer(Equipment)
class EquipmentSerializer(CommonModelSerializer):
    """
    Serializer de sortie pour afficher des équipements
    """
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@to_model_serializer(CharacterEffect)
class CharacterEffectSerializer(CommonModelSerializer):
    """
    Serializer de sortie pour afficher des effets actifs sur un personnage
    """
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


class ActionInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour toutes les actions
    """
    action = serializers.BooleanField(default=False, initial=False, label=_("action ?"))


@api_view_with_serializer(['POST'], input_serializer=ActionInputSerializer, serializer=EquipmentSerializer)
def equipment_equip(request, equipment_id):
    """
    API permettant de s'équiper ou de déséquiper d'un équipement de l'inventaire
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    return equipment.equip(**request.validated_data)


@api_view_with_serializer(['POST'], input_serializer=ActionInputSerializer, serializer=CharacterEffectSerializer)
def equipment_use(request, equipment_id):
    """
    API permettant d'utiliser un objet (si applicable)
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    return equipment.use(**request.validated_data)


@api_view_with_serializer(['POST'], input_serializer=ActionInputSerializer, serializer=EquipmentSerializer)
def equipment_reload(request, equipment_id):
    """
    API permettant de recharger une arme à feu (si applicable)
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    return equipment.reload(**request.validated_data)


class ActionWithQuantityInputSerializer(ActionInputSerializer):
    """
    Serializer d'entrée pour effectuer une action impliquant une quantité
    """
    quantity = serializers.IntegerField(default=1, initial=1, label=_("quantité"))


@to_model_serializer(Loot)
class LootSerializer(CommonModelSerializer):
    """
    Serializer des butins
    """
    pass


@api_view_with_serializer(['POST'], input_serializer=ActionWithQuantityInputSerializer, serializer=LootSerializer)
def equipment_drop(request, equipment_id):
    """
    API permettant de séparer d'un équipement et d'en faire un butin
    """
    equipment = get_object_or_404(Equipment, pk=equipment_id)
    return equipment.drop(**request.validated_data)


class LootTakeInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour ramasser un butin
    """
    character = serializers.PrimaryKeyRelatedField(queryset=Character.objects.order_by('name'), label=_("personnage"))
    count = serializers.IntegerField(default=1, initial=1, label=_("nombre"))

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        loot_id = int(getattr(self.context.get('view'), 'kwargs', {}).get('loot_id', 0))
        if loot_id:
            character_field = self.fields['character']
            character_field.queryset = character_field.queryset.filter(campaign__loots=loot_id)


@api_view_with_serializer(['POST'], input_serializer=LootTakeInputSerializer, serializer=EquipmentSerializer)
def loot_take(request, loot_id):
    """
    API permettant de ramasser un butin
    """
    loot = get_object_or_404(Loot, pk=loot_id)
    return loot.take(**request.validated_data)


class LootTemplateOpenInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour l'ouverture des butins
    """
    campaign = serializers.PrimaryKeyRelatedField(queryset=Campaign.objects.order_by('name'), label=_("campagne"))
    character = serializers.PrimaryKeyRelatedField(
        allow_empty=True, allow_null=True, queryset=Character.objects.order_by('name'), label=_("personnage"))


@api_view_with_serializer(['POST'], input_serializer=LootTemplateOpenInputSerializer, serializer=LootSerializer)
def loottemplate_open(request, template_id):
    """
    API permettant d'ouvrir un butin dans une campagne
    """
    loot_template = get_object_or_404(LootTemplate, pk=template_id)
    return loot_template.create(**request.validated_data)

