# coding: utf-8
from common.utils import render_to
from django.shortcuts import get_object_or_404

from rpg.fallout.models import Campaign, Character


def view_index(request):
    return view_campaign(request, 0)


@render_to('fallout/campaign.html')
def view_campaign(request, campaign_id):
    campaign = Campaign.objects.filter(id=campaign_id).first()
    characters = Character.objects.filter(campaign=campaign)
    return {
        'campaigns': Campaign.objects.all(),
        'characters': characters,
        'campaign': campaign,
    }


@render_to('fallout/character.html')
def view_character(request, character_id):
    character = get_object_or_404(Character.objects.select_related(), id=character_id)
    characters = Character.objects.filter(campaign=character.campaign)
    return {
        'campaigns': Campaign.objects.all(),
        'characters': characters,
        'character': character,
    }
