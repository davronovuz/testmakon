"""
News Signals
Notification modeliga yangi yozuv qo'shilganda WebSocket orqali
foydalanuvchining brauzeriga real-time xabar yuboradi.
Celery task, view, yoki istalgan joydan ishlaydi.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver


@receiver(post_save, sender='news.Notification')
def push_notification_via_websocket(sender, instance, created, **kwargs):
    """
    Yangi Notification yaratilganda WS orqali yuborish.
    Faqat yangi yaratilganlar — update qilinganlarda ishlamaydi.
    """
    if not created:
        return

    # icon mapping
    icon_map = {
        'system':      'gear-fill',
        'news':        'newspaper',
        'competition': 'trophy-fill',
        'battle':      'lightning-charge-fill',
        'achievement': 'award-fill',
        'friend':      'person-plus-fill',
        'reminder':    'bell-fill',
    }

    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer

        channel_layer = get_channel_layer()
        if not channel_layer:
            return

        async_to_sync(channel_layer.group_send)(
            f'user_{instance.user_id}',
            {
                'type': 'push.notification',
                'notification': {
                    'id':    instance.id,
                    'title': instance.title,
                    'message': instance.message,
                    'notification_type': instance.notification_type,
                    'icon':  icon_map.get(instance.notification_type, 'bell-fill'),
                    'link':  instance.link or '',
                    'created_at': instance.created_at.isoformat(),
                },
            }
        )
    except Exception:
        # WS ishlamasa ham notification DB da qoladi — xato chiqarmaymiz
        pass
