# coding: utf-8
from common.utils import render_to
from django.shortcuts import get_object_or_404

from rpg.fallout.models import Character


@render_to('fallout/character.html')
def character_infos(request, pk):
    character = get_object_or_404(Character, pk=pk)
    return {
        'character': character,
    }
