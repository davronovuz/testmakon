"""
TestMakon.uz - Subscriptions Celery Tasks
Auto-expiry va expiring-soon notification tizimi
"""

from celery import shared_task
from django.utils import timezone


@shared_task(name='subscriptions.tasks.check_all_subscriptions_expiry')
def check_all_subscriptions_expiry():
    """
    Har soatda ishlaydi.
    status='active' lekin expires_at o'tgan obunalarni expired qiladi,
    user.is_premium = False qiladi.
    """
    from .models import Subscription

    now = timezone.now()
    expired_subs = Subscription.objects.filter(
        status='active',
        expires_at__lt=now,
    ).select_related('user')

    count = 0
    for sub in expired_subs:
        sub.check_and_expire()
        count += 1

    return f'{count} ta obuna expired qilindi'


@shared_task(name='subscriptions.tasks.send_expiring_soon_notifications')
def send_expiring_soon_notifications():
    """
    Har kuni 10:00 da ishlaydi.
    3 kun ichida tugaydigan faol obunalar uchun Notification yuboradi.
    """
    from .models import Subscription
    from news.models import Notification

    now = timezone.now()
    three_days_later = now + timezone.timedelta(days=3)

    expiring = Subscription.objects.filter(
        status='active',
        expires_at__gte=now,
        expires_at__lte=three_days_later,
    ).select_related('user', 'plan')

    count = 0
    for sub in expiring:
        days = sub.days_remaining
        # Bugun allaqachon yuborilganmi — dublikat oldini olish
        already_sent = Notification.objects.filter(
            user=sub.user,
            notification_type='system',
            title__startswith='Premium muddati tugayapti',
            created_at__date=now.date(),
        ).exists()
        if not already_sent:
            Notification.objects.create(
                user=sub.user,
                notification_type='system',
                title=f'Premium muddati tugayapti — {days} kun qoldi!',
                message=(
                    f"{sub.plan.name} obunangiz {days} kun ichida tugaydi "
                    f"({timezone.localtime(sub.expires_at).strftime('%d.%m.%Y')}). "
                    f"Uzluksiz o'qishni davom ettirish uchun yangilang."
                ),
                link='/subscriptions/pricing/',
            )
            count += 1

    return f'{count} ta expiring-soon notification yuborildi'
