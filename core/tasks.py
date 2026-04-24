"""
Core Celery tasks.
"""
from celery import shared_task


@shared_task(name='core.indexnow_submit_task', ignore_result=True)
def indexnow_submit_task(url):
    """IndexNow'ga URL yuborish — background'da, HTTP request-cycle'ni bloklamaydi."""
    from core.indexnow import submit_url
    submit_url(url)
