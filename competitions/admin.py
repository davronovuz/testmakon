"""
TestMakon.uz - Competition Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from .models import (
    Competition,
    CompetitionParticipant,
    Battle,
    BattleInvitation,
    DailyChallenge,
    DailyChallengeParticipant
)


class CompetitionParticipantInline(admin.TabularInline):
    model = CompetitionParticipant
    extra = 0
    readonly_fields = ('user', 'score', 'rank', 'xp_earned', 'joined_at')
    fields = ('user', 'score', 'rank', 'is_completed', 'xp_earned')
    can_delete = False


@admin.register(Competition)
class CompetitionAdmin(admin.ModelAdmin):
    list_display = ('title', 'competition_type', 'status', 'start_time', 'end_time', 'participants_count',
                    'is_premium_only', 'type_badge', 'status_badge', 'time_status')
    list_filter = ('competition_type', 'status', 'is_premium_only', 'is_active', 'start_time')
    search_fields = ('title', 'slug', 'description')
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ('uuid', 'participants_count', 'created_at', 'updated_at', 'banner_preview', 'time_remaining')
    date_hierarchy = 'start_time'
    inlines = [CompetitionParticipantInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'title', 'slug', 'description', 'rules', 'competition_type', 'status')
        }),
        ('Media', {
            'fields': ('banner', 'banner_preview')
        }),
        ('Fan va Test', {
            'fields': ('subject', 'test')
        }),
        ('Vaqt sozlamalari', {
            'fields': ('start_time', 'end_time', 'duration_minutes', 'time_remaining')
        }),
        ('Qatnashish shartlari', {
            'fields': ('max_participants', 'min_level', 'is_premium_only')
        }),
        ('Sovrinlar va XP', {
            'fields': ('prizes', 'xp_reward_first', 'xp_reward_second', 'xp_reward_third', 'xp_participation')
        }),
        ('Statistika', {
            'fields': ('participants_count',),
            'classes': ('collapse',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_competitions', 'cancel_competitions', 'mark_as_finished']

    def banner_preview(self, obj):
        if obj.banner:
            return format_html(
                '<img src="{}" style="max-width: 300px; max-height: 200px;" />',
                obj.banner.url
            )
        return '-'

    banner_preview.short_description = 'Banner ko\'rinishi'

    def type_badge(self, obj):
        colors = {
            'daily': '#3498db',
            'weekly': '#2ecc71',
            'monthly': '#9b59b6',
            'special': '#e67e22',
            'olympiad': '#e74c3c',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.competition_type, '#95a5a6'),
            obj.get_competition_type_display()
        )

    type_badge.short_description = 'Turi'

    def status_badge(self, obj):
        colors = {
            'upcoming': '#3498db',
            'active': '#2ecc71',
            'finished': '#95a5a6',
            'cancelled': '#e74c3c',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def time_status(self, obj):
        if obj.is_ongoing:
            return format_html('<span style="color: #2ecc71; font-weight: bold;">⏱️ Davom etmoqda</span>')
        elif obj.is_finished:
            return format_html('<span style="color: #95a5a6;">✓ Tugagan</span>')
        else:
            return format_html('<span style="color: #3498db;">⏰ Kutilmoqda</span>')

    time_status.short_description = 'Vaqt holati'

    def activate_competitions(self, request, queryset):
        queryset.update(is_active=True, status='active')

    activate_competitions.short_description = "Faollashtirish"

    def cancel_competitions(self, request, queryset):
        queryset.update(status='cancelled')

    cancel_competitions.short_description = "Bekor qilish"

    def mark_as_finished(self, request, queryset):
        queryset.update(status='finished')

    mark_as_finished.short_description = "Yakunlangan deb belgilash"


@admin.register(CompetitionParticipant)
class CompetitionParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'competition', 'score', 'rank', 'correct_answers', 'wrong_answers', 'xp_earned',
                    'is_completed', 'rank_badge')
    list_filter = ('is_completed', 'is_started', 'competition__competition_type', 'joined_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'competition__title')
    readonly_fields = ('joined_at', 'started_at', 'completed_at')
    date_hierarchy = 'joined_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('competition', 'user')
        }),
        ('Natijalar', {
            'fields': ('score', 'correct_answers', 'wrong_answers', 'time_spent', 'rank', 'xp_earned')
        }),
        ('Holat', {
            'fields': ('is_started', 'is_completed', 'started_at', 'completed_at')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('joined_at',)
        }),
    )

    def rank_badge(self, obj):
        if obj.rank == 1:
            return format_html(
                '<span style="background-color: #f1c40f; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥇 1</span>')
        elif obj.rank == 2:
            return format_html(
                '<span style="background-color: #95a5a6; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥈 2</span>')
        elif obj.rank == 3:
            return format_html(
                '<span style="background-color: #cd7f32; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥉 3</span>')
        elif obj.rank:
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 5px 10px; border-radius: 50%;">{}</span>',
                obj.rank)
        return '-'

    rank_badge.short_description = 'O\'rin'


@admin.register(Battle)
class BattleAdmin(admin.ModelAdmin):
    list_display = ('challenger', 'opponent', 'subject', 'status', 'winner', 'is_draw', 'created_at', 'status_badge',
                    'result_display')
    list_filter = ('status', 'is_draw', 'is_block_test', 'created_at')
    search_fields = ('challenger__email', 'opponent__email', 'uuid')
    readonly_fields = ('uuid', 'created_at', 'accepted_at', 'started_at', 'completed_at', 'expires_at')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'status', 'challenger', 'opponent', 'winner', 'is_draw')
        }),
        ('Sozlamalar', {
            'fields': ('subject', 'is_block_test', 'question_count', 'time_per_question')
        }),
        ('Chaqiruvchi natijalari', {
            'fields': ('challenger_score', 'challenger_correct', 'challenger_time', 'challenger_completed'),
            'classes': ('collapse',)
        }),
        ('Raqib natijalari', {
            'fields': ('opponent_score', 'opponent_correct', 'opponent_time', 'opponent_completed'),
            'classes': ('collapse',)
        }),
        ('XP mukofotlar', {
            'fields': ('winner_xp', 'loser_xp')
        }),
        ('Vaqt', {
            'fields': ('created_at', 'accepted_at', 'started_at', 'completed_at', 'expires_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['cancel_battles', 'expire_battles']

    def status_badge(self, obj):
        colors = {
            'pending': '#f39c12',
            'accepted': '#3498db',
            'in_progress': '#2ecc71',
            'completed': '#95a5a6',
            'rejected': '#e74c3c',
            'expired': '#7f8c8d',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.status, '#95a5a6'),
            obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def result_display(self, obj):
        if obj.status != 'completed':
            return '-'

        if obj.is_draw:
            return format_html('<span style="color: #95a5a6; font-weight: bold;">DURRANG</span>')

        if obj.winner:
            winner_name = obj.winner.get_full_name() or obj.winner.email
            return format_html(
                '<span style="color: #2ecc71; font-weight: bold;">🏆 {}</span><br>'
                '<small>{} : {} vs {} : {}</small>',
                winner_name,
                obj.challenger.get_full_name() or obj.challenger.email,
                obj.challenger_correct,
                obj.opponent_correct,
                obj.opponent.get_full_name() or obj.opponent.email
            )
        return '-'

    result_display.short_description = 'Natija'

    def cancel_battles(self, request, queryset):
        queryset.filter(status__in=['pending', 'accepted']).update(status='rejected')

    cancel_battles.short_description = "Bekor qilish"

    def expire_battles(self, request, queryset):
        queryset.filter(status='pending').update(status='expired')

    expire_battles.short_description = "Muddati o'tgan deb belgilash"


@admin.register(BattleInvitation)
class BattleInvitationAdmin(admin.ModelAdmin):
    list_display = ('battle', 'sent_at', 'seen_at', 'responded_at', 'is_seen', 'is_responded')
    list_filter = ('sent_at', 'seen_at', 'responded_at')
    search_fields = ('battle__challenger__email', 'battle__opponent__email')
    readonly_fields = ('sent_at', 'seen_at', 'responded_at')
    date_hierarchy = 'sent_at'

    def is_seen(self, obj):
        if obj.seen_at:
            return format_html('<span style="color: #2ecc71;">✓</span>')
        return format_html('<span style="color: #e74c3c;">✗</span>')

    is_seen.short_description = 'Ko\'rilgan'

    def is_responded(self, obj):
        if obj.responded_at:
            return format_html('<span style="color: #2ecc71;">✓</span>')
        return format_html('<span style="color: #e74c3c;">✗</span>')

    is_responded.short_description = 'Javob berilgan'


class DailyChallengeParticipantInline(admin.TabularInline):
    model = DailyChallengeParticipant
    extra = 0
    readonly_fields = ('user', 'score', 'correct_answers', 'xp_earned', 'completed_at')
    fields = ('user', 'score', 'correct_answers', 'time_spent', 'xp_earned')
    can_delete = False


@admin.register(DailyChallenge)
class DailyChallengeAdmin(admin.ModelAdmin):
    list_display = ('date', 'subject', 'xp_reward', 'participants_count', 'is_active', 'question_count_display')
    list_filter = ('is_active', 'date', 'subject')
    search_fields = ('date',)
    filter_horizontal = ('questions',)
    readonly_fields = ('participants_count', 'created_at')
    date_hierarchy = 'date'
    inlines = [DailyChallengeParticipantInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('date', 'subject', 'questions')
        }),
        ('Mukofotlar', {
            'fields': ('xp_reward',)
        }),
        ('Statistika', {
            'fields': ('participants_count', 'is_active'),
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_challenges', 'deactivate_challenges']

    def question_count_display(self, obj):
        count = obj.questions.count()
        return format_html(
            '<span style="background-color: #3498db; color: white; padding: 3px 10px; border-radius: 3px;">{} ta</span>',
            count
        )

    question_count_display.short_description = 'Savollar'

    def activate_challenges(self, request, queryset):
        queryset.update(is_active=True)

    activate_challenges.short_description = "Faollashtirish"

    def deactivate_challenges(self, request, queryset):
        queryset.update(is_active=False)

    deactivate_challenges.short_description = "O'chirish"


@admin.register(DailyChallengeParticipant)
class DailyChallengeParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'challenge', 'score', 'correct_answers', 'time_spent', 'xp_earned', 'completed_at',
                    'rank_display')
    list_filter = ('challenge__date', 'completed_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'completed_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('challenge', 'user')
        }),
        ('Natijalar', {
            'fields': ('score', 'correct_answers', 'time_spent', 'xp_earned')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('completed_at',)
        }),
    )

    def rank_display(self, obj):
        # Get rank within same challenge
        rank = DailyChallengeParticipant.objects.filter(
            challenge=obj.challenge,
            score__gt=obj.score
        ).count() + 1

        if rank == 1:
            return format_html(
                '<span style="background-color: #f1c40f; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥇 1</span>')
        elif rank == 2:
            return format_html(
                '<span style="background-color: #95a5a6; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥈 2</span>')
        elif rank == 3:
            return format_html(
                '<span style="background-color: #cd7f32; color: white; padding: 5px 10px; border-radius: 50%; font-weight: bold;">🥉 3</span>')
        else:
            return format_html(
                '<span style="background-color: #3498db; color: white; padding: 5px 10px; border-radius: 50%;">{}</span>',
                rank)

    rank_display.short_description = 'Reyting'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'challenge', 'challenge__subject')