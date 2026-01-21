"""
TestMakon.uz - Leaderboard Admin
Professional admin panel for rankings and achievements
"""

from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from .models import (
    GlobalLeaderboard, SubjectLeaderboard, Achievement,
    UserAchievement, UserStats, SeasonalLeaderboard,
    SeasonalParticipant
)


@admin.register(GlobalLeaderboard)
class GlobalLeaderboardAdmin(admin.ModelAdmin):
    """Umumiy reyting admin"""

    list_display = [
        'rank_badge', 'user', 'period_display', 'xp_earned_display',
        'tests_completed', 'accuracy_badge', 'rank_change_display'
    ]
    list_filter = ['period', 'period_start', 'period_end']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number'
    ]
    readonly_fields = ['updated_at', 'rank_change_display', 'stats_overview']
    autocomplete_fields = ['user']

    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user', 'period', 'period_start', 'period_end')
        }),
        ('Reyting', {
            'fields': ('rank', 'previous_rank', 'rank_change_display')
        }),
        ('Statistika', {
            'fields': (
                'stats_overview',
                'xp_earned', 'tests_completed', 'correct_answers',
                'accuracy_rate', 'streak_days'
            )
        }),
        ('Vaqt', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='O\'rin', ordering='rank')
    def rank_badge(self, obj):
        if obj.rank == 1:
            badge = '🥇'
            color = '#FFD700'
        elif obj.rank == 2:
            badge = '🥈'
            color = '#C0C0C0'
        elif obj.rank == 3:
            badge = '🥉'
            color = '#CD7F32'
        else:
            badge = f'#{obj.rank}'
            color = '#95a5a6'

        return format_html(
            '<strong style="color: {}; font-size: 16px;">{}</strong>',
            color, badge
        )

    @admin.display(description='Davr')
    def period_display(self, obj):
        colors = {
            'daily': '#3498db',
            'weekly': '#2ecc71',
            'monthly': '#f39c12',
            'all_time': '#9b59b6'
        }
        color = colors.get(obj.period, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            color, obj.get_period_display()
        )

    @admin.display(description='XP', ordering='xp_earned')
    def xp_earned_display(self, obj):
        return format_html(
            '<strong style="color: #2ecc71;">{:,}</strong>',
            obj.xp_earned
        )

    @admin.display(description='Aniqlik', ordering='accuracy_rate')
    def accuracy_badge(self, obj):
        if obj.accuracy_rate >= 80:
            color = '#2ecc71'
        elif obj.accuracy_rate >= 60:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.accuracy_rate
        )

    @admin.display(description='O\'zgarish')
    def rank_change_display(self, obj):
        change = obj.rank_change
        if change is None:
            return format_html('<span style="color: #95a5a6;">Yangi</span>')
        elif change > 0:
            return format_html(
                '<span style="color: #2ecc71;">▲ +{}</span>',
                change
            )
        elif change < 0:
            return format_html(
                '<span style="color: #e74c3c;">▼ {}</span>',
                change
            )
        else:
            return format_html('<span style="color: #95a5a6;">─ 0</span>')

    @admin.display(description='Statistika')
    def stats_overview(self, obj):
        return format_html(
            '<table style="width: 100%;">'
            '<tr><td><strong>XP:</strong></td><td>{:,}</td></tr>'
            '<tr><td><strong>Testlar:</strong></td><td>{}</td></tr>'
            '<tr><td><strong>To\'g\'ri:</strong></td><td style="color: #2ecc71;">{}</td></tr>'
            '<tr><td><strong>Aniqlik:</strong></td><td><strong>{:.1f}%</strong></td></tr>'
            '<tr><td><strong>Streak:</strong></td><td>{} kun 🔥</td></tr>'
            '</table>',
            obj.xp_earned, obj.tests_completed, obj.correct_answers,
            obj.accuracy_rate, obj.streak_days
        )


@admin.register(SubjectLeaderboard)
class SubjectLeaderboardAdmin(admin.ModelAdmin):
    """Fan reytingi admin"""

    list_display = [
        'rank_badge', 'user', 'subject', 'period_display',
        'score_display', 'tests_completed', 'accuracy_badge'
    ]
    list_filter = ['period', 'subject', 'period_start']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'subject__name'
    ]
    readonly_fields = ['updated_at']
    autocomplete_fields = ['user', 'subject']

    @admin.display(description='O\'rin', ordering='rank')
    def rank_badge(self, obj):
        if obj.rank <= 3:
            medals = {1: '🥇', 2: '🥈', 3: '🥉'}
            colors = {1: '#FFD700', 2: '#C0C0C0', 3: '#CD7F32'}
            return format_html(
                '<strong style="color: {}; font-size: 16px;">{}</strong>',
                colors[obj.rank], medals[obj.rank]
            )
        return format_html('<strong>#{}</strong>', obj.rank)

    @admin.display(description='Davr')
    def period_display(self, obj):
        colors = {'weekly': '#2ecc71', 'monthly': '#f39c12', 'all_time': '#9b59b6'}
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.period, '#95a5a6'), obj.get_period_display()
        )

    @admin.display(description='Ball', ordering='score')
    def score_display(self, obj):
        return format_html(
            '<strong style="color: #2ecc71;">{:,}</strong>',
            obj.score
        )

    @admin.display(description='Aniqlik', ordering='accuracy_rate')
    def accuracy_badge(self, obj):
        color = '#2ecc71' if obj.accuracy_rate >= 80 else '#f39c12' if obj.accuracy_rate >= 60 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.accuracy_rate
        )


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    """Yutuqlar admin"""

    list_display = [
        'icon_preview', 'name', 'category_badge', 'rarity_badge',
        'requirement_display', 'xp_reward_display', 'earn_stats', 'is_active'
    ]
    list_filter = ['category', 'rarity', 'is_active', 'is_hidden']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['icon_preview', 'total_earned', 'earn_percentage_display', 'created_at']

    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'description', 'category', 'rarity')
        }),
        ('Vizual', {
            'fields': ('icon', 'icon_preview', 'color')
        }),
        ('Talablar', {
            'fields': ('requirement_type', 'requirement_value')
        }),
        ('Mukofot', {
            'fields': ('xp_reward',)
        }),
        ('Statistika', {
            'fields': ('total_earned', 'earn_percentage_display')
        }),
        ('Sozlamalar', {
            'fields': ('is_active', 'is_hidden', 'created_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='')
    def icon_preview(self, obj):
        if obj.icon:
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: contain;" />',
                obj.icon.url
            )
        return '–'

    @admin.display(description='Kategoriya')
    def category_badge(self, obj):
        colors = {
            'streak': '#e74c3c', 'test': '#3498db', 'score': '#2ecc71',
            'competition': '#f39c12', 'social': '#1abc9c', 'special': '#9b59b6'
        }
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px;">{}</span>',
            colors.get(obj.category, '#95a5a6'), obj.get_category_display()
        )

    @admin.display(description='Nodirligi')
    def rarity_badge(self, obj):
        colors = {
            'common': '#95a5a6', 'uncommon': '#2ecc71',
            'rare': '#3498db', 'epic': '#9b59b6', 'legendary': '#f1c40f'
        }
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 3px 8px; border-radius: 3px; font-weight: bold;">{}</span>',
            colors.get(obj.rarity, '#95a5a6'), obj.get_rarity_display()
        )

    @admin.display(description='Talab')
    def requirement_display(self, obj):
        return format_html(
            '<strong>{}</strong>: {}',
            obj.requirement_type, obj.requirement_value
        )

    @admin.display(description='XP', ordering='xp_reward')
    def xp_reward_display(self, obj):
        return format_html(
            '<strong style="color: #2ecc71;">+{:,}</strong> XP',
            obj.xp_reward
        )

    @admin.display(description='Olganlar')
    def earn_stats(self, obj):
        return format_html(
            '<strong>{}</strong> ({:.1f}%)',
            obj.total_earned, obj.earn_percentage
        )

    @admin.display(description='Foiz')
    def earn_percentage_display(self, obj):
        percentage = obj.earn_percentage
        if percentage >= 50:
            color = '#2ecc71'
        elif percentage >= 20:
            color = '#f39c12'
        else:
            color = '#e74c3c'
        return format_html(
            '<div style="width: 200px; background-color: #ecf0f1; '
            'border-radius: 10px; height: 20px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; height: 100%;"></div></div>'
            '<small>{:.1f}% foydalanuvchi olgan</small>',
            min(percentage, 100), color, percentage
        )

    actions = ['activate', 'deactivate', 'make_hidden']

    @admin.action(description='Faollashtirish')
    def activate(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} ta yutuq faollashtirildi.')

    @admin.action(description='Faolsizlantirish')
    def deactivate(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} ta yutuq faolsizlantirildi.')

    @admin.action(description='Yashirin qilish')
    def make_hidden(self, request, queryset):
        updated = queryset.update(is_hidden=True)
        self.message_user(request, f'{updated} ta yutuq yashirin qilindi.')


@admin.register(UserAchievement)
class UserAchievementAdmin(admin.ModelAdmin):
    """Foydalanuvchi yutuqlari admin"""

    list_display = [
        'user', 'achievement_display', 'rarity_badge',
        'earned_at', 'is_notified_icon'
    ]
    list_filter = [
        'achievement__category', 'achievement__rarity',
        'is_notified', 'earned_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'achievement__name'
    ]
    readonly_fields = ['earned_at']
    autocomplete_fields = ['user', 'achievement']
    date_hierarchy = 'earned_at'

    @admin.display(description='Yutuq')
    def achievement_display(self, obj):
        return format_html(
            '<strong>{}</strong><br><small style="color: #95a5a6;">{}</small>',
            obj.achievement.name, obj.achievement.get_category_display()
        )

    @admin.display(description='Nodirligi')
    def rarity_badge(self, obj):
        colors = {
            'common': '#95a5a6', 'uncommon': '#2ecc71',
            'rare': '#3498db', 'epic': '#9b59b6', 'legendary': '#f1c40f'
        }
        return format_html(
            '<span style="background-color: {}; color: white; '
            'padding: 2px 6px; border-radius: 3px; font-size: 11px;">{}</span>',
            colors.get(obj.achievement.rarity, '#95a5a6'),
            obj.achievement.get_rarity_display()
        )

    @admin.display(description='Xabar', boolean=True)
    def is_notified_icon(self, obj):
        return obj.is_notified


@admin.register(UserStats)
class UserStatsAdmin(admin.ModelAdmin):
    """Foydalanuvchi statistikasi admin"""

    list_display = [
        'user', 'total_tests', 'accuracy_display', 'win_rate_display',
        'best_performance', 'updated_at'
    ]
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number'
    ]
    readonly_fields = [
        'updated_at', 'accuracy_rate', 'win_rate',
        'test_stats_overview', 'battle_stats_overview',
        'time_stats_overview', 'weekly_stats_overview'
    ]
    autocomplete_fields = ['user']

    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user',)
        }),
        ('Test statistikasi', {
            'fields': (
                'test_stats_overview',
                'total_tests', 'total_questions_answered',
                'total_correct', 'total_wrong', 'accuracy_rate'
            )
        }),
        ('Vaqt statistikasi', {
            'fields': (
                'time_stats_overview',
                'total_time_spent', 'average_time_per_question'
            ),
            'classes': ('collapse',)
        }),
        ('Eng yaxshi natijalar', {
            'fields': ('best_score', 'best_streak', 'best_accuracy')
        }),
        ('Jang statistikasi', {
            'fields': (
                'battle_stats_overview',
                'battles_won', 'battles_lost', 'battles_draw', 'win_rate'
            ),
            'classes': ('collapse',)
        }),
        ('Musobaqa statistikasi', {
            'fields': ('competitions_participated', 'competitions_top3'),
            'classes': ('collapse',)
        }),
        ('Haftalik statistika', {
            'fields': (
                'weekly_stats_overview',
                'weekly_xp', 'weekly_tests', 'weekly_correct'
            ),
            'classes': ('collapse',)
        }),
        ('Kunlik statistika', {
            'fields': (
                'today_xp', 'today_tests', 'today_correct', 'last_daily_reset'
            ),
            'classes': ('collapse',)
        }),
        ('Vaqt', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='Aniqlik', ordering='total_correct')
    def accuracy_display(self, obj):
        accuracy = obj.accuracy_rate
        color = '#2ecc71' if accuracy >= 80 else '#f39c12' if accuracy >= 60 else '#e74c3c'
        return format_html(
            '<strong style="color: {};">{:.1f}%</strong>',
            color, accuracy
        )

    @admin.display(description='Win Rate')
    def win_rate_display(self, obj):
        rate = obj.win_rate
        color = '#2ecc71' if rate >= 60 else '#f39c12' if rate >= 40 else '#e74c3c'
        return format_html(
            '<strong style="color: {};">{:.1f}%</strong>',
            color, rate
        )

    @admin.display(description='Eng yaxshi')
    def best_performance(self, obj):
        return format_html(
            'Ball: <strong>{:.1f}</strong> | '
            'Streak: <strong>{}</strong> | '
            'Aniqlik: <strong>{:.1f}%</strong>',
            obj.best_score, obj.best_streak, obj.best_accuracy
        )

    @admin.display(description='Test statistikasi')
    def test_stats_overview(self, obj):
        return format_html(
            '<table style="width: 100%;">'
            '<tr><td>Jami testlar:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Jami javoblar:</td><td><strong>{}</strong></td></tr>'
            '<tr><td style="color: #2ecc71;">To\'g\'ri:</td><td><strong>{}</strong></td></tr>'
            '<tr><td style="color: #e74c3c;">Noto\'g\'ri:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Aniqlik:</td><td><strong style="color: #2ecc71;">{:.1f}%</strong></td></tr>'
            '</table>',
            obj.total_tests, obj.total_questions_answered,
            obj.total_correct, obj.total_wrong, obj.accuracy_rate
        )

    @admin.display(description='Jang statistikasi')
    def battle_stats_overview(self, obj):
        return format_html(
            '<table style="width: 100%;">'
            '<tr><td style="color: #2ecc71;">Yutdi:</td><td><strong>{}</strong></td></tr>'
            '<tr><td style="color: #e74c3c;">Yutqazdi:</td><td><strong>{}</strong></td></tr>'
            '<tr><td style="color: #95a5a6;">Durrang:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>Win Rate:</td><td><strong style="color: #2ecc71;">{:.1f}%</strong></td></tr>'
            '</table>',
            obj.battles_won, obj.battles_lost, obj.battles_draw, obj.win_rate
        )

    @admin.display(description='Vaqt statistikasi')
    def time_stats_overview(self, obj):
        hours = obj.total_time_spent // 60
        minutes = obj.total_time_spent % 60
        return format_html(
            '<table style="width: 100%;">'
            '<tr><td>Jami vaqt:</td><td><strong>{} soat {} daqiqa</strong></td></tr>'
            '<tr><td>O\'rtacha:</td><td><strong>{:.1f} soniya/savol</strong></td></tr>'
            '</table>',
            hours, minutes, obj.average_time_per_question
        )

    @admin.display(description='Haftalik statistika')
    def weekly_stats_overview(self, obj):
        return format_html(
            '<table style="width: 100%;">'
            '<tr><td>XP:</td><td><strong style="color: #2ecc71;">{:,}</strong></td></tr>'
            '<tr><td>Testlar:</td><td><strong>{}</strong></td></tr>'
            '<tr><td>To\'g\'ri:</td><td><strong>{}</strong></td></tr>'
            '</table>',
            obj.weekly_xp, obj.weekly_tests, obj.weekly_correct
        )


class SeasonalParticipantInline(admin.TabularInline):
    model = SeasonalParticipant
    extra = 0
    readonly_fields = ['joined_at', 'updated_at']
    fields = ['user', 'rank', 'total_xp', 'total_tests', 'accuracy_rate']
    autocomplete_fields = ['user']
    max_num = 20


@admin.register(SeasonalLeaderboard)
class SeasonalLeaderboardAdmin(admin.ModelAdmin):
    """Mavsumiy reyting admin"""

    list_display = [
        'name', 'status_badge', 'date_range',
        'participants_count', 'is_active'
    ]
    list_filter = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_at', 'is_ongoing', 'participants_count', 'prizes_overview']
    inlines = [SeasonalParticipantInline]

    fieldsets = (
        ('Asosiy', {
            'fields': ('name', 'slug', 'description')
        }),
        ('Sana', {
            'fields': ('start_date', 'end_date', 'is_ongoing')
        }),
        ('Sovrinlar', {
            'fields': ('prizes', 'prizes_overview')
        }),
        ('Statistika', {
            'fields': ('participants_count',)
        }),
        ('Sozlamalar', {
            'fields': ('is_active', 'created_at'),
            'classes': ('collapse',)
        })
    )

    @admin.display(description='Holat')
    def status_badge(self, obj):
        if obj.is_ongoing:
            return format_html(
                '<span style="background-color: #2ecc71; color: white; '
                'padding: 3px 10px; border-radius: 3px; font-weight: bold;">⚡ Davom etmoqda</span>'
            )
        today = timezone.now().date()
        if today < obj.start_date:
            return format_html(
                '<span style="background-color: #3498db; color: white; '
                'padding: 3px 10px; border-radius: 3px;">📅 Kutilmoqda</span>'
            )
        return format_html(
            '<span style="background-color: #95a5a6; color: white; '
            'padding: 3px 10px; border-radius: 3px;">✓ Tugallangan</span>'
        )

    @admin.display(description='Davr')
    def date_range(self, obj):
        return format_html(
            '{} - {}',
            obj.start_date.strftime('%d.%m.%Y'),
            obj.end_date.strftime('%d.%m.%Y')
        )

    @admin.display(description='Ishtirokchilar')
    def participants_count(self, obj):
        count = obj.participants.count()
        return format_html(
            '<strong style="color: #2ecc71; font-size: 16px;">{:,}</strong> ta',
            count
        )

    @admin.display(description='Sovrinlar ko\'rinishi')
    def prizes_overview(self, obj):
        if not obj.prizes:
            return format_html('<em>Sovrinlar kiritilmagan</em>')

        html = '<ul style="margin: 0; padding-left: 20px;">'
        for prize in obj.prizes[:5]:
            html += f'<li>{prize}</li>'
        if len(obj.prizes) > 5:
            html += f'<li><em>...va yana {len(obj.prizes) - 5} ta</em></li>'
        html += '</ul>'
        return format_html(html)


@admin.register(SeasonalParticipant)
class SeasonalParticipantAdmin(admin.ModelAdmin):
    """Mavsum ishtirokchisi admin"""

    list_display = [
        'rank_badge', 'user', 'season', 'total_xp_display',
        'total_tests', 'accuracy_badge'
    ]
    list_filter = ['season', 'joined_at']
    search_fields = [
        'user__first_name', 'user__last_name', 'user__phone_number',
        'season__name'
    ]
    readonly_fields = ['joined_at', 'updated_at']
    autocomplete_fields = ['user', 'season']

    @admin.display(description='O\'rin', ordering='rank')
    def rank_badge(self, obj):
        if not obj.rank:
            return format_html('<span style="color: #95a5a6;">–</span>')

        if obj.rank == 1:
            return format_html('<strong style="color: #FFD700; font-size: 18px;">🥇 #1</strong>')
        elif obj.rank == 2:
            return format_html('<strong style="color: #C0C0C0; font-size: 18px;">🥈 #2</strong>')
        elif obj.rank == 3:
            return format_html('<strong style="color: #CD7F32; font-size: 18px;">🥉 #3</strong>')
        else:
            return format_html('<strong>#{}</strong>', obj.rank)

    @admin.display(description='XP', ordering='total_xp')
    def total_xp_display(self, obj):
        return format_html(
            '<strong style="color: #2ecc71;">{:,}</strong>',
            obj.total_xp
        )

    @admin.display(description='Aniqlik', ordering='accuracy_rate')
    def accuracy_badge(self, obj):
        color = '#2ecc71' if obj.accuracy_rate >= 80 else '#f39c12' if obj.accuracy_rate >= 60 else '#e74c3c'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}%</span>',
            color, obj.accuracy_rate
        )


# Admin site customization
admin.site.site_header = 'TestMakon.uz - Reyting va Yutuqlar'
admin.site.index_title = 'Leaderboard boshqaruvi'