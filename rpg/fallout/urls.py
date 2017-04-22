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
    # url(_(r'^test/$'), views.test, name='test'),
] + router.urls
