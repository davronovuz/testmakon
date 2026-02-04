"""
TestMakon.uz - Universities URLs
Complete URL patterns for universities app
"""

from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    # ============================================================
    # MAIN PAGES
    # ============================================================

    # Universities list (main page)
    path('', views.universities_list, name='list'),

    # University detail
    path('<slug:slug>/', views.university_detail, name='detail'),

    # University directions
    path('<slug:slug>/directions/', views.university_directions, name='directions'),

    # University faculties
    path('<slug:slug>/faculties/', views.faculties_list, name='faculties'),

    # University admission calculator
    path('<slug:slug>/admission/', views.university_admission, name='admission'),

    # Add review
    path('<slug:slug>/review/add/', views.add_review, name='add_review'),

    # ============================================================
    # STANDALONE PAGES
    # ============================================================

    # Compare universities
    path('compare/', views.university_compare, name='compare'),

    # All directions (across all universities)
    path('directions/all/', views.all_directions, name='all_directions'),

    # Direction detail
    path('direction/<uuid:uuid>/', views.direction_detail, name='direction_detail'),

    # ============================================================
    # API ENDPOINTS
    # ============================================================

    # Search API
    path('api/search/', views.api_search, name='api_search'),

    # Universities list API (for compare modal)
    path('api/list/', views.api_universities, name='api_universities'),

    # University directions API (for calculator)
    path('api/<slug:slug>/directions/', views.api_directions, name='api_directions'),

    # Direction passing scores API
    path('api/direction/<int:direction_id>/scores/', views.api_passing_scores, name='api_passing_scores'),

    # Compare API
    path('api/compare/', views.api_compare, name='api_compare'),

    # Calculate admission API
    path('api/calculate/', views.api_calculate_admission, name='api_calculate'),
]