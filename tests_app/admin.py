import json
import uuid
from django.contrib import admin
from django.utils.html import format_html, mark_safe
from django.db.models import JSONField
from django.forms import widgets
from django.utils.text import slugify
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
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
    """JSON ma'lumotlarni admin panelda chiroyli o'qish uchun"""
    try:
        result = json.dumps(data, indent=4, ensure_ascii=False)
        return format_html('<pre>{}</pre>', result)
    except:
        return str(data)


# =========================================================
# IMPORT-EXPORT RESURSLARI (MUKAMMAL VERSIYA)
# =========================================================

class QuestionResource(resources.ModelResource):
    """Exceldan savollarni yuklash uchun resurs"""

    # Model maydonlarini Excel ustunlariga bog'lash
    subject = fields.Field(
        column_name='Fan',
        attribute='subject',
        widget=ForeignKeyWidget(Subject, field='name')
    )
    topic = fields.Field(
        column_name='Mavzu',
        attribute='topic',
        widget=ForeignKeyWidget(Topic, field='name')
    )
    text = fields.Field(attribute='text', column_name='Savol matni')
    difficulty = fields.Field(attribute='difficulty', column_name='Qiyinlik')

    # Exceldagi vaqtinchalik maydonlar (Variantlar)
    option_a = fields.Field(column_name='A variant')
    option_b = fields.Field(column_name='B variant')
    option_c = fields.Field(column_name='C variant')
    option_d = fields.Field(column_name='D variant')
    correct_option = fields.Field(column_name="To'g'ri javob")

    class Meta:
        model = Question
        # MUHIM: Xatolik chiqmasligi uchun barcha ishlatiladigan maydonlar shu yerda bo'lishi SHART
        fields = (
            'id', 'text', 'subject', 'topic', 'difficulty', 'points',
            'option_a', 'option_b', 'option_c', 'option_d', 'correct_option'
        )
        # Import paytida savollarni matni bo'yicha tekshirish (dublikat bo'lmasligi uchun)
        import_id_fields = ('text',)

    # --- 1. AVTOMATIK YARATISH LOGIKASI (DoesNotExist xatosi uchun) ---
    def before_import_row(self, row, **kwargs):
        """
        Import qilishdan oldin Fan va Mavzuni tekshiradi.
        Agar ular yo'q bo'lsa, avtomatik yaratadi.
        """
        self.current_row = row

        # 1. FANNI TEKSHIRISH
        subject_name = row.get('Fan')
        subject_obj = None

        if subject_name:
            subject_name = str(subject_name).strip()  # Bo'sh joylarni tozalash

            # Slug yaratish
            slug = slugify(subject_name)
            if not slug: slug = str(uuid.uuid4())[:8]  # Agar slugify bo'sh qaytarsa (masalan kirillcha)

            # Bazadan olish yoki yaratish
            subject_obj, created = Subject.objects.get_or_create(
                name=subject_name,
                defaults={'slug': slug, 'is_active': True}
            )
            # Row'ni yangilash (ForeignKeyWidget topa olishi uchun)
            row['Fan'] = subject_obj.name

        # 2. MAVZUNI TEKSHIRISH
        topic_name = row.get('Mavzu')
        if topic_name and subject_obj:
            topic_name = str(topic_name).strip()

            slug = slugify(topic_name)
            if not slug: slug = str(uuid.uuid4())[:8]

            topic_obj, created = Topic.objects.get_or_create(
                name=topic_name,
                subject=subject_obj,
                defaults={'slug': slug, 'is_active': True}
            )
            row['Mavzu'] = topic_obj.name

    # --- 2. JAVOBLARNI SAQLASH (TypeError xatosi uchun) ---
    # **kwargs qo'shildi - bu 'file_name' xatosini yo'qotadi
    def after_save_instance(self, instance, using_transactions, dry_run, **kwargs):
        if dry_run: return

        row = self.current_row

        # Variantlarni ro'yxatga yig'ish
        options = [
            {'text': row.get('A variant'), 'key': 'A'},
            {'text': row.get('B variant'), 'key': 'B'},
            {'text': row.get('C variant'), 'key': 'C'},
            {'text': row.get('D variant'), 'key': 'D'},
        ]

        # To'g'ri javobni aniqlash
        correct_val = row.get("To'g'ri javob")
        correct_key = str(correct_val).strip().upper() if correct_val else ''

        # Eski javoblarni o'chirish (savol yangilanganda dublikat bo'lmasligi uchun)
        instance.answers.all().delete()

        # Yangi javoblarni yaratish
        for idx, opt in enumerate(options):
            if opt['text']:  # Agar variant bo'sh bo'lmasa
                Answer.objects.create(
                    question=instance,
                    text=str(opt['text']).strip(),
                    is_correct=(opt['key'] == correct_key),
                    order=idx
                )


# =========================================================
# INLINES (Ichma-ich jadvallar)
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
    autocomplete_fields = ['question']  # Savollarni qidirib topish uchun
    fields = ('question', 'order')


class AttemptAnswerInline(admin.TabularInline):
    """Urinish ichida javoblarni ko'rish (faqat o'qish uchun)"""
    model = AttemptAnswer
    extra = 0
    can_delete = False
    readonly_fields = ('question', 'selected_answer', 'is_correct', 'time_spent')

    def has_add_permission(self, request, obj=None):
        return False


# =========================================================
# ASOSIY ADMINLAR
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

    stats_view.short_description = "Statistika"


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
    list_display = ('short_text', 'subject', 'topic', 'difficulty', 'question_type', 'is_active', 'created_at')
    list_filter = ('subject', 'difficulty', 'question_type', 'is_active', 'created_at')
    search_fields = ('text', 'subject__name', 'topic__name')
    autocomplete_fields = ['subject', 'topic']
    inlines = [AnswerInline]

    fieldsets = (
        ('Asosiy Ma\'lumot', {
            'fields': (('subject', 'topic'), 'text', 'image')
        }),
        ('Sozlamalar', {
            'fields': (('difficulty', 'question_type'), ('points', 'time_limit'))
        }),
        ('AI va Tushuntirish', {
            'fields': ('explanation', 'hint'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('source', 'year', 'is_active', 'created_by')
        }),
    )

    def short_text(self, obj):
        return obj.text[:60] + "..." if len(obj.text) > 60 else obj.text

    short_text.short_description = "Savol"


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_type', 'subject', 'question_count', 'status_badge', 'is_premium')
    list_filter = ('test_type', 'subject', 'is_active', 'is_premium', 'created_at')
    search_fields = ('title', 'description')
    autocomplete_fields = ['subject']
    filter_horizontal = ('subjects',)
    inlines = [TestQuestionInline]
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Asosiy', {
            'fields': ('title', 'slug', 'description', ('test_type', 'subject'), 'subjects')
        }),
        ('Konfiguratsiya', {
            'fields': (('time_limit', 'question_count', 'passing_score'),
                       ('shuffle_questions', 'shuffle_answers', 'show_correct_answers'))
        }),
        ('Mavjudlik', {
            'fields': ('is_active', 'is_premium', ('start_date', 'end_date'))
        }),
    )

    def status_badge(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="background:green; color:white; padding:3px 6px; border-radius:3px;">Active</span>')
        return format_html(
            '<span style="background:red; color:white; padding:3px 6px; border-radius:3px;">Inactive</span>')

    status_badge.short_description = "Status"


@admin.register(TestAttempt)
class TestAttemptAdmin(ExportActionModelAdmin):
    """Test urinishlarini boshqarish (asosan o'qish uchun)"""
    list_display = ('user', 'test', 'score_display', 'status', 'started_at', 'time_spent_formatted')
    list_filter = ('status', 'test__subject', 'started_at')
    search_fields = ('user__username', 'user__first_name', 'test__title')
    autocomplete_fields = ['user', 'test']
    readonly_fields = ('uuid', 'user', 'test', 'status', 'total_questions', 'correct_answers', 'wrong_answers', 'score',
                       'percentage', 'xp_earned', 'started_at', 'completed_at', 'json_analysis')
    inlines = [AttemptAnswerInline]

    fieldsets = (
        ('Foydalanuvchi va Test', {
            'fields': (('user', 'test'), 'uuid')
        }),
        ('Natijalar', {
            'fields': (('score', 'percentage', 'xp_earned'), ('correct_answers', 'wrong_answers', 'total_questions'))
        }),
        ('Vaqt va Holat', {
            'fields': ('status', ('started_at', 'completed_at', 'time_spent'))
        }),
        ('AI Tahlili', {
            'fields': ('ai_analysis', 'json_analysis'),
            'classes': ('collapse',)
        })
    )

    def score_display(self, obj):
        color = 'red'
        if obj.percentage >= 80:
            color = 'green'
        elif obj.percentage >= 60:
            color = 'orange'
        return format_html('<b style="color:{}">{}%</b>', color, obj.percentage)

    score_display.short_description = "Natija"

    def time_spent_formatted(self, obj):
        mins = obj.time_spent // 60
        secs = obj.time_spent % 60
        return f"{mins}m {secs}s"

    time_spent_formatted.short_description = "Vaqt"

    def json_analysis(self, obj):
        data = {
            "weak_topics": obj.weak_topics,
            "strong_topics": obj.strong_topics,
            "recommendations": obj.ai_recommendations
        }
        return pretty_json(data)

    json_analysis.short_description = "JSON Data"


# =========================================================
# ANALYTICS VA STATISTIKA ADMINLARI
# =========================================================

@admin.register(DailyUserStats)
class DailyUserStatsAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'tests_taken', 'accuracy_rate', 'total_time_spent')
    list_filter = ('date',)
    search_fields = ('user__username',)
    date_hierarchy = 'date'
    readonly_fields = ('activity_json', 'subjects_json')

    def activity_json(self, obj): return pretty_json(obj.activity_hours)

    activity_json.short_description = "Faollik soatlari"

    def subjects_json(self, obj): return pretty_json(obj.subjects_practiced)

    subjects_json.short_description = "Fanlar"


@admin.register(UserActivityLog)
class UserActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'action', 'device_type', 'created_at')
    list_filter = ('action', 'created_at', 'device_type')
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('details_pretty',)

    def details_pretty(self, obj): return pretty_json(obj.details)

    details_pretty.short_description = "Tafsilotlar"


@admin.register(UserTopicPerformance)
class UserTopicPerformanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'topic', 'current_score', 'trend_icon', 'is_mastered')
    list_filter = ('score_trend', 'is_weak', 'is_mastered', 'subject')
    search_fields = ('user__username', 'topic__name')
    autocomplete_fields = ['user', 'topic', 'subject']

    def trend_icon(self, obj):
        icons = {'improving': '📈', 'stable': '➖', 'declining': '📉'}
        return icons.get(obj.score_trend, '')

    trend_icon.short_description = "Trend"


@admin.register(UserSubjectPerformance)
class UserSubjectPerformanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'subject', 'average_score', 'total_tests', 'subject_rank')
    search_fields = ('user__username', 'subject__name')
    list_filter = ('subject',)


@admin.register(UserStudySession)
class UserStudySessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'started_at', 'duration_min', 'device_type', 'is_active')
    list_filter = ('device_type', 'is_active', 'started_at')

    def duration_min(self, obj):
        return f"{obj.duration // 60} min"

    duration_min.short_description = "Davomiylik"


@admin.register(UserAnalyticsSummary)
class UserAnalyticsSummaryAdmin(admin.ModelAdmin):
    list_display = ('user', 'overall_accuracy', 'total_study_hours', 'learning_style')
    search_fields = ('user__username',)

    def total_study_hours(self, obj):
        return f"{obj.total_study_time} soat"


@admin.register(SavedQuestion)
class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    autocomplete_fields = ['user', 'question']


# =========================================================
# ADMIN HEADER SOZLAMALARI
# =========================================================
admin.site.site_header = "TestMakon SuperAdmin"
admin.site.site_title = "TestMakon Tizimi"
admin.site.index_title = "Boshqaruv Paneli"