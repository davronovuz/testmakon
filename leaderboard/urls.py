"""
TestMakon.uz - Leaderboard URLs
"""

from django.urls import path
from . import views

app_name = 'leaderboard'

urlpatterns = [
    # Main leaderboard
    path('', views.leaderboard_main, name='leaderboard_main'),
    path('global/', views.global_leaderboard, name='global_leaderboard'),
    path('weekly/', views.weekly_leaderboard, name='weekly_leaderboard'),
    path('monthly/', views.monthly_leaderboard, name='monthly_leaderboard'),

    # Subject leaderboards
    path('subject/<slug:slug>/', views.subject_leaderboard, name='subject_leaderboard'),

    # Achievements
    path('achievements/', views.achievements_list, name='achievements_list'),
    path('achievements/<slug:slug>/', views.achievement_detail, name='achievement_detail'),

    # My stats
    path('my-stats/', views.my_stats, name='my_stats'),

    # Seasons
    path('season/', views.current_season, name='current_season'),
    path('season/<slug:slug>/', views.season_detail, name='season_detail'),

    # Friends
    path('friends/', views.friends_leaderboard, name='friends_leaderboard'),

    # API
    path('api/my-rank/', views.api_my_rank, name='api_my_rank'),
    path('api/top-users/', views.api_top_users, name='api_top_users'),
]