"""
TestMakon.uz - Leaderboard Views
"""

from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, Count, Avg
from django.core.cache import cache
from datetime import timedelta

from .models import (
    GlobalLeaderboard, SubjectLeaderboard, Achievement,
    UserAchievement, UserStats, SeasonalLeaderboard, SeasonalParticipant
)
from accounts.models import User
from tests_app.models import Subject, TestAttempt


def leaderboard_main(request):
    """Asosiy reyting sahifasi"""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    # Top 10 haftalik
    weekly_top = User.objects.filter(
        is_active=True
    ).order_by('-xp_points')[:10]

    # Fanlar
    subjects = Subject.objects.filter(is_active=True)[:6]

    # Foydalanuvchi reytingi
    user_rank = None
    if request.user.is_authenticated:
        user_rank = request.user.global_rank

    context = {
        'weekly_top': weekly_top,
        'subjects': subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/leaderboard_main.html', context)


def global_leaderboard(request):
    """Umumiy reyting — Redis cache (10 daqiqa)"""
    users = cache.get('leaderboard:global')
    if users is None:
        users = list(
            User.objects.filter(is_active=True)
            .only('id', 'first_name', 'last_name', 'username', 'xp_points', 'level', 'avatar', 'global_rank')
            .order_by('-xp_points')[:100]
        )
        cache.set('leaderboard:global', users, 60 * 10)

    subjects = Subject.objects.filter(is_active=True)
    user_rank = request.user.global_rank if request.user.is_authenticated else None

    context = {
        'users': users,
        'period': 'all_time',
        'subjects': subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/global_leaderboard.html', context)


def weekly_leaderboard(request):
    """Haftalik reyting — Redis cache (10 daqiqa)"""
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    leaderboard = cache.get('leaderboard:weekly')
    if leaderboard is None:
        top_users = TestAttempt.objects.filter(
            started_at__date__gte=week_start,
            status='completed'
        ).values('user').annotate(
            total_xp=Sum('xp_earned'),
            tests_count=Count('id')
        ).order_by('-total_xp')[:100]

        user_ids = [u['user'] for u in top_users]
        users_map = {
            u.id: u for u in User.objects.filter(id__in=user_ids)
            .only('id', 'first_name', 'last_name', 'username', 'xp_points', 'level', 'avatar')
        }
        leaderboard = [
            {'rank': i, 'user': users_map[e['user']], 'xp': e['total_xp'], 'tests': e['tests_count']}
            for i, e in enumerate(top_users, 1) if e['user'] in users_map
        ]
        cache.set('leaderboard:weekly', leaderboard, 60 * 10)

    subjects = Subject.objects.filter(is_active=True)
    user_rank = request.user.global_rank if request.user.is_authenticated else None

    context = {
        'leaderboard': leaderboard,
        'period': 'weekly',
        'week_start': week_start,
        'subjects': subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/weekly_leaderboard.html', context)


def monthly_leaderboard(request):
    """Oylik reyting — Redis cache (10 daqiqa)"""
    today = timezone.now().date()
    month_start = today.replace(day=1)

    leaderboard = cache.get('leaderboard:monthly')
    if leaderboard is None:
        top_users = TestAttempt.objects.filter(
            started_at__date__gte=month_start,
            status='completed'
        ).values('user').annotate(
            total_xp=Sum('xp_earned'),
            tests_count=Count('id')
        ).order_by('-total_xp')[:100]

        user_ids = [u['user'] for u in top_users]
        users_map = {
            u.id: u for u in User.objects.filter(id__in=user_ids)
            .only('id', 'first_name', 'last_name', 'username', 'xp_points', 'level', 'avatar')
        }
        leaderboard = [
            {'rank': i, 'user': users_map[e['user']], 'xp': e['total_xp'], 'tests': e['tests_count']}
            for i, e in enumerate(top_users, 1) if e['user'] in users_map
        ]
        cache.set('leaderboard:monthly', leaderboard, 60 * 10)

    subjects = Subject.objects.filter(is_active=True)
    user_rank = request.user.global_rank if request.user.is_authenticated else None

    context = {
        'leaderboard': leaderboard,
        'period': 'monthly',
        'month_start': month_start,
        'subjects': subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/monthly_leaderboard.html', context)


def subject_leaderboard(request, slug):
    """Fan bo'yicha reyting"""
    subject = get_object_or_404(Subject, slug=slug, is_active=True)

    top_users = TestAttempt.objects.filter(
        test__subject=subject,
        status='completed'
    ).values('user').annotate(
        total_xp=Sum('xp_earned'),
        tests_count=Count('id')
    ).order_by('-total_xp')[:100]

    user_ids = [u['user'] for u in top_users]
    users = {u.id: u for u in User.objects.filter(id__in=user_ids)}

    leaderboard = []
    for i, entry in enumerate(top_users, 1):
        user = users.get(entry['user'])
        if user:
            leaderboard.append({
                'rank': i,
                'user': user,
                'xp': entry['total_xp'],
                'tests': entry['tests_count'],
            })

    # Barcha fanlar
    subjects = Subject.objects.filter(is_active=True)

    context = {
        'subject': subject,
        'leaderboard': leaderboard,
        'subjects': subjects,
    }

    return render(request, 'leaderboard/subject_leaderboard.html', context)


def achievements_list(request):
    """Yutuqlar ro'yxati"""
    achievements = Achievement.objects.filter(is_active=True).order_by('category', 'requirement_value')

    # Kategoriyalar bo'yicha guruhlash
    by_category = {}
    for ach in achievements:
        cat = ach.get_category_display()
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(ach)

    # Foydalanuvchi yutuqlari
    earned_ids = []
    if request.user.is_authenticated:
        earned_ids = list(UserAchievement.objects.filter(
            user=request.user
        ).values_list('achievement_id', flat=True))

    subjects = Subject.objects.filter(is_active=True)
    user_rank = request.user.global_rank if request.user.is_authenticated else None

    context = {
        'by_category': by_category,
        'earned_ids': earned_ids,
        'subjects': subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/achievements_list.html', context)


def achievement_detail(request, slug):
    """Yutuq tafsilotlari"""
    achievement = get_object_or_404(Achievement, slug=slug)

    # Oxirgi olganlar
    recent_earners = UserAchievement.objects.filter(
        achievement=achievement
    ).select_related('user').order_by('-earned_at')[:10]

    # Foydalanuvchi olganligi
    is_earned = False
    if request.user.is_authenticated:
        is_earned = UserAchievement.objects.filter(
            user=request.user,
            achievement=achievement
        ).exists()

    context = {
        'achievement': achievement,
        'recent_earners': recent_earners,
        'is_earned': is_earned,
    }

    return render(request, 'leaderboard/achievement_detail.html', context)


@login_required
def my_stats(request):
    """Mening statistikam"""
    user = request.user

    # Yoki yaratish
    stats, created = UserStats.objects.get_or_create(user=user)

    # Test statistikasi
    attempts = TestAttempt.objects.filter(user=user, status='completed')

    agg = attempts.aggregate(
        total=Count('id'),
        total_xp=Sum('xp_earned'),
        avg_score=Avg('percentage'),
    )
    test_stats = {
        'total': agg['total'] or 0,
        'total_xp': agg['total_xp'] or 0,
        'avg_score': round(agg['avg_score'] or 0, 1),
    }

    # Yutuqlar
    achievements = UserAchievement.objects.filter(
        user=user
    ).select_related('achievement').order_by('-earned_at')[:10]

    # Fan bo'yicha — bitta query (N+1 o'rniga)
    subject_raw = (
        attempts.values('test__subject__id', 'test__subject__name', 'test__subject__color')
        .annotate(avg_score=Avg('percentage'), count=Count('id'))
        .filter(count__gt=0)
    )
    subjects_map = {s.id: s for s in Subject.objects.filter(is_active=True)}
    subject_stats = [
        {
            'subject': subjects_map.get(row['test__subject__id']),
            'avg_score': round(row['avg_score'] or 0, 1),
            'count': row['count'],
        }
        for row in subject_raw if row['test__subject__id'] in subjects_map
    ]

    all_subjects = Subject.objects.filter(is_active=True)
    user_rank = user.global_rank

    context = {
        'stats': stats,
        'test_stats': test_stats,
        'achievements': achievements,
        'subject_stats': subject_stats,
        'subjects': all_subjects,
        'user_rank': user_rank,
    }

    return render(request, 'leaderboard/my_stats.html', context)


def current_season(request):
    """Joriy mavsum"""
    season = SeasonalLeaderboard.objects.filter(
        is_active=True
    ).first()

    if not season:
        return render(request, 'leaderboard/no_season.html')

    participants = SeasonalParticipant.objects.filter(
        season=season
    ).select_related('user').order_by('rank')[:100]

    # Foydalanuvchi qatnashyaptimi
    user_participant = None
    if request.user.is_authenticated:
        user_participant = SeasonalParticipant.objects.filter(
            season=season,
            user=request.user
        ).first()

    context = {
        'season': season,
        'participants': participants,
        'user_participant': user_participant,
    }

    return render(request, 'leaderboard/current_season.html', context)


def season_detail(request, slug):
    """Mavsum tafsilotlari"""
    season = get_object_or_404(SeasonalLeaderboard, slug=slug)

    participants = SeasonalParticipant.objects.filter(
        season=season
    ).select_related('user').order_by('rank')

    context = {
        'season': season,
        'participants': participants,
    }

    return render(request, 'leaderboard/season_detail.html', context)


# API Views

@login_required
def api_my_rank(request):
    """Mening reytingim API"""
    user = request.user

    # Umumiy reyting
    higher_count = User.objects.filter(
        xp_points__gt=user.xp_points,
        is_active=True
    ).count()

    global_rank = higher_count + 1

    data = {
        'global_rank': global_rank,
        'xp': user.xp_points,
        'level': user.level,
        'streak': user.current_streak,
    }

    return JsonResponse(data)


def api_top_users(request):
    """Top foydalanuvchilar API"""
    period = request.GET.get('period', 'all_time')
    limit = int(request.GET.get('limit', 10))

    users = User.objects.filter(
        is_active=True
    ).order_by('-xp_points')[:limit]

    data = [{
        'id': u.id,
        'name': u.full_name,
        'avatar': u.get_avatar_url(),
        'xp': u.xp_points,
        'level': u.level,
    } for u in users]

    return JsonResponse({'users': data})