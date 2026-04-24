"""
Barcha sitemap URL'larni IndexNow orqali Yandex/Bing'ga yuborish.

Foydalanish:
    python manage.py indexnow_submit            # sitemap'dagi barcha URL'lar
    python manage.py indexnow_submit --url https://testmakon.uz/dtm-test/
"""
from django.core.management.base import BaseCommand
from django.urls import reverse
from core.indexnow import submit_url, submit_urls
from core.sitemaps import (
    StaticViewSitemap, SubjectSitemap, TopicSitemap,
    TestSitemap, ArticleSitemap,
)


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

        # Sitemap klasslarini to'g'ridan-to'g'ri chaqirib URL'larni yig'ish
        # (sitemap_view template render ishlatadi -> context processor crash)
        base = 'https://testmakon.uz'
        urls = []
        for sm_class in [StaticViewSitemap, SubjectSitemap, TopicSitemap, TestSitemap, ArticleSitemap]:
            sm = sm_class()
            for item in sm.items():
                try:
                    loc = sm.location(item) if callable(sm.location) else sm.location
                    if loc:
                        urls.append(f'{base}{loc}')
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'skip: {e}'))

        limit = options.get('limit') or 0
        if limit > 0:
            urls = urls[:limit]

        self.stdout.write(f'Topildi: {len(urls)} URL, IndexNow\'ga yuborilmoqda...')
        ok = submit_urls(urls)
        if ok:
            self.stdout.write(self.style.SUCCESS(f'✅ {len(urls)} URL muvaffaqiyatli yuborildi'))
        else:
            self.stdout.write(self.style.ERROR('❌ Yuborish muvaffaqiyatsiz (log\'ga qarang)'))
