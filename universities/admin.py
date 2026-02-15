"""
TestMakon.uz - Universities Admin Configuration
"""
import csv
import io
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from django.contrib import messages
from django.utils.text import slugify
from django.utils.html import format_html
from .models import (
    University, Faculty, Direction,
    PassingScore, UniversityReview, AdmissionCalculation
)


class FacultyInline(admin.TabularInline):
    model = Faculty
    extra = 0
    fields = ['name', 'slug', 'is_active']
    show_change_link = True
    prepopulated_fields = {'slug': ('name',)}


@admin.register(University)
class UniversityAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'university_type', 'region',
                    'directions_count', 'student_count', 'is_partner', 'is_featured', 'is_active']
    list_filter = ['university_type', 'region', 'is_partner', 'is_featured', 'is_active']
    search_fields = ['name', 'short_name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['uuid', 'created_at', 'updated_at', 'logo_preview']
    inlines = [FacultyInline]

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

    def directions_count(self, obj):
        count = obj.directions.count()
        return format_html(
            '<span style="background:#3B82F6;color:white;padding:2px 8px;border-radius:10px;font-size:12px;">{}</span>',
            count
        )

    directions_count.short_description = "Yo'nalishlar"

    def get_urls(self):
        custom_urls = [
            path(
                'import-data/',
                self.admin_site.admin_view(self.import_data_view),
                name='university-import-data',
            ),
        ]
        return custom_urls + super().get_urls()

    def import_data_view(self, request):
        if request.method == 'POST':
            import_type = request.POST.get('import_type')
            file = request.FILES.get('file')

            if not file:
                messages.error(request, 'Fayl tanlanmadi!')
                return redirect('admin:university-import-data')

            try:
                if file.name.endswith('.xlsx'):
                    import openpyxl
                    wb = openpyxl.load_workbook(file)
                    ws = wb.active
                    rows = []
                    for row in ws.iter_rows(min_row=2, values_only=True):
                        rows.append([str(cell) if cell is not None else '' for cell in row])
                elif file.name.endswith('.csv'):
                    content = file.read().decode('utf-8-sig')
                    reader = csv.reader(io.StringIO(content))
                    next(reader, None)  # skip header
                    rows = list(reader)
                else:
                    messages.error(request, 'Faqat .csv yoki .xlsx fayllar qabul qilinadi!')
                    return redirect('admin:university-import-data')

                if import_type == 'scores':
                    count = self._import_scores(rows)
                    messages.success(request, f'{count} ta o\'tish bali import qilindi!')
                elif import_type == 'universities':
                    count = self._import_universities(rows)
                    messages.success(request, f'{count} ta universitet import qilindi!')

            except Exception as e:
                messages.error(request, f'Xatolik: {str(e)}')

            return redirect('admin:university-import-data')

        context = {
            **self.admin_site.each_context(request),
            'title': 'Ma\'lumotlarni import qilish',
            'uni_count': University.objects.count(),
            'dir_count': Direction.objects.count(),
            'score_count': PassingScore.objects.count(),
        }
        return render(request, 'admin/universities/import_data.html', context)

    def _import_scores(self, rows):
        """Import o'tish ballari: Universitet | Kod | Yo'nalish | Yil | Grant | Kontrakt | Arizalar | Tanlov"""
        count = 0
        for row in rows:
            if len(row) < 6:
                continue
            uni_name = row[0].strip()
            code = row[1].strip()
            year = int(float(row[3])) if row[3] else 2024
            grant_score = float(row[4]) if row[4] else None
            contract_score = float(row[5]) if row[5] else None
            applications = int(float(row[6])) if len(row) > 6 and row[6] else None
            ratio = float(row[7]) if len(row) > 7 and row[7] else None

            # Find direction by code or by university+name
            direction = None
            if code:
                direction = Direction.objects.filter(code=code).first()
            if not direction:
                direction = Direction.objects.filter(
                    university__name__icontains=uni_name
                ).first()

            if direction:
                PassingScore.objects.update_or_create(
                    direction=direction,
                    year=year,
                    defaults={
                        'grant_score': grant_score,
                        'contract_score': contract_score,
                        'total_applications': applications,
                        'competition_ratio': ratio,
                    }
                )
                count += 1
        return count

    def _import_universities(self, rows):
        """Import universitetlar: Nomi | Qisqa_nomi | Turi | Viloyat | Shahar | Tashkil_yili | Veb_sayt"""
        count = 0
        for row in rows:
            if len(row) < 4:
                continue
            name = row[0].strip()
            short_name = row[1].strip() if len(row) > 1 else ''
            uni_type = row[2].strip() if len(row) > 2 else 'state'
            region = row[3].strip() if len(row) > 3 else ''
            city = row[4].strip() if len(row) > 4 else region
            est_year = int(float(row[5])) if len(row) > 5 and row[5] else None
            website = row[6].strip() if len(row) > 6 else ''

            slug = slugify(name)

            University.objects.update_or_create(
                slug=slug,
                defaults={
                    'name': name,
                    'short_name': short_name,
                    'university_type': uni_type if uni_type in ('state', 'private', 'foreign', 'joint') else 'state',
                    'region': region,
                    'city': city,
                    'established_year': est_year,
                    'website': website,
                    'is_active': True,
                }
            )
            count += 1
        return count

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_url'] = 'import-data/'
        return super().changelist_view(request, extra_context=extra_context)


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
