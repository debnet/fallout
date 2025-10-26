# coding: utf-8
import dataclasses
from collections import OrderedDict as odict, Counter
from collections import namedtuple
from datetime import datetime, timedelta
from operator import add
from random import choice, randint
from typing import Dict, Iterable, List, Optional, Tuple, Union

from common.fields import JsonField
from common.models import CommonModel, CommonQuerySet, Entity
from common.utils import to_object
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Case, Count, F, Prefetch, Q, Sum, Value, When
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField

from fallout.constants import *  # noqa
from fallout.enums import *  # noqa


gv, sv = getattr, setattr


def _assert(condition, message: str = None) -> None:
    """
    Assertion
    :param condition: Condition à vérifier
    :param message: Message de l'assertion
    :return: Rien
    """
    if not condition:
        raise AssertionError(message)


def get_thumbnails(directory: str = "") -> List[Tuple[str, str]]:
    """
    Scanne les images le répertoire "medias" à la recherche de miniatures
    :param directory: Répertoire à scanner
    :return: Liste des images
    """
    import os
    import sys

    if any(command in sys.argv for command in ("makemigrations", "migrate")):
        return []
    images = []
    try:
        dirname = os.path.join(settings.STATIC_ROOT, "fallout/img/thumbnails", directory)
        if not os.path.exists(dirname) and settings.DEBUG:
            dirname = os.path.join(settings.BASE_DIR, "fallout/static/fallout/img/thumbnails", directory)
        for filename in os.listdir(dirname):
            filepath = os.path.join(dirname, filename)
            title, ext = os.path.splitext(filename.replace("_", " "))
            filename = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                images.append((title, get_thumbnails(filename)))
            elif ext.lower() in (".jpg", ".jpeg", ".gif", ".png"):
                url = os.path.join("thumbnails", filename).replace("\\", "/")
                images.append((url, title))
    finally:
        return sorted(images)


def get_class(
    value: Union[int, float],
    maximum: Union[int, float],
    classes: Iterable[str] = None,
    values: Iterable[float] = None,
    reverse: bool = False,
    default: str = "light",
) -> str:
    """
    Affecte une classe CSS à une valeur donnée
    :param value: Valeur
    :param maximum: Plafond
    :param classes: Ensemble de classes CSS
    :param values: Ensemble de valeurs de comparaison
    :param reverse: Inverser l'ordre des classes
    :param default: Classe par défaut
    :return: Classe CSS
    """
    if not maximum:
        return default
    classes = classes or ("info", "info", "success", "warning", "danger", "secondary")
    values = values or (1.0, 0.8, 0.6, 0.4, 0.2, 0.0)
    rate = value / maximum
    classes_values = list(zip(classes, values))
    classes_values = reversed(classes_values) if reverse else classes_values
    for _class, _value in classes_values:
        if rate >= _value:
            return _class
    return default


@dataclasses.dataclass
class Stats:
    """
    Statistiques actuelles du personnage
    """

    # S.P.E.C.I.A.L.
    strength: int = 5
    perception: int = 5
    endurance: int = 5
    charisma: int = 5
    intelligence: int = 5
    agility: int = 5
    luck: int = 5
    # Secondary statistics
    max_health: int = 0
    max_action_points: int = 0
    armor_class: int = 0
    carry_weight: int = 0
    melee_damage: int = 0
    sequence: int = 0
    healing_rate: int = 0
    ap_cost_modifier: int = 0
    one_hand_accuracy: int = 0
    two_hands_accuracy: int = 0
    damage_modifier: int = 0
    critical_chance: int = 0
    critical_raw_chance: int = 0
    critical_damage: int = 0
    # Skills
    small_guns: int = 0
    big_guns: int = 0
    energy_weapons: int = 0
    unarmed: int = 0
    melee_weapons: int = 0
    throwing: int = 0
    athletics: int = 0
    detection: int = 0
    first_aid: int = 0
    doctor: int = 0
    chems: int = 0
    sneak: int = 0
    lockpick: int = 0
    steal: int = 0
    traps: int = 0
    explosives: int = 0
    science: int = 0
    repair: int = 0
    computers: int = 0
    electronics: int = 0
    speech: int = 0
    deception: int = 0
    barter: int = 0
    survival: int = 0
    knowledge: int = 0
    # Leveled stats
    hit_points_per_level: int = 0
    skill_points_per_level: int = 0
    perk_rate: int = 0
    # Resistances
    damage_threshold: int = 0
    damage_resistance: int = 0
    normal_threshold: int = 0
    normal_resistance: int = 0
    laser_threshold: int = 0
    laser_resistance: int = 0
    plasma_threshold: int = 0
    plasma_resistance: int = 0
    explosive_threshold: int = 0
    explosive_resistance: int = 0
    fire_threshold: int = 0
    fire_resistance: int = 0
    electricity_threshold: int = 0
    electricity_resistance: int = 0
    poison_threshold: int = 0
    poison_resistance: int = 0
    radiation_threshold: int = 0
    radiation_resistance: int = 0
    gas_contact_threshold: int = 0
    gas_contact_resistance: int = 0
    gas_inhaled_threshold: int = 0
    gas_inhaled_resistance: int = 0
    # Modifiers
    charge: float = 0.0
    modifiers: dict = dataclasses.field(init=False)

    def __post_init__(self):
        self.raw = {}
        self.base = {}
        self.modifiers = {}
        self.character_modifiers = {}
        self.character = None

    @staticmethod
    def get(character: "Character") -> "Stats":
        """
        Récupère toutes les statistiques à jour d'un personnage
        :param character: Personnage
        :return: Statistiques
        """
        stats = Stats()
        stats.character = character
        # Get all character's stats
        for stats_name in LIST_EDITABLE_STATS:
            stats.base[stats_name] = gv(character, stats_name, 0)
            sv(stats, stats_name, gv(character, stats_name, 0))
        # Racial modifiers
        race_stats = RACES_STATS.get(character.race, {})
        stats.change_all_stats(limit=True, **race_stats)
        for stats_name, (value, mini, maxi) in race_stats.items():
            stats.base[stats_name] = (stats.base.get(stats_name) or 0) + (value or 0)
        # Tag skills
        for skill in set(character.tag_skills):
            stats.base[skill] = (stats.base.get(skill) or 0) + TAG_SKILL_BONUS
            stats.change_stats(skill, TAG_SKILL_BONUS, raw=False)
        # Base statistics
        base_stats = to_object(stats.base)
        base_stats.level = character.level
        for stats_name, formula in COMPUTED_STATS:
            result = stats.base[stats_name] = stats.base.get(stats_name, 0) + formula(base_stats, base_stats)
            sv(base_stats, stats_name, result)
        # Survival modifiers
        for stats_name, survival in SURVIVAL_EFFECTS:
            for (mini, maxi), effects in survival.items():
                if (mini or 0) <= gv(character, stats_name, 0) < (maxi or float("inf")):
                    stats.change_all_stats(**effects)
                    break
        # Equipment modifiers
        for equipment in character.inventory.filter(~Q(slot="") | Q(item__type__in=(ITEM_EXTRA, ITEM_TOOL))):
            for count in range(equipment.quantity):
                for modifier in equipment.item.modifiers.all():
                    stats.change_stats(modifier.stats, modifier.calculated_value)
        # Active effects modifiers
        for effect in character.effects.exclude(effect__modifiers__isnull=True):
            for modifier in effect.effect.modifiers.all():
                stats.change_stats(modifier.stats, modifier.calculated_value)
        # Campaign effects modifiers
        if character.campaign:
            for effect in character.campaign.effects.exclude(effect__modifiers__isnull=True):
                for modifier in effect.effect.modifiers.all():
                    stats.change_stats(modifier.stats, modifier.calculated_value, limit=False)
        # Carry weight & charge
        for stats_name, formula in COMPUTED_STATS[:1]:  # Only carry weight formula (1st in list)
            stats.change_stats(stats_name, formula(stats, character) + stats.raw.get(stats_name, 0), raw=False)
        stats.charge = (
            character.equipments.aggregate(
                charge=Sum(F("quantity") * F("item__weight"), output_field=models.FloatField())
            ).get("charge")
            or 0.0
        )
        charge_rate = (stats.charge / (stats.carry_weight or 1)) * 100.0
        for (mini, maxi), effects in CARRY_WEIGHT_EFFECTS.items():
            if (mini or 0.0) <= charge_rate < (maxi or float("inf")):
                stats.change_all_stats(**effects)
                break
        # Derivated statistics
        for stats_name, formula in COMPUTED_STATS[1:]:  # Except carry weight
            stats.change_stats(stats_name, formula(stats, character) + stats.raw.get(stats_name, 0), raw=False)
        # Modifiers
        for stats_name in LIST_EDITABLE_STATS:
            from_base = stats.base.get(stats_name, 0)
            from_stats = gv(stats, stats_name, 0)
            if from_base == from_stats:
                continue
            stats.modifiers[stats_name] = from_stats - from_base
        return stats

    def change_all_stats(self, limit: bool = False, **stats: Tuple[int, Optional[int], Optional[int]]) -> None:
        for name, values in stats.items():
            self.change_stats(name, *values, limit=limit)

    def change_stats(
        self,
        name: str,
        value: int = 0,
        mini: Optional[int] = None,
        maxi: Optional[int] = None,
        limit: bool = False,
        raw: bool = True,
    ) -> None:
        if raw and name in LIST_COMPUTED_STATS:
            self.raw[name] = self.raw.setdefault(name, 0) + value
            return
        if not self.character:
            return
        bonus, race_mini, race_maxi = RACES_STATS.get(self.character.race, {}).get(name, (None, None, None))
        target = self if name in LIST_EDITABLE_STATS else self.character
        if limit:
            mini = (mini if mini is not None else race_mini) or float("-inf")  # type: ignore
            maxi = (maxi if maxi is not None else race_maxi) or float("+inf")  # type: ignore
        else:
            mini, maxi = 0, float("+inf")  # type: ignore
        result = min(max(gv(target, name, 0) + value, mini), maxi)
        sv(target, name, result)
        if isinstance(target, Character):
            self.character_modifiers[name] = result


class Player(AbstractUser):
    """
    Joueur
    """

    nickname = models.CharField(max_length=100, blank=True, verbose_name=_("surnom"))

    def __str__(self):
        return self.nickname or self.first_name or self.username

    class Meta:
        verbose_name = _("joueur")
        verbose_name_plural = _("joueurs")


class Campaign(CommonModel):
    """
    Campagne
    """

    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, upload_to="campaigns", verbose_name=_("image"))
    thumbnail = models.CharField(
        blank=True,
        max_length=100,
        choices=get_thumbnails("campaigns"),
        verbose_name=_("miniature"),
    )
    game_master = models.ForeignKey(
        "Player",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("maître du jeu"),
    )
    start_game_date = models.DateTimeField(default=now, verbose_name=_("date de début"))
    current_game_date = models.DateTimeField(default=now, verbose_name=_("date courante"))
    current_character = models.ForeignKey(
        "Character",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("personnage actif"),
    )
    radiation = models.PositiveSmallIntegerField(default=0, verbose_name=_("rads par heure"))
    needs = models.BooleanField(default=True, verbose_name=_("besoins activés ?"))
    view_pc = models.BooleanField(default=False, verbose_name=_("voir les personnages joueurs"))
    view_npc = models.BooleanField(default=False, verbose_name=_("voir les personnages non-joueurs"))
    view_rolls = models.BooleanField(default=False, verbose_name=_("voir les jets lancés"))
    money = models.PositiveIntegerField(default=0, verbose_name=_("argent"))
    money_loot = models.PositiveIntegerField(default=0, verbose_name=_("argent à piller"))
    damages: List["DamageHistory"] = []
    # Cache
    _effects: "CommonQuerySet[ActiveEffect]" = None

    @property
    def elapsed_time(self) -> timedelta:
        """
        Temps passé depuis le début de la campagne
        :return:
        """
        return self.current_game_date - self.start_game_date

    @property
    def effects(self) -> "CommonQuerySet[CampaignEffect]":
        """
        Retourne les effets actifs de la campagne
        :return: Effets
        """
        self._effects = (
            self._effects
            if self._effects is not None
            else (
                self.active_effects.select_related("campaign", "effect__next_effect").prefetch_related(
                    "effect__modifiers"
                )
            )
        )
        return self._effects

    def clear_loot(self):
        """
        Supprime les butins non réclamés de la campagne
        """
        return self.loots.all().delete()

    def next_turn(
        self,
        seconds: int = TURN_TIME,
        resting: bool = False,
        apply: bool = True,
        reset: bool = False,
    ) -> Tuple[Optional["Character"], List["DamageHistory"]]:
        """
        Détermine qui est le prochain personnage à agir
        :param seconds: Temps utilisé (en secondes) par le personnage précédent pour son tour de jeu
        :param resting: Temps de repos ?
        :param apply: Applique directement le changement sur la campagne
        :param reset: Réinitialise l'ordre de passage des personnages
        :return: Personnage suivant potentiel, liste des dégâts
        """
        next_character = None
        if not reset:
            characters = self.characters.filter(is_active=True).exclude(health__lte=0)
            characters = sorted(characters, key=lambda e: -e.stats.sequence)
            if self.current_character not in characters:
                self.current_character = None
            if not self.current_character:
                next_character = next(iter(characters), None)
            else:
                from itertools import cycle

                previous_character = None
                for character in cycle(characters):
                    if previous_character == self.current_character:
                        next_character = character
                        break
                    previous_character = character
        if apply:
            self.current_game_date += timedelta(seconds=seconds)
            self.current_character = next_character
            self.save(resting=resting)
            # Reset character action points
            if (
                self.current_character
                and self.current_character.action_points != self.current_character.stats.max_action_points
            ):
                self.current_character.action_points = self.current_character.stats.max_action_points
                self.current_character.save(reset=False)
        return next_character, self.damages

    def clear_turn(self) -> None:
        """
        Désactive le système de tour par tour
        :return: Rien
        """
        self.current_character = None
        for character in self.characters.all():
            character.action_points = character.stats.max_action_points
            character.save(reset=False)
        self.save()

    def save(self, resting=False, *args, **kwargs):
        """
        Sauvegarde la campagne
        """
        self.previous_game_date = self._copy.get("current_game_date") or self.current_game_date
        difference = self.current_game_date - self.previous_game_date
        hours = round(difference.total_seconds() / 3600, 6)
        super().save(*args, **kwargs)
        if hours <= 0:
            return
        self.damages = []
        for effect in self.effects:
            self.damages.extend(effect.apply_all(save=False))
        for character in self.characters.filter(is_active=True).exclude(health__lte=0):
            self.damages.extend(
                character.update_needs(
                    hours=hours,
                    radiation=self.radiation,
                    resting=resting,
                    needs=self.needs,
                    save=False,
                )
            )
            self.damages.extend(character.apply_effects(save=False))
            character.save()

    def get_absolute_url(self):
        """
        Retourne l'URL vers la page de la campagne
        """
        from django.urls import reverse

        return reverse("fallout:campaign", args=[str(self.pk)])

    def __str__(self) -> str:
        if self.title:
            return f"{self.name} ({self.title})"
        return self.name

    class Meta:
        verbose_name = _("campagne")
        verbose_name_plural = _("campagnes")


class Resistance(CommonModel):
    """
    Résistances
    """

    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption de dégâts"))
    damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts"))
    normal_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption normal"))
    normal_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance normal"))
    laser_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption laser"))
    laser_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance laser"))
    plasma_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption plasma"))
    plasma_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance plasma"))
    explosive_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption explosifs"))
    explosive_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance explosifs"))
    fire_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption feu"))
    fire_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance feu"))
    electricity_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption électricité"))
    electricity_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance électricité"))
    poison_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption poison"))
    poison_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance poison"))
    radiation_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption radiations"))
    radiation_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance radiations"))
    gas_contact_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption gaz (contact)"))
    gas_contact_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance gaz (contact)"))
    gas_inhaled_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption gaz (inhalé)"))
    gas_inhaled_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance gaz (inhalé)"))

    def get_threshold(self, damage_type: str = DAMAGE_NORMAL) -> int:
        """
        Récupère l'absorption de dégâts d'un type particulier
        """
        return gv(self, damage_type + "_threshold", 0)

    def get_resistance(self, damage_type: str = DAMAGE_NORMAL) -> int:
        """
        Récupère la résistance aux dégâts d'un type
        """
        return gv(self, damage_type + "_resistance", 0)

    class Meta:
        abstract = True


class BaseStatistics(Resistance):
    """
    Statistiques de base
    """

    # S.P.E.C.I.A.L.
    strength = models.PositiveSmallIntegerField(default=5, verbose_name=_("force"))
    perception = models.PositiveSmallIntegerField(default=5, verbose_name=_("perception"))
    endurance = models.PositiveSmallIntegerField(default=5, verbose_name=_("endurance"))
    charisma = models.PositiveSmallIntegerField(default=5, verbose_name=_("charisme"))
    intelligence = models.PositiveSmallIntegerField(default=5, verbose_name=_("intelligence"))
    agility = models.PositiveSmallIntegerField(default=5, verbose_name=_("agilité"))
    luck = models.PositiveSmallIntegerField(default=5, verbose_name=_("chance"))
    # Secondary statistics
    max_health = models.PositiveSmallIntegerField(default=0, verbose_name=_("santé maximale"))
    max_action_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points d'action max."))
    armor_class = models.SmallIntegerField(default=0, verbose_name=_("classe d'armure"))
    carry_weight = models.SmallIntegerField(default=0, verbose_name=_("charge maximale"))
    melee_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts en mêlée"))
    sequence = models.SmallIntegerField(default=0, verbose_name=_("initiative"))
    healing_rate = models.SmallIntegerField(default=0, verbose_name=_("taux de regénération"))
    ap_cost_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur d'action"))
    one_hand_accuracy = models.SmallIntegerField(default=0, verbose_name=_("précision à une main"))
    two_hands_accuracy = models.SmallIntegerField(default=0, verbose_name=_("précision à deux mains"))
    damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de dégâts"))
    critical_chance = models.SmallIntegerField(default=0, verbose_name=_("chances de critiques"))
    critical_raw_chance = models.SmallIntegerField(default=0, verbose_name=_("chances de dégâts bruts"))
    critical_damage = models.SmallIntegerField(default=0, verbose_name=_("modificateur dégâts critiques"))
    # Skills
    small_guns = models.SmallIntegerField(default=0, verbose_name=_("armes à feu légères"))
    big_guns = models.SmallIntegerField(default=0, verbose_name=_("armes à feu lourdes"))
    energy_weapons = models.SmallIntegerField(default=0, verbose_name=_("armes à énergie"))
    unarmed = models.SmallIntegerField(default=0, verbose_name=_("à mains nues"))
    melee_weapons = models.SmallIntegerField(default=0, verbose_name=_("armes de mêlée"))
    throwing = models.SmallIntegerField(default=0, verbose_name=_("armes de lancer"))
    athletics = models.SmallIntegerField(default=0, verbose_name=_("athlétisme"))
    detection = models.SmallIntegerField(default=0, verbose_name=_("détection"))
    first_aid = models.SmallIntegerField(default=0, verbose_name=_("premiers secours"))
    doctor = models.SmallIntegerField(default=0, verbose_name=_("médecine"))
    chems = models.SmallIntegerField(default=0, verbose_name=_("pharmacologie"))
    sneak = models.SmallIntegerField(default=0, verbose_name=_("discrétion"))
    lockpick = models.SmallIntegerField(default=0, verbose_name=_("crochetage"))
    steal = models.SmallIntegerField(default=0, verbose_name=_("pickpocket"))
    traps = models.SmallIntegerField(default=0, verbose_name=_("pièges"))
    explosives = models.SmallIntegerField(default=0, verbose_name=_("explosifs"))
    science = models.SmallIntegerField(default=0, verbose_name=_("science"))
    repair = models.SmallIntegerField(default=0, verbose_name=_("mécanique"))
    computers = models.SmallIntegerField(default=0, verbose_name=_("informatique"))
    electronics = models.SmallIntegerField(default=0, verbose_name=_("électronique"))
    speech = models.SmallIntegerField(default=0, verbose_name=_("persuasion"))
    deception = models.SmallIntegerField(default=0, verbose_name=_("tromperie"))
    barter = models.SmallIntegerField(default=0, verbose_name=_("marchandage"))
    survival = models.SmallIntegerField(default=0, verbose_name=_("survie"))
    knowledge = models.SmallIntegerField(default=0, verbose_name=_("connaissance"))
    # Leveled stats
    hit_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("santé par niveau"))
    skill_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("compétences par niveau"))
    perk_rate = models.SmallIntegerField(default=0, verbose_name=_("niveaux pour un talent"))

    class Meta:
        abstract = True


class Statistics(BaseStatistics):
    """
    Statistiques de personnage
    """

    character = models.OneToOneField(
        "Character",
        primary_key=True,
        on_delete=models.CASCADE,
        related_name="statistics",
        verbose_name=_("personnage"),
    )
    # Others
    charge = models.FloatField(default=0.0, verbose_name=_("charge"))
    modifiers = JsonField(blank=True, null=True, verbose_name=_("modificateurs"))
    obsolete = models.BooleanField(default=False, editable=False, verbose_name=_("obsolète"))
    date = models.DateTimeField(auto_now=True, editable=False, verbose_name=_("date"))
    _code_field = "character"

    def __str__(self) -> str:
        if self.character:
            return str(self.character)
        return ""

    class Meta:
        verbose_name = _("statistiques")
        verbose_name_plural = _("statistiques")


# Tuple pour les données des statistiques
StatInfo = namedtuple(
    "StatInfo",
    (
        "code",
        "label",
        "lvalue",
        "rvalue",
        "css",
        "rate",
        "prefix",
        "suffix",
        "title",
    ),
)

# Sous-titre pour les bonus d'équipements
EQUIP_TITLE = _("Armure : <strong>{armor}</strong><br>Casque : <strong>{helmet}</strong>")
EMPTY = _("absent")


class Character(Entity, BaseStatistics):
    """
    Personnage
    """

    # Technical information
    player = models.ForeignKey(
        "Player",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="characters",
        verbose_name=_("joueur"),
    )
    campaign = models.ForeignKey(
        "Campaign",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="characters",
        verbose_name=_("campagne"),
    )
    # General information
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    background = models.TextField(blank=True, verbose_name=_("contexte"))
    image = models.ImageField(blank=True, null=True, upload_to="characters", verbose_name=_("image"))
    thumbnail = models.CharField(
        blank=True,
        max_length=100,
        choices=get_thumbnails("characters"),
        verbose_name=_("miniature"),
    )
    race = models.CharField(
        max_length=20,
        choices=RACES,
        default=RACE_HUMAN,
        db_index=True,
        verbose_name=_("race"),
    )
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_("niveau"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("actif ?"))
    is_visible = models.BooleanField(default=False, db_index=True, verbose_name=_("visible ?"))
    is_player = models.BooleanField(default=False, db_index=True, verbose_name=_("joueur ?"))
    is_resting = models.BooleanField(default=False, verbose_name=_("au repos ?"))
    has_stats = models.BooleanField(default=True, verbose_name=_("stats calculées ?"))
    has_needs = models.BooleanField(default=True, verbose_name=_("besoins activés ?"))
    enable_levelup = models.BooleanField(default=False, verbose_name=_("montée de niveau ?"))
    enable_stats = models.BooleanField(default=False, verbose_name=_("active les stats ?"))
    enable_logs = models.BooleanField(default=False, verbose_name=_("active le journal ?"))
    # Primary statistics
    health = models.PositiveSmallIntegerField(default=0, verbose_name=_("santé"))
    action_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points d'action"))
    skill_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de compétence"))
    perk_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de talent"))
    experience = models.PositiveIntegerField(default=0, verbose_name=_("expérience"))
    karma = models.SmallIntegerField(default=0, verbose_name=_("karma"))
    money = models.PositiveIntegerField(default=0, verbose_name=_("argent"))
    reward = models.PositiveSmallIntegerField(default=0, verbose_name=_("récompense"))
    loot_on_death = models.BooleanField(default=True, verbose_name=_("butin au décès ?"))
    # Needs
    rads = models.FloatField(default=0.0, verbose_name=_("rads"))
    thirst = models.FloatField(default=0.0, verbose_name=_("soif"))
    hunger = models.FloatField(default=0.0, verbose_name=_("faim"))
    sleep = models.FloatField(default=0.0, verbose_name=_("sommeil"))
    regeneration = models.FloatField(default=0.0, verbose_name=_("regénération"))
    # Tag skills
    tag_skills = MultiSelectField(max_length=300, choices=SKILLS, blank=True, verbose_name=_("spécialités"))
    # Extra data
    extra_data = JsonField(blank=True, null=True, verbose_name=_("données complémentaires"))
    # Cache
    charge = 0
    _stats: Dict[str, float] = {}
    _inventory = _equipment = _effects = None

    @staticmethod
    def reset_stats(character: Union["Character", int]):
        """
        Réinitialise le calcul des statistiques pour un personnage
        """
        if isinstance(character, Character):
            character.statistics = None  # type: ignore
            character = character.pk
        if character:
            Character._stats.pop(character, None)  # type: ignore
            Statistics.objects.filter(character_id=character).update(obsolete=True)

    @property
    def stats(self) -> Union[Statistics, Stats]:
        """
        Retourne les statistiques calculées du personnage
        :return: Statistiques
        """
        if not self.has_stats:
            return self
        try:
            _assert(not self.statistics.obsolete)
        except:  # noqa
            stats: Union[Statistics, Stats] = self._stats.get(self.pk) or Stats.get(self)  # type: ignore
            if self.pk:
                self._stats[self.pk] = stats
                self.statistics, created = Statistics.objects.update_or_create(
                    character=self,
                    defaults=dict(obsolete=False, **dataclasses.asdict(stats)),
                )
                # Character modifiers from statistics
                if stats.character_modifiers:
                    for key, value in stats.character_modifiers.items():
                        sv(self, key, value)
                    self.save(reset=False)
            else:
                return stats
        return self.statistics

    @property
    def inventory(self) -> "CommonQuerySet[Equipment]":
        """
        Retourne le contenu de l'inventaire du personnage
        :return: Equipements
        """
        self._inventory = (
            self._inventory
            if self._inventory is not None
            else (
                self.equipments.select_related("item")
                .prefetch_related(
                    "item__modifiers",
                    Prefetch(
                        "item__effects",
                        queryset=Effect.objects.select_related("next_effect", "cancel_effect"),
                    ),
                )
                .order_by("item__name")
            )
        )
        return self._inventory

    def get_from_inventory(self, many: bool = False, **criterias) -> Optional[Union["Equipment", List["Equipment"]]]:
        """
        Retourne un objet depuis l'inventaire correspondant aux critères
        (optimisé si l'inventaire est déjà chargé)
        :param many: Retourne plusieurs objets ?
        :param criterias: Critères exacts de recherche
        :return: Un ou plusieurs objets
        """
        items: Optional[Union["Equipment", List["Equipment"]]] = [] if many else None
        for item in self.inventory:
            found = True
            for key, value in criterias.items():
                found &= bool(gv(item, key) == value)
            if found:
                if not many:
                    return item
                items.append(item)  # type: ignore
        return items

    @property
    def effects(self) -> "CommonQuerySet[CharacterEffect]":
        """
        Retourne les effets actifs du personnage
        :return: Effets
        """
        self._effects = (
            self._effects
            if self._effects is not None
            else self.active_effects.select_related("character__campaign", "effect__next_effect").prefetch_related(
                "effect__modifiers"
            )
        )
        return self._effects

    def _get_stats(
        self, stats: Iterable[Tuple[str, str]], from_stats: bool = True
    ) -> Iterable[Tuple[str, str, Union[int, float]]]:
        """
        Fonction interne pour retourner les valeurs des statistiques ciblées
        :param stats: Tuple de statistiques (code, libellé)
        :param from_stats: Récupère la valeur calculée et pas la valeur brute enregistrée
        :return: Liste des statistiques avec leur valeur
        """
        for code, label in stats:
            yield code, label, gv(self.stats if from_stats else self, code, 0)

    @property
    def special(self) -> Iterable[StatInfo]:
        """
        Retourne le S.P.E.C.I.A.L.
        """
        for code, label, value in self._get_stats(SPECIALS):
            yield StatInfo(
                code=code,
                label=label,
                lvalue=value,
                rvalue=None,
                css=get_class(value, maximum=10),
                rate=None,
                prefix=None,
                suffix=None,
                title=None,
            )

    @property
    def skills(self) -> Iterable[StatInfo]:
        """
        Retourne les compétences
        """
        for code, label, value in self._get_stats(SKILLS):
            yield StatInfo(
                code=code,
                label=label,
                lvalue=value,
                rvalue=None,
                css=get_class(value, maximum=100),
                rate=None,
                prefix=None,
                suffix=" %",
                title=None,
            )

    @property
    def general_stats(self) -> Iterable[StatInfo]:
        """
        Retourne les statistiques générales
        :return: code, label, valeur à gauche, valeur à droite, classe, taux
        """
        classes: Iterable[str] = (
            "info",
            "info",
            "success",
            "warning",
            "danger",
            "secondary",
            "light",
        )
        values: Iterable[float] = (0.000, 0.001, 0.200, 0.400, 0.600, 0.800, 1.000)
        for code, label in GENERAL_STATS:
            lvalue = gv(self, code, 0)
            rvalue, rclass, prefix, suffix, title = None, None, None, None, None
            if code == STATS_HEALTH:
                code = STATS_MAX_HEALTH
                rvalue = gv(self.stats, STATS_MAX_HEALTH, 0)
                rclass = get_class(lvalue, rvalue)
            elif code == STATS_ACTION_POINTS:
                code = STATS_MAX_ACTION_POINTS
                rvalue = gv(self.stats, STATS_MAX_ACTION_POINTS, 0)
                rclass = get_class(lvalue, rvalue)
            elif code == STATS_SKILL_POINTS:
                rvalue = lvalue
                lvalue = self.used_skill_points
            elif code == STATS_EXPERIENCE:
                # Put carry weight before experience
                charge, carry_weight = self.stats.charge, self.stats.carry_weight
                if carry_weight:
                    classes = (
                        "info",
                        "info",
                        "success",
                        "warning",
                        "danger",
                        "secondary",
                    )
                    values = (0.000, 0.001, 0.250, 0.500, 0.750, 1.000)
                    rate = (charge / carry_weight or 0) * 100.0
                    yield StatInfo(
                        code=STATS_CARRY_WEIGHT,
                        label=_("charge"),
                        lvalue=charge,
                        rvalue=carry_weight,
                        css=get_class(
                            charge,
                            carry_weight,
                            reverse=True,
                            classes=classes,
                            values=values,
                        ),
                        rate=rate,
                        prefix=None,
                        suffix=_(" kg"),
                        title=self.get_need_label(STATS_CARRY_WEIGHT, value=rate),
                    )
                lvalue = lvalue - self.previous_required_experience
                rvalue = self.next_required_experience - self.previous_required_experience
                rclass = get_class(lvalue, rvalue)
            elif code in LIST_NEEDS:
                rvalue = 1000
                rclass = get_class(lvalue, rvalue, reverse=True, classes=classes, values=values)
                title = self.get_need_label(code)
            elif code == STATS_KARMA:
                prefix = "+" if lvalue > 0 else ""
                rclass = "success" if lvalue > 0 else "danger" if lvalue < 0 else None
            elif code == STATS_MONEY:
                suffix, rclass = _(" ¤"), "warning" if lvalue > 0 else None
            elif code == STATS_REWARD:
                suffix, rclass = _(" XP"), "success" if lvalue > 0 else None
            rate = ((lvalue / rvalue) * 100.0) if rvalue else None
            yield StatInfo(
                code=code,
                label=label,
                lvalue=lvalue,
                rvalue=rvalue,
                css=rclass,
                rate=rate,
                prefix=prefix,
                suffix=suffix,
                title=title,
            )
        # Secondary stats
        for statinfo in self.secondary_stats:
            yield statinfo

    @property
    def secondary_stats(self) -> Iterable[StatInfo]:
        """
        Retourne les statistiques secondaires
        """
        for code, label, value in self._get_stats(SECONDARY_STATS):
            if code in (
                STATS_MAX_HEALTH,
                STATS_MAX_ACTION_POINTS,
                STATS_CARRY_WEIGHT,
                STATS_ARMOR_CLASS,
            ):
                continue
            rclass, prefix, suffix, title = None, None, None, None
            if code == STATS_HEALING_RATE:
                suffix, rclass = _(" PV/j"), "success" if value > 0 else "danger" if value < 0 else None
            elif code == STATS_AP_COST_MODIFIER:
                prefix, suffix = "+" if value > 0 else None, _(" PA")
                rclass = "danger" if value > 0 else "success" if value < 0 else None
            elif code != STATS_SEQUENCE:
                prefix, suffix = "+" if value > 0 else None, " %" if code != STATS_MELEE_DAMAGE else None
                rclass = "success" if value > 0 else "danger" if value < 0 else None
            yield StatInfo(
                code=code,
                label=label,
                lvalue=value,
                rvalue=None,
                css=rclass,
                rate=None,
                prefix=prefix,
                suffix=suffix,
                title=title,
            )

    @property
    def resistances(self) -> Iterable[StatInfo]:
        """
        Retourne les résistances
        """
        armor, helmet = self.get_from_inventory(slot=ITEM_ARMOR), self.get_from_inventory(slot=ITEM_HELMET)
        # Armor classe
        armor, helmet = gv(armor, "item", None), gv(helmet, "item", None)
        code, label, value = (
            STATS_ARMOR_CLASS,
            LIST_ALL_STATS.get(STATS_ARMOR_CLASS),
            self.stats.armor_class,
        )
        armor_v, helmet_v = gv(armor, code, 0) or 0, gv(helmet, code, 0) or 0
        title = EQUIP_TITLE.format(armor=armor_v, helmet=helmet_v)
        css = "info" if armor_v or helmet_v else "success" if value > 0 else "danger" if value < 0 else None
        yield StatInfo(
            code=code,
            label=label,
            lvalue=value,
            rvalue=None,
            css=css,
            rate=None,
            prefix=None,
            suffix=None,
            title=title,
        )
        # Damage threshold and damage resistance
        for threshold, resistance in zip(self._get_stats(THRESHOLDS), self._get_stats(RESISTANCES)):
            (code_t, label_t, value_t), (code_r, label_r, value_r) = (
                threshold,
                resistance,
            )
            value_r = min(value_r, MAX_DAMAGE_RESISTANCE)
            armor_t, helmet_t = gv(armor, code_t, 0), gv(helmet, code_t, 0)
            armor_r, helmet_r = gv(armor, code_r, 0), gv(helmet, code_r, 0)
            css_t, css_r = (
                "info" if armor_t or helmet_t else "success" if value_t > 0 else "danger" if value_t < 0 else None,
                "info" if armor_r or helmet_r else "success" if value_r > 0 else "danger" if value_r < 0 else None,
            )
            title_t, title_r = (
                EQUIP_TITLE.format(armor=armor_t or EMPTY, helmet=helmet_t or EMPTY),
                EQUIP_TITLE.format(
                    armor=f"{armor_r} %" if armor_r else EMPTY,
                    helmet=f"{helmet_r} %" if helmet_r else EMPTY,
                ),
            )
            yield StatInfo(
                code=code_t,
                label=label_t,
                lvalue=value_t,
                rvalue=None,
                css=css_t,
                rate=None,
                prefix=None,
                suffix=None,
                title=title_t if css_t else None,
            )
            yield StatInfo(
                code=code_r,
                label=label_r,
                lvalue=value_r,
                rvalue=None,
                css=css_r,
                rate=None,
                prefix=None,
                suffix=" %",
                title=title_r if css_r else None,
            )

    @property
    def all_stats(self) -> Iterable[Stats]:
        """
        Retourne toutes les statistiques du personnage
        """
        yield from self.special
        yield from self.skills
        yield from self.general_stats
        yield from self.secondary_stats
        yield from self.resistances

    @property
    def current_charge(self) -> float:
        """
        Retourne la charge totale de l'équipement du personnage
        """
        if self.has_stats:
            return self.charge
        return (
            self.equipments.aggregate(
                charge=Sum(F("quantity") * F("item__weight"), output_field=models.FloatField())
            ).get("charge")
            or 0.0
        )

    @property
    def used_skill_points(self) -> float:
        """
        Retourne le nombre de points de compétences utilisées
        """
        return sum(gv(self, skill) * (1 if skill in self.tag_skills else 2) for skill in LIST_SKILLS)

    @property
    def next_required_experience(self) -> int:
        """
        Retourne le nombre de points d'expérience nécessaires pour passer au niveau suivant
        """
        return sum(level * BASE_XP for level in range(1, self.level + 1))

    @property
    def previous_required_experience(self) -> int:
        """
        Retourne le nombre de points d'expérience nécessaires pour le niveau précédent
        """
        return sum(level * BASE_XP for level in range(1, self.level))

    @property
    def required_experience(self) -> int:
        """
        Retourne le nombre de points d'expérience nécessaires pour passer au niveau suivant
        """
        return self.next_required_experience - self.experience

    def get_need_label(self, need: str, value: Optional[Union[int, float]] = None) -> str:
        """
        Retourne le libellé relatif au niveau d'un besoin
        :param need: Code du besoin
        :param value: Valeur du besoin en question
        :return: Libellé
        """
        value = gv(self, need, 0.0) if value is None else value
        labels, effects = {
            STATS_RADS: (RADS_LABELS, RADS_EFFECTS),
            STATS_THIRST: (THIRST_LABELS, THIRST_EFFECTS),
            STATS_HUNGER: (HUNGER_LABELS, HUNGER_EFFECTS),
            STATS_SLEEP: (SLEEP_LABELS, SLEEP_EFFECTS),
            STATS_CARRY_WEIGHT: (CARRY_WEIGHT_LABELS, CARRY_WEIGHT_EFFECTS),
        }[need]
        label = None
        for (mini, maxi), label in labels.items():
            if (mini or 0) <= value < (maxi or float("inf")):
                break
        for (mini, maxi), modifiers in effects.items():
            if (mini or 0) <= value < (maxi or float("inf")):
                break
        effects = ", ".join(
            f"{modifier} {LIST_ALL_STATS[stats]}" for stats, (modifier, mini, maxi) in modifiers.items()
        )
        effects = effects or _("aucun malus")
        if label:
            return f"{label} ({effects})"
        return effects

    @property
    def label_rads(self) -> str:
        """
        Libellé du niveau de rads
        """
        return self.get_need_label(STATS_RADS)

    @property
    def label_thirst(self) -> str:
        """
        Libellé du niveau de soif
        """
        return self.get_need_label(STATS_THIRST)

    @property
    def label_hunger(self) -> str:
        """
        Libellé du niveau de faim
        """
        return self.get_need_label(STATS_HUNGER)

    @property
    def label_sleep(self) -> str:
        """
        Libellé du niveau de sommeil
        """
        return self.get_need_label(STATS_SLEEP)

    @property
    def labels(self):
        return {
            STATS_RADS: self.label_rads,
            STATS_THIRST: self.label_thirst,
            STATS_HUNGER: self.label_hunger,
            STATS_SLEEP: self.label_sleep,
        }

    @property
    def modifiers(self):
        for stats_name, value in (self.stats.modifiers or {}).items():
            yield stats_name, LIST_ALL_STATS.get(stats_name), value

    def modify_value(self, name: str, value: Union[int, float]) -> Union[int, float]:
        """
        Permet de modifier la valeur d'une statistique
        :param name: Nom de la statistique
        :param value: Valeur
        :return: Valeur actuelle
        """
        value = gv(self, name, 0) + value
        sv(self, name, value)
        return value

    def add_experience(self, amount: int = 0, save: bool = True) -> Tuple[int, int, bool]:
        """
        Ajoute de l'expérience à ce personnage
        :param amount: Quantité d'expérience ajoutée
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Niveau actuel, expérience requise jusqu'au niveau suivant
        """
        level_up = False
        if amount:
            previous_level = self.level
            self.experience += amount
            if save:
                self.save()
            level_up = self.level > previous_level
        return self.level, self.required_experience, level_up

    def check_level(self) -> Tuple[int, int]:
        """
        Vérification du niveau en fonction de l'expérience
        :return: Niveau actuel, expérience requise jusqu'au niveau suivant
        """
        level = 1
        needed_xp = BASE_XP
        while self.experience >= needed_xp:
            level += 1
            needed_xp += level * BASE_XP
            if self.level >= level:
                continue
            self.level += 1
            self.skill_points += self.stats.skill_points_per_level
            if self.stats.perk_rate and not self.level % self.stats.perk_rate:
                self.perk_points += 1
            if not self.has_stats:
                self.max_health += self.stats.hit_points_per_level
            self.health += self.stats.hit_points_per_level
        return level, needed_xp

    def randomize_special(self, points: int = 40, save: bool = True, **kwargs) -> None:
        """
        Randomise le S.P.E.C.I.A.L. du personnage
        :param points: Nombre de points à répartir
        :param save: Sauvegarde le personnage ?
        :return: Rien
        """
        points = points or 40
        race = RACES_STATS.get(self.race) or RACES_STATS.get(RACE_HUMAN)
        points_min = points_max = 0
        for stat in LIST_SPECIALS:
            bonus, mini, maxi = race.get(stat, (0, 1, 10))
            points_min += mini
            points_max += maxi
        points = max(min(points, points_max), points_min)
        special = {}
        for idx, stat in enumerate(LIST_SPECIALS):
            bonus, mini, maxi = race.get(stat, (0, 1, 10))
            special[stat] = randint(mini, maxi)
        left = points - sum(special.values())
        while left:
            shift = -1 if left < 0 else 1
            for stat, value in sorted(special.items(), key=lambda e: e[1] * shift):
                bonus, mini, maxi = race.get(stat, (0, 1, 10))
                special[stat] = max(min(value + shift, maxi), mini)
                left = points - sum(special.values())
                if not left:
                    break
        for key, value in special.items():
            sv(self, key, value)
        # Reset health and action points to their maximum
        self.heal(save=save)

    def randomize_stats(self, level: int = None, balance: int = 0, save: bool = True, **kwargs) -> None:
        """
        Randomise les statistiques d'un personnage jusqu'à un certain niveau
        :param level: Niveau du personnage à forcer
        :param balance: Pourcentage des points à répartir sur les spécialités
        :param save: Sauvegarde le personnage ?
        :return: Rien
        """
        # Reset stats
        if self.has_stats:
            self.skill_points = self.perk_points = self.max_health = 0
            for skill in LIST_SKILLS:
                sv(self, skill, 0)
        # Experience points for the targeted level
        level = level or self.level or 1
        self.level = 1
        self.experience = sum((lvl - 1) * BASE_XP for lvl in range(2, level + 1))
        self.check_level()
        # Randomly distribute a fraction of the skill points on tag skills
        skill_points = self.skill_points - self.used_skill_points
        if self.tag_skills:
            for i in range(int(skill_points * (balance / 100))):
                self.modify_value(choice(self.tag_skills), 1)
                skill_points -= 1
        # Randomly distribute remaining skill points on other skills
        other_skills = list(set(LIST_SKILLS) - set(self.tag_skills)) if balance else list(LIST_SKILLS)
        while skill_points > 0:
            skill = choice(other_skills)
            self.modify_value(skill, 1)
            skill_points -= 1 if skill in self.tag_skills else 2
        # Reset health and action points to their maximum
        self.heal(save=save)

    def equip(
        self,
        armor: "Item" = None,
        armor_min_condition: int = 100,
        armor_max_condition: int = 100,
        helmet: "Item" = None,
        helmet_min_condition: int = 100,
        helmet_max_condition: int = 100,
        weapon: "Item" = None,
        weapon_min_condition: int = 100,
        weapon_max_condition: int = 100,
        ammo: "Item" = None,
        ammo_min_count: int = 10,
        ammo_max_count: int = 20,
        **kwargs,
    ) -> None:
        """
        Permet d'équiper rapidement un personnage avec une armure, un casque, une arme et des munitions
        :param armor: Armure
        :param armor_min_condition: Condition minimale de l'armure
        :param armor_max_condition: Condition maximale de l'armure
        :param helmet: Casque
        :param helmet_min_condition: Condition minimale du casque
        :param helmet_max_condition: Condition maximale du casque
        :param weapon: Arme
        :param weapon_min_condition: Condition minimale de l'arme
        :param weapon_max_condition: Condition maximale de l'arme
        :param ammo: Munition
        :param ammo_min_count: Nombre minimal de munitions
        :param ammo_max_count: Nombre maximal de munitions
        :return: Rien
        """
        equiped_weapon = None
        items = (
            (ITEM_ARMOR, armor, armor_min_condition, armor_max_condition),
            (ITEM_HELMET, helmet, helmet_min_condition, helmet_max_condition),
            (ITEM_WEAPON, weapon, weapon_min_condition, weapon_max_condition),
        )
        for slot, item, mini, maxi in items:
            if not item:
                continue
            if isinstance(item, (int, str)):
                item = Item.objects.get(id=item)
            equipment = Equipment.objects.create(
                character=self,
                item=item,
                slot=slot,
                quantity=1,
                condition=round(randint(mini, maxi) / 100.0, 0),
            )
            if slot == ITEM_WEAPON:
                equiped_weapon = equipment
        if ammo:
            if isinstance(ammo, (int, str)):
                ammo = Item.objects.get(id=ammo)
            Equipment.objects.create(
                character=self,
                item=ammo,
                slot=ITEM_AMMO,
                quantity=randint(ammo_min_count, ammo_max_count),
                condition=None,
            )
        if equiped_weapon and ammo:
            equiped_weapon.reload(is_action=False)

    def generate_stats(self, reset: bool = True, save: bool = True, **kwargs) -> None:
        """
        Génère définitivement les statistiques secondaires et les affecte au personnage
        :param reset: Réinitialise les compétences à 0 ?
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Rien
        """
        if reset:
            for stats_name in LIST_NON_SPECIAL_STATS:
                sv(self, stats_name, 0)
        stats = Stats.get(self)
        self.skill_points = 0
        for stats_name, stats_value in dataclasses.asdict(stats).items():
            if stats_name == "modifiers":
                continue
            if stats_name in LIST_SKILLS:
                self.skill_points += stats_value * (2, 1)[stats_name in self.tag_skills]
            sv(self, stats_name, stats_value)
        self.heal(save=save)

    def heal(
        self,
        health: bool = True,
        action_points: bool = True,
        needs: bool = True,
        save: bool = True,
    ):
        """
        Soigne la santé, réinitialise les points d'action et réduit les besoins
        :param health: Soigner la santé ?
        :param action_points: Réinitialiser les points d'action ?
        :param needs: Réduire les besoins ?
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Rien
        """
        if health:
            self.health = self.stats.max_health
        if action_points:
            self.action_points = self.stats.max_action_points
        if needs:
            for stats_name, formula in COMPUTED_NEEDS:
                sv(self, stats_name, 0)
        self.is_active = True  # Should be active if healed
        if save:
            self.save(reset=False)

    def update_needs(
        self,
        hours: float = 0.0,
        radiation: int = 0,
        resting: bool = True,
        needs: bool = True,
        save: bool = True,
    ) -> List["DamageHistory"]:
        """
        Mise à jour des besoins
        :param hours: Nombre d'heures passées
        :param radiation: Radioactivité actuelle (en rads / heure)
        :param resting: Personnage en train de se reposer ?
        :param needs: Active la perte des besoins (soif, faim, sommeil) ?
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Dégâts potentiels infligés
        """
        damages = []
        if needs and self.has_needs:
            for stats_name, formula in COMPUTED_NEEDS:
                rate = -2.0 if stats_name == STATS_SLEEP and (resting or self.is_resting) else 1.0
                rate *= NEEDS_RESTING_RATE if resting or self.is_resting else NEEDS_NORMAL_RATE
                self.modify_value(stats_name, formula(self.stats, self) * hours * rate)
        if radiation:
            damage = self.damage(
                raw_damage=radiation * hours,
                damage_type=DAMAGE_RADIATION,
                save=False,
                log=False,
            )
            damage.reason = _("environnement radioactif")
            damages.append(damage)
        healing_rate_modifier = HEALING_RATE_RESTING_MULT if (resting or self.is_resting) else 1.0
        print(healing_rate_modifier)
        self.regeneration += max(self.stats.healing_rate * (hours / 24.0) * healing_rate_modifier, 0.0)
        print(self.regeneration)
        if save:
            self.save(reset=False)
        return damages

    def roll(self, stats: str, modifier: int = 0, xp: bool = True, log: bool = True, reason: str = "") -> "RollHistory":
        """
        Réalise un jet de compétence pour un personnage
        :param stats: Code de la statistique
        :param modifier: Modificateur de jet éventuel
        :param xp: Gain d'expérience ?
        :param log: Historise le jet ?
        :param reason: Raison du jet ou de ses modificateurs (facultatif)
        :return: Historique de jet
        """
        history = RollHistory(character=self, level=self.level, stats=stats, modifier=modifier, reason=reason or "")
        history.game_date = self.campaign and self.campaign.current_game_date
        history.value = gv(self.stats, stats, 0)
        if stats in LIST_SPECIALS:
            history.roll = randint(1, 10)
            history.success = history.roll <= (history.value + history.modifier)
            history.critical = (
                history.roll <= CRITICAL_SUCCESS_D10 if history.success else history.roll >= CRITICAL_FAIL_D10
            )
        else:
            history.roll = randint(1, 100)
            roll_modifier = int(round((5 - self.stats.luck) * LUCK_ROLL_MULT, 0))
            history.success = history.roll <= (history.value + history.modifier)
            history.critical = (
                history.roll <= max(1, CRITICAL_SUCCESS_D100 - roll_modifier)
                if history.success
                else history.roll >= min(100, CRITICAL_FAIL_D100 - roll_modifier)
            )
        if xp:
            history.experience = XP_GAIN_ROLL[history.success] * self.level
            level, required_xp, history.level_up = self.add_experience(history.experience)
        if log:
            history.save()
        return history

    def loot(self, empty: bool = True) -> Optional[List["Loot"]]:
        """
        Transforme l'équipement de ce personnage en butin
        :param empty: Vide l'inventaire du joueur ?
        :return: Liste des butins
        """
        if not self.pk:
            return
        loots = []
        if self.money:
            self.campaign.money_loot += self.money
            self.campaign.save(update_fields=("money_loot",))
        for equipement in self.inventory.exclude(slot=""):
            equipement.equip(is_action=False)
        for equipement in self.inventory.filter(item__is_droppable=True):
            loots.append(
                Loot.create(
                    campaign=self.campaign,
                    item=equipement.item,
                    condition=equipement.condition,
                    quantity=equipement.quantity,
                )
            )
        if empty:
            self.inventory.delete()
            if self.money:
                self.money = 0
                self.save(update_fields=("money",))
        return loots

    def burst(
        self,
        targets: List[Tuple[Union["Character", int], int]],
        hit_chance_modifier: int = 0,
        weapon_type: str = WEAPON_TYPE_PRIMARY,
        is_action: bool = True,
        log: bool = True,
        simulation: bool = False,
        **kwargs,
    ) -> List["FightHistory"]:
        """
        Permet de lancer une attaque en rafale sur un groupe d'ennemis
        :param targets: Liste de personnages ciblés avec leur distance relative (en cases) pour chacun dans un tuple
        :param hit_chance_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param weapon_type: Type d'arme utilisé ("primary", "secondary", "grenade" ou "unarmed")
        :param is_action: Consomme les points d'action de l'attaquant ?
        :param log: Historise le combat ?
        :param simulation: Fait une simulation du combat ?
        :return: Liste d'historiques de combat
        """
        _assert(targets, _("Une attaque en rafale doit cibler au moins un personnage."))
        # Fetch characters for optimisation
        query = Character.objects.select_related("statistics")
        targets = [
            (
                target if isinstance(target, Character) else query.get(id=target),
                target_range,
            )
            for target, target_range in targets
        ]
        histories = []
        if weapon_type == WEAPON_TYPE_GRENADE:
            attacker_weapon_equipment = self.get_from_inventory(slot=ITEM_GRENADE)
            attacker_weapon = gv(attacker_weapon_equipment, "item", None)
            _assert(
                attacker_weapon and attacker_weapon_equipment.quantity != 0,
                _("L'attaquant ne possède pas ou plus de grenade."),
            )
            for hit_count, (target, target_range) in enumerate(targets):
                history = self.fight(
                    target,
                    weapon_type=weapon_type,
                    target_range=int(target_range),
                    hit_chance_modifier=hit_chance_modifier,
                    log=log,
                    simulation=simulation,
                    is_action=is_action,
                    is_burst=True,
                    hit_count=hit_count,
                    **kwargs,
                )
                histories.append(history)
        else:
            attacker_weapon_equipment = self.get_from_inventory(slot=ITEM_WEAPON)
            attacker_weapon = gv(attacker_weapon_equipment, "item", None)
            attacker_ammo_equipment = self.get_from_inventory(slot=ITEM_AMMO)
            attacker_ammo = gv(attacker_ammo_equipment, "item", None)
            _assert(
                attacker_weapon and attacker_weapon.burst_count != 0,
                _("L'attaquant ne possède pas d'arme ou celle-ci ne permet pas d'attaque en rafale."),
            )

            target, target_range, hit_count, dead_targets = None, 0, 0, set()
            for hit_count in range(attacker_weapon.burst_count):
                while not target or target in dead_targets:
                    target, target_range = choice(targets)
                history = self.fight(
                    target,
                    weapon_type=weapon_type,
                    target_range=int(target_range),
                    hit_chance_modifier=hit_chance_modifier,
                    attacker_weapon=attacker_weapon_equipment,
                    attacker_ammo=attacker_ammo_equipment,
                    log=log,
                    simulation=simulation,
                    is_action=is_action,
                    is_burst=True,
                    hit_count=hit_count,
                    **kwargs,
                )
                histories.append(history)
                if history.status in (STATUS_TARGET_DEAD, STATUS_TARGET_KILLED):
                    dead_targets.add(target)
                # Premature end of burst: removing remaining ammo and degrading weapon condition
                if history.stop_burst or len(targets) == len(dead_targets):
                    break
                target = None

            attacker_remaining_ammo = attacker_weapon.burst_count - hit_count + 1
            if attacker_remaining_ammo > 0:
                attacker_remaining_ammo = min(attacker_ammo_equipment.quantity, attacker_remaining_ammo)
                attacker_ammo_equipment.quantity -= attacker_remaining_ammo
                if not simulation:
                    attacker_ammo_equipment.save()
                if attacker_weapon.durability:
                    attacker_weapon_damage = (
                        attacker_remaining_ammo
                        * (1.0 / attacker_weapon.durability)
                        * (
                            1.0
                            - add(
                                gv(attacker_weapon, "condition_modifier", 0.0),
                                gv(attacker_ammo, "condition_modifier", 0.0),
                            ),
                        )
                    )
                    attacker_weapon_equipment.condition -= attacker_weapon_damage
            if not simulation:
                attacker_weapon_equipment.save()
        # Saves characters
        if not simulation:
            for history in histories:
                if history.defender.reward and history.damage and history.damage.damage_rate:
                    history.experience = int(history.defender.reward * history.damage.damage_rate)
                else:
                    history.experience = max(history.defender.level - self.level, 1) * XP_GAIN_BURST
                level, required_xp, history.level_up = self.add_experience(history.experience, save=False)
            for target, target_range in targets:
                target.save()
            self.save()
        return histories

    def fight(
        self,
        target: Union["Character", int],
        target_range: int = 1,
        target_part: BODY_PARTS = None,
        weapon_type: str = WEAPON_TYPE_PRIMARY,
        simulation: bool = False,
        hit_chance_modifier: int = 0,
        is_burst: bool = False,
        is_action: bool = False,
        hit_count: int = 0,
        log: bool = True,
        force_success: bool = False,
        force_critical: bool = False,
        force_raw_damage: bool = False,
        attacker_weapon: Optional["Equipment"] = None,
        attacker_ammo: Optional["Equipment"] = None,
        fail_target: Union["Character", int] = None,
        fail: bool = False,
        reason: str = "",
        **kwargs,
    ) -> Optional["FightHistory"]:
        """
        Calcul un round de combat entre deux personnages
        :param target: Personnage ciblé
        :param target_range: Distance (en cases) entre les deux personnages
        :param target_part: Partie du corps ciblée par l'attaquant (ou torse par défaut)
        :param weapon_type: Type d'arme utilisé ("primary", "secondary", "grenade" ou "unarmed")
        :param simulation: Fait une simulation du combat ?
        :param hit_chance_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param is_burst: Attaque en rafale ?
        :param is_action: Consomme les points d'action de l'attaquant ?
        :param hit_count: Compteur de coups lors d'une attaque en rafale
        :param log: Historise le combat ?
        :param force_success: Force le succès du coup ?
        :param force_critical: Force un coup critique ?
        :param force_raw_damage: Force les dégâts bruts ?
        :param attacker_weapon: Arme équipée pour l'attaque en rafale (optimisation)
        :param attacker_ammo: Munition équipée pour l'attaque en rafale (optimisation)
        :param fail_target: Cible secondaire en cas d'échec critique
        :param fail: Attaque donnée sur la cible secondaire en cas d'échec critique ?
        :param reason: Raison de l'attaque ou de ses modificateurs (facultatif)
        :return: Historique de combat
        """
        if not target:
            return
        target_range, is_burst = int(target_range), bool(is_burst)
        if isinstance(target, (int, str)):
            target = Character.objects.select_related("statistics").get(pk=target)
        history = FightHistory(
            attacker=self,
            attacker_level=self.level,
            defender=target,
            defender_level=target.level,
            range=target_range,
            burst=is_burst,
            hit_count=hit_count + 1,
            reason=reason or "",
        )
        history.game_date = self.campaign and self.campaign.current_game_date
        # Equipment
        is_grenade = False
        if weapon_type == WEAPON_TYPE_GRENADE:
            attacker_weapon_equipment = attacker_weapon or self.get_from_inventory(slot=ITEM_GRENADE)
            attacker_ammo_equipment = None
            _assert(
                attacker_weapon_equipment,
                _("L'attaquant ne possède pas ou plus de grenade."),
            )
            is_grenade = True
        elif weapon_type == WEAPON_TYPE_SECONDARY:
            attacker_weapon_equipment = attacker_weapon or self.get_from_inventory(secondary=True)
            attacker_ammo_equipment = None
        elif weapon_type == WEAPON_TYPE_UNARMED:
            attacker_weapon_equipment = attacker_ammo_equipment = None
        else:
            attacker_weapon_equipment = attacker_weapon or self.get_from_inventory(slot=ITEM_WEAPON)
            attacker_ammo_equipment = attacker_ammo or self.get_from_inventory(slot=ITEM_AMMO)
        attacker_weapon = history.attacker_weapon = gv(attacker_weapon_equipment, "item", None)
        attacker_ammo = history.attacker_ammo = gv(attacker_ammo_equipment, "item", None)
        # Fight conditions
        if target.health <= 0:
            history.status = STATUS_TARGET_DEAD
        elif not fail:
            if attacker_weapon:
                if attacker_weapon.clip_size and attacker_weapon_equipment.clip_count <= 0:
                    history.status = STATUS_NO_MORE_AMMO
                elif attacker_weapon.is_throwable and attacker_weapon_equipment.quantity <= 0:
                    if not is_grenade or (is_burst and not hit_count):
                        history.status = STATUS_NO_MORE_AMMO
            elif (
                attacker_weapon_equipment
                and attacker_weapon_equipment.condition is not None
                and attacker_weapon_equipment.condition <= 0.0
            ):
                history.status = STATUS_WEAPON_BROKEN
        # Action points
        ap_cost = 0
        if is_action and not fail:
            if not is_burst or is_grenade:
                ap_cost_type = "ap_cost_target" if target_part else "ap_cost_normal"
            else:
                ap_cost_type = "ap_cost_burst"
            ap_cost = gv(attacker_weapon, ap_cost_type, None)
            ap_cost = ap_cost if ap_cost is not None else AP_COST_FIGHT
            ap_cost += self.stats.ap_cost_modifier
            if ap_cost > self.action_points:
                history.status = STATUS_NOT_ENOUGH_AP
        # Premature end of fight
        if history.status:
            if log and not simulation:
                history.save()
            return history
        # Targeted body part modifiers and equipment
        roll_modifier = int(round((5 - self.stats.luck) * LUCK_ROLL_MULT, 0))
        body_part = target_part
        if not target_part:
            for body_part, chance in BODY_PARTS_RANDOM_CHANCES:
                if randint(1, 100 + roll_modifier) <= chance:
                    break
        history.body_part = body_part = body_part or PART_TORSO
        (  # Body part hit/critical modifiers
            ranged_hit_modifier,
            melee_hit_modifier,
            critical_modifier,
            critical_damage_modifier,
        ) = BODY_PARTS_MODIFIERS[history.body_part]
        armor_slot = ITEM_HELMET if body_part in (PART_EYES, PART_HEAD) else ITEM_ARMOR
        defender_armor_equipment = target.get_from_inventory(slot=armor_slot)
        defender_armor = history.defender_armor = gv(defender_armor_equipment, "item", None)
        # Base hit chance
        is_melee = not attacker_weapon or attacker_weapon.is_melee
        attacker_skill = gv(attacker_weapon, "skill", SKILL_UNARMED)
        attacker_hit_chance = gv(self.stats, attacker_skill, 0)  # Base skill
        if not attacker_hit_chance and not self.has_stats:
            attacker_hit_chance = self.level * LEVELED_STATS_MULT  # Base skill level for creatures
        # Accuracy modifier for one-hand or two-hands weapons
        hands_hit_chance = [
            0,
            self.stats.one_hand_accuracy,
            self.stats.two_hands_accuracy,
        ]
        attacker_hit_chance += hands_hit_chance[gv(attacker_weapon, "hands", 0)]
        attacker_hit_chance += min(
            MIN_STRENGTH_MALUS
            * (  # Accuracy malus if below required strength
                self.stats.strength - gv(attacker_weapon, "min_strength", 0)
            ),
            0,
        )
        attacker_hit_chance += min(
            MIN_SKILL_MALUS
            * (  # Accuracy malus if below required skill
                gv(self.stats, attacker_skill, 0) - gv(attacker_weapon, "min_skill", 0)
            ),
            0,
        )
        # Weapon/ammo range modifiers (min & max)
        attacker_range_type = "{}_burst_range" if is_burst else "{}_range"
        attacker_min_range = (
            0
            if not attacker_weapon
            else max(
                add(
                    gv(attacker_weapon, attacker_range_type.format("min"), 0),
                    gv(attacker_ammo, attacker_range_type.format("min"), 0),
                ),
                0,
            )
        )
        attacker_max_range = (
            1
            if not attacker_weapon
            else max(
                add(
                    gv(attacker_weapon, attacker_range_type.format("max"), 0),
                    gv(attacker_ammo, attacker_range_type.format("max"), 0),
                ),
                1,
            )
        )
        # Ranged weapon accuracy modifiers
        if attacker_weapon and attacker_weapon.attack_mode in RANGE_MODIFIERS:
            weapon_range_modifier = RANGE_MODIFIERS.get(attacker_weapon.attack_mode)
            attacker_hit_chance += (self.stats.perception - 2) * weapon_range_modifier
            attacker_hit_chance -= max(attacker_min_range - target_range, 0) * RANGED_CLOSE_MALUS_MULT
            attacker_hit_chance -= max(target_range - attacker_min_range, 0) * RANGED_MALUS_MULT
        # Increase hit chance of weapons
        elif not is_melee:
            attacker_range_stats = SPECIAL_STRENGTH if attacker_weapon.is_throwable else SPECIAL_PERCEPTION
            attacker_hit_chance += RANGED_NORMAL_MULT * gv(self.stats, attacker_range_stats, 0)
            attacker_hit_chance -= target_range * RANGED_MALUS_MULT
        # Targeted hit chance modifier
        if target_part:  # Hit chance malus are only for targeted shot
            attacker_hit_chance += melee_hit_modifier if is_melee else ranged_hit_modifier
        # Hit chance modifiers
        attacker_hit_chance += gv(attacker_weapon, "hit_chance_modifier", 0)  # Weapon hit_count chance modifier
        attacker_hit_chance += gv(attacker_ammo, "hit_chance_modifier", 0)  # Ammo hit_count chance modifier
        attacker_hit_chance *= gv(attacker_weapon_equipment, "condition", 1.0) or 1.0  # Weapon condition
        defender_armor_class = gv(defender_armor, "armor_class", 0) + target.stats.armor_class
        defender_armor_class -= int((5 - target.stats.luck) * LUCK_ROLL_MULT)  # Luck-based armor class
        defender_armor_class *= max(
            (
                1.0
                + add(  # Armor class modifiers by weapon/ammo
                    gv(attacker_weapon, "armor_class_modifier", 0),
                    gv(attacker_ammo, "armor_class_modifier", 0),
                )
                / 100.0
            ),
            0.0,
        )
        attacker_hit_chance -= defender_armor_class  # Defender armor class modifier
        attacker_hit_chance += int(hit_chance_modifier)  # Other modifiers
        attacker_hit_chance = max(min(attacker_hit_chance, MAX_HIT_CHANCE), 0)
        # Force hit chance to null if target is farther than weapon range
        if target_range > attacker_max_range:
            attacker_hit_chance = 0
        # Hit roll and history
        history.hit_modifier = int(hit_chance_modifier)
        history.hit_chance = int(round(attacker_hit_chance))
        history.status = STATUS_HIT_FAILED
        history.hit_roll = randint(1, 100)
        history.success = bool(force_success) or history.hit_roll <= history.hit_chance
        history.critical = bool(force_critical) or history.hit_roll >= min(100, CRITICAL_FAIL_D100 - roll_modifier)
        if history.success:
            # Apply damage
            attacker_damage_type = (  # Damage type
                gv(attacker_ammo, "damage_type", None) or gv(attacker_weapon, "damage_type", None) or DAMAGE_NORMAL
            )
            damage = 0
            for item in (attacker_weapon, attacker_ammo):
                if not item:
                    continue
                damage += item.calculated_damage
            damage += self.stats.melee_damage if is_melee else 0
            damage *= max(
                (
                    1.0
                    + sum(  # Damage modifiers (in %) by weapon/ammo
                        (
                            self.stats.damage_modifier,
                            gv(attacker_weapon, "damage_modifier", 0),
                            gv(attacker_ammo, "damage_modifier", 0),
                        )
                    )
                    / 100.0
                ),
                0.0,
            )
            # Critical chance
            critical_chance = gv(self.stats, "critical_chance", 0)  # Base critical chance
            critical_chance += critical_modifier  # Critical chance modifiers by body part
            critical_chance += add(  # Critical chance modifiers by weapon/ammo
                gv(attacker_weapon, "critical_modifier", 0),
                gv(attacker_ammo, "critical_modifier", 0),
            )
            history.status = STATUS_HIT_SUCCEED
            history.critical = bool(force_critical) or history.hit_roll <= critical_chance
            # Critical damage
            if history.critical:
                damage *= max(
                    (
                        1.0
                        + sum(  # Critical damage modifiers (in %) by weapon/ammo
                            (
                                self.stats.critical_damage,
                                critical_damage_modifier,
                                gv(attacker_weapon, "critical_damage_modifier", 0),
                                gv(attacker_ammo, "critical_damage_modifier", 0),
                                ((self.stats.strength * 10) if is_melee else 0),
                            )
                        )
                        / 100.0
                    ),
                    0.0,
                )
                damage += add(  # Critical damage modifiers (in raw damage) by weapon/ammo
                    gv(attacker_weapon, "critical_damage", 0),
                    gv(attacker_ammo, "critical_damage", 0),
                )
                critical_raw_chance = self.stats.critical_raw_chance + add(  # Raw damage type chance modifiers
                    gv(attacker_weapon, "critical_raw_modifier", 0),
                    gv(attacker_ammo, "critical_raw_modifier", 0),
                )
                critical_raw_damage = force_raw_damage or randint(1, 100) <= critical_raw_chance
                if attacker_damage_type not in LIST_NON_DAMAGE and critical_raw_damage:
                    attacker_damage_type = DAMAGE_RAW
            damage = max(damage, 0)  # Avoid negative damage
            threshold_modifier = add(  # Threshold modifiers from weapon/ammo
                gv(attacker_weapon, "threshold_modifier", 0),
                gv(attacker_ammo, "threshold_modifier", 0),
            )
            threshold_rate_modifier = add(  # Threshold rate modifiers from weapon/ammo
                gv(attacker_weapon, "threshold_rate_modifier", 0),
                gv(attacker_ammo, "threshold_rate_modifier", 0),
            )
            resistance_modifier = add(  # Resistance modifiers from weapon/ammo
                gv(attacker_weapon, "resistance_modifier", 0),
                gv(attacker_ammo, "resistance_modifier", 0),
            )
            history.damage = target.damage(
                raw_damage=damage,
                damage_type=attacker_damage_type,
                body_part=body_part,
                save=not is_burst,
                threshold_modifier=threshold_modifier,
                threshold_rate_modifier=threshold_rate_modifier,
                resistance_modifier=resistance_modifier,
                simulation=simulation,
            )
            if target.health <= 0:
                history.status = STATUS_TARGET_KILLED
            # On hit_count effects
            if not simulation:
                damages = []
                for item in (attacker_weapon, attacker_ammo, defender_armor):
                    if not item:
                        continue
                    for effect in item.effects.all():
                        character_effect = effect.affect(target)
                        if character_effect:
                            damages.extend(character_effect)
                damages.extend(target.apply_effects())  # Apply effects immediatly
        # If critical fail and secondary target defined
        if not history.success and history.critical and fail_target:
            history.fail = self.fight(
                target=fail_target,
                target_range=0,
                force_success=True,
                fail=True,
                log=log,
                weapon_type=weapon_type,
                simulation=simulation,
                attacker_weapon=attacker_weapon_equipment,
                attacker_ammo=attacker_ammo_equipment,
            )
        # Clip count & weapon condition
        if attacker_weapon_equipment and attacker_weapon and not fail:
            if is_grenade and (not is_burst or not hit_count):
                attacker_weapon_equipment.quantity -= 1
            elif not is_grenade and attacker_weapon.is_throwable:
                attacker_weapon_equipment.drop(quantity=1, save=False)
            elif attacker_weapon.clip_size:
                attacker_weapon_equipment.clip_count -= 1
            if attacker_weapon.durability and attacker_weapon.is_repairable:
                attacker_weapon_damage = (1.0 / attacker_weapon.durability) * (
                    1.0
                    - add(  # Weapon/ammo condition modifier
                        gv(attacker_weapon, "condition_modifier", 0.0),
                        gv(attacker_ammo, "condition_modifier", 0.0),
                    )
                )
                attacker_weapon_equipment.condition -= attacker_weapon_damage
            if not is_burst and not simulation:
                # Optimisation: don't save if weapon is provided by burst attack
                attacker_weapon_equipment.save()
        # Save character and return history
        if not simulation:
            self.action_points -= max(ap_cost, 0)
            if not is_burst and not fail:
                # Experience only on single shot
                if target.reward and history.damage and history.damage.damage_rate:
                    history.experience = int(target.reward * history.damage.damage_rate)
                else:
                    history.experience = max(target.level - self.level, 1) * XP_GAIN_FIGHT[history.success]
                level, required_xp, history.level_up = self.add_experience(history.experience, save=False)
                self.save()
            if log and not simulation:
                history.save()
        return history

    def damage(
        self,
        raw_damage: float = 0.0,
        min_damage: int = 0,
        max_damage: int = 0,
        damage_type: str = "",
        body_part: str = "",
        threshold_modifier: int = 0,
        threshold_rate_modifier: int = 0,
        resistance_modifier: int = 0,
        save: bool = True,
        log: bool = True,
        simulation: bool = False,
        reason: str = "",
    ) -> "DamageHistory":
        """
        Inflige des dégâts au personnage
        :param raw_damage: Dégâts bruts
        :param min_damage: Dégâts minimum
        :param max_damage: Dégâts maximum
        :param damage_type: Type des dégâts
        :param body_part: Partie du corps touchée
        :param threshold_modifier: Modificateur d'absorption de dégâts (appliqué à l'armure et au personnage)
        :param threshold_rate_modifier: Modificateur de taux d'absorption de dégâts (appliqué à l'armure et au personnage)
        :param resistance_modifier: Modificateur de résistance aux dégâts (appliqué à l'armure et au personnage)
        :param save: Sauvegarder les modifications sur le personnage ?
        :param log: Historise les dégâts ?
        :param simulation: Fait une simulation des dégâts ?
        :param reason: Raison de l'origine des dégâts (facultatif)
        :return: Nombre de dégâts
        """
        threshold_rate_modifier = round(threshold_rate_modifier / 100.0, 2)
        damage_type, body_part = damage_type or DAMAGE_NORMAL, body_part or ""
        _assert(
            min_damage <= max_damage,
            _("Les bornes de dégâts min. et max. ne sont pas correctes."),
        )
        if not body_part and damage_type in LIST_NON_DAMAGE:
            roll_modifier = int(round((5 - self.stats.luck) * LUCK_ROLL_MULT, 0))
            for body_part, chance in BODY_PARTS_RANDOM_CHANCES:
                if randint(1, 100 + roll_modifier) <= chance:
                    break
        body_part = "" if damage_type in LIST_NON_DAMAGE else body_part
        history = DamageHistory(
            character=self,
            level=self.level,
            damage_type=damage_type,
            body_part=body_part,
            raw_damage=raw_damage,
            min_damage=min_damage,
            max_damage=max_damage,
            reason=reason,
        )
        history.game_date = self.campaign and self.campaign.current_game_date
        # Base damage
        total_damage = raw_damage + randint(min_damage, max_damage)
        base_damage = history.base_damage = total_damage
        # Character already KO
        if damage_type != HEAL_HEALTH and self.health <= 0:
            return history
        damage_threshold, damage_resistance = 0, 0.0
        if damage_type not in LIST_NON_DAMAGE:
            # Armor threshold and resistance
            to_head = damage_type == DAMAGE_GAZ_INHALED or body_part in (
                PART_EYES,
                PART_HEAD,
            )
            armor_slot = None if not body_part else ITEM_HELMET if to_head else ITEM_ARMOR
            armor_equipment = self.get_from_inventory(slot=armor_slot) if armor_slot else None
            armor = history.armor = gv(armor_equipment, "item", None)
            armor_damage = 0
            if armor and armor_equipment:
                armor_threshold = (armor.get_threshold(damage_type) * armor_equipment.condition) + threshold_modifier
                armor_threshold = round(armor_threshold * max(1.0 + threshold_rate_modifier, 0.0), 2)
                armor_resistance = armor.get_resistance(damage_type) * armor_equipment.condition
                armor_resistance *= 1.0 + (resistance_modifier / 100.0)
                armor_resistance = round(min(max(0, armor_resistance), MAX_DAMAGE_RESISTANCE), 2)
                total_damage = max(total_damage - max(armor_threshold, 0), 0)
                total_damage *= max(1.0 - min(round(armor_resistance / 100.0, 2), 1.0), 0.0)
                armor_damage = 0
                if armor.durability and damage_type in LIST_PHYSICAL_DAMAGE:
                    armor_condition_modifier = 1.0 - armor.condition_modifier
                    armor_damage = max(
                        ((base_damage - total_damage) / armor.durability) * armor_condition_modifier,
                        0,
                    )
                # History
                history.armor_threshold = armor_threshold
                history.armor_resistance = armor_resistance
                history.armor_damage = armor_damage
            # Condition decrease on armor
            if history.armor_damage > 0 and not simulation:
                armor_equipment.condition -= armor_damage
                armor_equipment.save()
            # Self threshold and resistance
            damage_threshold = self.stats.get_threshold(damage_type)
            damage_resistance = self.stats.get_resistance(damage_type)
            if damage_type in LIST_PHYSICAL_DAMAGE:
                damage_threshold += self.stats.damage_threshold
                damage_resistance += self.stats.damage_resistance
            damage_threshold += threshold_modifier
            damage_threshold = round(damage_threshold * threshold_rate_modifier, 2)
            damage_resistance *= 1.0 + (resistance_modifier / 100.0)
            damage_resistance = round(min(max(0, damage_resistance), MAX_DAMAGE_RESISTANCE), 2)
        total_damage = max(total_damage - max(damage_threshold, 0), 0)
        total_damage *= max(1.0 - round(damage_resistance / 100.0, 2), 0.0)
        total_damage *= (1.0, -1.0)[history.is_heal]
        total_damage = int(round(total_damage))
        # Apply damage on self
        if total_damage:
            if damage_type in (DAMAGE_RADIATION, HEAL_RADIATION):
                self.rads += total_damage
            elif damage_type in (DAMAGE_THIRST, HEAL_THIRST):
                self.thirst += total_damage
            elif damage_type in (DAMAGE_HUNGER, HEAL_HUNGER):
                self.hunger += total_damage
            elif damage_type in (DAMAGE_SLEEP, HEAL_SLEEP):
                self.sleep += total_damage
            elif damage_type in (ADD_MONEY, REMOVE_MONEY):
                self.money -= total_damage
            elif damage_type in (ADD_KARMA, REMOVE_KARMA):
                self.karma -= total_damage
            else:
                history.damage_rate = round(min(self.health, abs(total_damage)) / self.stats.max_health, 2)
                self.health -= total_damage
            if save and not simulation:
                self.save()
        # History
        history.damage_threshold = damage_threshold
        history.damage_resistance = damage_resistance
        history.real_damage = total_damage
        if log and not simulation:
            history.save()
        return history

    def apply_effects(self, save: bool = True) -> List["DamageHistory"]:
        """
        Applique les effets actifs du personnage
        :param save: Sauvegarde les données relatives aux personnages
        :return: Liste des dégâts éventuellement subis
        """
        damages, next_effects = [], []
        for effect in self.effects:
            damages.extend(effect.apply(self, save=save))
            next_effects.extend(effect.next_effects)
            effect.next_effects.clear()
        while next_effects:
            effects = next_effects[:]
            next_effects.clear()
            for effect in effects:
                damages.extend(effect.apply(self, save=save))
                next_effects.extend(effect.next_effects)
                effect.next_effects.clear()
        return damages

    def duplicate(
        self,
        equipments: bool = True,
        effects: bool = True,
        is_active: bool = True,
        campaign: Union[int, "Campaign"] = None,
        name: str = None,
    ) -> "Character":
        """
        Duplique ce personnage
        :param equipments: Duplique également les équipements
        :param effects: Duplique également les effets
        :param is_active: Active le personnage ?
        :param campaign: Campagne de destination
        :param name: Nouveau nom
        :return: Personnage
        """
        # _assert(self.pk, _("Ce personnage doit être préalablement enregistré avant d'être dupliqué."))
        character_id = self.pk
        self.pk = None
        self.name = name or self.name
        self.campaign_id = gv(campaign, "pk", campaign) or self.campaign_id
        self.is_active = is_active
        self.save(force_insert=True)
        if equipments and character_id:
            for equipment in Equipment.objects.filter(character_id=character_id):
                equipment.pk, equipment.id, equipment.character_id = None, None, self.pk
                equipment.save(force_insert=True)
        if effects and character_id:
            for effect in CharacterEffect.objects.filter(character_id=character_id):
                effect.pk, effect.id, effect.character_id = None, None, self.pk
                effect.save(force_insert=True)
        return self

    def levelup(self, stats: str, value: int = 0, save: bool = True, **kwargs) -> int:
        """
        Permet d'augmenter le niveau d'une compétence
        :param stats: Code de la compétence
        :param value: Valeur
        :param save: Sauvegarde le personnage ?
        :return: Valeur courante
        """
        _assert(stats in LIST_SKILLS, _("Cette compétence ne peut être améliorée."))
        _assert(
            self.skill_points + (value * (2, 1)[stats in self.tag_skills]) >= self.used_skill_points,
            _("Ce personnage n'a pas assez de points de compétences."),
        )
        self.modify_value(stats, value)
        if save:
            self.save(**kwargs)
        return gv(self, stats)

    def save(self, *args, reset: bool = True, **kwargs):
        """
        Sauvegarde du personnage
        :param reset: Réinitialise le cache ?
        """
        # Regeneration
        if self.regeneration >= 1.0:
            healing = int(self.regeneration)
            self.regeneration -= healing
            self.health = self.health + healing
        # Detect if character is at max health/ap in case of level up or stats modifications
        has_max_health = not self.pk or self.health == self.stats.max_health
        has_max_action_points = not self.pk or self.action_points == self.stats.max_action_points
        # Check and increase level
        self.check_level()
        # Remove stats in cache
        if reset:
            Character.reset_stats(self)
        newly_created = not self.pk
        if not newly_created:
            # Fixing health and action points
            self.health = (
                self.stats.max_health
                if has_max_health and self.health > 0
                else max(0, min(self.health, self.stats.max_health))
            )
            self.action_points = (
                self.stats.max_action_points
                if has_max_action_points and self.action_points > 0
                else max(0, min(self.action_points, self.stats.max_action_points))
            )
            # Remove current character on campaign if character is added or removed
            for campaign_id in self.modified.get("campaign_id") or []:
                if not campaign_id:
                    continue
                Campaign.objects.filter(id=campaign_id).update(current_character=None)
        # Loot character if NPC
        if not newly_created and self.is_active and self.health <= 0 and not self.is_player:
            if self.loot_on_death:
                self.loot(empty=True)
            self.is_active = False
        # Fixing min value for needs
        self.rads = min(max(self.rads, 0), 1000)
        self.thirst = min(max(self.thirst, 0), 1000)
        self.hunger = min(max(self.hunger, 0), 1000)
        self.sleep = min(max(self.sleep, 0), 1000)
        self.money = max(self.money, 0)
        super().save(*args, **kwargs)
        if newly_created:
            self.heal()

    def get_absolute_url(self):
        """
        Retourne l'URL vers la page du personnage
        """
        from django.urls import reverse

        return reverse("fallout:character", args=[str(self.pk)])

    def __str__(self) -> str:
        if self.title:
            return f"{self.name} ({self.title})"
        return self.name

    class Meta:
        verbose_name = _("personnage")
        verbose_name_plural = _("personnages")


# Add property on Character for each stats
for stats, name in EDITABLE_STATS:

    def current_stats(self, stats=stats):
        return gv(self.stats, stats, None)

    current_stats.short_description = name
    sv(Character, "current_" + stats, property(current_stats))


class Modifier(CommonModel):
    """
    Modificateur de statistique
    """

    stats = models.CharField(max_length=30, choices=ALL_STATS, verbose_name=_("statistique"))
    raw_value = models.SmallIntegerField(default=0, verbose_name=_("valeur brute"))
    min_value = models.SmallIntegerField(default=0, verbose_name=_("valeur min."))
    max_value = models.SmallIntegerField(default=0, verbose_name=_("valeur max."))
    current_value = None

    @property
    def calculated_value(self) -> int:
        """
        Calcul unitaire de la valeur de modificateur
        :return: Valeur de modificateur
        """
        return randint(self.min_value, self.max_value) + self.raw_value

    @property
    def label_modifier(self) -> str:
        """
        Retourne le libellé de la valeur du modificateur
        :return: Représentation de la valeur du modificateur
        """
        value = ""
        if self.current_value is not None:
            value = f"+{self.current_value}" if self.current_value > 0 else str(self.current_value)
        else:
            if self.min_value or self.max_value:
                if self.max_value < 0:
                    value = f"-({abs(self.max_value)}-{abs(self.min_value)})"
                else:
                    value = f"{self.min_value}-{self.max_value}"
            if self.raw_value:
                raw_value = f"+{self.raw_value}" if self.raw_value >= 0 else str(self.raw_value)
                value = f"{value} ({raw_value})" if value else raw_value
        return value

    @property
    def label(self) -> str:
        """
        Retourne le libellé du modificateur
        :return: Représentation du modificateur
        """
        return f"{self.label_modifier} {self.get_stats_display()}"

    @property
    def message_level(self) -> str:
        """
        Niveau de message
        """
        return (messages.ERROR, messages.SUCCESS)[self.is_bonus]

    @property
    def is_bonus(self) -> bool:
        """
        Determine si le modificateur est un bonus ou un malus
        :return: Vrai si bonus, faux si malus
        """
        if self.stats in (STATS_RADS, STATS_HUNGER, STATS_THIRST, STATS_SLEEP):
            return self.calculated_value <= 0
        return self.calculated_value >= 0

    def get_calculated_value(self, fixed: bool = False) -> int:
        """
        Calcule la valeur du modificateur
        :param fixed: Fixe la valeur en mémoire
        :return: Valeur de modificateur
        """
        calculated_value = self.calculated_value
        if fixed:
            self.current_value = calculated_value
        return calculated_value

    def __str__(self) -> str:
        return self.label

    class Meta:
        abstract = True


class Damage(CommonModel):
    """
    Dégâts
    """

    damage_type = models.CharField(
        max_length=20,
        blank=True,
        choices=DAMAGES_TYPES,
        verbose_name=_("type de dégâts"),
    )
    min_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts min."))
    max_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts max."))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    body_part = models.CharField(max_length=10, blank=True, choices=BODY_PARTS, verbose_name=_("partie du corps"))

    @property
    def is_heal(self) -> bool:
        """
        Retourne si le type de dégâts est curatif ou non
        :return: Vrai si curatif, faux sinon
        """
        return self.damage_type in LIST_HEALS + (ADD_MONEY, ADD_KARMA)

    @property
    def calculated_damage(self) -> int:
        """
        Calcul unitaire des dégâts de base de l'objet
        :return: Nombre de dégâts de base
        """
        return randint(self.min_damage, self.max_damage) + self.raw_damage

    @property
    def label_damage(self) -> str:
        """
        Retourne le libellé des dégâts de l'arme ou de la munition
        :return: Représentation des dégâts ou rien si l'objet n'est pas une arme ou une munition
        """
        damage = ""
        if self.min_damage or self.max_damage:
            if self.max_damage < 0:
                damage = f"-({abs(self.max_damage)}-{abs(self.min_damage)})"
            else:
                damage = f"{self.min_damage}-{self.max_damage}"
        if self.raw_damage:
            raw_damage = f"+{self.raw_damage}" if self.raw_damage >= 0 else str(self.raw_damage)
            damage = f"{damage} ({raw_damage})" if damage else raw_damage
        return damage

    @property
    def long_label_damage(self) -> str:
        """
        Retourne le libellé (avec le type) des dégâts de l'arme ou de la munition
        :return: Représentation des dégâts ou rien si l'objet n'est pas une arme ou une munition
        """
        if not self.label_damage:
            if not self.body_part:
                return self.get_damage_type_display()
            return f"{self.get_damage_type_display()} ({self.get_body_part_display()}"
        if not self.body_part:
            return f"{self.label_damage} {self.get_damage_type_display()}"
        return f"{self.label_damage} {self.get_damage_type_display()} ({self.get_body_part_display()})"

    class Meta:
        abstract = True


# Tuple pour les données des résistances/absorptions
ResistanceInfo = namedtuple(
    "ResistanceInfo",
    (
        "code",
        "short_label",
        "long_label",
        "threshold",
        "resistance",
        "css_threshold",
        "css_resistance",
    ),
)


class Item(Entity, Resistance, Damage):
    """
    Objet
    """

    # General information
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, upload_to="items", verbose_name=_("image"))
    thumbnail = models.CharField(
        blank=True,
        max_length=100,
        choices=get_thumbnails("items"),
        verbose_name=_("miniature"),
    )
    type = models.CharField(max_length=10, choices=ITEM_TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    durability = models.PositiveIntegerField(default=0, verbose_name=_("durabilité"))
    condition_modifier = models.FloatField(default=0.0, verbose_name=_("modificateur de condition"))
    weight = models.FloatField(default=0.0, verbose_name=_("poids"))
    is_quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    is_droppable = models.BooleanField(default=True, verbose_name=_("jetable ?"))
    # Weapon specific
    hands = models.PositiveSmallIntegerField(default=0, choices=HANDS, verbose_name=_("mains nécessaires"))
    attack_mode = models.CharField(max_length=20, blank=True, choices=MODES, verbose_name=_("mode d'attaque"))
    skill = models.CharField(max_length=20, blank=True, choices=SKILLS, verbose_name=_("compétence"))
    min_skill = models.PositiveSmallIntegerField(default=0, verbose_name=_("compétence minimale"))
    min_strength = models.PositiveSmallIntegerField(default=0, verbose_name=_("force minimale"))
    clip_size = models.PositiveSmallIntegerField(default=0, verbose_name=_("taille du chargeur"))
    burst_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("munitions en rafale"))
    min_range = models.PositiveSmallIntegerField(default=0, verbose_name=_("portée minimale"))
    max_range = models.PositiveSmallIntegerField(default=0, verbose_name=_("portée maximale"))
    min_burst_range = models.PositiveIntegerField(default=0, verbose_name=_("portée min. en rafale"))
    max_burst_range = models.PositiveIntegerField(default=0, verbose_name=_("portée max. en rafale"))
    hit_chance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de précision"))
    armor_class_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur classe d'armure"))
    threshold_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur d'absorption"))
    threshold_rate_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur taux d'absorption"))
    resistance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de résistance"))
    is_single_charge = models.BooleanField(default=False, verbose_name=_("recharge unitaire ?"))
    # Action points
    ap_cost_reload = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA recharge"))
    ap_cost_normal = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA normal"))
    ap_cost_target = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA ciblé"))
    ap_cost_burst = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA rafale"))
    # Damage
    damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de dégâts"))
    critical_modifier = models.SmallIntegerField(default=0, verbose_name=_("chances de critiques"))
    critical_raw_modifier = models.SmallIntegerField(default=0, verbose_name=_("chances de dégâts bruts"))
    critical_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts critiques"))
    critical_damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur dégâts critiques"))
    # Resistances
    armor_class = models.SmallIntegerField(default=0, verbose_name=_("classe d'armure"))
    # Effets and ammunitions
    effects = models.ManyToManyField("Effect", blank=True, related_name="+", verbose_name=_("effets"))
    ammunitions = models.ManyToManyField(
        "Item",
        blank=True,
        limit_choices_to={"type": ITEM_AMMO},
        related_name="weapons",
        verbose_name=_("types de munitions"),
    )

    def clean(self):
        if self.min_range > self.max_range:
            raise ValidationError(
                dict(min_range=_("La portée minimale ne peut être plus grande que la portée maximale."))
            )
        if self.min_burst_range > self.max_burst_range:
            raise ValidationError(
                dict(min_burst_range=_("En rafale, la portée minimale ne peut être plus grand que la portée maximale."))
            )
        if self.min_damage > self.max_damage:
            raise ValidationError(
                dict(min_damage=_("Les dégâts minimums ne peuvent être plus grands que les dégâts maximums."))
            )

    @property
    def is_equipable(self) -> bool:
        """
        Objet équipable ?
        """
        return self.type in (
            ITEM_AMMO,
            ITEM_ARMOR,
            ITEM_HELMET,
            ITEM_WEAPON,
            ITEM_GRENADE,
        )

    @property
    def is_usable(self) -> bool:
        """
        Objet utilisable ?
        """
        return self.type in (ITEM_FOOD, ITEM_CHEM, ITEM_BOOK, ITEM_TOOL)

    @property
    def is_repairable(self) -> bool:
        """
        Objet réparable ?
        """
        return self.type in (ITEM_ARMOR, ITEM_HELMET, ITEM_WEAPON, ITEM_TOOL) and not self.is_throwable

    @property
    def is_ranged(self) -> bool:
        """
        Arme à distance ?
        """
        return self.type == ITEM_WEAPON and self.attack_mode not in (
            MODE_MELEE,
            MODE_THROW,
        )

    @property
    def is_melee(self) -> bool:
        """
        Arme de mêlée ?
        """
        return self.type == ITEM_WEAPON and self.attack_mode == MODE_MELEE

    @property
    def is_throwable(self) -> bool:
        """
        Arme de jet ?
        """
        return self.type == ITEM_GRENADE or (self.type == ITEM_WEAPON and self.attack_mode == MODE_THROW)

    @property
    def is_burst(self) -> bool:
        """
        Attaque en rafale ?
        """
        return self.type == ITEM_GRENADE or self.burst_count != 0

    @property
    def resistances(self) -> List[ResistanceInfo]:
        """
        Retourne les résistances de l'armure
        :return: code, libellé court, libellé long, absorption, résistance, CSS absorption, CSS résistance
        """
        resistances = []
        for code, label in DAMAGE_SHORTS:
            threshold, resistance = self.get_threshold(code), self.get_resistance(code)
            if threshold or resistance:
                resistances.append(
                    ResistanceInfo(
                        code,
                        label,
                        LIST_DAMAGES_TYPES.get(code),
                        threshold,
                        resistance,
                        get_class(threshold, 20),
                        get_class(resistance, 100),
                    )
                )
        return resistances

    def duplicate(self, name: str = None) -> "Item":
        """
        Duplique cet objet
        :param name: Nouveau nom
        :return: Objet
        """
        _assert(
            self.pk,
            _("Cet objet doit être préalablement enregistré avant d'être dupliqué."),
        )
        item_id = self.pk
        effects, ammunitions = self.effects.values_list("id", flat=True), self.ammunitions.values_list("id", flat=True)
        self.name = name or f"* {self.name.replace('* ', '')}"
        self.save(force_insert=True)
        for modifier in ItemModifier.objects.filter(item_id=item_id):
            modifier.pk, modifier.id, modifier.item_id = None, None, self.pk
            modifier.save(force_insert=True)
        self.effects.add(*effects)
        self.ammunitions.add(*ammunitions)
        return self

    def give(
        self,
        character: Union["Character", int],
        quantity: int = 1,
        condition: float = 1.0,
    ) -> Union[List["Equipment"], "Equipment"]:
        """
        Donne un ou plusieurs exemplaires de cet objet à un joueur ciblé
        :param character: Joueur
        :param quantity: Quantité
        :param condition: Etat
        :return: Equipement(s)
        """
        if self.is_repairable:
            equipments = []
            for i in range(quantity):
                equipment = Equipment.objects.create(character=character, item=self, quantity=1, condition=condition)
                equipments.append(equipment)
            return equipments if len(equipments) > 1 else next(iter(equipments), None)
        else:
            equipment, created = Equipment.objects.get_or_create(
                character=character,
                item=self,
                defaults=dict(quantity=quantity, condition=condition),
            )
            if not created:
                equipment.quantity += quantity
                equipment.save()
            return equipment

    def __str__(self) -> str:
        if self.title:
            return f"{self.name} ({self.title})"
        return self.name

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class ItemModifier(Modifier):
    """
    Modificateur d'objet
    """

    item = models.ForeignKey(
        "Item",
        on_delete=models.CASCADE,
        related_name="modifiers",
        verbose_name=_("objet"),
    )

    def clean(self):
        if self.min_value > self.max_value:
            raise ValidationError(
                dict(min_value=_("La valeur minimale ne peut être plus grande que la valeur maximale."))
            )

    class Meta:
        verbose_name = _("modificateur d'objet")
        verbose_name_plural = _("modificateurs d'objets")


class Equipment(CommonModel):
    """
    Equipement
    """

    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="equipments",
        verbose_name=_("personnage"),
    )
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="+", verbose_name=_("objet"))
    slot = models.CharField(
        max_length=10,
        choices=SLOT_ITEM_TYPES,
        blank=True,
        verbose_name=_("emplacement"),
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantité"))
    clip_count = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("munitions"))
    condition = models.FloatField(blank=True, null=True, verbose_name=_("état"))
    secondary = models.BooleanField(default=False, verbose_name=_("secondaire"))

    @property
    def equiped(self) -> bool:
        """
        Identifie si l'objet est équipé
        :return:
        """
        return self.slot != ""

    @property
    def value(self) -> float:
        """
        Valeur de l'objet en fonction de son état
        """
        return self.item.value * self.quantity * ((self.condition or 1.0) ** 1.5)

    @property
    def charge(self) -> float:
        """
        Taille de l'équipement en fonction de son nombre
        """
        return self.item.weight * self.quantity

    @property
    def compatible_ammunition(self) -> Optional[bool]:
        """
        Munitions compatibles
        """
        if self.slot or self.item.type != ITEM_AMMO:
            return None
        weapon = self.character.get_from_inventory(slot=ITEM_WEAPON)
        return weapon and self.item in weapon.item.ammunitions.all()

    @property
    def current_condition(self) -> Optional[int]:
        """
        Etat actuel
        """
        if self.condition is not None:
            return int(self.condition * 100)
        return None

    def equip(self, is_action: bool = False) -> "Equipment":
        """
        Permet d'équiper ou de déséquiper un objet
        :param is_action: Consommera des points d'action
        :return: Equipement
        """
        _assert(
            self.item.is_equipable,
            _("Il n'est pas possible de s'équiper de ce type d'objet."),
        )
        _assert(
            not is_action or self.character.action_points >= AP_COST_EQUIP,
            _("Le personnage ne possède plus assez de points d'actions pour s'équiper de cet objet."),
        )

        def get_equipment(equipment: "Equipment", slot: str) -> Optional["Equipment"]:
            return (
                Equipment.objects.select_related("item").filter(character_id=equipment.character_id, slot=slot).first()
            )

        def handle_equipment(equipment: "Equipment") -> None:
            if equipment.clip_count and not equipment.item.is_single_charge:
                ammo = get_equipment(equipment, ITEM_AMMO)
                if ammo:
                    ammo.quantity += equipment.clip_count
                    ammo.save()
                    equipment.clip_count = 0
            elif equipment.slot == ITEM_AMMO:
                weapon = get_equipment(equipment, ITEM_WEAPON)
                if weapon and not weapon.item.is_single_charge:
                    equipment.quantity += weapon.clip_count
                    weapon.clip_count = 0
                    weapon.save()
            equipment.slot = ""

        if self.slot:
            handle_equipment(self)
        else:
            item = get_equipment(self, self.item.type)
            if item:
                handle_equipment(item)
                item.save()
            self.slot = self.item.type
        self.full_clean()
        self.save()
        if is_action:
            self.character.action_points -= AP_COST_EQUIP
            self.character.save()
        return self

    def use(self, is_action: bool = False, save: bool = True) -> List["CharacterEffect"]:
        """
        Permet d'utiliser un objet
        :param is_action: Consommera des points d'action
        :param save: Sauvegardera la modification
        :return: Liste des effets
        """
        _assert(self.item.is_usable, _("Il n'est pas possible d'utiliser ce type d'objet."))
        _assert(
            not is_action or self.character.action_points >= AP_COST_USE,
            _("Le personnage ne possède plus assez de points d'actions pour utiliser cet objet."),
        )
        _assert(
            self.quantity > 0,
            _("Le personnage doit posséder au moins un exemplaire de cet objet pour l'utiliser."),
        )
        effects, modifiers = [], []
        change_character = False
        for effect in self.item.effects.all():
            character_effect = effect.affect(self.character)
            if character_effect:
                effects.append(character_effect)
        if self.item.type != ITEM_TOOL:
            for modifier in self.item.modifiers.all():
                calculated_value = modifier.get_calculated_value(fixed=True)
                self.character.modify_value(modifier.stats, calculated_value)
                modifiers.append(modifier)
                change_character = True
            self.quantity -= 1
            if save:
                self.save()
        elif self.item.durability > 0:
            self.condition -= 1.0 / self.item.durability
            if save:
                self.save()
        if is_action:
            self.character.action_points -= AP_COST_USE
        if change_character or is_action:
            self.character.save()
        return effects, modifiers

    def drop(self, quantity: int = 1, is_action: bool = False, save: bool = True) -> "Loot":
        """
        Permet de jeter un ou plusieurs objets
        :param quantity: Quantité
        :param is_action: Consommera des points d'action
        :param save: Sauvegardera la modification
        :return: Butin
        """
        _assert(
            self.quantity >= quantity,
            _("Le personnage doit posséder la quantité d'objets qu'il souhaite jeter."),
        )
        _assert(
            not is_action or self.character.action_points >= AP_COST_USE,
            _("Le personnage ne possède plus assez de points d'actions pour jeter cet objet."),
        )
        if self.slot and not self.item.is_throwable:
            self.equip(is_action=False)
        loot = Loot.create(
            campaign=self.character.campaign,
            item=self.item,
            quantity=quantity,
            condition=self.condition,
        )
        self.quantity -= quantity
        if save:
            self.save()
        if is_action:
            self.character.action_points -= AP_COST_DROP
            self.character.save()
        return loot

    def reload(self, is_action: bool = False, save: bool = True) -> "Equipment":
        """
        Permet de recharger une arme
        :param is_action: Consommera des points d'action
        :param save: Sauvegardera la modification
        :return: Equipement
        """
        _assert(
            self.slot == ITEM_WEAPON and self.item.clip_size,
            _("Cet objet n'est pas une arme équipée ou ne peut être rechargé."),
        )
        _assert(
            not is_action or self.character.action_points >= self.item.ap_cost_reload,
            _("Le personnage ne possède plus assez de points d'actions pour recharger cette arme."),
        )
        ammo = Equipment.objects.filter(character_id=self.character_id, slot=ITEM_AMMO).first()
        _assert(
            ammo and ammo.quantity > 0,
            _("Il n'y a aucun type de munition équipé ou le nombre de munitions disponibles est insuffisant."),
        )
        _assert(
            ammo.item in self.item.ammunitions.all(),
            _("Cette arme est incompatible avec le type de munition équipé."),
        )
        if self.item.is_single_charge:
            needed_ammo = 1
            self.clip_count = self.item.clip_size
        else:
            needed_ammo = min(self.item.clip_size - self.clip_count, ammo.quantity)
            self.clip_count += needed_ammo
        ammo.quantity -= needed_ammo
        if save:
            ammo.save()
        self.save()
        if is_action:
            self.character.action_points -= self.item.ap_cost_reload
            self.character.save()
        return self

    def repair(self, value: Union[int, float] = 100, is_action: bool = False, save: bool = True) -> "Equipment":
        """
        Permet de réparer un équipement détérioré
        :param value: Valeur de réparation
        :param is_action: Consommera des points d'action
        :param save: Sauvegardera la modification
        :return: Equipement
        """
        _assert(self.item.is_repairable, _("Cet objet n'est pas réparable."))
        _assert(
            not is_action or self.character.action_points >= AP_COST_REPAIR,
            _("Le personnage ne possède plus assez de points d'actions pour réparer cet objet."),
        )
        self.condition = (value / 100.0) if isinstance(value, int) else float(value)
        if save:
            self.save()
        if is_action:
            self.character.action_points -= AP_COST_REPAIR
            self.character.save()
        return self

    def set_secondary(self) -> "Equipment":
        """
        Permet de définir un équipement libre de l'inventaire comme arme secondaire
        :return: Equipement
        """
        old_equipment = self.character.equipments.filter(secondary=True)
        old_equipment.update(secondary=False)
        self.secondary = True
        try:
            self.save()
        except ValidationError:
            old_equipment.update(secondary=True)
            raise
        return self

    def clean(self):
        """
        Validation de l'objet
        """
        if self.slot:
            if self.slot != self.item.type:
                raise ValidationError(dict(slot=_("L'emplacement doit correspondre au type d'objet.")))
            if self.character.equipments.exclude(id=self.pk).filter(slot=self.slot).exists():
                raise ValidationError(dict(slot=_("Un autre objet est déjà présent à cet emplacement.")))
        if self.slot == ITEM_AMMO:
            equipment = self.character.equipments.select_related("item").filter(slot=ITEM_WEAPON).first()
            if equipment and not equipment.item.ammunitions.filter(id=self.item.pk).exists():
                raise ValidationError(dict(item=_("Ces munitions sont incompatibles avec l'arme équipée.")))
        elif self.slot == ITEM_WEAPON:
            equipment = self.character.equipments.select_related("item").filter(slot=ITEM_AMMO).first()
            if equipment and not self.item.ammunitions.filter(id=equipment.item.pk).exists():
                raise ValidationError(dict(item=_("Cette arme est incompatible avec les munitions équipées.")))
        if self.secondary:
            if self.item.type != ITEM_WEAPON:
                raise ValidationError(dict(item=_("Cet objet ne peut être considéré comme une arme secondaire.")))
            if not self.item.is_melee:
                raise ValidationError(
                    dict(item=_("Seule une arme de corps-à-corps ne peut être utilisée comme arme secondaire."))
                )
            if self.character.equipments.exclude(id=self.pk).filter(secondary=True).exists():
                raise ValidationError(
                    dict(secondary=_("Un autre objet de l'inventaire est déjà défini comme arme secondaire."))
                )

    def reset_character_stats(self):
        """
        Optimisation de la réinitialisation des stats du personnage concerné
        """
        character = self._state.fields_cache.get("character")
        Character.reset_stats(character or self.character_id)

    def save(self, *args, **kwargs):
        """
        Sauvegarde de l'objet
        """
        self.reset_character_stats()
        if (not self.slot and self.quantity <= 0) or (self.condition is not None and self.condition <= 0):
            kwargs = {k: v for k, v in kwargs.items() if k.startswith("_")}
            return self.delete(**kwargs)
        self.quantity = max(0, self.quantity) if self.quantity else 0
        self.condition = (
            max(0.0, min(1.0, self.condition or 0.0))
            if (self.item.is_repairable and self.item.durability > 0)
            else None
        )
        self.clip_count = max(0, self.clip_count or 0) if self.item.clip_size else None
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Suppression de l'objet
        """
        self.reset_character_stats()
        return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.character.name}) {self.item}"

    class Meta:
        verbose_name = _("équipement")
        verbose_name_plural = _("équipements")


class Effect(Entity, Damage):
    """
    Effet
    """

    # General information
    character = models.ForeignKey(
        "Character",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="perks",
        verbose_name=_("personnage"),
    )
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, upload_to="effects", verbose_name=_("image"))
    thumbnail = models.CharField(
        blank=True,
        max_length=100,
        verbose_name=_("miniature"),
        choices=get_thumbnails("effects") + get_thumbnails("items"),
    )
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance d'effet"))
    min_duration = models.DurationField(blank=True, null=True, verbose_name=_("durée d'effet min."))
    max_duration = models.DurationField(blank=True, null=True, verbose_name=_("durée d'effet max."))
    controlled = models.BooleanField(default=False, verbose_name=_("contrôlable ?"))
    # Timed effects
    apply = models.BooleanField(default=True, verbose_name=_("appliquer ?"))
    interval = models.DurationField(blank=True, null=True, verbose_name=_("intervalle"))
    damage_chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance de dégâts"))
    # Next effect
    next_effect = models.ForeignKey(
        "Effect",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("effet suivant"),
    )
    cancel_effect = models.ForeignKey(
        "Effect",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name="+",
        verbose_name=_("effet annulé"),
    )
    damages = []

    def clean(self):
        if self.min_duration and self.max_duration and self.min_duration > self.max_duration:
            raise ValidationError(
                dict(min_duration=_("La durée minimale ne peut être plus grande que la durée maximale."))
            )
        if self.min_damage > self.max_damage:
            raise ValidationError(
                dict(min_damage=_("Les dégâts minimums ne peuvent être plus grands que les dégâts maximums."))
            )

    @property
    def damage_config(self) -> Optional[Dict[str, Union[str, int]]]:
        """
        Dégâts de l'effet
        """
        if not self.damage_type:
            return None
        return dict(
            raw_damage=self.raw_damage,
            min_damage=self.min_damage,
            max_damage=self.max_damage,
            damage_type=self.damage_type,
            body_part=self.body_part,
        )

    @property
    def duration(self) -> timedelta:
        if self.min_duration and not self.max_duration:
            return self.min_duration
        if self.max_duration and not self.min_duration:
            return self.max_duration
        if self.min_duration and self.max_duration:
            return timedelta(
                seconds=randint(
                    int(self.min_duration.total_seconds()),
                    int(self.max_duration.total_seconds()),
                )
            )

    def affect(
        self,
        target: Union["Campaign", "Character"],
        date: datetime = None,
        force: bool = False,
    ) -> Optional[Union["CampaignEffect", "CharacterEffect"]]:
        """
        Applique l'effet à un personnage ou une campagne
        :param target: Personnage ou campagne
        :param date: Date de début de l'effet
        :param force: Force l'application de l'effet
        :return: Effect actif ou rien si l'effet ne s'applique pas
        """
        effect = None
        if isinstance(target, Campaign):
            if not force and randint(1, 100) > self.chance:
                return None
            if self.cancel_effect_id:
                CampaignEffect.objects.filter(campaign=target, effect_id=self.cancel_effect_id).delete()
            effect, created = CampaignEffect.objects.update_or_create(
                campaign=target,
                effect=self,
                defaults=dict(
                    start_date=date or target.current_game_date,
                    end_date=None,
                    next_date=None,
                ),
            )
            if effect:
                self.damages.extend(effect.apply_all())
        elif isinstance(target, Character):
            _assert(
                (self.duration is None and self.interval is None) or target.campaign is not None,
                _("Le personnage doit faire partie d'une campagne pour lui appliquer un effet sur la durée."),
            )
            if not force and randint(1, 100) > self.chance:
                return None
            if self.cancel_effect_id:
                CharacterEffect.objects.filter(character=target, effect_id=self.cancel_effect_id).delete()
            current_game_date = gv(target.campaign, "current_game_date", None)
            effect, created = CharacterEffect.objects.update_or_create(
                character=target,
                effect=self,
                defaults=dict(start_date=date or current_game_date, end_date=None, next_date=None),
            )
            if effect:
                self.damages.extend(effect.apply(target))
        return effect

    def duplicate(self, name: str = None) -> "Effect":
        """
        Duplique cet effet
        :param name: Nouveau nom
        :return: Effet
        """
        _assert(
            self.pk,
            _("Cet effet doit être préalablement enregistré avant d'être dupliqué."),
        )
        effect_id = self.pk
        self.name = name or f"* {self.name.replace('* ', '')}"
        self.save(force_insert=True)
        for modifier in EffectModifier.objects.filter(effect_id=effect_id):
            modifier.pk, modifier.id, modifier.effect_id = None, None, self.pk
            modifier.save(force_insert=True)
        return self

    def __str__(self) -> str:
        if self.title:
            return f"{self.name} ({self.title})"
        return self.name

    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")


class EffectModifier(Modifier):
    """
    Modificateur d'effet
    """

    effect = models.ForeignKey(
        "Effect",
        on_delete=models.CASCADE,
        related_name="modifiers",
        verbose_name=_("effet"),
    )

    def clean(self):
        if self.min_value > self.max_value:
            raise ValidationError(
                dict(min_value=_("La valeur minimale ne peut être plus grande que la valeur maximale."))
            )

    class Meta:
        verbose_name = _("modificateur d'effet")
        verbose_name_plural = _("modificateurs d'effets")


class ActiveEffect(CommonModel):
    """
    Effet actif
    """

    effect = models.ForeignKey("Effect", on_delete=models.CASCADE, related_name="+", verbose_name=_("effet"))
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'effet"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'arrêt"))
    next_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date suivante"))
    damages, next_effects = [], []

    def get_progress(self, current_date: datetime) -> Optional[List[Tuple[float, datetime, str]]]:
        """
        Retourne l'avancement de l'effet dans le temps
        :param current_date: Date actuelle de jeu
        :return: Tuple avec la progression en pourcentage et le temps écoulé/restant
        """
        if not self.start_date or not self.end_date:
            return None
        start_date, end_date = self.start_date, self.end_date
        total, elapsed, remaining = (
            (end_date - start_date),
            (current_date - start_date),
            (end_date - current_date),
        )
        elapsed_rate, remaining_rate = (
            max(0.0, min(100.0, round(elapsed * 100 / total, 2))),
            max(0.0, min(100.0, round(remaining * 100 / total, 2))),
        )
        elapsed_style, remaining_style = (
            ("primary" if elapsed_rate < 100 else "success") if self.effect.controlled else "danger",
            "dark" if self.effect.controlled else "success",
        )
        return [(elapsed_rate, start_date, elapsed_style), (remaining_rate, end_date, remaining_style)]

    class Meta:
        abstract = True


class CampaignEffect(ActiveEffect):
    """
    Effet actif dans une campagne
    """

    campaign = models.ForeignKey(
        "Campaign",
        on_delete=models.CASCADE,
        related_name="active_effects",
        verbose_name=_("campagne"),
    )

    @property
    def progress(self) -> Optional[List[Tuple[float, datetime, str]]]:
        if not self.end_date or not self.campaign:
            return
        return super().get_progress(self.campaign.current_game_date)

    def apply(self, character: "Character", save: bool = True) -> List["DamageHistory"]:
        """
        Applique l'effet d'une campagne à un personnage
        :param character: Personnage auquel est appliqué l'effet
        :param save: Sauvegarde les données relatives aux personnages ?
        :return: Dégâts potentiels infligés
        """
        self.damages = []
        if not self.campaign or not self.effect.damage_config:
            return self.damages
        game_date = self.campaign.current_game_date
        while self.next_date and self.next_date <= game_date:
            if self.start_date != game_date and not self.effect.interval:
                break
            if self.end_date and self.next_date > self.end_date:
                break
            damage = character.damage(save=save, **self.effect.damage_config)
            damage.source = self.effect
            self.damages.append(damage)
            if not self.effect.interval:
                break
            self.next_date += self.effect.interval
        if self.damages or (self.end_date and self.end_date <= game_date):
            self.save()
        self.damages = self.damages
        return self.damages

    def apply_all(self, save: bool = True) -> List["DamageHistory"]:
        """
        Applique l'effet aux personnages de la campagne
        :param save: Sauvegarde les données relatives aux personnages ?
        :return: Dégâts potentiels infligés
        """
        self.damages = []
        if not self.campaign:
            return self.damages
        game_date = self.campaign.current_game_date
        if self.effect.damage_config:
            characters = self.campaign.characters.filter(is_active=True).exclude(health__lte=0)
            while self.next_date and self.next_date <= game_date:
                if self.start_date != game_date and not self.effect.interval:
                    break
                if self.end_date and self.next_date > self.end_date:
                    break
                for character in characters:
                    damage = character.damage(save=save, **self.effect.damage_config)
                    damage.source = self.effect
                    self.damages.append(damage)
                if not self.effect.interval:
                    break
                self.next_date += self.effect.interval
                if not self.end_date or game_date <= self.end_date:
                    break
        if self.damages or (self.end_date and self.end_date <= game_date):
            self.save()
        return self.damages

    def save(self, *args, **kwargs):
        """
        Sauvegarde de l'effet actif
        """
        for character_id in self.campaign.characters.values_list("pk", flat=True):
            Character.reset_stats(character_id)
        if not self.start_date:
            self.start_date = self.campaign.current_game_date
        if not self.end_date and self.start_date and self.effect.duration:
            self.end_date = self.start_date + self.effect.duration
        if not self.next_date and self.start_date:
            if self.effect.apply:
                self.next_date = self.start_date
            elif self.effect.interval:
                self.next_date = self.start_date + self.effect.interval
            if self.next_date and self.end_date and self.next_date > self.end_date:
                self.next_date = None
        if self.end_date and self.end_date <= self.campaign.current_game_date and not self.effect.controlled:
            if self.effect.next_effect:
                effect = self.effect.next_effect.affect(self.campaign, self.end_date)
                if effect:
                    self.next_effects.append(effect)
                    self.damages.extend(effect.damages)
            kwargs = {k: v for k, v in kwargs.items() if k.startswith("_")}
            return self.delete(**kwargs)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Suppression de l'effet actif
        """
        for character_id in self.campaign.characters.values_list("pk", flat=True):
            Character.reset_stats(character_id)
        if self.pk:
            return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.campaign.name}) {self.effect}"

    class Meta:
        verbose_name = _("effet de campagne")
        verbose_name_plural = _("effets de campagne")


class CharacterEffect(ActiveEffect):
    """
    Effet actif sur un personnage
    """

    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="active_effects",
        verbose_name=_("personnage"),
    )

    @property
    def progress(self) -> Optional[List[Tuple[float, datetime, str]]]:
        if not self.end_date or not self.character.campaign:
            return None
        return super().get_progress(self.character.campaign.current_game_date)

    def apply(self, character: Optional["Character"] = None, save: bool = True) -> List["DamageHistory"]:
        """
        Applique l'effet au personnage
        :param character: Personnage auquel est appliqué l'effet
        :param save: Sauvegarde les données relatives au personnage ?
        :return: Liste des dégâts éventuellement subis
        """
        self.damages = []
        character = character or self.character
        if not character.campaign:
            return self.damages
        game_date = character.campaign.current_game_date
        if self.effect.damage_config:
            while self.next_date and self.next_date <= game_date:
                if self.start_date != game_date and not self.effect.interval:
                    break
                if self.end_date and self.next_date > self.end_date:
                    break
                damage = character.damage(save=save, **self.effect.damage_config)
                damage.source = self.effect
                self.damages.append(damage)
                if not self.effect.interval:
                    break
                self.next_date += self.effect.interval
        if self.damages or (self.end_date and self.end_date <= game_date):
            self.save()
        return self.damages

    def reset_character_stats(self):
        """
        Optimisation de la réinitialisation des stats du personnage concerné
        """
        character = self._state.fields_cache.get("character")
        Character.reset_stats(character or self.character_id)

    def save(self, *args, **kwargs):
        """
        Sauvegarde de l'effet actif
        """
        self.reset_character_stats()
        if self.character.campaign:
            if not self.start_date and self.character.campaign:
                self.start_date = self.character.campaign.current_game_date
            if not self.end_date and self.start_date and self.effect.duration:
                self.end_date = self.start_date + self.effect.duration
            if not self.next_date and self.start_date:
                if self.effect.apply:
                    self.next_date = self.start_date
                elif self.effect.interval:
                    self.next_date = self.start_date + self.effect.interval
                if self.next_date and self.end_date and self.next_date > self.end_date:
                    self.next_date = None
            if (
                self.end_date
                and self.end_date <= self.character.campaign.current_game_date
                and not self.effect.controlled
            ):
                if self.effect.next_effect:
                    effect = self.effect.next_effect.affect(self.character, self.end_date)
                    if effect:
                        self.next_effects.append(effect)
                        self.damages.extend(effect.damages)
                kwargs = {k: v for k, v in kwargs.items() if k.startswith("_")}
                return self.delete(**kwargs)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """
        Suppression de l'effet actif
        """
        self.reset_character_stats()
        if self.pk:
            return super().delete(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.character.name}) {self.effect}"

    class Meta:
        verbose_name = _("effet de personnage")
        verbose_name_plural = _("effets de personnage")


class Loot(CommonModel):
    """
    Butin
    """

    campaign = models.ForeignKey(
        "Campaign",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="loots",
        verbose_name=_("campagne"),
    )
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="loots", verbose_name=_("objet"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantité"))
    condition = models.FloatField(blank=True, null=True, verbose_name=_("état"))

    @property
    def value(self) -> float:
        """
        Valeur de l'objet en fonction de son état
        """
        return self.item.value * self.quantity * (self.condition or 1)

    @property
    def charge(self) -> float:
        """
        Taille de l'équipement en fonction de son nombre
        """
        return self.item.weight * self.quantity

    @property
    def current_condition(self) -> Optional[int]:
        """
        Etat actuel
        """
        if self.condition is not None:
            return int(self.condition * 100)
        return None

    def take(
        self,
        character: Union["Character", int],
        quantity: int = 1,
        is_action: bool = False,
    ) -> "Equipment":
        """
        Permet à un personnage de prendre un ou plusieurs objets du butin
        :param character: Personnage
        :param quantity: Nombre d'objets à prendre
        :param is_action: Consommera des points d'action
        :return: Equipement
        """
        if isinstance(character, (int, str)):
            character = Character.objects.select_related("statistics").get(pk=character)
        _assert(
            self.campaign_id == character.campaign_id,
            _("Le personnage doit être dans la même campagne."),
        )
        _assert(
            not is_action or character.action_points >= AP_COST_TAKE,
            _("Le personnage ne possède plus assez de points d'actions pour s'équiper de cet objet."),
        )
        quantity = max(0, min(quantity, self.quantity))
        equipment = Equipment.objects.select_related("item").filter(character=character, item=self.item).first()
        if equipment and not equipment.item.is_repairable:
            equipment.quantity += quantity
            equipment.save()
        else:
            equipment = Equipment.objects.create(
                character=character,
                item=self.item,
                quantity=quantity,
                condition=self.condition,
            )
        if quantity >= self.quantity:
            self.delete()
        else:
            self.quantity -= quantity
            self.save()
        if is_action:
            character.action_points -= AP_COST_TAKE
            character.save()
        return equipment

    @classmethod
    def create(
        cls,
        campaign: Union["Campaign", int],
        item: Union["Item", int],
        quantity: int = 1,
        condition: float = 1.0,
    ) -> "Loot":
        if isinstance(item, (int, str)):
            item = Item.objects.get(pk=int(item))
        try:
            _assert(not item.is_repairable)
            loot = Loot.objects.get(campaign=campaign, item=item)
            loot.quantity += quantity
            loot.save()
        except (AssertionError, Loot.DoesNotExist):
            loot = Loot.objects.create(campaign=campaign, item=item, quantity=quantity, condition=condition)
        return loot

    def save(self, *args, **kwargs):
        """
        Sauvegarde le butin
        """
        if self.quantity <= 0:
            kwargs = {k: v for k, v in kwargs.items() if k.startswith("_")}
            return self.delete(**kwargs)
        self.quantity = max(0, self.quantity) if self.quantity else 0
        self.condition = max(0.0, min(1.0, self.condition or 1.0)) if self.item.is_repairable else None
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return f"({self.campaign.name}) {self.item}"

    class Meta:
        verbose_name = _("butin")
        verbose_name_plural = _("butins")


class LootTemplate(CommonModel):
    """
    Modèle de butin
    """

    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, upload_to="loots", verbose_name=_("image"))
    min_money = models.PositiveIntegerField(default=0, verbose_name=_("argent min."))
    max_money = models.PositiveIntegerField(default=0, verbose_name=_("argent max."))
    thumbnail = models.CharField(
        blank=True,
        max_length=100,
        choices=get_thumbnails("items"),
        verbose_name=_("miniature"),
    )

    def clean(self):
        if self.min_money and self.max_money and self.min_money > self.max_money:
            raise ValidationError(dict(min_money=_("L'argent minimal ne peut être plus grand que l'argent maximal.")))

    def create(
        self,
        campaign: Union["Campaign", int],
        character: Optional[Union["Character", int]] = None,
    ) -> (List["Loot"], int):
        """
        Permet de créer un butin à partir du modèle (éventuellement en fonction de la chance du personnage)
        :param campaign: Campagne
        :param character: Personnage
        :return: Liste de butins, argent trouvé
        """
        loots = []
        if isinstance(campaign, (int, str)):
            campaign = Campaign.objects.get(pk=campaign)
        roll_modifier = 0
        if character:
            if isinstance(character, (int, str)):
                character = Character.objects.select_related("statistics").get(pk=character)
            roll_modifier = int(round((5 - character.stats.luck) * LUCK_ROLL_MULT, 0))
        _assert(
            not character or campaign.pk == character.campaign_id,
            _("Le personnage concerné doit être dans la même campagne que le butin a créer."),
        )
        money = int(round(randint(self.min_money, self.max_money) * (1 - roll_modifier) * EXTRA_LUCK_MONEY_MULT, 0))
        if money:
            campaign.money_loot += money
            campaign.save(update_fields=("money_loot",))
        for template in self.items.select_related("item").all():
            if randint(1, 100 + roll_modifier) > template.chance:
                continue
            loots.append(
                Loot.create(
                    campaign=campaign,
                    item=template.item,
                    quantity=randint(template.min_quantity, template.max_quantity),
                    condition=randint(template.min_condition, template.max_condition) / 100.0,
                )
            )
        return loots, money

    def duplicate(self, name: str = None) -> "LootTemplate":
        """
        Duplique ce modèle de butin
        :param name: Nouveau nom
        :return: Modèle de butin
        """
        _assert(
            self.pk,
            _("Ce modèle de butin doit être préalablement enregistré avant d'être dupliqué."),
        )
        template_id = self.pk
        self.name = name or f"* {self.name.replace('* ', '')}"
        self.save(force_insert=True)
        for item in LootTemplateItem.objects.filter(template_id=template_id):
            item.pk, item.id, item.template_id = None, None, self.pk
            item.save(force_insert=True)
        return self

    def __str__(self) -> str:
        if self.title:
            return f"{self.name} ({self.title})"
        return self.name

    class Meta:
        verbose_name = _("modèle de butin")
        verbose_name_plural = _("modèles des butins")


class LootTemplateItem(CommonModel):
    """
    Objet de butin
    """

    template = models.ForeignKey(
        "LootTemplate",
        on_delete=models.CASCADE,
        related_name="items",
        verbose_name=_("modèle"),
    )
    item = models.ForeignKey("Item", on_delete=models.CASCADE, related_name="+", verbose_name=_("objet"))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    min_quantity = models.PositiveIntegerField(default=1, verbose_name=_("nombre min."))
    max_quantity = models.PositiveIntegerField(default=1, null=True, verbose_name=_("nombre max."))
    min_condition = models.PositiveSmallIntegerField(default=100, verbose_name=_("état min."))
    max_condition = models.PositiveSmallIntegerField(default=100, verbose_name=_("état max."))

    def clean(self):
        if self.min_quantity > self.max_quantity:
            raise ValidationError(
                dict(min_quantity=_("La quantité minimale ne peut être plus grande que la quantité maximale."))
            )
        if self.min_condition > self.max_condition:
            raise ValidationError(dict(min_condition=_("L'état minimum ne peut être plus grand que l'état maximum.")))

    def __str__(self) -> str:
        return f"({self.template.name}) {self.item}"

    class Meta:
        verbose_name = _("objet de butin")
        verbose_name_plural = _("objets des butins")


class RollHistory(CommonModel):
    """
    Historique des jets
    """

    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="roll_history",
        verbose_name=_("personnage"),
    )
    level = models.SmallIntegerField(default=0, verbose_name=_("niveau"))
    stats = models.CharField(max_length=20, blank=True, choices=ROLL_STATS, verbose_name=_("statistique"))
    value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur"))
    modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur"))
    roll = models.PositiveIntegerField(default=0, verbose_name=_("jet"))
    success = models.BooleanField(default=False, verbose_name=_("succès ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))
    experience = models.PositiveSmallIntegerField(default=0, verbose_name=_("expérience"))
    level_up = models.BooleanField(default=False, verbose_name=_("niveau+ ?"))
    reason = models.TextField(blank=True, verbose_name=_("raison"))

    class RollStats:
        """
        Statistiques des jets
        """

        def __init__(self, character: "Character", code: str, label: str):
            self.character = character
            self.code = code
            self.label = label
            self.total_count = 0
            self.count_by_level = Counter()
            self.stats = odict((((1, 1), 0), ((1, 0), 0), ((0, 0), 0), ((0, 1), 0)))
            self.stats_by_level = {}

        def add(self, level: int, success: bool, critical: bool, count: int):
            """
            Ajoute un jet aux statistiques
            :param level: Niveau
            :param success: Succès ?
            :param critical: Critique ?
            :param count: Nombre
            :return: Rien
            """
            self.total_count += count
            self.count_by_level[level] += count
            self.stats[success, critical] += count
            self.stats_by_level.setdefault(
                level,
                odict((((1, 1), 0), ((1, 0), 0), ((0, 0), 0), ((0, 1), 0))),
            )[success, critical] += count

        @property
        def all(self) -> List[Tuple[int, float, str, str]]:
            """
            Ventilation des statistiques par succès/échec
            :return: Liste ventilée par valeur, pourcentage, classe CSS et libellé
            """
            return [
                (
                    count,
                    round(((count / self.total_count) * 100) if self.total_count else 0, 2),
                    settings.CSS_CLASSES[success, critical],
                    get_label(success, critical),
                )
                for (success, critical), count in self.stats.items()
            ]

        def get_all_by_level(self, level: int) -> List[Tuple[int, float, str, str]]:
            """
            Ventilation des statistiques par succès/échec en fonction du niveau
            :param level: Niveau cible
            :return: Liste ventilée par valeur, pourcentage, classe CSS et libellé
            """
            return [
                (
                    count,
                    round(((count / self.count_by_level[level]) * 100) if self.count_by_level.get(level) else 0, 2),
                    settings.CSS_CLASSES[success, critical],
                    get_label(success, critical),
                )
                for (success, critical), count in self.stats_by_level.get(level, {}).items()
            ]

        @property
        def previous_stats(self) -> List[Tuple[int, float, str, str]]:
            return self.get_all_by_level(self.character.level - 1)

        @property
        def current_stats(self) -> List[Tuple[int, float, str, str]]:
            return self.get_all_by_level(self.character.level)

        @property
        def previous_total(self) -> int:
            return self.count_by_level.get(self.character.level - 1, 0)

        @property
        def current_total(self) -> int:
            return self.count_by_level.get(self.character.level, 0)

        @property
        def total_success(self) -> int:
            """
            Nombre total des succès
            """
            return sum(self.stats[1, x] for x in range(2))

        @property
        def success_rate(self) -> float:
            """
            Taux de succès
            """
            if not self.total_count:
                return 0.0
            return round(self.total_success * 100.0 / self.total_count, 1)

    @staticmethod
    def get_stats(character: "Character") -> List[RollStats]:
        """
        Récupère les statistiques de jets
        :param character: Personnage
        :return: Liste des statistiques de jets
        """
        all_stats = odict()
        for code, label in SPECIALS + SKILLS:
            all_stats[code] = RollHistory.RollStats(character, code, label)
        rolls = (
            RollHistory.objects.filter(character=character)
            .values("level", "stats", "success", "critical")
            .annotate(count=Count("*"))
            .values_list("level", "stats", "success", "critical", "count")
        )
        for level, stats, success, critical, count in rolls:
            all_stats[stats].add(level, success, critical, count or 0)
        return list(all_stats.values())

    @property
    def css_class(self) -> str:
        """
        Classe CSS associée
        """
        return settings.CSS_CLASSES[self.success, self.critical]

    @property
    def message_level(self) -> str:
        """
        Niveau de message
        """
        return settings.MESSAGE_INFOS[self.success, self.critical]

    @property
    def pre_label(self) -> str:
        """
        Pré-libellé
        """
        return _("🎲 {character}").format(character=self.character)

    @property
    def label(self) -> str:
        """
        Libellé du jet
        """
        return get_label(self.success, self.critical)

    @property
    def long_label(self) -> str:
        """
        Libellé long du jet
        """
        message = _("{label} du jet de {stats} : {roll} pour {value}")
        if self.modifier:
            message = _("{label} du jet de {stats} : {roll} pour {total} ({value}{modifier:+d})")
        return message.format(
            stats=self.get_stats_display(),
            label=self.label,
            roll=self.roll,
            value=self.value,
            modifier=self.modifier,
            total=self.value + self.modifier,
        )

    def __str__(self) -> str:
        return f"{self.pre_label} - {self.long_label}"

    class Meta:
        verbose_name = _("historique de jet")
        verbose_name_plural = _("historiques des jets")


class DamageHistory(Damage):
    """
    Historique des dégâts
    """

    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="damage_history",
        verbose_name=_("personnage"),
    )
    level = models.SmallIntegerField(default=0, verbose_name=_("niveau"))
    base_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts de base"))
    armor = models.ForeignKey(
        "Item",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        limit_choices_to={"type__in": (ITEM_ARMOR, ITEM_HELMET)},
        related_name="+",
        verbose_name=_("protection"),
    )
    armor_threshold = models.FloatField(default=0.0, verbose_name=_("absorption armure"))
    armor_resistance = models.FloatField(default=0.0, verbose_name=_("résistance armure"))
    armor_damage = models.FloatField(default=0.0, verbose_name=_("dégâts armure"))
    damage_threshold = models.FloatField(default=0.0, verbose_name=_("absorption dégâts"))
    damage_resistance = models.FloatField(default=0.0, verbose_name=_("résistance dégâts"))
    real_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts réels"))
    damage_rate = models.FloatField(default=0.0, verbose_name=_("taux de dégâts"))
    source = models.ForeignKey("Effect", blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("source"))
    reason = models.TextField(blank=True, verbose_name=_("raison"))

    @property
    def css_class(self) -> str:
        """
        Classe CSS associée
        """
        return settings.MESSAGE_TAGS.get(self.message_level)

    @property
    def message_level(self) -> str:
        """
        Niveau de message
        """
        return (messages.ERROR, messages.SUCCESS)[self.is_heal]

    @property
    def icon(self) -> str:
        """
        Icône des dégâts
        """
        return DAMAGE_ICONS.get(self.damage_type, "⚠️")

    @property
    def pre_label(self) -> str:
        """
        Pré-libellé
        """
        return _("{icon} {character}").format(icon=self.icon, character=self.character)

    @property
    def label(self) -> str:
        """
        Libellé des dégâts
        """
        return self.get_damage_type_display()

    @property
    def long_label(self) -> str:
        """
        Libellé long des dégâts
        """
        if self.body_part:
            label = _("{real_damage} points de {type} ({body_part})").format(
                real_damage=self.real_damage * (1, -1)[self.is_heal],
                type=self.get_damage_type_display(),
                body_part=self.get_body_part_display(),
            )
        else:
            label = _("{real_damage} points de {type}").format(
                real_damage=self.real_damage * (1, -1)[self.is_heal],
                type=self.get_damage_type_display(),
            )
        return _("{label} - source : {source}").format(label=label, source=self.source) if self.source else label

    def __str__(self) -> str:
        return f"{self.pre_label} - {self.label}"

    class Meta:
        verbose_name = _("historique de dégâts")
        verbose_name_plural = _("historiques des dégâts")


class FightHistory(CommonModel):
    """
    Historique des combats
    """

    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    attacker = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("attaquant"),
    )
    attacker_level = models.SmallIntegerField(default=0, verbose_name=_("niveau de l'attaquant"))
    defender = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("défenseur"),
    )
    defender_level = models.SmallIntegerField(default=0, verbose_name=_("niveau du défenseur"))
    attacker_weapon = models.ForeignKey(
        "Item",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        limit_choices_to={"type__in": (ITEM_WEAPON, ITEM_GRENADE)},
        related_name="+",
        verbose_name=_("arme de l'attaquant"),
    )
    attacker_ammo = models.ForeignKey(
        "Item",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        limit_choices_to={"type": ITEM_AMMO},
        related_name="+",
        verbose_name=_("munitions de l'attaquant"),
    )
    defender_armor = models.ForeignKey(
        "Item",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        limit_choices_to={"type__in": (ITEM_ARMOR, ITEM_HELMET)},
        related_name="+",
        verbose_name=_("protection du défenseur"),
    )
    range = models.PositiveSmallIntegerField(default=0, verbose_name=_("distance"))
    body_part = models.CharField(max_length=10, choices=BODY_PARTS, verbose_name=_("partie du corps"))
    burst = models.BooleanField(default=False, verbose_name=_("tir en rafale ?"))
    hit_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("compteur de coups"))
    hit_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de précision"))
    hit_chance = models.SmallIntegerField(default=0, verbose_name=_("précision"))
    hit_roll = models.PositiveSmallIntegerField(default=0, verbose_name=_("jet de précision"))
    success = models.BooleanField(default=False, verbose_name=_("touché ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))
    status = models.CharField(max_length=20, choices=FIGHT_STATUS, blank=True, verbose_name=_("status"))
    damage = models.OneToOneField(
        "DamageHistory",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        limit_choices_to={"fight__isnull": False},
        related_name="fight",
        verbose_name=_("historique des dégâts"),
    )
    experience = models.PositiveSmallIntegerField(default=0, verbose_name=_("expérience"))
    level_up = models.BooleanField(default=False, verbose_name=_("niveau+ ?"))
    reason = models.TextField(blank=True, verbose_name=_("raison"))
    fail = None  # Placeholder for fight against a secondary target when critical fail

    class FightStats:
        """
        Statistiques des combats
        """

        def __init__(self, character: "Character", is_attacker: bool = True):
            self.character = character
            self.is_attacker = is_attacker
            self.total_count = self.total_damage = 0
            self.count_by_level = Counter()
            self.damage_by_level = Counter()
            self.stats = odict((((1, 1), [0, 0]), ((1, 0), [0, 0]), ((0, 0), [0, 0]), ((0, 1), [0, 0])))
            self.stats_by_level = {}

        def add(self, level: int, success: bool, critical: bool, count: int, damage: int) -> None:
            """
            Ajoute un combat aux statistiques
            :param level: Niveau
            :param success: Succès ?
            :param critical: Critique ?
            :param count: Nombre
            :param damage: Dégâts
            :return: Rien
            """
            self.total_count += count
            self.count_by_level[level] += 1
            self.total_damage += damage
            self.damage_by_level[level] += 1
            value = self.stats[success, critical]
            value[0] += count
            value[1] += damage
            value = self.stats_by_level.setdefault(
                level,
                odict((((1, 1), [0, 0]), ((1, 0), [0, 0]), ((0, 0), [0, 0]), ((0, 1), [0, 0]))),
            )[success, critical]
            value[0] += count
            value[1] += damage

        @property
        def all(self) -> List[Tuple[int, float, str, str]]:
            """
            Ventilation des statistiques par succès/échec
            :return: Liste ventilée par valeur, pourcentage, classe CSS et libellé
            """
            return [
                (
                    count,
                    round(((count / self.total_count) * 100) if self.total_count else 0, 2),
                    settings.CSS_CLASSES[success, critical],
                    get_label(success, critical),
                )
                for (success, critical), (count, damage) in self.stats.items()
            ]

        def get_all_by_level(self, level: int) -> List[Tuple[int, float, str, str]]:
            """
            Ventilation des statistiques par succès/échec en fonction du niveau
            :param level: Niveau cible
            :return: Liste ventilée par valeur, pourcentage, classe CSS et libellé
            """
            return [
                (
                    count,
                    round(((count / self.count_by_level[level]) * 100) if self.count_by_level.get(level) else 0, 2),
                    settings.CSS_CLASSES[success, critical],
                    get_label(success, critical),
                )
                for (success, critical), (count, damage) in self.stats_by_level.get(level, {}).items()
            ]

        @property
        def previous_stats(self) -> List[Tuple[int, float, str, str]]:
            return self.get_all_by_level(self.character.level - 1)

        @property
        def current_stats(self) -> List[Tuple[int, float, str, str]]:
            return self.get_all_by_level(self.character.level)

        @property
        def previous_total(self) -> int:
            return self.count_by_level.get(self.character.level - 1, 0)

        @property
        def current_total(self) -> int:
            return self.count_by_level.get(self.character.level, 0)

        @property
        def previous_damage(self) -> int:
            return self.damage_by_level.get(self.character.level - 1, 0)

        @property
        def current_damage(self) -> int:
            return self.damage_by_level.get(self.character.level, 0)

        @property
        def total_success(self) -> int:
            """
            Nombre total des succès
            """
            return sum(self.stats[1, x][0] for x in range(2))

        @property
        def success_rate(self) -> float:
            """
            Taux de succès
            """
            if not self.total_count:
                return 0.0
            return round(self.total_success * 100.0 / self.total_count, 1)

        @property
        def damage_rate(self) -> float:
            """
            Taux de dégâts
            """
            if not self.total_success:
                return 0.0
            return round(self.total_damage / self.total_success, 1)

    @staticmethod
    def get_stats(character: "Character") -> Tuple[FightStats, FightStats]:
        """
        Récupère les statistiques de combats
        :param character: Personnage
        :return: Liste des statistiques de combats
        """
        fights = (
            FightHistory.objects.filter(
                Q(attacker=character) | Q(defender=character),
                status__in=(
                    STATUS_HIT_SUCCEED,
                    STATUS_TARGET_KILLED,
                    STATUS_HIT_FAILED,
                ),
            )
            .annotate(
                is_attacker=Case(
                    When(attacker=character, then=Value(True, models.BooleanField())),
                    default=Value(False, models.BooleanField()),
                ),
                level=Case(
                    When(attacker=character, then=F("attacker_level")),
                    default=F("defender_level"),
                ),
            )
            .values("level", "success", "critical", "is_attacker")
            .annotate(count=Count("*"), damage=Sum("damage__real_damage"))
            .values_list("level", "is_attacker", "success", "critical", "count", "damage")
        )
        attacker, defender = FightHistory.FightStats(character, True), FightHistory.FightStats(character, False)
        for level, is_attacker, success, critical, count, damage in fights:
            (defender, attacker)[is_attacker].add(level, success, critical, count or 0, damage or 0)
        return attacker, defender

    @property
    def stop_burst(self):
        """
        Stoppe l'attaque en rafale ?
        """
        return self.status in (
            STATUS_NOT_ENOUGH_AP,
            STATUS_NO_MORE_AMMO,
            STATUS_WEAPON_BROKEN,
        )

    @property
    def css_class(self) -> str:
        """
        Classe CSS associée
        """
        return settings.CSS_CLASSES[self.success, self.critical]

    @property
    def message_level(self) -> str:
        """
        Niveau de message
        """
        return settings.MESSAGE_INFOS[self.success, self.critical]

    @property
    def pre_label(self) -> str:
        """
        Pré-libellé des acteurs
        """
        return _("🗡️️ {attacker} vs. {defender}").format(attacker=self.attacker, defender=self.defender)

    @property
    def label(self) -> str:
        """
        Libellé du combat
        """
        return get_label(self.success, self.critical)

    @property
    def long_label(self) -> str:
        """
        Libellé long du combat
        """
        if not self.damage:
            return _("{label} : {status}").format(label=self.label, status=self.get_status_display())
        return _("{label} : {status} - {damage}").format(
            label=self.label,
            status=self.get_status_display(),
            damage=self.damage_label,
        )

    @property
    def damage_label(self) -> str:
        """
        Libellé des dégâts infligés
        """
        if not self.damage:
            return ""
        return _("{real_damage} {damage_type} infligés ({body_part}) sur {base_damage}").format(
            real_damage=self.damage.real_damage,
            damage_type=self.damage.get_damage_type_display(),
            body_part=self.get_body_part_display(),
            base_damage=int(self.damage.base_damage),
        )

    @property
    def description(self) -> str:
        """
        Description du combat
        """
        if self.attacker_weapon:
            label_data = dict(
                weapon=self.attacker_weapon.name,
                skill_name=self.attacker_weapon.get_skill_display(),
                skill=gv(self.attacker.stats, self.attacker_weapon.skill),
            )
        else:
            label_data = dict(
                weapon=_("Combat à mains nues"),
                skill_name=LIST_SKILLS[SKILL_UNARMED],
                skill=gv(self.attacker.stats, SKILL_UNARMED),
            )
        weapon_label = _("{weapon} ({skill_name} = {skill}%)").format(**label_data)
        hit_label = _("{status} - {label} : {hit_roll} pour {hit_chance} ({hit_modifier})").format(
            status=self.get_status_display().capitalize(),
            label=self.label.capitalize(),
            hit_roll=self.hit_roll,
            hit_chance=self.hit_chance,
            hit_modifier=f"+{self.hit_modifier}" if self.hit_modifier >= 0 else self.hit_modifier,
        )
        base_label = _("{attacker} vs. {defender}\n{weapon_label}\n{hit_label}").format(
            attacker=self.attacker,
            defender=self.defender,
            weapon_label=weapon_label,
            hit_label=hit_label,
        )
        if not self.damage:
            return base_label
        return _("{base}\n{damage}").format(base=base_label, damage=self.damage_label)

    def __str__(self) -> str:
        return f"{self.pre_label} - {self.long_label}"

    class Meta:
        verbose_name = _("historique de combat")
        verbose_name_plural = _("historiques des combats")


class Log(CommonModel):
    """
    Journal
    """

    player = models.ForeignKey(
        "Player",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("joueur"),
    )
    character = models.ForeignKey(
        "Character",
        on_delete=models.CASCADE,
        related_name="+",
        verbose_name=_("personnage"),
    )
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    text = models.TextField(blank=True, verbose_name=_("texte"))
    private = models.BooleanField(default=False, verbose_name=_("privé ?"))

    @property
    def log_id(self):
        return str(self.pk or 0)

    def __str__(self):
        return _("{character} ({date})").format(character=self.character.name, date=self.game_date or self.date)

    class Meta:
        verbose_name = _("journal")
        verbose_name_plural = _("journaux")


# List of all models
MODELS = (
    Player,
    Campaign,
    Character,
    Statistics,
    Item,
    ItemModifier,
    Equipment,
    Effect,
    EffectModifier,
    CampaignEffect,
    CharacterEffect,
    Loot,
    LootTemplate,
    LootTemplateItem,
    RollHistory,
    DamageHistory,
    FightHistory,
    Log,
)

__all__ = (
    "ActiveEffect",
    "BaseStatistics",
    "Campaign",
    "CampaignEffect",
    "Character",
    "CharacterEffect",
    "Damage",
    "DamageHistory",
    "Effect",
    "EffectModifier",
    "Equipment",
    "FightHistory",
    "Item",
    "ItemModifier",
    "Log",
    "Loot",
    "LootTemplate",
    "LootTemplateItem",
    "MODELS",
    "Modifier",
    "Player",
    "Resistance",
    "RollHistory",
    "Statistics",
    "Stats",
)
