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

import random
from datetime import timedelta
from django.utils import timezone
from .models import TelegramUser
from accounts.models import TelegramAuthCode

logger = logging.getLogger('tgbot')


def _tg_send(chat_id, text, parse_mode='HTML', reply_markup=None):
    """Bot nomidan xabar yuborish (webhook ichida sinxron)."""
    import requests
    token = settings.TELEGRAM_BOT_TOKEN
    payload = {'chat_id': chat_id, 'text': text, 'parse_mode': parse_mode}
    if reply_markup:
        payload['reply_markup'] = reply_markup
    try:
        requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json=payload,
            timeout=10,
        )
    except Exception as exc:
        logger.warning(f'Telegram xabar xatosi: {exc}')


def _send_auth_code(chat_id, tg_id, username, first_name):
    """Autentifikatsiya kodi yaratib Telegram ga yuborish"""
    # Eski ishlatilmagan kodlarni bekor qilish
    TelegramAuthCode.objects.filter(
        telegram_id=tg_id,
        is_used=False,
    ).update(is_used=True)

    # Yangi 6 xonali kod
    code = str(random.randint(100000, 999999))

    # Saqlash (5 daqiqa amal qiladi)
    TelegramAuthCode.objects.create(
        telegram_id=tg_id,
        telegram_username=username or '',
        telegram_first_name=first_name or '',
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    _tg_send(chat_id,
        f"<b>TestMakon.uz</b>\n\n"
        f"Sizning kodingiz:\n\n"
        f"<code>{code}</code>\n\n"
        f"Kodni ilovaga kiriting. 5 daqiqa amal qiladi.\n\n"
        f"Yangi kod olish uchun /code bosing."
    )


def _get_site_user(tg_id):
    """telegram_id orqali accounts.User ni topish."""
    try:
        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.select_related('analytics_summary').get(telegram_id=tg_id)
    except Exception:
        return None


def _handle_result(chat_id, tg_id):
    """/result — predicted DTM bali + oxirgi test natijasi."""
    user = _get_site_user(tg_id)
    if not user:
        _tg_send(chat_id,
            "❌ Sizning Telegram akkauntingiz TestMakon.uz bilan bog'lanmagan.\n"
            "Saytga kiring va profilingizni Telegram bilan ulang."
        )
        return

    # DTM bashorati
    try:
        predicted = user.analytics_summary.predicted_dtm_score
        accuracy = user.analytics_summary.overall_accuracy
    except Exception:
        predicted = 0
        accuracy = 0

    # Oxirgi test
    try:
        from tests_app.models import TestAttempt
        last = TestAttempt.objects.filter(
            user=user, status='completed'
        ).select_related('test').order_by('-created_at').first()
    except Exception:
        last = None

    name = user.first_name or user.username or "O'quvchi"
    lines = [f"📊 <b>{name}ning natijalari</b>\n"]
    lines.append(f"🎯 DTM bashorat bali: <b>{predicted}/189</b>")
    lines.append(f"✅ Umumiy aniqlik: <b>{accuracy:.0f}%</b>")

    if last:
        lines.append(f"\n📝 Oxirgi test: <b>{last.test.title if last.test else 'Test'}</b>")
        lines.append(f"   Natija: <b>{last.percentage:.0f}%</b> ({last.correct_answers}/{last.total_questions})")
        lines.append(f"   Sana: {last.created_at.strftime('%d.%m.%Y')}")
    else:
        lines.append("\n📝 Hali test ishlanmagan")

    lines.append(f"\n🌐 <a href='https://testmakon.uz/ai/progress/'>Batafsil progress</a>")
    _tg_send(chat_id, "\n".join(lines))


def _handle_streak(chat_id, tg_id):
    """/streak — joriy streak + rag'batlantirish."""
    user = _get_site_user(tg_id)
    if not user:
        _tg_send(chat_id,
            "❌ Akkauntingiz bog'lanmagan. testmakon.uz ga kiring."
        )
        return

    streak = user.current_streak or 0
    longest = user.longest_streak or 0
    name = user.first_name or user.username or "O'quvchi"

    if streak == 0:
        msg = (
            f"😴 <b>{name}</b>, hozir faol streak yo'q.\n\n"
            f"Bugun testlar ishlab streakni boshlang! 🔥\n"
            f"📈 Eng uzun streak: {longest} kun\n\n"
            f"🌐 <a href='https://testmakon.uz/tests/'>Testlar</a>"
        )
    elif streak < 3:
        msg = (
            f"🔥 <b>{name}</b>, {streak} kunlik streak!\n\n"
            f"Ajoyib boshlanish! Ertaga ham davom eting. 💪\n"
            f"📈 Rekord: {longest} kun\n\n"
            f"🌐 <a href='https://testmakon.uz/tests/'>Testlar</a>"
        )
    elif streak < 7:
        msg = (
            f"🔥🔥 <b>{name}</b>, {streak} kunlik streak!\n\n"
            f"Zo'r! {7 - streak} kun qoldi — haftalik maqsadga yetasiz. 🎯\n"
            f"📈 Rekord: {longest} kun\n\n"
            f"🌐 <a href='https://testmakon.uz/tests/'>Testlar</a>"
        )
    elif streak < 30:
        msg = (
            f"🔥🔥🔥 <b>{name}</b>, {streak} kunlik streak!\n\n"
            f"Bu juda katta yutuq! DTM imtihoni bunday odamlarni kutmoqda. 🏆\n"
            f"📈 Rekord: {longest} kun\n\n"
            f"🌐 <a href='https://testmakon.uz/ai/progress/'>Progress</a>"
        )
    else:
        msg = (
            f"🏆 <b>{name}</b>, {streak} kunlik MEGA streak!\n\n"
            f"Siz haqiqiy champion! {streak} kun ketma-ket o'qish — bu kamdan-kam uchraydi!\n"
            f"📈 Rekord: {longest} kun\n\n"
            f"🌐 <a href='https://testmakon.uz/ai/progress/'>Progress</a>"
        )
    _tg_send(chat_id, msg)


def _handle_weaktest(chat_id, tg_id):
    """/weaktest — sust mavzular asosida smart test yaratib URL yuborish."""
    user = _get_site_user(tg_id)
    if not user:
        _tg_send(chat_id,
            "❌ Akkauntingiz bog'lanmagan. testmakon.uz ga kiring."
        )
        return

    _tg_send(chat_id, "⏳ AI sizning sust mavzularingizni tahlil qilyapti...")

    try:
        from ai_core.models import WeakTopicAnalysis
        from tests_app.models import Question, Test, TestQuestion, TestAttempt
        from django.utils import timezone as tz

        weak_topic_ids = list(
            WeakTopicAnalysis.objects.filter(user=user)
            .order_by('accuracy_rate')
            .values_list('topic_id', flat=True)[:5]
        )

        q_filter = Question.objects.filter(is_active=True)
        if weak_topic_ids:
            weak_qs = list(q_filter.filter(topic_id__in=weak_topic_ids).order_by('?')[:15])
            other_qs = list(q_filter.exclude(topic_id__in=weak_topic_ids).order_by('?')[:5])
            questions = (weak_qs + other_qs)[:20]
        else:
            questions = list(q_filter.order_by('?')[:20])

        if not questions:
            _tg_send(chat_id,
                "😔 Hozircha savollar topilmadi.\n"
                "Avval saytda bir necha test ishlang, keyin qayta urinib ko'ring."
            )
            return

        subject = questions[0].subject if questions else None
        test = Test.objects.create(
            title=f"AI Smart Test (Telegram)",
            slug=f"tg-smart-{user.id}-{int(tz.now().timestamp())}",
            test_type='practice',
            subject=subject,
            time_limit=len(questions) * 2,
            question_count=len(questions),
            shuffle_questions=True,
            shuffle_answers=True,
            show_correct_answers=True,
            created_by=user,
        )
        for i, q in enumerate(questions):
            TestQuestion.objects.create(test=test, question=q, order=i)

        attempt = TestAttempt.objects.create(
            user=user,
            test=test,
            total_questions=len(questions),
            status='in_progress',
        )

        domain = getattr(settings, 'SITE_DOMAIN', 'https://testmakon.uz')
        play_url = f"{domain}/tests/play/{attempt.uuid}/"

        markup = {
            'inline_keyboard': [[
                {'text': '▶️ Testni boshlash', 'url': play_url}
            ]]
        }
        name = user.first_name or user.username or "O'quvchi"
        _tg_send(
            chat_id,
            f"✅ <b>{name}</b>, {len(questions)} ta savollik AI Smart Test tayyor!\n\n"
            f"Sust mavzularingizdan tanlangan savollar. Bosing:",
            reply_markup=markup,
        )
    except Exception as exc:
        logger.error(f"_handle_weaktest xato: user={user.id}, {exc}")
        _tg_send(chat_id, "❌ Test yaratishda xatolik yuz berdi. Qayta urinib ko'ring.")


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

    cmd = text.split()[0].lower() if text else ''

    if cmd == '/start':
        # /start login — kod yaratib yuborish
        parts = text.split()
        if len(parts) > 1 and parts[1] == 'login':
            _send_auth_code(chat_id, tg_id, uname, fname)
        else:
            display_name = fname or "Do'st"
            welcome = getattr(settings, 'TELEGRAM_WELCOME_MESSAGE',
                f'👋 Salom, <b>{display_name}</b>!\n\n'
                "TestMakon.uz botiga xush kelibsiz. "
                'Saytimizga o\'ting: <a href="https://testmakon.uz">testmakon.uz</a>'
            )
            _tg_send(chat_id, welcome)
            if created:
                logger.info(f'Yangi Telegram user: @{uname or tg_id}')

    elif cmd == '/code':
        _send_auth_code(chat_id, tg_id, uname, fname)

    elif cmd == '/result':
        _handle_result(chat_id, tg_id)

    elif cmd == '/streak':
        _handle_streak(chat_id, tg_id)

    elif cmd == '/weaktest':
        _handle_weaktest(chat_id, tg_id)

    elif cmd == '/help':
        _tg_send(chat_id,
            "📚 <b>TestMakon Bot buyruqlari:</b>\n\n"
            "/start — Botni ishga tushirish\n"
            "/code — Ilovaga kirish kodi olish\n"
            "/result — DTM bashorati va oxirgi test natijasi\n"
            "/streak — Joriy streak va rekord\n"
            "/weaktest — Sust mavzulardan AI Smart Test\n"
            "/help — Buyruqlar ro'yxati\n\n"
            "🌐 <a href='https://testmakon.uz'>testmakon.uz</a>"
        )

    return JsonResponse({'ok': True})
