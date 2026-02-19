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

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

logger = logging.getLogger(__name__)


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
            from accounts.models import TelegramAuthCode

            # Eski ishlatilmagan kodlarni bekor qilish
            TelegramAuthCode.objects.filter(
                telegram_id=message.from_user.id,
                is_used=False,
            ).update(is_used=True)

            # Yangi 6 xonali kod
            code = str(random.randint(100000, 999999))

            # Saqlash (1 daqiqa amal qiladi)
            TelegramAuthCode.objects.create(
                telegram_id=message.from_user.id,
                telegram_username=message.from_user.username or '',
                telegram_first_name=message.from_user.first_name or '',
                code=code,
                expires_at=timezone.now() + timedelta(minutes=1),
            )

            await message.answer(
                f"<b>TestMakon.uz</b>\n\n"
                f"Sizning kodingiz:\n\n"
                f"<code>{code}</code>\n\n"
                f"<i>Kodni saytga kiriting. 1 daqiqa amal qiladi.</i>",
            )

        self.stdout.write(self.style.SUCCESS('Bot tayyor! Polling boshlandi...'))
        await dp.start_polling(bot)
