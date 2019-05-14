# coding: utf-8
from django.urls import path

from fallout import api, views

namespace = 'fallout'
app_name = 'fallout'
urlpatterns = [
    path('', views.view_index, name='index'),
    path('campaign/<int:campaign_id>/', views.view_campaign, name='campaign'),
    path('character/<int:character_id>/', views.view_character, name='character'),
    path('next_turn/<int:campaign_id>/', views.next_turn, name='next_turn'),
    path('thumbnails/', views.thumbnails, name='thumbnails'),
]
