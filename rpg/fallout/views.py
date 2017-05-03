# coding: utf-8
from common.utils import render_to
from django.contrib.auth.decorators import login_required

from rpg.fallout.enums import BODY_PARTS, DAMAGES_TYPES
from rpg.fallout.models import Campaign, Character


@login_required
def view_index(request):
    return view_campaign(request, 0)


@login_required
@render_to('fallout/campaign.html')
def view_campaign(request, campaign_id):
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
@render_to('fallout/character.html')
def view_character(request, character_id):
    characters = Character.objects.select_related()
    if not request.user.is_superuser:
        characters = characters.filter(user=request.user)
    character = characters.filter(id=character_id).first()
    # Actions
    roll_history = None
    characters = characters.filter(campaign_id=character.campaign_id if character else None)
    if character and request.user.is_superuser and request.method == 'POST':
        data = request.POST
        if data.get('type') == 'roll':
            roll_history = character.roll(data.get('stats'), int(data.get('modifier')))
        elif data.get('type') in ['fight', 'burst']:
            print(data)  # TODO: for testing purpose only
        elif data.get('type') == 'damage':
            print(data)  # TODO: for testing purpose only
    return {
        'campaigns': Campaign.objects.order_by('name'),
        'characters': characters.exclude(id=character_id).order_by('name'),
        'character': character,
        # History
        'roll': roll_history,
        'fight': None,
        'damage': None,
        # Enums
        'body_parts': BODY_PARTS,
        'damage_types': DAMAGES_TYPES,
    }
