"""
TestMakon.uz — Sitemap (Himoyalangan versiya)
"""
import logging
import re
from django.contrib.sitemaps import Sitemap
from django.urls import reverse, NoReverseMatch
from tests_app.models import Subject, Topic, Test
from news.models import Article

logger = logging.getLogger(__name__)

# Django URLconf slug pattern: [-a-zA-Z0-9_]+ — nuqta, bo'sh joy, boshqa
# belgilar qabul qilinmaydi. Slug tekshirish uchun shu regex.
_SAFE_SLUG_RE = re.compile(r'^[-a-zA-Z0-9_]+$')


def _is_safe_slug(slug):
    return bool(slug) and bool(_SAFE_SLUG_RE.match(slug))


class SafeSitemap(Sitemap):
    """Base: bitta obyektda xatolik bo'lsa butun sitemap sinmasin.

    items() metodi har bir obyektni oldindan _safe_location bilan tekshiradi
    va FAQAT muvaffaqiyatli reverse bo'lganlarni qaytaradi. Shunday qilib
    Django internal'idagi location() chaqiruvi hech qachon exception
    bermaydi.
    """

    def _items(self):
        return []

    def items(self):
        safe = []
        for obj in self._items():
            try:
                loc = self._safe_location(obj)
            except Exception as e:
                logger.warning("sitemap skip %s id=%s: %s", type(obj).__name__, getattr(obj, 'pk', '?'), e)
                continue
            if loc:
                safe.append(obj)
        return safe

    def _safe_location(self, obj):
        return None

    def location(self, obj):
        # items() allaqachon filter qilgan — bu chaqiruv xavfsiz bo'lishi kerak.
        # Lekin himoya uchun try/except qo'shamiz.
        try:
            return self._safe_location(obj)
        except Exception as e:
            logger.warning("sitemap location fallback %s: %s", type(obj).__name__, e)
            return '/'


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        names = [
            'core:home',
            'core:landing_dtm',
            'core:landing_online_test',
            'core:dtm_test_hub',
            'tests_app:tests_list',
            'tests_app:practice_select',
            'tests_app:dtm_simulation',
            'tests_app:quick_test',
            'tests_app:block_test',
            'tests_app:question_bank',
            'leaderboard:leaderboard_main',
            'news:news_list',
            'universities:universities_list',
            'core:about',
            'core:faq',
        ]
        valid = []
        for n in names:
            try:
                reverse(n)
                valid.append(n)
            except NoReverseMatch as e:
                logger.warning("sitemap static skip %s: %s", n, e)
        return valid

    def location(self, item):
        return reverse(item)


class SubjectSitemap(SafeSitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def _items(self):
        return Subject.objects.filter(is_active=True).exclude(slug__isnull=True).exclude(slug='').order_by('order')

    def _safe_location(self, obj):
        if not _is_safe_slug(obj.slug):
            return None
        return reverse('tests_app:practice_subject', kwargs={'subject_slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class TopicSitemap(SafeSitemap):
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'

    def _items(self):
        return (
            Topic.objects.filter(is_active=True, subject__is_active=True)
            .exclude(slug__isnull=True)
            .exclude(slug='')
            .select_related('subject')
        )

    def _safe_location(self, obj):
        if not _is_safe_slug(obj.slug):
            return None
        if not obj.subject or not _is_safe_slug(obj.subject.slug):
            return None
        return reverse('tests_app:practice_topic', kwargs={
            'subject_slug': obj.subject.slug,
            'topic_slug': obj.slug,
        })


class TestSitemap(SafeSitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'
    limit = 200  # bir sitemapda max 200, katta tests qismlanadi

    def _items(self):
        # Faqat "sof" slug (harf/raqam/tire/pastki chiziq) bo'lgan Test'lar.
        # Auto-generated practice testlar slug'ida nuqta bor — ular public
        # sitemapda kerak emas.
        return (
            Test.objects.filter(is_active=True)
            .exclude(slug__isnull=True)
            .exclude(slug='')
            .exclude(slug__contains='.')
            .exclude(slug__contains=' ')
            .order_by('-created_at')[:500]
        )

    def _safe_location(self, obj):
        if not _is_safe_slug(obj.slug):
            return None
        return reverse('tests_app:test_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'updated_at', None)


class ArticleSitemap(SafeSitemap):
    priority = 0.6
    changefreq = 'daily'
    protocol = 'https'
    limit = 200

    def _items(self):
        return (
            Article.objects.filter(is_published=True)
            .exclude(slug__isnull=True)
            .exclude(slug='')
            .order_by('-published_at')[:500]
        )

    def _safe_location(self, obj):
        if not _is_safe_slug(obj.slug):
            return None
        return reverse('news:article_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'published_at', None) or getattr(obj, 'updated_at', None)
