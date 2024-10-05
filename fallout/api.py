# coding: utf-8
from common.api.serializers import BaseCustomSerializer, CommonModelSerializer
from common.api.utils import (
    api_view_with_serializer,
    create_api,
    create_model_serializer,
    disable_relation_fields,
    to_model_serializer,
)
from django.urls import path
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404

from fallout.enums import *  # noqa
from fallout.models import *  # noqa

# Désactive les listes déroulantes sur les champs de relations
disable_relation_fields(*MODELS)

# Création des APIs REST standard pour les modèles de cette application
router, all_serializers, all_viewsets = create_api(*MODELS)

# Serializer sans statistiques pour le personnage
BaseCharacterSerializer = create_model_serializer(Character, exclude=tuple(LIST_EDITABLE_STATS))


class SimpleCharacterSerializer(BaseCharacterSerializer):
    """
    Serializer simplifié pour les personnages
    """

    current_charge = serializers.FloatField()
    used_skill_points = serializers.FloatField()
    next_required_experience = serializers.IntegerField()
    previous_required_experience = serializers.IntegerField()
    required_experience = serializers.IntegerField()
    labels = serializers.DictField()


def is_authorized(request, campaign):
    """
    Vérifie que l'utilisateur courant peut utiliser l'API
    :param request: Request
    :param campaign: Campagne
    :return: Rien
    """
    authorized = request.user and (
        request.user.is_superuser or (campaign and campaign.game_master_id == request.user.id)
    )
    if not authorized:
        raise PermissionDenied()
    return authorized


class RecursiveField(serializers.Serializer):
    """
    Serializer permettant d'utiliser le serializer parent en tant que champ
    """

    def to_representation(self, value):
        serializer = self.parent.__class__(value, context=self.context)
        return serializer.data


@api_view_with_serializer(["POST"])
def campaign_clear_loot(request, campaign_id):
    """
    API pour supprimer tous les butins de la campagne
    """
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    is_authorized(request, campaign)
    try:
        return campaign.clear_loot()
    except Exception as exception:
        raise ValidationError(str(exception))


class RollInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour les jets de compétence
    """

    stats = serializers.ChoiceField(choices=ROLL_STATS, label=_("statistique"))
    modifier = serializers.IntegerField(initial=0, required=False, label=_("modificateur"))
    xp = serializers.BooleanField(initial=True, required=False, label=_("expérience"))


class CampaignRollInputSerializer(RollInputSerializer):
    """
    Serializer d'entrée pour les jets de compétence multiples
    """

    GROUPS = (
        (0, _("Tous les personnages")),
        (1, _("Personnages joueurs uniquement")),
        (2, _("Personnages non joueurs uniquement")),
    )
    group = serializers.ChoiceField(choices=GROUPS, label=_("groupe"))


class HistorySerializer(CommonModelSerializer):
    """
    Serializer permettant d'afficher les éventuels labels d'un historique
    """

    label = serializers.SerializerMethodField()
    long_label = serializers.SerializerMethodField()

    def get_label(self, obj):
        return getattr(obj, "label", None)

    def get_long_label(self, obj):
        return getattr(obj, "long_label", None)


@to_model_serializer(RollHistory)
class RollHistorySerializer(HistorySerializer):
    """
    Serializer de sortie pour l'affichage des historiques de jets de compétence
    """

    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=CampaignRollInputSerializer,
    serializer=RollHistorySerializer,
)
def campaign_roll(request, campaign_id):
    """
    API pour effectuer un jet de compétence l'ensemble des personnages d'une campagne
    """
    group = request.validated_data.pop("group", None)
    filters = dict(campaign_id=campaign_id) if campaign_id else dict(campaign__isnull=True)
    filters.update(is_active=True)
    if group:
        filters.update(is_player=(group == 1))
    characters = Character.objects.select_related("campaign", "statistics").filter(**filters)
    any(is_authorized(request, character.campaign) for character in characters)
    try:
        return [character.roll(**request.validated_data) for character in characters]
    except Exception as exception:
        raise ValidationError(str(exception))


class EffectAffectInputSerializer(BaseCustomSerializer):
    """
    Sérializer d'entrée pour l'affectation d'un effet
    """

    effect = serializers.PrimaryKeyRelatedField(queryset=Effect.objects.order_by("name"), label=_("effet"))


@to_model_serializer(CampaignEffect)
class CampaignEffectSerializer(CommonModelSerializer):
    """
    Serializer des butins
    """

    campaign = create_model_serializer(Campaign)(read_only=True, label=_("campagne"))
    effect = create_model_serializer(Effect)(read_only=True, label=_("effet"))
    damages = create_model_serializer(DamageHistory)(read_only=True, many=True, label=_("dégâts"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=EffectAffectInputSerializer,
    serializer=CampaignEffectSerializer,
)
def campaign_effect(request, campaign_id):
    """
    API permettant d'affecter un effet à une campagne
    """
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    is_authorized(request, campaign)
    effect = request.validated_data.get("effect")
    try:
        return effect.affect(campaign)
    except Exception as exception:
        raise ValidationError(str(exception))


class ExperienceInputSerializer(BaseCustomSerializer):
    """
    Serializer pour l'ajout d'expérience à un personnage
    """

    amount = serializers.IntegerField(default=0, label=_("quantité"))


class ExperienceSerializer(SimpleCharacterSerializer):
    """
    Serializer de l'expérience acquise d'un personnage
    """

    level_up = serializers.BooleanField()


@api_view_with_serializer(
    ["POST"],
    input_serializer=ExperienceInputSerializer,
    serializer=ExperienceSerializer,
)
def character_xp(request, character_id):
    """
    API pour augmenter l'expérience d'un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        level, required_xp, character.level_up = character.add_experience(**request.validated_data)
        return character
    except Exception as exception:
        raise ValidationError(str(exception))


@api_view_with_serializer(
    ["POST"],
    input_serializer=RollInputSerializer,
    serializer=RollHistorySerializer,
)
def character_roll(request, character_id):
    """
    API pour effectuer un jet de compétence sur un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        return character.roll(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class BaseFightInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée de base pour les attaques
    """

    target = serializers.PrimaryKeyRelatedField(queryset=Character.objects.order_by("name"), label=_("cible"))
    target_range = serializers.IntegerField(initial=1, required=False, label=_("distance"))

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        character_id = int(getattr(self.context.get("view"), "kwargs", {}).get("character_id", 0))
        if character_id:
            target_field = self.fields["target"]
            target_field.queryset = target_field.queryset.exclude(id=character_id).filter(
                campaign_id=Character.objects.values_list("campaign_id", flat=True).get(id=character_id)
            )


class FightInputSerializer(BaseFightInputSerializer):
    """
    Serializer d'entrée pour les attaques
    """

    target_part = serializers.ChoiceField(
        choices=BODY_PARTS,
        allow_blank=True,
        required=False,
        label=_("partie du corps"),
    )
    fail_target = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.order_by("name"),
        required=False,
        label=_("cible d'échec"),
    )
    hit_chance_modifier = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("modificateur"),
    )
    force_success = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("succès ?"),
    )
    force_critical = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("critique ?"),
    )
    force_raw_damage = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("dégâts bruts ?"),
    )
    is_action = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("action ?"),
    )
    weapon_type = serializers.ChoiceField(
        initial="primary",
        choices=WEAPON_TYPES,
        required=False,
        label=_("type d'arme"),
    )
    simulation = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("simulation ?"),
    )


class BurstInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour les attaques en rafales
    """

    targets = BaseFightInputSerializer(
        many=True,
        required=False,
        label=_("cibles"),
    )
    hit_chance_modifier = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("modificateur"),
    )
    force_success = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("succès ?"),
    )
    force_critical = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("critique ?"),
    )
    force_raw_damage = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("dégâts bruts ?"),
    )
    is_action = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("action ?"),
    )
    weapon_type = serializers.ChoiceField(
        initial="primary",
        choices=WEAPON_TYPES,
        required=False,
        label=_("type d'arme"),
    )
    simulation = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("simulation ?"),
    )


@to_model_serializer(FightHistory)
class FightHistorySerializer(HistorySerializer):
    """
    Serializer de sortie pour les attaques
    """

    attacker = SimpleCharacterSerializer(read_only=True, label=_("attaquant"))
    defender = SimpleCharacterSerializer(read_only=True, label=_("défenseur"))
    damage = create_model_serializer(DamageHistory)(read_only=True, label=_("dégâts"))
    fail = RecursiveField(read_only=True)


@api_view_with_serializer(
    ["POST"],
    input_serializer=FightInputSerializer,
    serializer=FightHistorySerializer,
)
def character_fight(request, character_id):
    """
    API permettant d'attaquer un autre personnage
    """
    attacker = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, attacker.campaign)
    try:
        return attacker.fight(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


@api_view_with_serializer(
    ["POST"],
    input_serializer=BurstInputSerializer,
    serializer=FightHistorySerializer,
)
def character_burst(request, character_id):
    """
    API permettant d'effectuer une attaque en rafale sur un ou plusieurs personnages
    """
    attacker = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, attacker.campaign)
    targets = [(t.get("target"), t.get("target_range")) for t in request.validated_data.pop("targets", {})]
    try:
        return attacker.burst(targets=targets, **request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class DamageInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour infliger des dégâts à un seul personnage
    """

    raw_damage = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("dégâts bruts"),
    )
    min_damage = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("dégâts min."),
    )
    max_damage = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("dégâts max."),
    )
    damage_type = serializers.ChoiceField(
        choices=DAMAGES_TYPES,
        required=False,
        label=_("type de dégâts"),
    )
    body_part = serializers.ChoiceField(
        choices=BODY_PARTS,
        allow_blank=True,
        allow_null=True,
        required=False,
        label=_("partie du corps"),
    )
    threshold_modifier = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("modificateur d'absorption"),
    )
    threshold_rate_modifier = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("modificateur taux d'absorption"),
    )
    resistance_modifier = serializers.IntegerField(
        initial=0,
        required=False,
        label=_("modificateur de résistance"),
    )
    simulation = serializers.BooleanField(
        initial=False,
        required=False,
        label=_("simulation ?"),
    )


class MultiDamageInputSerializer(DamageInputSerializer):
    """
    Serializer d'entrée pour infliger des dégâts à de multiples personnages
    """

    characters = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.order_by("name"),
        many=True,
        label=_("personnages"),
    )

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        campaign_id = int(getattr(self.context.get("view"), "kwargs", {}).get("campaign_id", 0))
        characters_field = self.fields["characters"]
        characters_field.child_relation.queryset = characters_field.child_relation.queryset.filter(
            campaign_id=campaign_id or None
        )


@to_model_serializer(DamageHistory)
class DamageHistorySerializer(HistorySerializer):
    """
    Serializer de sortie des historiques de dégâts
    """

    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))
    icon = serializers.ReadOnlyField()
    is_heal = serializers.ReadOnlyField()


@api_view_with_serializer(
    ["POST"],
    input_serializer=MultiDamageInputSerializer,
    serializer=DamageHistorySerializer,
)
def campaign_damage(request, campaign_id):
    """
    API permettant d'infliger des dégâts à plusieurs personnages de la campagne
    """
    characters = Character.objects.select_related("campaign", "statistics").filter(
        pk__in=request.validated_data.pop("characters", [])
    )
    any(is_authorized(request, character.campaign) for character in characters)
    try:
        return [character.damage(**request.validated_data) for character in characters]
    except Exception as exception:
        raise ValidationError(str(exception))


@api_view_with_serializer(
    ["POST"],
    input_serializer=DamageInputSerializer,
    serializer=DamageHistorySerializer,
)
def character_damage(request, character_id):
    """
    API permettant d'infliger des dégâts à un seul personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        return character.damage(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class CharacterCopyInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour la copie de personnages
    """

    campaign = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.order_by("name"),
        label=_("campagne"),
    )
    name = serializers.CharField(
        allow_blank=True,
        required=False,
        label=_("nom"),
    )
    count = serializers.IntegerField(
        initial=1,
        required=False,
        label=_("nombre"),
    )
    equipments = serializers.BooleanField(
        initial=True,
        required=False,
        label=_("équipements ?"),
    )
    effects = serializers.BooleanField(
        initial=True,
        required=False,
        label=_("effets ?"),
    )
    is_active = serializers.BooleanField(
        initial=True,
        required=False,
        label=_("actif ?"),
    )


@api_view_with_serializer(
    ["POST"],
    input_serializer=CharacterCopyInputSerializer,
    serializer=SimpleCharacterSerializer,
)
def character_copy(request, character_id):
    """
    API permettant de copier un personnage dans une campagne
    """
    character = get_object_or_404(Character, pk=character_id)
    is_authorized(request, request.validated_data.get("campaign"))
    name, count = request.validated_data.pop("name"), request.validated_data.pop("count")
    try:
        character_name = character.name
        characters = []
        for nb in range(count):
            new_name = f"{name or character_name} {nb + 1}" if count > 1 else name
            characters.append(character.duplicate(name=new_name, **request.validated_data))
            if count > 1:  # Recharge le personnage d'origine
                character = Character.objects.get(pk=character_id)
        return characters
    except Exception as exception:
        raise ValidationError(str(exception))


class CharacterRandomizeSpecialSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour la génération aléatoire du S.P.E.C.I.A.L.
    """

    points = serializers.IntegerField(initial=40, min_value=1, label=_("points"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=CharacterRandomizeSpecialSerializer,
    serializer=SimpleCharacterSerializer,
)
def character_randomize_special(request, character_id):
    """
    API permettant de générer aléatoirement le S.P.E.C.I.A.L. d'un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        character.randomize_special(**request.validated_data)
        return character
    except Exception as exception:
        raise ValidationError(str(exception))


class CharacterRandomizeStatsSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour la génération aléatoire des statistiques
    """

    level = serializers.IntegerField(initial=1, min_value=1, label=_("niveau"))
    balance = serializers.IntegerField(initial=0, min_value=0, max_value=100, label=_("balance"))
    reset = serializers.BooleanField(initial=False, required=False, label=_("reset ?"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=CharacterRandomizeStatsSerializer,
    serializer=SimpleCharacterSerializer,
)
def character_randomize_stats(request, character_id):
    """
    API permettant de générer aléatoirement les statistiques d'un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        character.randomize_stats(**request.validated_data)
        return character
    except Exception as exception:
        raise ValidationError(str(exception))


@to_model_serializer(CharacterEffect)
class CharacterEffectSerializer(CommonModelSerializer):
    """
    Serializer des butins
    """

    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))
    effect = create_model_serializer(Effect)(read_only=True, label=_("effet"))
    damages = create_model_serializer(DamageHistory)(read_only=True, many=True, label=_("dégâts"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=EffectAffectInputSerializer,
    serializer=CharacterEffectSerializer,
)
def character_effect(request, character_id):
    """
    API permettant d'affecter un effet à un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    effect = request.validated_data.get("effect")
    try:
        return effect.affect(character)
    except Exception as exception:
        raise ValidationError(str(exception))


@to_model_serializer(Equipment)
class EquipmentSerializer(CommonModelSerializer):
    """
    Serializer de sortie pour afficher des équipements
    """

    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))
    item = create_model_serializer(Item, exclude=("effects", "ammunitions"))(read_only=True, label=_("objet"))


class ItemGiveInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour donner des objets
    """

    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.order_by("name"), label=_("objet"))
    quantity = serializers.IntegerField(initial=1, required=False, label=_("quantité"))
    condition = serializers.IntegerField(initial=100, required=False, label=_("état"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=ItemGiveInputSerializer,
    serializer=EquipmentSerializer,
)
def character_item(request, character_id):
    """
    API permettant de donner un objet à un personnage
    """
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    item = request.validated_data.pop("item")
    try:
        return item.give(character=character, **request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class ActionInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour toutes les actions
    """

    is_action = serializers.BooleanField(initial=False, required=False, label=_("action ?"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=ActionInputSerializer,
    serializer=EquipmentSerializer,
)
def equipment_equip(request, equipment_id):
    """
    API permettant de s'équiper ou de déséquiper d'un équipement de l'inventaire
    """
    equipment = get_object_or_404(Equipment.objects.select_related("character__campaign"), pk=equipment_id)
    is_authorized(request, equipment.character.campaign)
    try:
        return equipment.equip(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


@to_model_serializer(ItemModifier)
class ItemModifierSerializer(CommonModelSerializer):
    """
    Serialiser des modificateurs
    """

    current_value = serializers.IntegerField(read_only=True, label=_("valeur"))


class EquipmentUseSerializer(BaseCustomSerializer):
    """
    Serializer pour l'utilisation d'objets
    """

    effects = CharacterEffectSerializer(read_only=True, many=True, label=_("effets"))
    modifiers = ItemModifierSerializer(read_only=True, many=True, label=_("modificateurs"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=ActionInputSerializer,
    serializer=EquipmentUseSerializer,
)
def equipment_use(request, equipment_id):
    """
    API permettant d'utiliser un objet (si applicable)
    """
    equipment = get_object_or_404(Equipment.objects.select_related("character__campaign"), pk=equipment_id)
    is_authorized(request, equipment.character.campaign)
    try:
        effects, modifiers = equipment.use(**request.validated_data)
        return dict(effects=effects, modifiers=modifiers)
    except Exception as exception:
        raise ValidationError(str(exception))


@api_view_with_serializer(
    ["POST"],
    input_serializer=ActionInputSerializer,
    serializer=EquipmentSerializer,
)
def equipment_reload(request, equipment_id):
    """
    API permettant de recharger une arme à feu (si applicable)
    """
    equipment = get_object_or_404(Equipment.objects.select_related("character__campaign"), pk=equipment_id)
    is_authorized(request, equipment.character.campaign)
    try:
        return equipment.reload(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class ActionWithQuantityInputSerializer(ActionInputSerializer):
    """
    Serializer d'entrée pour effectuer une action impliquant une quantité
    """

    quantity = serializers.IntegerField(initial=1, required=False, label=_("quantité"))


@to_model_serializer(Loot)
class LootSerializer(CommonModelSerializer):
    """
    Serializer des butins
    """

    campaign = create_model_serializer(Campaign)(read_only=True, label=_("campagne"))
    item = create_model_serializer(Item)(read_only=True, label=_("objet"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=ActionWithQuantityInputSerializer,
    serializer=LootSerializer,
)
def equipment_drop(request, equipment_id):
    """
    API permettant de séparer d'un équipement et d'en faire un butin
    """
    equipment = get_object_or_404(Equipment.objects.select_related("character__campaign"), pk=equipment_id)
    is_authorized(request, equipment.character.campaign)
    try:
        return equipment.drop(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class LootTakeInputSerializer(ActionInputSerializer):
    """
    Serializer d'entrée pour ramasser un butin
    """

    character = serializers.PrimaryKeyRelatedField(
        queryset=Character.objects.order_by("name"),
        label=_("personnage"),
    )
    count = serializers.IntegerField(initial=1, required=False, label=_("nombre"))

    def __init__(self, *args, **kwargs):
        """
        Initialisateur spécifique pour restreindre la liste des personnages à ceux de la campagne ciblée
        """
        super().__init__(*args, **kwargs)
        loot_id = int(getattr(self.context.get("view"), "kwargs", {}).get("loot_id", 0))
        if loot_id:
            character_field = self.fields["character"]
            character_field.queryset = character_field.queryset.filter(campaign__loots=loot_id)


@api_view_with_serializer(
    ["POST"],
    input_serializer=LootTakeInputSerializer,
    serializer=EquipmentSerializer,
)
def loot_take(request, loot_id):
    """
    API permettant de ramasser un butin
    """
    loot = get_object_or_404(Loot.objects.select_related("campaign"), pk=loot_id)
    is_authorized(request, loot.campaign)
    try:
        return loot.take(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class LootTemplateOpenInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour l'ouverture des butins
    """

    campaign = serializers.PrimaryKeyRelatedField(
        queryset=Campaign.objects.order_by("name"),
        label=_("campagne"),
    )
    character = serializers.PrimaryKeyRelatedField(
        allow_empty=True,
        allow_null=True,
        required=False,
        queryset=Character.objects.order_by("name"),
        label=_("personnage"),
    )


@api_view_with_serializer(
    ["POST"],
    input_serializer=LootTemplateOpenInputSerializer,
    serializer=LootSerializer,
)
def loottemplate_open(request, template_id):
    """
    API permettant d'ouvrir un butin dans une campagne
    """
    loot_template = get_object_or_404(LootTemplate, pk=template_id)
    is_authorized(request, request.validated_data.get("campaign"))
    try:
        return loot_template.create(**request.validated_data)
    except Exception as exception:
        raise ValidationError(str(exception))


class NextTurnInputSerializer(BaseCustomSerializer):
    """
    Serializer d'entrée pour changer le tour des personnages dans une campagne
    """

    seconds = serializers.IntegerField(initial=0, required=False, label=_("secondes"))
    resting = serializers.BooleanField(initial=False, required=False, label=_("au repos ?"))
    apply = serializers.BooleanField(initial=True, required=False, label=_("valider ?"))
    reset = serializers.BooleanField(initial=False, required=False, label=_("réinitialiser ?"))


class NextTurnSerializer(BaseCustomSerializer):
    """
    Serializer des données de fin de tour
    """

    campaign = create_model_serializer(Campaign)(read_only=True, label=_("campagne"))
    character = SimpleCharacterSerializer(read_only=True, label=_("personnage"))
    damages = DamageHistorySerializer(read_only=True, many=True, label=_("dégâts"))


@api_view_with_serializer(
    ["POST"],
    input_serializer=NextTurnInputSerializer,
    serializer=NextTurnSerializer,
)
def campaign_next_turn(request, campaign_id):
    """
    API pour changer le tour des personnages
    """
    campaign = get_object_or_404(Campaign, pk=campaign_id)
    is_authorized(request, campaign)
    try:
        character, damages = campaign.next_turn(**request.validated_data)
        return dict(campaign=campaign, character=character, damages=damages)
    except Exception as exception:
        raise ValidationError(str(exception))


class StatInfoSerializer(BaseCustomSerializer):
    """
    Serializer des statistiques de personnage
    """

    code = serializers.CharField(label=_("code"))
    label = serializers.CharField(label=_("libellé"))
    value = serializers.IntegerField(source="lvalue", label=_("valeur"))
    max = serializers.IntegerField(source="rvalue", label=_("maximum"))
    css = serializers.CharField(label=_("CSS"))
    rate = serializers.FloatField(label=_("taux"))
    prefix = serializers.CharField(label=_("préfixe"))
    suffix = serializers.CharField(label=_("suffixe"))
    title = serializers.CharField(label=_("titre"))


@api_view_with_serializer(["GET"], serializer=StatInfoSerializer)
def character_stats(request, character_id):
    character = get_object_or_404(Character.objects.select_related("campaign", "statistics"), pk=character_id)
    is_authorized(request, character.campaign)
    try:
        return [stats._asdict() for stats in character.all_stats]
    except Exception as exception:
        raise ValidationError(str(exception))


namespace = "fallout-api"
app_name = "fallout"
urlpatterns = [
    path(
        "campaign/<int:campaign_id>/next/",
        campaign_next_turn,
        name="campaign_next_turn",
    ),
    path(
        "campaign/<int:campaign_id>/clear/",
        campaign_clear_loot,
        name="campaign_clear_loot",
    ),
    path(
        "campaign/<int:campaign_id>/roll/",
        campaign_roll,
        name="campaign_roll",
    ),
    path(
        "campaign/<int:campaign_id>/damage/",
        campaign_damage,
        name="campaign_damage",
    ),
    path(
        "campaign/<int:campaign_id>/effect/",
        campaign_effect,
        name="campaign_effect",
    ),
    path(
        "character/<int:character_id>/xp/",
        character_xp,
        name="character_xp",
    ),
    path(
        "character/<int:character_id>/roll/",
        character_roll,
        name="character_roll",
    ),
    path(
        "character/<int:character_id>/fight/",
        character_fight,
        name="character_fight",
    ),
    path(
        "character/<int:character_id>/burst/",
        character_burst,
        name="character_burst",
    ),
    path(
        "character/<int:character_id>/damage/",
        character_damage,
        name="character_damage",
    ),
    path(
        "character/<int:character_id>/copy/",
        character_copy,
        name="character_copy",
    ),
    path(
        "character/<int:character_id>/random_special/",
        character_randomize_special,
        name="character_randomize_special",
    ),
    path(
        "character/<int:character_id>/random_stats/",
        character_randomize_stats,
        name="character_randomize_stats",
    ),
    path(
        "character/<int:character_id>/effect/",
        character_effect,
        name="character_effect",
    ),
    path(
        "character/<int:character_id>/item/",
        character_item,
        name="character_item",
    ),
    path(
        "character/<int:character_id>/stats/",
        character_stats,
        name="character_stats",
    ),
    path(
        "equipment/<int:equipment_id>/equip/",
        equipment_equip,
        name="equipment_equip",
    ),
    path(
        "equipment/<int:equipment_id>/use/",
        equipment_use,
        name="equipment_use",
    ),
    path(
        "equipment/<int:equipment_id>/reload/",
        equipment_reload,
        name="equipment_reload",
    ),
    path(
        "equipment/<int:equipment_id>/drop/",
        equipment_drop,
        name="equipment_drop",
    ),
    path(
        "loottemplate/<int:template_id>/open/",
        loottemplate_open,
        name="loottemplate_open",
    ),
    path(
        "loot/<int:loot_id>/take/",
        loot_take,
        name="loot_take",
    ),
] + router.urls
urls = (urlpatterns, namespace, app_name)
