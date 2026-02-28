from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tgbot', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Raw SQL: eski jadvalni o'chirib, yangi tuzilma bilan qayta yaratish.
        # AlterUniqueTogether ishlatilmaydi — constraint nomi farq qilishi mumkin.
        migrations.RunSQL(
            sql="""
                DROP TABLE IF EXISTS tgbot_telegrambroadcastlog;
                CREATE TABLE tgbot_telegrambroadcastlog (
                    id          BIGSERIAL PRIMARY KEY,
                    broadcast_id BIGINT NOT NULL
                        REFERENCES tgbot_telegrambroadcast(id) ON DELETE CASCADE,
                    site_user_id BIGINT NOT NULL
                        REFERENCES accounts_user(id) ON DELETE CASCADE,
                    status      VARCHAR(20)  NOT NULL DEFAULT 'pending',
                    error_text  VARCHAR(500) NOT NULL DEFAULT '',
                    sent_at     TIMESTAMPTZ,
                    UNIQUE(broadcast_id, site_user_id)
                );
            """,
            reverse_sql="DROP TABLE IF EXISTS tgbot_telegrambroadcastlog;",
        ),

        # Django migration state ni DB bilan moslashtirish (hech qanday DB o'zgarish yo'q)
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.AlterUniqueTogether(
                    name='telegrambroadcastlog',
                    unique_together=set(),
                ),
                migrations.RemoveField(
                    model_name='telegrambroadcastlog',
                    name='telegram_user',
                ),
                migrations.AddField(
                    model_name='telegrambroadcastlog',
                    name='site_user',
                    field=models.ForeignKey(
                        default=1,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='broadcast_logs',
                        to=settings.AUTH_USER_MODEL,
                        verbose_name='Foydalanuvchi',
                    ),
                    preserve_default=False,
                ),
                migrations.AlterUniqueTogether(
                    name='telegrambroadcastlog',
                    unique_together={('broadcast', 'site_user')},
                ),
            ],
        ),
    ]
