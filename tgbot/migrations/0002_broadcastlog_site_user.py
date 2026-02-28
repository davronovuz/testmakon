from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # 1. Eski log yozuvlarini tozalash (telegram_user FK bilan, eski data)
        migrations.RunSQL(
            "DELETE FROM tgbot_telegrambroadcastlog;",
            reverse_sql=migrations.RunSQL.noop,
        ),
        # 2. Eski unique_together ni olib tashlash
        migrations.AlterUniqueTogether(
            name='telegrambroadcastlog',
            unique_together=set(),
        ),
        # 3. Eski telegram_user FK ni olib tashlash
        migrations.RemoveField(
            model_name='telegrambroadcastlog',
            name='telegram_user',
        ),
        # 4. Yangi site_user FK qo'shish (accounts.User ga)
        migrations.AddField(
            model_name='telegrambroadcastlog',
            name='site_user',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='broadcast_logs',
                to=settings.AUTH_USER_MODEL,
                verbose_name='Foydalanuvchi',
                # Mavjud (bo'sh) jadval uchun vaqtinchalik default
                default=1,
                preserve_default=False,
            ),
        ),
        # 5. Yangi unique_together
        migrations.AlterUniqueTogether(
            name='telegrambroadcastlog',
            unique_together={('broadcast', 'site_user')},
        ),
    ]
