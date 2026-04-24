"""
Barcha sitemap URL'larni IndexNow orqali Yandex/Bing'ga yuborish.

Foydalanish:
    python manage.py indexnow_submit            # sitemap'dagi barcha URL'lar
    python manage.py indexnow_submit --url https://testmakon.uz/dtm-test/
"""
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from django.contrib.sitemaps.views import sitemap as sitemap_view
from core.indexnow import submit_url, submit_urls
from core.sitemaps import (
    StaticViewSitemap, SubjectSitemap, TopicSitemap,
    TestSitemap, ArticleSitemap,
)
import re


class Command(BaseCommand):
    help = 'Sitemapdagi URL\'larni IndexNow orqali Yandex/Bing\'ga yuboradi'

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='Bitta URL yuborish')
        parser.add_argument('--limit', type=int, default=0, help='URL soni (0 = barchasi)')

    def handle(self, *args, **options):
        single = options.get('url')
        if single:
            ok = submit_url(single)
            self.stdout.write(self.style.SUCCESS(f'OK: {single}') if ok else self.style.ERROR(f'XATO: {single}'))
            return

        # Sitemap'dan barcha URL'larni olib chiqish
        rf = RequestFactory()
        req = rf.get('/sitemap.xml', HTTP_HOST='testmakon.uz')
        req.META['wsgi.url_scheme'] = 'https'
        sitemaps = {
            'static': StaticViewSitemap,
            'subjects': SubjectSitemap,
            'topics': TopicSitemap,
            'tests': TestSitemap,
            'articles': ArticleSitemap,
        }
        resp = sitemap_view(req, sitemaps=sitemaps)
        if hasattr(resp, 'render'):
            resp.render()
        content = resp.content.decode('utf-8', errors='ignore')
        urls = re.findall(r'<loc>([^<]+)</loc>', content)

        limit = options.get('limit') or 0
        if limit > 0:
            urls = urls[:limit]

        self.stdout.write(f'Topildi: {len(urls)} URL, IndexNow\'ga yuborilmoqda...')
        ok = submit_urls(urls)
        if ok:
            self.stdout.write(self.style.SUCCESS(f'✅ {len(urls)} URL muvaffaqiyatli yuborildi'))
        else:
            self.stdout.write(self.style.ERROR('❌ Yuborish muvaffaqiyatsiz (log\'ga qarang)'))
