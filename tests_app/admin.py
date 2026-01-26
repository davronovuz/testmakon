# """
# TestMakon.uz - Tests App Admin
# """
#
# from django.contrib import admin
# from django.utils.html import format_html
#
# from .models import (
#     Subject, Topic, Question, Answer,
#     Test, TestQuestion, TestAttempt, AttemptAnswer, SavedQuestion
# )
#
#
# class AnswerInline(admin.TabularInline):
#     model = Answer
#     extra = 4
#     fields = ('text', 'is_correct', 'order')
#
#
# class TopicInline(admin.TabularInline):
#     model = Topic
#     extra = 1
#     fields = ('name', 'slug', 'order', 'is_active')
#     prepopulated_fields = {'slug': ('name',)}
#
#
# @admin.register(Subject)
# class SubjectAdmin(admin.ModelAdmin):
#     list_display = ('name', 'icon', 'total_questions', 'total_tests', 'is_active', 'order')
#     list_editable = ('order', 'is_active')
#     search_fields = ('name',)
#     prepopulated_fields = {'slug': ('name',)}
#     inlines = [TopicInline]
#
#
# @admin.register(Topic)
# class TopicAdmin(admin.ModelAdmin):
#     list_display = ('name', 'subject', 'order', 'is_active')
#     list_filter = ('subject', 'is_active')
#     list_editable = ('order', 'is_active')
#     search_fields = ('name', 'subject__name')
#     prepopulated_fields = {'slug': ('name',)}
#
#
# @admin.register(Question)
# class QuestionAdmin(admin.ModelAdmin):
#     list_display = ('short_text', 'subject', 'topic', 'difficulty', 'is_active')
#     list_filter = ('subject', 'topic', 'difficulty', 'is_active')
#     list_editable = ('is_active',)
#     search_fields = ('text', 'subject__name', 'topic__name')
#     inlines = [AnswerInline]
#
#     fieldsets = (
#         ('Asosiy', {
#             'fields': ('subject', 'topic', 'text', 'image')
#         }),
#         ('Sozlamalar', {
#             'fields': ('question_type', 'difficulty', 'points', 'time_limit')
#         }),
#         ('Tushuntirish', {
#             'fields': ('explanation', 'hint'),
#             'classes': ('collapse',)
#         }),
#         ('Boshqa', {
#             'fields': ('source', 'year', 'is_active'),
#             'classes': ('collapse',)
#         }),
#     )
#
#     def short_text(self, obj):
#         return obj.text[:80] + '...' if len(obj.text) > 80 else obj.text
#     short_text.short_description = 'Savol'
#
#
# @admin.register(Answer)
# class AnswerAdmin(admin.ModelAdmin):
#     list_display = ('short_text', 'question_short', 'is_correct')
#     list_filter = ('is_correct',)
#     search_fields = ('text', 'question__text')
#
#     def short_text(self, obj):
#         return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
#     short_text.short_description = 'Javob'
#
#     def question_short(self, obj):
#         return obj.question.text[:40] + '...'
#     question_short.short_description = 'Savol'
#
#
# @admin.register(Test)
# class TestAdmin(admin.ModelAdmin):
#     list_display = ('title', 'test_type', 'subject', 'question_count', 'time_limit', 'is_active', 'is_premium')
#     list_filter = ('test_type', 'subject', 'is_active', 'is_premium')
#     list_editable = ('is_active', 'is_premium')
#     search_fields = ('title',)
#     prepopulated_fields = {'slug': ('title',)}
#
#     fieldsets = (
#         ('Asosiy', {
#             'fields': ('title', 'slug', 'description', 'test_type', 'subject')
#         }),
#         ('Sozlamalar', {
#             'fields': ('time_limit', 'question_count', 'passing_score', 'shuffle_questions', 'shuffle_answers', 'show_correct_answers')
#         }),
#         ('Mavjudlik', {
#             'fields': ('is_active', 'is_premium', 'start_date', 'end_date')
#         }),
#     )
#
#
# @admin.register(TestAttempt)
# class TestAttemptAdmin(admin.ModelAdmin):
#     list_display = ('user', 'test', 'status', 'correct_answers', 'total_questions', 'percentage', 'started_at')
#     list_filter = ('status', 'test__subject', 'started_at')
#     search_fields = ('user__phone_number', 'user__first_name', 'test__title')
#     readonly_fields = ('uuid', 'user', 'test', 'status', 'total_questions', 'correct_answers', 'wrong_answers', 'percentage', 'xp_earned', 'started_at', 'completed_at')
#
#     def has_add_permission(self, request):
#         return False
#
#
# @admin.register(SavedQuestion)
# class SavedQuestionAdmin(admin.ModelAdmin):
#     list_display = ('user', 'question', 'created_at')
#     list_filter = ('created_at',)
#     search_fields = ('user__phone_number', 'question__text')
#
#
# admin.site.site_header = "TestMakon Admin"
# admin.site.site_title = "TestMakon"