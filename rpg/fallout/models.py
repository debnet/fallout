# coding: utf-8
from datetime import timedelta
from random import randint, choice
from typing import Dict, Iterable, List, Tuple, Union

from common.models import CommonModel, Entity
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q, Sum
from django.utils.translation import ugettext as _

from rpg.fallout.constants import *  # noqa
from rpg.fallout.enums import *  # noqa
from rpg.fallout.fields import MultipleChoiceField


class Campaign(CommonModel):
    """
    Aventure
    """
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='campaign', verbose_name=_("image"))
    start_game_date = models.DateTimeField(verbose_name=_("date de début"))
    current_game_date = models.DateTimeField(verbose_name=_("date courante"))
    current_character = models.ForeignKey(
        'Character', blank=True, null=True, on_delete=models.SET_NULL,
        related_name='+', verbose_name=_("personnage actif"))
    active_effects = models.ManyToManyField(
        'Effect', blank=True,
        related_name='+', verbose_name=_("effets actifs"))
    radiation = models.PositiveSmallIntegerField(default=0, verbose_name=_("rads par heure"))

    def clear_loot(self):
        """
        Supprime les butins non réclamés de la campagne
        """
        return self.loots.all().delete()

    def next_turn(self, apply: bool=True, seconds: int=TURN_TIME):
        """
        Détermine qui est le prochain personnage à agir
        :param apply: Applique directement le changement sur la campagne
        :param seconds: Temps utilisé (en secondes) par le personnage précédent pour son tour de jeu
        :return: Personnage suivant
        """
        next_character = None
        characters = self.characters.filter(is_active=True)
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
        if apply and next_character:
            self.current_game_date += timedelta(seconds=seconds)
            self.current_character = next_character
            self.save()
            # Reset character action points
            self.current_character.action_points = self.current_character.stats.max_action_points
            self.current_character.save()
        return next_character

    def save(self, *args, **kwargs):
        difference = (self._copy.get('current_game_date') or self.current_game_date) - self.current_game_date
        hours = round(difference.seconds / 3600, 2)
        if hours <= 0:
            for character in self.characters.all():
                character.update_needs(hours=hours, radiation=self.radiation)
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('fallout_campaign', args=[str(self.id)])

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
    critical_chance = models.SmallIntegerField(default=0, verbose_name=_("chance de critique"))
    damage_threshold = models.SmallIntegerField(default=0, verbose_name=_("seuil de dégâts"))
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

    def __str__(self):
        return self.character.name

    @staticmethod
    def get(character: 'Character') -> 'Stats':
        stats = Stats()
        stats.character = character
        # Get all character's stats
        for stats_name in LIST_EDITABLE_STATS:
            setattr(stats, stats_name, getattr(character, stats_name, 0))
        # Racial modifiers
        stats._change_all_stats(**RACES_STATS.get(character.race, {}))
        # Tag skills
        for skill in set(character.tag_skills):
            stats._change_stats(skill, TAG_SKILL_BONUS)
        # Survival modifiers
        for stats_name, survival in SURVIVAL_EFFECTS:
            for (mini, maxi), effects in survival.items():
                if (mini or 0) <= getattr(character, stats_name, 0) < (maxi or float('+inf')):
                    stats._change_all_stats(**effects)
        # Equipment modifiers
        for equipment in character.equipments.filter(slot__isnull=False)\
                .select_related('item').prefetch_related('item__modifiers').all():
            for modifier in equipment.item.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Active effects modifiers
        for effect in character.active_effects.select_related('effect').prefetch_related('effect__modifiers').filter(
                Q(start_date__isnull=True) | Q(start_date__gte=F('character__campaign__current_game_date')),
                Q(end_date__isnull=True) | Q(end_date__lte=F('character__campaign__current_game_date'))):
            for modifier in effect.effect.modifiers.all():
                stats._change_stats(modifier.stats, modifier.value)
        # Campaign effects modifiers
        if character.campaign:
            for effect in character.campaign.active_effects.all():
                for modifier in effect.modifiers.all():
                    stats._change_stats(modifier.stats, modifier.value)
        # Derivated statistics
        for stats_name, formula in COMPUTED_STATS:
            stats._change_stats(stats_name, formula(stats, character))
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
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='character', verbose_name=_("image"))
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
    irradiation = models.FloatField(default=0.0, verbose_name=_("irradiation"))
    dehydration = models.FloatField(default=0.0, verbose_name=_("soif"))
    hunger = models.FloatField(default=0.0, verbose_name=_("faim"))
    sleep = models.FloatField(default=0.0, verbose_name=_("sommeil"))
    regeneration = models.FloatField(default=0.0, verbose_name=_("regénération"))
    # Tag skills
    tag_skills = MultipleChoiceField(max_length=200, choices=SKILLS, blank=True, verbose_name=_("spécialités"))
    # Statistics cache
    _stats = {}

    def get_stats(self, stats, from_stats=True):
        return [(code, label, getattr(self.stats if from_stats else self, code, 0)) for code, label in stats]

    @property
    def special(self):
        return self.get_stats(SPECIALS)

    @property
    def skills(self):
        return self.get_stats(SKILLS)

    @property
    def general_stats(self):
        results = []
        for code, label in GENERAL_STATS:
            lvalue = getattr(self, code, 0)
            rvalue = None
            if code == STATS_HEALTH:
                rvalue = getattr(self.stats, STATS_MAX_HEALTH, 0)
            elif code == STATS_ACTION_POINTS:
                rvalue = getattr(self.stats, STATS_MAX_ACTION_POINTS, 0)
            elif code == STATS_SKILL_POINTS:
                rvalue = lvalue
                lvalue = self.used_skill_points
            elif code == STATS_EXPERIENCE:
                rvalue = sum(l * BASE_XP for l in range(1, self.level + 1))
            elif code in LIST_NEEDS:
                rvalue = 1000
            results.append((code, label, lvalue, rvalue))
        results.append((STATS_CARRY_WEIGHT, _("charge"), self.total_charge, self.stats.carry_weight))
        return results

    @property
    def secondary_stats(self):
        return self.get_stats(SECONDARY_STATS)

    @property
    def resistances(self):
        return self.get_stats(RESISTANCES)

    @property
    def other_stats(self):
        return self.secondary_stats + self.resistances

    @property
    def stats(self) -> Stats:
        stats = Character._stats.get(self.id) or Stats.get(self)
        if self.id:
            Character._stats[self.id] = stats
        return stats

    @property
    def total_charge(self):
        return self.equipments.aggregate(charge=Sum(F('count') * F('item__weight'))).get('charge', 0) or 0

    @property
    def used_skill_points(self):
        return sum(getattr(self, skill) * (0.5 if skill in self.tag_skills else 1) for skill in LIST_SKILLS)

    def modify_value(self, name, value):
        value = getattr(self, name, 0) + value
        setattr(self, name, value)
        return value

    def check_level(self) -> int:
        """
        Vérification du niveau en fonction de l'expérience
        :return: Niveau actuel
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
        return level

    def randomize(self, level: int=None, rate: float=0.0) -> None:
        """
        Randomise les statistiques d'un personnage jusqu'à un certain niveau
        :param level: Niveau du personnage à forcer
        :param rate: Pourcentage des points à répartir sur les compétences ciblées
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
            self.modified(choice(self.tag_skills), 2)
            skill_points -= 1
        # Randomly distribute remaining skill points on other skills
        other_skills = (set(LIST_SKILLS) - self.tag_skills) if rate else LIST_SKILLS
        while skill_points:
            skill = choice(other_skills)
            self.modified(skill, 2 if skill in self.tag_skills else 1)
            skill_points -= 1
        # Reset health and action points to their maximum
        self.health = self.stats.max_health
        self.action_points = self.stats.max_action_points
        # Save the changes
        self.save()

    def update_needs(self, hours: float=0.0, radiation: int=0, save: bool=True) -> None:
        """
        Mise à jour des besoins
        :param hours: Nombre d'heures passées
        :param radiation: Radioactivité actuelle (en rads / heure)
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Rien
        """
        for stats_name, formula in COMPUTED_NEEDS:
            self.modify_value(stats_name, formula(self.stats, self) * hours)
        self.damage(raw_damage=radiation * hours, damage_type=DAMAGE_RADIATION, save=False)
        self.regeneration += self.stats.healing_rate * (hours / 24.0) * (
            HEALING_RATE_RESTING_MULT if self.is_resting else 1.0)
        if save:
            self.save()

    def roll(self, stats: str, modifier: int=0) -> 'RollHistory':
        """
        Réalise un jet de compétence pour un personnage
        :param stats: Code de la statistique
        :param modifier: Modificateur de jet éventuel
        :return: Historique de jet
        """
        history = RollHistory(character=self, stats=stats, modifier=modifier)
        history.game_date = self.campaign and self.campaign.current_game_date
        is_special = stats in LIST_SPECIALS
        history.value = getattr(self.stats, stats, 0)
        history.roll = randint(1, 10 if is_special else 100)
        history.success = history.roll < (history.value + history.modifier)
        history.critical = (history.roll <= (1 if is_special else self.stats.luck)) if history.success \
            else (history.roll >= (CRITICAL_FAIL_D10 if is_special else CRITICAL_FAIL_D100))
        history.save()
        return history

    def loot(self, empty=True):
        """
        Transforme l'équipement de ce personnage en butin
        :param empty: Vide l'inventaire du joueur ?
        :return: Liste des butins
        """
        if not self.campaign:
            return None
        loots = []
        equipements = self.equipments.select_related('item').all()
        for equipement in equipements:
            try:
                assert equipement.item.type not in [ITEM_WEAPON, ITEM_ARMOR]
                loot = Loot.objects.get(campaign=self.campaign, item=equipement.item)
                loot.count += equipement.count
                loot.save()
            except (AssertionError, Loot.DoesNotExist):
                loot = Loot.objects.create(campaign=self.campaign, item=equipement.item, condition=equipement.condition)
            loots.append(loot)
        if empty:
            equipements.delete()
        return loots

    def burst(self, *targets: Iterable['Character'], targets_range: Iterable[int]=None,
              hit_modifier: int=0) -> List['FightHistory']:
        """
        Permet de lancer une attaque en rafale sur un groupe d'ennemis
        :param targets: Liste de personnages ciblés
        :param targets_range: Liste des distances (en cases) de chaque personnage dans le même ordre que la liste précédente
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :return: Liste d'historiques de combat
        """
        histories = []
        attacker_weapon_equipment = self.equipments.filter(slot=ITEM_WEAPON).first()
        attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        all_targets = list(zip(targets, targets_range))
        for hit in range(getattr(attacker_weapon, 'burst_count', 0)):
            target, target_range = choice(all_targets)
            history = self.fight(target, is_burst=True, target_range=target_range, hit_modifier=hit_modifier, hit=hit)
            histories.append(history)
        return histories

    def fight(self, defender: 'Character', is_burst: bool=False, target_range: int=1,
              hit_modifier: int=0, target_part: BODY_PARTS=None, hit: int=0) -> 'FightHistory':
        """
        Calcul un round de combat entre deux personnages
        :param defender: Personnage ciblé
        :param is_burst: Attaque en rafale ?
        :param target_range: Distance (en cases) entre les deux personnages
        :param hit_modifier: Modificateurs complémentaires de précision (lumière, couverture, etc...)
        :param target_part: Partie du corps ciblée par l'attaquant (ou torse par défaut)
        :param hit: Compteur de coups lors d'une attaque en rafale
        :return: Historique de combat
        """
        if isinstance(defender, (int, str)):
            defender = Character.objects.get(pk=str(defender))
        history = FightHistory(attacker=self, defender=defender, burst=is_burst, hit_count=hit + 1, range=target_range)
        history.game_date = self.campaign and self.campaign.current_game_date
        # Equipment
        attacker_weapon_equipment = self.equipments.filter(slot=ITEM_WEAPON).first()
        attacker_ammo_equipment = self.equipments.filter(slot=ITEM_AMMO).first()
        defender_armor_equipment = defender.equipments.filter(slot=ITEM_ARMOR).first()
        attacker_weapon = history.attacker_weapon = getattr(attacker_weapon_equipment, 'item', None)
        attacker_ammo = history.attacker_ammo = getattr(attacker_ammo_equipment, 'item', None)
        defender_armor = history.defender_armor = getattr(defender_armor_equipment, 'item', None)
        # Fight conditions
        if attacker_weapon and attacker_weapon.clip_size and attacker_weapon_equipment.clip_count == 0:
            history.fail = STATUS_NO_MORE_AMMO
        elif defender.health <= 0:
            history.fail = STATUS_TARGET_DEAD
        elif attacker_weapon_equipment and attacker_weapon_equipment.condition <= 0.0:
            history.status = STATUS_WEAPON_BROKEN
        # Action points
        ap_cost = 0
        if not is_burst:
            ap_cost_type = 'ap_cost_target' if target_part else 'ap_cost_normal'
            ap_cost = getattr(attacker_weapon, ap_cost_type, None) or AP_COST_FIGHT
        elif not hit:
            ap_cost = getattr(attacker_weapon, 'ap_cost_burst', None) or AP_COST_FIGHT
        if ap_cost > self.action_points:
            history.status = STATUS_NOT_ENOUGH_AP
        # Premature end of fight
        if history.status:
            history.save()
            return history
        # Chance to hit
        attacker_skill = getattr(attacker_weapon, 'skill', SKILL_UNARMED)
        attacker_hit_chance = getattr(self.stats, attacker_skill, 0)  # Base skill and min strength modifier
        attacker_hit_chance += min(20 * (self.stats.strength - getattr(attacker_weapon, 'min_strength', 0)), 0)
        attacker_weapon_range = getattr(attacker_weapon, 'range', 0)
        attacker_weapon_throwable = getattr(attacker_weapon, 'throwable', False)
        if attacker_skill in [SKILL_UNARMED, SKILL_MELEE_WEAPONS]:
            attacker_hit_range = 1
        else:
            attacker_range_stats = SPECIAL_STRENGTH if attacker_weapon_throwable else SPECIAL_PERCEPTION
            attacker_hit_range = attacker_weapon_range + (2 * getattr(self.stats, attacker_range_stats, 0)) + 1
        attacker_hit_range *= getattr(attacker_weapon, 'range_modifier', 1.0)
        attacker_hit_range *= getattr(attacker_ammo, 'range_modifier', 1.0)
        attacker_hit_chance -= min(target_range - attacker_hit_range, 0) * FIGHT_RANGE_MALUS  # Range modifiers
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
        if target_part:
            attacker_hit_chance += melee_hit_modifier if attacker_skill == SKILL_UNARMED else ranged_hit_modifier
        attacker_hit_chance += hit_modifier  # Other modifiers
        attacker_hit_chance *= getattr(attacker_weapon_equipment, 'condition', 1.0)  # Weapon condition
        # Hit chance is null if attacker is melee/unarmed and target is farther than weapon range
        if target_range - attacker_hit_range > 0 and attacker_skill in [SKILL_UNARMED, SKILL_MELEE_WEAPONS]:
            attacker_hit_chance = 0
        history.hit_modifier = int(hit_modifier)
        history.hit_chance = int(max(attacker_hit_chance, 0))
        history.status = STATUS_HIT_FAILED
        attacker_hit_roll = history.hit_roll = randint(1, 100)
        history.hit_success = attacker_hit_roll <= history.hit_chance
        history.hit_critical = attacker_hit_roll >= CRITICAL_FAIL_D100
        if history.hit_success:
            # Critical chance
            critical_chance = getattr(self.stats, 'critical_chance', 0)
            critical_chance += critical_modifier
            critical_chance *= getattr(attacker_weapon, 'critical_modifier', 1.0)
            critical_chance *= getattr(attacker_ammo, 'critical_modifier', 1.0)
            # Apply damage
            history.status = STATUS_HIT_SUCCEED
            history.hit_critical = attacker_hit_roll < critical_chance
            attacker_damage_type = getattr(attacker_weapon, 'damage_type', DAMAGE_NORMAL)
            damage = 0
            for item in [attacker_weapon, attacker_ammo]:
                if not item:
                    continue
                damage += item.base_damage
            damage += self.stats.melee_damage if attacker_skill in [SKILL_UNARMED, SKILL_MELEE_WEAPONS] else 0
            damage *= getattr(attacker_weapon, 'damage_modifier', 1.0) * getattr(attacker_ammo, 'damage_modifier', 1.0)
            damage *= getattr(attacker_weapon, 'critical_damage', 1.0) * getattr(attacker_ammo, 'critical_damage', 1.0)
            damage *= UNARMED_CRITICAL_DAMAGE if attacker_skill == SKILL_UNARMED else 1.0
            history.damage = defender.damage(raw_damage=damage, damage_type=attacker_damage_type, save=True)
            # On hit effects
            for item in (attacker_weapon, attacker_ammo, defender_armor):
                if not item:
                    continue
                for effect in item.effects.all():
                    if randint(1, 100) >= effect.chance:
                        continue
                    ActiveEffect.objects.get_or_create(
                        character=defender, effect=effect,
                        defaults=dict(start_date=history.game_date))
            defender.apply_effects()  # Apply effects immediatly
        # Clip count & weapon condition
        if attacker_weapon_equipment and attacker_weapon:
            attacker_weapon_equipment.clip_count -= 0 if attacker_weapon.is_melee else 1
            # TODO: weapon condition based on damage
            attacker_weapon_equipment.condition -= attacker_weapon_equipment.condition * (
                getattr(attacker_weapon, 'condition_modifier', 0.0) + getattr(attacker_ammo, 'condition_modifier', 0.0))
            attacker_weapon_equipment.save()
        # Save character and return history
        self.action_points -= ap_cost
        self.save()
        history.save()
        return history

    def damage(self, raw_damage: float=0.0, dice_count: int=0, dice_value: int=0,
               damage_type: str=DAMAGE_NORMAL, save: bool=True) -> int:
        """
        Inflige des dégâts au personnage
        :param raw_damage: Dégâts bruts
        :param dice_count: Nombre de dés
        :param dice_value: Valeur des dés
        :param damage_type: Type des dégâts
        :param save: Sauvegarder les modifications sur le personnage ?
        :return: Nombre de dégâts
        """
        history = DamageHistory(
            character=self, damage_type=damage_type, raw_damage=raw_damage,
            damage_dice_count=dice_count, damage_dice_value=dice_value)
        history.game_date = self.campaign and self.campaign.current_game_date
        # Base damage
        total_damage = raw_damage
        for i in range(dice_count):
            total_damage += randint(1, dice_value)
        base_damage = history.base_damage = total_damage
        # Armor threshold and resistance
        armor_equipment = self.equipments.filter(slot=ITEM_ARMOR).first()
        armor = history.armor = getattr(armor_equipment, 'item', None)
        armor_damage = 0
        if armor and armor_equipment:
            armor_threshold = armor.get_threshold(damage_type)
            total_damage -= armor_threshold  # Armor damage threshold
            armor_resistance = armor.get_resistance(damage_type) * armor_equipment.condition
            total_damage *= armor_resistance * armor.resistance_modifier
            armor_damage = max((base_damage - total_damage) * (getattr(armor, 'condition_modifier', 0.0)), 0)
            # History
            history.armor_threshold = armor_threshold
            history.armor_resistance = armor_resistance
            history.armor_damage = armor_damage
        # Self threshold and resistance
        total_damage -= self.stats.damage_threshold
        damage_resistance = self.stats.damage_resistance + getattr(self.stats, DAMAGE_RESISTANCE.get(damage_type), 0.0)
        total_damage -= total_damage * (-1.0 if damage_type == DAMAGE_HEAL else damage_resistance)
        total_damage = int(total_damage)
        # Apply damage on self
        if total_damage:
            if damage_type == DAMAGE_RADIATION:
                self.irradiation += total_damage
            else:
                self.health -= total_damage
            if save:
                self.save()
        # Condition decrease on armor
        if armor_damage > 0 and damage_type in PHYSICAL_DAMAGES:
            armor_equipment.condition -= armor_damage
            armor_equipment.save()
        # History
        history.damage_threshold = self.stats.damage_threshold
        history.damage_resistance = damage_resistance
        history.real_damage = total_damage
        history.save()
        return history

    def apply_effects(self):
        """
        Force l'application des effets en cours
        :return: Rien
        """
        for effect in self.active_effects.all():
            effect.apply()

    def save(self, *args, **kwargs):
        # Regeneration
        if self.regeneration >= 1.0:
            healing = int(self.regeneration)
            self.regeneration -= healing
            self.health = self.health + healing
        # Detect if character is at max health/ap in case of level up or stats modifications
        has_max_health = not self.id or self.health == self.stats.max_health
        has_max_action_points = not self.id or self.action_points == self.stats.max_action_points
        # Check and increase level
        self.check_level()
        # Remove stats in cache
        Character._stats.pop(self.id, None)
        # Fixing health and action points
        self.health = self.stats.max_health if has_max_health else \
            max(0, min(self.health, self.stats.max_health))
        self.action_points = self.stats.max_action_points if has_max_action_points else \
            max(0, min(self.action_points, self.stats.max_action_points))
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('fallout_character', args=[str(self.id)])

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


class Item(Entity):
    """
    Objet
    """
    # General informations
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='item', verbose_name=_("image"))
    type = models.CharField(max_length=7, choices=ITEM_TYPES, verbose_name=_("type"))
    value = models.PositiveIntegerField(default=0, verbose_name=_("valeur"))
    weight = models.FloatField(default=0.0, verbose_name=_("poids"))
    is_quest = models.BooleanField(default=False, verbose_name=_("quête ?"))
    # Weapon specific
    is_melee = models.BooleanField(default=False, verbose_name=_("arme de mêlée ?"))
    is_throwable = models.BooleanField(default=False, verbose_name=_("jetable ?"))
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    range = models.PositiveSmallIntegerField(default=1, verbose_name=_("portée"))
    clip_size = models.PositiveSmallIntegerField(default=0, verbose_name=_("taille du chargeur"))
    ap_cost_reload = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA recharge"))
    ap_cost_normal = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA normal"))
    ap_cost_target = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA ciblé"))
    ap_cost_burst = models.PositiveSmallIntegerField(default=0, verbose_name=_("coût PA rafale"))
    burst_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("munitions en rafale"))
    min_strength = models.PositiveSmallIntegerField(default=0, verbose_name=_("force minimum"))
    skill = models.CharField(max_length=15, blank=True, choices=SKILLS, verbose_name=_("compétence"))
    ammunition = models.ManyToManyField(
        'Item', blank=True, verbose_name=_("type de munition"),
        limit_choices_to={'type': ITEM_AMMO})
    # Modifiers
    hit_chance_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. de précision"))
    armor_class_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. d'esquive"))
    resistance_modifier = models.FloatField(default=1.0, verbose_name=_("modif. de resistance"))
    range_modifier = models.FloatField(default=1.0, verbose_name=_("modif. de portée"))
    damage_modifier = models.FloatField(default=1.0, verbose_name=_("modif. de dégâts"))
    critical_modifier = models.FloatField(default=1.0, verbose_name=_("modif. de coup critique"))
    critical_damage = models.FloatField(default=1.0, verbose_name=_("dégâts critiques"))
    condition_modifier = models.FloatField(default=0.0, verbose_name=_("modif. de condition"))
    # Resistances
    normal_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil normal"))
    normal_resistance = models.FloatField(default=0.0, verbose_name=_("résistance normal"))
    laser_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil laser"))
    laser_resistance = models.FloatField(default=0.0, verbose_name=_("résistance laser"))
    plasma_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil plasma"))
    plasma_resistance = models.FloatField(default=0.0, verbose_name=_("résistance plasma"))
    explosive_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil explosifs"))
    explosive_resistance = models.FloatField(default=0.0, verbose_name=_("résistance explosifs"))
    fire_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil feu"))
    fire_resistance = models.FloatField(default=0.0, verbose_name=_("résistance feu"))
    # Effets
    effects = models.ManyToManyField('Effect', blank=True, related_name='+', verbose_name=_("effets"))

    @property
    def base_damage(self) -> int:
        """
        Calcul unitaire des dégâts de base de l'objet
        :return: Nombre de dégâts de base
        """
        damage = self.raw_damage
        for i in range(self.damage_dice_count):
            damage += randint(1, self.damage_dice_value)
        return damage

    def get_threshold(self, damage_type: str=DAMAGE_NORMAL):
        return getattr(self, damage_type + '_threshold', 0)

    def get_resistance(self, damage_type: str=DAMAGE_NORMAL):
        return getattr(self, damage_type + '_resistance', 0)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("objet")
        verbose_name_plural = _("objets")


class ItemModifier(Modifier):
    """
    Modificateur d'objet
    """
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name='modifiers')

    def __str__(self) -> str:
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
    slot = models.CharField(max_length=7, choices=SLOT_ITEM_TYPES, blank=True, verbose_name=_("emplacement"))
    count = models.PositiveIntegerField(default=1, verbose_name=_("nombre"))
    clip_count = models.PositiveSmallIntegerField(blank=True, null=True, verbose_name=_("munitions"))
    condition = models.FloatField(blank=True, null=True, verbose_name=_("état"))

    @property
    def value(self):
        return self.item.value * self.condition * self.count

    def clean(self):
        if self.slot:
            if self.character.equipments.exclude(id=self.id).filter(slot=self.slot).exists():
                raise ValidationError(dict(slot=_("Un autre objet est déjà présent à cet emplacement.")))
            if self.slot != self.item.type:
                raise ValidationError(dict(slot=_("L'emplacement doit correspondre au type d'objet.")))
        if self.slot == ITEM_AMMO:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_WEAPON).first()
            if equipment and not equipment.item.ammunition.filter(id=self.item.id).exists():
                raise ValidationError(dict(item=_("Ces munitions sont incompatibles avec l'arme équipée.")))
        elif self.slot == ITEM_WEAPON:
            equipment = self.character.equipments.select_related('item').filter(slot=ITEM_AMMO).first()
            if equipment and not self.item.ammunition.filter(id=equipment.item.id).exists():
                raise ValidationError(dict(item=_("Cette arme est incompatible avec les munitions équipées.")))

    def save(self, *args, **kwargs):
        self.condition = max(0.0, min(1.0, self.condition or 1.0)) if self.slot in [ITEM_WEAPON, ITEM_ARMOR] else None
        self.clip_count = max(0, self.clip_count or 0) if self.slot == ITEM_WEAPON and not self.item.is_melee else None
        return super().save(*args, **kwargs)

    def __str__(self) -> str:
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
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='effect', verbose_name=_("image"))
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    duration = models.DurationField(blank=True, null=True, verbose_name=_("durée"))
    # Timed effects
    interval = models.DurationField(blank=True, null=True, verbose_name=_("intervalle"))
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))

    @property
    def base_damage(self) -> int:
        """
        Calcul unitaire des dégâts de base de l'effet
        :return: Nombre de dégâts de base
        """
        damage = self.raw_damage
        for i in range(self.damage_dice_count):
            damage += randint(1, self.damage_dice_value)
        return damage

    @property
    def damage_config(self) -> Dict[str, Union[str, int]]:
        return dict(
            raw_damage=self.raw_damage,
            dice_count=self.damage_dice_count,
            dice_value=self.damage_dice_value,
            damage_type=self.damage_type)

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("effet")
        verbose_name_plural = _("effets")


class EffectModifier(Modifier):
    """
    Modificateur d'effet
    """
    effect = models.ForeignKey('Effect', on_delete=models.CASCADE, verbose_name=_("effet"), related_name='modifiers')

    def __str__(self) -> str:
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

    def apply(self):
        if not self.next_date and self.effect.interval:
            self.next_date = self.start_date
        if not self.character.campaign and not self.next_date:
            return
        game_date = self.character.campaign.current_game_date
        while self.next_date <= game_date:
            self.character.damage(**self.effect.damage_config)
            self.next_date += self.effect.interval
        self.save()

    def save(self, *args, **kwargs):
        if not self.start_date and self.character.campaign:
            self.start_date = self.character.campaign.current_game_date
        if not self.end_date and self.start_date and self.effect.duration:
            self.end_date = self.start_date + self.effect.duration
        if self.character.campaign and self.end_date and self.end_date <= self.character.campaign.current_game_date:
            return self.delete(*args, **kwargs)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return "({}) {}".format(str(self.character), str(self.effect))

    class Meta:
        verbose_name = _("effet en cours")
        verbose_name_plural = _("effets en cours")


class LootTemplate(Entity):
    """
    Modèle de butin
    """
    name = models.CharField(max_length=200, verbose_name=_("nom"))
    title = models.CharField(max_length=200, blank=True, verbose_name=_("titre"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    image = models.ImageField(blank=True, upload_to='loot', verbose_name=_("image"))

    def __str__(self) -> str:
        return self.name

    class Meta:
        verbose_name = _("modèle de butin")
        verbose_name_plural = _("modèles des butins")


class LootTemplateItem(Entity):
    """
    Objet de butin
    """
    template = models.ForeignKey('LootTemplate', on_delete=models.CASCADE, verbose_name=_("modèle"), related_name="items")
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name="+")
    chance = models.PositiveSmallIntegerField(default=100, verbose_name=_("chance"))
    min_count = models.PositiveIntegerField(default=1, verbose_name=_("nombre min."))
    max_count = models.PositiveIntegerField(default=1, null=True, verbose_name=_("nombre max."))
    min_condition = models.FloatField(default=1.0, verbose_name=_("état min."))
    max_condition = models.FloatField(default=1.0, verbose_name=_("état max."))

    def __str__(self) -> str:
        return "({}) {}".format(str(self.template), str(self.item))

    class Meta:
        verbose_name = _("objet de butin")
        verbose_name_plural = _("objets des butins")


class Loot(CommonModel):
    """
    Butin
    """
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, verbose_name=_("campagne"), related_name="loots")
    item = models.ForeignKey('Item', on_delete=models.CASCADE, verbose_name=_("objet"), related_name="loots")
    count = models.PositiveIntegerField(default=1, verbose_name=_("nombre"))
    condition = models.FloatField(default=1.0, verbose_name=_("état"))

    def save(self, *args, **kwargs):
        if self.count <= 0:
            return self.delete(*args, **kwargs)
        super().save(*args, **kwargs)

    def __str__(self) -> str:
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
    stats = models.CharField(max_length=10, blank=True, choices=ROLL_STATS, verbose_name=_("statistique"))
    value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur"))
    modifier = models.SmallIntegerField(default=0, verbose_name=_("modificateur"))
    roll = models.PositiveIntegerField(default=0, verbose_name=_("jet"))
    success = models.BooleanField(default=False, verbose_name=_("succès ?"))
    critical = models.BooleanField(default=False, verbose_name=_("critique ?"))

    @property
    def label(self) -> str:
        return ' '.join((
            [_("échec"), _("réussite")][self.success],
            ['', _("critique")][self.critical])).strip()

    def __str__(self) -> str:
        return _("({character}) jet de {stats} : {result}").format(
            character=str(self.character),
            stats=self.get_stats_display(),
            result=self.label)

    class Meta:
        verbose_name = _("historique de jet")
        verbose_name_plural = _("historiques des jets")


class DamageHistory(CommonModel):
    """
    Historique des dégâts
    """
    date = models.DateTimeField(auto_now_add=True, verbose_name=_("date"))
    game_date = models.DateTimeField(blank=True, null=True, verbose_name=_("date en jeu"))
    character = models.ForeignKey('Character', on_delete=models.CASCADE, verbose_name=_("personnage"), related_name='+')
    damage_type = models.CharField(max_length=10, blank=True, choices=DAMAGES_TYPES, verbose_name=_("type de dégâts"))
    raw_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts bruts"))
    damage_dice_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("nombre de dés"))
    damage_dice_value = models.PositiveSmallIntegerField(default=0, verbose_name=_("valeur de dé"))
    base_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts de base"))
    armor = models.ForeignKey(
        'Item', blank=True, null=True, on_delete=models.CASCADE, related_name='+',
        verbose_name=_("protection"), limit_choices_to={'type': ITEM_ARMOR})
    armor_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil armure"))
    armor_resistance = models.FloatField(default=0.0, verbose_name=_("résistance armure"))
    armor_damage = models.FloatField(default=0.0, verbose_name=_("dégats armure"))
    damage_threshold = models.PositiveSmallIntegerField(default=0, verbose_name=_("seuil dégâts"))
    damage_resistance = models.FloatField(default=0.0, verbose_name=_("résistance dégâts"))
    real_damage = models.PositiveSmallIntegerField(default=0, verbose_name=_("dégâts réels"))

    def __str__(self) -> str:
        return _("({character}) {damage_type} : {damage}").format(
            character=str(self.character),
            damage_type=self.get_damage_type_display(),
            damage=self.real_damage)

    class Meta:
        verbose_name = _("historique de dégâts")
        verbose_name_plural = _("historiques des dégâts")


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
    range = models.PositiveSmallIntegerField(default=0, verbose_name=_("distance"))
    body_part = models.CharField(max_length=5, choices=BODY_PARTS, verbose_name=_("partie du corps"))
    burst = models.BooleanField(default=False, verbose_name=_("tir en rafale ?"))
    hit_count = models.PositiveSmallIntegerField(default=0, verbose_name=_("compteur de coups"))
    hit_modifier = models.SmallIntegerField(default=0, verbose_name=_("modif. de précision"))
    hit_chance = models.SmallIntegerField(default=0, verbose_name=_("précision"))
    hit_roll = models.PositiveSmallIntegerField(default=0, verbose_name=_("jet de précision"))
    hit_success = models.BooleanField(default=False, verbose_name=_("touché ?"))
    hit_critical = models.BooleanField(default=False, verbose_name=_("critique ?"))
    status = models.CharField(max_length=15, choices=FIGHT_STATUS, blank=True, verbose_name=_("status"))
    damage = models.OneToOneField(
        'DamageHistory', blank=True, null=True, on_delete=models.CASCADE, related_name='+',
        verbose_name=_("historique des dégâts"), editable=False)

    def __str__(self) -> str:
        return "{} vs. {}".format(self.attacker, self.defender)

    class Meta:
        verbose_name = _("historique de combat")
        verbose_name_plural = _("historiques des combats")


MODELS = (
    Campaign,
    Character,
    Item,
    ItemModifier,
    Equipment,
    Effect,
    EffectModifier,
    ActiveEffect,
    LootTemplate,
    LootTemplateItem,
    Loot,
    RollHistory,
    DamageHistory,
    FightHistory,
)
