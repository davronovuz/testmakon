"""
TestMakon.uz - Main URL Configuration
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from django.http import Http404
from core.sitemaps import StaticViewSitemap, SubjectSitemap, TopicSitemap, TestSitemap, ArticleSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'subjects': SubjectSitemap,
    'topics': TopicSitemap,
    'tests': TestSitemap,
    'articles': ArticleSitemap,
}


def _trap_admin(request):
    raise Http404


urlpatterns = [
    # Admin panel — yashirin URL (botlar /admin/ ga kelsa 404)
    path('admin/', _trap_admin),
    path('tm-admin-9x7/', admin.site.urls),

    # Apps
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('tests/', include('tests_app.urls', namespace='tests_app')),
    path('ai/', include('ai_core.urls', namespace='ai_core')),
    path('competitions/', include('competitions.urls', namespace='competitions')),
    path('universities/', include('universities.urls', namespace='universities')),
    path('news/', include('news.urls', namespace='news')),
    path('leaderboard/', include('leaderboard.urls', namespace='leaderboard')),
    path('subscriptions/', include('subscriptions.urls', namespace='subscriptions')),
    path('tgbot/', include('tgbot.urls', namespace='tgbot')),

    # SEO
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name='core/robots.txt', content_type='text/plain')),
]

# Static and Media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Custom error handlers
handler404 = 'core.views.error_404'
handler500 = 'core.views.error_500'