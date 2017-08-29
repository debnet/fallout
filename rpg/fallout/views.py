# coding: utf-8
from common.utils import render_to
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import redirect

from rpg.fallout.enums import BODY_PARTS, DAMAGES_TYPES
from rpg.fallout.models import Campaign, Character, RollHistory


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
        characters = characters.filter(user=request.user)

    return {
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
    action = request.method == 'POST'
    data = request.POST
    # Prochain tour
    if action and 'next' in data:
        campaign = Campaign.objects.filter(characters=character_id).first()
        if campaign:
            next_character = campaign.next_turn()
            return redirect('fallout_character', next_character.id)
    # Données
    characters = Character.objects.select_related('user', 'campaign').filter(is_active=True).order_by('is_player')
    if not request.user.is_superuser:
        characters = characters.filter(user=request.user)
    character = characters.filter(id=character_id).first()
    equipment = character.equipments.select_related('item').prefetch_related('item__modifiers').exclude(slot='')
    inventory = character.equipments.select_related('item').prefetch_related('item__modifiers').filter(slot='')
    # Actions
    errors = None
    roll_history = fight_history = damage_history = None
    characters = characters.filter(campaign_id=character.campaign_id if character else None)
    if action and character and request.user.is_superuser:
        try:
            if data.get('type') == 'roll':
                roll_history = character.roll(
                    data.get('stats'),
                    int(data.get('modifier') or 0))
            elif data.get('type') == 'fight':
                fight_history = [character.fight(
                    target=data.get('target'),
                    target_part=data.get('target_part'),
                    target_range=int(data.get('target_range')),
                    hit_modifier=int(data.get('hit_modifier') or 0),
                    action=bool(data.get('action', False)))]
            elif data.get('type') == 'burst':
                fight_history = character.burst(
                    targets=zip(data.get('targets'), data.get('ranges')),
                    hit_modifier=int(data.get('hit_modifier') or 0),
                    action=bool(data.get('action', False)))
            elif data.get('type') == 'damage':
                damage_history = character.damage(
                    raw_damage=int(data.get('raw_damage')),
                    dice_count=int(data.get('dice_count')),
                    dice_value=int(data.get('dice_value')),
                    damage_type=int(data.get('damage_type')))
        except ValidationError as e:
            errors = e.error_list
        except Exception as e:
            errors = [str(e)]
    # Statistics
    rollstats = RollHistory.get_stats(character)

    return {
        # Lists
        'campaigns': Campaign.objects.order_by('name'),
        'characters': characters.exclude(id=character_id).order_by('name'),
        # Character
        'character': character,
        'equipment': equipment,
        'inventory': inventory,
        # Statistics
        'rollstats': rollstats,
        # Action history
        'roll': roll_history,
        'fight': fight_history,
        'damage': damage_history,
        # Enums
        'body_parts': BODY_PARTS,
        'damage_types': DAMAGES_TYPES,
        # Errors
        'errors': errors,
    }
