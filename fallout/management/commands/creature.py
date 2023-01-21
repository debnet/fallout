# coding: utf-8
import re
from dataclasses import dataclass

from django.core.management import BaseCommand
from django.utils.translation import gettext as _

from fallout.models import Character


@dataclass
class Creature:
    name: str
    reward: int
    max_health: int
    healing_rate: int
    armor_class: int
    sequence: int
    max_action_points: int
    melee_damage: int
    critical_chance: int
    normal_threshold: int
    normal_resistance: int
    laser_threshold: int
    laser_resistance: int
    fire_threshold: int
    fire_resistance: int
    plasma_threshold: int
    plasma_resistance: int
    electricity_threshold: int
    electricity_resistance: int
    explosive_threshold: int
    explosive_resistance: int


class Command(BaseCommand):
    help = _("Importe des créatures")
    leave_locale_alone = True

    def handle(self, _all=False, filename=None, *args, **options):
        try:
            while True:
                print(_("Nouvelle créature :"))
                lines = []
                while True:
                    line = input()
                    if not line:
                        break
                    line = line.replace("%", "")
                    line = re.sub(r"-\t", "\n", line)
                    line = re.sub(r"Icon(\s[a-zA-Z]+)+", "", line)
                    line = re.sub(r"\sGametitle-\w+", "", line)
                    if line.strip():
                        lines.extend(line.split("\n"))
                if not lines:
                    break
                lines = [lines[0]] + [int(e) for e in lines[2:-2]]
                creature = Creature(*lines)
                print(creature)
                creature.name = input(_("Nom : ")) or creature.name
                character = Character(
                    race="creature",
                    health=creature.max_health,
                    action_points=creature.max_action_points,
                    is_active=False,
                    has_stats=False,
                    **creature.__dict__
                )
                character.save()
        except KeyboardInterrupt:
            pass
