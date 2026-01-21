"""
TestMakon.uz - Core Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import (
    SiteSettings,
    ContactMessage,
    Feedback,
    FAQ,
    Banner,
    Partner
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('site_name', 'site_tagline', 'site_description')
        }),
        ('Aloqa ma\'lumotlari', {
            'fields': ('contact_email', 'contact_phone', 'contact_address')
        }),
        ('Ijtimoiy tarmoqlar', {
            'fields': ('telegram_url', 'instagram_url', 'youtube_url', 'facebook_url')
        }),
        ('SEO sozlamalari', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
        ('Analitika', {
            'fields': ('google_analytics_id', 'yandex_metrika_id')
        }),
        ('Funksiyalar', {
            'fields': ('is_registration_open', 'is_maintenance_mode', 'maintenance_message')
        }),
        ('Statistika (avtomatik yangilanadi)', {
            'fields': ('total_users', 'total_tests', 'total_questions', 'total_attempts'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        # Faqat bitta sozlama bo'lishi kerak
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Sozlamani o'chirib bo'lmaydi
        return False


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'status', 'created_at', 'status_badge')
    list_filter = ('status', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at', 'user')

    fieldsets = (
        ('Xabar ma\'lumotlari', {
            'fields': ('name', 'email', 'phone', 'subject', 'message', 'user')
        }),
        ('Admin ma\'lumotlari', {
            'fields': ('status', 'admin_notes', 'replied_at')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_closed']

    def status_badge(self, obj):
        colors = {
            'new': '#e74c3c',
            'read': '#3498db',
            'replied': '#2ecc71',
            'closed': '#95a5a6',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def mark_as_read(self, request, queryset):
        queryset.update(status='read')

    mark_as_read.short_description = "O'qilgan deb belgilash"

    def mark_as_replied(self, request, queryset):
        queryset.update(status='replied', replied_at=timezone.now())

    mark_as_replied.short_description = "Javob berilgan deb belgilash"

    def mark_as_closed(self, request, queryset):
        queryset.update(status='closed')

    mark_as_closed.short_description = "Yopilgan deb belgilash"


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'feedback_type', 'priority', 'is_resolved', 'created_at', 'priority_badge')
    list_filter = ('feedback_type', 'priority', 'is_resolved', 'created_at')
    search_fields = ('user__email', 'subject', 'message')
    readonly_fields = ('created_at', 'user', 'page_url')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'feedback_type', 'priority', 'subject', 'message')
        }),
        ('Qo\'shimcha ma\'lumotlar', {
            'fields': ('attachment', 'page_url')
        }),
        ('Admin javobi', {
            'fields': ('is_resolved', 'admin_response', 'resolved_at')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at',)
        }),
    )

    actions = ['mark_as_resolved', 'mark_as_unresolved']

    def priority_badge(self, obj):
        colors = {
            'low': '#95a5a6',
            'medium': '#3498db',
            'high': '#f39c12',
            'critical': '#e74c3c',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.priority, '#95a5a6'),
            obj.get_priority_display()
        )

    priority_badge.short_description = 'Muhimlik'

    def mark_as_resolved(self, request, queryset):
        queryset.update(is_resolved=True, resolved_at=timezone.now())

    mark_as_resolved.short_description = "Hal qilingan deb belgilash"

    def mark_as_unresolved(self, request, queryset):
        queryset.update(is_resolved=False, resolved_at=None)

    mark_as_unresolved.short_description = "Hal qilinmagan deb belgilash"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question_short', 'category', 'order', 'is_active', 'views_count', 'helpful_count')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('question', 'answer')
    list_editable = ('order', 'is_active')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('category', 'question', 'answer')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        }),
        ('Statistika', {
            'fields': ('views_count', 'helpful_count'),
            'classes': ('collapse',)
        }),
    )

    def question_short(self, obj):
        return obj.question[:60] + '...' if len(obj.question) > 60 else obj.question

    question_short.short_description = 'Savol'


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('title', 'position', 'is_active', 'order', 'start_date', 'end_date', 'views_count', 'clicks_count',
                    'ctr_display', 'image_preview')
    list_filter = ('position', 'is_active', 'created_at')
    search_fields = ('title', 'subtitle')
    list_editable = ('order', 'is_active')
    readonly_fields = ('views_count', 'clicks_count', 'ctr', 'created_at', 'image_preview')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('title', 'subtitle', 'position')
        }),
        ('Rasmlar', {
            'fields': ('image', 'mobile_image', 'image_preview')
        }),
        ('Havola', {
            'fields': ('link', 'button_text')
        }),
        ('Vaqt rejasi', {
            'fields': ('start_date', 'end_date')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        }),
        ('Statistika', {
            'fields': ('views_count', 'clicks_count', 'ctr'),
            'classes': ('collapse',)
        }),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px; max-height: 200px;" />',
                obj.image.url
            )
        return '-'

    image_preview.short_description = 'Rasm ko\'rinishi'

    def ctr_display(self, obj):
        return f"{obj.ctr}%"

    ctr_display.short_description = 'CTR'


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'website', 'order', 'is_active', 'logo_preview')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    list_editable = ('order', 'is_active')
    readonly_fields = ('created_at', 'logo_preview')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('name', 'logo', 'logo_preview', 'website', 'description')
        }),
        ('Sozlamalar', {
            'fields': ('order', 'is_active')
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html(
                '<img src="{}" style="max-width: 100px; max-height: 100px;" />',
                obj.logo.url
            )
        return '-'

    logo_preview.short_description = 'Logo ko\'rinishi'


from django.contrib import admin

# Register your models here.
