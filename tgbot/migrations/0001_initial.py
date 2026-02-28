from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TelegramUser',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('telegram_id', models.BigIntegerField(db_index=True, unique=True, verbose_name='Telegram ID')),
                ('username', models.CharField(blank=True, max_length=100, verbose_name='Username')),
                ('first_name', models.CharField(blank=True, max_length=100, verbose_name='Ism')),
                ('last_name', models.CharField(blank=True, max_length=100, verbose_name='Familiya')),
                ('language_code', models.CharField(blank=True, max_length=10, verbose_name='Til kodi')),
                ('is_active', models.BooleanField(default=True, verbose_name='Faol')),
                ('joined_at', models.DateTimeField(auto_now_add=True, verbose_name="Qo'shilgan")),
                ('last_activity', models.DateTimeField(auto_now=True, verbose_name='Oxirgi faollik')),
                ('site_user', models.OneToOneField(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='telegram_profile',
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Sayt useri',
                )),
            ],
            options={
                'verbose_name': 'Telegram foydalanuvchi',
                'verbose_name_plural': 'Telegram foydalanuvchilar',
                'ordering': ['-joined_at'],
            },
        ),
        migrations.CreateModel(
            name='TelegramBroadcast',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200, verbose_name='Sarlavha (admin uchun)')),
                ('message', models.TextField(verbose_name='Xabar matni')),
                ('image', models.ImageField(blank=True, null=True, upload_to='broadcasts/', verbose_name='Rasm (ixtiyoriy)')),
                ('button_text', models.CharField(blank=True, max_length=100, verbose_name='Tugma matni')),
                ('button_url', models.URLField(blank=True, verbose_name='Tugma URL')),
                ('status', models.CharField(
                    choices=[('draft', 'Qoralama'), ('running', 'Yuborilmoqda'), ('done', 'Tugallandi'), ('cancelled', 'Bekor qilindi')],
                    default='draft', max_length=20, verbose_name='Holat',
                )),
                ('total_users', models.PositiveIntegerField(default=0, verbose_name='Jami yuboriladi')),
                ('sent_count', models.PositiveIntegerField(default=0, verbose_name='Yuborildi')),
                ('failed_count', models.PositiveIntegerField(default=0, verbose_name='Xato')),
                ('celery_task_id', models.CharField(blank=True, max_length=150, verbose_name='Celery Task ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Yaratildi')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Boshlandi')),
                ('finished_at', models.DateTimeField(blank=True, null=True, verbose_name='Tugadi')),
                ('created_by', models.ForeignKey(
                    blank=True, null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    to=settings.AUTH_USER_MODEL,
                    verbose_name='Yaratdi',
                )),
            ],
            options={
                'verbose_name': 'Broadcast',
                'verbose_name_plural': 'Broadcastlar',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='TelegramBroadcastLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(
                    choices=[('pending', 'Kutmoqda'), ('sent', 'Yuborildi'), ('failed', 'Xato')],
                    default='pending', max_length=20, verbose_name='Holat',
                )),
                ('error_text', models.CharField(blank=True, max_length=500, verbose_name='Xato matni')),
                ('sent_at', models.DateTimeField(blank=True, null=True, verbose_name='Yuborilgan vaqt')),
                ('broadcast', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='logs',
                    to='tgbot.telegrambroadcast',
                    verbose_name='Broadcast',
                )),
                ('telegram_user', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='broadcast_logs',
                    to='tgbot.telegramuser',
                    verbose_name='Telegram user',
                )),
            ],
            options={
                'verbose_name': 'Yuborish jurnali',
                'verbose_name_plural': 'Yuborish jurnali',
                'ordering': ['-sent_at'],
                'unique_together': {('broadcast', 'telegram_user')},
            },
        ),
    ]
