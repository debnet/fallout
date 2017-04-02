# encoding: utf-8
from rpg.fallout.enums import *  # noqa


# Body part modifiers (ranged, melee, critical)
BODY_PARTS_MODIFIERS = {
    PART_TORSO: (0, 0, 0),
    PART_LEGS: (-20, -10, 10),
    PART_ARMS: (-30, -15, 20),
    PART_HEAD: (-40, -20, 25),
    PART_EYES: (-60, -30, 30),
}

# Body part randomly hit if not targetted
BODY_PARTS_RANDOM_CHANCES = (
    (PART_EYES, 5),
    (PART_HEAD, 10),
    (PART_ARMS, 30),
    (PART_LEGS, 50),
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
        RESISTANCE_ELECTRICITY: (30, 0, 100),
        PERK_RATE: (2, None, None),
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
        RESISTANCE_NORMAL_DAMAGE: (25, 0, 100),
        RESISTANCE_LASER_DAMAGE: (25, 0, 100),
        RESISTANCE_PLASMA_DAMAGE: (25, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (25, 0, 100),
        RESISTANCE_RADIATION: (50, 0, 100),
        RESISTANCE_POISON: (20, 0, 100),
        RESISTANCE_FIRE: (25, 0, 100),
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
        RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
        RESISTANCE_FIRE: (40, 0, 100),
        RESISTANCE_GAZ_CONTACT: (40, 0, 100),
        RESISTANCE_GAZ_INHALED: (40, 0, 100),
        HIT_POINTS_PER_LEVEL: (2, None, None),
        STATS_MELEE_DAMAGE: (5, None, None),
        STATS_DAMAGE_THRESHOLD: (4, None, None),
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
        RESISTANCE_NORMAL_DAMAGE: (40, 0, 100),
        RESISTANCE_LASER_DAMAGE: (40, 0, 100),
        RESISTANCE_PLASMA_DAMAGE: (40, 0, 100),
        RESISTANCE_EXPLOSIVE_DAMAGE: (40, 0, 100),
        RESISTANCE_RADIATION: (100, 0, 100),
        RESISTANCE_POISON: (100, 0, 100),
        RESISTANCE_FIRE: (40, 0, 100),
        RESISTANCE_ELECTRICITY: (-50, 0, 100),
        RESISTANCE_GAZ_CONTACT: (100, 0, 100),
        RESISTANCE_GAZ_INHALED: (100, 0, 100),
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
    }
}

# Radiation effects
IRRADIATION_EFFECTS = {
    (0, 149): {},
    (150, 299): {
        SPECIAL_STRENGTH: (-1, None, None),
    },
    (300, 449): {
        STATS_HEALING_RATE: (-3, 0, None),
        SPECIAL_STRENGTH: (-1, 1, None),
        SPECIAL_AGILITY: (-1, 1, None),
    },
    (450, 599): {
        STATS_HEALING_RATE: (-5, 0, None),
        STATS_MAX_HEALTH: (-5, 0, None),
        SPECIAL_STRENGTH: (-2, 1, None),
        SPECIAL_ENDURANCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (600, 999): {
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
        STATS_HEALING_RATE: (-10, 0, None),
        STATS_MAX_HEALTH: (-20, 0, None),
        SPECIAL_STRENGTH: (-6, 1, None),
        SPECIAL_PERCEPTION: (-5, 1, None),
        SPECIAL_ENDURANCE: (-5, 1, None),
        SPECIAL_CHARISMA: (-5, 1, None),
        SPECIAL_INTELLIGENCE: (-3, 1, None),
        SPECIAL_AGILITY: (-6, 1, None),
    }
}

# Dehydration effets
DEHYDRATION_EFFETS = {
    (0, 199): {},
    (200, 399): {
        SPECIAL_ENDURANCE: (-1, 1, None),
    },
    (400, 599): {
        SPECIAL_PERCEPTION: (-1, 1, None),
        SPECIAL_ENDURANCE: (-2, 1, None),
    },
    (600, 799): {
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_ENDURANCE: (-2, 1, None),
        SPECIAL_INTELLIGENCE: (-1, 1, None),
    },
    (8000, 999): {
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_ENDURANCE: (-3, 1, None),
        SPECIAL_INTELLIGENCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (1000, None): {
        STATS_HEALTH: (-9999, 0, None),
    }
}

# Hunger effects
HUNGER_EFFECTS = {
    (0, 199): {},
    (200, 399): {
        SPECIAL_STRENGTH: (-1, 1, None),
    },
    (400, 599): {
        SPECIAL_STRENGTH: (-2, 1, None),
        SPECIAL_CHARISMA: (-1, 1, None),
    },
    (600, 799): {
        SPECIAL_STRENGTH: (-3, 1, None),
        SPECIAL_PERCEPTION: (-1, 1, None),
        SPECIAL_CHARISMA: (-2, 1, None),
    },
    (8000, 999): {
        SPECIAL_STRENGTH: (-3, 1, None),
        SPECIAL_PERCEPTION: (-2, 1, None),
        SPECIAL_CHARISMA: (-2, 1, None),
    },
    (1000, None): {
        STATS_HEALTH: (-9999, 0, None),
    }
}

# Sleep deprivation effects
SLEEP_EFFECTS = {
    (0, 199): {},
    (200, 399): {
        SPECIAL_AGILITY: (-1, 1, None),
    },
    (400, 599): {
        SPECIAL_INTELLIGENCE: (-1, 1, None),
        SPECIAL_AGILITY: (-2, 1, None),
    },
    (600, 799): {
        SPECIAL_ENDURANCE: (-1, 1, None),
        SPECIAL_INTELLIGENCE: (-2, 1, None),
        SPECIAL_AGILITY: (-3, 1, None),
    },
    (8000, 999): {
        SPECIAL_ENDURANCE: (-2, 1, None),
        SPECIAL_INTELLIGENCE: (-2, 1, None),
        SPECIAL_AGILITY: (-3, 1, None),
    },
    (1000, None): {
        STATS_HEALTH: (-9999, 0, None),
    }
}

# Survival effects
SURVIVAL_EFFECTS = (
    (STATS_IRRADIATION, IRRADIATION_EFFECTS),
    (STATS_DEHYDRATION, DEHYDRATION_EFFETS),
    (STATS_HUNGER, HUNGER_EFFECTS),
    (STATS_SLEEP, SLEEP_EFFECTS),
)

# Critical rolls
CRITICAL_FAIL_D10 = 10
CRITICAL_FAIL_D100 = 96

# Valeur de base des points d'expérience
BASE_XP = 1000

# Action points cost
AP_COST_FIGHT = 5  # Fight unarmed

# Computed statistics from S.P.E.C.I.A.L.
COMPUTED_STATS = (
    ('hit_points_per_level', lambda s, c: 3 + (s.endurance // 2)),
    ('skill_points_per_level', lambda s, c: 5 + (2 * s.intelligence)),
    ('max_health', lambda s, c: (15 + (s.strength + (2 * s.endurance)) + ((c.level - 1) * s.hit_points_per_level))),
    ('max_action_points', lambda s, c: 5 + (s.agility // 2)),
    # Secondary statistics
    ('armor_class', lambda s, c: s.agility),
    ('carry_weight', lambda s, c: (25 + (25 * s.strength)) * 450),  # 1 lb = 453.592 g
    ('melee_damage', lambda s, c: max(0, s.strength - 5)),
    ('sequence', lambda s, c: 2 * s.perception),
    ('healing_rate', lambda s, c: (s.endurance // 3)),
    ('critical_chance', lambda s, c: s.luck),
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
    ('science', lambda s, c: 4 * s.intelligence),
    ('repair', lambda s, c: 3 * s.intelligence),
    ('speech', lambda s, c: 5 * s.charisma),
    ('barter', lambda s, c: 4 * s.charisma),
    ('gambling', lambda s, c: 5 * s.luck),
    ('survival', lambda s, c: 2 * (s.endurance + s.intelligence)),
    ('knowledge', lambda s, c: 5 * s.intelligence),
)

# Computed needs per hour
COMPUTED_NEEDS = {
    ('dehydration', lambda s, c: min(1, 20 - s.endurance * 2)),
    ('hunger', lambda s, c: min(1, 16 - s.endurance * 2)),
    ('sleep', lambda s, c: min(1, 14 - s.endurance * 2)),
}
