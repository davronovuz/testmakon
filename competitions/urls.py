"""
TestMakon.uz - Competitions URLs
Battles, tournaments, admin competitions
"""

from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    # Competitions list
    path('', views.competitions_list, name='competitions_list'),
    path('competition/<slug:slug>/', views.competition_detail, name='competition_detail'),
    path('competition/<slug:slug>/join/', views.competition_join, name='competition_join'),
    path('competition/<slug:slug>/start/', views.competition_start, name='competition_start'),
    path('competition/<slug:slug>/leaderboard/', views.competition_leaderboard, name='competition_leaderboard'),

    # Battles (1v1)
    path('battles/', views.battles_list, name='battles_list'),
    path('battle/create/', views.battle_create, name='battle_create'),
    path('battle/<uuid:uuid>/', views.battle_detail, name='battle_detail'),
    path('battle/<uuid:uuid>/accept/', views.battle_accept, name='battle_accept'),
    path('battle/<uuid:uuid>/reject/', views.battle_reject, name='battle_reject'),
    path('battle/<uuid:uuid>/play/', views.battle_play, name='battle_play'),
    path('battle/<uuid:uuid>/submit/', views.battle_submit, name='battle_submit'),
    path('battle/<uuid:uuid>/result/', views.battle_result, name='battle_result'),

    # Daily Challenge
    path('daily/', views.daily_challenge, name='daily_challenge'),
    path('daily/start/', views.daily_challenge_start, name='daily_challenge_start'),

    # API
    path('api/battle-status/<uuid:uuid>/', views.api_battle_status, name='api_battle_status'),
    path('api/online-friends/', views.api_online_friends, name='api_online_friends'),
]