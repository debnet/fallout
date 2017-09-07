# coding: utf-8
from django.conf.urls import url

from rpg.fallout import api, views


urlpatterns = [
    url(r'^$', views.view_index, name='fallout_index'),
    url(r'^campaign/(?P<campaign_id>\d+)/$', views.view_campaign, name='fallout_campaign'),
    url(r'^character/(?P<character_id>\d+)/$', views.view_character, name='fallout_character'),
    url(r'^next_turn/(?P<campaign_id>\d+)/$', views.next_turn, name='fallout_next_turn'),
]

# API REST
router = api.router
api_urlpatterns = [
    url(r'^campaign/(?P<campaign_id>\d+)/next/$', api.campaign_next_turn, name='campaign_next_turn'),
    url(r'^campaign/(?P<campaign_id>\d+)/clear/$', api.campaign_clear_loot, name='campaign_clear_loot'),
    url(r'^campaign/(?P<campaign_id>\d+)/roll/$', api.campaign_roll, name='campaign_roll'),
    url(r'^campaign/(?P<campaign_id>\d+)/damage/$', api.campaign_damage, name='campaign_damage'),
    url(r'^character/(?P<character_id>\d+)/roll/$', api.character_roll, name='character_roll'),
    url(r'^character/(?P<character_id>\d+)/fight/$', api.character_fight, name='character_fight'),
    url(r'^character/(?P<character_id>\d+)/burst/$', api.character_burst, name='character_burst'),
    url(r'^character/(?P<character_id>\d+)/damage/$', api.character_damage, name='character_damage'),
    url(r'^equipment/(?P<equipment_id>\d+)/equip/$', api.equipment_equip, name='equipment_equip'),
    url(r'^equipment/(?P<equipment_id>\d+)/use/$', api.equipment_use, name='equipment_use'),
    url(r'^equipment/(?P<equipment_id>\d+)/reload/$', api.equipment_reload, name='equipment_reload'),
    url(r'^equipment/(?P<equipment_id>\d+)/drop/$', api.equipment_drop, name='equipment_drop'),
    url(r'^loot/(?P<loot_id>\d+)/take/$', api.loot_take, name='loot_take'),
] + router.urls
