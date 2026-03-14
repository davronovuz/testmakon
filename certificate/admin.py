"""
TestMakon.uz — Milliy Sertifikat Admin
"""
import json
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.utils.html import format_html
from django.contrib import messages
from django.db import transaction
from .models import (
    CertSubject, CertMock, CertQuestion,
    CertChoice, CertGroupedOption, CertGroupedItem,
    CertShortOpen, CertMultiPart,
    CertMockAttempt, CertAttemptAnswer
)


# ─────────────────────────────────────────────────────────────
# INLINES
# ─────────────────────────────────────────────────────────────

def _img_thumb(url, size=60):
    """Rasm thumbnail HTML"""
    if not url:
        return '—'
    return format_html(
        '<img src="{}" style="height:{}px;max-width:{}px;'
        'object-fit:cover;border-radius:6px;border:1px solid #e2e8f0;" />',
        url, size, size * 2
    )


class CertChoiceInline(admin.TabularInline):
    model = CertChoice
    extra = 4
    fields = ('label', 'text', 'image', 'choice_thumb', 'is_correct', 'order')
    readonly_fields = ('choice_thumb',)

    def choice_thumb(self, obj):
        return _img_thumb(obj.image.url if obj.image else None, 40)
    choice_thumb.short_description = 'Ko\'rinish'


class CertGroupedOptionInline(admin.TabularInline):
    model = CertGroupedOption
    extra = 6
    fields = ('label', 'text', 'order')


class CertGroupedItemInline(admin.TabularInline):
    model = CertGroupedItem
    extra = 3
    fields = ('item_number', 'text', 'image', 'item_thumb', 'correct_option')
    readonly_fields = ('item_thumb',)

    def item_thumb(self, obj):
        return _img_thumb(obj.image.url if obj.image else None, 40)
    item_thumb.short_description = 'Rasm'


class CertShortOpenInline(admin.StackedInline):
    model = CertShortOpen
    extra = 0
    fields = ('correct_answer', 'answer_type', 'tolerance', 'case_sensitive')


class CertMultiPartInline(admin.TabularInline):
    model = CertMultiPart
    extra = 2
    fields = ('part_label', 'text', 'points', 'correct_answer', 'answer_type', 'requires_manual_check', 'tolerance', 'order')


class CertQuestionInline(admin.StackedInline):
    model = CertQuestion
    extra = 0
    fields = (
        ('number', 'question_type', 'points', 'is_active'),
        'text',
        'image',
        'q_thumb',
    )
    readonly_fields = ('q_thumb',)
    show_change_link = True
    ordering = ('number',)

    def q_thumb(self, obj):
        return _img_thumb(obj.image.url if obj.image else None, 80)
    q_thumb.short_description = 'Rasm ko\'rinishi'


class CertAttemptAnswerInline(admin.TabularInline):
    model = CertAttemptAnswer
    extra = 0
    readonly_fields = ('question', 'selected_choice', 'text_answer', 'structured_answer',
                       'is_correct', 'is_skipped', 'earned_points', 'checked_at')
    can_delete = False


# ─────────────────────────────────────────────────────────────
# CERT SUBJECT
# ─────────────────────────────────────────────────────────────

@admin.register(CertSubject)
class CertSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'total_mocks', 'order', 'is_active')
    list_editable = ('order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('subject__name',)
    autocomplete_fields = ['subject']
    actions = ['update_stats', 'auto_create_all']

    def update_stats(self, request, queryset):
        for obj in queryset:
            obj.update_stats()
        self.message_user(request, "Statistika yangilandi")
    update_stats.short_description = "Statistikani yangilash"

    def auto_create_all(self, request, queryset):
        """Barcha mavjud Subject lar uchun CertSubject yaratish"""
        from tests_app.models import Subject
        created = 0
        for subj in Subject.objects.filter(is_active=True):
            _, is_new = CertSubject.objects.get_or_create(
                subject=subj,
                defaults={'is_active': True, 'order': subj.order}
            )
            if is_new:
                created += 1
        self.message_user(request, f"{created} ta yangi CertSubject yaratildi")
    auto_create_all.short_description = "Barcha fanlar uchun CertSubject yaratish"


# ─────────────────────────────────────────────────────────────
# CERT MOCK
# ─────────────────────────────────────────────────────────────

@admin.register(CertMock)
class CertMockAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'cert_subject', 'year', 'version',
        'is_free_badge', 'questions_count', 'total_points',
        'time_limit', 'order', 'is_active'
    )
    list_editable = ('order', 'is_active')
    list_filter = ('cert_subject', 'is_free', 'is_active', 'year')
    search_fields = ('title', 'cert_subject__subject__name')
    prepopulated_fields = {'slug': ('title',)}
    inlines = [CertQuestionInline]
    actions = ['update_cached_stats']

    def is_free_badge(self, obj):
        if obj.is_free:
            return format_html('<span style="color:green;font-weight:bold">✓ Bepul</span>')
        return format_html('<span style="color:#e67e22;font-weight:bold">⭐ Premium</span>')
    is_free_badge.short_description = 'Kirish'

    def update_cached_stats(self, request, queryset):
        for obj in queryset:
            obj.update_cached_stats()
            obj.cert_subject.update_stats()
        self.message_user(request, "Cache yangilandi")
    update_cached_stats.short_description = "Cache-ni yangilash"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'import-json/',
                self.admin_site.admin_view(self.import_json_view),
                name='certificate_certmock_import_json',
            ),
        ]
        return custom_urls + urls

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_json_url'] = reverse('admin:certificate_certmock_import_json')
        return super().changelist_view(request, extra_context=extra_context)

    def import_json_view(self, request):
        from tests_app.models import Subject

        if request.method == 'POST':
            json_file = request.FILES.get('json_file')
            cert_subject_id = request.POST.get('cert_subject') or ''
            is_free = request.POST.get('is_free') == 'on'
            do_update = request.POST.get('do_update') == 'on'

            if not json_file:
                self.message_user(request, "JSON fayl tanlanmadi!", level=messages.ERROR)
                return redirect('.')

            try:
                content = json_file.read().decode('utf-8')
                data = json.loads(content)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                self.message_user(request, f"JSON o'qib bo'lmadi: {e}", level=messages.ERROR)
                return redirect('.')

            mocks_data = data if isinstance(data, list) else [data]

            imported = 0
            mock_titles = []
            errors = []

            for idx, mock_data in enumerate(mocks_data):
                mock_title = mock_data.get('mock_title') or mock_data.get('title', f'Mock #{idx+1}')
                try:
                    with transaction.atomic():
                        count, mock_obj = self._do_import_mock(
                            mock_data, cert_subject_id, is_free, do_update
                        )
                        imported += count
                        mock_titles.append(
                            f'"{mock_obj.title}" — {count} ta savol'
                        )
                except Exception as e:
                    import traceback
                    detail = traceback.format_exc().strip().split('\n')[-1]
                    errors.append(f'[{mock_title}] {e} | {detail}')

            if errors:
                for err in errors:
                    self.message_user(request, f"Xato: {err}", level=messages.ERROR)

            if mock_titles:
                self.message_user(
                    request,
                    f"Import muvaffaqiyatli! Jami {imported} ta savol. "
                    + " | ".join(mock_titles),
                    level=messages.SUCCESS
                )
            elif not errors:
                self.message_user(
                    request,
                    "Hech narsa import qilinmadi. "
                    "Ehtimol mock allaqachon mavjud — "
                    "'Mavjudlarni yangilash' checkboxini belgilang.",
                    level=messages.WARNING
                )

            return redirect(reverse('admin:certificate_certmock_changelist'))

        cert_subjects = CertSubject.objects.select_related('subject').filter(is_active=True)
        context = {
            **self.admin_site.each_context(request),
            'title': 'JSON dan import',
            'cert_subjects': cert_subjects,
            'opts': self.model._meta,
        }
        return render(request, 'admin/certificate/import_json.html', context)

    def _do_import_mock(self, data, cert_subject_id, is_free, do_update):
        """Import a single mock from JSON data. Returns (created_count, mock_obj)."""
        from tests_app.models import Subject

        # Resolve CertSubject
        if cert_subject_id:
            cert_subject = CertSubject.objects.get(pk=int(cert_subject_id))
        else:
            subject_slug = data.get('subject_slug') or data.get('subject')
            if not subject_slug:
                raise ValueError(
                    "Fan tanlanmadi va JSON da 'subject_slug' yo'q. "
                    "Dropdowndan fan tanlang yoki JSON ga subject_slug qo'shing."
                )
            try:
                subject = Subject.objects.get(slug=subject_slug)
            except Subject.DoesNotExist:
                available = ', '.join(Subject.objects.values_list('slug', flat=True)[:10])
                raise ValueError(
                    f"Fan topilmadi: slug='{subject_slug}'. "
                    f"Mavjud sluglar: {available}"
                )
            cert_subject, _ = CertSubject.objects.get_or_create(
                subject=subject,
                defaults={'is_active': True, 'order': 0}
            )

        mock_slug = data.get('mock_slug') or data.get('slug')
        mock_title = data.get('mock_title') or data.get('title', 'Mock')

        mock_defaults = {
            'title': mock_title,
            'year': data.get('year'),
            'version': data.get('version', ''),
            'time_limit': data.get('time_limit', 150),
            'is_free': is_free,
            'is_active': True,
        }

        if do_update:
            mock, _ = CertMock.objects.update_or_create(
                cert_subject=cert_subject, slug=mock_slug,
                defaults=mock_defaults
            )
        else:
            mock, _ = CertMock.objects.get_or_create(
                cert_subject=cert_subject, slug=mock_slug,
                defaults=mock_defaults
            )

        questions = data.get('questions', [])
        created_q = 0

        for q_data in questions:
            number = q_data.get('number')
            qtype = q_data.get('type')
            if not number or not qtype:
                continue

            # Topic slug orqali Topic topish
            topic_obj = None
            topic_slug = q_data.get('topic_slug') or q_data.get('topic')
            if topic_slug:
                try:
                    from tests_app.models import Topic
                    topic_obj = Topic.objects.get(slug=topic_slug)
                except Exception:
                    pass

            q_defaults = {
                'question_type': qtype,
                'text': q_data.get('text', ''),
                'points': q_data.get('points', 1),
                'difficulty': q_data.get('difficulty', 'medium'),
                'explanation': q_data.get('explanation', ''),
                'hint': q_data.get('hint', ''),
                'source': q_data.get('source', ''),
                'year': q_data.get('year'),
                'is_active': True,
            }
            if topic_obj:
                q_defaults['topic'] = topic_obj

            if do_update:
                q, q_created = CertQuestion.objects.update_or_create(
                    mock=mock, number=number, defaults=q_defaults
                )
            else:
                q, q_created = CertQuestion.objects.get_or_create(
                    mock=mock, number=number, defaults=q_defaults
                )

            if not q_created and not do_update:
                continue

            if do_update and not q_created:
                q.choices.all().delete()
                q.grouped_options.all().delete()
                q.grouped_items.all().delete()
                CertShortOpen.objects.filter(question=q).delete()
                q.parts.all().delete()

            if qtype == 'choice':
                for opt in q_data.get('choices', []):
                    CertChoice.objects.create(
                        question=q,
                        label=opt.get('label', 'A'),
                        text=opt.get('text', ''),
                        is_correct=opt.get('is_correct', False),
                        order=opt.get('order', 0),
                    )
            elif qtype == 'grouped_af':
                option_map = {}
                for opt in q_data.get('options', []):
                    obj = CertGroupedOption.objects.create(
                        question=q,
                        label=opt.get('label', 'A'),
                        text=opt.get('text', ''),
                        order=opt.get('order', 0),
                    )
                    option_map[opt.get('label')] = obj
                for item in q_data.get('items', []):
                    correct_label = item.get('correct_option')
                    CertGroupedItem.objects.create(
                        question=q,
                        item_number=item.get('number', 1),
                        text=item.get('text', ''),
                        correct_option=option_map.get(correct_label),
                    )
            elif qtype == 'short_open':
                ans = q_data.get('answer', {})
                CertShortOpen.objects.create(
                    question=q,
                    correct_answer=str(ans.get('value', '')),
                    answer_type=ans.get('type', 'text'),
                    tolerance=ans.get('tolerance', 0.0),
                    case_sensitive=ans.get('case_sensitive', False),
                )
            elif qtype == 'multi_part':
                for i, part in enumerate(q_data.get('parts', [])):
                    CertMultiPart.objects.create(
                        question=q,
                        part_label=part.get('label', chr(97 + i)),
                        text=part.get('text', ''),
                        points=part.get('points', 1),
                        correct_answer=str(part.get('answer', '')),
                        answer_type=part.get('answer_type', 'text'),
                        requires_manual_check=part.get('manual_check', False),
                        tolerance=part.get('tolerance', 0.0),
                        order=i,
                    )

            created_q += 1

        mock.update_cached_stats()
        cert_subject.update_stats()
        return created_q, mock


# ─────────────────────────────────────────────────────────────
# CERT QUESTION
# ─────────────────────────────────────────────────────────────

@admin.register(CertQuestion)
class CertQuestionAdmin(admin.ModelAdmin):
    list_display = (
        'number', 'mock', 'question_type', 'topic_name',
        'difficulty', 'image_thumb', 'points', 'times_answered', 'irt_cr', 'is_active'
    )
    list_filter = ('question_type', 'difficulty', 'is_active', 'mock__cert_subject')
    search_fields = ('text', 'mock__title', 'topic__name')
    raw_id_fields = ('mock', 'topic')
    list_select_related = ('mock', 'mock__cert_subject')
    readonly_fields = ('image_preview',)

    def topic_name(self, obj):
        return obj.topic.name if obj.topic else '—'
    topic_name.short_description = 'Mavzu'
    topic_name.admin_order_field = 'topic__name'

    def irt_cr(self, obj):
        if obj.times_answered >= 5:
            pct = round(obj.times_correct / obj.times_answered * 100)
            color = '#16a34a' if pct >= 60 else ('#d97706' if pct >= 40 else '#dc2626')
            return format_html('<span style="color:{};font-weight:700;">{}%</span>', color, pct)
        return '—'
    irt_cr.short_description = 'To\'g\'rilik %'

    def image_thumb(self, obj):
        return _img_thumb(obj.image.url if obj.image else None, 40)
    image_thumb.short_description = 'Rasm'

    def image_preview(self, obj):
        return _img_thumb(obj.image.url if obj.image else None, 200)
    image_preview.short_description = 'Rasm ko\'rinishi'

    def get_inlines(self, request, obj=None):
        if obj is None:
            return []
        qtype = obj.question_type
        if qtype == 'choice':
            return [CertChoiceInline]
        elif qtype == 'grouped_af':
            return [CertGroupedOptionInline, CertGroupedItemInline]
        elif qtype == 'short_open':
            return [CertShortOpenInline]
        elif qtype == 'multi_part':
            return [CertMultiPartInline]
        return []

    fieldsets = (
        ('Asosiy', {
            'fields': ('mock', 'number', 'question_type', 'text')
        }),
        ('Rasm', {
            'fields': ('image', 'image_preview'),
        }),
        ('Metadata', {
            'fields': ('points', 'topic', 'difficulty', 'source', 'year')
        }),
        ('Qo\'shimcha', {
            'fields': ('explanation', 'hint', 'requires_manual_check', 'is_active'),
            'classes': ('collapse',),
        }),
    )


# ─────────────────────────────────────────────────────────────
# ATTEMPTS
# ─────────────────────────────────────────────────────────────

@admin.register(CertMockAttempt)
class CertMockAttemptAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'mock', 'status', 'grade', 'percentage',
        'correct_answers', 'wrong_answers', 'skipped_questions',
        'time_spent_fmt', 'started_at'
    )
    list_filter = ('status', 'grade', 'mock__cert_subject')
    search_fields = ('user__first_name', 'user__last_name', 'user__phone_number', 'mock__title')
    readonly_fields = (
        'uuid', 'user', 'mock', 'status', 'started_at', 'completed_at',
        'time_spent', 'total_questions', 'correct_answers', 'wrong_answers',
        'skipped_questions', 'total_points', 'earned_points', 'percentage',
        'grade', 'feedback', 'ip_address'
    )
    inlines = [CertAttemptAnswerInline]

    def time_spent_fmt(self, obj):
        m, s = divmod(obj.time_spent, 60)
        return f"{m}:{s:02d}"
    time_spent_fmt.short_description = 'Vaqt'

    def has_add_permission(self, request):
        return False
