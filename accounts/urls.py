"""
TestMakon.uz - Accounts URLs
Authentication, profile, friends
"""

from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Phone verification
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('resend-code/', views.resend_code, name='resend_code'),

    # Password
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/<str:token>/', views.reset_password, name='reset_password'),
    path('change-password/', views.change_password, name='change_password'),

    # Profile
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('profile/avatar/', views.profile_avatar, name='profile_avatar'),
    path('profile/<uuid:uuid>/', views.profile_public, name='profile_public'),

    # Settings
    path('settings/', views.settings, name='settings'),
    path('settings/notifications/', views.notification_settings, name='notification_settings'),
    path('settings/privacy/', views.privacy_settings, name='privacy_settings'),

    # Friends
    path('friends/', views.friends_list, name='friends_list'),
    path('friends/requests/', views.friend_requests, name='friend_requests'),
    path('friends/add/<int:user_id>/', views.friend_add, name='friend_add'),
    path('friends/accept/<int:request_id>/', views.friend_accept, name='friend_accept'),
    path('friends/reject/<int:request_id>/', views.friend_reject, name='friend_reject'),
    path('friends/remove/<int:user_id>/', views.friend_remove, name='friend_remove'),
    path('friends/search/', views.friend_search, name='friend_search'),

    # Activity
    path('activity/', views.activity_log, name='activity_log'),

    # Badges
    path('badges/', views.badges, name='badges'),

    # API
    path('api/check-phone/', views.api_check_phone, name='api_check_phone'),
    path('api/profile-stats/', views.api_profile_stats, name='api_profile_stats'),
]