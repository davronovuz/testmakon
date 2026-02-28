"""
TestMakon.uz — Telegram Bot Admin Panel
Broadcast yaratish, yuborish, kuzatish va bekor qilish.
"""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import JsonResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count

from django.contrib.auth import get_user_model

from .models import TelegramUser, TelegramBroadcast, TelegramBroadcastLog
from .tasks import start_broadcast


# ══════════════════════════════════════════════
# TelegramUser Admin
# ══════════════════════════════════════════════

@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display  = ['telegram_id', 'full_name_col', 'username_link', 'language_code', 'is_active', 'joined_at']
    list_filter   = ['is_active', 'language_code']
    search_fields = ['username', 'first_name', 'last_name', 'telegram_id']
    readonly_fields = ['telegram_id', 'username', 'first_name', 'last_name',
                       'language_code', 'joined_at', 'last_activity']
    list_per_page = 50
    ordering = ['-joined_at']

    fieldsets = [
        ('Telegram ma\'lumotlari', {
            'fields': ['telegram_id', 'username', 'first_name', 'last_name', 'language_code']
        }),
        ('Holat', {
            'fields': ['is_active', 'site_user', 'joined_at', 'last_activity']
        }),
    ]

    def full_name_col(self, obj):
        return obj.full_name
    full_name_col.short_description = 'Ism'

    def username_link(self, obj):
        if obj.username:
            return format_html(
                '<a href="https://t.me/{}" target="_blank" style="color:#2563EB">@{}</a>',
                obj.username, obj.username
            )
        return format_html('<span style="color:#9CA3AF">—</span>')
    username_link.short_description = 'Username'

    actions = ['activate_users', 'deactivate_users']

    @admin.action(description='✓ Faollashtirish')
    def activate_users(self, request, qs):
        n = qs.update(is_active=True)
        self.message_user(request, f'{n} ta user faollashtirildi', messages.SUCCESS)

    @admin.action(description='✗ Faolsizlashtirish')
    def deactivate_users(self, request, qs):
        n = qs.update(is_active=False)
        self.message_user(request, f'{n} ta user faolsizlashtirildi', messages.WARNING)


# ══════════════════════════════════════════════
# BroadcastLog Inline
# ══════════════════════════════════════════════

class BroadcastLogInline(admin.TabularInline):
    model      = TelegramBroadcastLog
    extra      = 0
    max_num    = 0
    can_delete = False
    readonly_fields = ['telegram_user_link', 'status_col', 'error_text', 'sent_at']
    fields      = ['telegram_user_link', 'status_col', 'error_text', 'sent_at']
    verbose_name_plural = 'Xatolar jurnali (faqat failed)'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(
            status=TelegramBroadcastLog.STATUS_FAILED
        ).select_related('site_user')[:100]

    def telegram_user_link(self, obj):
        u = obj.site_user
        name = getattr(u, 'get_full_name', lambda: str(u))()
        return format_html('<span>{}</span>', name or str(u))
    telegram_user_link.short_description = 'Foydalanuvchi'

    def status_col(self, obj):
        return format_html(
            '<span style="color:#DC2626;font-weight:600">✗ Xato</span>'
        )
    status_col.short_description = 'Holat'

    def has_add_permission(self, request, obj=None):
        return False


# ══════════════════════════════════════════════
# TelegramBroadcast Admin
# ══════════════════════════════════════════════

@admin.register(TelegramBroadcast)
class TelegramBroadcastAdmin(admin.ModelAdmin):

    list_display  = ['title', 'status_badge', 'total_users_col', 'sent_col',
                     'failed_col', 'progress_bar_col', 'created_at', 'action_col']
    list_filter   = ['status', 'created_at']
    search_fields = ['title', 'message']
    ordering      = ['-created_at']
    list_per_page = 20
    inlines       = [BroadcastLogInline]

    readonly_fields = [
        'status', 'total_users', 'sent_count', 'failed_count',
        'created_by', 'created_at', 'started_at', 'finished_at',
        'celery_task_id', 'stats_widget',
    ]

    fieldsets = [
        ('📝 Xabar', {
            'fields': ['title', 'message', 'image'],
            'description': 'HTML teglari ishlatsa bo\'ladi: <b>qalin</b>, <i>kursiv</i>, <a href="...">havola</a>'
        }),
        ('🔘 Inline tugma (ixtiyoriy)', {
            'fields': ['button_text', 'button_url'],
            'classes': ['collapse'],
        }),
        ('📊 Statistika', {
            'fields': ['stats_widget', 'status', 'total_users', 'sent_count', 'failed_count'],
        }),
        ('ℹ️ Qo\'shimcha', {
            'fields': ['created_by', 'created_at', 'started_at', 'finished_at', 'celery_task_id'],
            'classes': ['collapse'],
        }),
    ]

    change_form_template = 'admin/tgbot/telegrambroadcast/change_form.html'

    # ── Custom URLs ───────────────────────────────────────────
    def get_urls(self):
        custom = [
            path('<int:pk>/send/',      self.admin_site.admin_view(self._send_view),   name='tgbot_broadcast_send'),
            path('<int:pk>/cancel/',    self.admin_site.admin_view(self._cancel_view), name='tgbot_broadcast_cancel'),
            path('<int:pk>/stats-api/', self.admin_site.admin_view(self._stats_api),   name='tgbot_broadcast_stats'),
            path('setup-webhook/',      self.admin_site.admin_view(self._setup_webhook), name='tgbot_setup_webhook'),
        ]
        return custom + super().get_urls()

    def _send_view(self, request, pk):
        bc = get_object_or_404(TelegramBroadcast, pk=pk)
        if bc.status != TelegramBroadcast.STATUS_DRAFT:
            self.message_user(request, 'Faqat "Qoralama" statusidagi broadcastni yuborsa bo\'ladi.', messages.ERROR)
        else:
            task = start_broadcast.delay(pk)
            self.message_user(
                request,
                f'✓ Broadcast yuborish boshlandi! Task ID: {task.id}. '
                f'Statistika avtomatik yangilanib turadi.',
                messages.SUCCESS
            )
        return redirect(reverse('admin:tgbot_telegrambroadcast_change', args=[pk]))

    def _cancel_view(self, request, pk):
        bc = get_object_or_404(TelegramBroadcast, pk=pk)
        if bc.status != TelegramBroadcast.STATUS_RUNNING:
            self.message_user(request, 'Faqat "Yuborilmoqda" statusidagi broadcastni bekor qilsa bo\'ladi.', messages.ERROR)
        else:
            TelegramBroadcast.objects.filter(pk=pk).update(
                status=TelegramBroadcast.STATUS_CANCELLED,
                finished_at=timezone.now(),
            )
            self.message_user(
                request,
                '⚠️ Broadcast bekor qilindi. Joriy yuborilayotgan xabarlar tugagach to\'xtaydi.',
                messages.WARNING
            )
        return redirect(reverse('admin:tgbot_telegrambroadcast_change', args=[pk]))

    def _stats_api(self, request, pk):
        """AJAX: real-time statistika JSON."""
        bc = get_object_or_404(TelegramBroadcast, pk=pk)
        bc.refresh_from_db()
        return JsonResponse({
            'status':         bc.status,
            'status_display': bc.get_status_display(),
            'total_users':    bc.total_users,
            'sent_count':     bc.sent_count,
            'failed_count':   bc.failed_count,
            'pending_count':  bc.pending_count,
            'progress_pct':   bc.progress_pct,
            'is_done':        bc.status in (TelegramBroadcast.STATUS_DONE, TelegramBroadcast.STATUS_CANCELLED),
        })

    def _setup_webhook(self, request):
        """Telegram webhookni o'rnatish."""
        from django.conf import settings as s
        import requests as req
        token   = getattr(s, 'TELEGRAM_BOT_TOKEN', '')
        domain  = getattr(s, 'SITE_DOMAIN', 'https://testmakon.uz')
        wh_url  = f'{domain.rstrip("/")}/tgbot/webhook/{token}/'
        result  = req.post(
            f'https://api.telegram.org/bot{token}/setWebhook',
            json={'url': wh_url, 'allowed_updates': ['message']},
            timeout=10
        ).json()
        if result.get('ok'):
            self.message_user(request, f'✓ Webhook o\'rnatildi: {wh_url}', messages.SUCCESS)
        else:
            self.message_user(request, f'✗ Xato: {result.get("description")}', messages.ERROR)
        return redirect(reverse('admin:tgbot_telegrambroadcast_changelist'))

    # ── save_model ────────────────────────────────────────────
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    # ── List display methods ──────────────────────────────────
    STATUS_COLORS = {
        'draft':     ('#6B7280', '#F3F4F6'),
        'running':   ('#1D4ED8', '#DBEAFE'),
        'done':      ('#059669', '#D1FAE5'),
        'cancelled': ('#DC2626', '#FEE2E2'),
    }

    def status_badge(self, obj):
        c, bg = self.STATUS_COLORS.get(obj.status, ('#6B7280', '#F3F4F6'))
        icon = {'draft': '📝', 'running': '🔄', 'done': '✅', 'cancelled': '❌'}.get(obj.status, '')
        return format_html(
            '<span style="background:{};color:{};padding:3px 9px;border-radius:5px;'
            'font-size:11px;font-weight:700;white-space:nowrap">{} {}</span>',
            bg, c, icon, obj.get_status_display()
        )
    status_badge.short_description = 'Holat'

    def total_users_col(self, obj):
        if obj.total_users:
            return format_html('<b>{}</b>', obj.total_users)
        active = get_user_model().objects.filter(telegram_id__isnull=False, is_active=True).count()
        return format_html('<span style="color:#9CA3AF">~{}</span>', active)
    total_users_col.short_description = 'Jami'

    def sent_col(self, obj):
        if not obj.sent_count:
            return format_html('<span style="color:#9CA3AF">0</span>')
        return format_html('<span style="color:#059669;font-weight:700">✓ {}</span>', obj.sent_count)
    sent_col.short_description = 'Yuborildi'

    def failed_col(self, obj):
        if not obj.failed_count:
            return format_html('<span style="color:#9CA3AF">—</span>')
        return format_html('<span style="color:#DC2626;font-weight:700">✗ {}</span>', obj.failed_count)
    failed_col.short_description = 'Xato'

    def progress_bar_col(self, obj):
        if not obj.total_users:
            return '—'
        pct   = obj.progress_pct
        color = {'done': '#059669', 'cancelled': '#DC2626', 'running': '#2563EB'}.get(obj.status, '#6B7280')
        return format_html(
            '<div style="width:90px">'
            '<div style="background:#E5E7EB;border-radius:4px;height:8px;overflow:hidden">'
            '<div style="background:{};width:{}%;height:100%;border-radius:4px"></div></div>'
            '<small style="color:#6B7280;font-size:10px">{}/{}</small></div>',
            color, pct, obj.processed_count, obj.total_users
        )
    progress_bar_col.short_description = 'Progress'

    def action_col(self, obj):
        if obj.status == TelegramBroadcast.STATUS_DRAFT:
            url = reverse('admin:tgbot_broadcast_send', args=[obj.pk])
            active = get_user_model().objects.filter(telegram_id__isnull=False, is_active=True).count()
            return format_html(
                '<a href="{}" style="background:#059669;color:white;padding:4px 12px;'
                'border-radius:5px;font-size:11px;font-weight:700;text-decoration:none;white-space:nowrap" '
                'onclick="return confirm(\'▶ {} ta foydalanuvchiga yuboriladi. Tasdiqlaysizmi?\')">▶ Yuborish</a>',
                url, active
            )
        elif obj.status == TelegramBroadcast.STATUS_RUNNING:
            url = reverse('admin:tgbot_broadcast_cancel', args=[obj.pk])
            return format_html(
                '<a href="{}" style="background:#DC2626;color:white;padding:4px 12px;'
                'border-radius:5px;font-size:11px;font-weight:700;text-decoration:none;white-space:nowrap" '
                'onclick="return confirm(\'Broadcastni to\\\'xtatishni tasdiqlaysizmi?\')">■ To\'xtatish</a>',
                url
            )
        return format_html('<span style="color:#9CA3AF;font-size:11px">—</span>')
    action_col.short_description = 'Amal'

    # ── stats_widget read-only field ──────────────────────────
    def stats_widget(self, obj):
        if not obj.pk:
            return '—'
        active_users = get_user_model().objects.filter(telegram_id__isnull=False, is_active=True).count()
        return format_html(
            '<div id="bc-stats-box" data-pk="{}" data-status="{}">'
            '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:10px">'
            '<div style="background:#F0FDF4;border:1px solid #BBF7D0;border-radius:8px;padding:10px;text-align:center">'
            '  <div style="font-size:24px;font-weight:900;color:#059669" id="s-sent">{}</div>'
            '  <div style="font-size:11px;color:#6B7280;margin-top:2px">Yuborildi</div></div>'
            '<div style="background:#FEF2F2;border:1px solid #FECACA;border-radius:8px;padding:10px;text-align:center">'
            '  <div style="font-size:24px;font-weight:900;color:#DC2626" id="s-failed">{}</div>'
            '  <div style="font-size:11px;color:#6B7280;margin-top:2px">Xato</div></div>'
            '<div style="background:#EFF6FF;border:1px solid #BFDBFE;border-radius:8px;padding:10px;text-align:center">'
            '  <div style="font-size:24px;font-weight:900;color:#2563EB" id="s-pending">{}</div>'
            '  <div style="font-size:11px;color:#6B7280;margin-top:2px">Kutmoqda</div></div>'
            '<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:8px;padding:10px;text-align:center">'
            '  <div style="font-size:24px;font-weight:900;color:#0F172A" id="s-total">{}</div>'
            '  <div style="font-size:11px;color:#6B7280;margin-top:2px">Jami</div></div>'
            '</div>'
            '<div style="background:#E2E8F0;border-radius:6px;height:12px;overflow:hidden;margin-bottom:6px">'
            '  <div id="s-pbar" style="background:linear-gradient(90deg,#059669,#34D399);'
            '       height:100%;border-radius:6px;transition:width .4s;width:{}%"></div></div>'
            '<div style="display:flex;justify-content:space-between;font-size:12px;color:#64748B">'
            '  <span>Faol Telegram userlar: <b>{}</b></span>'
            '  <span id="s-pct" style="font-weight:700">{}%</span>'
            '</div></div>',
            obj.pk, obj.status,
            obj.sent_count, obj.failed_count, obj.pending_count, obj.total_users,
            obj.progress_pct,
            active_users,
            obj.progress_pct,
        )
    stats_widget.short_description = 'Real-time statistika'


@admin.register(TelegramBroadcastLog)
class TelegramBroadcastLogAdmin(admin.ModelAdmin):
    list_display  = ['broadcast', 'user_col', 'status_col', 'error_text', 'sent_at']
    list_filter   = ['status', 'broadcast']
    search_fields = ['site_user__first_name', 'site_user__last_name', 'error_text']
    readonly_fields = ['broadcast', 'site_user', 'status', 'error_text', 'sent_at']
    list_per_page  = 100

    def user_col(self, obj):
        u = obj.site_user
        name = getattr(u, 'get_full_name', lambda: '')()
        tg_id = getattr(u, 'telegram_id', None)
        if tg_id:
            return format_html('{} <span style="color:#9CA3AF;font-size:11px">(tg:{})</span>', name or str(u), tg_id)
        return name or str(u)
    user_col.short_description = 'Foydalanuvchi'

    def status_col(self, obj):
        colors = {
            'pending': ('#9CA3AF', '#F9FAFB'),
            'sent':    ('#059669', '#D1FAE5'),
            'failed':  ('#DC2626', '#FEE2E2'),
        }
        c, bg = colors.get(obj.status, ('#9CA3AF', '#F9FAFB'))
        icons  = {'pending': '⏳', 'sent': '✓', 'failed': '✗'}
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600">'
            '{} {}</span>', bg, c, icons.get(obj.status, ''), obj.get_status_display()
        )
    status_col.short_description = 'Holat'

    def has_add_permission(self, request):
        return False
