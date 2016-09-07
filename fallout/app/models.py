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


# S.P.E.C.I.A.L.
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

# General statistics
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
LIST_GENERAL_STATS = [a for a, *_ in GENERAL_STATS]

# Secondary statistics
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
SECONDARY_STATS = (
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
LIST_SECONDARY_STATS = [a for a, *_ in SECONDARY_STATS]

# Skills
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

# Resistances
RESISTANCE_RADIATION = 'radiation_resistance'
RESISTANCE_POISON = 'poison_resistance'
RESISTANCE_FIRE = 'fire_resistance'
RESISTANCE_ELECTRICITY = 'electricity_resistance'
RESISTANCE_GAZ_CONTACT = 'gas_contact_resistance'
RESISTANCE_GAZ_INHALED = 'gas_inhaled_resistance'
RESISTANCE_NORMAL_DAMAGE = 'normal_damage_resistance'
RESISTANCE_LASER_DAMAGE = 'laser_damage_resistance'
RESISTANCE_PLASMA_DAMAGE = 'plasma_damage_resistance'
RESISTANCE_EXPLOSIVE_DAMAGE = 'explosive_damage_resistance'
RESISTANCES = (
    (RESISTANCE_RADIATION, _("radiations")),
    (RESISTANCE_POISON, _("poisons")),
    (RESISTANCE_FIRE, _("feu")),
    (RESISTANCE_ELECTRICITY, _("électricité")),
    (RESISTANCE_GAZ_CONTACT, _("gaz (contact)")),
    (RESISTANCE_GAZ_INHALED, _("gaz (inhalé)")),
    (RESISTANCE_NORMAL_DAMAGE, _("dégâts normaux")),
    (RESISTANCE_LASER_DAMAGE, _("dégâts de laser")),
    (RESISTANCE_PLASMA_DAMAGE, _("dégâts de plasma")),
    (RESISTANCE_EXPLOSIVE_DAMAGE, _("dégâts explosifs")),
)
LIST_RESISTANCES = [a for a, *_ in RESISTANCES]

# Leveled stats
HIT_POINTS_PER_LEVEL = 'hit_points_per_level'
SKILL_POINTS_PER_LEVEL = 'skill_points_per_level'
LEVELED_STATS = (
    (HIT_POINTS_PER_LEVEL, _("points de santé par niveau")),
    (SKILL_POINTS_PER_LEVEL, _("points de compétence par niveau")),
)
LIST_LEVELED_STATS = [a for a, *_ in LEVELED_STATS]

# Lists of statistics
LIST_EDITABLE_STATS = LIST_SECONDARY_STATS + LIST_RESISTANCES + LIST_LEVELED_STATS
LIST_ALL_STATS = LIST_SPECIALS + LIST_GENERAL_STATS + LIST_EDITABLE_STATS

# All statistics
ALL_STATS = (
    (_("S.P.E.C.I.A.L."), SPECIALS),
    (_("Statistiques générales"), GENERAL_STATS),
    (_("Statistiques secondaires"), SECONDARY_STATS),
    (_("Compétences"), SKILLS),
    (_("Résistances"), RESISTANCES),
)

# Item type
ITEM_WEAPON = 'weapon'
ITEM_AMMO = 'ammo'
ITEM_ARMOR = 'armor'
ITEM_FOOD = 'food'
ITEM_CHEM = 'chem'
ITEM_MISC = 'misc'
ITEM_TYPES = (
    (ITEM_WEAPON, _("arme")),
    (ITEM_AMMO, _("munition")),
    (ITEM_ARMOR, _("armure")),
    (ITEM_FOOD, _("nourriture")),
    (ITEM_CHEM, _("drogue")),
    (ITEM_MISC, _("autre")),
)

# Races
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
        SPECIAL_STRENGTH: (0, 1, 10),
        SPECIAL_PERCEPTION: (0, 1, 10),
        SPECIAL_ENDURANCE: (0, 1, 10),
        SPECIAL_CHARISMA: (0, 1, 10),
        SPECIAL_INTELLIGENCE: (0, 1, 10),
        SPECIAL_AGILITY: (0, 1, 10),
        SPECIAL_LUCK: (0, 1, 10),
        RESISTANCE_ELECTRICITY: (30, 0, 100),
    },
    RACE_GHOUL: {
        SPECIAL_STRENGTH: (0, 1, 8),
        SPECIAL_PERCEPTION: (0, 4, 13),
        SPECIAL_ENDURANCE: (0, 1, 10),
        SPECIAL_CHARISMA: (0, 1, 10),
        SPECIAL_INTELLIGENCE: (0, 2, 10),
        SPECIAL_AGILITY: (0, 1, 6),
        SPECIAL_LUCK: (0, 5, 12),
        RESISTANCE_RADIATION: (80, 0, 100),
        RESISTANCE_POISON: (30, 0, 100),
    },
    RACE_SUPER_MUTANT: {
        SPECIAL_STRENGTH: (0, 5, 13),
        SPECIAL_PERCEPTION: (0, 1, 11),
        SPECIAL_ENDURANCE: (0, 4, 11),
        SPECIAL_CHARISMA: (0, 1, 7),
        SPECIAL_INTELLIGENCE: (0, 1, 11),
        SPECIAL_AGILITY: (0, 1, 8),
        SPECIAL_LUCK: (0, 1, 10),
        RESISTANCE_RADIATION: (50, 0, 100),
        RESISTANCE_POISON: (20, 0, 100),
        RESISTANCE_FIRE: (25, 0, 100),
        HIT_POINTS_PER_LEVEL: (2, None, None),
        RESISTANCE_NORMAL_DAMAGE: (25, 0, 100),
        RESISTANCE_LASER_DAMAGE: (25, 0, 100),
        RESISTANCE_PLASMA_DAMAGE: (25, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (25, 0, 100),
    },
    RACE_DEATHCLAW: {
        SPECIAL_STRENGTH: (0, 6, 14),
        SPECIAL_PERCEPTION: (0, 4, 12),
        SPECIAL_ENDURANCE: (0, 1, 13),
        SPECIAL_CHARISMA: (0, 1, 3),
        SPECIAL_INTELLIGENCE: (0, 1, 4),
        SPECIAL_AGILITY: (0, 6, 16),
        SPECIAL_LUCK: (0, 1, 10),
        HIT_POINTS_PER_LEVEL: (2, None, None),
        STAT_MELEE_DAMAGE: (5, None, None),
        STAT_DAMAGE_THRESHOLD: (4, None, None),
        RESISTANCE_FIRE: (40, 0, 100),
        RESISTANCE_GAZ_CONTACT: (40, 0, 100),
        RESISTANCE_GAZ_INHALED: (40, 0, 100),
        RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
    },
    RACE_ROBOT: {
        SPECIAL_STRENGTH: (0, 7, 12),
        SPECIAL_PERCEPTION: (0, 7, 12),
        SPECIAL_ENDURANCE: (0, 7, 12),
        SPECIAL_CHARISMA: (0, 1, 1),
        SPECIAL_INTELLIGENCE: (0, 1, 12),
        SPECIAL_AGILITY: (0, 1, 12),
        SPECIAL_LUCK: (0, 5, 5),
        HIT_POINTS_PER_LEVEL: (0, 0, 0),
        RESISTANCE_RADIATION: (100, 0, 100),
        RESISTANCE_POISON: (100, 0, 100),
        RESISTANCE_FIRE: (40, 0, 100),
        RESISTANCE_GAZ_CONTACT: (100, 0, 100),
        RESISTANCE_GAZ_INHALED: (100, 0, 100),
        RESISTANCE_ELECTRICITY: (-50, 0, 100),
        RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
        RESISTANCE_LASER_DAMAGE: (40, 0, 100),
        RESISTANCE_PLASMA_DAMAGE: (40, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
    },
}


class Adventure(Entity):
    """
    Aventure
    """
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    date = models.DateTimeField(verbose_name=_("date"))
    current = models.ForeignKey('Character', blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("personnage actif"))


class Character(Entity):
    """
    Personnage
    """
    # General informations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, blank=True, null=True, on_delete=models.SET_NULL, verbose_name=_("utilisateur"))
    adventure = models.ForeignKey('Adventure', on_delete=models.CASCADE, verbose_name=_("aventure"))
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
    # Tag skills
    tag_1 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 1"))
    tag_2 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 2"))
    tag_3 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 3"))
    tag_4 = models.CharField(max_length=20, choices=SKILLS, blank=True, null=True, verbose_name=_("spécialité 4"))
    tag_5 = models.CharField(max_length=20, choices=SKILLS, blank=True, null=True, verbose_name=_("spécialité 5"))
    # Others
    equipement = models.ManyToManyField('Item', blank=True, through=Equipment, verbose_name=_("inventaire"))
    # Statistics cache
    _stats = {}

    class Stats:
        """
        Statistiques actuelle du personnage
        """
        def __init__(self, character: Character):
            self.character = character
            self.change_all(RACES_STATS[character.race])

        def change_all(self, stats):
            for name in ALL_STATS:
                values = stats.get(name, None)
                if values:
                    self.change(name, *values)
                    continue
                self.change(name)

        def change(self, name, value=0, mini=None, maxi=None):
            old_value = getattr(self, name, 0)
            new_value = min(max(old_value + value, mini or float('-inf')), maxi or float('+inf'))
            if old_value != new_value:
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

    def init(self):
        # Main statistics
        self.hit_points_per_level += 3 + (self.endurance // 2)
        self.skill_points_per_level += 5 + (2 * self.intelligence)
        # Secondary statistics
        self.max_health += (15 + (self.strength + (2 * self.endurance)) + ((self.level - 1) * self.hit_points_per_level))
        self.max_action_points += 5 + (self.agility // 2)
        self.evade += self.armor_class + self.agility
        self.carry_weight += 25 + (25 * self.strength)
        self.melee_damage += max(0, self.strength - 5)
        self.sequence += 2 * self.perception
        self.healing_rate += (self.endurance // 3)
        self.critical_chance += self.luck
        # Resistances
        self.radiation_resistance += 2 * self.endurance
        self.poison_resistance += 5 * self.endurance
        # Skills
        self.small_guns += 5 + (4 * self.agility)
        self.big_guns += 2 * self.agility
        self.energy_weapons += 2 * self.agility
        self.unarmed += 30 + (2 * (self.strength + self.agility))
        self.melee_weapons = 20 + (2 * (self.strength + self.agility))
        self.throwing += 4 * self.agility
        self.first_aid += 2 * (self.perception + self.endurance)
        self.doctor += 5 + self.perception + self.intelligence
        self.chems += 10 + (2 * self.intelligence)
        self.sneak += 5 + (3 * self.agility)
        self.lockpick += 10 + self.perception + self.agility
        self.steal += 3 * self.agility
        self.traps += 10 + (2 * self.perception)
        self.science += 4 * self.intelligence
        self.repair += 3 * self.intelligence
        self.speech += 5 * self.charisma
        self.barter += 4 * self.charisma
        self.gambling += 5 * self.luck
        self.survival += 2 * (self.endurance + self.intelligence)
        self.knowledge += 5 * self.intelligence
        # Tag skills
        for name in self.tags:
            setattr(self, name, getattr(self, name, 0) + 20)

    @property
    def tags(self) -> List[str]:
        return [tag for tag in [self.tag_1, self.tag_2, self.tag_3, self.tag_4, self.tag_5] if tag]

    def save(self, *args, **kwargs):
        if not self.pk:
            self.init()
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
            self.max_health += self.hit_points_per_level
            self.skill_points += self.skill_points_per_level
            if not self.level % 3:
                self.perk_points += 1
            level += 1
        return level

    def roll(self, skill, malus=0):
        pass


class Statistic(models.Model):
    """
    Statistique
    """
    stats = models.CharField(max_length=20, choices=ALL_STATS, verbose_name=_("statistique"))
    value = models.SmallIntegerField(default=0, verbose_name=_("valeur"))

    class Meta:
        verbose_name = _("statistique")
        verbose_name_plural = _("statistiques")


class Condition(models.Model):
    """
    Condition
    """
    CONDITION_EQUAL = '=='
    CONDITION_GREATER_OR_EQUAL = '>='
    CONDITION_GREATER = '>'
    CONDITION_LESS_OR_EQUAL = '<='
    CONDITION_LESS = '<'
    CONDITION_DIFFERENT = '!='
    CONDITIONS = (
        (CONDITION_EQUAL, _("est égal à")),
        (CONDITION_GREATER_OR_EQUAL, _("est supérieur ou égal à")),
        (CONDITION_GREATER, _("est supérieur à")),
        (CONDITION_LESS_OR_EQUAL, _("est inférieur ou égal à")),
        (CONDITION_LESS, _("est inférieur à")),
        (CONDITION_DIFFERENT, _("est différent de")),
    )

    stats = models.CharField(max_length=20, choices=ALL_STATS, verbose_name=_("statistique"))
    condition = models.CharField(max_length=2, choices=CONDITIONS, verbose_name=_("condition"))
    value = models.SmallIntegerField(default=0, verbose_name=_("valeur"))

    class Meta:
        verbose_name = _("condition")
        verbose_name_plural = _("conditions")


class Effect(Entity):
    """
    Effet
    """
    name = models.CharField(max_length=100, verbose_name=_("nom"))
    stats = models.ManyToManyField('Statistic', blank=True, related_name='effects', verbose_name=_("statistiques"))
    duration = models.DurationField(blank=True, null=True, verbose_name=_("durée"))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    # Damage
    damage_tick = models.DurationField(blank=True, null=True, verbose_name=_("intervalle"))
    damage_type = models.CharField(max_length=30, blank=True, null=True, choices=RESISTANCES, verbose_name=_("type de dégâts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    damage_bonus = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bonus"))

    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")


class RunningEffect(Entity):
    """
    Effet en cours
    """
    character = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("personnage"))
    effect = models.ForeignKey('Effect', on_delete=models.CASCADE, verbose_name=_("effet"))
    start_date = models.DateTimeField(verbose_name=_("date d'effet"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'arrêt"))
    last_update = models.DateTimeField(verbose_name=_("dernière mise à jour"))
    # TODO: calculer les effets appliqués et à appliquer

    class Meta:
        verbose_name = _("effet en cours")
        verbose_name_plural = _("effets en cours")


class Item(Entity):
    """
    Objet
    """
    name = models.CharField(max_length=100, verbose_name=_("nom"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    type = models.CharField(max_length=6, choices=ITEM_TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    weight = models.PositiveSmallIntegerField(default=0, verbose_name=_("poids"))
    # Specific
    melee = models.BooleanField(default=False, verbose_name=_("arme de mêlée"))
    damage_type = models.CharField(max_length=30, blank=True, null=True, choices=RESISTANCES, verbose_name=_("type de dégâts"))
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
    ammo = models.ManyToManyField('Item', blank=True, verbose_name=_("type de munition"))
    evasion_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur d'esquive"))
    damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de dégâts"))
    resistance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de résistance"))
    critical_modifier = models.FloatField(default=0.0, verbose_name=_("modificateur de coup critique"))
    # Effets
    effects_on_hit = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets à l'impact"))
    effects_on_use = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets à l'usage"))
    effects_on_equip = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets sur soi"))

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class Equipment(Entity):
    """
    Equipement
    """
    character = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("personnage"))
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"))
    count = models.PositiveIntegerField(default=0, verbose_name=_("nombre"))
    equiped = models.BooleanField(default=False, verbose_name=_("équipé ?"))
    condition = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("état"))

    class Meta:
        verbose_name = _("équipement")
        verbose_name_plural = _("équipements")

