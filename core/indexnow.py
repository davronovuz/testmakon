"""
IndexNow protokoli — Yandex/Bing/Seznam'ga yangi URL'larni darhol xabar qilish.

Protokol: https://www.indexnow.org/
API endpoint: https://api.indexnow.org/indexnow

Google IndexNow'ni qo'llab-quvvatlamaydi, lekin Yandex va Bing qo'llab
quvvatlaydi. O'zbekistonda Yandex muhim bo'lgani uchun bu kuchli foyda.

Foydalanish:
    from core.indexnow import submit_url, submit_urls
    submit_url('https://testmakon.uz/new-page/')
    submit_urls(['https://testmakon.uz/a/', 'https://testmakon.uz/b/'])
"""
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

INDEXNOW_ENDPOINT = 'https://api.indexnow.org/indexnow'
DEFAULT_KEY = '9a6c223b3f6c55377a2fc7fcda46a26d'
HOST = 'testmakon.uz'


def _get_key():
    return getattr(settings, 'INDEXNOW_KEY', DEFAULT_KEY)


def _key_location():
    return f'https://{HOST}/{_get_key()}.txt'


def submit_url(url, timeout=5):
    """Bitta URL'ni IndexNow'ga yuborish. Xato bo'lsa ham crash bo'lmaydi."""
    try:
        resp = requests.get(
            INDEXNOW_ENDPOINT,
            params={
                'url': url,
                'key': _get_key(),
                'keyLocation': _key_location(),
            },
            timeout=timeout,
        )
        if resp.status_code in (200, 202):
            logger.info("IndexNow OK %s -> %s", url, resp.status_code)
            return True
        logger.warning("IndexNow %s qaytardi %s: %s", resp.status_code, url, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("IndexNow xato %s: %s", url, e)
        return False


def submit_urls(urls, timeout=10):
    """Ko'p URL'larni bir POST so'rovida yuborish (max 10,000)."""
    if not urls:
        return False
    try:
        resp = requests.post(
            INDEXNOW_ENDPOINT,
            json={
                'host': HOST,
                'key': _get_key(),
                'keyLocation': _key_location(),
                'urlList': list(urls)[:10000],
            },
            headers={'Content-Type': 'application/json; charset=utf-8'},
            timeout=timeout,
        )
        if resp.status_code in (200, 202):
            logger.info("IndexNow batch OK (%d URL) -> %s", len(urls), resp.status_code)
            return True
        logger.warning("IndexNow batch %s: %s", resp.status_code, resp.text[:200])
        return False
    except Exception as e:
        logger.warning("IndexNow batch xato: %s", e)
        return False
