"""
TestMakon.uz — Telegram Bot Models
TelegramUser, TelegramBroadcast, TelegramBroadcastLog
"""
from django.db import models
from django.conf import settings


class TelegramUser(models.Model):
    """Bot orqali ro'yxatdan o'tgan Telegram foydalanuvchilari."""

    telegram_id   = models.BigIntegerField('Telegram ID', unique=True, db_index=True)
    username      = models.CharField('Username', max_length=100, blank=True)
    first_name    = models.CharField('Ism', max_length=100, blank=True)
    last_name     = models.CharField('Familiya', max_length=100, blank=True)
    language_code = models.CharField('Til kodi', max_length=10, blank=True)

    is_active = models.BooleanField(
        'Faol', default=True,
        help_text='False: foydalanuvchi botni bloklagan yoki o\'chirilgan'
    )

    # Sayt useri bilan bog'lanish (ixtiyoriy)
    site_user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name='telegram_profile',
        verbose_name='Sayt useri'
    )

    joined_at     = models.DateTimeField('Qo\'shilgan', auto_now_add=True)
    last_activity = models.DateTimeField('Oxirgi faollik', auto_now=True)

    class Meta:
        verbose_name = 'Telegram foydalanuvchi'
        verbose_name_plural = 'Telegram foydalanuvchilar'
        ordering = ['-joined_at']

    def __str__(self):
        if self.username:
            return f'@{self.username}'
        return f'{self.first_name or "User"} (ID: {self.telegram_id})'

    @property
    def full_name(self):
        return f'{self.first_name} {self.last_name}'.strip() or f'ID:{self.telegram_id}'

    @property
    def tg_url(self):
        if self.username:
            return f'https://t.me/{self.username}'
        return f'tg://user?id={self.telegram_id}'


class TelegramBroadcast(models.Model):
    """Admin paneldan Telegram foydalanuvchilariga yuborish uchun xabar."""

    STATUS_DRAFT     = 'draft'
    STATUS_RUNNING   = 'running'
    STATUS_DONE      = 'done'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT,     'Qoralama'),
        (STATUS_RUNNING,   'Yuborilmoqda'),
        (STATUS_DONE,      'Tugallandi'),
        (STATUS_CANCELLED, 'Bekor qilindi'),
    ]

    title   = models.CharField(
        'Sarlavha (admin uchun)', max_length=200,
        help_text='Bu nom faqat admin panelda ko\'rinadi, foydalanuvchiga ketmaydi'
    )
    message = models.TextField(
        'Xabar matni',
        help_text='HTML: <b>qalin</b>, <i>kursiv</i>, <a href="...">havola</a>, <code>kod</code>'
    )
    image = models.ImageField(
        'Rasm (ixtiyoriy)', upload_to='broadcasts/',
        blank=True, null=True,
        help_text='Rasm yuborilsa caption sifatida xabar matni ishlatiladi'
    )

    # Inline tugma
    button_text = models.CharField('Tugma matni', max_length=100, blank=True)
    button_url  = models.URLField('Tugma URL', blank=True)

    # Holat
    status = models.CharField(
        'Holat', max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT
    )

    # Statistika (atomik yangilanadi)
    total_users  = models.PositiveIntegerField('Jami yuboriladi', default=0)
    sent_count   = models.PositiveIntegerField('Yuborildi', default=0)
    failed_count = models.PositiveIntegerField('Xato', default=0)

    # Meta
    created_by  = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, verbose_name='Yaratdi'
    )
    created_at  = models.DateTimeField('Yaratildi', auto_now_add=True)
    started_at  = models.DateTimeField('Boshlandi', null=True, blank=True)
    finished_at = models.DateTimeField('Tugadi', null=True, blank=True)

    celery_task_id = models.CharField(
        'Celery Task ID', max_length=150, blank=True,
        help_text='Jarayonni kuzatish/bekor qilish uchun'
    )

    class Meta:
        verbose_name = 'Broadcast'
        verbose_name_plural = 'Broadcastlar'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.title} [{self.get_status_display()}]'

    @property
    def processed_count(self):
        return self.sent_count + self.failed_count

    @property
    def pending_count(self):
        return max(0, self.total_users - self.processed_count)

    @property
    def progress_pct(self):
        if not self.total_users:
            return 0
        return round(self.processed_count / self.total_users * 100)

    @property
    def can_send(self):
        return self.status == self.STATUS_DRAFT

    @property
    def is_running(self):
        return self.status == self.STATUS_RUNNING

    @property
    def duration_seconds(self):
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds())
        return None


class TelegramBroadcastLog(models.Model):
    """Har bir foydalanuvchiga yuborish holati."""

    STATUS_PENDING = 'pending'
    STATUS_SENT    = 'sent'
    STATUS_FAILED  = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Kutmoqda'),
        (STATUS_SENT,    'Yuborildi'),
        (STATUS_FAILED,  'Xato'),
    ]

    broadcast     = models.ForeignKey(
        TelegramBroadcast, on_delete=models.CASCADE,
        related_name='logs', verbose_name='Broadcast'
    )
    telegram_user = models.ForeignKey(
        TelegramUser, on_delete=models.CASCADE,
        related_name='broadcast_logs', verbose_name='Telegram user'
    )
    status     = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_text = models.CharField('Xato matni', max_length=500, blank=True)
    sent_at    = models.DateTimeField('Yuborilgan vaqt', null=True, blank=True)

    class Meta:
        verbose_name = 'Yuborish jurnali'
        verbose_name_plural = 'Yuborish jurnali'
        unique_together = [('broadcast', 'telegram_user')]
        ordering = ['-sent_at']

    def __str__(self):
        return f'{self.broadcast.title} → {self.telegram_user} [{self.status}]'
