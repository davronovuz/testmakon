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

    # Admin analytics panel
    path('panel/analytics/', views.admin_analytics, name='admin_analytics'),

    # Admin tools
    path('panel/broadcast/', views.admin_broadcast, name='admin_broadcast'),
    path('panel/system/', views.admin_system_health, name='admin_system_health'),

    # SEO Landing Pages
    path('dtm-tayyorgarligi/', views.landing_dtm, name='landing_dtm'),
    path('online-test/', views.landing_online_test, name='landing_online_test'),
    path('dtm-test/', views.dtm_test_hub, name='dtm_test_hub'),

    # Short URL aliases -> 301 redirect to full articles (SEO)
    path('dtm-2026/', views.dtm_2026_redirect, name='dtm_2026_alias'),
    path('matematika-dtm/', views.matematika_dtm_redirect, name='matematika_dtm_alias'),
    path('fizika-dtm/', views.fizika_dtm_redirect, name='fizika_dtm_alias'),
    path('biologiya-dtm/', views.biologiya_dtm_redirect, name='biologiya_dtm_alias'),
    path('kimyo-dtm/', views.kimyo_dtm_redirect, name='kimyo_dtm_alias'),
    path('dtm-ball/', views.dtm_ball_redirect, name='dtm_ball_alias'),
]