# encoding: utf-8
import logging
from typing import List

from common.models import Entity
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _

# Logger
logger = logging.getLogger(__name__)


class Statistics(models.Model):
    """
    Statistiques
    """
    SPECIAL_STRENGTH = 'strength'
    SPECIAL_PERCEPTION = 'perception'
    SPECIAL_ENDURANCE = 'endurance'
    SPECIAL_CHARISMA = 'charisma'
    SPECIAL_INTELLIGENCE = 'intelligence'
    SPECIAL_AGILITY = 'agility'
    SPECIAL_LUCK = 'luck'
    SPECIALS = (
        (SPECIAL_STRENGTH, _("force")),
        (SPECIAL_PERCEPTION, _("perception")),
        (SPECIAL_ENDURANCE, _("endurance")),
        (SPECIAL_CHARISMA, _("charisme")),
        (SPECIAL_INTELLIGENCE, _("intelligence")),
        (SPECIAL_AGILITY, _("agilité")),
        (SPECIAL_LUCK, _("chance")),
    )
    LIST_SPECIALS = [a for a, *_ in SPECIALS]

    SKILL_SMALL_GUNS = 'small_guns'
    SKILL_BIG_GUNS = 'big_guns'
    SKILL_ENERGY_WEAPONS = 'energy_weapons'
    SKILL_UNARMED = 'unarmed'
    SKILL_MELEE_WEAPONS = 'melee_weapons'
    SKILL_THROWING = 'throwing'
    SKILL_FIRST_AID = 'first_aid'
    SKILL_DOCTOR = 'doctor'
    SKILL_CHEMS = 'chems'
    SKILL_SNEAK = 'sneak'
    SKILL_LOCKPICK = 'lockpick'
    SKILL_STEAL = 'steal'
    SKILL_TRAPS = 'traps'
    SKILL_SCIENCE = 'science'
    SKILL_REPAIR = 'repair'
    SKILL_SPEECH = 'speech'
    SKILL_BARTER = 'barter'
    SKILL_GAMBLING = 'gambling'
    SKILL_SURVIVAL = 'survival'
    SKILL_KNOWLEDGE = 'knowledge'
    SKILLS = (
        (SKILL_SMALL_GUNS, _("armes à feu légères")),
        (SKILL_BIG_GUNS, _("armes à feu lourdes")),
        (SKILL_ENERGY_WEAPONS, _("armes à énergie")),
        (SKILL_UNARMED, _("à mains nues")),
        (SKILL_MELEE_WEAPONS, _("armes de mélée")),
        (SKILL_THROWING, _("armes de lancer")),
        (SKILL_FIRST_AID, _("premiers secours")),
        (SKILL_DOCTOR, _("médecine")),
        (SKILL_CHEMS, _("chimie")),
        (SKILL_SNEAK, _("discrétion")),
        (SKILL_LOCKPICK, _("crochetage")),
        (SKILL_STEAL, _("pickpocket")),
        (SKILL_TRAPS, _("pièges")),
        (SKILL_SCIENCE, _("science")),
        (SKILL_REPAIR, _("réparation")),
        (SKILL_SPEECH, _("discours")),
        (SKILL_BARTER, _("marchandage")),
        (SKILL_GAMBLING, _("hasard")),
        (SKILL_SURVIVAL, _("survie")),
        (SKILL_KNOWLEDGE, _("connaissance")),
    )
    LIST_SKILLS = [a for a, *_ in SKILLS]

    STAT_MAX_HEALTH = 'max_health'
    STAT_MAX_ACTION_POINTS = 'max_action_points'
    STAT_DAMAGE_RESISTANCE = 'damage_resistance'
    STAT_DAMAGE_THRESHOLD = 'damage_threashold'
    STAT_EVADE = 'evade'
    STAT_CARRY_WEIGHT = 'carry_weight'
    STAT_MELEE_DAMAGE = 'melee_damage'
    STAT_SEQUENCE = 'sequence'
    STAT_HEALING_RATE = 'healing_rate'
    STAT_CRITICAL_CHANCE = 'critical_chance'
    STATS = (
        (STAT_MAX_HEALTH, _("santé maximale")),
        (STAT_MAX_ACTION_POINTS, _("points d'action max.")),
        (STAT_DAMAGE_RESISTANCE, _("résistance aux dégâts")),
        (STAT_DAMAGE_THRESHOLD, _("seuil de dégâts")),
        (STAT_EVADE, _("esquive")),
        (STAT_CARRY_WEIGHT, _("charge maximale")),
        (STAT_MELEE_DAMAGE, _("attaque en mélée")),
        (STAT_SEQUENCE, _("initiative")),
        (STAT_HEALING_RATE, _("taux de regénération")),
        (STAT_CRITICAL_CHANCE, _("chance de critique")),
    )
    LIST_STATS = [a for a, *_ in STATS]

    RESISTANCE_RADIATION = 'radiation_resistance'
    RESISTANCE_POISON = 'poison_resistance'
    RESISTANCE_GAZ_CONTACT = 'gas_contact_resistance'
    RESISTANCE_GAZ_INHALED = 'gas_inhaled_resistance'
    RESISTANCE_FIRE = 'fire_resistance'
    RESISTANCE_ELECTRICITY = 'electricity_resistance'
    RESISTANCE_NORMAL_DAMAGE = 'normal_damage_resistance'
    RESISTANCE_FIRE_DAMAGE = 'fire_damage_resistance'
    RESISTANCE_LASER_DAMAGE = 'laser_damage_resistance'
    RESISTANCE_PLASMA_DAMAGE = 'plasma_damage_resistance'
    RESISTANCE_EXPLOSIVE_DAMAGE = 'explosive_damage_resistance'
    RESISTANCES = (
        (RESISTANCE_RADIATION, _("résistance aux radiations")),
        (RESISTANCE_POISON, _("résistance aux poisons")),
        (RESISTANCE_GAZ_CONTACT, _("résistance aux gaz (contact)")),
        (RESISTANCE_GAZ_INHALED, _("résistance aux gaz (inhalé)")),
        (RESISTANCE_FIRE, _("résistance au feu")),
        (RESISTANCE_ELECTRICITY, _("résistance à l'électricité")),
        (RESISTANCE_NORMAL_DAMAGE, _("résistance aux dégâts normaux")),
        (RESISTANCE_FIRE_DAMAGE, _("résistance aux dégâts de feu")),
        (RESISTANCE_LASER_DAMAGE, _("résistance aux dégâts de laser")),
        (RESISTANCE_PLASMA_DAMAGE, _("résistance aux dégâts de plasma")),
        (RESISTANCE_EXPLOSIVE_DAMAGE, _("résistance aux dégâts explosifs")),
    )
    LIST_RESISTANCES = [a for a, *_ in RESISTANCES]

    HIT_POINTS_PER_LEVEL = 'hit_points_per_level'
    SKILL_POINTS_PER_LEVEL = 'skill_points_per_level'
    LEVELED_STATS = (
        (HIT_POINTS_PER_LEVEL, _("points de santé par niveau")),
        (SKILL_POINTS_PER_LEVEL, _("points de compétence par niveau")),
    )
    LIST_LEVELED_STATS = [a for a, *_ in LEVELED_STATS]

    LIST_SECONDARY_STATS = LIST_STATS + LIST_RESISTANCES + LIST_LEVELED_STATS
    LIST_ALL_STATS = LIST_SPECIALS + LIST_SECONDARY_STATS

    # S.P.E.C.I.A.L.
    strength = models.PositiveSmallIntegerField(default=0, verbose_name=_("force"))
    perception = models.PositiveSmallIntegerField(default=0, verbose_name=_("perception"))
    endurance = models.PositiveSmallIntegerField(default=0, verbose_name=_("endurance"))
    charisma = models.PositiveSmallIntegerField(default=0, verbose_name=_("charisme"))
    intelligence = models.PositiveSmallIntegerField(default=0, verbose_name=_("intelligence"))
    agility = models.PositiveSmallIntegerField(default=0, verbose_name=_("agilité"))
    luck = models.PositiveSmallIntegerField(default=0, verbose_name=_("chance"))
    # Secondary statistics
    max_health = models.SmallIntegerField(default=0, verbose_name=_("santé maximale"))
    max_action_points = models.SmallIntegerField(default=0, verbose_name=_("points d'action max."))
    damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts"))
    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("seuil de dégâts"))
    evade = models.SmallIntegerField(default=0, verbose_name=_("esquive"))
    carry_weight = models.SmallIntegerField(default=0, verbose_name=_("charge maximale"))
    melee_damage = models.SmallIntegerField(default=0, verbose_name=_("attaque en mélée"))
    sequence = models.SmallIntegerField(default=0, verbose_name=_("initiative"))
    healing_rate = models.SmallIntegerField(default=0, verbose_name=_("taux de regénération"))
    critical_chance = models.SmallIntegerField(default=0, verbose_name=_("chance de critique"))
    # Resistances
    radiation_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux radiations"))
    poison_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux poisons"))
    gas_resistance_contact = models.SmallIntegerField(default=0, verbose_name=_("résistance aux gaz (contact)"))
    gas_resistance_inhaled = models.SmallIntegerField(default=0, verbose_name=_("résistance aux gaz (inhalé)"))
    fire_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance au feu"))
    electricity_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance à l'électricité"))
    normal_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts normaux"))
    fire_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts de feu"))
    laser_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts de laser"))
    plasma_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts de plasma"))
    explosive_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts explosifs"))
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
    # Per level
    hit_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("points de santé par niveau"))
    skill_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("points de compétence par niveau"))

    class Meta:
        abstract = True


class Character(Entity, Statistics):
    """
    Personnage
    """
    STAT_HEALTH = 'health'
    STAT_ACTION_POINTS = 'action_points'
    STAT_IRRADIATION = 'irradiation'
    STAT_EXPERIENCE = 'experience'
    STAT_KARMA = 'karma'
    GENERAL_STATS = (
        (STAT_EXPERIENCE, _("expérience")),
        (STAT_KARMA, _("karma")),
        (STAT_HEALTH, _("santé")),
        (STAT_ACTION_POINTS, _("points d'action")),
        (STAT_IRRADIATION, _("irradiation")),
    )

    RACE_HUMAN = 'human'
    RACE_GHOUL = 'ghoul'
    RACE_SUPER_MUTANT = 'super_mutant'
    RACE_DEATHCLAW = 'deathclaw'
    RACE_ROBOT = 'robot'
    RACES = (
        (RACE_HUMAN, _("humain")),
        (RACE_GHOUL, _("ghoul")),
        (RACE_SUPER_MUTANT, _("super-mutant")),
        (RACE_DEATHCLAW, _("écorcheur")),
        (RACE_ROBOT, _("robot")),
    )

    # Racial trait (bonus, min, max)
    RACES_STATS = {
        RACE_HUMAN: {
            Statistics.SPECIAL_STRENGTH: (0, 1, 10),
            Statistics.SPECIAL_PERCEPTION: (0, 1, 10),
            Statistics.SPECIAL_ENDURANCE: (0, 1, 10),
            Statistics.SPECIAL_CHARISMA: (0, 1, 10),
            Statistics.SPECIAL_INTELLIGENCE: (0, 1, 10),
            Statistics.SPECIAL_AGILITY: (0, 1, 10),
            Statistics.SPECIAL_LUCK: (0, 1, 10),
            Statistics.RESISTANCE_ELECTRICITY: (30, 0, 100),
        },
        RACE_GHOUL: {
            Statistics.SPECIAL_STRENGTH: (0, 1, 8),
            Statistics.SPECIAL_PERCEPTION: (0, 4, 13),
            Statistics.SPECIAL_ENDURANCE: (0, 1, 10),
            Statistics.SPECIAL_CHARISMA: (0, 1, 10),
            Statistics.SPECIAL_INTELLIGENCE: (0, 2, 10),
            Statistics.SPECIAL_AGILITY: (0, 1, 6),
            Statistics.SPECIAL_LUCK: (0, 5, 12),
            Statistics.RESISTANCE_RADIATION: (80, 0, 100),
            Statistics.RESISTANCE_POISON: (30, 0, 100),
        },
        RACE_SUPER_MUTANT: {
            Statistics.SPECIAL_STRENGTH: (0, 5, 13),
            Statistics.SPECIAL_PERCEPTION: (0, 1, 11),
            Statistics.SPECIAL_ENDURANCE: (0, 4, 11),
            Statistics.SPECIAL_CHARISMA: (0, 1, 7),
            Statistics.SPECIAL_INTELLIGENCE: (0, 1, 11),
            Statistics.SPECIAL_AGILITY: (0, 1, 8),
            Statistics.SPECIAL_LUCK: (0, 1, 10),
            Statistics.RESISTANCE_RADIATION: (50, 0, 100),
            Statistics.RESISTANCE_POISON: (20, 0, 100),
            Statistics.HIT_POINTS_PER_LEVEL: (2, None, None),
            Statistics.RESISTANCE_NORMAL_DAMAGE: (25, 0, 100),
            Statistics.RESISTANCE_FIRE_DAMAGE: (25, 0, 100),
            Statistics.RESISTANCE_LASER_DAMAGE: (25, 0, 100),
            Statistics.RESISTANCE_PLASMA_DAMAGE: (25, 0, 100),
            Statistics.RESISTANCE_EXPLOSIVE_DAMAGE: (25, 0, 100),
        },
        RACE_DEATHCLAW: {
            Statistics.SPECIAL_STRENGTH: (0, 6, 14),
            Statistics.SPECIAL_PERCEPTION: (0, 4, 12),
            Statistics.SPECIAL_ENDURANCE: (0, 1, 13),
            Statistics.SPECIAL_CHARISMA: (0, 1, 3),
            Statistics.SPECIAL_INTELLIGENCE: (0, 1, 4),
            Statistics.SPECIAL_AGILITY: (0, 6, 16),
            Statistics.SPECIAL_LUCK: (0, 1, 10),
            Statistics.HIT_POINTS_PER_LEVEL: (2, None, None),
            Statistics.STAT_MELEE_DAMAGE: (5, None, None),
            Statistics.STAT_DAMAGE_THRESHOLD: (4, None, None),
            Statistics.RESISTANCE_GAZ_CONTACT: (40, 0, 100),
            Statistics.RESISTANCE_GAZ_INHALED: (40, 0, 100),
            Statistics.RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_FIRE_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
        },
        RACE_ROBOT: {
            Statistics.SPECIAL_STRENGTH: (0, 7, 12),
            Statistics.SPECIAL_PERCEPTION: (0, 7, 12),
            Statistics.SPECIAL_ENDURANCE: (0, 7, 12),
            Statistics.SPECIAL_CHARISMA: (0, 1, 1),
            Statistics.SPECIAL_INTELLIGENCE: (0, 1, 12),
            Statistics.SPECIAL_AGILITY: (0, 1, 12),
            Statistics.SPECIAL_LUCK: (0, 5, 5),
            Statistics.HIT_POINTS_PER_LEVEL: (0, 0, 0),
            Statistics.RESISTANCE_RADIATION: (100, 0, 100),
            Statistics.RESISTANCE_POISON: (100, 0, 100),
            Statistics.RESISTANCE_GAZ_CONTACT: (100, 0, 100),
            Statistics.RESISTANCE_GAZ_INHALED: (100, 0, 100),
            Statistics.RESISTANCE_ELECTRICITY: (-50, 0, 100),
            Statistics.RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_LASER_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_PLASMA_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_FIRE_DAMAGE: (40, 0, 100),
            Statistics.RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
        },
    }

    # Statistics cache
    _stats = {}

    # General informations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("utilisateur"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    is_player = models.BooleanField(default=False, verbose_name=_("joueur ?"))
    name = models.CharField(max_length=100, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    race = models.CharField(max_length=12, choices=RACES, default=RACE_HUMAN, verbose_name=_("race"))
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_("niveau"))
    experience = models.PositiveIntegerField(default=0, verbose_name=_("expérience"))
    karma = models.SmallIntegerField(default=0, verbose_name=_("karma"))
    health = models.SmallIntegerField(default=0, verbose_name=_("santé"))
    action_points = models.SmallIntegerField(default=0, verbose_name=_("points d'action"))
    irradiation = models.SmallIntegerField(default=0, verbose_name=_("irradiation"))
    skill_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de compétences"))
    perk_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de talent"))
    # Tag skills
    tag_1 = models.CharField(max_length=20, choices=Statistics.SKILLS, verbose_name=_("spécialité 1"))
    tag_2 = models.CharField(max_length=20, choices=Statistics.SKILLS, verbose_name=_("spécialité 2"))
    tag_3 = models.CharField(max_length=20, choices=Statistics.SKILLS, verbose_name=_("spécialité 3"))
    tag_4 = models.CharField(max_length=20, choices=Statistics.SKILLS, blank=True, null=True, verbose_name=_("spécialité 4"))
    tag_5 = models.CharField(max_length=20, choices=Statistics.SKILLS, blank=True, null=True, verbose_name=_("spécialité 5"))
    # Others
    equipement = models.ManyToManyField('Item', blank=True, through=Equipment, verbose_name=_("inventaire"))

    class Stats:
        """
        Statistiques actuelle du personnage
        """
        def __init__(self, character: Character):
            # Racial traits
            stats = Character.RACES_STATS[character.race]
            # S.P.E.C.I.A.L.
            self.strength = character.strength
            self.perception = character.perception
            self.endurance = character.endurance
            self.charisma = character.charisma
            self.intelligence = character.intelligence
            self.agility = character.agility
            self.luck = character.luck
            self.change_all(stats, Statistics.LIST_SPECIALS)
            # Main statistics
            self.hit_points_per_level = character.hit_points_per_level + 3 + (self.endurance // 2)
            self.skill_points_per_level = character.skill_points_per_level + 5 + (2 * self.intelligence)
            # Secondary statistics
            self.max_health = (
                character.max_health + 15 + (self.strength + (2 * self.endurance)) +
                ((character.level - 1) * self.hit_points_per_level))
            self.max_action_points = character.max_action_points + 5 + (self.agility // 2)
            self.damage_resistance = character.damage_resistance
            self.damage_threshold = character.damage_threshold
            self.evade = character.armor_class + self.agility
            self.carry_weight = character.carry_weight + 25 + (25 * self.strength)
            self.melee_damage = character.melee_damage + max(0, self.strength - 5)
            self.sequence = character.sequence + 2 * self.perception
            self.healing_rate = character.healing_rate + (self.endurance // 3)
            self.critical_chance = character.critical_chance + self.luck
            # Resistances
            self.radiation_resistance = character.radiation_resistance + 2 * self.endurance
            self.poison_resistance = character.poison_resistance + 5 * self.endurance
            self.gas_resistance_contact = character.gas_resistance_contact
            self.gas_resistance_inhaled = character.gas_resistance_inhaled
            self.fire_resistance = character.fire_resistance
            self.electricity_resistance = character.electricity_resistance
            self.normal_damage_resistance = character.normal_damage_resistance
            self.fire_damage_resistance = character.fire_damage_resistance
            self.laser_damage_resistance = character.laser_damage_resistance
            self.plasma_damage_resistance = character.plasma_damage_resistance
            self.explosive_damage_resistance = character.explosive_damage_resistance
            # Skills
            self.small_guns = character.small_guns + 5 + (4 * self.agility)
            self.big_guns = character.big_guns + 2 * self.agility
            self.energy_weapons = character.energy_weapons + 2 * self.agility
            self.unarmed = character.unarmed + 30 + (2 * (self.strength + self.agility))
            self.melee_weapons = character.melee_weapons + 20 + (2 * (self.strength + self.agility))
            self.throwing = character.throwing + 4 * self.agility
            self.first_aid = character.first_aid + 2 * (self.perception + self.endurance)
            self.doctor = character.doctor + 5 + self.perception + self.intelligence
            self.chems = character.chems + 10 + (2 * self.intelligence)
            self.sneak = character.sneak + 5 + (3 * self.agility)
            self.lockpick = character.lockpick + 10 + self.perception + self.agility
            self.steal = character.steal + 3 * self.agility
            self.traps = character.traps + 10 + (2 * self.perception)
            self.science = character.science + 4 * self.intelligence
            self.repair = character.repair + 3 * self.intelligence
            self.speech = character.speech + 5 * self.charisma
            self.barter = character.barter + 4 * self.charisma
            self.gambling = character.gambling + 5 * self.luck
            self.survival = character.survival + 2 * (self.endurance + self.intelligence)
            self.knowledge = character.knowledge + 5 * self.intelligence
            # Tag skills
            for name in character.tags:
                self.change(name, +20)
            # Normalize
            self.change_all(stats, Statistics.LIST_SECONDARY_STATS)

        def change_all(self, stats, names):
            for name in names:
                values = stats.get(name, None)
                if values:
                    self.change(name, *values)

        def change(self, name, value=0, mini=None, maxi=None):
            old_value = getattr(self, name, 0)
            new_value = min(max(old_value + value, mini or float('-inf')), maxi or float('+inf'))
            logger.info("{}: {} => {}".format(name, old_value, new_value))
            setattr(self, name, new_value)

    class Meta:
        verbose_name = _("personnage")
        verbose_name_plural = _("personnages")

    @property
    def stats(self) -> Stats:
        stats = Character._stats.get(self.id) or Character.Stats(self)
        if self.id:
            Character._stats[self.id] = stats
        return stats

    @property
    def tags(self) -> List[str]:
        return [tag for tag in [self.tag_1, self.tag_2, self.tag_3, self.tag_4, self.tag_5] if tag]

    def save(self, *args, **kwargs):
        self.check_level()
        Character._stats.pop(self.id, None)
        super().save(*args, **kwargs)

    def clean(self):
        if len(self.tags) != len(set(self.tags)):
            raise ValidationError(_("Une spécialisation ne peut être choisie plus d'une fois."))

    def check_level(self) -> int:
        """
        Vérification du niveau en fonction de l'expérience
        :return: Niveau actuel
        """
        needed_xp = 0
        level = 2
        while True:
            needed_xp += (level - 1) * 1000
            if self.level >= level:
                continue
            if self.experience < needed_xp:
                break
            self.level += 1
            self.skill_points += self.stats.skill_points_per_level
            level += 1
        return level

    def roll(self, skill, malus=0):
        pass


class Item(Entity):
    """
    Objet
    """
    TYPE_WEAPON = 'weapon'
    TYPE_AMMO = 'ammo'
    TYPE_ARMOR = 'armor'
    TYPE_FOOD = 'food'
    TYPE_CHEM = 'chem'
    TYPE_MISC = 'misc'
    TYPES = (
        (TYPE_WEAPON, _("arme")),
        (TYPE_AMMO, _("munition")),
        (TYPE_ARMOR, _("armure")),
        (TYPE_FOOD, _("nourriture")),
        (TYPE_CHEM, _("drogue")),
        (TYPE_MISC, _("autre")),
    )

    DAMAGE_NORMAL = 'normal'
    DAMAGE_FIRE = 'fire'
    DAMAGE_LASER = 'laser'
    DAMAGE_PLASMA = 'plasma'
    DAMAGE_EXPLOSIVE = 'explosive'
    DAMAGE_TYPES = (
        (DAMAGE_NORMAL, _("normal")),
        (DAMAGE_FIRE, _("feu")),
        (DAMAGE_LASER, _("laser")),
        (DAMAGE_PLASMA, _("plasma")),
        (DAMAGE_EXPLOSIVE, _("explosif")),
    )

    name = models.CharField(max_length=100, verbose_name=_("nom"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    type = models.CharField(max_length=6, choices=TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    weight = models.PositiveSmallIntegerField(default=0, verbose_name=_("poids"))
    effects_wear = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets quand porté"))
    effects_use = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets quand utilisé"))
    effects_target = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets sur cible"))
    # Weapon
    ammo = models.ManyToManyField('Item', blank=True, verbose_name=_("type de munition"))
    damage_type = models.CharField(max_length=10, choices=DAMAGE_TYPES, default=DAMAGE_NORMAL, verbose_name=_("type de dégâts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    damage_bonus = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bonus"))
    range = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("portée"))
    clip_size = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("taille du chargeur"))
    ap_cost_normal = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA normal"))
    ap_cost_target = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA ciblé"))
    ap_cost_burst = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA rafale"))
    burst_count = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("munitions en rafale"))
    min_stength = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("force minimum"))
    # Ammo
    evasion_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur d'esquive"))
    damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de dégâts"))
    resistance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de résistance"))

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class Equipment(Entity):
    """
    Equipement
    """
    character = models.ForeignKey('Character', verbose_name=_("personnage"))
    item = models.ForeignKey('Item', verbose_name=_("objet"))
    count = models.PositiveIntegerField(default=0, verbose_name=_("nombre"))
    equiped = models.BooleanField(default=False, verbose_name=_("équipé ?"))
    condition = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("état"))

    class Meta:
        verbose_name = _("équipement")
        verbose_name_plural = _("équipements")


class Effect(Entity):
    """
    Effet
    """
