# coding: utf-8
from django.urls import path

from fallout import api, views


urlpatterns = [
    path(r'', views.view_index, name='fallout_index'),
    path(r'campaign/<int:campaign_id>/', views.view_campaign, name='fallout_campaign'),
    path(r'character/<int:character_id>/', views.view_character, name='fallout_character'),
    path(r'next_turn/<int:campaign_id>/', views.next_turn, name='fallout_next_turn'),
]

# API REST
router = api.router
api_urlpatterns = [
    path(r'campaign/<int:campaign_id>/next/', api.campaign_next_turn, name='campaign_next_turn'),
    path(r'campaign/<int:campaign_id>/clear/', api.campaign_clear_loot, name='campaign_clear_loot'),
    path(r'campaign/<int:campaign_id>/roll/', api.campaign_roll, name='campaign_roll'),
    path(r'campaign/<int:campaign_id>/damage/', api.campaign_damage, name='campaign_damage'),
    path(r'character/<int:character_id>/roll/', api.character_roll, name='character_roll'),
    path(r'character/<int:character_id>/fight/', api.character_fight, name='character_fight'),
    path(r'character/<int:character_id>/burst/', api.character_burst, name='character_burst'),
    path(r'character/<int:character_id>/damage/', api.character_damage, name='character_damage'),
    path(r'equipment/<int:equipment_id>/equip/', api.equipment_equip, name='equipment_equip'),
    path(r'equipment/<int:equipment_id>/use/', api.equipment_use, name='equipment_use'),
    path(r'equipment/<int:equipment_id>/reload/', api.equipment_reload, name='equipment_reload'),
    path(r'equipment/<int:equipment_id>/drop/', api.equipment_drop, name='equipment_drop'),
    path(r'loot/<int:loot_id>/take/', api.loot_take, name='loot_take'),
    path(r'loottemplate/<int:template_id>/open/', api.loottemplate_open, name='loottemplate_open'),
] + router.urls
