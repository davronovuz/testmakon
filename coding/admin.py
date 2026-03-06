"""
TestMakon.uz — Coding Admin
"""

from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import (
    ProgrammingLanguage, CodingCategory, CodingProblem,
    TestCase, CodeSubmission, UserCodingStats,
)


class TestCaseInline(admin.TabularInline):
    model = TestCase
    extra = 2
    fields = ['order', 'input_data', 'expected_output', 'is_sample']


@admin.register(ProgrammingLanguage)
class ProgrammingLanguageAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'docker_image', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CodingCategory)
class CodingCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'icon', 'order']
    list_editable = ['order']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(CodingProblem)
class CodingProblemAdmin(ImportExportModelAdmin):
    list_display = ['order', 'title', 'difficulty', 'category', 'total_submissions', 'accepted_submissions', 'acceptance_rate', 'is_active']
    list_display_links = ['title']
    list_filter = ['difficulty', 'category', 'is_active', 'languages']
    search_fields = ['title', 'description']
    list_editable = ['order', 'is_active']
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ['languages']
    inlines = [TestCaseInline]
    readonly_fields = ['total_submissions', 'accepted_submissions', 'created_at']

    def acceptance_rate(self, obj):
        return f"{obj.acceptance_rate}%"
    acceptance_rate.short_description = "Qabul %"


@admin.register(CodeSubmission)
class CodeSubmissionAdmin(admin.ModelAdmin):
    list_display = ['user', 'problem', 'language', 'status', 'passed_count', 'total_count', 'execution_time', 'created_at']
    list_filter = ['status', 'language', 'is_sample_run']
    search_fields = ['user__phone_number', 'problem__title']
    readonly_fields = ['results', 'created_at']
    raw_id_fields = ['user', 'problem']


@admin.register(UserCodingStats)
class UserCodingStatsAdmin(admin.ModelAdmin):
    list_display = ['user', 'problems_solved', 'problems_attempted', 'easy_solved', 'medium_solved', 'hard_solved', 'current_streak']
    search_fields = ['user__phone_number']
    readonly_fields = ['updated_at']
    raw_id_fields = ['user']
