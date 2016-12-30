# encoding: utf-8
from django.utils.translation import ugettext as _


# General statistics
STATS_HEALTH = 'health'
STATS_ACTION_POINTS = 'action_points'
STATS_EXPERIENCE = 'experience'
STATS_KARMA = 'karma'
STATS_IRRADIATION = 'irradiation'
STATS_DEHYDRATION = 'dehydration'
STATS_HUNGER = 'hunger'
STATS_SLEEP = 'sleep'
GENERAL_STATS = (
    (STATS_HEALTH, _("santé")),
    (STATS_ACTION_POINTS, _("points d'action")),
    (STATS_EXPERIENCE, _("expérience")),
    (STATS_KARMA, _("karma")),
    (STATS_IRRADIATION, _("irradiation")),
    (STATS_DEHYDRATION, _("soif")),
    (STATS_HUNGER, _("faim")),
    (STATS_SLEEP, _("sommeil")),
)
LIST_GENERAL_STATS = [a for a, *_ in GENERAL_STATS]

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

# Secondary statistics
STATS_MAX_HEALTH = 'max_health'
STATS_MAX_ACTION_POINTS = 'max_action_points'
STATS_ARMOR_CLASS = 'armor_class'
STATS_DAMAGE_THRESHOLD = 'damage_threshold'
STATS_DAMAGE_RESISTANCE = 'damage_resistance'
STATS_CARRY_WEIGHT = 'carry_weight'
STATS_MELEE_DAMAGE = 'melee_damage'
STATS_SEQUENCE = 'sequence'
STATS_HEALING_RATE = 'healing_rate'
STATS_CRITICAL_CHANCE = 'critical_chance'
SECONDARY_STATS = (
    (STATS_MAX_HEALTH, _("santé maximale")),
    (STATS_MAX_ACTION_POINTS, _("points d'action max.")),
    (STATS_ARMOR_CLASS, _("esquive")),
    (STATS_DAMAGE_THRESHOLD, _("seuil de dégâts")),
    (STATS_DAMAGE_RESISTANCE, _("résistance aux dégâts")),
    (STATS_CARRY_WEIGHT, _("charge maximale")),
    (STATS_MELEE_DAMAGE, _("attaque en mélée")),
    (STATS_SEQUENCE, _("initiative")),
    (STATS_HEALING_RATE, _("taux de regénération")),
    (STATS_CRITICAL_CHANCE, _("chance de critique")),
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
RESISTANCE_NORMAL_DAMAGE = 'normal_damage_resistance'
RESISTANCE_LASER_DAMAGE = 'laser_damage_resistance'
RESISTANCE_PLASMA_DAMAGE = 'plasma_damage_resistance'
RESISTANCE_EXPLOSIVE_DAMAGE = 'explosive_damage_resistance'
RESISTANCE_RADIATION = 'radiation_resistance'
RESISTANCE_POISON = 'poison_resistance'
RESISTANCE_FIRE = 'fire_resistance'
RESISTANCE_ELECTRICITY = 'electricity_resistance'
RESISTANCE_GAZ_CONTACT = 'gas_contact_resistance'
RESISTANCE_GAZ_INHALED = 'gas_inhaled_resistance'
RESISTANCES = (
    (RESISTANCE_NORMAL_DAMAGE, _("résistance aux dégâts normaux")),
    (RESISTANCE_LASER_DAMAGE, _("résistance aux dégâts de laser")),
    (RESISTANCE_PLASMA_DAMAGE, _("résistance aux dégâts de plasma")),
    (RESISTANCE_EXPLOSIVE_DAMAGE, _("résistance aux dégâts explosifs")),
    (RESISTANCE_RADIATION, _("résistance aux radiations")),
    (RESISTANCE_POISON, _("résistance aux poisons")),
    (RESISTANCE_FIRE, _("résistance au feu")),
    (RESISTANCE_ELECTRICITY, _("résistance à l'électricité")),
    (RESISTANCE_GAZ_CONTACT, _("résistance au gaz (contact)")),
    (RESISTANCE_GAZ_INHALED, _("résistance au gaz (inhalé)")),
)
LIST_RESISTANCES = [a for a, *_ in RESISTANCES]

# Damage
DAMAGE_NORMAL = 'normal'
DAMAGE_LASER = 'laser'
DAMAGE_PLASMA = 'plasma'
DAMAGE_EXPLOSIVE = 'explosive'
DAMAGE_RADIATION = 'radiation'
DAMAGE_POISON = 'poison'
DAMAGE_FIRE = 'fire'
DAMAGE_ELECTRICITY = 'electricity'
DAMAGE_GAZ_CONTACT = 'gas_contact'
DAMAGE_GAZ_INHALED = 'gas_inhaled'
DAMAGE_HEAL = 'heal'
DAMAGES = (
    (DAMAGE_NORMAL, _("dégâts normaux")),
    (DAMAGE_LASER, _("dégâts de laser")),
    (DAMAGE_PLASMA, _("dégâts de plasma")),
    (DAMAGE_EXPLOSIVE, _("dégâts explosifs")),
    (DAMAGE_RADIATION, _("dégâts de radiations")),
    (DAMAGE_POISON, _("dégâts de poison")),
    (DAMAGE_FIRE, _("dégâts de feu")),
    (DAMAGE_ELECTRICITY, _("dégâts d'électricité")),
    (DAMAGE_GAZ_CONTACT, _("dégâts de gaz (contact)")),
    (DAMAGE_GAZ_INHALED, _("dégâts de gaz (inhalé)")),
    (DAMAGE_HEAL, _("soins")),
)
LIST_DAMAGES = [a for a, *_ in DAMAGES]

# Damage / resistance
DAMAGE_RESISTANCE = {
    DAMAGE_NORMAL: RESISTANCE_NORMAL_DAMAGE,
    DAMAGE_LASER: RESISTANCE_LASER_DAMAGE,
    DAMAGE_PLASMA: RESISTANCE_PLASMA_DAMAGE,
    DAMAGE_EXPLOSIVE: RESISTANCE_EXPLOSIVE_DAMAGE,
    DAMAGE_RADIATION: RESISTANCE_RADIATION,
    DAMAGE_POISON: RESISTANCE_POISON,
    DAMAGE_FIRE: RESISTANCE_FIRE,
    DAMAGE_ELECTRICITY: RESISTANCE_ELECTRICITY,
    DAMAGE_GAZ_CONTACT: RESISTANCE_GAZ_CONTACT,
    DAMAGE_GAZ_INHALED: RESISTANCE_GAZ_INHALED,
    DAMAGE_HEAL: None,
}

# Leveled stats
HIT_POINTS_PER_LEVEL = 'hit_points_per_level'
SKILL_POINTS_PER_LEVEL = 'skill_points_per_level'
PERK_RATE = 'perk_rate'
LEVELED_STATS = (
    (HIT_POINTS_PER_LEVEL, _("points de santé par niveau")),
    (SKILL_POINTS_PER_LEVEL, _("points de compétence par niveau")),
    (PERK_RATE, _("niveaux pour un talent")),
)
LIST_LEVELED_STATS = [a for a, *_ in LEVELED_STATS]

# Rollable statistics
ROLL_STATS = (
    (_("S.P.E.C.I.A.L."), SPECIALS),
    (_("Compétences"), SKILLS),
)

# All statistics
ALL_STATS = ROLL_STATS + (
    (_("Statistiques générales"), GENERAL_STATS),
    (_("Statistiques secondaires"), SECONDARY_STATS),
    (_("Résistances"), RESISTANCES),
    (_("Statistiques de niveau"), LEVELED_STATS),
)

# Lists of statistics
EDITABLE_STATS = SPECIALS + SKILLS + SECONDARY_STATS + RESISTANCES + LEVELED_STATS
LIST_EDITABLE_STATS = [a for a, *_ in EDITABLE_STATS]
LIST_ALL_STATS = LIST_GENERAL_STATS + LIST_EDITABLE_STATS

# Item type
ITEM_WEAPON = 'weapon'
ITEM_AMMO = 'ammo'
ITEM_ARMOR = 'armor'
ITEM_IMPLANT = 'implant'
SLOT_ITEM_TYPES = (
    (ITEM_WEAPON, _("arme")),
    (ITEM_AMMO, _("munition")),
    (ITEM_ARMOR, _("armure")),
    (ITEM_IMPLANT, _("implant")),
)

ITEM_FOOD = 'food'
ITEM_CHEM = 'chem'
ITEM_MISC = 'misc'
ITEM_TYPES = SLOT_ITEM_TYPES + (
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
RACE_ANIMAL = 'animal'
RACES = (
    (RACE_HUMAN, _("humain")),
    (RACE_GHOUL, _("ghoule")),
    (RACE_SUPER_MUTANT, _("super-mutant")),
    (RACE_DEATHCLAW, _("écorcheur")),
    (RACE_ROBOT, _("robot")),
    (RACE_ANIMAL, _("animal")),
)

# Body parts
PART_TORSO = 'torso'
PART_LEGS = 'legs'
PART_ARMS = 'arms'
PART_HEAD = 'head'
PART_EYES = 'eyes'
BODY_PARTS = (
    (PART_TORSO, _("torse")),
    (PART_LEGS, _("jambes")),
    (PART_ARMS, _("bras")),
    (PART_HEAD, _("tête")),
    (PART_EYES, _("yeux")),
)
