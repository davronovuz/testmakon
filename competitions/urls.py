"""
TestMakon.uz - Competitions URLs (Fixed Order)
"""

from django.urls import path
from . import views

app_name = 'competitions'

urlpatterns = [
    # 1. ASOSIY RO'YXAT
    path('', views.competitions_list, name='competitions_list'),

    # 2. BATTLES (Static qismlar)
    path('battles/', views.battles_list, name='battles_list'),
    path('battles/create/', views.battle_create, name='battle_create'),
    path('battles/matchmaking/', views.battle_matchmaking, name='battle_matchmaking'),
    path('battles/matchmaking/<int:subject_id>/', views.battle_matchmaking, name='battle_matchmaking_subject'),

    # 3. DAILY CHALLENGE (Static qismlar)
    path('daily/', views.daily_challenge, name='daily_challenge'),
    path('daily/start/', views.daily_challenge_start, name='daily_challenge_start'),
    path('daily/play/', views.daily_challenge_play, name='daily_challenge_play'),
    path('daily/submit/', views.daily_challenge_submit, name='daily_challenge_submit'),

    # 4. WEEKLY LEAGUE
    path('league/', views.weekly_league, name='weekly_league'),

    # 5. CERTIFICATES
    path('certificates/', views.my_certificates, name='my_certificates'),
    path('certificate/verify/<str:code>/', views.verify_certificate, name='verify_certificate'),

    # 6. API ENDPOINTS (Bular ham statik prefiksga ega)
    path('api/battle/<uuid:uuid>/status/', views.api_battle_status, name='api_battle_status'),
    path('api/matchmaking/status/', views.api_matchmaking_status, name='api_matchmaking_status'),
    path('api/matchmaking/cancel/', views.api_matchmaking_cancel, name='api_matchmaking_cancel'),
    path('api/friends/online/', views.api_online_friends, name='api_online_friends'),
    path('api/log-violation/', views.api_log_violation, name='api_log_violation'),

    # 7. BATTLE ACTIONS (UUID asosida)
    path('battle/<uuid:uuid>/', views.battle_detail, name='battle_detail'),
    path('battle/<uuid:uuid>/accept/', views.battle_accept, name='battle_accept'),
    path('battle/<uuid:uuid>/reject/', views.battle_reject, name='battle_reject'),
    path('battle/<uuid:uuid>/play/', views.battle_play, name='battle_play'),
    path('battle/<uuid:uuid>/submit/', views.battle_submit, name='battle_submit'),
    path('battle/<uuid:uuid>/result/', views.battle_result, name='battle_result'),

    # 8. COMPETITION ACTIONS (SLUG - DOIM ENG PASTDA TURISHI KERAK)
    path('<slug:slug>/', views.competition_detail, name='competition_detail'),
    path('<slug:slug>/join/', views.competition_join, name='competition_join'),
    path('<slug:slug>/payment/', views.competition_payment, name='competition_payment'),
    path('<slug:slug>/start/', views.competition_start, name='competition_start'),
    path('<slug:slug>/play/', views.competition_play, name='competition_play'),
    path('<slug:slug>/submit/', views.competition_submit, name='competition_submit'),
    path('<slug:slug>/result/', views.competition_result, name='competition_result'),
    path('<slug:slug>/leaderboard/', views.competition_leaderboard, name='competition_leaderboard'),
    path('api/<slug:slug>/leaderboard/', views.api_leaderboard, name='api_leaderboard'),
]