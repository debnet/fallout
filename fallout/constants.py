# encoding: utf-8
from fallout.enums import *  # noqa


# Body part modifiers (ranged, melee, critical)
BODY_PARTS_MODIFIERS = {
    PART_TORSO: (0, 0, 0),
    PART_LEGS: (-20, -10, 5),
    PART_ARMS: (-30, -15, 10),
    PART_HEAD: (-40, -20, 15),
    PART_EYES: (-60, -30, 20),
}

# Body part randomly hit if not targetted (body part, chance)
BODY_PARTS_RANDOM_CHANCES = (
    (PART_EYES, 1),
    (PART_HEAD, 2),
    (PART_ARMS, 5),
    (PART_LEGS, 10),
    (PART_TORSO, 100),
)

# Racial traits (bonus, min, max)
RACES_STATS = {
    RACE_HUMAN: {
        SPECIAL_STRENGTH: (0, 1, 10),
        SPECIAL_PERCEPTION: (0, 1, 10),
        SPECIAL_ENDURANCE: (0, 1, 10),
        SPECIAL_CHARISMA: (0, 1, 10),
        SPECIAL_INTELLIGENCE: (0, 1, 10),
        SPECIAL_AGILITY: (0, 1, 10),
        SPECIAL_LUCK: (0, 1, 10),
        RESISTANCE_ELECTRICITY: (30, -100, 100),
        PERK_RATE: (2, None, None),
    },
    RACE_GHOUL: {
        SPECIAL_STRENGTH: (0, 1, 8),
        SPECIAL_PERCEPTION: (0, 4, 13),
        SPECIAL_ENDURANCE: (0, 1, 10),
        SPECIAL_CHARISMA: (0, 1, 6),
        SPECIAL_INTELLIGENCE: (0, 2, 10),
        SPECIAL_AGILITY: (0, 1, 10),
        SPECIAL_LUCK: (0, 5, 12),
        RESISTANCE_RADIATION: (80, -100, 100),
        RESISTANCE_POISON: (30, -100, 100),
        PERK_RATE: (3, None, None),
    },
    RACE_SUPER_MUTANT: {
        SPECIAL_STRENGTH: (0, 5, 13),
        SPECIAL_PERCEPTION: (0, 1, 11),
        SPECIAL_ENDURANCE: (0, 4, 11),
        SPECIAL_CHARISMA: (0, 1, 7),
        SPECIAL_INTELLIGENCE: (0, 1, 8),
        SPECIAL_AGILITY: (0, 1, 8),
        SPECIAL_LUCK: (0, 1, 10),
        RESISTANCE_DAMAGE: (25, -100, 100),
        RESISTANCE_RADIATION: (50, -100, 100),
        RESISTANCE_POISON: (20, -100, 100),
        RESISTANCE_FIRE: (25, -100, 100),
        HIT_POINTS_PER_LEVEL: (2, None, None),
        PERK_RATE: (3, None, None),
    },
    RACE_DEATHCLAW: {
        SPECIAL_STRENGTH: (0, 6, 14),
        SPECIAL_PERCEPTION: (0, 4, 12),
        SPECIAL_ENDURANCE: (0, 1, 13),
        SPECIAL_CHARISMA: (0, 1, 3),
        SPECIAL_INTELLIGENCE: (0, 1, 4),
        SPECIAL_AGILITY: (0, 6, 16),
        SPECIAL_LUCK: (0, 1, 10),
        STATS_MELEE_DAMAGE: (5, None, None),
        RESISTANCE_DAMAGE: (40, -100, 100),
        THRESHOLD_DAMAGE: (4, None, None),
        HIT_POINTS_PER_LEVEL: (2, None, None),
        PERK_RATE: (3, None, None),
    },
    RACE_ROBOT: {
        SPECIAL_STRENGTH: (0, 7, 12),
        SPECIAL_PERCEPTION: (0, 7, 12),
        SPECIAL_ENDURANCE: (0, 7, 12),
        SPECIAL_CHARISMA: (0, 1, 1),
        SPECIAL_INTELLIGENCE: (0, 1, 12),
        SPECIAL_AGILITY: (0, 1, 12),
        SPECIAL_LUCK: (0, 5, 5),
        STATS_HEALING_RATE: (0, 0, 0),
        RESISTANCE_DAMAGE: (40, -100, 100),
        RESISTANCE_RADIATION: (100, -100, 100),
        RESISTANCE_POISON: (100, -100, 100),
        RESISTANCE_FIRE: (40, -100, 100),
        RESISTANCE_ELECTRICITY: (-50, -100, 100),
        RESISTANCE_GAZ_CONTACT: (1.0, -100, 100),
        RESISTANCE_GAZ_INHALED: (1.0, -100, 100),
        HIT_POINTS_PER_LEVEL: (0, 0, 0),
        PERK_RATE: (10, None, None),
    },
    RACE_ANIMAL: {
        SPECIAL_STRENGTH: (0, 1, 7),
        SPECIAL_PERCEPTION: (0, 4, 14),
        SPECIAL_ENDURANCE: (0, 1, 6),
        SPECIAL_CHARISMA: (0, 1, 5),
        SPECIAL_INTELLIGENCE: (0, 1, 3),
        SPECIAL_AGILITY: (0, 1, 15),
        SPECIAL_LUCK: (0, 1, 10),
        PERK_RATE: (10, None, None),
    },
}

# Radiation effects
RADS_EFFECTS = {
    (0, 200): {},
    (200, 400): {
        SPECIAL_STRENGTH: (-1, None, None),
    },
    (400, 600): {
        STATS_HEALING_RATE: (-3, 0, None),
        SPECIAL_STRENGTH: (-1, 1, None),
        SPECIAL_AGILITY: (-1, 1, None),
    },
    (600, 800): {
        STATS_HEALING_RATE: (-5, 0, None),
        STATS_MAX_HEALTH: (-5, 0, None),
        SPECIAL_STRENGTH: (-2, 1, None),
        SPECIAL_ENDURANCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (800, 1000): {
        STATS_HEALING_RATE: (-10, 0, None),
        STATS_MAX_HEALTH: (-15, 0, None),
        SPECIAL_STRENGTH: (-4, 1, None),
        SPECIAL_PERCEPTION: (-3, 1, None),
        SPECIAL_ENDURANCE: (-3, 1, None),
        SPECIAL_CHARISMA: (-3, 1, None),
        SPECIAL_INTELLIGENCE: (-1, 1, None),
        SPECIAL_AGILITY: (-5, 1, None),
    },
    (1000, None): {
        STATS_HEALING_RATE: (-10, None, None),
        STATS_MAX_HEALTH: (-20, None, None),
        SPECIAL_STRENGTH: (-6, 1, None),
        SPECIAL_PERCEPTION: (-5, 1, None),
        SPECIAL_ENDURANCE: (-5, 1, None),
        SPECIAL_CHARISMA: (-5, 1, None),
        SPECIAL_INTELLIGENCE: (-3, 1, None),
        SPECIAL_AGILITY: (-6, 1, None),
    },
}

# Dehydration effets
THIRST_EFFECTS = {
    (0, 200): {},
    (200, 400): {
        SPECIAL_ENDURANCE: (-1, 1, None),
    },
    (400, 600): {
        SPECIAL_PERCEPTION: (-1, 1, None),
        SPECIAL_ENDURANCE: (-2, 1, None),
    },
    (600, 800): {
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_ENDURANCE: (-2, 1, None),
        SPECIAL_INTELLIGENCE: (-1, 1, None),
    },
    (800, 1000): {
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_ENDURANCE: (-3, 1, None),
        SPECIAL_INTELLIGENCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (1000, None): {
        STATS_MAX_HEALTH: (-1000, None, None),
    },
}

# Hunger effects
HUNGER_EFFECTS = {
    (0, 200): {},
    (200, 400): {
        SPECIAL_STRENGTH: (-1, 1, None),
    },
    (400, 600): {
        SPECIAL_STRENGTH: (-2, 1, None),
        SPECIAL_CHARISMA: (-1, 1, None),
    },
    (600, 800): {
        SPECIAL_STRENGTH: (-3, 1, None),
        SPECIAL_PERCEPTION: (-1, 1, None),
        SPECIAL_CHARISMA: (-2, 1, None),
    },
    (800, 1000): {
        SPECIAL_STRENGTH: (-3, 1, None),
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_CHARISMA: (-2, 1, None),
    },
    (1000, None): {
        STATS_MAX_HEALTH: (-1000, None, None),
    },
}

# Sleep deprivation effects
SLEEP_EFFECTS = {
    (0, 200): {},
    (200, 400): {
        SPECIAL_AGILITY: (-1, 1, None),
    },
    (400, 600): {
        SPECIAL_INTELLIGENCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (600, 800): {
        SPECIAL_ENDURANCE: (-1, 1, None),
        SPECIAL_INTELLIGENCE: (-2, 1, None),
        SPECIAL_AGILITY: (-3, 1, None),
    },
    (800, 1000): {
        SPECIAL_ENDURANCE: (-2, 1, None),
        SPECIAL_INTELLIGENCE: (-2, 1, None),
        SPECIAL_AGILITY: (-3, 1, None),
    },
    (1000, None): {
        STATS_MAX_HEALTH: (-1000, None, None),
    },
}

# Survival effects
SURVIVAL_EFFECTS = (
    (STATS_RADS, RADS_EFFECTS),
    (STATS_THIRST, THIRST_EFFECTS),
    (STATS_HUNGER, HUNGER_EFFECTS),
    (STATS_SLEEP, SLEEP_EFFECTS),
)

# S.P.E.C.I.A.L.
SPECIAL_POINTS = 40

# Survival modifiers when resting
NEEDS_RESTING_RATE = 0.75
NEEDS_NORMAL_RATE = 1.00

# Critical rolls
CRITICAL_SUCCESS_D10 = 1
CRITICAL_FAIL_D10 = 10
CRITICAL_SUCCESS_D100 = 5
CRITICAL_FAIL_D100 = 96

# Multiplier effect of luck on rolls
LUCK_ROLL_MULT = 1

# Base value for experience points
BASE_XP = 1000

# Tag skill bonus
TAG_SKILL_BONUS = 20

# Healing rate multiplier when resting
HEALING_RATE_RESTING_MULT = 4.0

# Maximum hit chance
MAX_HIT_CHANCE = 95

# Maximum damage resistance
MAX_DAMAGE_RESISTANCE = 95

# Perception multiplier for ranged attacks
RANGED_PERCEPTION_MULT = 8

# Ranged bonus/malus multipliers
RANGED_BONUS_MULT = 2
RANGED_MALUS_MULT = 4

# Ranged hit chance multipliers
RANGE_NORMAL_MULT = 2
RANGE_LONG_MULT = 4
RANGE_SCOPED_MULT = 5

RANGE_MODIFIERS = {
    MODE_RANGED: RANGE_NORMAL_MULT,
    MODE_LONG: RANGE_LONG_MULT,
    MODE_SCOPED: RANGE_SCOPED_MULT,
}

# Hit chance malus
MIN_STRENGTH_MALUS = 20
MIN_SKILL_MALUS = 1

# Action points cost
AP_COST_FIGHT = 5  # Fight unarmed
AP_COST_EQUIP = 4  # Equip item
AP_COST_USE = 3  # Use item
AP_COST_DROP = 2  # Drop item
AP_COST_TAKE = 2  # Take item
AP_COST_REPAIR = 5  # Repair item

# Experience gains
XP_GAIN_ROLL_FAIL = 5  # XP gain for roll failure
XP_GAIN_ROLL_SUCCESS = 3  # XP gain for roll success
XP_GAIN_ROLL = (XP_GAIN_ROLL_FAIL, XP_GAIN_ROLL_SUCCESS)
XP_GAIN_FIGHT_MISS = 5  # XP gain for fight failure (multiplier)
XP_GAIN_FIGHT_HIT = 3  # XP gain for fight success (multiplier)
XP_GAIN_FIGHT = (XP_GAIN_FIGHT_MISS, XP_GAIN_FIGHT_HIT)
XP_GAIN_BURST = 2  # XP gain in burst

# Turn time
TURN_TIME = 30

# Leveled stats multiplier for creatures
LEVELED_STATS_MULT = 10

# Computed statistics from S.P.E.C.I.A.L.
COMPUTED_STATS = (
    ('hit_points_per_level', lambda s, c: 3 + (s.endurance // 2)),
    ('skill_points_per_level', lambda s, c: (5 + (2 * s.intelligence)) * 2),
    ('max_health', lambda s, c: (15 + (s.strength + (2 * s.endurance)) + ((c.level - 1) * s.hit_points_per_level))),
    ('max_action_points', lambda s, c: 5 + (s.agility // 2)),
    # Secondary statistics
    ('armor_class', lambda s, c: s.agility),
    ('carry_weight', lambda s, c: (15 + (15 * s.strength)) // 3),
    ('melee_damage', lambda s, c: max(1, s.strength - 5) * 2),
    ('sequence', lambda s, c: 2 * s.perception),
    ('healing_rate', lambda s, c: (s.endurance // 3)),
    ('critical_chance', lambda s, c: s.luck),
    ('critical_raw_chance', lambda s, c: max(1, s.luck - 5)),
    # Resistances
    ('radiation_resistance', lambda s, c: 2 * s.endurance),
    ('poison_resistance', lambda s, c: 5 * s.endurance),
    # Skills
    ('small_guns', lambda s, c: 5 + (4 * s.agility)),
    ('big_guns', lambda s, c: 2 * s.agility),
    ('energy_weapons', lambda s, c: 2 * s.agility),
    ('unarmed', lambda s, c: 30 + (2 * (s.strength + s.agility))),
    ('melee_weapons', lambda s, c: 20 + (2 * (s.strength + s.agility))),
    ('throwing', lambda s, c: 4 * s.agility),
    ('first_aid', lambda s, c: 2 * (s.perception + s.endurance)),
    ('doctor', lambda s, c: 5 + s.perception + s.intelligence),
    ('chems', lambda s, c: 10 + (2 * s.intelligence)),
    ('sneak', lambda s, c: 5 + (3 * s.agility)),
    ('lockpick', lambda s, c: 10 + s.perception + s.agility),
    ('steal', lambda s, c: 3 * s.agility),
    ('traps', lambda s, c: 10 + (2 * s.perception)),
    ('explosives', lambda s, c: 2 * s.perception),
    ('science', lambda s, c: 4 * s.intelligence),
    ('repair', lambda s, c: 3 * s.intelligence),
    ('speech', lambda s, c: 5 * s.charisma),
    ('barter', lambda s, c: 4 * s.charisma),
    ('survival', lambda s, c: 2 * (s.endurance + s.intelligence)),
    ('knowledge', lambda s, c: 5 * s.intelligence),
)
LIST_COMPUTED_STATS = dict(COMPUTED_STATS)

# Computed needs per hour
COMPUTED_NEEDS = (
    ('thirst', lambda s, c: max(1, 20 - s.endurance)),
    ('hunger', lambda s, c: max(1, 15 - s.endurance)),
    ('sleep', lambda s, c: max(1, 10 - s.endurance)),
)
