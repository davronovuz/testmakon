"""
TestMakon.uz — Telegram bot admin buyruqlari.

Faqat settings.TELEGRAM_ADMIN_IDS ro'yxatidagi foydalanuvchilar ishlata oladi.
Admin state Redis cache-da saqlanadi (TTL 10 daqiqa) — webhook so'rovlari
orasidagi dialog uzluksizligi uchun.
"""
import logging
from datetime import timedelta

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger('tgbot')

ADMIN_STATE_KEY = 'tgbot:admin_state:{tg_id}'
ADMIN_STATE_TTL = 600  # 10 daqiqa

# Admin dialog holatlari
STATE_WAITING_BROADCAST_TEXT = 'wait_bc_text'


def is_admin(tg_id):
    """TG ID admin ro'yxatidami?"""
    return tg_id in getattr(settings, 'TELEGRAM_ADMIN_IDS', [])


def set_state(tg_id, state, data=None):
    cache.set(
        ADMIN_STATE_KEY.format(tg_id=tg_id),
        {'state': state, 'data': data or {}},
        ADMIN_STATE_TTL,
    )


def get_state(tg_id):
    return cache.get(ADMIN_STATE_KEY.format(tg_id=tg_id))


def clear_state(tg_id):
    cache.delete(ADMIN_STATE_KEY.format(tg_id=tg_id))


# ════════════════════════════════════════════════════════
# STATISTIKA
# ════════════════════════════════════════════════════════

def handle_stats(chat_id, _send):
    """/stats — umumiy sayt statistikasi."""
    from accounts.models import User
    from tests_app.models import TestAttempt
    from tgbot.models import TelegramBroadcast, TelegramUser

    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    try:
        total_users = User.objects.count()
        new_today = User.objects.filter(date_joined__date=today).count()
        new_week = User.objects.filter(date_joined__date__gte=week_ago).count()
        new_month = User.objects.filter(date_joined__date__gte=month_ago).count()

        active_today = User.objects.filter(last_activity_date=today).count()
        active_week = User.objects.filter(last_activity_date__gte=week_ago).count()

        premium = User.objects.filter(is_premium=True).count()
        with_tg = User.objects.filter(telegram_id__isnull=False, is_active=True).count()
        with_google = User.objects.filter(google_id__isnull=False).count()

        tests_today = TestAttempt.objects.filter(
            started_at__date=today, status='completed'
        ).count()
        tests_week = TestAttempt.objects.filter(
            started_at__date__gte=week_ago, status='completed'
        ).count()

        tg_bot_users = TelegramUser.objects.filter(is_active=True).count()

        text = (
            "📊 <b>TestMakon statistikasi</b>\n\n"
            f"👥 <b>Userlar ({total_users})</b>\n"
            f"  • Bugun: <b>+{new_today}</b>\n"
            f"  • 7 kun: <b>+{new_week}</b>\n"
            f"  • 30 kun: <b>+{new_month}</b>\n\n"
            f"🔥 <b>Faollik</b>\n"
            f"  • Bugun online: <b>{active_today}</b>\n"
            f"  • 7 kun ichida: <b>{active_week}</b>\n\n"
            f"📝 <b>Testlar</b>\n"
            f"  • Bugun ishlandi: <b>{tests_today}</b>\n"
            f"  • 7 kun: <b>{tests_week}</b>\n\n"
            f"💎 <b>Premium:</b> {premium}\n"
            f"🔗 <b>Telegram ulangan:</b> {with_tg}\n"
            f"🔗 <b>Google ulangan:</b> {with_google}\n"
            f"🤖 <b>Bot foydalanuvchilar:</b> {tg_bot_users}\n\n"
            f"📅 {today.strftime('%d.%m.%Y')}"
        )
        _send(chat_id, text)
    except Exception as exc:
        logger.error(f'handle_stats xato: {exc}')
        _send(chat_id, f"❌ Statistika olishda xato: {exc}")


def handle_users_list(chat_id, _send):
    """/users — oxirgi 10 ta ro'yxatdan o'tgan user."""
    from accounts.models import User
    try:
        users = list(User.objects.order_by('-date_joined')[:10])
        if not users:
            _send(chat_id, "👤 Userlar yo'q")
            return

        lines = ["👥 <b>Oxirgi 10 ta user:</b>\n"]
        for i, u in enumerate(users, 1):
            premium = "💎" if u.is_premium else ""
            tg = f" @{u.telegram_username}" if getattr(u, 'telegram_username', '') else ""
            google = " 🔗G" if u.google_id else ""
            name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "User"
            lines.append(
                f"{i}. {premium}<b>{name}</b>{tg}{google}\n"
                f"   📞 <code>{u.phone_number}</code>\n"
                f"   📅 {u.date_joined.strftime('%d.%m.%Y %H:%M')}"
            )
        _send(chat_id, "\n".join(lines))
    except Exception as exc:
        logger.error(f'handle_users_list xato: {exc}')
        _send(chat_id, f"❌ Xato: {exc}")


def handle_top_users(chat_id, _send):
    """/top — eng ko'p XP olgan 10 user."""
    from accounts.models import User
    try:
        users = list(User.objects.order_by('-xp_points')[:10])
        if not users:
            _send(chat_id, "🏆 Userlar yo'q")
            return

        lines = ["🏆 <b>TOP 10 — XP reyting:</b>\n"]
        medals = ['🥇', '🥈', '🥉'] + [f'{i}.' for i in range(4, 11)]
        for i, u in enumerate(users):
            name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "User"
            lines.append(
                f"{medals[i]} <b>{name}</b>\n"
                f"   ⚡ {u.xp_points} XP | 🔥 {u.current_streak} streak"
            )
        _send(chat_id, "\n".join(lines))
    except Exception as exc:
        logger.error(f'handle_top_users xato: {exc}')
        _send(chat_id, f"❌ Xato: {exc}")


# ════════════════════════════════════════════════════════
# BROADCAST
# ════════════════════════════════════════════════════════

def handle_broadcast_start(chat_id, tg_id, _send):
    """/broadcast — dialogni boshlash."""
    set_state(tg_id, STATE_WAITING_BROADCAST_TEXT)
    _send(
        chat_id,
        "📢 <b>Reklama yuborish rejimi</b>\n\n"
        "Yuboriladigan matnni bitta xabar bilan yuboring.\n\n"
        "<b>HTML teglar qo'llab-quvvatlanadi:</b>\n"
        "• <code>&lt;b&gt;qalin&lt;/b&gt;</code>\n"
        "• <code>&lt;i&gt;kursiv&lt;/i&gt;</code>\n"
        "• <code>&lt;a href=\"URL\"&gt;matn&lt;/a&gt;</code>\n\n"
        "❌ Bekor: /cancel"
    )


def handle_broadcast_text(chat_id, tg_id, text, _send):
    """Admin broadcast matnini yubordi — preview va tasdiqlash."""
    from accounts.models import User

    total = User.objects.filter(
        telegram_id__isnull=False, is_active=True
    ).count()

    # State ga matnni saqlash
    set_state(tg_id, STATE_WAITING_BROADCAST_TEXT, {
        'text': text,
        'total': total,
    })

    # Preview (500 belgi cheklov)
    preview = text[:500] + ('...' if len(text) > 500 else '')
    est_seconds = total // 25 + 2
    est_text = f"{est_seconds} soniya" if est_seconds < 60 else f"{est_seconds // 60} daqiqa"

    reply_markup = {
        'inline_keyboard': [[
            {'text': '✅ Yuborish', 'callback_data': 'bc:confirm'},
            {'text': '❌ Bekor', 'callback_data': 'bc:cancel'},
        ]]
    }
    _send(
        chat_id,
        f"📝 <b>Matn:</b>\n\n{preview}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"👥 Jami yuboriladi: <b>{total}</b> user\n"
        f"⏱ Taxminiy vaqt: ~{est_text}\n\n"
        f"Tasdiqlaysizmi?",
        reply_markup=reply_markup,
    )


def handle_broadcast_confirm(chat_id, tg_id, _send):
    """Admin tasdiqladi — broadcast Celery'ga yuboriladi."""
    state = get_state(tg_id)
    if not state or state.get('state') != STATE_WAITING_BROADCAST_TEXT:
        _send(chat_id,
            "⚠️ Sessiya eskirgan.\n/broadcast bilan qaytadan boshlang."
        )
        return

    text = state.get('data', {}).get('text', '').strip()
    if not text:
        _send(chat_id, "⚠️ Matn topilmadi. /broadcast bilan qayta urinib ko'ring.")
        return

    from tgbot.models import TelegramBroadcast
    from tgbot.tasks import start_broadcast
    from accounts.models import User

    admin_user = User.objects.filter(telegram_id=tg_id).first()

    broadcast = TelegramBroadcast.objects.create(
        title=f"Bot {timezone.now().strftime('%d.%m %H:%M')}",
        message=text,
        created_by=admin_user,
        status=TelegramBroadcast.STATUS_DRAFT,
    )

    # Celery'ga yuborish
    start_broadcast.delay(broadcast.id)
    clear_state(tg_id)

    _send(
        chat_id,
        f"✅ <b>Broadcast #{broadcast.id} ishga tushdi!</b>\n\n"
        f"📊 Status: /bc_status\n"
        f"⛔ To'xtatish: /bc_stop_{broadcast.id}"
    )


def handle_broadcast_cancel(chat_id, tg_id, _send):
    """Admin bekor qildi."""
    clear_state(tg_id)
    _send(chat_id, "❌ Broadcast bekor qilindi")


def handle_broadcasts_list(chat_id, _send):
    """/bc_status — oxirgi broadcastlar holati."""
    from tgbot.models import TelegramBroadcast
    bcs = list(TelegramBroadcast.objects.order_by('-created_at')[:5])
    if not bcs:
        _send(chat_id, "📭 Broadcastlar hali yo'q")
        return

    status_icons = {
        'draft':     '📝',
        'running':   '🏃',
        'done':      '✅',
        'cancelled': '❌',
    }

    lines = ["📢 <b>Oxirgi broadcastlar:</b>\n"]
    for bc in bcs:
        icon = status_icons.get(bc.status, '❓')
        progress = (
            f"{bc.sent_count}/{bc.total_users}"
            if bc.total_users else "—"
        )
        lines.append(
            f"{icon} <b>#{bc.id}</b> — {bc.title[:30]}\n"
            f"   📊 {progress} | ❌ {bc.failed_count}\n"
            f"   📅 {bc.created_at.strftime('%d.%m %H:%M')}"
        )
    _send(chat_id, "\n".join(lines))


def handle_broadcast_stop(chat_id, broadcast_id, _send):
    """/bc_stop_<id> — ishlab turgan broadcastni to'xtatish."""
    from tgbot.models import TelegramBroadcast
    try:
        bc = TelegramBroadcast.objects.get(id=broadcast_id)
    except TelegramBroadcast.DoesNotExist:
        _send(chat_id, f"❌ Broadcast #{broadcast_id} topilmadi")
        return

    if bc.status != TelegramBroadcast.STATUS_RUNNING:
        _send(chat_id,
            f"⚠️ Broadcast #{broadcast_id} ishlab turgani yo'q "
            f"(holat: {bc.get_status_display()})"
        )
        return

    bc.status = TelegramBroadcast.STATUS_CANCELLED
    bc.save(update_fields=['status'])
    _send(chat_id,
        f"⛔ Broadcast #{broadcast_id} to'xtatish signali yuborildi.\n"
        f"Celery keyingi batch oldidan (max 1s) to'xtaydi."
    )


# ════════════════════════════════════════════════════════
# YORDAM
# ════════════════════════════════════════════════════════

def handle_admin_help(chat_id, _send):
    """/admin — buyruqlar ro'yxati."""
    _send(chat_id,
        "🛠 <b>Admin panel</b>\n\n"
        "📊 <b>Statistika:</b>\n"
        "/stats — umumiy statistika\n"
        "/users — oxirgi 10 user\n"
        "/top — TOP 10 XP reyting\n\n"
        "📢 <b>Reklama:</b>\n"
        "/broadcast — yangi reklama yuborish\n"
        "/bc_status — oxirgi broadcastlar\n"
        "/bc_stop_&lt;id&gt; — broadcastni to'xtatish\n\n"
        "🔧 <b>Boshqa:</b>\n"
        "/cancel — joriy operatsiyani bekor qilish\n"
        "/admin — ushbu ro'yxat"
    )


# ════════════════════════════════════════════════════════
# MARKAZIY ROUTER
# ════════════════════════════════════════════════════════

def route_admin_command(cmd, chat_id, tg_id, text, _send):
    """Admin buyrug'ini tegishli handler'ga yo'naltirish.

    Returns:
        True  — buyruq admin buyrug'i sifatida qayta ishlandi
        False — bu admin buyrug'i emas, oddiy bot flow davom etsin
    """
    # State-based: broadcast matnini kutayapti
    if cmd and not cmd.startswith('/'):
        state = get_state(tg_id)
        if state and state.get('state') == STATE_WAITING_BROADCAST_TEXT \
                and not state.get('data', {}).get('text'):
            handle_broadcast_text(chat_id, tg_id, text, _send)
            return True

    if cmd == '/admin' or cmd == '/help_admin':
        handle_admin_help(chat_id, _send)
        return True

    if cmd == '/stats':
        handle_stats(chat_id, _send)
        return True

    if cmd == '/users':
        handle_users_list(chat_id, _send)
        return True

    if cmd == '/top':
        handle_top_users(chat_id, _send)
        return True

    if cmd == '/broadcast':
        handle_broadcast_start(chat_id, tg_id, _send)
        return True

    if cmd == '/bc_status':
        handle_broadcasts_list(chat_id, _send)
        return True

    if cmd.startswith('/bc_stop_'):
        try:
            bc_id = int(cmd.replace('/bc_stop_', ''))
            handle_broadcast_stop(chat_id, bc_id, _send)
            return True
        except ValueError:
            pass

    if cmd == '/cancel':
        handle_broadcast_cancel(chat_id, tg_id, _send)
        return True

    return False


def handle_callback(callback_query, _send, _answer_cb):
    """Inline tugma bosildi — Broadcast tasdiq/bekor.

    Returns True — callback qayta ishlandi.
    """
    data = callback_query.get('data', '')
    cb_id = callback_query.get('id')
    from_user = callback_query.get('from', {})
    tg_id = from_user.get('id')
    message = callback_query.get('message', {})
    chat_id = message.get('chat', {}).get('id')

    if not is_admin(tg_id):
        _answer_cb(cb_id, 'Ruxsat yo\'q')
        return True

    if data == 'bc:confirm':
        _answer_cb(cb_id, 'Ishga tushirilmoqda...')
        handle_broadcast_confirm(chat_id, tg_id, _send)
        return True

    if data == 'bc:cancel':
        _answer_cb(cb_id, 'Bekor qilindi')
        handle_broadcast_cancel(chat_id, tg_id, _send)
        return True

    return False
