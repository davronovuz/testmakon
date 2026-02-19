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


# Error handlers

def error_404(request, exception):
    """404 sahifasi"""
    return render(request, 'errors/404.html', status=404)


def error_500(request):
    """500 sahifasi"""
    return render(request, 'errors/500.html', status=500)