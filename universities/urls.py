"""
TestMakon.uz - Universities URLs
"""

from django.urls import path
from . import views

app_name = 'universities'

urlpatterns = [
    path('', views.universities_list, name='universities_list'),
    path('<slug:slug>/', views.university_detail, name='university_detail'),
    path('<slug:slug>/directions/', views.university_directions, name='university_directions'),
    path('direction/<uuid:uuid>/', views.direction_detail, name='direction_detail'),
    path('<slug:slug>/review/', views.add_review, name='add_review'),

    # API
    path('api/search/', views.api_search, name='api_search'),
    path('api/passing-scores/<int:direction_id>/', views.api_passing_scores, name='api_passing_scores'),
]