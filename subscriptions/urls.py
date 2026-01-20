"""
TestMakon.uz - Subscriptions URLs
"""

from django.urls import path
from . import views

app_name = 'subscriptions'

urlpatterns = [
    # Pages
    path('pricing/', views.pricing, name='pricing'),
    path('checkout/<slug:slug>/', views.checkout, name='checkout'),
    path('process/<slug:slug>/', views.process_payment, name='process_payment'),
    path('success/<uuid:uuid>/', views.payment_success, name='success'),
    path('failed/<uuid:uuid>/', views.payment_failed, name='failed'),
    path('my-subscription/', views.my_subscription, name='my_subscription'),
    path('cancel/', views.cancel_subscription, name='cancel'),

    # API
    path('api/check-promo/', views.api_check_promo, name='api_check_promo'),
    path('api/check-limits/', views.api_check_limits, name='api_check_limits'),

    # Webhooks
    path('webhook/click/', views.click_webhook, name='click_webhook'),
    path('webhook/payme/', views.payme_webhook, name='payme_webhook'),
]