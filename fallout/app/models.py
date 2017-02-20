# encoding: utf-8
from random import randint, choice
from typing import Dict, Iterable, List, Tuple

from common.models import CommonModel, Entity
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Sum
from django.utils.translation import ugettext as _

from fallout.app.constants import *  # noqa
from fallout.app.enums import *  # noqa


class Campaign(CommonModel):
    """
    Aventure
    """
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    game_date = models.DateTimeField(verbose_name=_("date"))
    current_character = models.ForeignKey(
        'Character', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name=_("personnage actif"))
    active_effects = models.ManyToManyField(
        'Effect', blank=True,
        related_name='+', verbose_name=_("effets actifs"))

    def clear_loot(self):
        """
        Supprime les butins non réclamés de la campagne
        """
        return self.loots.all().delete()

    def __str__(self):
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
    armor_class = models.PositiveSmallIntegerField(default=0, verbose_name=_("esquive"))
    damage_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil de dégâts"))
    damage_resistance = models.PositiveSmallIntegerField(default=0, verbose_name=_("résistance aux dégâts"))
    carry_weight = models.PositiveSmallIntegerField(default=0, verbose_name=_("charge maximale"))
    melee_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("attaque en mélée"))
    sequence = models.PositiveSmallIntegerField(default=0, verbose_name=_("initiative"))
    healing_rate = models.PositiveSmallIntegerField(default=0, verbose_name=_("taux de regénération"))
    critical_chance = models.PositiveSmallIntegerField(default=0, verbose_name=_("chance de critique"))
    # Damage resistances
    normal_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts normaux"))
    laser_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts de laser"))
    plasma_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts de plasma"))
    explosive_damage_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux dégâts explosifs"))
    # Environment resistances
    radiation_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux radiations"))
    poison_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance aux poisons"))
    fire_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance au feu"))
    electricity_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance à l'électricité"))
    gas_contact_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance au gaz (contact)"))
    gas_inhaled_resistance = models.SmallIntegerField(default=0, verbose_name=_("résistance au gaz (inhalé)"))
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
    perk_rate = models.SmallIntegerField(default=0, verbose_name=_("niveaux pour un talent"))

    def __str__(self):
        return self.character.name

    @staticmethod
    def get(character: 'Character'):
        stats = Stats()
        stats.character = character
        old_max_health = stats.max_health
        old_max_action_points = stats.max_action_points
        # Get all character's stats
        for stats_name in LIST_EDITABLE_STATS:
            setattr(stats, stats_name, getattr(character, stats_name, 0))
        # Racial modifiers
        stats._change_all_stats(**RACES_STATS.get(character.race, {}))
        # Survival modifiers
        for stats_name, survival in SURVIVAL_EFFECTS:
            for (mini, maxi), effects in survival.items():
                if mini <= getattr(character, stats_name, 0) < maxi:
                    stats._change_all_stats(**effects)
        # Equipment modifiers
        for equipment in character.equipments.filter(slot__isnull=False)\
                .select_related('item').prefetch_related('item__modifiers').all():
            for modifier in equipment.item.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Active effects modifiers
        for effect in character.active_effects.select_related('effect').prefetch_related('effect__modifiers').filter(
                Q(start_date__isnull=True) | Q(start_date__gte=F('character__campaign__game_date')),
                Q(end_date__isnull=True) | Q(end_date__lte=F('character__campaign__game_date'))):
            for modifier in effect.effect.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Campaign effects modifiers
        if character.campaign:
            for modifier in character.campaign.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Derivated statistics
        for stats_name, formula in COMPUTED_STATS:
            stats._change_stats(stats_name, formula(stats, character))
        # Health & action points
        if character.health > stats.max_health or character.health == old_max_health:
            character.health = stats.max_health
        if character.action_points > stats.max_action_points or character.action_points == old_max_action_points:
            character.action_points = stats.max_action_points
        return stats

    def _change_all_stats(self, **stats: Dict[str, Tuple[int, int, int]]):
        assert isinstance(self, Stats), _("Cette fonction ne peut être utilisée que par les statistiques.")
        for name, values in stats.items():
            self._change_stats(name, *values)

    def _change_stats(self, name: str, value: int=0, mini: int=None, maxi: int=None):
        assert isinstance(self, Stats), _("Cette fonction ne peut être utilisée que par les statistiques.")
        target = self if name in LIST_EDITABLE_STATS else self.character
        mini = mini if mini is not None else float('-inf')
        maxi = maxi if maxi is not None else float('+inf')
        setattr(target, name, min(max(getattr(target, name, 0) + value, mini), maxi))

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
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    race = models.CharField(max_length=12, choices=RACES, default=RACE_HUMAN, verbose_name=_("race"))
    level = models.PositiveSmallIntegerField(default=1, verbose_name=_("niveau"))
    is_player = models.BooleanField(default=False, verbose_name=_("joueur ?"))
    # Primary statistics
    experience = models.PositiveIntegerField(default=0, verbose_name=_("expérience"))
    karma = models.SmallIntegerField(default=0, verbose_name=_("karma"))
    health = models.PositiveSmallIntegerField(default=0, verbose_name=_("santé"))
    action_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points d'action"))
    skill_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de compétences"))
    perk_points = models.PositiveSmallIntegerField(default=0, verbose_name=_("points de talent"))
    # Needs
    dehydration = models.PositiveSmallIntegerField(default=0, verbose_name=_("soif"))
    hunger = models.PositiveSmallIntegerField(default=0, verbose_name=_("faim"))
    sleep = models.PositiveSmallIntegerField(default=0, verbose_name=_("sommeil"))
    irradiation = models.PositiveSmallIntegerField(default=0, verbose_name=_("irradiation"))
    # Statistics cache
    _stats = {}

    @property
    def stats(self) -> Stats:
        stats = Character._stats.get(self.id) or Stats.get(self)
        if self.id:
            Character._stats[self.id] = stats
        return stats

    def charge(self):
        return self.equipments.aggregate(charge=Sum(F('count') * F('item__weight'))).get('charge', 0)

    def save(self, *args, **kwargs):
        self.check_level()
        Character._stats.pop(self.id, None)
        if not self.id:
            self.health = self.stats.max_health
            self.action_points = self.stats.max_action_points
        super().save(*args, **kwargs)

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
            self.max_health += self.stats.hit_points_per_level
            self.skill_points += self.stats.skill_points_per_level
            if not self.level % self.stats.perk_rate:
                self.perk_points += 1
            level += 1
        return level

    def update_needs(self, hours: float=0.0) -> None:
        """
        Mise à jour des besoins
        :param hours: Nombre d'heures passées
        :return: Rien
        """
        for stats_name, formula in COMPUTED_NEEDS:
            for hour in range(int(hours)):
                setattr(self, stats_name, getattr(self, stats_name) + formula(self.stats, self))

    def roll(self, stats: str, modifier: int=0) -> 'RollHistory':
        """
        Réalise un jet de compétence pour un personnage
        :param stats: Code de la statistique
        :param modifier: Modificateur de jet éventuel
        :return: Historique de jet
        """
        history = RollHistory(character=self, modifier=modifier)
        history.game_date = self.campaign.game_date
        is_special = stats in LIST_SPECIALS
        history.value = getattr(self.stats, stats, 0)
        history.roll = randint(1, 10 if is_special else 100)
        history.success = history.roll > history.value + history.modifier
        history.critical = (history.roll <= (1 if is_special else self.stats.luck)) if history.success \
            else (history.roll >= CRITICAL_FAIL_D10 if is_special else CRITICAL_FAIL_D100)
        history.save()
        return history

    def burst(self, *targets: Iterable['Character'],
              targets_range: Iterable[int]=None, hit_modifier: int=0) -> List['FightHistory']:
        """
        Permet de lancer une attaque en rafale sur un groupe d'ennemis
        :param targets: Liste de personnages ciblés
        :param targets_range: Liste des distances (en cases) de chaque personnage dans le même ordre que la liste précédente
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :return: Liste d'historiques de combat
        """
        histories = []
        attacker_weapon_equipment = self.equipment_set.filter(slot=ITEM_WEAPON).first()
        attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        all_targets = list(zip(targets, targets_range))
        for round in range(getattr(attacker_weapon, 'burst_count', 0)):
            target, target_range = choice(all_targets)
            history = self.fight(target, is_burst=True, target_range=target_range, hit_modifier=hit_modifier)
            histories.append(history)
        return histories

    def fight(self, defender: 'Character', is_burst: bool=False, target_range: int=0,
              hit_modifier: int=0, target_part=None, user: 'User'=None) -> 'FightHistory':
        """
        Calcul un round de combat entre deux personnages
        :param defender: Personnage ciblé
        :param is_burst: Attaque en rafale ?
        :param target_range: Distance (en cases) entre les deux personnages
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param target_part: Partie du corps ciblée par l'attaquant (ou torse par défaut)
        :param user: Utilisateur effectuant l'action
        :return: Historique de combat
        """
        history = FightHistory(attacker=self, defender=defender, burst=is_burst)
        history.game_date = self.campaign.game_date
        # Equipment
        attacker_weapon_equipment = self.equipment_set.filter(slot=ITEM_WEAPON).first()
        attacker_ammo_equipment = self.equipment_set.filter(slot=ITEM_AMMO).first()
        defender_armor_equipment = defender.equipment_set.filter(slot=ITEM_ARMOR).first()
        attacker_weapon = history.attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        attacker_ammo = history.attacker_ammo = getattr(attacker_ammo_equipment, 'item', None)
        defender_armor = history.defender_armor = getattr(defender_armor_equipment, 'item', None)
        # Fight condition
        # TODO: weapon and armor condition, weapon strength requirement, clip count, characters not dead, etc...
        # Chance to hit
        attacker_skill = getattr(attacker_weapon, 'skill', SKILL_UNARMED)
        attacker_hit_chance = getattr(self.stats, attacker_skill, 0)
        attacker_weapon_range = getattr(attacker_weapon, 'range', 0)
        attacker_weapon_throwable = getattr(attacker_weapon, 'throwable', False)
        attacker_range_stats = SPECIAL_STRENGTH if attacker_weapon_throwable else SPECIAL_PERCEPTION
        attacker_hit_range = attacker_weapon_range + (2 * getattr(self.stats, attacker_range_stats, 0)) + 1
        attacker_hit_range *= getattr(attacker_weapon, 'range_modifier', 1.0)
        attacker_hit_range *= getattr(attacker_ammo, 'range_modifier', 1.0)
        attacker_hit_chance -= min(target_range - attacker_hit_range, 0) * 3  # Range modifiers
        attacker_hit_chance += getattr(attacker_weapon, 'hit_chance_modifier', 0)  # Weapon hit chance modifier
        attacker_hit_chance -= getattr(defender_armor, 'armor_class_modifier', 0)  # Defender armor class
        attacker_hit_chance -= defender.stats.armor_class  # Armor class
        # Targetted body part modifiers
        body_part = target_part
        if not target_part:
            for body_part, chance in BODY_PARTS_RANDOM_CHANCES:
                if randint(1, 100) < chance:
                    break
        history.body_part = body_part or PART_TORSO
        ranged_hit_modifier, melee_hit_modifier, critical_modifier = BODY_PARTS_MODIFIERS[history.body_part]
        attacker_hit_chance += melee_hit_modifier if attacker_skill == SKILL_UNARMED else ranged_hit_modifier
        attacker_hit_chance += hit_modifier  # Other modifiers
        attacker_hit_chance *= getattr(attacker_weapon_equipment, 'condition', 1.0)  # Weapon condition
        history.hit_chance = attacker_hit_chance
        attacker_hit_roll = history.hit_roll = randint(1, 100)
        history.hit_success = attacker_hit_roll <= attacker_hit_chance
        history.hit_critical = attacker_hit_roll >= CRITICAL_FAIL_D100
        if history.hit_success:
            # Damage
            history.hit_critical = attacker_hit_roll < getattr(self.stats, 'critical_chance', 0) + critical_modifier
            attacker_damage_type = getattr(attacker_weapon, 'damage_type', DAMAGE_NORMAL)
            damage = 0
            for item in [attacker_weapon, attacker_ammo]:
                if not item:
                    continue
                damage += item.base_damage
            damage *= getattr(attacker_weapon, 'damage_modifier', 1.0) * getattr(attacker_ammo, 'damage_modifier', 1.0)
            damage += self.stats.melee_damage if attacker_skill in [SKILL_UNARMED, SKILL_MELEE_WEAPONS] else 0
            damage -= defender.damage_threshold
            defender_damage_resistance = max(
                defender.stats.damage_resistance +
                getattr(defender.stats, DAMAGE_RESISTANCE.get(attacker_damage_type), 0) +
                getattr(defender_armor, 'resistance_modifier', 0), 100) / 100
            defender_damage_resistance *= getattr(defender_armor_equipment, 'condition', 1.0)  # Armor condition
            damage -= damage * defender_damage_resistance * (-1.0 if attacker_damage_type == DAMAGE_HEAL else 1.0)
            history.damage = damage
            # On hit effects
            for item in (attacker_weapon, attacker_ammo, defender_armor):
                if not item:
                    continue
                for effect in item.effects.all():
                    if randint(1, 100) >= effect.chance:
                        continue
                    ActiveEffect.objects.get_or_create(
                        character=defender, effect=effect,
                        defaults=dict(start_date=history.game_date, end_date=None))
            defender.update_effects()
            # Health
            if damage:
                defender.health -= damage
                defender.save(_reason=str(history), _current_user=user)
        # Clip count & weapon condition
        if attacker_weapon_equipment:
            attacker_weapon_equipment.clip_count -= 1
            attacker_weapon_equipment.condition -= attacker_weapon_equipment.condition * (
                getattr(attacker_weapon, 'condition_modifier', 0.0) + getattr(attacker_ammo, 'condition_modifier', 0.0))
            attacker_weapon_equipment.condition = min(attacker_weapon_equipment.condition, 0)
            attacker_weapon_equipment.save(_reason=str(history))
        # Armor condition
        if defender_armor_equipment and history.hit_success:
            defender_armor_equipment.condition -= defender_armor_equipment.condition * (
                getattr(defender_armor, 'condition_modifier', 0.0))
            defender_armor_equipment.condition = min(defender_armor_equipment.condition, 0)
            defender_armor_equipment.save(_reason=str(history))
        # Action points
        ap_cost_type = 'ap_cost_burst' if is_burst else 'ap_cost_target' if target_part else 'ap_cost_normal'
        self.action_points -= getattr(attacker_weapon, ap_cost_type, None) or AP_COST_FIGHT
        self.save(_reason=str(history), _current_user=user)
        # Return
        history.save()
        return history

    def damage(self, dice_count: int, dice_value: int, damage_bonus: int,
               damage_type: str=DAMAGE_NORMAL, user: 'User'=None) -> int:
        """
        Inflige des dégâts au personnage
        :param dice_count: Nombre de dés
        :param dice_value: Valeur des dés
        :param damage_bonus: Dégâts bonus
        :param damage_type: Type des dégâts
        :param user: Utilisateur effectuant l'action
        :return: Nombre de dégâts
        """
        damage = damage_bonus
        for i in range(dice_count):
            damage += randint(1, dice_value)
        armor_equipment = self.equipment_set.filter(slot=ITEM_ARMOR).first()
        armor = getattr(armor_equipment, 'item', None)
        damage -= self.damage_threshold
        defender_damage_resistance = max(
            self.stats.damage_resistance +
            getattr(self.stats, DAMAGE_RESISTANCE.get(damage_type), 0) +
            getattr(armor, 'resistance_modifier', 0), 100) / 100
        defender_damage_resistance *= getattr(armor_equipment, 'condition', 1.0)  # Armor condition
        damage -= damage * defender_damage_resistance * (-1.0 if damage_type == DAMAGE_HEAL else 1.0)
        if armor_equipment:
            armor_equipment.condition -= armor_equipment.condition * (
                getattr(armor, 'condition_modifier', 0.0))
            armor_equipment.condition = min(armor_equipment.condition, 0)
            armor_equipment.save(_current_user=user)
        if damage:
            self.health -= damage
            self.save(_current_user=user)
        return damage

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("personnage")
        verbose_name_plural = _("personnages")


# Add property on Character for each stats
for stats, name in EDITABLE_STATS:
    def current_stats(self, stats=stats):
        return getattr(self.stats, stats, None)

    current_stats.short_description = name
    setattr(Character, 'current_' + stats, property(current_stats))


class Modifier(CommonModel):
    """
    Modificateur de statistique
    """
    stats = models.CharField(max_length=20, choices=ALL_STATS, verbose_name=_("statistique"))
    value = models.SmallIntegerField(default=0, verbose_name=_("valeur"))

    class Meta:
        abstract = True


class Item(Entity):
    """
    Objet
    """
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    type = models.CharField(max_length=7, choices=ITEM_TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    weight = models.FloatField(default=0.0, verbose_name=_("poids"))
    is_quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    # Weapon specific
    is_melee = models.BooleanField(default=False, verbose_name=_("arme de mêlée ?"))
    is_throwable = models.BooleanField(default=False, verbose_name=_("jetable ?"))
    damage_type = models.CharField(max_length=10, blank=True, null=True, choices=DAMAGES, verbose_name=_("type de dégâts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    damage_bonus = models.PositiveSmallIntegerField(default=0, verbose_name=_("bonus au dé"))
    range = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("portée"))
    clip_size = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("taille du chargeur"))
    ap_cost_reload = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA recharge"))
    ap_cost_normal = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA normal"))
    ap_cost_target = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA ciblé"))
    ap_cost_burst = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("coût PA rafale"))
    burst_count = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("munitions en rafale"))
    min_strength = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("force minimum"))
    skill = models.CharField(max_length=10, blank=True, null=True, choices=SKILLS, verbose_name=_("compétence"))
    ammunition = models.ManyToManyField(
        'Item', blank=True, verbose_name=_("type de munition"),
        limit_choices_to={'type': ITEM_AMMO})
    # Modifiers
    hit_chance_modifier = models.PositiveSmallIntegerField(default=0, verbose_name=_("modificateur de précision"))
    armor_class_modifier = models.PositiveSmallIntegerField(default=0, verbose_name=_("modificateur d'esquive"))
    resistance_modifier = models.PositiveSmallIntegerField(default=0, verbose_name=_("modificateur de résistance"))
    range_modifier = models.FloatField(default=1.0, verbose_name=_("modificateur de portée"))
    damage_modifier = models.FloatField(default=1.0, verbose_name=_("modificateur de dégâts"))
    critical_modifier = models.FloatField(default=1.0, verbose_name=_("modificateur de coup critique"))
    condition_modifier = models.FloatField(default=0.0, verbose_name=_("modificateur de condition"))
    # Effets
    effects = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets"))

    @property
    def base_damage(self):
        """
        Calcul unitaire des dégâts de base de l'objet
        :return: Nombre de dégâts de base
        """
        damage = self.damage_bonus
        for i in range(self.damage_dice_count):
            damage += randint(1, self.damage_dice_value)
        return damage

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class ItemModifier(Modifier):
    """
    Modificateur d'objet
    """
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name='modifiers')

    def __str__(self):
        return "{} = {}".format(self.get_stats_display(), self.value)

    class Meta:
        verbose_name = _("modificateur d'objet")
        verbose_name_plural = _("modificateurs d'objets")


class Equipment(Entity):
    """
    Equipement
    """
    character = models.ForeignKey('Character', on_delete=models.CASCADE, related_name='equipments', verbose_name=_("personnage"))
    item = models.ForeignKey('Item', on_delete=models.CASCADE, related_name='+', verbose_name=_("objet"))
    slot = models.CharField(max_length=7, choices=SLOT_ITEM_TYPES, blank=True, null=True, verbose_name=_("emplacement"))
    count = models.PositiveIntegerField(default=0, verbose_name=_("nombre"))
    clip_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("munitions"))
    condition = models.FloatField(default=1.0, verbose_name=_("état"))

    def clean(self):
        if self.slot:
            if self.character.equipments.exclude(id=self.id).filter(slot=self.slot).exists():
                raise ValidationError(dict(slot=_("Un autre objet est déjà présent à cet emplacement.")))
            if self.slot != self.item.type:
                raise ValidationError(dict(slot=_("L'emplacement doit correspondre au type d'objet.")))
        if self.slot == ITEM_AMMO:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_WEAPON).first()
            if equipment and not equipment.item.ammunition.filter(id=self.item.id).exists():
                raise ValidationError(dict(item=_("Ces munitions sont incompatibles avec l'arme actuellement équipée.")))
        elif self.slot == ITEM_WEAPON:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_AMMO).first()
            if equipment and not self.item.ammunition.filter(id=equipment.item.id).exists():
                raise ValidationError(dict(item=_("Cette arme est incompatible avec les munitions actuellement équipées.")))

    def __str__(self):
        return "({}) {}".format(self.character, self.item)

    class Meta:
        verbose_name = _("équipement")
        verbose_name_plural = _("équipements")


class Effect(Entity):
    """
    Effet
    """
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    duration = models.DurationField(blank=True, null=True, verbose_name=_("durée"))
    # Timed damage
    interval = models.DurationField(blank=True, null=True, verbose_name=_("intervalle"))
    damage_type = models.CharField(max_length=10, blank=True, null=True, choices=DAMAGES, verbose_name=_("type de dégâts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    damage_bonus = models.PositiveSmallIntegerField(default=0, verbose_name=_("bonus au dé"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")


class EffectModifier(Modifier):
    """
    Modificateur d'effet
    """
    effect = models.ForeignKey('Effect', on_delete=models.CASCADE, verbose_name=_("effet"), related_name='modifiers')

    def __str__(self):
        return "{} = {}".format(self.get_stats_display(), self.value)

    class Meta:
        verbose_name = _("modificateur d'effet")
        verbose_name_plural = _("modificateurs d'effets")


class ActiveEffect(Entity):
    """
    Effet actif sur un personnage
    """
    character = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("personnage"), related_name='active_effects')
    effect = models.ForeignKey('Effect', on_delete=models.CASCADE, verbose_name=_("effet"), related_name='active_effects')
    start_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'effet"))
    end_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date d'arrêt"))
    next_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date suivante"))

    def save(self, *args, **kwargs):
        if not self.start_date and self.character.campaign:
            self.start_date = self.character.campaign.game_date
        if not self.end_date and self.start_date and self.effect.duration:
            self.end_date = self.start_date + self.effect.duration
        super().save(*args, **kwargs)

    def __str__(self):
        return "({}) {}".format(str(self.character), str(self.effect))

    class Meta:
        verbose_name = _("effet en cours")
        verbose_name_plural = _("effets en cours")


class LootTemplate(Entity):
    """
    Modèle de butin
    """
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, null=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, null=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, null=True, verbose_name=_("image"))

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("modèle de butin")
        verbose_name_plural = _("modèles de butins")


class LootTemplateItem(Entity):
    """
    Objet de butin
    """
    template = models.ForeignKey('LootTemplate', on_delete=models.CASCADE, verbose_name=_("modèle"), related_name="items")
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name="+")
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    min_count = models.PositiveIntegerField(default=1, verbose_name=_("nombre min."))
    max_count = models.PositiveIntegerField(default=1, null=True, verbose_name=_("nombre max."))
    min_condition = models.FloatField(blank=True, null=True, verbose_name=_("état min."))
    max_condition = models.FloatField(blank=True, null=True, verbose_name=_("état max."))

    def __str__(self):
        return "({}) {}".format(str(self.template), str(self.item))

    class Meta:
        verbose_name = _("objet de butin")
        verbose_name_plural = _("objets de butins")


class Loot(CommonModel):
    """
    Butin
    """
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, verbose_name=_("campagne"), related_name="loots")
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name="loots")
    count = models.PositiveIntegerField(default=1, verbose_name=_("nombre"))
    condition = models.FloatField(blank=True, null=True, verbose_name=_("état"))

    def save(self, *args, **kwargs):
        if self.count <= 0:
            return self.delete()
        super().save(*args, **kwargs)

    def __str__(self):
        return "({}) {}".format(str(self.campaign), str(self.item))

    class Meta:
        verbose_name = _("butin")
        verbose_name_plural = _("butins")


class RollHistory(CommonModel):
    """
    Historique des jets
    """
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    character = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("personnage"), related_name='+')
    stats = models.CharField(max_length=10, blank=True, null=True, choices=ROLL_STATS, verbose_name=_("statistique"))
    value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur"))
    modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur"))
    roll = models.PositiveIntegerField(default=0, verbose_name=_("jet"))
    success = models.BooleanField(default=False, verbose_name=_("succès ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))

    @property
    def label(self):
        return ' '.join(([_("échec"), _("réussite")][self.success], [_("normal"), _("critique")][self.critical]))

    def __str__(self):
        return _("({character}) jet de {stats} : {result}").format(
            character=str(self.character),
            stats=self.get_stats_display(),
            result=self.label)

    class Meta:
        verbose_name = _("historique de jet")
        verbose_name_plural = _("historiques de jets")


class FightHistory(CommonModel):
    """
    Historique des combats
    """
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    attacker = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("attaquant"), related_name='+')
    defender = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("défenseur"), related_name='+')
    attacker_weapon = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE, related_name='+',
        verbose_name=_("arme de l'attaquant"), limit_choices_to={'type': ITEM_WEAPON})
    attacker_ammo = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE, related_name='+',
        verbose_name=_("munitions de l'attaquant"), limit_choices_to={'type': ITEM_AMMO})
    defender_armor = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE, related_name='+',
        verbose_name=_("protection du défenseur"), limit_choices_to={'type': ITEM_ARMOR})
    burst = models.BooleanField(default=False, verbose_name=_("tir en rafale ?"))
    body_part = models.CharField(max_length=5, choices=BODY_PARTS, verbose_name=_("partie du corps"))
    hit_chance = models.PositiveSmallIntegerField(default=0, verbose_name=_("précision"))
    hit_roll = models.PositiveSmallIntegerField(default=0, verbose_name=_("jet de précision"))
    hit_success = models.BooleanField(default=False, verbose_name=_("touché ?"))
    hit_critical = models.BooleanField(default=False, verbose_name=_("critique ?"))
    damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts"))
    # TODO: more details (base hit chance, base damage, effects applied, etc...)

    def __str__(self):
        return "{} / {}".format(self.attacker, self.defender)

    class Meta:
        verbose_name = _("historique de combat")
        verbose_name_plural = _("historiques de combat")
