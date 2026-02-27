"""
Online Presence Middleware
Har requestda foydalanuvchi online statusini yangilaydi.
"""

from django.utils import timezone
from django.core.cache import cache


class OnlinePresenceMiddleware:
    """
    Kirgan foydalanuvchi har requestda online deb belgilanadi.
    Redis da 5 daqiqa TTL bilan saqlanadi.
    DB ga esa 60 soniyada bir marta yoziladi (cache orqali).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            user_id = request.user.id
            cache_key = f'online:{user_id}'
            db_write_key = f'online_db_write:{user_id}'

            # Redis da online belgisi qo'yish (5 daqiqa TTL)
            cache.set(cache_key, 1, timeout=300)

            # DB ga 60 soniyada bir marta yozish
            if not cache.get(db_write_key):
                try:
                    from accounts.models import User
                    User.objects.filter(pk=user_id).update(last_online=timezone.now())
                except Exception:
                    pass
                cache.set(db_write_key, 1, timeout=60)

        response = self.get_response(request)
        return response
