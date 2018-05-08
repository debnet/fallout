# coding: utf-8
from common.utils import render_to
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from rpg.fallout.enums import BODY_PARTS, DAMAGES_TYPES, ROLL_STATS
from rpg.fallout.models import (
    Campaign, Character, CampaignEffect, CharacterEffect, Effect,
    Equipment, Item, Loot, LootTemplate, RollHistory)


@login_required
def view_index(request):
    """
    Page d'accueil
    """
    return view_campaign(request, 0)


@login_required
@render_to('fallout/campaign/campaign.html')
def view_campaign(request, campaign_id):
    """
    Vue principale des campagnes
    """
    data = request.POST
    # Campagne
    campaign = Campaign.objects.filter(id=campaign_id).first()
    characters = Character.objects.filter(campaign=campaign, is_active=True)
    if not request.user.is_superuser:
        characters = characters.filter(Q(user=request.user) | Q(campaign__game_master=request.user))
    loots = Loot.objects.select_related('item').filter(campaign=campaign).order_by('item__name')
    # Actions
    authorized = request.user and (request.user.is_superuser or (
        campaign and campaign.game_master_id == request.user.id))
    if request.method == 'POST' and authorized:
        try:
            type = data.get('type')
            method = data.get('method')
            if type == 'loot':
                if method == 'open':
                    loot_id, loot_name = data.get('loot-id'), data.get('loot-name')
                    character_id = data.get('character-id') or None
                    filter = dict(pk=loot_id) if loot_id else dict(name__icontains=loot_name)
                    LootTemplate.objects.filter(**filter).first().create(campaign, character_id)
                elif method == 'add':
                    item_id, item_name = data.get('item-id'), data.get('item-name')
                    quantity = int(data.get('quantity') or 1)
                    condition = int(data.get('condition') or 100) / 100.0
                    filter = dict(pk=item_id) if item_id else dict(name__icontains=item_name)
                    item = Item.objects.filter(**filter).first()
                    Loot.create(campaign=campaign, item=item, quantity=quantity, condition=condition)
                elif method == 'clear':
                    Loot.objects.filter(campaign=campaign).delete()
                elif method.startswith('delete'):
                    method, loot_id = method.split('-')
                    quantity = int(data.get(f'quantity-{loot_id}') or 0)
                    if quantity:
                        loot = Loot.objects.filter(pk=loot_id).first()
                        loot.quantity -= quantity
                        loot.save()
                elif method.startswith('take'):
                    method, loot_id = method.split('-')
                    character = int(data.get('character') or 0)
                    quantity = int(data.get(f'quantity-{loot_id}') or 0)
                    if quantity:
                        loot = Loot.objects.filter(pk=loot_id).first()
                        loot.take(character, quantity)
            elif type == 'effect':
                effect_id, effect_name = data.get('effect-id'), data.get('effect-name')
                if method == 'add':
                    filter = dict(pk=effect_id) if effect_id else dict(name__icontains=effect_name)
                    Effect.objects.filter(**filter).first().affect(campaign)
            elif type == 'radiation':
                if method == 'set':
                    radiation = int(data.get('radiation') or 0)
                    campaign.radiation = radiation
                    campaign.save()
            elif type == 'time':
                if method == 'add':
                    hours, minutes = int(data.get('hours') or 0), int(data.get('minutes') or 0)
                    campaign.next_turn(seconds=hours * 3600 + minutes * 60, reset=True)
            elif type == 'roll':
                group, stats, modifier, xp = (
                    data.get('group'), data.get('stats'), int(data.get('modifier') or 0), 'xp' in data)
                filter = dict(is_player=(group == 'pj')) if group else dict()
                for character in Character.objects.filter(is_active=True, **filter):
                    result = character.roll(stats=stats, modifier=modifier, xp=xp)
                    messages.add_message(request, result.message_level, _(
                        f"<strong>{result.character}</strong> {result.long_label}"))
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                for error in (errors if isinstance(errors, list) else [errors]):
                    messages.error(request, _(f"<strong>Erreur</strong> {error}"))
        except Exception as error:
            messages.error(request, _(f"<strong>Erreur</strong> {error}"))

    return {
        'authorized': authorized,
        'campaigns': Campaign.objects.exclude(id=campaign_id).order_by('name'),
        'characters': characters.order_by('name'),
        'campaign': campaign,
        'loots': loots,
        # Enums
        'stats': ROLL_STATS,
    }


@login_required
@render_to('fallout/character/character.html')
def view_character(request, character_id):
    """
    Vue principale des personnages
    """
    data = request.POST
    # Personnage
    characters = Character.objects.select_related('user', 'campaign').filter(is_active=True).order_by('is_player')
    if not request.user.is_superuser:
        characters = characters.filter(Q(user=request.user) | Q(campaign__game_master=request.user))
    character = characters.filter(id=character_id).first()
    # Actions
    authorized = request.user and (request.user.is_superuser or (
        character and character.campaign and character.campaign.game_master_id == request.user.id))
    characters = characters.filter(campaign_id=character.campaign_id if character else None)
    if request.method == 'POST' and character and authorized:
        try:
            type = data.get('type')
            method = data.get('method')
            if type == 'roll':
                result = character.roll(
                    stats=data.get('stats'),
                    modifier=int(data.get('modifier') or 0))
                messages.add_message(request, result.message_level, _(
                    f"<strong>{result.character}</strong> {result.long_label}"))
            elif type == 'fight' and data.get('target'):
                result = character.fight(
                    target=data.get('target'),
                    target_part=data.get('target_part'),
                    target_range=int(data.get('target_range')),
                    hit_modifier=int(data.get('hit_modifier') or 0),
                    action=bool(data.get('action', False)))
                messages.add_message(request, result.message_level, _(
                    f"<strong>{result.attacker} vs {result.defender}</strong> {result.long_label}"))
            elif type == 'burst' and data.get('targets'):
                results = character.burst(
                    targets=zip(data.get('targets') or [], data.get('ranges') or []),
                    hit_modifier=int(data.get('hit_modifier') or 0),
                    action=bool(data.get('action', False)))
                for result in results:
                    messages.add_message(request, result.message_level, _(
                        f"<strong>{result.attacker} vs {result.defender}</strong> {result.long_label}"))
            elif type == 'damage':
                result = character.damage(
                    raw_damage=int(data.get('raw_damage') or 0),
                    min_damage=int(data.get('min_damage') or 0),
                    max_damage=int(data.get('max_damage') or 0),
                    damage_type=int(data.get('damage_type') or 0))
                messages.success(request, _(f"<strong>{result.character}</strong> {result.label}"))
            elif type == 'item':
                item_id, item_name = data.get('item-id'), data.get('item-name')
                if method == 'add':
                    quantity = int(data.get('quantity') or 1)
                    condition = int(data.get('condition') or 100) / 100.0
                    filter = dict(pk=item_id) if item_id else dict(name__icontains=item_name)
                    equip = Item.objects.filter(**filter).first()
                    equip.give(character=character, quantity=quantity, condition=condition)
                elif method == 'equip':
                    equip = Equipment.objects.filter(pk=item_id).first()
                    equip.equip(action=bool(data.get('action', False)))
                elif method == 'reload':
                    equip = Equipment.objects.filter(pk=item_id).first()
                    equip.reload(action=bool(data.get('action', False)))
                elif method == 'use':
                    equip = Equipment.objects.filter(pk=item_id).first()
                    equip.use(action=bool(data.get('action', False)))
                elif method == 'drop':
                    equip = Equipment.objects.filter(pk=item_id).first()
                    equip.drop(quantity=int(data.get('quantity') or 1), action=bool(data.get('action', False)))
            elif type == 'effect':
                effect_id, effect_name = data.get('effect-id'), data.get('effect-name')
                if method == 'add':
                    filter = dict(pk=effect_id) if effect_id else dict(name__icontains=effect_name)
                    Effect.objects.filter(**filter).first().affect(character)
                elif method == 'remove':
                    scope = data.get('scope')
                    if scope == 'character':
                        CharacterEffect.objects.filter(pk=effect_id).delete()
                    elif scope == 'campaign':
                        CampaignEffect.objects.filter(pk=effect_id).delete()
            elif type == 'action':
                character.health = int(data.get('hp'))
                character.action_points = int(data.get('ap'))
                character.experience = int(data.get('xp'))
                character.karma = int(data.get('karma'))
                character.save()
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                for error in (errors if isinstance(errors, list) else [errors]):
                    messages.error(request, _(f"<strong>Erreur</strong> {error}"))
        except Exception as error:
            messages.error(request, _(f"<strong>Erreur</strong> {error}"))
    # Données
    inventory, effects = character.inventory, character.effects
    rollstats = RollHistory.get_stats(character)

    return {
        'authorized': authorized,
        # Lists
        'campaigns': Campaign.objects.order_by('name'),
        'characters': characters.order_by('name'),
        # Character
        'character': character,
        'inventory': inventory,
        # Effects
        'character_effects': effects,
        'campaign_effects': character.campaign.effects if character.campaign else None,
        # Statistics
        'rollstats': rollstats,
        # Enums
        'body_parts': BODY_PARTS,
        'damage_types': DAMAGES_TYPES,
    }


def next_turn(request, campaign_id):
    """
    Action pour passer au tour suivant
    """
    action = request.method == 'POST'
    data = request.POST
    # Prochain tour
    if action and 'next' in data:
        campaign = Campaign.objects.filter(id=campaign_id).first()
        if campaign and (request.user.is_superuser or campaign.game_master == request.user):
            next_character = campaign.next_turn(seconds=int(data.get('seconds') or 0))
            return redirect('fallout_character', next_character.id)
    return redirect('fallout_campaign', campaign_id)
