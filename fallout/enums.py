# encoding: utf-8
from django.utils.translation import gettext_lazy as _

# General statistics
STATS_HEALTH = "health"
STATS_ACTION_POINTS = "action_points"
STATS_THIRST = "thirst"
STATS_HUNGER = "hunger"
STATS_SLEEP = "sleep"
STATS_RADS = "rads"
STATS_EXPERIENCE = "experience"
STATS_SKILL_POINTS = "skill_points"
STATS_PERK_POINTS = "perk_points"
STATS_KARMA = "karma"
STATS_MONEY = "money"
STATS_REWARD = "reward"
GENERAL_STATS = (
    (STATS_HEALTH, _("santé")),
    (STATS_ACTION_POINTS, _("points d'action")),
    (STATS_THIRST, _("soif")),
    (STATS_HUNGER, _("faim")),
    (STATS_SLEEP, _("sommeil")),
    (STATS_RADS, _("rads")),
    (STATS_EXPERIENCE, _("expérience")),
    (STATS_SKILL_POINTS, _("points de compétence")),
    (STATS_PERK_POINTS, _("points de talent")),
    (STATS_KARMA, _("karma")),
    (STATS_MONEY, _("argent")),
    (STATS_REWARD, _("récompense")),
)
LIST_GENERAL_STATS = dict(GENERAL_STATS)
LIST_NEEDS = [STATS_RADS, STATS_THIRST, STATS_HUNGER, STATS_SLEEP]

# S.P.E.C.I.A.L.
SPECIAL_STRENGTH = "strength"
SPECIAL_PERCEPTION = "perception"
SPECIAL_ENDURANCE = "endurance"
SPECIAL_CHARISMA = "charisma"
SPECIAL_INTELLIGENCE = "intelligence"
SPECIAL_AGILITY = "agility"
SPECIAL_LUCK = "luck"
SPECIALS = (
    (SPECIAL_STRENGTH, _("force")),
    (SPECIAL_PERCEPTION, _("perception")),
    (SPECIAL_ENDURANCE, _("endurance")),
    (SPECIAL_CHARISMA, _("charisme")),
    (SPECIAL_INTELLIGENCE, _("intelligence")),
    (SPECIAL_AGILITY, _("agilité")),
    (SPECIAL_LUCK, _("chance")),
)
LIST_SPECIALS = dict(SPECIALS)

# Secondary statistics
STATS_MAX_HEALTH = "max_health"
STATS_MAX_ACTION_POINTS = "max_action_points"
STATS_CARRY_WEIGHT = "carry_weight"
STATS_ARMOR_CLASS = "armor_class"
STATS_MELEE_DAMAGE = "melee_damage"
STATS_SEQUENCE = "sequence"
STATS_HEALING_RATE = "healing_rate"
STATS_AP_COST_MODIFIER = "ap_cost_modifier"
STATS_ONE_HAND_ACCURACY = "one_hand_accuracy"
STATS_TWO_HANDS_ACCURACY = "two_hands_accuracy"
STATS_DAMAGE_MODIFIER = "damage_modifier"
STATS_CRITICAL_CHANCE = "critical_chance"
STATS_CRITICAL_RAW_CHANCE = "critical_raw_chance"
STATS_CRITICAL_DAMAGE = "critical_damage"
SECONDARY_STATS = (
    (STATS_MAX_HEALTH, _("santé maximale")),
    (STATS_MAX_ACTION_POINTS, _("points d'action max.")),
    (STATS_CARRY_WEIGHT, _("charge maximale")),
    (STATS_ARMOR_CLASS, _("classe d'armure")),
    (STATS_MELEE_DAMAGE, _("dégâts en mêlée")),
    (STATS_SEQUENCE, _("initiative")),
    (STATS_HEALING_RATE, _("taux de regénération")),
    (STATS_AP_COST_MODIFIER, _("modificateur d'action")),
    (STATS_ONE_HAND_ACCURACY, _("précision à une main")),
    (STATS_TWO_HANDS_ACCURACY, _("précision à deux mains")),
    (STATS_DAMAGE_MODIFIER, _("modificateur de dégâts")),
    (STATS_CRITICAL_CHANCE, _("chance de critique")),
    (STATS_CRITICAL_RAW_CHANCE, _("chance de dégâts bruts")),
    (STATS_CRITICAL_DAMAGE, _("modificateur dégâts critiques")),
)
LIST_SECONDARY_STATS = dict(SECONDARY_STATS)

# Skills
SKILL_SMALL_GUNS = "small_guns"
SKILL_BIG_GUNS = "big_guns"
SKILL_ENERGY_WEAPONS = "energy_weapons"
SKILL_UNARMED = "unarmed"
SKILL_MELEE_WEAPONS = "melee_weapons"
SKILL_THROWING = "throwing"
SKILL_ATHLETICS = "athletics"
SKILL_DETECTION = "detection"
SKILL_FIRST_AID = "first_aid"
SKILL_DOCTOR = "doctor"
SKILL_CHEMS = "chems"
SKILL_SNEAK = "sneak"
SKILL_LOCKPICK = "lockpick"
SKILL_STEAL = "steal"
SKILL_TRAPS = "traps"
SKILL_EXPLOSIVES = "explosives"
SKILL_SCIENCE = "science"
SKILL_COMPUTERS = "computers"
SKILL_ELECTRONICS = "electronics"
SKILL_REPAIR = "repair"
SKILL_SPEECH = "speech"
SKILL_DECEPTION = "deception"
SKILL_BARTER = "barter"
SKILL_SURVIVAL = "survival"
SKILL_KNOWLEDGE = "knowledge"
SKILLS = (
    (SKILL_SMALL_GUNS, _("armes à feu légères")),
    (SKILL_BIG_GUNS, _("armes à feu lourdes")),
    (SKILL_ENERGY_WEAPONS, _("armes à énergie")),
    (SKILL_UNARMED, _("à mains nues")),
    (SKILL_MELEE_WEAPONS, _("armes de mêlée")),
    (SKILL_THROWING, _("armes de lancer")),
    (SKILL_ATHLETICS, _("athlétisme")),
    (SKILL_DETECTION, _("détection")),
    (SKILL_FIRST_AID, _("premiers secours")),
    (SKILL_DOCTOR, _("médecine")),
    (SKILL_CHEMS, _("pharmacologie")),
    (SKILL_SNEAK, _("discrétion")),
    (SKILL_LOCKPICK, _("crochetage")),
    (SKILL_STEAL, _("pickpocket")),
    (SKILL_TRAPS, _("pièges")),
    (SKILL_EXPLOSIVES, _("explosifs")),
    (SKILL_SCIENCE, _("science")),
    (SKILL_REPAIR, _("mécanique")),
    (SKILL_COMPUTERS, _("informatique")),
    (SKILL_ELECTRONICS, _("électronique")),
    (SKILL_SPEECH, _("persuasion")),
    (SKILL_DECEPTION, _("tromperie")),
    (SKILL_BARTER, _("marchandage")),
    (SKILL_SURVIVAL, _("survie")),
    (SKILL_KNOWLEDGE, _("connaissance")),
)
LIST_SKILLS = dict(SKILLS)

# Resistances
RESISTANCE_DAMAGE = "damage_resistance"
RESISTANCE_NORMAL = "normal_resistance"
RESISTANCE_LASER = "laser_resistance"
RESISTANCE_PLASMA = "plasma_resistance"
RESISTANCE_EXPLOSIVE = "explosive_resistance"
RESISTANCE_FIRE = "fire_resistance"
RESISTANCE_ELECTRICITY = "electricity_resistance"
RESISTANCE_POISON = "poison_resistance"
RESISTANCE_RADIATION = "radiation_resistance"
RESISTANCE_GAZ_CONTACT = "gas_contact_resistance"
RESISTANCE_GAZ_INHALED = "gas_inhaled_resistance"
RESISTANCES = (
    (RESISTANCE_DAMAGE, _("résistance aux dégâts")),
    (RESISTANCE_NORMAL, _("résistance physique")),
    (RESISTANCE_LASER, _("résistance aux lasers")),
    (RESISTANCE_PLASMA, _("résistance au plasma")),
    (RESISTANCE_EXPLOSIVE, _("résistance aux explosions")),
    (RESISTANCE_FIRE, _("résistance au feu")),
    (RESISTANCE_ELECTRICITY, _("résistance à l'électricité")),
    (RESISTANCE_POISON, _("résistance aux poisons")),
    (RESISTANCE_RADIATION, _("résistance aux radiations")),
    (RESISTANCE_GAZ_CONTACT, _("résistance au gaz (contact)")),
    (RESISTANCE_GAZ_INHALED, _("résistance au gaz (inhalé)")),
)
LIST_RESISTANCES = dict(RESISTANCES)

# Thresholds
THRESHOLD_DAMAGE = "damage_threshold"
THRESHOLD_NORMAL = "normal_threshold"
THRESHOLD_LASER = "laser_threshold"
THRESHOLD_PLASMA = "plasma_threshold"
THRESHOLD_EXPLOSIVE = "explosive_threshold"
THRESHOLD_FIRE = "fire_threshold"
THRESHOLD_ELECTRICITY = "electricity_threshold"
THRESHOLD_POISON = "poison_threshold"
THRESHOLD_RADIATION = "radiation_threshold"
THRESHOLD_GAZ_CONTACT = "gas_contact_threshold"
THRESHOLD_GAZ_INHALED = "gas_inhaled_threshold"
THRESHOLDS = (
    (THRESHOLD_DAMAGE, _("absorption de dégâts")),
    (THRESHOLD_NORMAL, _("absorption physique")),
    (THRESHOLD_LASER, _("absorption des lasers")),
    (THRESHOLD_PLASMA, _("absorption du plasma")),
    (THRESHOLD_EXPLOSIVE, _("absorption des explosions")),
    (THRESHOLD_FIRE, _("absorption du feu")),
    (THRESHOLD_ELECTRICITY, _("absorption de l'électricité")),
    (THRESHOLD_POISON, _("absorption des poisons")),
    (THRESHOLD_RADIATION, _("absorption des radiations")),
    (THRESHOLD_GAZ_CONTACT, _("absorption du gaz (contact)")),
    (THRESHOLD_GAZ_INHALED, _("absorption du gaz (inhalé)")),
)
LIST_THRESHOLDS = dict(THRESHOLDS)

# Weapon types
WEAPON_TYPE_PRIMARY = "primary"
WEAPON_TYPE_SECONDARY = "secondary"
WEAPON_TYPE_GRENADE = "grenade"
WEAPON_TYPE_UNARMED = "unarmed"
WEAPON_TYPES = (
    (WEAPON_TYPE_PRIMARY, _("arme principale")),
    (WEAPON_TYPE_SECONDARY, _("arme secondaire")),
    (WEAPON_TYPE_GRENADE, _("grenade")),
    (WEAPON_TYPE_UNARMED, _("à mains nues")),
)

ALL_RESISTANCES = tuple((field, label) for field, label in THRESHOLDS + RESISTANCES)
LIST_ALL_RESISTANCES = dict(ALL_RESISTANCES)

# Damage
DAMAGE_NORMAL = "normal"
DAMAGE_LASER = "laser"
DAMAGE_PLASMA = "plasma"
DAMAGE_EXPLOSIVE = "explosive"
DAMAGE_FIRE = "fire"
DAMAGE_ELECTRICITY = "electricity"
DAMAGE_POISON = "poison"
DAMAGE_RADIATION = "radiation"
DAMAGE_GAZ_CONTACT = "gas_contact"
DAMAGE_GAZ_INHALED = "gas_inhaled"
DAMAGE_RAW = "raw"
DAMAGE_THIRST = "thirst"
DAMAGE_HUNGER = "hunger"
DAMAGE_SLEEP = "sleep"
HEAL_HEALTH = "heal"
HEAL_THIRST = "heal_thirst"
HEAL_HUNGER = "heal_hunger"
HEAL_SLEEP = "heal_sleep"
HEAL_RADIATION = "heal_rad"
ADD_MONEY = "add_money"
REMOVE_MONEY = "remove_money"

DAMAGES = (
    (DAMAGE_NORMAL, _("dégâts normaux")),
    (DAMAGE_LASER, _("dégâts de laser")),
    (DAMAGE_PLASMA, _("dégâts de plasma")),
    (DAMAGE_EXPLOSIVE, _("dégâts explosifs")),
    (DAMAGE_FIRE, _("dégâts de feu")),
    (DAMAGE_ELECTRICITY, _("dégâts d'électricité")),
    (DAMAGE_POISON, _("dégâts de poison")),
    (DAMAGE_RADIATION, _("dégâts de radiations")),
    (DAMAGE_GAZ_CONTACT, _("dégâts de gaz (contact)")),
    (DAMAGE_GAZ_INHALED, _("dégâts de gaz (inhalé)")),
    (DAMAGE_RAW, _("dégâts directs")),
    (DAMAGE_THIRST, _("augmentation de la soif")),
    (DAMAGE_HUNGER, _("augmentation de la faim")),
    (DAMAGE_SLEEP, _("augmentation du sommeil")),
)
HEALS = (
    (HEAL_HEALTH, _("soins de santé")),
    (HEAL_RADIATION, _("soins de radiations")),
    (HEAL_THIRST, _("diminution de la soif")),
    (HEAL_HUNGER, _("diminution de la faim")),
    (HEAL_SLEEP, _("diminution du sommeil")),
)
MONEY = (
    (ADD_MONEY, _("gain d'argent")),
    (REMOVE_MONEY, _("perte d'argent")),
)
DAMAGES_TYPES = (
    (_("dégâts"), DAMAGES),
    (_("soins"), HEALS),
    (_("argent"), MONEY),
)
LIST_DAMAGES_TYPES = dict(DAMAGES + HEALS + MONEY)
LIST_PHYSICAL_DAMAGE = (DAMAGE_NORMAL, DAMAGE_LASER, DAMAGE_PLASMA, DAMAGE_EXPLOSIVE, DAMAGE_FIRE)
LIST_HEALS = (HEAL_HEALTH, HEAL_RADIATION, HEAL_THIRST, HEAL_HUNGER, HEAL_SLEEP)
LIST_MONEY = (ADD_MONEY, REMOVE_MONEY)
LIST_NON_DAMAGE = (DAMAGE_RAW, DAMAGE_THIRST, DAMAGE_HUNGER, DAMAGE_SLEEP) + LIST_HEALS + LIST_MONEY

# Damage / resistance
DAMAGE_RESISTANCE = {
    DAMAGE_NORMAL: RESISTANCE_NORMAL,
    DAMAGE_LASER: RESISTANCE_LASER,
    DAMAGE_PLASMA: RESISTANCE_PLASMA,
    DAMAGE_EXPLOSIVE: RESISTANCE_EXPLOSIVE,
    DAMAGE_FIRE: RESISTANCE_FIRE,
    DAMAGE_ELECTRICITY: RESISTANCE_ELECTRICITY,
    DAMAGE_POISON: RESISTANCE_POISON,
    DAMAGE_RADIATION: RESISTANCE_RADIATION,
    DAMAGE_GAZ_CONTACT: RESISTANCE_GAZ_CONTACT,
    DAMAGE_GAZ_INHALED: RESISTANCE_GAZ_INHALED,
}

# Damage / threshold
DAMAGE_THRESHOLD = {
    DAMAGE_NORMAL: THRESHOLD_NORMAL,
    DAMAGE_LASER: THRESHOLD_LASER,
    DAMAGE_PLASMA: THRESHOLD_PLASMA,
    DAMAGE_EXPLOSIVE: THRESHOLD_EXPLOSIVE,
    DAMAGE_FIRE: THRESHOLD_FIRE,
    DAMAGE_ELECTRICITY: THRESHOLD_ELECTRICITY,
    DAMAGE_POISON: THRESHOLD_POISON,
    DAMAGE_RADIATION: THRESHOLD_RADIATION,
    DAMAGE_GAZ_CONTACT: THRESHOLD_GAZ_CONTACT,
    DAMAGE_GAZ_INHALED: THRESHOLD_GAZ_INHALED,
}

# Short labels for damage types
DAMAGE_SHORTS = (
    (DAMAGE_NORMAL, _("N")),
    (DAMAGE_LASER, _("L")),
    (DAMAGE_PLASMA, _("P")),
    (DAMAGE_EXPLOSIVE, _("E")),
    (DAMAGE_FIRE, _("F")),
    (DAMAGE_ELECTRICITY, _("E")),
    (DAMAGE_POISON, _("P")),
    (DAMAGE_RADIATION, _("R")),
    (DAMAGE_GAZ_CONTACT, _("GC")),
    (DAMAGE_GAZ_INHALED, _("GI")),
)

# Damage icons
DAMAGE_ICONS = {
    DAMAGE_NORMAL: "💪",
    DAMAGE_LASER: "☀️",
    DAMAGE_PLASMA: "✨",
    DAMAGE_EXPLOSIVE: "💥",
    DAMAGE_FIRE: "🔥",
    DAMAGE_ELECTRICITY: "⚡",
    DAMAGE_POISON: "☣️",
    DAMAGE_RADIATION: "☢️",
    DAMAGE_GAZ_CONTACT: "☁️",
    DAMAGE_GAZ_INHALED: "☁️",
    DAMAGE_RAW: "💀",
    DAMAGE_THIRST: "💧🔻",
    DAMAGE_HUNGER: "🍖🔻",
    DAMAGE_SLEEP: "💤🔻",
    HEAL_HEALTH: "❤️",
    HEAL_RADIATION: "💉",
    HEAL_THIRST: "💧🔺",
    HEAL_HUNGER: "🍖🔺",
    HEAL_SLEEP: "💤🔺",
    ADD_MONEY: "💰",
    REMOVE_MONEY: "💸",
}

# Leveled stats
HIT_POINTS_PER_LEVEL = "hit_points_per_level"
SKILL_POINTS_PER_LEVEL = "skill_points_per_level"
PERK_RATE = "perk_rate"
LEVELED_STATS = (
    (HIT_POINTS_PER_LEVEL, _("santé par niveau")),
    (SKILL_POINTS_PER_LEVEL, _("compétences par niveau")),
    (PERK_RATE, _("niveaux pour un talent")),
)
LIST_LEVELED_STATS = dict(LEVELED_STATS)

# Rollable statistics
ROLL_STATS = (
    (_("S.P.E.C.I.A.L."), SPECIALS),
    (_("Compétences"), SKILLS),
)
LIST_ROLL_STATS = dict(sum((stats for label, stats in ROLL_STATS), ()))

# All statistics
ALL_EDITABLE_STATS = ROLL_STATS + (
    (_("Statistiques secondaires"), SECONDARY_STATS),
    (_("Statistiques de niveau"), LEVELED_STATS),
    (_("Résistances"), ALL_RESISTANCES),
)
ALL_STATS = ALL_EDITABLE_STATS + ((_("Etat général"), GENERAL_STATS),)

# Lists of statistics
NON_SPECIAL_STATS = SKILLS + SECONDARY_STATS + RESISTANCES + THRESHOLDS + LEVELED_STATS
LIST_NON_SPECIAL_STATS = dict(NON_SPECIAL_STATS)
EDITABLE_STATS = SPECIALS + NON_SPECIAL_STATS
LIST_EDITABLE_STATS = dict(EDITABLE_STATS)
LIST_ALL_STATS = dict(sum((stats for _, stats in ALL_STATS), ()))

# Item type
ITEM_WEAPON = "weapon"
ITEM_AMMO = "ammo"
ITEM_ARMOR = "armor"
ITEM_HELMET = "helmet"
ITEM_GRENADE = "grenade"
SLOT_ITEM_TYPES = (
    (ITEM_WEAPON, _("arme")),
    (ITEM_AMMO, _("munition")),
    (ITEM_ARMOR, _("armure")),
    (ITEM_HELMET, _("casque")),
    (ITEM_GRENADE, _("grenade")),
)
LIST_SLOT_ITEM_TYPES = dict(SLOT_ITEM_TYPES)

ITEM_EXTRA = "extra"
ITEM_TOOL = "tool"
ITEM_FOOD = "food"
ITEM_CHEM = "chem"
ITEM_BOOK = "book"
ITEM_MISC = "misc"
ITEM_TYPES = SLOT_ITEM_TYPES + (
    (ITEM_EXTRA, _("accessoire")),
    (ITEM_TOOL, _("outil")),
    (ITEM_FOOD, _("nourriture")),
    (ITEM_CHEM, _("drogue")),
    (ITEM_BOOK, _("livre")),
    (ITEM_MISC, _("autre")),
)
LIST_ITEM_TYPES = dict(ITEM_TYPES)

# Weapon modes
MODE_RANGED = "ranged"
MODE_LONG = "long"
MODE_SCOPED = "scoped"
MODE_MELEE = "melee"
MODE_THROW = "throw"
MODES = (
    (MODE_RANGED, _("attaque à distance")),
    (MODE_LONG, _("attaque à longue distance")),
    (MODE_SCOPED, _("attaque avec lunette")),
    (MODE_MELEE, _("attaque en mêlée")),
    (MODE_THROW, _("attaque de lancer")),
)

# Hands required for weapon
HANDS = (
    (0, _("aucune")),
    (1, _("une main")),
    (2, _("deux mains")),
)

# Races
RACE_HUMAN = "human"
RACE_GHOUL = "ghoul"
RACE_SUPER_MUTANT = "super_mutant"
RACE_DEATHCLAW = "deathclaw"
RACE_ROBOT = "robot"
RACE_ANIMAL = "animal"
RACE_CREATURE = "creature"
RACES = (
    (RACE_HUMAN, _("humain")),
    (RACE_GHOUL, _("ghoule")),
    (RACE_SUPER_MUTANT, _("super-mutant")),
    (RACE_DEATHCLAW, _("écorcheur")),
    (RACE_ROBOT, _("robot")),
    (RACE_ANIMAL, _("animal")),
    (RACE_CREATURE, _("créature")),
)
LIST_RACES = dict(RACES)

# Body parts
PART_TORSO = "torso"
PART_LEGS = "legs"
PART_ARMS = "arms"
PART_HEAD = "head"
PART_EYES = "eyes"
BODY_PARTS = (
    (PART_TORSO, _("torse")),
    (PART_LEGS, _("jambes")),
    (PART_ARMS, _("bras")),
    (PART_HEAD, _("tête")),
    (PART_EYES, _("yeux")),
)
LIST_BODY_PARTS = dict(BODY_PARTS)

# Fight status
STATUS_HIT_SUCCEED = "hit_succeed"
STATUS_HIT_FAILED = "hit_failed"
STATUS_NOT_ENOUGH_AP = "not_enough_ap"
STATUS_NO_MORE_AMMO = "no_more_ammo"
STATUS_TARGET_DEAD = "target_dead"
STATUS_TARGET_KILLED = "target_killed"
STATUS_WEAPON_BROKEN = "weapon_broken"
FIGHT_STATUS = (
    (STATUS_HIT_SUCCEED, _("cible touchée")),
    (STATUS_HIT_FAILED, _("cible manquée")),
    (STATUS_NOT_ENOUGH_AP, _("points d'action insuffisants")),
    (STATUS_NO_MORE_AMMO, _("munitions insuffisantes")),
    (STATUS_TARGET_DEAD, _("cible inconsciente")),
    (STATUS_TARGET_KILLED, _("cible tuée")),
    (STATUS_WEAPON_BROKEN, _("arme défectueuse")),
)
LIST_FIGHT_STATUS = dict(FIGHT_STATUS)

# Radiation effects
RADS_LABELS = {
    (0, 200): _("Etat normal"),
    (200, 400): _("Faiblement irradié"),
    (400, 600): _("Modérément irradié"),
    (600, 800): _("Fortement irradié"),
    (800, 1000): _("Dangereusement irradié"),
    (1000, None): _("Mortellement irradié"),
}

# Dehydration effets
THIRST_LABELS = {
    (0, 200): _("Désaltéré"),
    (200, 400): _("Faiblement assoiffé"),
    (400, 600): _("Modérément assoiffé"),
    (600, 800): _("Fortement assoiffé"),
    (800, 1000): _("Dangereusement assoiffé"),
    (1000, None): _("Mortellement assoiffé"),
}

# Hunger effects
HUNGER_LABELS = {
    (0, 200): _("Rassasié"),
    (200, 400): _("Faiblement affamé"),
    (400, 600): _("Modérément affamé"),
    (600, 800): _("Fortement affamé"),
    (800, 1000): _("Dangereusement affamé"),
    (1000, None): _("Mortellement affamé"),
}

# Sleep deprivation effects
SLEEP_LABELS = {
    (0, 200): _("Reposé"),
    (200, 400): _("Faiblement fatigué"),
    (400, 600): _("Modérément fatigué"),
    (600, 800): _("Fortement fatigué"),
    (800, 1000): _("Dangereusement fatigué"),
    (1000, None): _("Mortellement fatigué"),
}

# Labels
LABEL_FAIL = _("échec")
LABEL_SUCCESS = _("réussite")
LABEL_CRITICAL = _("critique")


def get_label(success, critical):
    return " ".join((str([LABEL_FAIL, LABEL_SUCCESS][success]), str(["", LABEL_CRITICAL][critical]))).strip()


__all__ = (
    "ADD_MONEY",
    "ALL_EDITABLE_STATS",
    "ALL_RESISTANCES",
    "ALL_STATS",
    "BODY_PARTS",
    "DAMAGES",
    "DAMAGES_TYPES",
    "DAMAGE_ELECTRICITY",
    "DAMAGE_EXPLOSIVE",
    "DAMAGE_FIRE",
    "DAMAGE_GAZ_CONTACT",
    "DAMAGE_GAZ_INHALED",
    "DAMAGE_HUNGER",
    "DAMAGE_ICONS",
    "DAMAGE_LASER",
    "DAMAGE_NORMAL",
    "DAMAGE_PLASMA",
    "DAMAGE_POISON",
    "DAMAGE_RADIATION",
    "DAMAGE_RAW",
    "DAMAGE_RESISTANCE",
    "DAMAGE_SHORTS",
    "DAMAGE_SLEEP",
    "DAMAGE_THIRST",
    "DAMAGE_THRESHOLD",
    "EDITABLE_STATS",
    "FIGHT_STATUS",
    "GENERAL_STATS",
    "HANDS",
    "HEALS",
    "HEAL_HEALTH",
    "HEAL_HUNGER",
    "HEAL_RADIATION",
    "HEAL_SLEEP",
    "HEAL_THIRST",
    "HIT_POINTS_PER_LEVEL",
    "HUNGER_LABELS",
    "ITEM_AMMO",
    "ITEM_ARMOR",
    "ITEM_BOOK",
    "ITEM_CHEM",
    "ITEM_EXTRA",
    "ITEM_FOOD",
    "ITEM_GRENADE",
    "ITEM_HELMET",
    "ITEM_MISC",
    "ITEM_TOOL",
    "ITEM_TYPES",
    "ITEM_WEAPON",
    "LABEL_CRITICAL",
    "LABEL_FAIL",
    "LABEL_SUCCESS",
    "LEVELED_STATS",
    "LIST_ALL_RESISTANCES",
    "LIST_ALL_STATS",
    "LIST_BODY_PARTS",
    "LIST_DAMAGES_TYPES",
    "LIST_EDITABLE_STATS",
    "LIST_FIGHT_STATUS",
    "LIST_GENERAL_STATS",
    "LIST_HEALS",
    "LIST_ITEM_TYPES",
    "LIST_LEVELED_STATS",
    "LIST_MONEY",
    "LIST_NEEDS",
    "LIST_NON_DAMAGE",
    "LIST_NON_SPECIAL_STATS",
    "LIST_PHYSICAL_DAMAGE",
    "LIST_RACES",
    "LIST_RESISTANCES",
    "LIST_ROLL_STATS",
    "LIST_SECONDARY_STATS",
    "LIST_SKILLS",
    "LIST_SLOT_ITEM_TYPES",
    "LIST_SPECIALS",
    "LIST_THRESHOLDS",
    "MODES",
    "MODE_LONG",
    "MODE_MELEE",
    "MODE_RANGED",
    "MODE_SCOPED",
    "MODE_THROW",
    "NON_SPECIAL_STATS",
    "PART_ARMS",
    "PART_EYES",
    "PART_HEAD",
    "PART_LEGS",
    "PART_TORSO",
    "PERK_RATE",
    "RACES",
    "RACE_ANIMAL",
    "RACE_CREATURE",
    "RACE_DEATHCLAW",
    "RACE_GHOUL",
    "RACE_HUMAN",
    "RACE_ROBOT",
    "RACE_SUPER_MUTANT",
    "RADS_LABELS",
    "REMOVE_MONEY",
    "RESISTANCES",
    "RESISTANCE_DAMAGE",
    "RESISTANCE_ELECTRICITY",
    "RESISTANCE_EXPLOSIVE",
    "RESISTANCE_FIRE",
    "RESISTANCE_GAZ_CONTACT",
    "RESISTANCE_GAZ_INHALED",
    "RESISTANCE_LASER",
    "RESISTANCE_NORMAL",
    "RESISTANCE_PLASMA",
    "RESISTANCE_POISON",
    "RESISTANCE_RADIATION",
    "ROLL_STATS",
    "SECONDARY_STATS",
    "SKILLS",
    "SKILL_BARTER",
    "SKILL_BIG_GUNS",
    "SKILL_CHEMS",
    "SKILL_DOCTOR",
    "SKILL_ENERGY_WEAPONS",
    "SKILL_EXPLOSIVES",
    "SKILL_FIRST_AID",
    "SKILL_KNOWLEDGE",
    "SKILL_LOCKPICK",
    "SKILL_MELEE_WEAPONS",
    "SKILL_POINTS_PER_LEVEL",
    "SKILL_REPAIR",
    "SKILL_SCIENCE",
    "SKILL_SMALL_GUNS",
    "SKILL_SNEAK",
    "SKILL_SPEECH",
    "SKILL_STEAL",
    "SKILL_SURVIVAL",
    "SKILL_THROWING",
    "SKILL_TRAPS",
    "SKILL_UNARMED",
    "SLEEP_LABELS",
    "SLOT_ITEM_TYPES",
    "SPECIALS",
    "SPECIAL_AGILITY",
    "SPECIAL_CHARISMA",
    "SPECIAL_ENDURANCE",
    "SPECIAL_INTELLIGENCE",
    "SPECIAL_LUCK",
    "SPECIAL_PERCEPTION",
    "SPECIAL_STRENGTH",
    "STATS_ACTION_POINTS",
    "STATS_AP_COST_MODIFIER",
    "STATS_ARMOR_CLASS",
    "STATS_CARRY_WEIGHT",
    "STATS_CRITICAL_CHANCE",
    "STATS_CRITICAL_DAMAGE",
    "STATS_CRITICAL_RAW_CHANCE",
    "STATS_DAMAGE_MODIFIER",
    "STATS_EXPERIENCE",
    "STATS_HEALING_RATE",
    "STATS_HEALTH",
    "STATS_HUNGER",
    "STATS_KARMA",
    "STATS_MAX_ACTION_POINTS",
    "STATS_MAX_HEALTH",
    "STATS_MONEY",
    "STATS_MELEE_DAMAGE",
    "STATS_ONE_HAND_ACCURACY",
    "STATS_PERK_POINTS",
    "STATS_RADS",
    "STATS_REWARD",
    "STATS_SEQUENCE",
    "STATS_SKILL_POINTS",
    "STATS_SLEEP",
    "STATS_THIRST",
    "STATS_TWO_HANDS_ACCURACY",
    "STATUS_HIT_FAILED",
    "STATUS_HIT_SUCCEED",
    "STATUS_NOT_ENOUGH_AP",
    "STATUS_NO_MORE_AMMO",
    "STATUS_TARGET_DEAD",
    "STATUS_TARGET_KILLED",
    "STATUS_WEAPON_BROKEN",
    "THIRST_LABELS",
    "THRESHOLDS",
    "THRESHOLD_DAMAGE",
    "THRESHOLD_ELECTRICITY",
    "THRESHOLD_EXPLOSIVE",
    "THRESHOLD_FIRE",
    "THRESHOLD_GAZ_CONTACT",
    "THRESHOLD_GAZ_INHALED",
    "THRESHOLD_LASER",
    "THRESHOLD_NORMAL",
    "THRESHOLD_PLASMA",
    "THRESHOLD_POISON",
    "THRESHOLD_RADIATION",
    "WEAPON_TYPE_GRENADE",
    "WEAPON_TYPE_PRIMARY",
    "WEAPON_TYPE_SECONDARY",
    "WEAPON_TYPE_UNARMED",
    "WEAPON_TYPES",
    "get_label",
)
