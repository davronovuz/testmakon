"""
TestMakon.uz — Telegram Bot Webhook
Telegram /start → TelegramUser yaratish/yangilash
"""
import json
import logging

from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings

from .models import TelegramUser

logger = logging.getLogger('tgbot')


def _tg_send(chat_id, text, parse_mode='HTML'):
    """Bot nomidan xabar yuborish (webhook ichida sinxron)."""
    import requests
    token = settings.TELEGRAM_BOT_TOKEN
    try:
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode},
            timeout=10,
        )
    except Exception as exc:
        logger.warning(f'Welcome xabar xatosi: {exc}')


@csrf_exempt
@require_POST
def webhook(request, token):
    """Telegram webhook endpoint. URL: /tgbot/webhook/<TOKEN>/"""
    if token != settings.TELEGRAM_BOT_TOKEN:
        return HttpResponseForbidden('Invalid token')

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Invalid JSON'}, status=400)

    # Message yoki channel_post
    message = data.get('message') or data.get('channel_post')
    if not message:
        return JsonResponse({'ok': True})  # callback_query etc — ignore

    chat    = message.get('chat', {})
    from_u  = message.get('from', {})
    chat_id = chat.get('id')
    text    = message.get('text', '')

    if not chat_id or chat.get('type') != 'private':
        return JsonResponse({'ok': True})  # Faqat private chat

    tg_id   = from_u.get('id', chat_id)
    uname   = from_u.get('username', '')
    fname   = from_u.get('first_name', '')
    lname   = from_u.get('last_name', '')
    lang    = from_u.get('language_code', '')

    # TelegramUser yaratish yoki yangilash
    user, created = TelegramUser.objects.update_or_create(
        telegram_id=tg_id,
        defaults={
            'username':      uname,
            'first_name':    fname,
            'last_name':     lname,
            'language_code': lang,
            'is_active':     True,
        }
    )

    # /start buyrug'i
    if text.startswith('/start'):
        welcome = getattr(settings, 'TELEGRAM_WELCOME_MESSAGE',
            f'👋 Salom, <b>{fname or "Do\'st"}</b>!\n\n'
            f'TestMakon.uz botiga xush kelibsiz. '
            f'Saytimizga o\'ting: <a href="https://testmakon.uz">testmakon.uz</a>'
        )
        _tg_send(chat_id, welcome)
        if created:
            logger.info(f'Yangi Telegram user: @{uname or tg_id}')

    return JsonResponse({'ok': True})
