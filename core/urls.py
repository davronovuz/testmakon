"""
TestMakon.uz - Core URLs
Home, dashboard, and static pages
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Dashboard (authenticated users)
    path('dashboard/', views.dashboard, name='dashboard'),

    # Static pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('faq/', views.faq, name='faq'),
    path('privacy/', views.privacy, name='privacy'),
    path('terms/', views.terms, name='terms'),

    # Contact form submission
    path('contact/submit/', views.contact_submit, name='contact_submit'),

    # Feedback
    path('feedback/', views.feedback, name='feedback'),
    path('feedback/submit/', views.feedback_submit, name='feedback_submit'),

    # Search
    path('search/', views.search, name='search'),

    # API endpoints for dashboard widgets
    path('api/stats/', views.api_stats, name='api_stats'),
    path('api/activity/', views.api_activity, name='api_activity'),
]