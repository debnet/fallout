# coding: utf-8
from datetime import timedelta
from unittest.mock import patch

from django.test import SimpleTestCase
from django.utils.timezone import now

from fallout.enums import DAMAGE_RAW
from fallout.models import CampaignEffect, Character, CharacterEffect, Effect
from fallout.tests.models.base import CoreTestCase


class EffectMetadataTests(SimpleTestCase):
    def test_duration_supports_minimum_maximum_and_random_bounds(self):
        minute = timedelta(minutes=1)
        self.assertIsNone(Effect().duration)
        self.assertEqual(Effect(min_duration=minute).duration, minute)
        self.assertEqual(Effect(max_duration=minute).duration, minute)
        with patch("fallout.models.randint", return_value=90) as random:
            self.assertEqual(Effect(min_duration=minute, max_duration=2 * minute).duration, timedelta(seconds=90))
        random.assert_called_once_with(60, 120)

    def test_progress_is_clamped_before_during_and_after_effect(self):
        start = now()
        for controlled in (False, True):
            effect = CampaignEffect(
                effect=Effect(controlled=controlled), start_date=start, end_date=start + timedelta(minutes=10)
            )
            for minutes, expected in ((-1, (0, 100)), (4, (40, 60)), (11, (100, 0))):
                with self.subTest(controlled=controlled, minutes=minutes):
                    progress = effect.get_progress(start + timedelta(minutes=minutes))
                    self.assertEqual((progress[0][0], progress[1][0]), expected)
                    self.assertEqual(
                        progress[0][2], ("success" if minutes > 10 else "primary") if controlled else "danger"
                    )
                    self.assertEqual(progress[1][2], "dark" if controlled else "success")
        self.assertIsNone(CampaignEffect().get_progress(start))


class ActiveEffectOperationTests(CoreTestCase):
    def test_single_character_application_of_campaign_effect_catches_up(self):
        effect = Effect.objects.create(
            name="Periodic", damage_type=DAMAGE_RAW, raw_damage=5, interval=timedelta(minutes=1), apply=False
        )
        active = effect.affect(self.campaign, force=True)
        active.campaign.current_game_date += timedelta(minutes=2)
        damages = active.apply(self.hero)
        self.hero.refresh_from_db()
        self.target.refresh_from_db()
        self.assertEqual([damage.real_damage for damage in damages], [5, 5])
        self.assertEqual((self.hero.health, self.target.health), (90, 100))
        self.assertEqual(active.next_date, active.campaign.current_game_date + timedelta(minutes=1))
        self.assertEqual(active.apply(self.hero), [])

    def test_campaign_effect_without_damage_configuration_has_nothing_to_apply(self):
        active = Effect.objects.create(name="General").affect(self.campaign, force=True)
        self.assertEqual(active.apply(self.hero), [])

    def test_campaign_effect_respects_chance_unless_forced(self):
        effect = Effect.objects.create(name="Unlikely global", chance=0)
        self.assertIsNone(effect.affect(self.campaign))
        self.assertFalse(CampaignEffect.objects.exists())
        self.assertIsNotNone(effect.affect(self.campaign, force=True))

    def test_interval_longer_than_duration_does_not_trigger_damage(self):
        effect = Effect.objects.create(
            name="Short",
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            apply=False,
            interval=timedelta(minutes=2),
            min_duration=timedelta(minutes=1),
        )
        for target in (self.campaign, self.hero):
            with self.subTest(target=type(target).__name__):
                active = effect.affect(target, force=True)
                self.assertIsNone(active.next_date)
        self.campaign.next_turn(seconds=120, reset=True)
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 100)
        self.assertFalse(CampaignEffect.objects.exists())
        self.assertFalse(CharacterEffect.objects.exists())

    def test_progress_properties_use_campaign_clock(self):
        effect = Effect.objects.create(name="Timed", min_duration=timedelta(minutes=10))
        global_active = effect.affect(self.campaign, force=True)
        individual = effect.affect(self.hero, force=True)
        self.campaign.next_turn(seconds=240, reset=True)
        for model, pk in ((CampaignEffect, global_active.pk), (CharacterEffect, individual.pk)):
            with self.subTest(model=model.__name__):
                active = model.objects.get(pk=pk)
                self.assertEqual(active.progress[0][0], 40)
        detached = CharacterEffect(character=Character(has_stats=False))
        self.assertIsNone(detached.progress)

    def test_controlled_effect_remains_active_after_duration_without_extra_ticks(self):
        effect = Effect.objects.create(
            name="Controlled",
            controlled=True,
            damage_type=DAMAGE_RAW,
            raw_damage=5,
            apply=False,
            interval=timedelta(minutes=1),
            min_duration=timedelta(minutes=2),
        )
        active = effect.affect(self.campaign, force=True)
        self.campaign.next_turn(seconds=300, reset=True)
        active.refresh_from_db()
        self.hero.refresh_from_db()
        self.assertEqual(self.hero.health, 90)
        self.assertEqual(active.progress[0][0], 100)
        self.assertEqual(active.progress[0][2], "success")
