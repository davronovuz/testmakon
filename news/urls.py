"""
TestMakon.uz - News URLs
"""

from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.news_list, name='news_list'),
    path('category/<slug:slug>/', views.category_detail, name='category_detail'),
    path('article/<slug:slug>/', views.article_detail, name='article_detail'),
    path('article/<slug:slug>/like/', views.article_like, name='article_like'),
    path('tips/', views.tips_list, name='tips_list'),
    path('notifications/', views.notifications_list, name='notifications_list'),
    path('notifications/mark-read/<int:id>/', views.notification_mark_read, name='notification_mark_read'),
    path('notifications/mark-all-read/', views.notifications_mark_all_read, name='notifications_mark_all_read'),
    path('api/unread-count/', views.api_unread_count, name='api_unread_count'),
    path('api/notifications/recent/', views.api_notifications_recent, name='api_notifications_recent'),
    path('api/notifications/read/<int:id>/', views.api_notification_read, name='api_notification_read'),
]