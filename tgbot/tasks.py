"""
TestMakon.uz — Telegram Broadcast Celery Tasks
Sayt userlariga (telegram_id mavjud) 25 xabar/sekund tezligida yuboradi.
"""
import time
import logging
import requests

from celery import shared_task
from django.db import models as db_models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth import get_user_model

logger = logging.getLogger('tgbot')

TELEGRAM_API = 'https://api.telegram.org/bot{token}/{method}'


def _tg_call(method, payload, files=None):
    """Telegram Bot API ga so'rov yuborish."""
    token = settings.TELEGRAM_BOT_TOKEN
    url = TELEGRAM_API.format(token=token, method=method)
    try:
        if files:
            resp = requests.post(url, data=payload, files=files, timeout=15)
        else:
            resp = requests.post(url, json=payload, timeout=15)
        return resp.json()
    except Exception as exc:
        return {'ok': False, 'description': str(exc)}


def _send_to_user(chat_id, message, image_url=None, button_text='', button_url=''):
    """
    Bitta foydalanuvchiga xabar yuborish.
    Returns: (ok: bool, error_code: int|None, description: str)
    """
    reply_markup = None
    if button_text and button_url:
        reply_markup = {
            'inline_keyboard': [[{'text': button_text, 'url': button_url}]]
        }

    if image_url:
        payload = {
            'chat_id': chat_id,
            'photo': image_url,
            'caption': message,
            'parse_mode': 'HTML',
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        result = _tg_call('sendPhoto', payload)
    else:
        payload = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML',
            'disable_web_page_preview': False,
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup
        result = _tg_call('sendMessage', payload)

    ok = result.get('ok', False)
    error_code = result.get('error_code')
    description = result.get('description', '')
    return ok, error_code, description


@shared_task(bind=True, name='tgbot.start_broadcast', max_retries=0,
             soft_time_limit=3600, time_limit=3700)
def start_broadcast(self, broadcast_id):
    """
    telegram_id mavjud barcha sayt foydalanuvchilariga broadcast yuborish.

    Tezlik: 25 xabar/sekund (Telegram limiti: 30/sek).
    Jarayon: DRAFT -> RUNNING -> DONE/CANCELLED
    """
    from tgbot.models import TelegramBroadcast, TelegramBroadcastLog

    User = get_user_model()

    try:
        broadcast = TelegramBroadcast.objects.get(id=broadcast_id)
    except TelegramBroadcast.DoesNotExist:
        logger.error(f'Broadcast #{broadcast_id} topilmadi')
        return

    if broadcast.status != TelegramBroadcast.STATUS_DRAFT:
        logger.warning(f'Broadcast #{broadcast_id} draft emas: {broadcast.status}')
        return

    # telegram_id mavjud, faol sayt userlari
    users = list(
        User.objects.filter(telegram_id__isnull=False, is_active=True)
        .values_list('id', 'telegram_id')
        .order_by('id')
    )
    total = len(users)

    TelegramBroadcast.objects.filter(id=broadcast_id).update(
        status=TelegramBroadcast.STATUS_RUNNING,
        started_at=timezone.now(),
        total_users=total,
        celery_task_id=self.request.id,
    )

    if total == 0:
        TelegramBroadcast.objects.filter(id=broadcast_id).update(
            status=TelegramBroadcast.STATUS_DONE,
            finished_at=timezone.now(),
        )
        logger.info(f'Broadcast #{broadcast_id}: telegram_id li user yoq')
        return 'Telegram ID li user topilmadi'

    # Log yozuvlarini bulk yaratish
    logs = [
        TelegramBroadcastLog(
            broadcast_id=broadcast_id,
            site_user_id=uid,
            status=TelegramBroadcastLog.STATUS_PENDING,
        )
        for uid, _ in users
    ]
    TelegramBroadcastLog.objects.bulk_create(logs, ignore_conflicts=True)
    logger.info(f'Broadcast #{broadcast_id} boshlandi: {total} ta user')

    # Image URL
    image_url = None
    if broadcast.image:
        try:
            img_url = broadcast.image.url
            if img_url and not img_url.startswith('http'):
                domain = getattr(settings, 'SITE_DOMAIN', 'https://testmakon.uz')
                image_url = domain.rstrip('/') + img_url
            else:
                image_url = img_url
        except Exception:
            image_url = None

    msg      = broadcast.message
    btn_text = broadcast.button_text
    btn_url  = broadcast.button_url

    # Yuborish (25 xabar/sekund)
    BATCH_SIZE = 25
    sent_batch = failed_batch = 0

    for i, (user_id, tg_id) in enumerate(users):
        # Har 25 xabardan oldin bekor qilinganini tekshirish + rate limit
        if i % BATCH_SIZE == 0 and i > 0:
            broadcast.refresh_from_db(fields=['status'])
            if broadcast.status == TelegramBroadcast.STATUS_CANCELLED:
                TelegramBroadcastLog.objects.filter(
                    broadcast_id=broadcast_id,
                    status=TelegramBroadcastLog.STATUS_PENDING,
                ).update(
                    status=TelegramBroadcastLog.STATUS_FAILED,
                    error_text='Broadcast bekor qilindi',
                )
                pending_cnt = total - i
                TelegramBroadcast.objects.filter(id=broadcast_id).update(
                    failed_count=db_models.F('failed_count') + pending_cnt,
                )
                logger.info(f'Broadcast #{broadcast_id} bekor qilindi: {i}/{total}')
                return f'Bekor qilindi: {i} ta yuborildi, {total - i} ta qoldi'

            time.sleep(1)

            if sent_batch or failed_batch:
                TelegramBroadcast.objects.filter(id=broadcast_id).update(
                    sent_count=db_models.F('sent_count') + sent_batch,
                    failed_count=db_models.F('failed_count') + failed_batch,
                )
                sent_batch = failed_batch = 0

        ok, error_code, description = _send_to_user(
            tg_id, msg, image_url, btn_text, btn_url
        )

        if ok:
            TelegramBroadcastLog.objects.filter(
                broadcast_id=broadcast_id,
                site_user_id=user_id,
            ).update(
                status=TelegramBroadcastLog.STATUS_SENT,
                sent_at=timezone.now(),
            )
            sent_batch += 1
        else:
            # 403: user botni bloklagan, 400: chat topilmadi
            if error_code in (403, 400):
                User.objects.filter(id=user_id).update(telegram_id=None)

            err_msg = (f'[{error_code}] {description}'[:490]
                       if error_code else description[:490])
            TelegramBroadcastLog.objects.filter(
                broadcast_id=broadcast_id,
                site_user_id=user_id,
            ).update(
                status=TelegramBroadcastLog.STATUS_FAILED,
                error_text=err_msg,
            )
            failed_batch += 1

    # Oxirgi batch
    if sent_batch or failed_batch:
        TelegramBroadcast.objects.filter(id=broadcast_id).update(
            sent_count=db_models.F('sent_count') + sent_batch,
            failed_count=db_models.F('failed_count') + failed_batch,
        )

    TelegramBroadcast.objects.filter(id=broadcast_id).update(
        status=TelegramBroadcast.STATUS_DONE,
        finished_at=timezone.now(),
    )
    broadcast.refresh_from_db()
    msg_out = (f'Broadcast #{broadcast_id} tugadi: '
               f'{broadcast.sent_count} yuborildi, {broadcast.failed_count} xato')
    logger.info(msg_out)
    return msg_out
