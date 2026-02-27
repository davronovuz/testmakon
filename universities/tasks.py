"""
Universities Celery Tasks
- Universitetlar statistikasini Redis'da cache'lash
- Har soatda yangilash
"""
from celery import shared_task
from django.core.cache import cache
from django.db.models import Count


@shared_task(bind=True, name='universities.cache_university_stats')
def cache_university_stats(self):
    """
    Barcha universitetlar uchun yo'nalishlar sonini hisoblash va Redis'da saqlash.
    Celery Beat: har soatda bir marta.
    """
    try:
        from universities.models import University
        unis = University.objects.filter(is_active=True).annotate(
            dir_count=Count('directions', distinct=True)
        ).values('id', 'dir_count')

        stats = {u['id']: u['dir_count'] for u in unis}
        cache.set('uni_dir_counts', stats, 3600 * 2)  # 2 soat

        # Cache version'ni reset qilish (uni list cache invalid bo'ladi)
        cache.delete_pattern('testmakon:unis_list_*')

        return f"{len(stats)} ta universitetlar statistikasi yangilandi"
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@shared_task(name='universities.invalidate_unis_cache')
def invalidate_unis_cache():
    """Universitetlar list cache'ini tozalash (ma'lumot o'zgarganda chaqirish)."""
    try:
        cache.delete_pattern('testmakon:unis_list_*')
    except Exception:
        # Agar delete_pattern ishlamasa (memory cache), version o'zgartirish
        v = cache.get('unis_cache_v', 1)
        cache.set('unis_cache_v', v + 1, 86400)
