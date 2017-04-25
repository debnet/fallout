# coding: utf-8
from common.utils import render_to
from django.contrib.auth.decorators import login_required

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
        'campaigns': Campaign.objects.all(),
        'characters': characters,
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
            print(data.get('modifier'))
            roll_history = character.roll(data.get('stats'), int(data.get('modifier')))
    return {
        'campaigns': Campaign.objects.all(),
        'characters': characters,
        'character': character,
        'roll': roll_history,
    }
