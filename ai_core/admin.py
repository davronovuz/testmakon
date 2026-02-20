"""
TestMakon.uz - AI Core Admin
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.db.models import Count, Avg
from .models import (
    AIConversation,
    AIMessage,
    AIRecommendation,
    StudyPlan,
    StudyPlanTask,
    WeakTopicAnalysis
)


class AIMessageInline(admin.TabularInline):
    model = AIMessage
    extra = 0
    readonly_fields = ('created_at', 'tokens_used')
    fields = ('role', 'content', 'model_used', 'tokens_used', 'is_helpful')
    can_delete = False
    max_num = 10  # Faqat oxirgi 10 ta message ko'rsatish


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'conversation_type', 'title_display', 'message_count', 'is_active', 'created_at',
                    'type_badge')
    list_filter = ('conversation_type', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title')
    readonly_fields = ('uuid', 'message_count', 'created_at', 'updated_at')
    date_hierarchy = 'created_at'
    inlines = [AIMessageInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'user', 'conversation_type', 'title')
        }),
        ('Bog\'langan ma\'lumotlar', {
            'fields': ('subject', 'topic', 'test_attempt'),
            'classes': ('collapse',)
        }),
        ('Statistika', {
            'fields': ('message_count', 'is_active')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['archive_conversations', 'activate_conversations']

    def title_display(self, obj):
        return obj.title or "Yangi suhbat"

    title_display.short_description = 'Sarlavha'

    def type_badge(self, obj):
        colors = {
            'mentor': '#3498db',
            'tutor': '#2ecc71',
            'advisor': '#9b59b6',
            'analyzer': '#e67e22',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            colors.get(obj.conversation_type, '#95a5a6'),
            obj.get_conversation_type_display()
        )

    type_badge.short_description = 'Turi'

    def archive_conversations(self, request, queryset):
        queryset.update(is_active=False)

    archive_conversations.short_description = "Arxivga yuborish"

    def activate_conversations(self, request, queryset):
        queryset.update(is_active=True)

    activate_conversations.short_description = "Faollashtirish"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'subject', 'topic', 'test_attempt')


@admin.register(AIMessage)
class AIMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'role', 'content_preview', 'tokens_used', 'is_helpful', 'created_at', 'role_badge')
    list_filter = ('role', 'is_helpful', 'created_at', 'model_used')
    search_fields = ('content', 'conversation__user__email', 'conversation__title')
    readonly_fields = ('created_at', 'tokens_used')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('conversation', 'role', 'content')
        }),
        ('AI ma\'lumotlari', {
            'fields': ('model_used', 'tokens_used'),
            'classes': ('collapse',)
        }),
        ('Fikr-mulohaza', {
            'fields': ('is_helpful', 'feedback')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at',)
        }),
    )

    def content_preview(self, obj):
        preview = obj.content[:100]
        if len(obj.content) > 100:
            preview += '...'
        return preview

    content_preview.short_description = 'Matn'

    def role_badge(self, obj):
        colors = {
            'user': '#3498db',
            'assistant': '#2ecc71',
            'system': '#95a5a6',
        }
        icons = {
            'user': '👤',
            'assistant': '🤖',
            'system': '⚙️',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.role, '#95a5a6'),
            icons.get(obj.role, ''),
            obj.get_role_display()
        )

    role_badge.short_description = 'Rol'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('conversation', 'conversation__user')


@admin.register(AIRecommendation)
class AIRecommendationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'recommendation_type', 'priority', 'is_read', 'is_completed', 'created_at',
                    'priority_badge', 'status_icons')
    list_filter = ('recommendation_type', 'priority', 'is_read', 'is_completed', 'is_dismissed', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title', 'content')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'recommendation_type', 'priority', 'title', 'content')
        }),
        ('Bog\'langan ma\'lumotlar', {
            'fields': ('subject', 'topic'),
            'classes': ('collapse',)
        }),
        ('Harakat', {
            'fields': ('action_url', 'action_text')
        }),
        ('Holat', {
            'fields': ('is_read', 'is_dismissed', 'is_completed', 'expires_at')
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_completed', 'dismiss_recommendations']

    def priority_badge(self, obj):
        colors = {
            'low': '#95a5a6',
            'medium': '#3498db',
            'high': '#f39c12',
            'critical': '#e74c3c',
        }
        icons = {
            'low': '⬇️',
            'medium': '➡️',
            'high': '⬆️',
            'critical': '🔴',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.priority, '#95a5a6'),
            icons.get(obj.priority, ''),
            obj.get_priority_display()
        )

    priority_badge.short_description = 'Muhimlik'

    def status_icons(self, obj):
        icons = []
        if obj.is_read:
            icons.append('✅ O\'qilgan')
        if obj.is_completed:
            icons.append('✅ Bajarilgan')
        if obj.is_dismissed:
            icons.append('❌ Yopilgan')
        return format_html(' | '.join(icons)) if icons else '⏳ Kutilmoqda'

    status_icons.short_description = 'Holat'

    def mark_as_read(self, request, queryset):
        queryset.update(is_read=True)

    mark_as_read.short_description = "O'qilgan deb belgilash"

    def mark_as_completed(self, request, queryset):
        queryset.update(is_completed=True)

    mark_as_completed.short_description = "Bajarilgan deb belgilash"

    def dismiss_recommendations(self, request, queryset):
        queryset.update(is_dismissed=True)

    dismiss_recommendations.short_description = "Yopish"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'subject', 'topic')


class StudyPlanTaskInline(admin.TabularInline):
    model = StudyPlanTask
    extra = 0
    fields = ('title', 'task_type', 'scheduled_date', 'estimated_minutes', 'is_completed', 'order')
    ordering = ['scheduled_date', 'order']
    max_num = 20


@admin.register(StudyPlan)
class StudyPlanAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'status', 'progress_bar', 'total_tasks', 'completed_tasks', 'target_exam_date',
                    'created_at', 'status_badge')
    list_filter = ('status', 'created_at', 'target_exam_date')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title', 'description')
    readonly_fields = ('uuid', 'total_tasks', 'completed_tasks', 'progress_percentage', 'created_at', 'updated_at')
    filter_horizontal = ('subjects',)
    date_hierarchy = 'created_at'
    inlines = [StudyPlanTaskInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'user', 'title', 'description', 'status')
        }),
        ('Maqsad', {
            'fields': ('target_exam_date', 'target_score', 'target_university', 'target_direction')
        }),
        ('Fanlar va jadval', {
            'fields': ('subjects', 'daily_hours', 'weekly_days')
        }),
        ('Progress', {
            'fields': ('total_tasks', 'completed_tasks', 'progress_percentage')
        }),
        ('AI tahlili', {
            'fields': ('ai_analysis',),
            'classes': ('collapse',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_plans', 'pause_plans', 'complete_plans', 'abandon_plans']

    def status_badge(self, obj):
        colors = {
            'active': '#2ecc71',
            'paused': '#f39c12',
            'completed': '#3498db',
            'abandoned': '#95a5a6',
        }
        icons = {
            'active': '▶️',
            'paused': '⏸️',
            'completed': '✅',
            'abandoned': '❌',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.status, '#95a5a6'),
            icons.get(obj.status, ''),
            obj.get_status_display()
        )

    status_badge.short_description = 'Holat'

    def progress_bar(self, obj):
        percentage = obj.progress_percentage
        if percentage < 30:
            color = '#e74c3c'
            emoji = '🔴'
        elif percentage < 70:
            color = '#f39c12'
            emoji = '🟡'
        else:
            color = '#2ecc71'
            emoji = '🟢'

        return format_html(
            '<div style="width: 120px;">'
            '<div style="background-color: #ecf0f1; border-radius: 10px; overflow: hidden;">'
            '<div style="width: {}%; background-color: {}; color: white; text-align: center; padding: 2px 0; font-size: 11px; font-weight: bold;">'
            '{} {}%</div></div></div>',
            percentage, color, emoji, f'{percentage:.0f}'
        )

    progress_bar.short_description = 'Progress'

    def activate_plans(self, request, queryset):
        queryset.update(status='active')

    activate_plans.short_description = "Faollashtirish"

    def pause_plans(self, request, queryset):
        queryset.update(status='paused')

    pause_plans.short_description = "To'xtatish"

    def complete_plans(self, request, queryset):
        queryset.update(status='completed')

    complete_plans.short_description = "Yakunlangan deb belgilash"

    def abandon_plans(self, request, queryset):
        queryset.update(status='abandoned')

    abandon_plans.short_description = "Tashlab ketilgan deb belgilash"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'target_university', 'target_direction').prefetch_related('subjects')


@admin.register(StudyPlanTask)
class StudyPlanTaskAdmin(admin.ModelAdmin):
    list_display = ('study_plan_user', 'title', 'task_type', 'scheduled_date', 'estimated_minutes', 'is_completed',
                    'type_badge', 'completion_badge')
    list_filter = ('task_type', 'is_completed', 'scheduled_date', 'study_plan__status')
    search_fields = ('title', 'description', 'study_plan__user__email', 'study_plan__title')
    readonly_fields = ('completed_at',)
    date_hierarchy = 'scheduled_date'

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('study_plan', 'title', 'description', 'task_type', 'order')
        }),
        ('Bog\'langan ma\'lumotlar', {
            'fields': ('subject', 'topic', 'test'),
            'classes': ('collapse',)
        }),
        ('Jadval', {
            'fields': ('scheduled_date', 'estimated_minutes')
        }),
        ('Holat', {
            'fields': ('is_completed', 'completed_at', 'actual_minutes')
        }),
    )

    actions = ['mark_as_completed', 'mark_as_incomplete']

    def study_plan_user(self, obj):
        return obj.study_plan.user

    study_plan_user.short_description = 'Foydalanuvchi'

    def type_badge(self, obj):
        colors = {
            'study': '#3498db',
            'test': '#e74c3c',
            'review': '#f39c12',
            'practice': '#2ecc71',
        }
        icons = {
            'study': '📖',
            'test': '📝',
            'review': '🔄',
            'practice': '💪',
        }
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{} {}</span>',
            colors.get(obj.task_type, '#95a5a6'),
            icons.get(obj.task_type, ''),
            obj.get_task_type_display()
        )

    type_badge.short_description = 'Turi'

    def completion_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: #2ecc71; font-size: 18px;">✅</span>')
        return format_html('<span style="color: #e74c3c; font-size: 18px;">⏳</span>')

    completion_badge.short_description = 'Holat'

    def mark_as_completed(self, request, queryset):
        queryset.update(is_completed=True, completed_at=timezone.now())
        # Update study plan progress
        for task in queryset:
            task.study_plan.update_progress()

    mark_as_completed.short_description = "Bajarilgan deb belgilash"

    def mark_as_incomplete(self, request, queryset):
        queryset.update(is_completed=False, completed_at=None)
        # Update study plan progress
        for task in queryset:
            task.study_plan.update_progress()

    mark_as_incomplete.short_description = "Bajarilmagan deb belgilash"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('study_plan', 'study_plan__user', 'subject', 'topic', 'test')


@admin.register(WeakTopicAnalysis)
class WeakTopicAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'topic', 'accuracy_badge', 'total_questions', 'correct_answers',
                    'priority_score', 'last_updated')
    list_filter = ('subject', 'last_updated')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'topic__name', 'subject__name')
    readonly_fields = ('last_updated',)

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('user', 'subject', 'topic')
        }),
        ('Statistika', {
            'fields': ('total_questions', 'correct_answers', 'accuracy_rate', 'priority_score')
        }),
        ('AI tavsiyasi', {
            'fields': ('recommendation',)
        }),
        ('Tizim ma\'lumotlari', {
            'fields': ('last_updated',)
        }),
    )

    def accuracy_badge(self, obj):
        if obj.accuracy_rate >= 70:
            color = '#2ecc71'
            emoji = '🟢'
            status = 'Yaxshi'
        elif obj.accuracy_rate >= 50:
            color = '#f39c12'
            emoji = '🟡'
            status = 'O\'rtacha'
        elif obj.accuracy_rate >= 30:
            color = '#e67e22'
            emoji = '🟠'
            status = 'Zaif'
        else:
            color = '#e74c3c'
            emoji = '🔴'
            status = 'Juda zaif'

        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 12px; border-radius: 5px; font-weight: bold;">'
            '{} {}% - {}</span>',
            color, emoji, f'{obj.accuracy_rate:.1f}', status
        )

    accuracy_badge.short_description = 'To\'g\'rilik'

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user', 'subject', 'topic')
