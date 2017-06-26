# coding: utf-8
from django.conf.urls import url

from rpg.fallout import api, views


urlpatterns = [
    url(r'^$', views.view_index, name='fallout_index'),
    url(r'^campaign/(?P<campaign_id>\d+)/$', views.view_campaign, name='fallout_campaign'),
    url(r'^character/(?P<character_id>\d+)/$', views.view_character, name='fallout_character'),
]

# API REST
router = api.router
api_urlpatterns = [
    url(r'^campaign/(?P<campaign_id>\d+)/next/$', api.campaign_next_turn, name='campaign_next_turn'),
    url(r'^campaign/(?P<campaign_id>\d+)/clear/$', api.campaign_clear_loot, name='campaign_clear_loot'),
    url(r'^campaign/(?P<campaign_id>\d+)/roll/$', api.campaign_roll, name='campaign_roll'),
    url(r'^character/(?P<character_id>\d+)/roll/$', api.character_roll, name='character_roll'),
    url(r'^character/(?P<character_id>\d+)/fight/$', api.character_fight, name='character_fight'),
    url(r'^character/(?P<character_id>\d+)/burst/$', api.character_burst, name='character_burst'),
] + router.urls
