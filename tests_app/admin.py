from django.contrib import admin
from django.utils.text import slugify
from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from import_export.admin import ImportExportModelAdmin
import uuid

from .models import (
    Subject, Topic, Question, Answer,
    Test, TestQuestion, TestAttempt, AttemptAnswer, SavedQuestion
)


# ---------------------------------------------------------
# 1. Excel Import Resursi
# ---------------------------------------------------------
class QuestionResource(resources.ModelResource):
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

    option_a = fields.Field(column_name='A variant')
    option_b = fields.Field(column_name='B variant')
    option_c = fields.Field(column_name='C variant')
    option_d = fields.Field(column_name='D variant')
    correct_option = fields.Field(column_name="To'g'ri javob")

    class Meta:
        model = Question
        fields = ('text', 'subject', 'topic', 'difficulty')
        import_id_fields = ('text',)

    # --- YANGI QO'SHILGAN QISM: Avtomatik yaratish ---
    def before_import_row(self, row, **kwargs):
        self.current_row = row

        # 1. FANNI TEKSHIRISH VA YARATISH
        subject_name = row.get('Fan')
        subject_obj = None

        if subject_name:
            # Slug yaratish (Matematika -> matematika)
            slug = slugify(subject_name)
            if not slug: slug = str(uuid.uuid4())[:8]  # Kirillcha bo'lsa muammo chiqmasligi uchun

            subject_obj, created = Subject.objects.get_or_create(
                name=subject_name,
                defaults={'slug': slug, 'is_active': True}
            )

        # 2. MAVZUNI TEKSHIRISH VA YARATISH
        topic_name = row.get('Mavzu')
        if topic_name and subject_obj:
            slug = slugify(topic_name)
            if not slug: slug = str(uuid.uuid4())[:8]

            Topic.objects.get_or_create(
                name=topic_name,
                subject=subject_obj,  # Mavzuni fanga bog'laymiz
                defaults={'slug': slug, 'is_active': True}
            )

    def after_save_instance(self, instance, using_transactions, dry_run):
        if dry_run: return

        row = self.current_row
        options = [
            {'text': row.get('A variant'), 'key': 'A'},
            {'text': row.get('B variant'), 'key': 'B'},
            {'text': row.get('C variant'), 'key': 'C'},
            {'text': row.get('D variant'), 'key': 'D'},
        ]
        correct_key = str(row.get("To'g'ri javob")).strip().upper()

        instance.answers.all().delete()

        for idx, opt in enumerate(options):
            if opt['text']:
                is_correct = (opt['key'] == correct_key)
                Answer.objects.create(
                    question=instance,
                    text=opt['text'],
                    is_correct=is_correct,
                    order=idx
                )


# ---------------------------------------------------------
# 2. Admin Klasslar
# ---------------------------------------------------------

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    fields = ('text', 'is_correct', 'order')


class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1
    fields = ('name', 'slug', 'order', 'is_active')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'total_questions', 'total_tests', 'is_active', 'order')
    list_editable = ('order', 'is_active')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    inlines = [TopicInline]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'order', 'is_active')
    list_filter = ('subject', 'is_active')
    list_editable = ('order', 'is_active')
    search_fields = ('name', 'subject__name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Question)
class QuestionAdmin(ImportExportModelAdmin):
    resource_class = QuestionResource

    list_display = ('short_text', 'subject', 'topic', 'difficulty', 'is_active')
    list_filter = ('subject', 'topic', 'difficulty', 'is_active')
    list_editable = ('is_active',)
    search_fields = ('text', 'subject__name', 'topic__name')
    inlines = [AnswerInline]

    fieldsets = (
        ('Asosiy', {
            'fields': ('subject', 'topic', 'text', 'image')
        }),
        ('Sozlamalar', {
            'fields': ('question_type', 'difficulty', 'points', 'time_limit')
        }),
        ('Tushuntirish', {
            'fields': ('explanation', 'hint'),
            'classes': ('collapse',)
        }),
        ('Boshqa', {
            'fields': ('source', 'year', 'is_active'),
            'classes': ('collapse',)
        }),
    )

    def short_text(self, obj):
        return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text

    short_text.short_description = 'Savol'


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('short_text', 'question_short', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')

    def short_text(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text

    short_text.short_description = 'Javob'

    def question_short(self, obj):
        return obj.question.text[:40] + '...'

    question_short.short_description = 'Savol'


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ('title', 'test_type', 'subject', 'question_count', 'time_limit', 'is_active', 'is_premium')
    list_filter = ('test_type', 'subject', 'is_active', 'is_premium')
    list_editable = ('is_active', 'is_premium')
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}

    fieldsets = (
        ('Asosiy', {
            'fields': ('title', 'slug', 'description', 'test_type', 'subject')
        }),
        ('Sozlamalar', {
            'fields': ('time_limit', 'question_count', 'passing_score', 'shuffle_questions', 'shuffle_answers',
                       'show_correct_answers')
        }),
        ('Mavjudlik', {
            'fields': ('is_active', 'is_premium', 'start_date', 'end_date')
        }),
    )


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'test', 'status', 'correct_answers', 'total_questions', 'percentage', 'started_at')
    list_filter = ('status', 'test__subject', 'started_at')
    search_fields = ('user__phone_number', 'user__first_name', 'test__title')
    readonly_fields = ('uuid', 'user', 'test', 'status', 'total_questions', 'correct_answers', 'wrong_answers',
                       'percentage', 'xp_earned', 'started_at', 'completed_at')

    def has_add_permission(self, request):
        return False


@admin.register(SavedQuestion)
class SavedQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__phone_number', 'question__text')


admin.site.site_header = "TestMakon Admin"
admin.site.site_title = "TestMakon"