# coding: utf-8
from collections import OrderedDict as odict
from datetime import datetime, timedelta
from random import randint, choice
from typing import Dict, Iterable, List, Optional, Tuple, Union

from common.models import CommonModel, Entity
from common.utils import to_object
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Sum, FloatField
from django.utils.translation import ugettext as _
from multiselectfield import MultiSelectField

from fallout.constants import *  # noqa
from fallout.enums import *  # noqa


def get_thumbnails(directory: str='') -> List[Tuple[str, str]]:
    """
    Scanne les images le répertoire "medias" à la recherche de miniatures
    :param directory: Répertoire à scanner
    :return: Liste des images
    """
    import os
    import sys
    if any(command in sys.argv for command in ('makemigrations', 'migrate')):
        return []
    images = []
    try:
        dirname = os.path.join(settings.MEDIA_ROOT, 'thumbnail', directory)
        for filename in os.listdir(dirname):
            filepath = os.path.join(dirname, filename)
            title, ext = os.path.splitext(filename.replace('_', ' '))
            filename = os.path.join(directory, filename)
            if os.path.isdir(filepath):
                images.append((title, get_thumbnails(filename)))
            elif ext.lower() in ('.jpg', '.jpeg', '.gif', '.png'):
                url = os.path.join(settings.MEDIA_URL, 'thumbnail', filename).replace('\\', '/')
                images.append((url, title))
    except:
        pass
    return sorted(images)


def get_class(value: Union[int, float], maximum: Union[int, float], classes: Tuple[str]=None,
              values: Tuple[float]=None, reverse: bool=False, default: str='muted') -> str:
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
    classes = classes or ('primary', 'success', 'warning', 'danger')
    classes = reversed(classes) if reverse else classes
    values = values or (1.000, 0.666, 0.333, 0.000)
    rate = value / maximum
    for c, v in zip(classes, values):
        if rate >= v:
            return c
    return default


class Player(AbstractUser):
    """
    Joueur
    """
    nickname = models.CharField(max_length=100, blank=True, verbose_name=_("surnom"))
    phone_number = models.CharField(max_length=20, blank=True, verbose_name=_("numéro de téléphone"))

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
    image = models.ImageField(blank=True, upload_to='campaign', verbose_name=_("image"))
    thumbnail = models.CharField(blank=True, max_length=100, choices=get_thumbnails('campaign'), verbose_name=_("miniature"))
    game_master = models.ForeignKey(
        'Player', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name=_("maître du jeu"))
    start_game_date = models.DateTimeField(verbose_name=_("date de début"))
    current_game_date = models.DateTimeField(verbose_name=_("date courante"))
    current_character = models.ForeignKey(
        'Character', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name=_("personnage actif"))
    radiation = models.PositiveSmallIntegerField(default=0, verbose_name=_("rads par heure"))
    # Cache
    _effects = None

    @property
    def elapsed_time(self) -> timedelta:
        """
        Temps passé depuis le début de la campagne
        :return:
        """
        return self.current_game_date - self.start_game_date

    @property
    def effects(self) -> 'models.QuerySet[CampaignEffect]':
        """
        Retourne les effets actifs de la campagne
        :return: Effets
        """
        self._effects = self._effects if self._effects is not None else \
            self.active_effects.select_related('effect').prefetch_related('effect__modifiers').filter(
                Q(start_date__isnull=True) | Q(start_date__lte=F('campaign__current_game_date')),
                Q(end_date__isnull=True) | Q(end_date__gte=F('campaign__current_game_date')))
        return self._effects

    def clear_loot(self):
        """
        Supprime les butins non réclamés de la campagne
        """
        return self.loots.all().delete()

    def next_turn(self, seconds: int=TURN_TIME, resting: bool=False,
                  apply: bool=True, reset: bool=False) -> Optional['Character']:
        """
        Détermine qui est le prochain personnage à agir
        :param seconds: Temps utilisé (en secondes) par le personnage précédent pour son tour de jeu
        :param resting: Temps de repos ?
        :param apply: Applique directement le changement sur la campagne
        :param reset: Réinitialise l'ordre de passage des personnages
        :return: Personnage suivant
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
            if self.current_character and \
                    self.current_character.action_points != self.current_character.stats.max_action_points:
                self.current_character.action_points = self.current_character.stats.max_action_points
                self.current_character.save()
        return next_character

    def save(self, resting=False, *args, **kwargs):
        """
        Sauvegarde la campagne
        """
        self.previous_game_date = (self._copy.get('current_game_date') or self.current_game_date)
        difference = self.current_game_date - self.previous_game_date
        hours = round(difference.total_seconds() / 3600, 6)
        super().save(*args, **kwargs)
        if hours <= 0:
            return
        for character in self.characters.filter(is_active=True):
            character.update_needs(hours=hours, radiation=self.radiation, resting=resting, save=False)
            character.apply_effects(character, save=False)
            character.save()

    def get_absolute_url(self):
        """
        Retourne l'URL vers la page de la campagne
        """
        from django.urls import reverse
        return reverse('fallout_campaign', args=[str(self.pk)])

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("campagne")
        verbose_name_plural = _("campagnes")


class Stats(models.Model):
    """
    Statistiques actuelles du personnage
    """
    # S.P.E.C.I.A.L.
    strength = models.PositiveSmallIntegerField(default=1, verbose_name=_("force"))
    perception = models.PositiveSmallIntegerField(default=1, verbose_name=_("perception"))
    endurance = models.PositiveSmallIntegerField(default=1, verbose_name=_("endurance"))
    charisma = models.PositiveSmallIntegerField(default=1, verbose_name=_("charisme"))
    intelligence = models.PositiveSmallIntegerField(default=1, verbose_name=_("intelligence"))
    agility = models.PositiveSmallIntegerField(default=1, verbose_name=_("agilité"))
    luck = models.PositiveSmallIntegerField(default=1, verbose_name=_("chance"))
    # Secondary statistics
    max_health = models.PositiveSmallIntegerField(default=0, verbose_name=_("santé maximale"))
    max_action_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points d'action max."))
    armor_class = models.SmallIntegerField(default=0, verbose_name=_("esquive"))
    carry_weight = models.SmallIntegerField(default=0, verbose_name=_("charge maximale"))
    melee_damage = models.SmallIntegerField(default=0, verbose_name=_("attaque en mélée"))
    sequence = models.SmallIntegerField(default=0, verbose_name=_("initiative"))
    healing_rate = models.SmallIntegerField(default=0, verbose_name=_("taux de regénération"))
    critical_chance = models.SmallIntegerField(default=0, verbose_name=_("chances de critiques"))
    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption de dégâts"))
    damage_resistance = models.FloatField(default=0.0, verbose_name=_("résistance aux dégâts"))
    # Resistances
    normal_resistance = models.FloatField(default=0.0, verbose_name=_("résistance physique"))
    laser_resistance = models.FloatField(default=0.0, verbose_name=_("résistance au laser"))
    plasma_resistance = models.FloatField(default=0.0, verbose_name=_("résistance au plasma"))
    explosive_resistance = models.FloatField(default=0.0, verbose_name=_("résistance aux explosions"))
    fire_resistance = models.FloatField(default=0.0, verbose_name=_("résistance au feu"))
    gas_contact_resistance = models.FloatField(default=0.0, verbose_name=_("résistance au gaz (contact)"))
    gas_inhaled_resistance = models.FloatField(default=0.0, verbose_name=_("résistance au gaz (inhalé)"))
    electricity_resistance = models.FloatField(default=0.0, verbose_name=_("résistance à l'électricité"))
    poison_resistance = models.FloatField(default=0.0, verbose_name=_("résistance aux poisons"))
    radiation_resistance = models.FloatField(default=0.0, verbose_name=_("résistance aux radiations"))
    # Skills
    small_guns = models.SmallIntegerField(default=0, verbose_name=_("armes à feu légères"))
    big_guns = models.SmallIntegerField(default=0, verbose_name=_("armes à feu lourdes"))
    energy_weapons = models.SmallIntegerField(default=0, verbose_name=_("armes à énergie"))
    unarmed = models.SmallIntegerField(default=0, verbose_name=_("à mains nues"))
    melee_weapons = models.SmallIntegerField(default=0, verbose_name=_("armes de mélée"))
    throwing = models.SmallIntegerField(default=0, verbose_name=_("armes de lancer"))
    first_aid = models.SmallIntegerField(default=0, verbose_name=_("premiers secours"))
    doctor = models.SmallIntegerField(default=0, verbose_name=_("médecine"))
    chems = models.SmallIntegerField(default=0, verbose_name=_("chimie"))
    sneak = models.SmallIntegerField(default=0, verbose_name=_("discrétion"))
    lockpick = models.SmallIntegerField(default=0, verbose_name=_("crochetage"))
    steal = models.SmallIntegerField(default=0, verbose_name=_("pickpocket"))
    traps = models.SmallIntegerField(default=0, verbose_name=_("pièges"))
    science = models.SmallIntegerField(default=0, verbose_name=_("science"))
    repair = models.SmallIntegerField(default=0, verbose_name=_("réparation"))
    speech = models.SmallIntegerField(default=0, verbose_name=_("discours"))
    barter = models.SmallIntegerField(default=0, verbose_name=_("marchandage"))
    gambling = models.SmallIntegerField(default=0, verbose_name=_("hasard"))
    survival = models.SmallIntegerField(default=0, verbose_name=_("survie"))
    knowledge = models.SmallIntegerField(default=0, verbose_name=_("connaissance"))
    # Leveled stats
    hit_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("santé par niveau"))
    skill_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("compétences par niveau"))
    perk_rate = models.SmallIntegerField(default=0, verbose_name=_("niveaux pour un talent"))

    # Added at init
    character = None
    base = {}
    modifiers = {}

    def __str__(self) -> str:
        return self.character.name

    @staticmethod
    def get(character: 'Character') -> 'Stats':
        """
        Récupère toutes les statistiques à jour d'un personnage
        :param character: Personnage
        :return: Statistiques
        """
        stats = Stats()
        stats.base = {}
        stats.modifiers = {}
        stats.character = character
        # Get all character's stats
        for stats_name in LIST_EDITABLE_STATS:
            stats.base[stats_name] = getattr(character, stats_name, 0)
            setattr(stats, stats_name, getattr(character, stats_name, 0))
        # Racial modifiers
        race_stats = RACES_STATS.get(character.race, {})
        stats._change_all_stats(**race_stats)
        for stats_name, (value, mini, maxi) in race_stats.items():
            stats.base[stats_name] = stats.base.get(stats_name, 0) + value
        # Tag skills
        for skill in set(character.tag_skills):
            stats.base[skill] = stats.base.get(skill, 0) + TAG_SKILL_BONUS
            stats._change_stats(skill, TAG_SKILL_BONUS)
        # Base statistics
        base_stats = to_object(stats.base)
        base_stats.level = character.level
        for stats_name, formula in COMPUTED_STATS:
            result = stats.base[stats_name] = stats.base.get(stats_name, 0) + formula(base_stats, base_stats)
            setattr(base_stats, stats_name, result)

        # Survival modifiers
        for stats_name, survival in SURVIVAL_EFFECTS:
            for (mini, maxi), effects in survival.items():
                if (mini or 0) <= getattr(character, stats_name, 0) <= (maxi or float('+inf')):
                    stats._change_all_stats(**effects)
                    break
        # Equipment modifiers
        for equipment in character.inventory.exclude(slot=''):
            for modifier in equipment.item.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Active effects modifiers
        for effect in character.effects.exclude(effect__modifiers__isnull=True):
            for modifier in effect.effect.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Campaign effects modifiers
        if character.campaign:
            for effect in character.campaign.effects.exclude(effect__modifiers__isnull=True):
                for modifier in effect.effect.modifiers.all():
                    stats._change_stats(modifier.stats, modifier.value)
        # Derivated statistics
        for stats_name, formula in COMPUTED_STATS:
            stats._change_stats(stats_name, formula(stats, character))

        # Modifiers
        for stats_name in LIST_ALL_STATS:
            from_base = stats.base.get(stats_name, 0)
            from_stats = getattr(stats, stats_name, 0)
            if from_base == from_stats:
                continue
            stats.modifiers[stats_name] = from_stats - from_base
        return stats

    def _change_all_stats(self, **stats: Dict[str, Tuple[int, int, int]]) -> None:
        assert isinstance(self, Stats), _("Cette fonction ne peut être utilisée que par les statistiques.")
        for name, values in stats.items():
            self._change_stats(name, *values)

    def _change_stats(self, name: str, value: int=0, mini: int=None, maxi: int=None) -> None:
        assert isinstance(self, Stats), _("Cette fonction ne peut être utilisée que par les statistiques.")
        bonus, race_mini, race_maxi = RACES_STATS.get(self.character.race, {}).get(name, (None, None, None))
        target = self if name in LIST_EDITABLE_STATS else self.character
        mini = mini if mini is not None else race_mini or float('-inf')
        maxi = maxi if maxi is not None else race_maxi or float('+inf')
        result = min(max(getattr(target, name, 0) + value, mini), maxi)
        setattr(target, name, result)

    class Meta:
        abstract = True


class Character(Entity, Stats):
    """
    Personnage
    """
    # Technical informations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL,
        related_name='characters', verbose_name=_("utilisateur"))
    campaign = models.ForeignKey(
        'Campaign', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='characters', verbose_name=_("campagne"))
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='character', verbose_name=_("image"))
    thumbnail = models.CharField(blank=True, max_length=100, choices=get_thumbnails('character'), verbose_name=_("miniature"))
    race = models.CharField(max_length=12, choices=RACES, default=RACE_HUMAN, db_index=True, verbose_name=_("race"))
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_("niveau"))
    is_player = models.BooleanField(default=False, db_index=True, verbose_name=_("joueur ?"))
    is_active = models.BooleanField(default=True, db_index=True, verbose_name=_("actif ?"))
    is_resting = models.BooleanField(default=False, verbose_name=_("au repos ?"))
    # Primary statistics
    health = models.PositiveSmallIntegerField(default=0, verbose_name=_("santé"))
    action_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points d'action"))
    skill_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de compétence"))
    perk_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de talent"))
    experience = models.PositiveIntegerField(default=0, verbose_name=_("expérience"))
    karma = models.SmallIntegerField(default=0, verbose_name=_("karma"))
    # Needs
    rads = models.FloatField(default=0.0, verbose_name=_("rads"))
    thirst = models.FloatField(default=0.0, verbose_name=_("soif"))
    hunger = models.FloatField(default=0.0, verbose_name=_("faim"))
    sleep = models.FloatField(default=0.0, verbose_name=_("sommeil"))
    regeneration = models.FloatField(default=0.0, verbose_name=_("regénération"))
    # Tag skills
    tag_skills = MultiSelectField(max_length=200, choices=SKILLS, blank=True, verbose_name=_("spécialités"))
    # Cache
    _stats = {}
    _inventory = _equipment = _effects = None

    @staticmethod
    def clear_cache(character: Union['Character', int]):
        """
        Réinitialise le calcul des statistiques pour un personnage
        """
        if isinstance(character, Character):
            character = character.pk
        if character:
            Character._stats.pop(int(character), None)

    @property
    def stats(self) -> Stats:
        """
        Retourne les statistiques calculées du personnage
        :return: Statistiques
        """
        stats = Character._stats.get(self.pk) or Stats.get(self)
        if self.pk:
            Character._stats[self.pk] = stats
        return stats

    @property
    def inventory(self) -> 'models.QuerySet[Equipment]':
        """
        Retourne le contenu de l'inventaire du personnage
        :return: Equipements
        """
        self._inventory = self._inventory if self._inventory is not None else \
            self.equipments.select_related('item').prefetch_related('item__modifiers')
        return self._inventory

    @property
    def effects(self) -> 'models.QuerySet[CharacterEffect]':
        """
        Retourne les effets actifs du personnage
        :return: Effets
        """
        self._effects = self._effects if self._effects is not None else \
            self.active_effects.select_related('effect').prefetch_related('effect__modifiers').filter(
                Q(start_date__isnull=True) | Q(start_date__lte=F('character__campaign__current_game_date')),
                Q(end_date__isnull=True) | Q(end_date__gte=F('character__campaign__current_game_date')))
        return self._effects

    def _get_stats(self, stats: List[Tuple[str, str]], from_stats: bool=True) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Fonction interne pour retourner les valeurs des statistiques ciblées
        :param stats: Tuple de statistiques (code, libellé)
        :param from_stats: Récupère la valeur calculée et pas la valeur brute enregistrée
        :return: Liste des statistiques avec leur valeur
        """
        for code, label in stats:
            yield code, label, getattr(self.stats if from_stats else self, code, 0)

    @property
    def special(self) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Retourne le S.P.E.C.I.A.L.
        """
        for code, label, value in self._get_stats(SPECIALS):
            yield code, label, value, None, get_class(value, maximum=10)

    @property
    def skills(self) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Retourne les compétences
        """
        for code, label, value in self._get_stats(SKILLS):
            yield code, label, value, None, get_class(value, maximum=100)

    @property
    def general_stats(self) -> List[Tuple[str, str, Union[int, float], Optional[Union[int, float]], Optional[str]]]:
        """
        Retourne les statistiques générales
        :return: code, label, valeur à gauche, valeur à droite, classe
        """
        for code, label in GENERAL_STATS:
            lvalue = getattr(self, code, 0)
            rvalue, rclass = None, None
            if code == STATS_HEALTH:
                code = STATS_MAX_HEALTH
                rvalue = getattr(self.stats, STATS_MAX_HEALTH, 0)
                rclass = get_class(lvalue, rvalue)
            elif code == STATS_ACTION_POINTS:
                code = STATS_MAX_ACTION_POINTS
                rvalue = getattr(self.stats, STATS_MAX_ACTION_POINTS, 0)
                rclass = get_class(lvalue, rvalue)
            elif code == STATS_SKILL_POINTS:
                rvalue = lvalue
                lvalue = self.used_skill_points
            elif code == STATS_EXPERIENCE:
                rvalue = self.required_experience
            elif code in LIST_NEEDS:
                rvalue = 1000
                classes = ('primary', 'success', 'warning', 'danger', 'muted', 'muted')
                values = (1.000, 0.800, 0.600, 0.400, 0.200, 0.000)
                rclass = get_class(lvalue, rvalue, reverse=True, classes=classes, values=values)
            yield code, label, lvalue, rvalue, rclass
        yield (STATS_CARRY_WEIGHT, _("charge"), self.charge, self.stats.carry_weight,
               get_class(self.charge, self.stats.carry_weight, reverse=True))

    @property
    def secondary_stats(self) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Retourne les statistiques secondaires
        """
        for code, label, value in self._get_stats(SECONDARY_STATS):
            yield code, label, value

    @property
    def resistances(self) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Retourne les résistances
        """
        for code, label, value in self._get_stats(RESISTANCES):
            yield code, label, value, None, get_class(value, maximum=100)

    @property
    def other_stats(self) -> List[Tuple[str, str, Union[int, float]]]:
        """
        Retourne les autres statistiques
        :return:
        """
        for element in self.secondary_stats:
            if element[0] in (STATS_MAX_HEALTH, STATS_MAX_ACTION_POINTS, STATS_CARRY_WEIGHT):
                continue
            yield element
        for element in self.resistances:
            yield element

    @property
    def charge(self) -> float:
        """
        Retourne la charge totale de l'équipement
        """
        return self.equipments.aggregate(
            charge=Sum(F('quantity') * F('item__weight'), output_field=FloatField())
        ).get('charge') or 0

    @property
    def used_skill_points(self) -> float:
        """
        Retourne le nombre de points de compétences utilisées
        """
        return sum(getattr(self, skill) * (0.5 if skill in self.tag_skills else 1.0) for skill in LIST_SKILLS)

    @property
    def required_experience(self) -> int:
        """
        Retourne le nombre de points d'expérience nécessaires pour passer au niveau suivant
        """
        return sum(l * BASE_XP for l in range(1, self.level + 1))

    def get_need_label(self, need: str) -> str:
        """
        Retourne le libellé relatif au niveau d'un besoin
        :param need: Code du besoin
        :param value: Valeur du besoin
        :return: Libellé
        """
        value = getattr(self, need, 0.0)
        labels, effects = {
            STATS_RADS: (RADS_LABELS, RADS_EFFECTS),
            STATS_THIRST: (THIRST_LABELS, THIRST_EFFECTS),
            STATS_HUNGER: (HUNGER_LABELS, HUNGER_EFFECTS),
            STATS_SLEEP: (SLEEP_LABELS, SLEEP_EFFECTS),
        }[need]
        label = next(iter(label for (mini, maxi), label in labels.items() if mini <= value <= (maxi or float('inf'))))
        effects = next(iter(modifiers for (mini, maxi), modifiers in effects.items() if mini <= value <= (maxi or float('inf'))))
        effects = ", ".join(f"{modifier} {LIST_ALL_STATS[stats]}" for stats, (modifier, mini, maxi) in effects.items())
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
        for stats_name, value in self.stats.modifiers.items():
            yield stats_name, LIST_ALL_STATS.get(stats_name), value

    def modify_value(self, name: str, value: Union[int, float]) -> Union[int, float]:
        """
        Permet de modifier la valeur d'une statistique
        :param name: Nom de la statistique
        :param value: Valeur
        :return: Valeur actuelle
        """
        value = getattr(self, name, 0) + value
        setattr(self, name, value)
        return value

    def add_experience(self, amount: int=0, save: bool=True) -> Tuple[int, int]:
        """
        Ajoute de l'expérience à ce personnage
        :param amount: Quantité d'expérience ajoutée
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Niveau actuel, expérience requise jusqu'au niveau suivant
        """
        if amount:
            self.experience += amount
            if save:
                self.save()
        return self.level, self.required_experience

    def check_level(self) -> Tuple[int, int]:
        """
        Vérification du niveau en fonction de l'expérience
        :return: Niveau actuel, expérience requise jusqu'au niveau suivant
        """
        needed_xp = 0
        level = 2
        while True:
            needed_xp += (level - 1) * BASE_XP
            if self.level >= level:
                level += 1
                continue
            if self.experience < needed_xp:
                break
            self.level += 1
            self.skill_points += self.stats.skill_points_per_level
            if not self.level % self.stats.perk_rate:
                self.perk_points += 1
            level += 1
        return level, needed_xp

    def randomize(self, level: int=None, rate: float=0.0) -> None:
        """
        Randomise les statistiques d'un personnage jusqu'à un certain niveau
        :param level: Niveau du personnage à forcer
        :param rate: Pourcentage des points à répartir sur les spécialités
        :return: Rien
        """
        # Experience points for the targetted level
        level = level or self.level
        self.level = 1
        self.experience = sum((l - 1) * BASE_XP for l in range(2, level + 1))
        self.check_level()
        # Randomly distribute a fraction of the skill points on tag skills
        skill_points = self.skill_points
        for i in range(int(skill_points * rate)):
            self.modify_value(choice(self.tag_skills), 2)
            skill_points -= 1
        # Randomly distribute remaining skill points on other skills
        other_skills = list(set(LIST_SKILLS) - set(self.tag_skills)) if rate else LIST_SKILLS
        while skill_points:
            skill = choice(other_skills)
            self.modify_value(skill, 2 if skill in self.tag_skills else 1)
            skill_points -= 1
        # Reset health and action points to their maximum
        self.health = self.stats.max_health
        self.action_points = self.stats.max_action_points
        # Save the changes
        self.save()

    def update_needs(self, hours: float=0.0, radiation: int=0, resting: bool=True, save: bool=True) -> None:
        """
        Mise à jour des besoins
        :param hours: Nombre d'heures passées
        :param radiation: Radioactivité actuelle (en rads / heure)
        :param resting: Personnage en train de se reposer ?
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Rien
        """
        for stats_name, formula in COMPUTED_NEEDS:
            self.modify_value(stats_name, formula(self.stats, self) * hours)
        if radiation:
            self.damage(raw_damage=radiation * hours, damage_type=DAMAGE_RADIATION, save=False, log=False)
        self.regeneration += self.stats.healing_rate * (hours / 24.0) * (
            HEALING_RATE_RESTING_MULT if (resting or self.is_resting) else 1.0)
        if save:
            self.save(reset=False)

    def roll(self, stats: str, modifier: int=0, xp: bool=True, log: bool=True) -> 'RollHistory':
        """
        Réalise un jet de compétence pour un personnage
        :param stats: Code de la statistique
        :param modifier: Modificateur de jet éventuel
        :param xp: Gain d'expérience ?
        :param log: Historise le jet ?
        :return: Historique de jet
        """
        history = RollHistory(character=self, stats=stats, modifier=modifier)
        history.game_date = self.campaign and self.campaign.current_game_date
        is_special = stats in LIST_SPECIALS
        history.value = getattr(self.stats, stats, 0)
        history.roll = randint(1, 10 if is_special else (100 - randint(0, self.stats.luck)))
        history.success = history.roll <= (history.value + history.modifier)
        history.critical = (history.roll <= (1 if is_special else self.stats.luck)) if history.success \
            else (history.roll >= (CRITICAL_FAIL_D10 if is_special else CRITICAL_FAIL_D100))
        if log:
            history.save()
        if xp:
            self.add_experience(XP_GAIN_ROLL[history.success])
        return history

    def loot(self, empty: bool=True) -> List['Loot']:
        """
        Transforme l'équipement de ce personnage en butin
        :param empty: Vide l'inventaire du joueur ?
        :return: Liste des butins
        """
        if not self.campaign:
            return None
        loots = []
        equipements = self.inventory
        for equipement in equipements:
            loots.append(Loot.create(campaign=self.campaign, item=equipement.item, condition=equipement.condition))
        if empty:
            equipements.delete()
        return loots

    def burst(self, targets: Iterable[Tuple['Character', int]], hit_modifier: int=0,
              action: bool=True, log: bool=True) -> List['FightHistory']:
        """
        Permet de lancer une attaque en rafale sur un groupe d'ennemis
        :param targets: Liste de personnages ciblés avec leur distance relative (en cases) pour chacun dans un tuple
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param action: Consomme les points d'action de l'attaquant ?
        :param log: Historise le combat ?
        :return: Liste d'historiques de combat
        """
        histories = []
        attacker_weapon_equipment = self.inventory.filter(slot=ITEM_WEAPON).first()
        attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        assert attacker_weapon and attacker_weapon.burst_count != 0, _(
            "L'attaquant ne possède pas d'arme ou celle-ci ne permet pas d'attaque en rafale.")
        for hit in range(attacker_weapon.burst_count):
            target, target_range = choice(targets)
            history = self.fight(
                target, is_burst=True, target_range=target_range,
                hit_modifier=hit_modifier, action=action, hit=hit, log=log)
            histories.append(history)
        self.save()
        return histories

    def fight(self, target: 'Character', is_burst: bool=False, target_range: int=1, hit_modifier: int=0,
              target_part: BODY_PARTS=None, action: bool=True, hit: int=0, log: bool=True) -> 'FightHistory':
        """
        Calcul un round de combat entre deux personnages
        :param target: Personnage ciblé
        :param is_burst: Attaque en rafale ?
        :param target_range: Distance (en cases) entre les deux personnages
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param target_part: Partie du corps ciblée par l'attaquant (ou torse par défaut)
        :param action: Consomme les points d'action de l'attaquant ?
        :param hit: Compteur de coups lors d'une attaque en rafale
        :param log: Historise le combat ?
        :return: Historique de combat
        """
        if isinstance(target, (int, str)):
            target = Character.objects.get(pk=str(target))
        history = FightHistory(attacker=self, defender=target, burst=is_burst, hit_count=hit + 1, range=target_range)
        history.game_date = self.campaign and self.campaign.current_game_date
        # Equipment
        attacker_weapon_equipment = self.inventory.filter(slot=ITEM_WEAPON).first()
        attacker_ammo_equipment = self.inventory.filter(slot=ITEM_AMMO).first()
        attacker_weapon = history.attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        attacker_ammo = history.attacker_ammo = getattr(attacker_ammo_equipment, 'item', None)
        # Fight conditions
        if attacker_weapon and \
                (attacker_weapon.clip_size and attacker_weapon_equipment.clip_count <= 0) or \
                (attacker_weapon.is_throwable and attacker_weapon.quantity <= 0):
            history.status = STATUS_NO_MORE_AMMO
        elif target.health <= 0:
            history.status = STATUS_TARGET_DEAD
        elif attacker_weapon_equipment and attacker_weapon_equipment.condition <= 0.0:
            history.status = STATUS_WEAPON_BROKEN
        # Action points
        ap_cost = 0
        if action:
            if not is_burst:
                ap_cost_type = 'ap_cost_target' if target_part else 'ap_cost_normal'
                ap_cost = getattr(attacker_weapon, ap_cost_type, None) or AP_COST_FIGHT
            elif not hit:
                ap_cost = getattr(attacker_weapon, 'ap_cost_burst', None) or AP_COST_FIGHT
            if ap_cost > self.action_points:
                history.status = STATUS_NOT_ENOUGH_AP
        # Premature end of fight
        if history.status:
            if log:
                history.save()
            return history
        # Targetted body part modifiers and equipment
        body_part = target_part
        if not target_part:
            for body_part, chance in BODY_PARTS_RANDOM_CHANCES:
                if randint(1, 100) < chance:
                    break
        history.body_part = body_part = body_part or PART_TORSO
        ranged_hit_modifier, melee_hit_modifier, critical_modifier = BODY_PARTS_MODIFIERS[history.body_part]
        armor_slot = ITEM_HELMET if body_part in (PART_EYES, PART_HEAD) else ITEM_ARMOR
        defender_armor_equipment = target.inventory.filter(slot=armor_slot).first()
        defender_armor = history.defender_armor = getattr(defender_armor_equipment, 'item', None)
        # Chance to hit
        attacker_skill = getattr(attacker_weapon, 'skill', SKILL_UNARMED)
        is_melee = attacker_skill in (SKILL_UNARMED, SKILL_MELEE_WEAPONS)
        attacker_hit_chance = getattr(self.stats, attacker_skill, 0)  # Base skill and min strength modifier
        attacker_hit_chance += min(20 * (self.stats.strength - getattr(attacker_weapon, 'min_strength', 0)), 0)
        attacker_weapon_melee = getattr(attacker_weapon, 'is_melee', True)
        attacker_weapon_throwable = getattr(attacker_weapon, 'is_throwable', False)
        if attacker_weapon_melee:
            attacker_hit_range = max(getattr(attacker_weapon, 'range', 0), 1)
        else:
            attacker_range_stats = SPECIAL_STRENGTH if attacker_weapon_throwable else SPECIAL_PERCEPTION
            attacker_hit_range = max(getattr(attacker_weapon, 'range', 0) + getattr(attacker_ammo, 'range', 0), 0)
            attacker_hit_range += (2 * getattr(self.stats, attacker_range_stats, 0)) + 1
        attacker_hit_chance -= max(target_range - attacker_hit_range, 0) * FIGHT_RANGE_MALUS  # Range modifiers
        attacker_hit_chance += getattr(attacker_weapon, 'hit_chance_modifier', 0)  # Weapon hit chance modifier
        attacker_hit_chance += getattr(attacker_ammo, 'hit_chance_modifier', 0)  # Ammo hit chance modifier
        attacker_hit_chance -= getattr(defender_armor, 'armor_class', 0)  # Defender armor class modifier
        attacker_hit_chance -= target.stats.armor_class  # Armor class
        if target_part:
            attacker_hit_chance += melee_hit_modifier if attacker_skill == SKILL_UNARMED else ranged_hit_modifier
        attacker_hit_chance += hit_modifier  # Other modifiers
        attacker_hit_chance *= getattr(attacker_weapon_equipment, 'condition', 1.0)  # Weapon condition
        # Hit chance is null if attacker is melee/unarmed and target is farther than weapon range
        if target_range - attacker_hit_range > 0 and is_melee:
            attacker_hit_chance = 0
        history.hit_modifier = int(hit_modifier)
        history.hit_chance = int(max(attacker_hit_chance, 0))
        history.status = STATUS_HIT_FAILED
        attacker_hit_roll = history.hit_roll = randint(1, 100)
        history.success = attacker_hit_roll <= history.hit_chance
        history.critical = attacker_hit_roll >= CRITICAL_FAIL_D100
        self.add_experience(max(target.level - target.level, 1) * XP_GAIN_FIGHT[history.success], save=False)
        if history.success:
            # Critical chance
            critical_chance = getattr(self.stats, 'critical_chance', 0)
            critical_chance += critical_modifier
            critical_mult = 1.0 + (
                getattr(attacker_weapon, 'critical_modifier', 0.0) +
                getattr(attacker_ammo, 'critical_modifier', 0.0))
            critical_chance *= critical_mult
            # Apply damage
            history.status = STATUS_HIT_SUCCEED
            history.critical = critical = attacker_hit_roll < critical_chance
            attacker_damage_type = getattr(attacker_ammo, 'damage_type', None)
            attacker_damage_type = attacker_damage_type or getattr(attacker_weapon, 'damage_type') or DAMAGE_NORMAL
            damage = 0
            for item in (attacker_weapon, attacker_ammo):
                if not item:
                    continue
                damage += item.base_damage
            damage += self.stats.melee_damage if is_melee else 0
            damage_mult = 1.0 + (
                getattr(attacker_weapon, 'damage_modifier', 0.0) +
                getattr(attacker_weapon, 'damage_modifier', 0.0))
            damage *= damage_mult
            if critical:
                damage_mult = 1.0 + (
                    getattr(attacker_weapon, 'critical_damage', 0.0) +
                    getattr(attacker_ammo, 'critical_damage', 1.0) +
                    ((self.stats.strength / 10.0) if is_melee else 1.0))
                damage *= damage_mult
            threshold_modifier = getattr(attacker_weapon, 'threshold_modifier', 0)
            threshold_modifier += getattr(attacker_ammo, 'threshold_modifier', 0)
            resistance_modifier = 1.0 + getattr(attacker_weapon, 'resistance_modifier', 0.0)
            resistance_modifier += getattr(attacker_ammo, 'resistance_modifier', 0.0)
            history.damage = target.damage(
                raw_damage=damage, damage_type=attacker_damage_type, body_part=body_part, save=True,
                threshold_modifier=threshold_modifier, resistance_modifier=resistance_modifier)
            if not target.health:
                history.status = STATUS_TARGET_KILLED
            # On hit effects
            for item in (attacker_weapon, attacker_ammo, defender_armor):
                if not item:
                    continue
                for effect in item.effects.all():
                    effect.affect(target)
            target.apply_effects()  # Apply effects immediatly
        # Clip count & weapon condition
        if attacker_weapon_equipment and attacker_weapon:
            attacker_weapon_equipment.quantity -= 1 if attacker_weapon.is_throwable else 0
            if not attacker_weapon.is_melee:
                attacker_weapon_equipment.clip_count -= 1
            if not attacker_weapon.is_throwable:
                attacker_weapon_equipment.condition -= attacker_weapon_equipment.condition * (
                    getattr(attacker_weapon, 'condition_modifier', 0.0) +
                    getattr(attacker_ammo, 'condition_modifier', 0.0))
            attacker_weapon_equipment.save()
        # Save character and return history
        self.action_points -= ap_cost
        if not is_burst:
            self.save()
        if log:
            history.save()
        return history

    def damage(self, raw_damage: float=0.0, min_damage: int=0, max_damage: int=0, damage_type: str=DAMAGE_NORMAL,
               body_part: str=PART_TORSO, threshold_modifier: float=1.0, resistance_modifier: float=1.0,
               save: bool=True, log: bool=True) -> 'DamageHistory':
        """
        Inflige des dégâts au personnage
        :param raw_damage: Dégâts bruts
        :param min_damage: Dégâts minimum
        :param max_damage: Dégâts maximum
        :param damage_type: Type des dégâts
        :param body_part: Partie du corps touchée
        :param threshold_modifier: Modificateur d'absorption de dégâts (appliqué à l'armure et au personnage)
        :param resistance_modifier: Modificateur de résistance aux dégâts (appliqué à l'armure et au personnage)
        :param save: Sauvegarder les modifications sur le personnage ?
        :param log: Historise les dégâts ?
        :return: Nombre de dégâts
        """
        assert min_damage <= max_damage, _("Les bornes de dégâts min. et max. ne sont pas correctes.")
        history = DamageHistory(
            character=self, damage_type=damage_type, raw_damage=raw_damage,
            min_damage=min_damage, max_damage=max_damage)
        history.game_date = self.campaign and self.campaign.current_game_date
        # Base damage
        total_damage = raw_damage + randint(min_damage, max_damage)
        base_damage = history.base_damage = total_damage
        # Character already KO
        if damage_type != DAMAGE_HEAL and self.health <= 0:
            return history
        # Armor threshold and resistance
        armor_slot = ITEM_HELMET if damage_type == DAMAGE_GAZ_INHALED or (body_part in (PART_EYES, PART_HEAD)) else ITEM_ARMOR
        armor_equipment = self.inventory.filter(slot=armor_slot).first()
        armor = history.armor = getattr(armor_equipment, 'item', None)
        armor_damage = 0
        if armor and armor_equipment:
            armor_threshold = armor.get_threshold(damage_type) * threshold_modifier
            armor_resistance = armor.get_resistance(damage_type) * armor_equipment.condition * resistance_modifier
            total_damage -= max(armor_threshold, 0)
            total_damage *= (1.0 - min(armor_resistance, 1.0))
            armor_damage = max((base_damage - total_damage) * armor.condition_modifier, 0)
            # History
            history.armor_threshold = armor_threshold
            history.armor_resistance = armor_resistance
            history.armor_damage = armor_damage
        # Self threshold and resistance
        type_resistance = DAMAGE_RESISTANCE.get(damage_type)
        if type_resistance:
            damage_threshold = self.stats.damage_threshold * threshold_modifier
            damage_resistance = self.stats.damage_resistance + getattr(self.stats, type_resistance, 0.0) / 100.0
            damage_resistance *= resistance_modifier
        else:
            damage_threshold = 0
            damage_resistance = 0
        total_damage *= (-1.0 if damage_type == DAMAGE_HEAL else 1.0)
        total_damage -= max(damage_threshold, 0)
        total_damage *= (1.0 - min(damage_resistance, 1.0))
        total_damage = round(total_damage)  # TODO: round, floor or ceil?
        # Apply damage on self
        if total_damage:
            if damage_type == DAMAGE_RADIATION:
                self.rads += total_damage
            else:
                self.health -= total_damage
            if save:
                self.save()
        # Condition decrease on armor
        if armor_damage > 0 and damage_type in PHYSICAL_DAMAGES:
            armor_equipment.condition -= armor_damage
            armor_equipment.save()
        # History
        history.damage_threshold = damage_threshold
        history.damage_resistance = damage_resistance
        history.real_damage = total_damage
        if log:
            history.save()
        return history

    def apply_effects(self, campaign: Optional['Campaign']=None, save: bool=True) -> List['DamageHistory']:
        """
        Applique les effets actifs de la campagne et du personnage
        :param campaign: Campagne (pour application des effets associés)
        :param save: Sauvegarde les données relatives aux personnages
        :return: Liste des dégâts éventuellement subis
        """
        damages = []
        for effect in self.effects.filter(effect__interval__isnull=False):
            damage = effect.apply(save=save)
            if damage:
                damages.append(damage)
        if campaign:
            for effect in self.campaign.effects.filter(effect__interval__isnull=False):
                damage = effect.apply(save=save)
                if damage:
                    damages.append(damage)
        return damages

    def duplicate(self, equipments: bool=True, effects: bool=True) -> 'Character':
        """
        Duplique ce personnage
        :param equipments: Duplique également les équipements
        :param effects: Duplique également les effets
        :return: Personnage
        """
        assert self.pk, _("Ce personnage doit être préalablement enregistré avant d'être dupliqué.")
        character_id = self.pk
        self.save(force_insert=True)
        if equipments:
            for equipment in Equipment.objects.filter(character_id=character_id):
                equipment.character_id = self.pk
                equipment.save(force_insert=True)
        if effects:
            for effect in CharacterEffect.objects.filter(character_id=character_id):
                effect.character_id = self.pk
                effect.save(force_insert=True)
        return self

    def levelup(self, stats: str, value: int=0, save: bool=True) -> int:
        """
        Permet d'augmenter le niveau d'une compétence
        :param stats: Code de la compétence
        :param value: Valeur
        :param save: Sauvegarde le personne ?
        :return: Valeur courante
        """
        assert self.skill_points, _("Ce personnage n'a pas de points de compétences à distribuer.")
        assert value <= self.skill_points, _("Ce personnage n'a pas assez de points de compétences.")
        assert stats in LIST_SKILLS, _("Cette compétence ne peut être améliorée.")
        value = value * (2 if stats in self.tag_skills else 1)
        setattr(self, stats, getattr(self, stats) + value)
        if save:
            self.save()
        return getattr(self, stats)

    def save(self, *args, reset=True, **kwargs):
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
            Character.clear_cache(self.pk)
        stats = self.stats
        if self.pk:
            # Fixing health and action points
            self.health = self.stats.max_health if has_max_health and self.health > 0 else \
                max(0, min(self.health, self.stats.max_health))
            self.action_points = self.stats.max_action_points if has_max_action_points and self.action_points > 0 else \
                max(0, min(self.action_points, self.stats.max_action_points))
            # Remove current character on campaign if character is added or removed
            for campaign_id in self.modified.get('campaign_id') or []:
                if not campaign_id:
                    continue
                Campaign.objects.filter(id=campaign_id).update(current_character=None)
        else:
            self.health = self.stats.max_health
            self.action_points = self.stats.max_action_points
        # Loot character if NPC
        if self.is_active and not self.health and not self.is_player:
            self.loot(empty=True)
            self.is_active = False
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        Retourne l'URL vers la page du personnage
        """
        from django.urls import reverse
        return reverse('fallout_character', args=[str(self.pk)])

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("personnage")
        verbose_name_plural = _("personnages")


# Add property on Character for each stats
for stats, name in EDITABLE_STATS:
    def current_stats(self, stats=stats):
        return getattr(self.stats, stats, None)

    current_stats.short_description = name
    setattr(Character, '_' + stats, property(current_stats))


class Modifier(CommonModel):
    """
    Modificateur de statistique
    """
    stats = models.CharField(max_length=20, choices=ALL_STATS, verbose_name=_("statistique"))
    value = models.SmallIntegerField(default=0, verbose_name=_("valeur"))

    class Meta:
        abstract = True


class DamageMixin:
    """
    Mixin pour les fonctions de dégâts
    """

    @property
    def base_damage(self) -> int:
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
        if self.type not in [ITEM_WEAPON, ITEM_AMMO]:
            return ''
        damage = ''
        if self.min_damage or self.max_damage:
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
            return self.get_damage_type_display()
        return _(f"{self.label_damage} {self.get_damage_type_display()}")


class Item(Entity, DamageMixin):
    """
    Objet
    """
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='item', verbose_name=_("image"))
    thumbnail = models.CharField(blank=True, max_length=100, choices=get_thumbnails('item'), verbose_name=_("miniature"))
    type = models.CharField(max_length=6, choices=ITEM_TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    weight = models.FloatField(default=0.0, verbose_name=_("poids"))
    is_quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    # Weapon specific
    is_melee = models.BooleanField(default=False, verbose_name=_("arme de mêlée ?"))
    is_throwable = models.BooleanField(default=False, verbose_name=_("jetable ?"))
    skill = models.CharField(max_length=15, blank=True, choices=SKILLS, verbose_name=_("compétence"))
    min_strength = models.PositiveSmallIntegerField(default=0, verbose_name=_("force minimum"))
    clip_size = models.PositiveSmallIntegerField(default=0, verbose_name=_("taille du chargeur"))
    burst_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("munitions en rafale"))
    range = models.PositiveSmallIntegerField(default=0, verbose_name=_("modif. de portée"))
    hit_chance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. de précision"))
    threshold_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. d'absorption"))
    resistance_modifier = models.FloatField(default=0.0, verbose_name=_("modif. de resistance"))
    # Action points
    ap_cost_reload = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA recharge"))
    ap_cost_normal = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA normal"))
    ap_cost_target = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA ciblé"))
    ap_cost_burst = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA rafale"))
    # Damage
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    min_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts mini."))
    max_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts max."))
    damage_modifier = models.FloatField(default=0.0, verbose_name=_("modif. de dégâts"))
    critical_modifier = models.FloatField(default=0.0, verbose_name=_("chances de critiques"))
    critical_damage = models.FloatField(default=0.0, verbose_name=_("dégâts critiques"))
    # Resistances
    armor_class = models.SmallIntegerField(default=0, verbose_name=_("esquive"))
    condition_modifier = models.FloatField(default=0.0, verbose_name=_("modif. de condition"))
    normal_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption normal"))
    normal_resistance = models.FloatField(default=0.0, verbose_name=_("résistance normal"))
    laser_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption laser"))
    laser_resistance = models.FloatField(default=0.0, verbose_name=_("résistance laser"))
    plasma_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption plasma"))
    plasma_resistance = models.FloatField(default=0.0, verbose_name=_("résistance plasma"))
    explosive_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption explosifs"))
    explosive_resistance = models.FloatField(default=0.0, verbose_name=_("résistance explosifs"))
    fire_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption feu"))
    fire_resistance = models.FloatField(default=0.0, verbose_name=_("résistance feu"))
    # Effets and ammunitions
    effects = models.ManyToManyField(
        'Effect', blank=True,
        related_name='+', verbose_name=_("effets"))
    ammunitions = models.ManyToManyField(
        'Item', blank=True, limit_choices_to={'type': ITEM_AMMO},
        related_name='weapons', verbose_name=_("types de munitions"))

    @property
    def is_equipable(self) -> bool:
        """
        Objet équipable ?
        """
        return self.type in (ITEM_AMMO, ITEM_ARMOR, ITEM_HELMET, ITEM_WEAPON)

    @property
    def is_usable(self) -> bool:
        """
        Objet utilisable ?
        """
        return self.type in (ITEM_FOOD, ITEM_CHEM)

    @property
    def is_repairable(self) -> bool:
        """
        Objet réparable ?
        """
        return self.type in (ITEM_ARMOR, ITEM_HELMET, ITEM_WEAPON)

    def get_threshold(self, damage_type: str=DAMAGE_NORMAL) -> int:
        """
        Récupère le seuil de dégâts d'un type particulier
        """
        return getattr(self, damage_type + '_threshold', 0)

    def get_resistance(self, damage_type: str=DAMAGE_NORMAL) -> float:
        """
        Récupère la résistance aux dégâts d'un type
        """
        return getattr(self, damage_type + '_resistance', 0.0)

    def duplicate(self) -> 'Item':
        """
        Duplique cet objet
        :return: Objet
        """
        assert self.pk, _("Cet objet doit être préalablement enregistré avant d'être dupliqué.")
        item_id = self.pk
        self.save(force_insert=True)
        for modifier in ItemModifier.objects.filter(item_id=item_id):
            modifier.item_id = self.pk
            modifier.save(force_insert=True)
        return self

    def give(self, character: Union['Character', int], quantity: int=1,
             condition: float=1.0) -> Union[List['Equipment'], 'Equipment']:
        """
        Donne un ou plusieurs exemplaire de cet objet à un joueur ciblé
        :param character: Joueur
        :param quantity: Quantité
        :param condition: Etat
        :return: Equipement(s)
        """
        if self.is_repairable:
            equipments = []
            for i in range(quantity):
                equipments.append(Equipment.objects.create(
                    character=character, item=self, quantity=1, condition=condition))
            return equipments if len(equipments) > 2 else next(iter(equipments), None)
        else:
            equipment, created = Equipment.objects.get_or_create(
                character=character, item=self, defaults=dict(quantity=quantity, condition=condition))
            if not created:
                equipment.quantity += quantity
                equipment.save()
            return equipment

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class ItemModifier(Modifier):
    """
    Modificateur d'objet
    """
    item = models.ForeignKey(
        'Item', on_delete=models.CASCADE,
        related_name='modifiers', verbose_name=_("objet"))

    def __str__(self) -> str:
        return _(f"{self.get_stats_display()} = {self.value}")

    class Meta:
        verbose_name = _("modificateur d'objet")
        verbose_name_plural = _("modificateurs d'objets")


class Equipment(CommonModel):
    """
    Equipement
    """
    character = models.ForeignKey(
        'Character', on_delete=models.CASCADE,
        related_name='equipments', verbose_name=_("personnage"))
    item = models.ForeignKey(
        'Item', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("objet"))
    slot = models.CharField(max_length=6, choices=SLOT_ITEM_TYPES, blank=True, verbose_name=_("emplacement"))
    quantity = models.PositiveIntegerField(default=1, verbose_name=_("quantité"))
    clip_count = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("munitions"))
    condition = models.FloatField(blank=True, null=True, verbose_name=_("état"))

    @property
    def equiped(self) -> bool:
        """
        Identifie si l'objet est équipé
        :return:
        """
        return self.slot != ''

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
    def compatible_ammunition(self) -> Optional[List['Item']]:
        """
        Munitions compatibles
        """
        if self.slot or self.item.type != ITEM_AMMO:
            return
        weapon = self.character.inventory.filter(slot=ITEM_WEAPON).prefetch_related('ammunitions').first()
        return weapon and self.item in weapon.item.ammunitions.all()

    @property
    def current_condition(self) -> Optional[int]:
        """
        Etat actuel
        """
        if self.condition is not None:
            return int(self.condition * 100)
        return None

    def equip(self, action: bool=False) -> 'Equipment':
        """
        Permet d'équiper ou de déséquiper un objet
        :param action: Consommera des points d'action
        :return: Equipement
        """
        assert self.item.is_equipable, _(
            "Il n'est pas possible de s'équiper de ce type d'objet.")
        assert not action or self.character.action_points < AP_COST_EQUIP, _(
            "Le personnage ne possède plus assez de points d'actions pour s'équiper de cet objet.")

        def get_equipment(equipment: 'Equipment', slot: str) -> Optional['Equipment']:
            return Equipment.objects.filter(character_id=equipment.character_id, slot=slot).first()

        def handle_equipment(equipment: 'Equipment') -> None:
            if equipment.clip_count:
                ammo = get_equipment(equipment, ITEM_AMMO)
                if ammo:
                    ammo.quantity += equipment.clip_count
                    ammo.save()
                    equipment.clip_count = 0
            elif equipment.slot == ITEM_AMMO:
                weapon = get_equipment(equipment, ITEM_WEAPON)
                if weapon:
                    equipment.quantity += weapon.clip_count
                    weapon.clip_count = 0
                    weapon.save()
            equipment.slot = ''

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
        if action:
            self.character.action_points -= AP_COST_EQUIP
            self.character.save()
        return self

    def use(self, action: bool=False) -> List['CharacterEffect']:
        """
        Permet d'utiliser un objet
        :param action: Consommera des points d'action
        :return: Liste des effets
        """
        assert self.item.is_usable, _(
            "Il n'est pas possible d'utiliser ce type d'objet.")
        assert not action or self.character.action_points >= AP_COST_USE, _(
            "Le personnage ne possède plus assez de points d'actions pour utiliser cet objet.")
        assert self.quantity > 0, _(
            "Le personnage doit posséder au moins un exemplaire de cet objet pour l'utiliser.")
        effects = []
        for effect in self.item.effects.all():
            effects.append(CharacterEffect.objects.update_or_create(
                character=self.character, effect=effect,
                defaults=dict(start_date=None, end_date=None, next_date=None)))
        self.quantity -= 1
        self.save()
        if action:
            self.character.action_points -= AP_COST_USE
            self.character.save()
        return effects

    def drop(self, quantity: int=1, action: bool=False) -> 'Loot':
        """
        Permet de jeter un ou plusieurs objets
        :param quantity: Quantité
        :param action: Consommera des points d'action
        :return: Butin
        """
        assert self.quantity >= quantity, _(
            "Le personnage doit posséder la quantité d'objets qu'il souhaite jeter.")
        assert not action or self.character.action_points >= AP_COST_USE, _(
            "Le personnage ne possède plus assez de points d'actions pour jeter cet objet.")
        loot = Loot.create(
            campaign=self.character.campaign, item=self.item,
            quantity=quantity, condition=self.condition)
        self.quantity -= quantity
        self.save()
        if action:
            self.character.action_points -= AP_COST_DROP
            self.character.save()
        return loot

    def reload(self, action: bool=False) -> 'Equipment':
        """
        Permet de recharger une arme
        :param action: Consommera des points d'action
        :return: Equipement
        """
        assert self.slot == ITEM_WEAPON and self.item.clip_size, _(
            "Cet objet n'est pas une arme équipée ou ne peut être rechargé.")
        assert not action or self.character.action_points >= self.item.ap_cost_reload, _(
            "Le personnage ne possède plus assez de points d'actions pour jeter cet objet.")
        ammo = Equipment.objects.filter(character_id=self.character_id, slot=ITEM_AMMO).first()
        assert ammo and ammo.quantity > 0, _(
            "Il n'y a aucun type de munition équipé ou le nombre de munitions disponibles est insuffisant.")
        assert ammo.item in self.item.ammunitions.all(), _(
            "Cette arme est incompatible avec le type de munition équipé.")
        needed_ammo = min(self.item.clip_size - self.clip_count, ammo.quantity)
        ammo.quantity -= needed_ammo
        ammo.save()
        self.clip_count += needed_ammo
        self.save()
        if action:
            self.character.action_points -= self.item.ap_cost_reload
            self.character.save()
        return self

    def repair(self, value: Union[int, float]=100, action: bool=False) -> 'Equipment':
        """
        Permet de réparer un équipement détérioré
        :param value: Valeur de réparation
        :param action: Consommera des points d'action
        :return: Equipement
        """
        assert self.item.is_repairable, _("Cet objet n'est pas réparable.")
        assert not action or self.character.action_points >= AP_COST_REPAIR, _(
            "Le personnage ne possède plus assez de points d'actions pour réparer cet objet.")
        self.condition = (value / 100.0) if isinstance(value, int) else float(value)
        self.save()
        if action:
            self.character.action_points -= AP_COST_REPAIR
            self.character.save()
        return self

    def clean(self):
        """
        Validation de l'objet
        """
        if self.slot:
            if self.character.equipments.exclude(id=self.pk).filter(slot=self.slot).exists():
                raise ValidationError(dict(slot=_("Un autre objet est déjà présent à cet emplacement.")))
            if self.slot != self.item.type:
                raise ValidationError(dict(slot=_("L'emplacement doit correspondre au type d'objet.")))
        if self.slot == ITEM_AMMO:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_WEAPON).first()
            if equipment and not equipment.item.ammunitions.filter(id=self.item.pk).exists():
                raise ValidationError(dict(item=_("Ces munitions sont incompatibles avec l'arme équipée.")))
        elif self.slot == ITEM_WEAPON:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_AMMO).first()
            if equipment and not self.item.ammunitions.filter(id=equipment.item.pk).exists():
                raise ValidationError(dict(item=_("Cette arme est incompatible avec les munitions équipées.")))

    def save(self, *args, **kwargs):
        """
        Sauvegarde de l'objet
        """
        Character.clear_cache(self.character_id)
        if self.quantity <= 0:
            kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
            return self.delete(**kwargs)
        self.quantity = max(0, self.quantity) if self.quantity else 0
        self.condition = max(0.0, min(1.0, self.condition or 1.0)) if self.item.is_repairable else None
        self.clip_count = max(0, self.clip_count or 0) if self.item.type == ITEM_WEAPON and not self.item.is_melee else None
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
        return _(f"({self.character}) {self.item}")

    class Meta:
        verbose_name = _("équipement")
        verbose_name_plural = _("équipements")


class Effect(Entity, DamageMixin):
    """
    Effet
    """
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='effect', verbose_name=_("image"))
    thumbnail = models.CharField(
        blank=True, max_length=100, verbose_name=_("miniature"),
        choices=get_thumbnails('effect') + get_thumbnails('item'))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    duration = models.DurationField(blank=True, null=True, verbose_name=_("durée"))
    # Timed effects
    interval = models.DurationField(blank=True, null=True, verbose_name=_("intervalle"))
    damage_chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    min_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts min."))
    max_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts max."))
    # Next effect
    next_effect = models.ForeignKey(
        'Effect', blank=True, null=True, on_delete=models.CASCADE,
        related_name='+', verbose_name=_("effet suivant"))

    @property
    def damage_config(self) -> Dict[str, Union[str, int]]:
        """
        Dégâts de l'effet
        """
        return dict(
            raw_damage=self.raw_damage,
            min_damage=self.min_damage,
            max_damage=self.max_damage,
            damage_type=self.damage_type)

    def affect(self, target: Union['Campaign', 'Character']) -> Optional[Union['CampaignEffect', 'CharacterEffect']]:
        """
        Applique l'effet à un personnage ou une campagne
        :param target: Personnage ou campagne
        :return: Effect actif ou rien si l'effet ne s'applique pas
        """
        if randint(1, 100) >= self.chance:
            return None
        if isinstance(target, Campaign):
            return CampaignEffect.objects.get_or_create(
                campaign=target, effect=self,
                defaults=dict(start_date=target.current_game_date))
        elif isinstance(target, Character):
            assert self.duration is None or target.campaign is not None, _(
                "Le personnage doit faire partie d'une campagne pour lui appliquer un effet sur la durée.")
            return CharacterEffect.objects.get_or_create(
                character=target, effect=self,
                defaults=dict(start_date=getattr(target.campaign, 'current_game_date', None)))

    def duplicate(self) -> 'Effect':
        """
        Duplique cet effet
        :return: Effet
        """
        assert self.pk, _("Cet effet doit être préalablement enregistré avant d'être dupliqué.")
        effect_id = self.pk
        self.save(force_insert=True)
        for modifier in EffectModifier.objects.filter(effect_id=effect_id):
            modifier.effect_id = self.pk
            modifier.save(force_insert=True)
        return self

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")


class EffectModifier(Modifier):
    """
    Modificateur d'effet
    """
    effect = models.ForeignKey(
        'Effect', on_delete=models.CASCADE,
        related_name='modifiers', verbose_name=_("effet"))

    def __str__(self) -> str:
        return _(f"{self.get_stats_display()} = {self.value}")

    class Meta:
        verbose_name = _("modificateur d'effet")
        verbose_name_plural = _("modificateurs d'effets")


class ActiveEffect(CommonModel):
    """
    Effet actif
    """
    effect = models.ForeignKey(
        'Effect', on_delete=models.CASCADE,
        related_name = '+', verbose_name=_("effet"))
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'effet"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'arrêt"))
    next_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date suivante"))

    @property
    def progress(self) -> Optional[Tuple[Tuple[float, str, datetime], Tuple[float, str, datetime]]]:
        """
        Retourne l'état de progression de l'effet actif
        :return: Tuple avec la progression en pourcentage, la classe CSS et la date attendue
        """
        if not self.next_date:
            return None
        malus = self.effect.damage_type != DAMAGE_HEAL
        total = (self.end_date - self.start_date) / self.effect.interval
        elapsed = ((self.next_date - self.start_date) / self.effect.interval) / total
        remaining = ((self.end_date - self.next_date) / self.effect.interval) / total
        return (
            (round(elapsed * 100.0, 2), 'success' if malus else 'danger', self.next_date),
            (round(remaining * 100.0, 2), 'danger' if malus else 'success', self.end_date),
        )

    class Meta:
        abstract = True


class CampaignEffect(ActiveEffect):
    """
    Effet actif dans une campagne
    """
    campaign = models.ForeignKey(
        'Campaign', on_delete=models.CASCADE,
        related_name='active_effects', verbose_name=_("campagne"))

    def apply(self, save: bool=True) -> Dict['Character', List['DamageHistory']]:
        """
        Applique l'effet aux personnages de la campagne
        :param save: Sauvegarde les données relatives aux personnages ?
        :return: Dégâts potentiels infligés
        """
        damages = {}
        if not self.next_date and self.effect.interval:
            self.next_date = self.start_date
        if not self.next_date:
            return damages
        game_date = self.campaign.current_game_date
        while self.next_date <= game_date:
            for character in self.campaign.characters.all():
                damage = character.damage(save=save, **self.effect.damage_config)
                if not damage:
                    continue
                damages[character] = damages.get(character, []) + [damage]
            self.next_date += self.effect.interval
        self.save()
        return damages

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'effet actif
        """
        for character_id in self.campaign.characters.values_list('pk', flat=True):
            Character.clear_cache(character_id)
        if not self.start_date:
            self.start_date = self.campaign.current_game_date
        if not self.end_date and self.start_date and self.effect.duration:
            self.end_date = self.start_date + self.effect.duration
        if not self.next_date and self.start_date and self.effect.interval:
            self.next_date = self.start_date + self.effect.interval
        if self.end_date and self.end_date <= self.campaign.current_game_date:
            if self.effect.next_effect:
                self.effect.next_effect.affect(self.campaign)
            kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
            return self.delete(**kwargs)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return _(f"({self.campaign}) {self.effect}")

    class Meta:
        verbose_name = _("effet de campagne")
        verbose_name_plural = _("effets de campagne")


class CharacterEffect(ActiveEffect):
    """
    Effet actif sur un personnage
    """
    character = models.ForeignKey(
        'Character', on_delete=models.CASCADE,
        related_name='active_effects', verbose_name=_("personnage"))

    def apply(self, save: bool=True) -> Optional['DamageHistory']:
        """
        Applique l'effet au personnage
        :param save: Sauvegarde les données relatives au personnage ?
        :return: Liste des dégâts éventuellement subis
        """
        damage = None
        if not self.next_date and self.effect.interval:
            self.next_date = self.start_date
        if not self.character.campaign and not self.next_date:
            return damage
        game_date = self.character.campaign.current_game_date
        while self.next_date <= game_date:
            damage = self.character.damage(save=save, **self.effect.damage_config)
            self.next_date += self.effect.interval
        self.save()
        return damage

    def save(self, *args, **kwargs):
        """
        Sauvegarde l'effet actif
        """
        Character.clear_cache(self.character_id)
        if not self.start_date and self.character.campaign:
            self.start_date = self.character.campaign.current_game_date
        if not self.end_date and self.start_date and self.effect.duration:
            self.end_date = self.start_date + self.effect.duration
        if self.character.campaign:
            if not self.next_date and self.start_date and self.effect.interval:
                self.next_date = self.start_date + self.effect.interval
            if self.end_date and self.end_date <= self.character.campaign.current_game_date:
                if self.effect.next_effect:
                    self.effect.next_effect.affect(self.character)
                kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
                return self.delete(**kwargs)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return _(f"({self.character}) {self.effect}")

    class Meta:
        verbose_name = _("effet de personnage")
        verbose_name_plural = _("effets de personnage")


class Loot(CommonModel):
    """
    Butin
    """
    campaign = models.ForeignKey(
        'Campaign', blank=True, null=True, on_delete=models.CASCADE,
        related_name='loots', verbose_name=_("campagne"))
    item = models.ForeignKey(
        'Item', on_delete=models.CASCADE,
        related_name='loots', verbose_name=_("objet"))
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

    def take(self, character: Union['Character', int], quantity: int=1, action: bool=False) -> 'Equipment':
        """
        Permet à un personnage de prendre un ou plusieurs objets du butin
        :param character: Personnage
        :param quantity: Nombre d'objets à prendre
        :param action: Consommera des points d'action
        :return: Equipement
        """
        if isinstance(character, (int, str)):
            character = Character.objects.get(pk=character)
        assert self.campaign_id == character.campaign_id, _(
            "Le personnage doit être dans la même campagne.")
        assert not action or character.action_points < AP_COST_TAKE, _(
            "Le personnage ne possède plus assez de points d'actions pour s'équiper de cet objet.")
        quantity = max(0, min(quantity, self.quantity))
        equipment = Equipment.objects.select_related('item').filter(character=character, item=self.item).first()
        if equipment and not equipment.item.is_repairable:
            equipment.quantity += quantity
            equipment.save()
        else:
            equipment = Equipment.objects.create(
                character=character,
                item=self.item,
                quantity=quantity,
                condition=self.condition)
        if quantity >= self.quantity:
            self.delete()
        else:
            self.quantity -= quantity
            self.save()
        if action:
            character.action_points -= AP_COST_TAKE
            character.save()
        return equipment

    @classmethod
    def create(cls, campaign: Union['Campaign', int], item: Union['Item', int],
               quantity: int=1, condition: float=1.0) -> 'Loot':
        if isinstance(item, (int, str)):
            item = Item.objects.get(pk=int(item))
        try:
            assert not item.is_repairable
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
            kwargs = {k: v for k, v in kwargs.items() if k.startswith('_')}
            return self.delete(**kwargs)
        self.quantity = max(0, self.quantity) if self.quantity else 0
        self.condition = max(0.0, min(1.0, self.condition or 1.0)) if self.item.is_repairable else None
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return _(f"({self.campaign}) {self.item}")

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
    image = models.ImageField(blank=True, upload_to='loot', verbose_name=_("image"))
    thumbnail = models.CharField(blank=True, max_length=100, choices=get_thumbnails('item'), verbose_name=_("miniature"))

    def create(self, campaign: Union['Campaign', int], character: Optional[Union['Character', int]]=None):
        """
        Permet de créer un butin à partir du modèle (éventuellement en fonction de la chance du personnage)
        :param campaign: Campagne
        :param character: Personnage
        :return: Liste de butins
        """
        loots = []
        if isinstance(campaign, (int, str)):
            campaign = Campaign.objects.get(pk=campaign)
        chance_modifier = 0
        if character:
            if isinstance(character, (int, str)):
                character = Character.objects.get(pk=character)
            chance_modifier = character.stats.luck
        assert not character or campaign.pk == character.campaign_id, _(
            "Le personnage concerné doit être dans la même campagne que le butin a créer.")
        for template in self.items.select_related('item').all():
            chance = randint(1, 100 - randint(0, chance_modifier) * 2)
            if chance > template.chance:
                continue
            loots.append(Loot.create(
                campaign=campaign, item=template.item,
                quantity=randint(template.min_quantity, template.max_quantity),
                condition=randint(template.min_condition * 100, template.max_condition * 100) / 100))
        return loots

    def duplicate(self) -> 'LootTemplate':
        """
        Duplique ce modèle de butin
        :return: Modèle de butin
        """
        assert self.pk, _("Ce modèle de butin doit être préalablement enregistré avant d'être dupliqué.")
        template_id = self.pk
        self.save(force_insert=True)
        for item in LootTemplateItem.objects.filter(template_id=template_id):
            item.template_id = self.pk
            item.save(force_insert=True)
        return self

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("modèle de butin")
        verbose_name_plural = _("modèles des butins")


class LootTemplateItem(CommonModel):
    """
    Objet de butin
    """
    template = models.ForeignKey(
        'LootTemplate', on_delete=models.CASCADE,
        related_name='items', verbose_name=_("modèle"))
    item = models.ForeignKey(
        'Item', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("objet"))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    min_quantity = models.PositiveIntegerField(default=1, verbose_name=_("nombre min."))
    max_quantity = models.PositiveIntegerField(default=1, null=True, verbose_name=_("nombre max."))
    min_condition = models.FloatField(default=1.0, verbose_name=_("état min."))
    max_condition = models.FloatField(default=1.0, verbose_name=_("état max."))

    def __str__(self) -> str:
        return _(f"({self.template}) {self.item}")

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
        'Character', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("personnage"))
    stats = models.CharField(max_length=10, blank=True, choices=ROLL_STATS, verbose_name=_("statistique"))
    value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur"))
    modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur"))
    roll = models.PositiveIntegerField(default=0, verbose_name=_("jet"))
    success = models.BooleanField(default=False, verbose_name=_("succès ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))

    class RollStats:
        """
        Statistiques des jets
        """
        def __init__(self, character: Union['Character', int], code: str, label: str):
            self.character = character
            self.code = code
            self.label = label
            self.count = 0
            self.stats = odict((((1, 1), 0), ((1, 0), 0), ((0, 0), 0), ((0, 1), 0)))

        def add(self, success: bool, critical: bool):
            """
            Ajoute un jet aux statistiques
            :param success: Succès ?
            :param critical: Critique ?
            :return: Rien
            """
            self.count += 1
            self.stats[success, critical] += 1

        @property
        def all(self) -> List[Tuple[int, float, str]]:
            """
            Ventilation des statistiques par succès/échec
            :return: Liste ventilée par valeur, pourcentage et classe CSS
            """
            return [(
                value,
                round((value / self.count) * 100 if self.count else 0, 2),
                settings.CSS_CLASSES[key],
            ) for key, value in self.stats.items()]

        @property
        def success_rate(self) -> float:
            return round((self.stats[1, 0] + self.stats[1, 1]) / self.count, 2) * 100

    @staticmethod
    def get_stats(character: Union['Character', int]):
        """
        Récupère les statistiques de jets
        :param character: Personnage
        :return: Liste des statistiques de jets
        """
        stats = odict()
        for code, label in SPECIALS + SKILLS:
            stats[code] = RollHistory.RollStats(character, code, label)
        for roll in RollHistory.objects.only('stats', 'success', 'critical').filter(character=character).iterator():
            stats[roll.stats].add(roll.success, roll.critical)
        return list(stats.values())

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
        return {v: k for k, v in settings.MESSAGE_TAGS.items()}.get(self.css_class) or 10  # Debug

    @property
    def label(self) -> str:
        """
        Libellé du jet
        """
        return ' '.join((
            [_("échec"), _("réussite")][self.success],
            ['', _("critique")][self.critical])).strip()

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
            total=self.value + self.modifier)

    def __str__(self) -> str:
        return _(f"({self.character}) - {self.label}")

    class Meta:
        verbose_name = _("historique de jet")
        verbose_name_plural = _("historiques des jets")


class DamageHistory(CommonModel):
    """
    Historique des dégâts
    """
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    character = models.ForeignKey(
        'Character', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("personnage"))
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    min_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts min."))
    max_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts max."))
    base_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts de base"))
    armor = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE,
        limit_choices_to={'type__in': (ITEM_ARMOR, ITEM_HELMET)},
        related_name='+', verbose_name=_("protection"))
    armor_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption armure"))
    armor_resistance = models.FloatField(default=0.0, verbose_name=_("résistance armure"))
    armor_damage = models.FloatField(default=0.0, verbose_name=_("dégats armure"))
    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("absorption dégâts"))
    damage_resistance = models.FloatField(default=0.0, verbose_name=_("résistance dégâts"))
    real_damage = models.SmallIntegerField(default=0, verbose_name=_("dégâts réels"))

    def __str__(self) -> str:
        return _(f"({self.character}) - {self.label}")

    @property
    def label(self) -> str:
        return _(f"{self.get_damage_type_display()} de {self.real_damage}")

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
        'Character', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("attaquant"))
    defender = models.ForeignKey(
        'Character', on_delete=models.CASCADE,
        related_name='+', verbose_name=_("défenseur"))
    attacker_weapon = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE,
        limit_choices_to={'type': ITEM_WEAPON},
        related_name='+', verbose_name=_("arme de l'attaquant"))
    attacker_ammo = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE,
        limit_choices_to={'type': ITEM_AMMO},
        related_name='+', verbose_name=_("munitions de l'attaquant"))
    defender_armor = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE,
        limit_choices_to={'type__in': (ITEM_ARMOR, ITEM_HELMET)},
        related_name='+', verbose_name=_("protection du défenseur"))
    range = models.PositiveSmallIntegerField(default=0, verbose_name=_("distance"))
    body_part = models.CharField(max_length=5, choices=BODY_PARTS, verbose_name=_("partie du corps"))
    burst = models.BooleanField(default=False, verbose_name=_("tir en rafale ?"))
    hit_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("compteur de coups"))
    hit_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. de précision"))
    hit_chance = models.SmallIntegerField(default=0, verbose_name=_("précision"))
    hit_roll = models.PositiveSmallIntegerField(default=0, verbose_name=_("jet de précision"))
    success = models.BooleanField(default=False, verbose_name=_("touché ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))
    status = models.CharField(max_length=15, choices=FIGHT_STATUS, blank=True, verbose_name=_("status"))
    damage = models.OneToOneField(
        'DamageHistory', blank=True, null=True, on_delete=models.CASCADE,
        limit_choices_to={'fight__isnull': False},
        related_name='fight', verbose_name=_("historique des dégâts"))

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
        return {v: k for k, v in settings.MESSAGE_TAGS.items()}.get(self.css_class) or ''

    @property
    def label(self) -> str:
        """
        Libellé du combat
        """
        return ' '.join((
            [_("échec"), _("réussite")][self.success],
            ['', _("critique")][self.critical])).strip()

    @property
    def long_label(self) -> str:
        """
        Libellé long du combat
        :return:
        """
        if not self.damage:
            return _(f"{self.label} : {self.get_status_display()}")
        return _(f"{self.label} : {self.damage.real_damage} dégât(s) infligé(s)")

    def __str__(self) -> str:
        return _(f"{self.attacker} vs. {self.defender} - {self.long_label}")

    class Meta:
        verbose_name = _("historique de combat")
        verbose_name_plural = _("historiques des combats")


# List of all models
MODELS = (
    Player,
    Campaign,
    Character,
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
)
