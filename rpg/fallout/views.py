# coding: utf-8
from common.utils import render_to
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from rpg.fallout.enums import BODY_PARTS, DAMAGES_TYPES
from rpg.fallout.models import Campaign, Character, CharacterEffect, Effect, Equipment, Item, RollHistory


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
    campaign = Campaign.objects.filter(id=campaign_id).first()
    characters = Character.objects.filter(campaign=campaign)
    if not request.user.is_superuser:
        characters = characters.filter(Q(user=request.user) | Q(campaign__game_master=request.user))

    return {
        'authorized': request.user and (request.user.is_superuser or (
            campaign and campaign.game_master_id == request.user.id)),
        'campaigns': Campaign.objects.exclude(id=campaign_id).order_by('name'),
        'characters': characters.order_by('name'),
        'campaign': campaign,
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
    characters = characters.filter(campaign_id=character.campaign_id if character else None)
    if request.method == 'POST' and character and request.user.is_superuser:
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
                    raw_damage=int(data.get('raw_damage')),
                    dice_count=int(data.get('dice_count')),
                    dice_value=int(data.get('dice_value')),
                    damage_type=int(data.get('damage_type')))
                messages.success(request, _(f"<strong>{result.character}</strong> {result.label}"))
            elif type == 'item':
                item = data.get('item', '')
                if method == 'add':
                    quantity = int(data.get('quantity') or 1)
                    condition = int(data.get('condition') or 100) / 100.0
                    filter = dict(pk=item) if item.isdigit() else dict(name__icontains=item)
                    equip = Item.objects.filter(**filter).first()
                    equip.give(character=character, quantity=quantity, condition=condition)
                elif method == 'equip':
                    equip = Equipment.objects.filter(pk=item).first()
                    equip.equip(action=bool(data.get('action', False)))
                elif method == 'reload':
                    equip = Equipment.objects.filter(pk=item).first()
                    equip.reload(action=bool(data.get('action', False)))
                elif method == 'use':
                    equip = Equipment.objects.filter(pk=item).first()
                    equip.use(action=bool(data.get('action', False)))
                elif method == 'drop':
                    equip = Equipment.objects.filter(pk=item).first()
                    equip.drop(quantity=equip.quantity, action=bool(data.get('action', False)))
            elif type == 'effect':
                effect = data.get('effect', '')
                if method == 'add':
                    filter = dict(pk=effect) if effect.isdigit() else dict(name__icontains=effect)
                    effect = Effect.objects.filter(**filter).first().affect(character)
                    messages.success(request, _(f"{effect.effect} appliqué à {character}."))
                elif method == 'remove':
                    CharacterEffect.objects.filter(pk=effect).delete()
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
        'authorized': request.user and (request.user.is_superuser or (
            character and character.campaign and character.campaign.game_master_id == request.user.id)),
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
