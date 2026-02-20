"""
TestMakon.uz - Accounts Admin
Production-ready Admin panel with advanced features
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.db.models import Count, Avg
from django.utils import timezone
from .models import (
    User, Badge, UserBadge, Friendship,
    UserActivity, PhoneVerification
)


class UserBadgeInline(admin.TabularInline):
    model = UserBadge
    extra = 0
    readonly_fields = ['earned_at']
    can_delete = False


class UserActivityInline(admin.TabularInline):
    model = UserActivity
    extra = 0
    readonly_fields = ['activity_type', 'description', 'xp_earned', 'created_at']
    can_delete = False
    max_num = 10

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin with gamification support"""

    list_display = [
        'phone_number', 'full_name_display', 'level_badge',
        'xp_display', 'streak_display', 'accuracy_display',
        'tests_count', 'is_premium_display', 'is_active'
    ]
    list_filter = [
        'is_active', 'is_premium', 'is_staff', 'level',
        'education_level', 'is_phone_verified', 'created_at'
    ]
    search_fields = [
        'phone_number', 'first_name', 'last_name',
        'email', 'telegram_username'
    ]
    readonly_fields = [
        'uuid', 'created_at', 'updated_at', 'last_login',
        'accuracy_rate', 'avatar_preview', 'xp_progress',
        'streak_info', 'statistics_overview'
    ]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'phone_number', 'password', 'is_phone_verified')
        }),
        ('Shaxsiy ma\'lumotlar', {
            'fields': (
                'first_name', 'last_name', 'middle_name',
                'email', 'is_email_verified', 'birth_date',
                'avatar', 'avatar_preview', 'bio'
            )
        }),
        ('Telegram', {
            'fields': ('telegram_id', 'telegram_username', 'telegram_photo_url'),
            'classes': ('collapse',)
        }),
        ('Ta\'lim', {
            'fields': (
                'education_level', 'school_name',
                'region', 'district',
                'target_university', 'target_direction'
            ),
            'classes': ('collapse',)
        }),
        ('Gamification', {
            'fields': (
                'xp_points', 'xp_progress', 'level',
                'current_streak', 'longest_streak', 'streak_info',
                'last_activity_date'
            )
        }),
        ('Statistika', {
            'fields': (
                'statistics_overview',
                'total_tests_taken', 'total_correct_answers',
                'total_wrong_answers', 'average_score', 'accuracy_rate'
            )
        }),
        ('Musobaqalar', {
            'fields': (
                'competitions_participated', 'competitions_won',
                'global_rank', 'weekly_rank'
            ),
            'classes': ('collapse',)
        }),
        ('Premium', {
            'fields': ('is_premium', 'premium_until')
        }),
        ('Ruxsatlar', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',)
        }),
        ('Muhim sanalar', {
            'fields': ('last_login', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        ('Yangi foydalanuvchi', {
            'classes': ('wide',),
            'fields': (
                'phone_number', 'password1', 'password2',
                'first_name', 'last_name', 'email'
            ),
        }),
    )

    inlines = [UserBadgeInline, UserActivityInline]

    ordering = ['-created_at']
    list_per_page = 25

    # Custom displays
    @admin.display(description='F.I.SH')
    def full_name_display(self, obj):

        return obj.full_name

    @admin.display(description='Daraja')
    def level_badge(self, obj):
        colors = {
            'beginner': '#95a5a6',
            'elementary': '#3498db',
            'intermediate': '#2ecc71',
            'advanced': '#f39c12',
            'expert': '#e74c3c',
            'master': '#9b59b6',
            'legend': '#f1c40f'
        }
        color = colors.get(obj.level, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color, obj.get_level_display()
        )

    @admin.display(description='XP')
    def xp_display(self, obj):
        return format_html(
            '<strong style="color: #2ecc71;">{}</strong> XP',
            f'{obj.xp_points:,}'
        )

    @admin.display(description='Streak 🔥')
    def streak_display(self, obj):
        if obj.current_streak >= 7:
            color = '#e74c3c'
        elif obj.current_streak >= 3:
            color = '#f39c12'
        else:
            color = '#95a5a6'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{} kun</span>',
            color, obj.current_streak
        )

    @admin.display(description='Aniqlik')
    def accuracy_display(self, obj):
        accuracy = obj.accuracy_rate
        if accuracy >= 80:
            color = '#2ecc71'
        elif accuracy >= 60:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}%</span>',
            color, accuracy
        )

    @admin.display(description='Testlar')
    def tests_count(self, obj):
        return obj.total_tests_taken

    @admin.display(description='Premium', boolean=True)
    def is_premium_display(self, obj):
        if obj.is_premium and obj.premium_until:
            if obj.premium_until > timezone.now():
                return True
        return False

    @admin.display(description='Avatar')
    def avatar_preview(self, obj):
        if obj.avatar:
            return format_html(
                '<img src="{}" width="100" height="100" '
                'style="border-radius: 50%; object-fit: cover;" />',
                obj.avatar.url
            )
        return format_html(
            '<div style="width: 100px; height: 100px; border-radius: 50%; '
            'background-color: #ecf0f1; display: flex; align-items: center; '
            'justify-content: center; color: #95a5a6; font-size: 40px;">{}</div>',
            obj.first_name[0] if obj.first_name else '?'
        )

    @admin.display(description='XP Progress')
    def xp_progress(self, obj):
        levels_xp = {
            'beginner': 500,
            'elementary': 2000,
            'intermediate': 5000,
            'advanced': 10000,
            'expert': 25000,
            'master': 50000,
            'legend': float('inf')
        }
        next_level_xp = levels_xp.get(obj.level, 500)

        if obj.level == 'legend':
            return format_html('<strong>MAX LEVEL! 🏆</strong>')

        progress = min((obj.xp_points / next_level_xp) * 100, 100)
        return format_html(
            '<div style="width: 200px; background-color: #ecf0f1; '
            'border-radius: 10px; height: 20px; overflow: hidden;">'
            '<div style="width: {}%; background-color: #2ecc71; '
            'height: 100%; transition: width 0.3s;"></div></div>'
            '<small>{} / {} XP</small>',
            progress, obj.xp_points, next_level_xp
        )

    @admin.display(description='Streak Ma\'lumoti')
    def streak_info(self, obj):
        return format_html(
            '<div style="padding: 10px; background-color: #ecf0f1; border-radius: 5px;">'
            '<strong>Joriy:</strong> {} kun 🔥<br>'
            '<strong>Eng uzun:</strong> {} kun 🏆<br>'
            '<strong>Oxirgi faollik:</strong> {}</div>',
            obj.current_streak,
            obj.longest_streak,
            obj.last_activity_date.strftime('%d.%m.%Y') if obj.last_activity_date else 'Hali yo\'q'
        )

    @admin.display(description='Statistika')
    def statistics_overview(self, obj):
        return format_html(
            '<table style="width: 100%; border-collapse: collapse;">'
            '<tr><td><strong>Jami testlar:</strong></td><td>{}</td></tr>'
            '<tr><td><strong>To\'g\'ri javoblar:</strong></td><td style="color: #2ecc71;">{}</td></tr>'
            '<tr><td><strong>Noto\'g\'ri javoblar:</strong></td><td style="color: #e74c3c;">{}</td></tr>'
            '<tr><td><strong>O\'rtacha ball:</strong></td><td><strong>{}</strong></td></tr>'
            '<tr><td><strong>Aniqlik:</strong></td><td><strong>{}%</strong></td></tr>'
            '</table>',
            obj.total_tests_taken,
            obj.total_correct_answers,
            obj.total_wrong_answers,
            round(obj.average_score, 2),
            obj.accuracy_rate
        )

    # Actions
    actions = ['make_premium', 'remove_premium', 'verify_phone', 'reset_streak']

    @admin.action(description='Premium qilish (1 oy)')
    def make_premium(self, request, queryset):
        updated = queryset.update(
            is_premium=True,
            premium_until=timezone.now() + timezone.timedelta(days=30)
        )
        self.message_user(request, f'{updated} ta foydalanuvchi premium qilindi.')

    @admin.action(description='Premium olib tashlash')
    def remove_premium(self, request, queryset):
        updated = queryset.update(is_premium=False, premium_until=None)
        self.message_user(request, f'{updated} ta foydalanuvchidan premium olib tashlandi.')

    @admin.action(description='Telefon tasdiqlash')
    def verify_phone(self, request, queryset):
        updated = queryset.update(is_phone_verified=True)
        self.message_user(request, f'{updated} ta telefon tasdiqlandi.')

    @admin.action(description='Streak reset qilish')
    def reset_streak(self, request, queryset):
        updated = queryset.update(current_streak=0)
        self.message_user(request, f'{updated} ta foydalanuvchining streak reset qilindi.')


@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ['name', 'badge_type', 'icon_preview', 'xp_reward', 'requirement_value', 'users_count', 'is_active']
    list_filter = ['badge_type', 'is_active']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['icon_preview', 'users_count']

    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'description', 'badge_type')
        }),
        ('Tasvirlar', {
            'fields': ('icon', 'icon_preview')
        }),
        ('Mukofot va talablar', {
            'fields': ('xp_reward', 'requirement_value', 'is_active')
        }),
        ('Statistika', {
            'fields': ('users_count',)
        })
    )

    @admin.display(description='Ikonka')
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: contain;" />',
                obj.icon.url
            )
        return '-'

    @admin.display(description='Foydalanuvchilar')
    def users_count(self, obj):
        count = obj.userbadge_set.count()
        return format_html(
            '<strong style="color: #2ecc71;">{}</strong> ta',
            count
        )


@admin.register(UserBadge)
class UserBadgeAdmin(admin.ModelAdmin):
    list_display = ['user', 'badge', 'badge_type', 'earned_at']
    list_filter = ['badge__badge_type', 'earned_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'badge__name']
    readonly_fields = ['earned_at']
    autocomplete_fields = ['user', 'badge']

    @admin.display(description='Turi')
    def badge_type(self, obj):
        return obj.badge.get_badge_type_display()


@admin.register(Friendship)
class FriendshipAdmin(admin.ModelAdmin):
    list_display = ['from_user', 'to_user', 'status_badge', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = [
        'from_user__first_name', 'from_user__last_name', 'from_user__phone_number',
        'to_user__first_name', 'to_user__last_name', 'to_user__phone_number'
    ]
    readonly_fields = ['created_at', 'updated_at']
    autocomplete_fields = ['from_user', 'to_user']

    @admin.display(description='Holat')
    def status_badge(self, obj):
        colors = {
            'pending': '#f39c12',
            'accepted': '#2ecc71',
            'rejected': '#e74c3c',
            'blocked': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_status_display()
        )


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'activity_type_badge', 'xp_earned', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['user__first_name', 'user__last_name', 'user__phone_number', 'description']
    readonly_fields = ['created_at', 'metadata']
    autocomplete_fields = ['user']

    date_hierarchy = 'created_at'

    @admin.display(description='Faoliyat')
    def activity_type_badge(self, obj):
        colors = {
            'login': '#3498db',
            'test_complete': '#2ecc71',
            'competition_join': '#e74c3c',
            'badge_earn': '#f1c40f',
            'level_up': '#9b59b6',
            'friend_add': '#1abc9c'
        }
        color = colors.get(obj.activity_type, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px;">{}</span>',
            color, obj.get_activity_type_display()
        )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'code', 'is_used', 'is_expired_display', 'created_at', 'expires_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['phone_number', 'code']
    readonly_fields = ['created_at', 'is_expired_display']

    @admin.display(description='Muddati o\'tgan', boolean=True)
    def is_expired_display(self, obj):
        return obj.is_expired

    actions = ['mark_as_used']

    @admin.action(description='Ishlatilgan deb belgilash')
    def mark_as_used(self, request, queryset):
        updated = queryset.update(is_used=True)
        self.message_user(request, f'{updated} ta kod ishlatilgan deb belgilandi.')


# Admin site customization
admin.site.site_header = 'TestMakon.uz Admin Panel'
admin.site.site_title = 'TestMakon.uz'
admin.site.index_title = 'Boshqaruv paneli'

