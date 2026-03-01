"""
TestMakon.uz — Sitemap
"""
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from tests_app.models import Subject
from news.models import Article, Category


class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return [
            'core:home', 'core:about', 'core:faq',
            'tests_app:tests_list', 'tests_app:question_bank',
            'leaderboard:leaderboard_main', 'news:news_list',
            'universities:universities_list',
        ]

    def location(self, item):
        return reverse(item)


class SubjectSitemap(Sitemap):
    priority = 0.7
    changefreq = 'weekly'
    protocol = 'https'

    def items(self):
        return Subject.objects.filter(is_active=True)

    def location(self, obj):
        return reverse('tests_app:practice_subject', kwargs={'subject_slug': obj.slug})


class ArticleSitemap(Sitemap):
    priority = 0.6
    changefreq = 'daily'
    protocol = 'https'

    def items(self):
        return Article.objects.filter(is_published=True).order_by('-published_at')[:200]

    def location(self, obj):
        return reverse('news:article_detail', kwargs={'slug': obj.slug})

    def lastmod(self, obj):
        return obj.published_at
