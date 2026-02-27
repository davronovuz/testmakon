"""
TestMakon.uz - Universities URLs
Complete URL patterns for universities app

MUHIM: URL tartibiga e'tibor bering!
Static URL'lar (compare/, directions/) <slug:slug>/ dan OLDIN bo'lishi kerak!
"""

from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    # ============================================================
    # STATIC PAGES (slug dan oldin bo'lishi kerak!)
    # ============================================================

    # Universities list (main page)
    path('', views.universities_list, name='universities_list'),

    # Compare universities
    path('compare/', views.university_compare, name='compare'),

    # All directions (across all universities)
    path('directions/', views.all_directions, name='all_directions'),

    # Direction detail (UUID)
    path('direction/<uuid:uuid>/', views.direction_detail, name='direction_detail'),

    # ============================================================
    # API ENDPOINTS (slug dan oldin bo'lishi kerak!)
    # ============================================================

    # Filter API (AJAX)
    path('api/filter/', views.api_filter, name='api_filter'),

    # Search API
    path('api/search/', views.api_search, name='api_search'),

    # Universities list API (for compare modal)
    path('api/list/', views.api_universities, name='api_universities'),

    # Compare API
    path('api/compare/', views.api_compare, name='api_compare'),

    # Calculate admission API
    path('api/calculate/', views.api_calculate_admission, name='api_calculate'),

    # University directions API (for calculator)
    path('api/<slug:slug>/directions/', views.api_directions, name='api_directions'),

    # Direction passing scores API
    path('api/direction/<int:direction_id>/scores/', views.api_passing_scores, name='api_passing_scores'),

    # ============================================================
    # DYNAMIC PAGES (slug bilan - oxirida bo'lishi kerak!)
    # ============================================================

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
]