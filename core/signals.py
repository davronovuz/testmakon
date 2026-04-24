"""
Post-save signallar — yangi yoki o'zgartirilgan obyektni avtomatik
IndexNow'ga yuborish (Yandex/Bing tezkor indekslash).
"""
import re
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse, NoReverseMatch

logger = logging.getLogger(__name__)

_SAFE_SLUG_RE = re.compile(r'^[-a-zA-Z0-9_]+$')


def _is_safe_slug(slug):
    return bool(slug) and bool(_SAFE_SLUG_RE.match(slug))


def _submit_later(url):
    """IndexNow — Celery background task orqali, request-cycle'ni bloklamaydi."""
    full_url = f'https://testmakon.uz{url}'
    try:
        from core.tasks import indexnow_submit_task
        indexnow_submit_task.delay(full_url)
    except Exception as e:
        # Celery down bo'lsa, sync chaqirib ham ko'ramiz
        logger.warning("IndexNow celery xato (%s), sync chaqiruvga o'tamiz", e)
        try:
            from core.indexnow import submit_url
            submit_url(full_url)
        except Exception as e2:
            logger.warning("IndexNow sync ham xato: %s", e2)


@receiver(post_save, sender='tests_app.Subject')
def subject_saved(sender, instance, created, **kwargs):
    if not instance.is_active or not _is_safe_slug(instance.slug):
        return
    try:
        url = reverse('tests_app:practice_subject', kwargs={'subject_slug': instance.slug})
        _submit_later(url)
    except NoReverseMatch:
        pass


@receiver(post_save, sender='tests_app.Topic')
def topic_saved(sender, instance, created, **kwargs):
    if not instance.is_active or not _is_safe_slug(instance.slug):
        return
    if not instance.subject or not _is_safe_slug(instance.subject.slug):
        return
    try:
        url = reverse('tests_app:practice_topic', kwargs={
            'subject_slug': instance.subject.slug,
            'topic_slug': instance.slug,
        })
        _submit_later(url)
    except NoReverseMatch:
        pass


@receiver(post_save, sender='tests_app.Test')
def test_saved(sender, instance, created, **kwargs):
    if not instance.is_active or not _is_safe_slug(instance.slug):
        return
    try:
        url = reverse('tests_app:test_detail', kwargs={'slug': instance.slug})
        _submit_later(url)
    except NoReverseMatch:
        pass


@receiver(post_save, sender='news.Article')
def article_saved(sender, instance, created, **kwargs):
    if not instance.is_published or not _is_safe_slug(instance.slug):
        return
    try:
        url = reverse('news:article_detail', kwargs={'slug': instance.slug})
        _submit_later(url)
    except NoReverseMatch:
        pass
