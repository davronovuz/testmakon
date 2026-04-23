"""
TestMakon Telegram Bot — aiogram 3 long-polling.

Funksiyalari:
  • /start — 6 xonali login kod yuborish (user uchun)
  • /result, /streak, /weaktest — sayt user natijalari
  • /admin, /stats, /users, /top — admin statistikasi
  • /broadcast — admin reklama yuborish (FSM orqali matn + tasdiqlash)
  • /bc_status, /bc_stop_<id> — broadcast monitoring
"""

import asyncio
import random
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone

from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command as CmdFilter
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Message,
)

logger = logging.getLogger(__name__)


# ═════════════════════════════════════════════════════════
# LOGIN CODE (user uchun)
# ═════════════════════════════════════════════════════════

async def generate_and_send_code(telegram_user):
    """6 xonali login kod generatsiya qilib text + markup qaytaradi."""
    from accounts.models import TelegramAuthCode

    # Eski ishlatilmagan kodlarni bekor qilish
    await sync_to_async(
        TelegramAuthCode.objects.filter(
            telegram_id=telegram_user.id,
            is_used=False,
        ).update
    )(is_used=True)

    code = str(random.randint(100000, 999999))

    await sync_to_async(TelegramAuthCode.objects.create)(
        telegram_id=telegram_user.id,
        telegram_username=telegram_user.username or '',
        telegram_first_name=telegram_user.first_name or '',
        code=code,
        expires_at=timezone.now() + timedelta(minutes=5),
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangi kod olish", callback_data="new_code")]
    ])

    text = (
        f"<b>TestMakon.uz</b>\n\n"
        f"Sizning kodingiz:\n\n"
        f"<code>{code}</code>\n\n"
        f"<i>Kodni saytga kiriting. 5 daqiqa amal qiladi.</i>"
    )
    return text, keyboard


# ═════════════════════════════════════════════════════════
# ADMIN HELPERS
# ═════════════════════════════════════════════════════════

ADMIN_STATE_KEY = 'tgbot:admin_state:{tg_id}'
ADMIN_STATE_TTL = 600

STATE_WAIT_BC_TEXT = 'wait_bc_text'


def is_admin(tg_id):
    return tg_id in getattr(settings, 'TELEGRAM_ADMIN_IDS', [])


def _set_state(tg_id, state, data=None):
    cache.set(ADMIN_STATE_KEY.format(tg_id=tg_id),
              {'state': state, 'data': data or {}}, ADMIN_STATE_TTL)


def _get_state(tg_id):
    return cache.get(ADMIN_STATE_KEY.format(tg_id=tg_id))


def _clear_state(tg_id):
    cache.delete(ADMIN_STATE_KEY.format(tg_id=tg_id))


# ═════════════════════════════════════════════════════════
# ADMIN — STATISTIKA (sync funksiyalar)
# ═════════════════════════════════════════════════════════

def _build_stats_text():
    from accounts.models import User
    from tests_app.models import TestAttempt
    from tgbot.models import TelegramUser

    today = timezone.localdate()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

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
        created_at__date=today, status='completed'
    ).count()
    tests_week = TestAttempt.objects.filter(
        created_at__date__gte=week_ago, status='completed'
    ).count()

    tg_bot_users = TelegramUser.objects.filter(is_active=True).count()

    return (
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


def _build_users_list():
    from accounts.models import User
    users = list(User.objects.order_by('-date_joined')[:10])
    if not users:
        return "👤 Userlar yo'q"

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
    return "\n".join(lines)


def _build_top_users():
    from accounts.models import User
    users = list(User.objects.order_by('-xp_points')[:10])
    if not users:
        return "🏆 Userlar yo'q"

    lines = ["🏆 <b>TOP 10 — XP reyting:</b>\n"]
    medals = ['🥇', '🥈', '🥉'] + [f'{i}.' for i in range(4, 11)]
    for i, u in enumerate(users):
        name = f"{u.first_name or ''} {u.last_name or ''}".strip() or "User"
        lines.append(
            f"{medals[i]} <b>{name}</b>\n"
            f"   ⚡ {u.xp_points} XP | 🔥 {u.current_streak} streak"
        )
    return "\n".join(lines)


def _build_broadcasts_list():
    from tgbot.models import TelegramBroadcast
    bcs = list(TelegramBroadcast.objects.order_by('-created_at')[:5])
    if not bcs:
        return "📭 Broadcastlar hali yo'q"

    status_icons = {
        'draft': '📝', 'running': '🏃',
        'done': '✅', 'cancelled': '❌',
    }
    lines = ["📢 <b>Oxirgi broadcastlar:</b>\n"]
    for bc in bcs:
        icon = status_icons.get(bc.status, '❓')
        progress = f"{bc.sent_count}/{bc.total_users}" if bc.total_users else "—"
        lines.append(
            f"{icon} <b>#{bc.id}</b> — {bc.title[:30]}\n"
            f"   📊 {progress} | ❌ {bc.failed_count}\n"
            f"   📅 {bc.created_at.strftime('%d.%m %H:%M')}"
        )
    return "\n".join(lines)


def _get_total_broadcast_recipients():
    from accounts.models import User
    return User.objects.filter(
        telegram_id__isnull=False, is_active=True
    ).count()


def _create_and_start_broadcast(admin_tg_id, text):
    from tgbot.models import TelegramBroadcast
    from tgbot.tasks import start_broadcast
    from accounts.models import User

    admin_user = User.objects.filter(telegram_id=admin_tg_id).first()
    broadcast = TelegramBroadcast.objects.create(
        title=f"Bot {timezone.now().strftime('%d.%m %H:%M')}",
        message=text,
        created_by=admin_user,
        status=TelegramBroadcast.STATUS_DRAFT,
    )
    start_broadcast.delay(broadcast.id)
    return broadcast.id


def _stop_broadcast(bc_id):
    """Returns (ok: bool, msg: str)."""
    from tgbot.models import TelegramBroadcast
    try:
        bc = TelegramBroadcast.objects.get(id=bc_id)
    except TelegramBroadcast.DoesNotExist:
        return False, f"❌ Broadcast #{bc_id} topilmadi"
    if bc.status != TelegramBroadcast.STATUS_RUNNING:
        return False, (
            f"⚠️ Broadcast #{bc_id} ishlab turgani yo'q "
            f"(holat: {bc.get_status_display()})"
        )
    bc.status = TelegramBroadcast.STATUS_CANCELLED
    bc.save(update_fields=['status'])
    return True, (
        f"⛔ Broadcast #{bc_id} to'xtatish signali yuborildi.\n"
        f"Celery keyingi batch oldidan (max 1s) to'xtaydi."
    )


# ═════════════════════════════════════════════════════════
# BOT
# ═════════════════════════════════════════════════════════

ADMIN_HELP_TEXT = (
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


class Command(BaseCommand):
    help = 'TestMakon Telegram botni ishga tushirish'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Bot ishga tushmoqda...'))
        asyncio.run(self.run_bot())

    async def run_bot(self):
        bot = Bot(
            token=settings.TELEGRAM_BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher()

        # ──────────────── USER: /start — login kod ────────────────
        @dp.message(CommandStart())
        async def start_handler(message: Message):
            text, keyboard = await generate_and_send_code(message.from_user)
            await message.answer(text, reply_markup=keyboard)

        @dp.callback_query(F.data == "new_code")
        async def new_code_handler(callback: CallbackQuery):
            text, keyboard = await generate_and_send_code(callback.from_user)
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer("Yangi kod yuborildi!")

        # ──────────────── ADMIN: /admin — yordam ────────────────
        @dp.message(CmdFilter('admin', 'help_admin'))
        async def admin_help_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            await message.answer(ADMIN_HELP_TEXT)

        # ──────────────── ADMIN: /stats ────────────────
        @dp.message(CmdFilter('stats'))
        async def stats_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            try:
                text = await sync_to_async(_build_stats_text)()
                await message.answer(text)
            except Exception as exc:
                logger.error(f'/stats xato: {exc}')
                await message.answer(f"❌ Statistika xatosi: {exc}")

        # ──────────────── ADMIN: /users ────────────────
        @dp.message(CmdFilter('users'))
        async def users_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            try:
                text = await sync_to_async(_build_users_list)()
                await message.answer(text)
            except Exception as exc:
                logger.error(f'/users xato: {exc}')
                await message.answer(f"❌ Xato: {exc}")

        # ──────────────── ADMIN: /top ────────────────
        @dp.message(CmdFilter('top'))
        async def top_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            try:
                text = await sync_to_async(_build_top_users)()
                await message.answer(text)
            except Exception as exc:
                logger.error(f'/top xato: {exc}')
                await message.answer(f"❌ Xato: {exc}")

        # ──────────────── ADMIN: /broadcast ────────────────
        @dp.message(CmdFilter('broadcast'))
        async def broadcast_start_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            await sync_to_async(_set_state)(message.from_user.id, STATE_WAIT_BC_TEXT)
            await message.answer(
                "📢 <b>Reklama yuborish rejimi</b>\n\n"
                "Yuboriladigan matnni bitta xabar bilan yuboring.\n\n"
                "<b>HTML teglar qo'llab-quvvatlanadi:</b>\n"
                "• <code>&lt;b&gt;qalin&lt;/b&gt;</code>\n"
                "• <code>&lt;i&gt;kursiv&lt;/i&gt;</code>\n"
                "• <code>&lt;a href=\"URL\"&gt;matn&lt;/a&gt;</code>\n\n"
                "❌ Bekor: /cancel"
            )

        # ──────────────── ADMIN: /bc_status ────────────────
        @dp.message(CmdFilter('bc_status'))
        async def bc_status_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            try:
                text = await sync_to_async(_build_broadcasts_list)()
                await message.answer(text)
            except Exception as exc:
                logger.error(f'/bc_status xato: {exc}')
                await message.answer(f"❌ Xato: {exc}")

        # ──────────────── ADMIN: /bc_stop_<id> ────────────────
        @dp.message(F.text.startswith('/bc_stop_'))
        async def bc_stop_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            try:
                bc_id = int(message.text.replace('/bc_stop_', '').strip())
            except ValueError:
                await message.answer("❌ Noto'g'ri format: /bc_stop_<raqam>")
                return
            _, msg = await sync_to_async(_stop_broadcast)(bc_id)
            await message.answer(msg)

        # ──────────────── ADMIN: /cancel ────────────────
        @dp.message(CmdFilter('cancel'))
        async def cancel_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            await sync_to_async(_clear_state)(message.from_user.id)
            await message.answer("❌ Bekor qilindi")

        # ──────────────── Broadcast matnini qabul qilish ────────────────
        # Admin /broadcast bosgandan keyin, oddiy matn yuborsa — preview
        @dp.message(F.text & ~F.text.startswith('/'))
        async def broadcast_text_handler(message: Message):
            if not is_admin(message.from_user.id):
                return
            state = await sync_to_async(_get_state)(message.from_user.id)
            if not state or state.get('state') != STATE_WAIT_BC_TEXT:
                return
            if state.get('data', {}).get('text'):
                # Allaqachon matn bor, tasdiqlash kutmoqda
                return

            text = message.text
            total = await sync_to_async(_get_total_broadcast_recipients)()

            await sync_to_async(_set_state)(
                message.from_user.id, STATE_WAIT_BC_TEXT,
                {'text': text, 'total': total}
            )

            preview = text[:500] + ('...' if len(text) > 500 else '')
            est_seconds = total // 25 + 2
            est_text = f"{est_seconds} soniya" if est_seconds < 60 else f"{est_seconds // 60} daqiqa"

            kb = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text='✅ Yuborish', callback_data='bc:confirm'),
                InlineKeyboardButton(text='❌ Bekor', callback_data='bc:cancel'),
            ]])
            await message.answer(
                f"📝 <b>Matn:</b>\n\n{preview}\n\n"
                f"━━━━━━━━━━━━━━━━━━━\n"
                f"👥 Jami yuboriladi: <b>{total}</b> user\n"
                f"⏱ Taxminiy vaqt: ~{est_text}\n\n"
                f"Tasdiqlaysizmi?",
                reply_markup=kb,
            )

        # ──────────────── Callback: broadcast tasdiq/bekor ────────────────
        @dp.callback_query(F.data == 'bc:confirm')
        async def bc_confirm_cb(cb: CallbackQuery):
            tg_id = cb.from_user.id
            if not is_admin(tg_id):
                await cb.answer("Ruxsat yo'q")
                return

            state = await sync_to_async(_get_state)(tg_id)
            if not state or state.get('state') != STATE_WAIT_BC_TEXT:
                await cb.answer("Sessiya tugagan")
                await cb.message.answer("⚠️ Sessiya eskirgan. /broadcast bilan qayta boshlang.")
                return

            text = state.get('data', {}).get('text', '').strip()
            if not text:
                await cb.answer("Matn yo'q")
                return

            bc_id = await sync_to_async(_create_and_start_broadcast)(tg_id, text)
            await sync_to_async(_clear_state)(tg_id)

            await cb.answer("Ishga tushirilmoqda...")
            await cb.message.edit_reply_markup(reply_markup=None)
            await cb.message.answer(
                f"✅ <b>Broadcast #{bc_id} ishga tushdi!</b>\n\n"
                f"📊 Holat: /bc_status\n"
                f"⛔ To'xtatish: /bc_stop_{bc_id}"
            )

        @dp.callback_query(F.data == 'bc:cancel')
        async def bc_cancel_cb(cb: CallbackQuery):
            tg_id = cb.from_user.id
            if not is_admin(tg_id):
                await cb.answer("Ruxsat yo'q")
                return
            await sync_to_async(_clear_state)(tg_id)
            await cb.answer("Bekor qilindi")
            await cb.message.edit_reply_markup(reply_markup=None)
            await cb.message.answer("❌ Broadcast bekor qilindi")

        self.stdout.write(self.style.SUCCESS('Bot tayyor! Polling boshlandi...'))
        await dp.start_polling(bot)
