"""
TestMakon.uz — Coding URLs
"""

from django.urls import path
from . import views

app_name = 'coding'

urlpatterns = [
    # Sahifalar
    path('', views.problems_list, name='problems_list'),
    path('leaderboard/', views.coding_leaderboard, name='leaderboard'),
    path('my-submissions/', views.my_submissions, name='my_submissions'),
    path('submission/<int:pk>/', views.submission_detail, name='submission_detail'),
    path('problem/<slug:slug>/', views.problem_detail, name='problem_detail'),

    # API — AJAX
    path('api/submit/', views.api_submit_code, name='api_submit'),
    path('api/run-sample/', views.api_run_sample, name='api_run_sample'),
    path('api/status/<int:pk>/', views.api_submission_status, name='api_submission_status'),
]
