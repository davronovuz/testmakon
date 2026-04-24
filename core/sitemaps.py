"""
TestMakon.uz — Sitemap (Himoyalangan versiya)
"""
import logging
from django.contrib.sitemaps import Sitemap
from django.urls import reverse, NoReverseMatch
from tests_app.models import Subject, Topic, Test
from news.models import Article

logger = logging.getLogger(__name__)


class SafeSitemap(Sitemap):
    """Base: bitta obyektda xatolik bo'lsa butun sitemap sinmasin."""

    def _items(self):
        return []

    def items(self):
        safe = []
        for obj in self._items():
            try:
                loc = self._safe_location(obj)
                if loc:
                    safe.append(obj)
            except Exception as e:
                logger.warning("sitemap skip %s: %s", type(obj).__name__, e)
        return safe

    def _safe_location(self, obj):
        return None

    def location(self, obj):
        return self._safe_location(obj)


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        names = [
            'core:home',
            'core:landing_dtm',
            'core:landing_online_test',
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
        if not obj.slug:
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
        if not obj.slug or not obj.subject or not obj.subject.slug:
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
        return (
            Test.objects.filter(is_active=True)
            .exclude(slug__isnull=True)
            .exclude(slug='')
            .order_by('-created_at')[:500]
        )

    def _safe_location(self, obj):
        if not obj.slug:
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
        if not obj.slug:
            return None
        return reverse('news:article_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return getattr(obj, 'published_at', None) or getattr(obj, 'updated_at', None)
