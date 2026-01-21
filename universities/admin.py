"""
TestMakon.uz - Universities Admin Configuration
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    University, Faculty, Direction,
    PassingScore, UniversityReview, AdmissionCalculation
)


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'university_type', 'region',
                    'student_count', 'rating', 'is_partner', 'is_featured', 'is_active']
    list_filter = ['university_type', 'region', 'is_partner', 'is_featured', 'is_active']
    search_fields = ['name', 'short_name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'logo_preview']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'name', 'short_name', 'slug', 'university_type')
        }),
        ('Tavsif', {
            'fields': ('description', 'history')
        }),
        ('Media', {
            'fields': ('logo', 'logo_preview', 'cover_image')
        }),
        ('Aloqa ma\'lumotlari', {
            'fields': ('website', 'email', 'phone')
        }),
        ('Manzil', {
            'fields': ('region', 'city', 'address')
        }),
        ('Statistika', {
            'fields': ('established_year', 'student_count', 'faculty_count',
                       'rating', 'reviews_count')
        }),
        ('Sozlamalar', {
            'fields': ('is_partner', 'is_featured', 'is_active',
                       'created_at', 'updated_at')
        }),
    )

    def logo_preview(self, obj):
        if obj.logo:
            return format_html('<img src="{}" width="100" height="100" />', obj.logo.url)
        return 'Logo yuklanmagan'

    logo_preview.short_description = 'Logo ko\'rinishi'


class DirectionInline(admin.TabularInline):
    model = Direction
    extra = 0
    fields = ['name', 'code', 'education_form', 'education_type', 'is_active']
    show_change_link = True


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ['name', 'university', 'is_active']
    list_filter = ['university', 'is_active']
    search_fields = ['name', 'university__name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [DirectionInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('university', 'name', 'slug')
        }),
        ('Tavsif', {
            'fields': ('description',)
        }),
        ('Sozlamalar', {
            'fields': ('is_active',)
        }),
    )


class PassingScoreInline(admin.TabularInline):
    model = PassingScore
    extra = 1
    fields = ['year', 'grant_score', 'contract_score',
              'total_applications', 'competition_ratio']


@admin.register(Direction)
class DirectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'university', 'faculty', 'education_form',
                    'education_type', 'grant_quota', 'contract_quota', 'is_active']
    list_filter = ['university', 'education_form', 'education_type', 'is_active']
    search_fields = ['name', 'code', 'university__name']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'total_quota']
    filter_horizontal = ['required_subjects']
    inlines = [PassingScoreInline]

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('uuid', 'university', 'faculty', 'code', 'name', 'slug')
        }),
        ('Tavsif', {
            'fields': ('description',)
        }),
        ('Ta\'lim tafsilotlari', {
            'fields': ('education_form', 'education_type', 'duration_years',
                       'required_subjects')
        }),
        ('Kvota', {
            'fields': ('grant_quota', 'contract_quota', 'total_quota')
        }),
        ('Narx', {
            'fields': ('contract_price',)
        }),
        ('Sozlamalar', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )

    def total_quota(self, obj):
        return obj.total_quota

    total_quota.short_description = 'Jami kvota'


@admin.register(PassingScore)
class PassingScoreAdmin(admin.ModelAdmin):
    list_display = ['direction', 'year', 'grant_score', 'contract_score',
                    'competition_ratio', 'total_applications']
    list_filter = ['year', 'direction__university']
    search_fields = ['direction__name', 'direction__university__name']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('direction', 'year')
        }),
        ('Ballar', {
            'fields': ('grant_score', 'contract_score')
        }),
        ('Statistika', {
            'fields': ('total_applications', 'grant_accepted', 'contract_accepted',
                       'competition_ratio')
        }),
    )


@admin.register(UniversityReview)
class UniversityReviewAdmin(admin.ModelAdmin):
    list_display = ['university', 'user', 'rating', 'title',
                    'is_approved', 'created_at']
    list_filter = ['is_approved', 'rating', 'university', 'created_at']
    search_fields = ['title', 'content', 'university__name', 'user__username']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Asosiy ma\'lumotlar', {
            'fields': ('university', 'user', 'rating')
        }),
        ('Sharh', {
            'fields': ('title', 'content')
        }),
        ('Batafsil baholar', {
            'fields': ('education_rating', 'facility_rating', 'staff_rating')
        }),
        ('Sozlamalar', {
            'fields': ('is_approved', 'created_at')
        }),
    )

    actions = ['approve_reviews', 'disapprove_reviews']

    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
        self.message_user(request, f"{queryset.count()} ta sharh tasdiqlandi")

    approve_reviews.short_description = "Tanlangan sharhlarni tasdiqlash"

    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
        self.message_user(request, f"{queryset.count()} ta sharh rad etildi")

    disapprove_reviews.short_description = "Tanlangan sharhlarni rad etish"


@admin.register(AdmissionCalculation)
class AdmissionCalculationAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['created_at', 'formatted_subject_scores',
                       'formatted_recommendations']
    filter_horizontal = ['top_directions']

    fieldsets = (
        ('Foydalanuvchi', {
            'fields': ('user', 'created_at')
        }),
        ('Ballar', {
            'fields': ('total_score', 'formatted_subject_scores')
        }),
        ('AI Natijalari', {
            'fields': ('analysis', 'formatted_recommendations')
        }),
        ('Top yo\'nalishlar', {
            'fields': ('top_directions',)
        }),
    )

    def formatted_subject_scores(self, obj):
        if obj.subject_scores:
            scores_html = '<ul>'
            for subject, score in obj.subject_scores.items():
                scores_html += f'<li><strong>{subject}:</strong> {score}</li>'
            scores_html += '</ul>'
            return format_html(scores_html)
        return 'Ma\'lumot yo\'q'

    formatted_subject_scores.short_description = 'Fan ballari'

    def formatted_recommendations(self, obj):
        if obj.recommendations:
            rec_html = '<ol>'
            for rec in obj.recommendations:
                rec_html += f'<li>{rec}</li>'
            rec_html += '</ol>'
            return format_html(rec_html)
        return 'Tavsiyalar yo\'q'

    formatted_recommendations.short_description = 'Tavsiyalar'
