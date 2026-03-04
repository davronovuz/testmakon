"""
TestMakon.uz — Sitemap (To'liq versiya)
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tests_app.models import Subject, Topic, Test
from news.models import Article


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
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

    def location(self, item):
        return reverse(item)


class SubjectSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Subject.objects.filter(is_active=True).order_by('order')

    def location(self, obj):
        return reverse('tests_app:practice_subject', kwargs={'subject_slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class TopicSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Topic.objects.filter(
            is_active=True,
            subject__is_active=True
        ).select_related('subject')

    def location(self, obj):
        return reverse('tests_app:practice_topic', kwargs={
            'subject_slug': obj.subject.slug,
            'topic_slug': obj.slug
        })


class TestSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Test.objects.filter(
            is_active=True
        ).order_by('-created_at')[:500]

    def location(self, obj):
        return reverse('tests_app:test_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.updated_at


class ArticleSitemap(Sitemap):
    priority = 0.6
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return Article.objects.filter(
            is_published=True
        ).order_by('-published_at')[:500]

    def location(self, obj):
        return reverse('news:article_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.published_at