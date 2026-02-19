"""
TestMakon Telegram Bot - Autentifikatsiya uchun kod yuboradi
Ishga tushirish: python manage.py run_bot
"""

import asyncio
import random
import logging

from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from asgiref.sync import sync_to_async

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

logger = logging.getLogger(__name__)


async def generate_and_send_code(telegram_user, bot_message_or_callback):
    """Kod generatsiya qilib yuborish"""
    from accounts.models import TelegramAuthCode

    # Eski ishlatilmagan kodlarni bekor qilish
    await sync_to_async(
        TelegramAuthCode.objects.filter(
            telegram_id=telegram_user.id,
            is_used=False,
        ).update
    )(is_used=True)

    # Yangi 6 xonali kod
    code = str(random.randint(100000, 999999))

    # Saqlash (1 daqiqa amal qiladi)
    await sync_to_async(TelegramAuthCode.objects.create)(
        telegram_id=telegram_user.id,
        telegram_username=telegram_user.username or '',
        telegram_first_name=telegram_user.first_name or '',
        code=code,
        expires_at=timezone.now() + timedelta(minutes=1),
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Yangi kod olish", callback_data="new_code")]
    ])

    text = (
        f"<b>TestMakon.uz</b>\n\n"
        f"Sizning kodingiz:\n\n"
        f"<code>{code}</code>\n\n"
        f"<i>Kodni saytga kiriting. 1 daqiqa amal qiladi.</i>"
    )

    return text, keyboard


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

        @dp.message(CommandStart())
        async def start_handler(message: types.Message):
            text, keyboard = await generate_and_send_code(message.from_user, message)
            await message.answer(text, reply_markup=keyboard)

        @dp.callback_query(F.data == "new_code")
        async def new_code_handler(callback: CallbackQuery):
            text, keyboard = await generate_and_send_code(callback.from_user, callback)
            await callback.message.edit_text(text, reply_markup=keyboard)
            await callback.answer("Yangi kod yuborildi!")

        self.stdout.write(self.style.SUCCESS('Bot tayyor! Polling boshlandi...'))
        await dp.start_polling(bot)
