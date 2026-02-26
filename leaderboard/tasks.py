from celery import shared_task
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

LEADERBOARD_CACHE_TTL = 60 * 10  # 10 daqiqa


@shared_task
def invalidate_leaderboard_cache():
    """
    Test tugagach yoki XP o'zgargach leaderboard cache tozalanadi.
    tests_app/tasks.py da chaqiriladi.
    """
    cache.delete('leaderboard:global')
    cache.delete('leaderboard:weekly')
    cache.delete('leaderboard:monthly')
    logger.info("Leaderboard cache tozalandi")


@shared_task
def warm_leaderboard_cache():
    """
    Celery beat bilan har 10 daqiqada leaderboard ni qayta hisoblash.
    Foydalanuvchi kirganida tayyor natija topadi — kutmaydi.
    """
    from accounts.models import User
    from tests_app.models import TestAttempt
    from django.db.models import Sum, Count
    from django.utils import timezone
    from datetime import timedelta

    # Global
    users = list(
        User.objects.filter(is_active=True)
        .only('id', 'first_name', 'last_name', 'phone_number', 'xp_points', 'level', 'avatar', 'global_rank', 'region', 'total_tests_taken')
        .order_by('-xp_points')[:100]
    )
    cache.set('leaderboard:global', users, LEADERBOARD_CACHE_TTL)

    # Weekly
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())
    weekly_raw = list(
        TestAttempt.objects.filter(started_at__date__gte=week_start, status='completed')
        .values('user').annotate(total_xp=Sum('xp_earned'), tests_count=Count('id'))
        .order_by('-total_xp')[:100]
    )
    user_ids = [u['user'] for u in weekly_raw]
    users_map = {
        u.id: u for u in User.objects.filter(id__in=user_ids)
        .only('id', 'first_name', 'last_name', 'phone_number', 'xp_points', 'level', 'avatar')
    }
    weekly = [
        {'rank': i + 1, 'user': users_map[e['user']], 'xp': e['total_xp'], 'tests': e['tests_count']}
        for i, e in enumerate(weekly_raw) if e['user'] in users_map
    ]
    cache.set('leaderboard:weekly', weekly, LEADERBOARD_CACHE_TTL)

    # Monthly
    month_start = today.replace(day=1)
    monthly_raw = list(
        TestAttempt.objects.filter(started_at__date__gte=month_start, status='completed')
        .values('user').annotate(total_xp=Sum('xp_earned'), tests_count=Count('id'))
        .order_by('-total_xp')[:100]
    )
    user_ids = [u['user'] for u in monthly_raw]
    users_map = {
        u.id: u for u in User.objects.filter(id__in=user_ids)
        .only('id', 'first_name', 'last_name', 'phone_number', 'xp_points', 'level', 'avatar')
    }
    monthly = [
        {'rank': i + 1, 'user': users_map[e['user']], 'xp': e['total_xp'], 'tests': e['tests_count']}
        for i, e in enumerate(monthly_raw) if e['user'] in users_map
    ]
    cache.set('leaderboard:monthly', monthly, LEADERBOARD_CACHE_TTL)

    logger.info("Leaderboard cache yangilandi")
