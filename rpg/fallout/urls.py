# coding: utf-8
from django.conf.urls import url

from rpg.fallout import api, views


urlpatterns = [
    url(r'^character/(?P<pk>\d+)/$', views.character_infos, name='character'),
]

# API REST
router = api.router
api_urlpatterns = [
    # url(_(r'^test/$'), views.test, name='test'),
] + router.urls
