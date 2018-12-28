# coding: utf-8
from common.utils import render_to
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.utils.translation import gettext as _

from fallout.enums import BODY_PARTS, DAMAGES_TYPES, ROLL_STATS
from fallout.models import (
    Campaign, Character, CampaignEffect, CharacterEffect, Effect,
    Equipment, Item, Loot, LootTemplate, RollHistory, FightHistory)


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

    campaign = Campaign.objects.select_related('current_character').filter(id=campaign_id).first()
    characters = Character.objects.select_related('statistics', 'campaign__current_character').filter(
        campaign=campaign, is_active=True)
    if not request.user.is_superuser:
        characters = characters.filter(Q(user=request.user) | Q(campaign__game_master=request.user))
    loots = Loot.objects.select_related('item').filter(campaign=campaign).order_by('item__name')

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
                    hours, minutes, resting = (
                        int(data.get('hours') or 0), int(data.get('minutes') or 0), 'resting' in data)
                    campaign.next_turn(seconds=hours * 3600 + minutes * 60, resting=resting, reset=True)
            elif type == 'roll':
                group, stats, modifier, xp = (
                    data.get('group'), data.get('stats'), int(data.get('modifier') or 0), 'xp' in data)
                filter = dict(is_player=(group == 'pj')) if group else dict()
                for character in characters.filter(is_active=True, **filter):
                    result = character.roll(stats=stats, modifier=modifier, xp=xp)
                    messages.add_message(request, result.message_level, _(
                        "<strong>{character}</strong> {label}").format(
                            character=character, label=result.long_label))
            elif type == 'gain':
                group, experience = (data.get('group'), int(data.get('experience') or 0))
                filter = dict(is_player=(group == 'pj')) if group else dict()
                for character in characters.filter(is_active=True, **filter):
                    old_level = character.level
                    level, required_experience = character.add_experience(experience)
                    if level != old_level:
                        messages.info(request, _(
                            "<strong>{character}</strong> vient de passer au niveau "
                            "<strong>{level}</strong> et a besoin de <strong>{experience}</strong> "
                            "points d'expérience pour passer au niveau suivant.").format(
                                character=character, level=level, experience=required_experience))
                    else:
                        messages.success(request, _(
                            "<strong>{character}</strong> a encore besoin de <strong>{experience}</strong> "
                            "points d'expérience pour passer au niveau suivant.").format(
                                character=character, experience=required_experience))
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                for error in (errors if isinstance(errors, list) else [errors]):
                    messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))
        except Exception as error:
            messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))

    return {
        'authorized': authorized,
        'campaigns': Campaign.objects.order_by('name'),
        'characters': characters.order_by('-is_player', 'name'),
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

    characters = Character.objects.select_related(
        'user', 'statistics', 'campaign__current_character').filter(is_active=True)
    if not request.user.is_superuser:
        characters = characters.filter(Q(user=request.user) | Q(campaign__game_master=request.user))
    character = characters.filter(id=character_id).first()
    if not character:
        raise Http404

    authorized = request.user and (request.user.is_superuser or (
        character and character.campaign and character.campaign.game_master_id == request.user.id))
    characters = characters.filter(campaign_id=character.campaign_id if character else None)
    if request.method == 'POST' and character and authorized:
        try:
            type = data.get('type')
            method = data.get('method')
            if type == 'stats':
                if 'roll' in data:
                    result = character.roll(
                        stats=data.get('roll'),
                        modifier=int(data.get('modifier') or 0))
                    messages.add_message(request, result.message_level, _(
                        "<strong>{character}</strong> {label}").format(
                            character=character, label=result.long_label))
                elif 'levelup' in data:
                    stats = data.get('levelup')
                    character.levelup(stats, 1)
            elif type == 'fight' and data.get('target'):
                result = character.fight(
                    target=data.get('target'),
                    target_part=data.get('target_part'),
                    target_range=int(data.get('target_range')),
                    hit_chance_modifier=int(data.get('hit_modifier') or 0),
                    is_grenade=bool(data.get('is_grenade', False)),
                    is_action=bool(data.get('is_action', False)))
                messages.add_message(request, result.message_level, _(
                    "<strong>{attacker} vs {defender}</strong> {label}").format(
                        attacker=result.attacker, defender=result.defender, label=result.long_label))
            elif type == 'burst' and data.get('targets'):
                histories = character.burst(
                    targets=list(zip(data.getlist('targets') or [], data.getlist('ranges') or [])),
                    hit_chance_modifier=int(data.get('hit_modifier') or 0),
                    is_grenade=bool(data.get('is_grenade', False)),
                    is_action=bool(data.get('is_action', False)))
                results = {}
                for history in histories:
                    results.setdefault(history.defender, dict(attacker=history.attacker, fail=0, success=0, damage=0))
                    results[history.defender]['fail'] += int(history.success is False)
                    results[history.defender]['success'] += int(history.success is True)
                    results[history.defender]['damage'] += history.damage.real_damage if history.damage else 0
                for defender, result in results.items():
                    from django.contrib.messages import constants
                    messages.add_message(request, constants.SUCCESS if result['damage'] else constants.ERROR, _(
                        "<strong>{attacker} vs {defender}</strong> {fail} coups ratés et {success} "
                        "coups au but pour {damage} dégâts").format(defender=defender, **result))
            elif type == 'damage':
                result = character.damage(
                    raw_damage=int(data.get('raw_damage') or 0),
                    min_damage=int(data.get('min_damage') or 0),
                    max_damage=int(data.get('max_damage') or 0),
                    damage_type=str(data.get('damage_type') or None),
                    body_part=str(data.get('body_part') or None))
                messages.success(request, _(
                    "<strong>{character}</strong> {label}").format(
                        character=character, label=result.label))
            elif type == 'item':
                item_id, item_name = data.get('item-id'), data.get('item-name')
                if method == 'add':
                    quantity = int(data.get('quantity') or 1)
                    condition = int(data.get('condition') or 100) / 100.0
                    filter = dict(pk=item_id) if item_id else dict(name__icontains=item_name)
                    equip = Item.objects.filter(**filter).first()
                    equip.give(character=character, quantity=quantity, condition=condition)
                else:
                    is_action = bool(data.get('is_action', False))
                    equip = Equipment.objects.select_related('character', 'item').filter(pk=item_id).first()
                    character = equip.character
                    if method == 'equip':
                        equip.equip(is_action=is_action)
                    elif method == 'reload':
                        equip.reload(is_action=is_action)
                    elif method == 'use':
                        equip.use(is_action=is_action)
                    elif method == 'repair':
                        equip.repair(value=int(data.get('condition') or 100), is_action=is_action)
                    elif method == 'drop':
                        equip.drop(quantity=int(data.get('quantity') or 1), is_action=is_action)
            elif type == 'effect':
                effect_id, effect_name = data.get('effect-id'), data.get('effect-name')
                if method == 'add':
                    filter = dict(pk=effect_id) if effect_id else dict(name__icontains=effect_name)
                    Effect.objects.filter(**filter).first().affect(character)
                elif method == 'remove':
                    scope = data.get('scope')
                    if scope == 'character':
                        CharacterEffect.objects.filter(pk=effect_id).delete()
                        Character.reset_stats(character)
                    elif scope == 'campaign':
                        CampaignEffect.objects.filter(pk=effect_id).delete()
                        Character.reset_stats(character)
            elif type == 'action':
                character.health, character.action_points = int(data.get('hp')), int(data.get('ap'))
                character.experience, character.karma = int(data.get('xp')), int(data.get('karma'))
                character.rads = int(data.get('rads'))
                character.thirst = int(data.get('thirst'))
                character.hunger = int(data.get('hunger'))
                character.sleep = int(data.get('sleep'))
                character.save()
        except ValidationError as error:
            for field, errors in error.message_dict.items():
                for error in (errors if isinstance(errors, list) else [errors]):
                    messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))
        except Exception as error:
            messages.error(request, _("<strong>Erreur</strong> {error}").format(error=error))

    inventory, effects = character.inventory, character.effects
    rollstats = RollHistory.get_stats(character)
    fightstats = FightHistory.get_stats(character)

    return {
        'authorized': authorized,
        # Lists
        'campaigns': Campaign.objects.order_by('name'),
        'characters': characters.order_by('-is_player', 'name'),
        # Character
        'character': character,
        'inventory': inventory,
        # Effects
        'character_effects': effects,
        'campaign_effects': character.campaign.effects if character.campaign else None,
        # Statistics
        'rollstats': rollstats,
        'fightstats': fightstats,
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
            return redirect('fallout:character', next_character.id)
    return redirect('fallout:campaign', campaign_id)


@login_required
@render_to('fallout/thumbnails.html')
def thumbnails(request):
    """
    Affiche les thumbnails d'un répertoire
    """
    import os
    from django.conf import settings
    directory = request.GET.get('dir') or ''
    directories = directory.split(os.sep)
    dirname = os.path.join(settings.MEDIA_ROOT, 'thumbnails', directory)
    images = []
    for filename in os.listdir(dirname):
        filepath = os.path.join(dirname, filename)
        title, ext = os.path.splitext(filename.replace('_', ' '))
        filename = os.path.join(directory, filename)
        if os.path.isdir(filepath):
            images.append((title, True, filename))
        else:
            url = os.path.join('thumbnails', filename).replace('\\', '/')
            images.append((title, False, url))
    return {
        'directories': directories,
        'images': sorted(images, key=lambda e: e[0]),
    }
