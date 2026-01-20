"""
TestMakon.uz - News Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone

from .models import Category, Article, ArticleLike, Notification


def news_list(request):
    """Yangilikar ro'yxati"""
    articles = Article.objects.filter(
        is_published=True
    ).select_related('category', 'author').order_by('-is_pinned', '-published_at')

    article_type = request.GET.get('type')
    if article_type:
        articles = articles.filter(article_type=article_type)

    categories = Category.objects.filter(is_active=True)
    featured = articles.filter(is_featured=True)[:3]

    context = {
        'articles': articles[:20],
        'categories': categories,
        'featured': featured,
    }

    return render(request, 'news/news_list.html', context)


def category_detail(request, slug):
    """Kategoriya bo'yicha yangilikar"""
    category = get_object_or_404(Category, slug=slug, is_active=True)
    articles = Article.objects.filter(category=category, is_published=True).order_by('-published_at')

    context = {
        'category': category,
        'articles': articles,
    }

    return render(request, 'news/category_detail.html', context)


def article_detail(request, slug):
    """Maqola tafsilotlari"""
    article = get_object_or_404(Article, slug=slug, is_published=True)
    article.increment_views()

    is_liked = False
    if request.user.is_authenticated:
        is_liked = ArticleLike.objects.filter(article=article, user=request.user).exists()

    related = Article.objects.filter(
        category=article.category, is_published=True
    ).exclude(id=article.id)[:4]

    context = {
        'article': article,
        'is_liked': is_liked,
        'related': related,
    }

    return render(request, 'news/article_detail.html', context)


@login_required
def article_like(request, slug):
    """Maqolani yoqtirish"""
    article = get_object_or_404(Article, slug=slug)

    like, created = ArticleLike.objects.get_or_create(article=article, user=request.user)

    if not created:
        like.delete()
        article.likes_count -= 1
    else:
        article.likes_count += 1

    article.save()

    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': created, 'count': article.likes_count})

    return redirect('news:article_detail', slug=slug)


def tips_list(request):
    """Maslahatlar ro'yxati"""
    tips = Article.objects.filter(article_type='tip', is_published=True).order_by('-published_at')

    subject_slug = request.GET.get('subject')
    if subject_slug:
        tips = tips.filter(subject__slug=subject_slug)

    from tests_app.models import Subject
    subjects = Subject.objects.filter(is_active=True)

    context = {
        'tips': tips,
        'subjects': subjects,
    }

    return render(request, 'news/tips_list.html', context)


@login_required
def notifications_list(request):
    """Bildirishnomalar"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:50]

    context = {'notifications': notifications}
    return render(request, 'news/notifications_list.html', context)


@login_required
def notification_mark_read(request, id):
    """Bildirishnomani o'qilgan deb belgilash"""
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.read_at = timezone.now()
    notification.save()

    if notification.link:
        return redirect(notification.link)

    return redirect('news:notifications_list')


@login_required
def notifications_mark_all_read(request):
    """Barcha bildirishnomalarni o'qilgan deb belgilash"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True, read_at=timezone.now()
    )

    return redirect('news:notifications_list')


def api_unread_count(request):
    """O'qilmagan bildirishnomalar soni"""
    count = 0
    if request.user.is_authenticated:
        count = Notification.objects.filter(user=request.user, is_read=False).count()

    return JsonResponse({'count': count})