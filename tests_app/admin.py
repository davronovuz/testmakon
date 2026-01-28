import json
import uuid
from django.contrib import admin
from django.utils.html import format_html
from django.utils.text import slugify
from import_export import resources, fields
from import_export.admin import ImportExportModelAdmin, ExportActionModelAdmin

from .models import (
    Subject, Topic, Question, Answer,
    Test, TestQuestion, TestAttempt, AttemptAnswer, SavedQuestion,
    UserTopicPerformance, UserSubjectPerformance, DailyUserStats,
    UserStudySession, UserActivityLog, UserAnalyticsSummary
)


# =========================================================
# YORDAMCHI FUNKSIYALAR
# =========================================================
def pretty_json(data):
    try:
        result = json.dumps(data, indent=4, ensure_ascii=False)
        return format_html('<pre>{}</pre>', result)
    except:
        return str(data)


# =========================================================
# IMPORT RESURSI (XATOSIZ VERSIYA)
# =========================================================

class QuestionResource(resources.ModelResource):
    # CSV ustun nomlarini modelga bog'lash
    text = fields.Field(attribute='text', column_name='Savol')
    difficulty = fields.Field(attribute='difficulty', column_name='Qiyinlik')

    # Variantlar
    option_a = fields.Field(column_name='A')
    option_b = fields.Field(column_name='B')
    option_c = fields.Field(column_name='C')
    option_d = fields.Field(column_name='D')
    correct_option = fields.Field(column_name='Togri_javob')

    class Meta:
        model = Question
        fields = (
            'id', 'text', 'difficulty', 'points',
            'option_a', 'option_b', 'option_c', 'option_d', 'correct_option'
        )
        import_id_fields = []  # ID tekshiruvi shart emas

    def before_import_row(self, row, **kwargs):
        """Fan va Mavzuni aniqlash"""
        # 1. FANNI ANIQLASH
        sub_name = row.get('Fan')
        if not sub_name:
            sub_name = "Umumiy Fan"

        sub_name = str(sub_name).strip()
        sub_slug = slugify(sub_name) or str(uuid.uuid4())[:8]

        self.temp_subject, _ = Subject.objects.get_or_create(
            name=sub_name,
            defaults={'slug': sub_slug, 'is_active': True}
        )

        # 2. MAVZUNI ANIQLASH
        top_name = row.get('Mavzu')
        if not top_name:
            top_name = "Umumiy Mavzu"

        top_name = str(top_name).strip()
        top_slug = slugify(top_name) or str(uuid.uuid4())[:8]

        self.temp_topic, _ = Topic.objects.get_or_create(
            name=top_name,
            subject=self.temp_subject,
            defaults={'slug': top_slug, 'is_active': True}
        )

    # --- TUZATILGAN JOY (TypeError yechimi) ---
    # Argumentlarni *args va **kwargs ga o'tkazdik.
    # Bu versiyalar o'rtasidagi mojarolarni butunlay yo'q qiladi.
    def before_save_instance(self, instance, row, *args, **kwargs):
        if hasattr(self, 'temp_subject'):
            instance.subject = self.temp_subject
        if hasattr(self, 'temp_topic'):
            instance.topic = self.temp_topic

    # --- TUZATILGAN JOY ---
    def after_save_instance(self, instance, row, *args, **kwargs):
        if kwargs.get('dry_run', False):
            return

        options = [
            {'text': row.get('A'), 'key': 'A'},
            {'text': row.get('B'), 'key': 'B'},
            {'text': row.get('C'), 'key': 'C'},
            {'text': row.get('D'), 'key': 'D'},
        ]

        correct_val = row.get('Togri_javob')
        correct_key = str(correct_val).strip().upper() if correct_val else ''

        instance.answers.all().delete()

        for idx, opt in enumerate(options):
            if opt['text']:
                Answer.objects.create(
                    question=instance,
                    text=str(opt['text']).strip(),
                    is_correct=(opt['key'] == correct_key),
                    order=idx
                )


# =========================================================
# ADMIN KLASSLAR
# =========================================================

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    min_num = 2
    fields = ('text', 'is_correct', 'order')


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    prepopulated_fields = {'slug': ('name',)}


class TestQuestionInline(admin.TabularInline):
    model = TestQuestion
    extra = 1
    autocomplete_fields = ['question']
    fields = ('question', 'order')


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    can_delete = False
    readonly_fields = ('question', 'selected_answer', 'is_correct', 'time_spent')

    def has_add_permission(self, request, obj=None): return False


# =========================================================
# REGISTRATSIYA
# =========================================================

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'stats_view', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TopicInline]

    def stats_view(self, obj):
        return format_html(
            '<span style="color:blue">Tests: {}</span> | <span style="color:green">Questions: {}</span>',
            obj.total_tests, obj.total_questions
        )


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'parent', 'is_active', 'order')
    list_filter = ('subject', 'is_active')
    search_fields = ('name', 'subject__name')
    autocomplete_fields = ['parent', 'subject']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    resource_class = QuestionResource

    list_display = ('short_text', 'subject', 'topic', 'difficulty', 'is_active', 'created_at')
    list_filter = ('subject', 'difficulty', 'is_active', 'created_at')
    search_fields = ('text', 'subject__name', 'topic__name')
    autocomplete_fields = ['subject', 'topic']
    inlines = [AnswerInline]

    def short_text(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_type', 'subject', 'question_count', 'status_badge', 'is_premium')
    list_filter = ('test_type', 'subject', 'is_active', 'is_premium')
    search_fields = ('title', 'description')
    autocomplete_fields = ['subject']
    filter_horizontal = ('subjects',)
    inlines = [TestQuestionInline]
    prepopulated_fields = {'slug': ('title',)}

    def status_badge(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="background:green; color:white; padding:3px 6px; border-radius:3px;">Active</span>')
        return format_html(
            '<span style="background:red; color:white; padding:3px 6px; border-radius:3px;">Inactive</span>')


@admin.register(TestAttempt)
class TestAttemptAdmin(ExportActionModelAdmin):
    list_display = ('user', 'test', 'score_display', 'status', 'started_at', 'time_spent_formatted')
    list_filter = ('status', 'test__subject', 'started_at')
    search_fields = ('user__username', 'test__title')
    autocomplete_fields = ['user', 'test']
    readonly_fields = ('uuid', 'user', 'test', 'status', 'total_questions', 'correct_answers', 'wrong_answers', 'score',
                       'percentage', 'xp_earned', 'started_at', 'completed_at', 'json_analysis')
    inlines = [AttemptAnswerInline]

    def score_display(self, obj):
        color = 'green' if obj.percentage >= 80 else 'orange' if obj.percentage >= 60 else 'red'
        return format_html('<b style="color:{}">{}%</b>', color, obj.percentage)

    def time_spent_formatted(self, obj):
        return f"{obj.time_spent // 60}m {obj.time_spent % 60}s"

    def json_analysis(self, obj):
        data = {"weak": obj.weak_topics, "strong": obj.strong_topics, "rec": obj.ai_recommendations}
        return pretty_json(data)


# Qolgan adminlar
@admin.register(DailyUserStats)
class DailyUserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'tests_taken')


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'created_at')


@admin.register(UserTopicPerformance)
class UserTopicPerformanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'current_score')


@admin.register(UserSubjectPerformance)
class UserSubjectPerformanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'average_score')


@admin.register(UserStudySession)
class UserStudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'started_at', 'duration')


@admin.register(UserAnalyticsSummary)
class UserAnalyticsSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'overall_accuracy')


@admin.register(SavedQuestion)
class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')


admin.site.site_header = "TestMakon SuperAdmin"
admin.site.site_title = "TestMakon"