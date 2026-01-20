"""
TestMakon.uz - Subscriptions Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    SubscriptionPlan, Subscription, Payment,
    PromoCode, PromoCodeUsage, UserDailyLimit
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price_display', 'duration_days', 'is_featured', 'is_active', 'order']
    list_filter = ['plan_type', 'is_active', 'is_featured']
    list_editable = ['is_active', 'is_featured', 'order']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'plan_type')
        }),
        ('Narx', {
            'fields': ('price', 'original_price', 'duration_days')
        }),
        ('Imkoniyatlar', {
            'fields': ('features', 'daily_test_limit', 'daily_ai_chat_limit',
                       'can_access_analytics', 'can_access_ai_mentor',
                       'can_download_pdf', 'can_access_competitions', 'ad_free')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured', 'order')
        }),
    )

    def price_display(self, obj):
        if obj.original_price and obj.discount_percent:
            return format_html(
                '<span style="text-decoration: line-through; color: #999;">{:,}</span> '
                '<strong style="color: #22c55e;">{:,} so\'m</strong> '
                '<span style="background: #22c55e; color: white; padding: 2px 6px; border-radius: 4px; font-size: 11px;">-{}%</span>',
                obj.original_price, obj.price, obj.discount_percent
            )
        return format_html('<strong>{:,} so\'m</strong>', obj.price)

    price_display.short_description = 'Narxi'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'status_badge', 'days_remaining_display', 'started_at', 'expires_at', 'auto_renew']
    list_filter = ['status', 'plan', 'auto_renew', 'created_at']
    search_fields = ['user__phone_number', 'user__first_name', 'user__last_name', 'uuid']
    raw_id_fields = ['user', 'plan']
    readonly_fields = ['uuid', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        colors = {
            'active': '#22c55e',
            'expired': '#ef4444',
            'cancelled': '#f59e0b',
            'pending': '#3b82f6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def days_remaining_display(self, obj):
        days = obj.days_remaining
        if days == 0:
            return format_html('<span style="color: #ef4444;">Tugagan</span>')
        elif days <= 3:
            return format_html('<span style="color: #f59e0b;">{} kun</span>', days)
        return format_html('<span style="color: #22c55e;">{} kun</span>', days)

    days_remaining_display.short_description = 'Qolgan'

    actions = ['activate_subscriptions', 'cancel_subscriptions']

    def activate_subscriptions(self, request, queryset):
        for sub in queryset.filter(status='pending'):
            sub.activate()
        self.message_user(request, f'{queryset.count()} ta obuna faollashtirildi')

    activate_subscriptions.short_description = 'Tanlangan obunalarni faollashtirish'

    def cancel_subscriptions(self, request, queryset):
        for sub in queryset.filter(status='active'):
            sub.cancel()
        self.message_user(request, f'{queryset.count()} ta obuna bekor qilindi')

    cancel_subscriptions.short_description = 'Tanlangan obunalarni bekor qilish'


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'user', 'amount_display', 'provider', 'status_badge', 'created_at', 'paid_at']
    list_filter = ['status', 'provider', 'created_at']
    search_fields = ['order_id', 'user__phone_number', 'user__first_name', 'provider_transaction_id']
    raw_id_fields = ['user', 'subscription', 'plan']
    readonly_fields = ['uuid', 'order_id', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy', {
            'fields': ('uuid', 'order_id', 'user', 'plan', 'subscription')
        }),
        ('To\'lov', {
            'fields': ('amount', 'provider', 'status')
        }),
        ('Provider', {
            'fields': ('provider_transaction_id', 'provider_response'),
            'classes': ('collapse',)
        }),
        ('Qo\'shimcha', {
            'fields': ('description', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Vaqtlar', {
            'fields': ('paid_at', 'created_at', 'updated_at')
        }),
    )

    def amount_display(self, obj):
        return format_html('<strong>{:,} so\'m</strong>', obj.amount)

    amount_display.short_description = 'Summa'

    def status_badge(self, obj):
        colors = {
            'completed': '#22c55e',
            'pending': '#3b82f6',
            'processing': '#f59e0b',
            'failed': '#ef4444',
            'cancelled': '#6b7280',
            'refunded': '#8b5cf6',
        }
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 4px 8px; border-radius: 4px; font-size: 11px;">{}</span>',
            color, obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    actions = ['mark_as_paid', 'mark_as_failed']

    def mark_as_paid(self, request, queryset):
        for payment in queryset.filter(status='pending'):
            payment.mark_as_paid()
        self.message_user(request, f'{queryset.count()} ta to\'lov tasdiqlandi')

    mark_as_paid.short_description = 'To\'langan deb belgilash'

    def mark_as_failed(self, request, queryset):
        queryset.update(status='failed')
        self.message_user(request, f'{queryset.count()} ta to\'lov rad etildi')

    mark_as_failed.short_description = 'Rad etilgan deb belgilash'


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_display', 'usage_display', 'valid_period', 'is_valid_badge', 'is_active']
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until']
    search_fields = ['code', 'description']
    list_editable = ['is_active']

    fieldsets = (
        ('Kod', {
            'fields': ('code', 'description')
        }),
        ('Chegirma', {
            'fields': ('discount_type', 'discount_value', 'plan')
        }),
        ('Cheklovlar', {
            'fields': ('max_uses', 'max_uses_per_user', 'current_uses')
        }),
        ('Vaqt', {
            'fields': ('valid_from', 'valid_until', 'is_active')
        }),
    )

    def discount_display(self, obj):
        if obj.discount_type == 'percent':
            return format_html('<strong>{}%</strong>', obj.discount_value)
        elif obj.discount_type == 'fixed':
            return format_html('<strong>{:,} so\'m</strong>', obj.discount_value)
        return format_html('<strong>{} kun</strong>', obj.discount_value)

    discount_display.short_description = 'Chegirma'

    def usage_display(self, obj):
        if obj.max_uses:
            return f'{obj.current_uses}/{obj.max_uses}'
        return f'{obj.current_uses}/∞'

    usage_display.short_description = 'Ishlatish'

    def valid_period(self, obj):
        return f'{obj.valid_from.strftime("%d.%m.%Y")} - {obj.valid_until.strftime("%d.%m.%Y")}'

    valid_period.short_description = 'Muddat'

    def is_valid_badge(self, obj):
        if obj.is_valid:
            return format_html('<span style="color: #22c55e;">✓ Amalda</span>')
        return format_html('<span style="color: #ef4444;">✗ Muddati o\'tgan</span>')

    is_valid_badge.short_description = 'Holat'


@admin.register(PromoCodeUsage)
class PromoCodeUsageAdmin(admin.ModelAdmin):
    list_display = ['promo_code', 'user', 'discount_amount', 'used_at']
    list_filter = ['promo_code', 'used_at']
    search_fields = ['user__phone_number', 'promo_code__code']
    raw_id_fields = ['user', 'promo_code', 'payment']
    date_hierarchy = 'used_at'


@admin.register(UserDailyLimit)
class UserDailyLimitAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'tests_taken', 'ai_chats_used']
    list_filter = ['date']
    search_fields = ['user__phone_number']
    raw_id_fields = ['user']
    date_hierarchy = 'date'