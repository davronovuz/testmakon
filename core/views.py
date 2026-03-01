"""
TestMakon.uz - Core Views
Home, dashboard, and static pages
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from .models import SiteSettings, ContactMessage, Feedback, FAQ, Banner, Partner
from accounts.models import User, UserActivity
from tests_app.models import Subject, Test, TestAttempt
from competitions.models import Competition, Battle
from news.models import Article
from leaderboard.models import GlobalLeaderboard


def home(request):
    """Bosh sahifa"""

    # Site settings
    settings = SiteSettings.get_settings()

    # Fanlar
    subjects = Subject.objects.filter(is_active=True).order_by('order')[:8]

    # Statistika
    stats = {
        'users': User.objects.filter(is_active=True).count(),
        'tests': Test.objects.filter(is_active=True).count(),
        'attempts': TestAttempt.objects.filter(status='completed').count(),
        'questions': settings.total_questions or 0,
    }

    # So'nggi yangiliklardan
    news = Article.objects.filter(
        is_published=True
    ).order_by('-published_at')[:3]

    # Yaqinlashayotgan musobaqalar
    upcoming_competitions = Competition.objects.filter(
        status='upcoming',
        is_active=True
    ).order_by('start_time')[:3]

    # Top foydalanuvchilar
    top_users = User.objects.filter(
        is_active=True
    ).order_by('-xp_points')[:5]

    # Bannerlar
    banners = Banner.objects.filter(
        is_active=True,
        position='home_hero'
    ).order_by('order')

    # Hamkorlar
    partners = Partner.objects.filter(is_active=True).order_by('order')

    context = {
        'settings': settings,
        'subjects': subjects,
        'stats': stats,
        'news': news,
        'upcoming_competitions': upcoming_competitions,
        'top_users': top_users,
        'banners': banners,
        'partners': partners,
    }

    # Authenticated user uchun personalized data
    if request.user.is_authenticated:
        user = request.user
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)

        recent_attempts = TestAttempt.objects.filter(
            user=user
        ).select_related('test', 'test__subject').order_by('-started_at')[:5]

        weekly_attempts = TestAttempt.objects.filter(
            user=user,
            started_at__date__gte=week_ago,
            status='completed'
        )

        # Kunlik challenge
        from competitions.models import DailyChallenge
        daily_challenge = DailyChallenge.objects.filter(
            date=today,
            is_active=True
        ).first()

        context.update({
            'user_stats': {
                'xp': user.xp_points,
                'level': user.get_level_display(),
                'streak': user.current_streak,
                'tests_taken': user.total_tests_taken,
                'accuracy': user.accuracy_rate,
            },
            'recent_attempts': recent_attempts,
            'weekly_tests': weekly_attempts.count(),
            'weekly_xp': weekly_attempts.aggregate(Sum('xp_earned'))['xp_earned__sum'] or 0,
            'daily_challenge': daily_challenge,
        })

    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """Foydalanuvchi dashboard"""

    user = request.user
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)

    # Foydalanuvchi statistikasi
    user_stats = {
        'xp': user.xp_points,
        'level': user.get_level_display(),
        'streak': user.current_streak,
        'tests_taken': user.total_tests_taken,
        'accuracy': user.accuracy_rate,
    }

    # So'nggi testlar
    recent_attempts = TestAttempt.objects.filter(
        user=user
    ).select_related('test').order_by('-started_at')[:5]

    # Haftalik progress
    weekly_attempts = TestAttempt.objects.filter(
        user=user,
        started_at__date__gte=week_ago,
        status='completed'
    )
    weekly_stats = {
        'tests': weekly_attempts.count(),
        'correct': weekly_attempts.aggregate(Sum('correct_answers'))['correct_answers__sum'] or 0,
        'xp': weekly_attempts.aggregate(Sum('xp_earned'))['xp_earned__sum'] or 0,
    }

    # AI tavsiyalar
    from ai_core.models import AIRecommendation
    recommendations = AIRecommendation.objects.filter(
        user=user,
        is_dismissed=False
    ).order_by('-priority', '-created_at')[:3]

    # Faol musobaqalar
    active_competitions = Competition.objects.filter(
        status='active',
        is_active=True
    )[:3]

    # Kutilayotgan janglar
    pending_battles = Battle.objects.filter(
        opponent=user,
        status='pending'
    ).select_related('challenger')[:5]

    # Kunlik challenge
    from competitions.models import DailyChallenge
    daily_challenge = DailyChallenge.objects.filter(
        date=today,
        is_active=True
    ).first()

    # Reyting
    user_rank = GlobalLeaderboard.objects.filter(
        user=user,
        period='weekly'
    ).first()

    # Fan bo'yicha progress
    subject_progress = []
    for subject in Subject.objects.filter(is_active=True)[:6]:
        attempts = TestAttempt.objects.filter(
            user=user,
            test__subject=subject,
            status='completed'
        )
        if attempts.exists():
            avg_score = attempts.aggregate(Avg('percentage'))['percentage__avg']
            subject_progress.append({
                'subject': subject,
                'avg_score': round(avg_score, 1) if avg_score else 0,
                'attempts': attempts.count()
            })

    context = {
        'user_stats': user_stats,
        'recent_attempts': recent_attempts,
        'weekly_stats': weekly_stats,
        'recommendations': recommendations,
        'active_competitions': active_competitions,
        'pending_battles': pending_battles,
        'daily_challenge': daily_challenge,
        'user_rank': user_rank,
        'subject_progress': subject_progress,
    }

    return render(request, 'core/dashboard.html', context)


def about(request):
    """Biz haqimizda"""
    settings = SiteSettings.get_settings()

    # Jamoa statistikasi
    stats = {
        'users': User.objects.filter(is_active=True).count(),
        'tests': Test.objects.filter(is_active=True).count(),
        'questions': settings.total_questions,
    }

    partners = Partner.objects.filter(is_active=True)

    context = {
        'settings': settings,
        'stats': stats,
        'partners': partners,
    }

    return render(request, 'core/about.html', context)


def contact(request):
    """Aloqa sahifasi"""
    settings = SiteSettings.get_settings()

    context = {
        'settings': settings,
    }

    return render(request, 'core/contact.html', context)


def contact_submit(request):
    """Aloqa formasini yuborish"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        ContactMessage.objects.create(
            name=name,
            email=email,
            phone=phone,
            subject=subject,
            message=message,
            user=request.user if request.user.is_authenticated else None
        )

        messages.success(request, "Xabaringiz muvaffaqiyatli yuborildi! Tez orada javob beramiz.")
        return redirect('core:contact')

    return redirect('core:contact')


def faq(request):
    """Ko'p beriladigan savollar"""
    faqs = FAQ.objects.filter(is_active=True).order_by('category', 'order')

    # Kategoriyalar bo'yicha guruhlash
    faq_by_category = {}
    for faq in faqs:
        category = faq.get_category_display()
        if category not in faq_by_category:
            faq_by_category[category] = []
        faq_by_category[category].append(faq)

    context = {
        'faq_by_category': faq_by_category,
    }

    return render(request, 'core/faq.html', context)


def privacy(request):
    """Maxfiylik siyosati"""
    return render(request, 'core/privacy.html')


def terms(request):
    """Foydalanish shartlari"""
    return render(request, 'core/terms.html')


@login_required
def feedback(request):
    """Fikr-mulohaza sahifasi"""
    return render(request, 'core/feedback.html')


@login_required
def feedback_submit(request):
    """Fikr-mulohaza yuborish"""
    if request.method == 'POST':
        feedback_type = request.POST.get('feedback_type')
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        page_url = request.POST.get('page_url', '')

        feedback = Feedback.objects.create(
            user=request.user,
            feedback_type=feedback_type,
            subject=subject,
            message=message,
            page_url=page_url
        )

        # Handle file upload
        if 'attachment' in request.FILES:
            feedback.attachment = request.FILES['attachment']
            feedback.save()

        messages.success(request, "Fikr-mulohazangiz uchun rahmat!")
        return redirect('core:dashboard')

    return redirect('core:feedback')


def search(request):
    """Qidiruv"""
    query = request.GET.get('q', '').strip()

    results = {
        'tests': [],
        'subjects': [],
        'universities': [],
        'news': [],
    }

    if query and len(query) >= 2:
        # Testlarni qidirish
        results['tests'] = Test.objects.filter(
            title__icontains=query,
            is_active=True
        )[:10]

        # Fanlarni qidirish
        results['subjects'] = Subject.objects.filter(
            name__icontains=query,
            is_active=True
        )[:5]

        # Universitetlarni qidirish
        from universities.models import University
        results['universities'] = University.objects.filter(
            name__icontains=query,
            is_active=True
        )[:10]

        # Yangiliklarni qidirish
        results['news'] = Article.objects.filter(
            title__icontains=query,
            is_published=True
        )[:5]

    context = {
        'query': query,
        'results': results,
        'total_results': sum(len(v) for v in results.values()),
    }

    return render(request, 'core/search.html', context)


# API Views

@login_required
def api_stats(request):
    """Dashboard statistika API"""
    user = request.user
    today = timezone.now().date()

    data = {
        'xp': user.xp_points,
        'level': user.level,
        'streak': user.current_streak,
        'tests_today': TestAttempt.objects.filter(
            user=user,
            started_at__date=today
        ).count(),
        'rank': user.global_rank,
    }

    return JsonResponse(data)


@login_required
def api_activity(request):
    """Foydalanuvchi faoliyati API"""
    activities = UserActivity.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]

    data = [{
        'type': a.activity_type,
        'description': a.description,
        'xp': a.xp_earned,
        'time': a.created_at.isoformat(),
    } for a in activities]

    return JsonResponse({'activities': data})


# ─────────────────────────────────────────────────
# ADMIN ANALYTICS PANEL
# ─────────────────────────────────────────────────

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def admin_analytics(request):
    """Staff uchun platform analytics paneli."""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Foydalanuvchilar
    total_users = User.objects.filter(is_active=True).count()
    new_today = User.objects.filter(date_joined__date=today).count()
    new_week = User.objects.filter(date_joined__date__gte=week_ago).count()
    new_month = User.objects.filter(date_joined__date__gte=month_ago).count()
    dau = User.objects.filter(last_activity_date=today).count() if hasattr(User, 'last_activity_date') else 0

    # Test urinishlari
    attempts_today = TestAttempt.objects.filter(started_at__date=today, status='completed').count()
    attempts_week = TestAttempt.objects.filter(started_at__date__gte=week_ago, status='completed').count()
    attempts_month = TestAttempt.objects.filter(started_at__date__gte=month_ago, status='completed').count()

    # O'rtacha ball
    avg_score = TestAttempt.objects.filter(
        status='completed', started_at__date__gte=month_ago
    ).aggregate(avg=Avg('percentage'))['avg'] or 0

    # Eng mashhur fanlar (oylik)
    popular_subjects = (
        TestAttempt.objects.filter(started_at__date__gte=month_ago, status='completed')
        .values('test__subject__name')
        .annotate(cnt=Count('id'))
        .order_by('-cnt')[:8]
    )

    # So'nggi 14 kun — kunlik attempt grafigi
    daily_attempts = []
    for i in range(13, -1, -1):
        d = today - timedelta(days=i)
        cnt = TestAttempt.objects.filter(started_at__date=d, status='completed').count()
        users_cnt = User.objects.filter(date_joined__date=d).count()
        daily_attempts.append({'date': d.strftime('%d.%m'), 'attempts': cnt, 'new_users': users_cnt})

    import json as json_mod
    chart_labels = json_mod.dumps([d['date'] for d in daily_attempts])
    chart_attempts = json_mod.dumps([d['attempts'] for d in daily_attempts])
    chart_users = json_mod.dumps([d['new_users'] for d in daily_attempts])

    # Top 10 foydalanuvchi (XP bo'yicha)
    top_users = User.objects.filter(is_active=True).order_by('-xp_points')[:10]

    # So'nggi xatolar (Sentry yo'q bo'lsa — oxirgi test urinishlari)
    recent_attempts = TestAttempt.objects.filter(
        status='completed'
    ).select_related('user', 'test').order_by('-started_at')[:15]

    # Obunalar
    try:
        from subscriptions.models import Subscription
        premium_count = Subscription.objects.filter(is_active=True).count()
    except Exception:
        premium_count = 0

    context = {
        'total_users': total_users,
        'new_today': new_today,
        'new_week': new_week,
        'new_month': new_month,
        'dau': dau,
        'attempts_today': attempts_today,
        'attempts_week': attempts_week,
        'attempts_month': attempts_month,
        'avg_score': round(avg_score, 1),
        'popular_subjects': popular_subjects,
        'chart_labels': chart_labels,
        'chart_attempts': chart_attempts,
        'chart_users': chart_users,
        'top_users': top_users,
        'recent_attempts': recent_attempts,
        'premium_count': premium_count,
        'today': today,
    }
    return render(request, 'core/admin_analytics.html', context)


# Error handlers

def error_404(request, exception):
    """404 sahifasi"""
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    """500 sahifasi"""
    return render(request, 'errors/500.html', status=500)

# ─────────────────────────────────────────────────
# BROADCAST NOTIFICATION
# ─────────────────────────────────────────────────

@staff_member_required
def admin_broadcast(request):
    """Staff: barcha yoki tanlangan userlarga bildirishnoma yuborish."""
    from news.models import Notification

    if request.method == 'GET':
        try:
            from subscriptions.models import Subscription
            premium_count = Subscription.objects.filter(is_active=True).count()
        except Exception:
            premium_count = 0
        free_count = User.objects.filter(is_active=True).count() - premium_count
        return render(request, 'core/admin_broadcast.html', {
            'total_users': User.objects.filter(is_active=True).count(),
            'premium_count': premium_count,
            'free_count': free_count,
        })

    # POST
    title = request.POST.get('title', '').strip()
    message = request.POST.get('message', '').strip()
    notif_type = request.POST.get('notif_type', 'system')
    target = request.POST.get('target', 'all')
    link = request.POST.get('link', '').strip()

    if not title or not message:
        messages.error(request, "Sarlavha va xabar maydoni to'ldirilishi shart.")
        return redirect('core:admin_broadcast')

    # Target users
    qs = User.objects.filter(is_active=True)
    if target == 'premium':
        try:
            from subscriptions.models import Subscription
            premium_ids = Subscription.objects.filter(is_active=True).values_list('user_id', flat=True)
            qs = qs.filter(id__in=premium_ids)
        except Exception:
            pass
    elif target == 'free':
        try:
            from subscriptions.models import Subscription
            premium_ids = Subscription.objects.filter(is_active=True).values_list('user_id', flat=True)
            qs = qs.exclude(id__in=premium_ids)
        except Exception:
            pass

    # Bulk create notifications
    valid_types = ('system', 'news', 'competition', 'battle', 'achievement', 'friend', 'reminder')
    if notif_type not in valid_types:
        notif_type = 'system'

    batch = []
    for user in qs.only('id'):
        batch.append(Notification(
            user=user,
            notification_type=notif_type,
            title=title,
            message=message,
            link=link,
        ))
        if len(batch) >= 500:
            Notification.objects.bulk_create(batch, ignore_conflicts=True)
            batch = []
    if batch:
        Notification.objects.bulk_create(batch, ignore_conflicts=True)

    count = qs.count()
    messages.success(request, f"Xabar {count} ta foydalanuvchiga yuborildi.")
    return redirect('core:admin_broadcast')


# ─────────────────────────────────────────────────
# SYSTEM HEALTH + SAVOL STATISTIKASI
# ─────────────────────────────────────────────────

@staff_member_required
def admin_system_health(request):
    """Staff: tizim holati va savol bank statistikasi."""
    from tests_app.models import Subject, Topic, Question
    from django.db.models import Q
    import json as json_mod

    # ── Redis holati ──
    redis_ok = False
    redis_info = ''
    try:
        from django.core.cache import cache
        cache.set('_health_check', 1, timeout=5)
        redis_ok = cache.get('_health_check') == 1
        redis_info = 'OK'
    except Exception as e:
        redis_info = str(e)[:80]

    # ── Celery holati ──
    celery_ok = False
    celery_info = ''
    try:
        from config.celery import app as celery_app
        resp = celery_app.control.ping(timeout=2)
        celery_ok = bool(resp)
        celery_info = f"{len(resp)} worker" if resp else "Worker topilmadi"
    except Exception as e:
        celery_info = str(e)[:80]

    # ── Savol bank statistikasi ──
    subject_stats = []
    for subj in Subject.objects.filter(is_active=True).order_by('name'):
        q_total = Question.objects.filter(subject=subj, is_active=True).count()
        q_with_topic = Question.objects.filter(subject=subj, is_active=True, topic__isnull=False).count()
        topics_total = Topic.objects.filter(subject=subj).count()
        # Mavzular bo'yicha savollar
        topic_details = (
            Topic.objects.filter(subject=subj)
            .annotate(qcount=Count('questions', filter=Q(questions__is_active=True)))
            .order_by('name')
        )
        empty_topics = [t.name for t in topic_details if t.qcount == 0]
        subject_stats.append({
            'subject': subj,
            'q_total': q_total,
            'q_with_topic': q_with_topic,
            'topics_total': topics_total,
            'empty_topics': empty_topics,
            'empty_count': len(empty_topics),
        })

    # ── Umumiy statistika ──
    total_questions = Question.objects.filter(is_active=True).count()
    total_answers = Answer.objects.count() if hasattr(Question, 'answers') else 0
    try:
        from tests_app.models import Answer as Ans
        total_answers = Ans.objects.count()
    except Exception:
        total_answers = 0

    # ── So'nggi 7 kun test urinishlari ──
    from tests_app.models import TestAttempt as TA
    today = timezone.now().date()
    week_data = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        cnt = TA.objects.filter(started_at__date=d, status='completed').count()
        week_data.append({'date': d.strftime('%d.%m'), 'count': cnt})

    context = {
        'redis_ok': redis_ok,
        'redis_info': redis_info,
        'celery_ok': celery_ok,
        'celery_info': celery_info,
        'subject_stats': subject_stats,
        'total_questions': total_questions,
        'total_answers': total_answers,
        'week_labels': json_mod.dumps([d['date'] for d in week_data]),
        'week_counts': json_mod.dumps([d['count'] for d in week_data]),
    }
    return render(request, 'core/admin_system_health.html', context)
