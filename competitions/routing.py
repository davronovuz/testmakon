"""
WebSocket URL Routing
"""

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/notifications/', consumers.NotificationConsumer.as_asgi()),
    path('ws/exam/<slug:slug>/', consumers.ExamConsumer.as_asgi()),
]
