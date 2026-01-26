# core/context_processors.py

from django.utils import timezone


def system_banners(request):
    """Faol bannerlarni har sahifaga yuborish"""
    from news.models import SystemBanner

    now = timezone.now()

    banners = SystemBanner.objects.filter(
        is_active=True
    ).filter(
        start_date__isnull=True
    ) | SystemBanner.objects.filter(
        is_active=True,
        start_date__lte=now
    )

    banners = banners.filter(
        end_date__isnull=True
    ) | banners.filter(
        end_date__gte=now
    )

    banners = banners.distinct().order_by('order')

    return {
        'system_banners': banners
    }