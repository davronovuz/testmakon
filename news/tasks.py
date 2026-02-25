from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def send_bulk_notifications(self, user_ids, title, message, notification_type, link=''):
    """
    Barcha foydalanuvchilarga bildirishnoma yuborish.
    Admin paneldan chaqirilganda request ni bloklamas — background'da ishlaydi.
    """
    from news.models import Notification

    try:
        users_chunk = user_ids  # list of IDs
        notifs = [
            Notification(
                user_id=uid,
                title=title,
                message=message,
                notification_type=notification_type,
                link=link or '',
            )
            for uid in users_chunk
        ]
        Notification.objects.bulk_create(notifs, batch_size=500, ignore_conflicts=True)
        logger.info(f"Bulk notification yuborildi: {len(notifs)} ta")
    except Exception as exc:
        logger.error(f"send_bulk_notifications xato: {exc}")
        raise self.retry(exc=exc, countdown=30)
