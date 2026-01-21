from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Subject, Topic, Question, Answer,
    Test, TestQuestion, TestAttempt,
    AttemptAnswer, SavedQuestion
)


# --- INLINES ---

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('text', 'is_correct', 'order', 'image')


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 5
    autocomplete_fields = ['question']


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'is_correct', 'time_spent', 'answered_at')
    can_delete = False


# --- ADMIN CLASSES ---

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('icon_display', 'name', 'total_questions', 'total_tests', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}
    list_filter = ('is_active',)

    def icon_display(self, obj):
        return format_html('<span style="font-size: 1.2rem;">{}</span>', obj.icon)

    icon_display.short_description = 'Ikonka'


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'parent', 'order', 'is_active')
    list_filter = ('subject', 'is_active')
    search_fields = ('name', 'subject__name')
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['subject', 'parent']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'subject', 'topic', 'question_type', 'difficulty', 'correct_rate_display',
                    'is_active')
    list_filter = ('subject', 'difficulty', 'question_type', 'is_active', 'created_at')
    search_fields = ('text', 'explanation', 'source')
    autocomplete_fields = ['subject', 'topic', 'created_by']
    inlines = [AnswerInline]
    readonly_fields = ('times_answered', 'times_correct', 'correct_rate_display')

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('subject', 'topic', 'text', 'image', 'question_type', 'difficulty')
        }),
        ('Ball va Vaqt', {
            'fields': ('points', 'time_limit')
        }),
        ('Tushuntirish va Maslahat', {
            'fields': ('explanation', 'hint')
        }),
        ('Statistika va Manba', {
            'fields': ('source', 'year', 'times_answered', 'times_correct', 'is_active', 'created_by')
        }),
    )

    def text_short(self, obj):
        return obj.text[:80] + "..." if len(obj.text) > 80 else obj.text

    text_short.short_description = 'Savol matni'

    def correct_rate_display(self, obj):
        rate = obj.correct_rate
        color = "red" if rate < 40 else "orange" if rate < 70 else "green"
        return format_html('<b style="color: {};">{}%</b>', color, rate)

    correct_rate_display.short_description = 'To\'g\'rilik %'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_type', 'subject', 'question_count', 'is_active', 'is_premium', 'is_available')
    list_filter = ('test_type', 'is_active', 'is_premium', 'subject')
    search_fields = ('title', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('subjects',)  # Block testlar uchun fanlarni tanlash qulay bo'lishi uchun
    inlines = [TestQuestionInline]

    fieldsets = (
        ('Umumiy', {
            'fields': ('title', 'slug', 'description', 'test_type', 'subject', 'subjects', 'is_active', 'is_premium')
        }),
        ('Sozlamalar', {
            'fields': ('time_limit', 'question_count', 'passing_score', 'shuffle_questions', 'shuffle_answers',
                       'show_correct_answers')
        }),
        ('Vaqt oralig\'i', {
            'fields': ('start_date', 'end_date')
        }),
        ('Statistika', {
            'fields': ('total_attempts', 'average_score'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'status', 'score_display', 'time_spent_min', 'started_at')
    list_filter = ('status', 'started_at', 'test__test_type')
    search_fields = ('user__username', 'test__title')
    readonly_fields = (
        'uuid', 'user', 'test', 'status', 'current_question',
        'total_questions', 'correct_answers', 'wrong_answers',
        'skipped_questions', 'score', 'percentage', 'xp_earned',
        'time_spent', 'started_at', 'completed_at',
        'ai_analysis', 'ai_recommendations', 'weak_topics', 'strong_topics'
    )
    inlines = [AttemptAnswerInline]

    def score_display(self, obj):
        return format_html('<b>{}%</b> ({} ta to\'g\'ri)', obj.percentage, obj.correct_answers)

    score_display.short_description = 'Natija'

    def time_spent_min(self, obj):
        return f"{obj.time_spent // 60}m {obj.time_spent % 60}s"

    time_spent_min.short_description = 'Sarflangan vaqt'


@admin.register(SavedQuestion)
class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    search_fields = ('user__username', 'question__text')


# Savollarni autocomplete ishlatishi uchun kerak
admin.site.site_header = "TestMakon.uz Admin"
admin.site.site_title = "TestMakon Admin Portali"
admin.site.index_title = "Tizim boshqaruvi"