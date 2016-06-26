# encoding: utf-8
from typing import List

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext as _


class Character(models.Model):
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
    )

    STAT_MAX_HEALTH = 'max_health'
    STAT_MAX_ACTION_POINTS = 'max_action_points'
    STAT_DAMAGE_RESISTANCE = 'damage_resistance'
    STAT_DAMAGE_THRESHOLD = 'damage_threashold'
    STAT_EVADE = 'evade'
    STAT_CARRY_WEIGHT = 'carry_weight'
    STAT_MELEE_DAMAGE = 'melee_damage'
    STAT_POISON_RESISTANCE = 'poison_resistance'
    STAT_RADIATION_RESISTANCE = 'radiation_resistance'
    STAT_GAS_RESISTANCE = 'gas_resistance'
    STAT_FIRE_RESISTANCE = 'fire_resistance'
    STAT_ELECTRICITY_RESISTANCE = 'electricity_resistance'
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
        (STAT_POISON_RESISTANCE, _("résistance aux poisons")),
        (STAT_RADIATION_RESISTANCE, _("résistance aux radiations")),
        (STAT_GAS_RESISTANCE, _("résistance aux gaz")),
        (STAT_FIRE_RESISTANCE, _("résistance au feu")),
        (STAT_ELECTRICITY_RESISTANCE, _("résistance à l'électricité")),
        (STAT_SEQUENCE, _("initiative")),
        (STAT_HEALING_RATE, _("taux de regénération")),
        (STAT_CRITICAL_CHANCE, _("chance de critique")),
    )

    # Statistics cache
    STATISTICS = {}

    # General informations
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("utilisateur"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    is_player = models.BooleanField(default=False, verbose_name=_("joueur ?"))
    name = models.CharField(max_length=100, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_("niveau"))
    experience = models.PositiveIntegerField(default=0, verbose_name=_("expérience"))
    karma = models.SmallIntegerField(default=0, verbose_name=_("karma"))
    health = models.SmallIntegerField(default=0, verbose_name=_("santé"))
    action_points = models.SmallIntegerField(default=0, verbose_name=_("points d'action"))
    irradiation = models.SmallIntegerField(default=0, verbose_name=_("irradiation"))
    skill_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de compétences"))
    # S.P.E.C.I.A.L.
    strength = models.PositiveSmallIntegerField(default=5, verbose_name=_("force"))
    perception = models.PositiveSmallIntegerField(default=5, verbose_name=_("perception"))
    endurance = models.PositiveSmallIntegerField(default=5, verbose_name=_("endurance"))
    charisma = models.PositiveSmallIntegerField(default=5, verbose_name=_("charisme"))
    intelligence = models.PositiveSmallIntegerField(default=5, verbose_name=_("intelligence"))
    agility = models.PositiveSmallIntegerField(default=5, verbose_name=_("agilité"))
    luck = models.PositiveSmallIntegerField(default=5, verbose_name=_("chance"))
    # Secondary statistics
    max_health = models.SmallIntegerField(default=0, verbose_name=_("santé maximale"))
    max_action_points = models.SmallIntegerField(default=0, verbose_name=_("points d'action max."))
    damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts"))
    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("seuil de dégâts"))
    evade = models.SmallIntegerField(default=0, verbose_name=_("esquive"))
    carry_weight = models.SmallIntegerField(default=0, verbose_name=_("charge maximale"))
    melee_damage = models.SmallIntegerField(default=0, verbose_name=_("attaque en mélée"))
    poison_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux poisons"))
    radiation_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux radiations"))
    gas_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux gaz"))
    fire_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance au feu"))
    electricity_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance à l'électricité"))
    sequence = models.SmallIntegerField(default=0, verbose_name=_("initiative"))
    healing_rate = models.SmallIntegerField(default=0, verbose_name=_("taux de regénération"))
    critical_chance = models.SmallIntegerField(default=0, verbose_name=_("chance de critique"))
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
    # Tag skills
    tag_1 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 1"))
    tag_2 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 2"))
    tag_3 = models.CharField(max_length=20, choices=SKILLS, verbose_name=_("spécialité 3"))
    tag_4 = models.CharField(max_length=20, choices=SKILLS, blank=True, null=True, verbose_name=_("spécialité 4"))
    tag_5 = models.CharField(max_length=20, choices=SKILLS, blank=True, null=True, verbose_name=_("spécialité 5"))
    # Per level
    hit_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("points de santé par niveau"))
    skill_points_per_level = models.SmallIntegerField(default=0, verbose_name=_("points de compétence par niveau"))

    class Meta:
        verbose_name = _("personnage")
        verbose_name_plural = _("personnages")

    class Statistics:
        """
        Statistiques du personnage
        """
        def __init__(self, character):
            self.hit_points_per_level = character.hit_points_per_level + 3 + (character.endurance // 2)
            self.skill_points_per_level = character.skill_points_per_level + 5 + (2 * character.intelligence)

            self.max_health = (
                character.max_health + 15 + (character.strength + (2 * character.endurance)) +
                ((character.level - 1) * self.hit_points_per_level))
            self.max_action_points = character.max_action_points + 5 + (character.agility // 2)
            self.damage_resistance = character.damage_resistance
            self.damage_threshold = character.damage_threshold
            self.evade = character.armor_class + character.agility
            self.carry_weight = character.carry_weight + 25 + (25 * character.strength)
            self.melee_damage = character.melee_damage + max(0, character.strength - 5)
            self.poison_resistance = character.poison_resistance + 5 * character.endurance
            self.radiation_resistance = character.radiation_resistance + 2 * character.endurance
            self.gas_resistance = character.gas_resistance
            self.fire_resistance = character.fire_resistance
            self.electricity_resistance = character.electricity_resistance
            self.sequence = character.sequence + 2 * character.perception
            self.healing_rate = character.healing_rate + (character.endurance // 3)
            self.critical_chance = character.critical_chance + character.luck

            self.small_guns = character.small_guns + 5 + (4 * character.agility)
            self.big_guns = character.big_guns + 2 * character.agility
            self.energy_weapons = character.energy_weapons + 2 * character.agility
            self.unarmed = character.unarmed + 30 + (2 * (character.strength + character.agility))
            self.melee_weapons = character.melee_weapons + 20 + (2 * (character.strength + character.agility))
            self.throwing = character.throwing + 4 * character.agility
            self.first_aid = character.first_aid + 2 * (character.perception + character.endurance)
            self.doctor = character.doctor + 5 + character.perception + character.intelligence
            self.chems = character.chems + 10 + (2 * character.intelligence)
            self.sneak = character.sneak + 5 + (3 * character.agility)
            self.lockpick = character.lockpick + 10 + character.perception + character.agility
            self.steal = character.steal + 3 * character.agility
            self.traps = character.traps + 10 + (2 * character.perception)
            self.science = character.science + 4 * character.intelligence
            self.repair = character.repair + 3 * character.intelligence
            self.speech = character.speech + 5 * character.charisma
            self.barter = character.barter + 4 * character.charisma
            self.gambling = character.gambling + 5 * character.luck
            self.survival = character.survival + 2 * (character.endurance + character.intelligence)

            for tag in character.tags:
                setattr(self, tag, getattr(self, tag, 0) + 20)

    @property
    def stats(self) -> Statistics:
        stats = Character.STATISTICS.get(self.id) or Character.Statistics(self)
        if self.id:
            Character.STATISTICS[self.id] = stats
        return stats

    @property
    def tags(self) -> List[str]:
        return [tag for tag in [self.tag_1, self.tag_2, self.tag_3, self.tag_4, self.tag_5] if tag]

    def save(self, *args, **kwargs):
        self.check_level()
        Character.STATISTICS.pop(self.id, None)
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


class Item(models.Model):
    """
    Objet
    """
    TYPE_WEAPON = 'weapon'
    TYPE_AMMO = 'ammo'
    TYPE_APPAREL = 'apparel'
    TYPE_FOOD = 'food'
    TYPE_CHEM = 'chem'
    TYPE_MISC = 'misc'
    TYPES = (
        (TYPE_WEAPON, _("arme")),
        (TYPE_AMMO, _("munition")),
        (TYPE_APPAREL, _("vêtement")),
        (TYPE_FOOD, _("nourriture")),
        (TYPE_CHEM, _("drogue")),
        (TYPE_MISC, _("autre")),
    )

    name = models.CharField(max_length=100, verbose_name=_("nom"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    type = models.CharField(max_length=7, choices=TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    weight = models.PositiveSmallIntegerField(default=0, verbose_name=_("poids"))
    effects_wear = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets quand porté"))
    effects_use = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets quand utilisé"))
    effects_target = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets sur cible"))

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class Ammo(Item):
    """
    Munition
    """
    evasion_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur d'esquive"))
    damage_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de dégâts"))
    resistance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur de résistance"))

    class Meta:
        verbose_name = _("munition")
        verbose_name_plural = _("munitions")


class Weapon(Item):
    """
    Arme
    """
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

    ammo = models.ManyToManyField('Ammo', blank=True, verbose_name=_("type de munition"))
    damage_type = models.CharField(max_length=10, choices=DAMAGE_TYPES, verbose_name=_("type de dégâts"))
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

    class Meta:
        verbose_name = _("arme")
        verbose_name_plural = _("armes")


class Apparel(Item):
    """
    Vêtement
    """
    evade = models.SmallIntegerField(default=0, verbose_name=_("esquive"))
    resistance_normal = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance dégâts normaux"))
    resistance_fire = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance dégâts feu"))
    resistance_laser = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance dégâts laser"))
    resistance_plasma = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance dégâts plasma"))
    resistance_explosive = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance dégâts explosifs"))

    class Meta:
        verbose_name = _("vêtement")
        verbose_name_plural = _("vêtements")


class Effect(models.Model):
    """
    Effet
    """
    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")
