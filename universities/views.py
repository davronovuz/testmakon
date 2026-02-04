"""
TestMakon.uz - Universities Views
Complete views for all university templates

MODEL FIELDS (University):
- address, city, cover_image, created_at, description, directions,
- directions_count, email, established_year, faculties, faculty_count,
- history, id, is_active, is_featured, is_partner, logo, name, phone,
- rating, region, reviews, reviews_count, short_name, slug, student_count,
- studyplan, target_users, university_type, updated_at, uuid, website
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg, Count, Min, Max, Sum
from django.core.paginator import Paginator
from django.views.decorators.http import require_GET, require_POST

from .models import University, Faculty, Direction, PassingScore, UniversityReview


# ============================================================
# UNIVERSITY LIST
# ============================================================

def universities_list(request):
    """
    Universitetlar ro'yxati - Akam.uz uslubida
    Template: universities/universities_list.html
    """
    universities = University.objects.filter(is_active=True).order_by(
        '-is_featured', '-is_partner', 'name'
    )

    # Filters
    university_type = request.GET.get('type')
    region = request.GET.get('region')
    search = request.GET.get('q')

    if university_type and university_type != 'all':
        universities = universities.filter(university_type=university_type)

    if region and region != 'all':
        universities = universities.filter(region__icontains=region)

    if search:
        universities = universities.filter(
            Q(name__icontains=search) |
            Q(short_name__icontains=search)
        )

    # Statistics
    total_count = universities.count()
    state_count = universities.filter(university_type='state').count()
    private_count = universities.filter(university_type='private').count()

    # Pagination
    paginator = Paginator(universities, 12)
    page = request.GET.get('page', 1)
    universities = paginator.get_page(page)

    # Regions for filter
    regions = University.objects.filter(is_active=True).values_list(
        'region', flat=True
    ).distinct().order_by('region')

    context = {
        'universities': universities,
        'regions': [r for r in regions if r],
        'total_count': total_count,
        'state_count': state_count,
        'private_count': private_count,
        'current_type': university_type,
        'current_region': region,
        'search': search,
    }

    return render(request, 'universities/universities_list.html', context)


# ============================================================
# UNIVERSITY DETAIL
# ============================================================

def university_detail(request, slug):
    """
    Universitet tafsilotlari
    Template: universities/university_detail.html
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    # Faculties
    faculties = university.faculties.filter(is_active=True)

    # Directions (top 10)
    directions = university.directions.filter(is_active=True).select_related(
        'faculty'
    ).order_by('name')[:10]

    # Reviews
    reviews = university.reviews.filter(is_approved=True).select_related(
        'user'
    ).order_by('-created_at')[:10]

    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    # Related universities (same region)
    related = University.objects.filter(
        is_active=True,
        region=university.region
    ).exclude(id=university.id)[:4]

    context = {
        'university': university,
        'faculties': faculties,
        'directions': directions,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else university.rating or 0,
        'reviews_count': university.reviews_count or reviews.count(),
        'related_universities': related,
    }

    return render(request, 'universities/university_detail.html', context)


# ============================================================
# UNIVERSITY DIRECTIONS
# ============================================================

def university_directions(request, slug):
    """
    Universitet yo'nalishlari ro'yxati
    Template: universities/university_directions.html
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    directions = university.directions.filter(is_active=True).select_related(
        'faculty'
    ).order_by('name')

    # Filters
    faculty_id = request.GET.get('faculty')
    degree = request.GET.get('degree')  # bachelor, master, phd
    study_form = request.GET.get('form')  # daytime, evening, distance
    search = request.GET.get('q')

    if faculty_id:
        directions = directions.filter(faculty_id=faculty_id)

    if degree:
        directions = directions.filter(degree=degree)

    if study_form:
        directions = directions.filter(study_form=study_form)

    if search:
        directions = directions.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    # Statistics (safe aggregation)
    total_count = directions.count()

    # Pagination
    paginator = Paginator(directions, 20)
    page = request.GET.get('page', 1)
    directions = paginator.get_page(page)

    context = {
        'university': university,
        'directions': directions,
        'faculties': university.faculties.filter(is_active=True),
        'total_directions': total_count,
        'current_faculty': faculty_id,
        'current_degree': degree,
        'current_form': study_form,
    }

    return render(request, 'universities/university_directions.html', context)


# ============================================================
# DIRECTION DETAIL
# ============================================================

def direction_detail(request, uuid):
    """
    Yo'nalish tafsilotlari
    Template: universities/direction_detail.html
    """
    direction = get_object_or_404(
        Direction.objects.select_related('university', 'faculty'),
        uuid=uuid,
        is_active=True
    )

    # Passing scores history
    passing_scores = PassingScore.objects.filter(
        direction=direction
    ).order_by('-year')[:5]

    # Similar directions (same field, different universities)
    similar = Direction.objects.filter(
        is_active=True,
        code=direction.code
    ).exclude(id=direction.id).select_related('university')[:5]

    context = {
        'direction': direction,
        'university': direction.university,
        'passing_scores': passing_scores,
        'similar_directions': similar,
    }

    return render(request, 'universities/direction_detail.html', context)


# ============================================================
# UNIVERSITY COMPARE
# ============================================================

def university_compare(request):
    """
    Universitetlarni solishtirish
    Template: universities/university_compare.html
    """
    uni1_slug = request.GET.get('uni1')
    uni2_slug = request.GET.get('uni2')

    uni1 = None
    uni2 = None

    if uni1_slug:
        uni1 = University.objects.filter(slug=uni1_slug, is_active=True).first()

    if uni2_slug:
        uni2 = University.objects.filter(slug=uni2_slug, is_active=True).first()

    # All universities for selection modal
    universities = University.objects.filter(is_active=True).order_by('name')

    context = {
        'uni1': uni1,
        'uni2': uni2,
        'universities': universities,
    }

    return render(request, 'universities/university_compare.html', context)


# ============================================================
# UNIVERSITY ADMISSION (Calculator)
# ============================================================

def university_admission(request, slug):
    """
    Qabul kalkulyatori
    Template: universities/university_admission.html
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    # All directions for calculator
    directions = university.directions.filter(is_active=True).order_by('name')

    # Popular directions (first 5)
    popular_directions = directions[:5]

    context = {
        'university': university,
        'directions': directions,
        'popular_directions': popular_directions,
    }

    return render(request, 'universities/university_admission.html', context)


# ============================================================
# ADD REVIEW
# ============================================================

@login_required
def add_review(request, slug):
    """
    Sharh qo'shish
    Template: universities/add_review.html
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    # Check if user already reviewed
    existing = UniversityReview.objects.filter(
        university=university,
        user=request.user
    ).first()

    if existing:
        messages.warning(request, "Siz allaqachon ushbu universitetga sharh yozgansiz")
        return redirect('universities:detail', slug=slug)

    if request.method == 'POST':
        rating = int(request.POST.get('rating', 3))
        title = request.POST.get('title', '').strip()
        content = request.POST.get('content', '').strip()

        if not content:
            messages.error(request, "Sharh matnini kiriting")
            return redirect('universities:add_review', slug=slug)

        if len(content) < 20:
            messages.error(request, "Sharh kamida 20 ta belgidan iborat bo'lishi kerak")
            return redirect('universities:add_review', slug=slug)

        UniversityReview.objects.create(
            university=university,
            user=request.user,
            rating=rating,
            title=title,
            content=content,
            is_approved=False,  # Needs moderation
        )

        messages.success(request, "Sharhingiz qabul qilindi. Moderatsiyadan keyin ko'rinadi.")
        return redirect('universities:detail', slug=slug)

    context = {
        'university': university,
    }

    return render(request, 'universities/add_review.html', context)


# ============================================================
# HELPER VIEWS
# ============================================================

def faculties_list(request, slug):
    """
    Universitet fakultetlari
    Template: universities/faculties_list.html
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    faculties = university.faculties.filter(is_active=True).order_by('name')

    context = {
        'university': university,
        'faculties': faculties,
    }

    return render(request, 'universities/faculties_list.html', context)


def all_directions(request):
    """
    Barcha yo'nalishlar (barcha universitetlar bo'yicha)
    Template: universities/all_directions.html
    """
    directions = Direction.objects.filter(is_active=True).select_related(
        'university', 'faculty'
    ).order_by('name')

    # Filters
    university_id = request.GET.get('university')
    degree = request.GET.get('degree')
    search = request.GET.get('q')

    if university_id:
        directions = directions.filter(university_id=university_id)

    if degree:
        directions = directions.filter(degree=degree)

    if search:
        directions = directions.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )

    # Pagination
    paginator = Paginator(directions, 30)
    page = request.GET.get('page', 1)
    directions = paginator.get_page(page)

    # Universities for filter
    universities = University.objects.filter(is_active=True).order_by('name')

    context = {
        'directions': directions,
        'universities': universities,
        'current_university': university_id,
        'current_degree': degree,
        'search': search,
    }

    return render(request, 'universities/all_directions.html', context)


# ============================================================
# API ENDPOINTS
# ============================================================

@require_GET
def api_search(request):
    """
    Universal qidiruv API
    GET /universities/api/search/?q=query
    """
    query = request.GET.get('q', '').strip()

    if len(query) < 2:
        return JsonResponse({'results': [], 'universities': [], 'directions': []})

    # Search universities
    universities = University.objects.filter(
        Q(name__icontains=query) | Q(short_name__icontains=query),
        is_active=True
    )[:10]

    # Search directions
    directions = Direction.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query),
        is_active=True
    ).select_related('university')[:10]

    return JsonResponse({
        'universities': [
            {
                'id': u.id,
                'name': u.name,
                'short_name': u.short_name,
                'slug': u.slug,
                'logo': u.logo.url if u.logo else None,
                'region': u.region,
                'type': u.university_type,
            }
            for u in universities
        ],
        'directions': [
            {
                'id': str(d.uuid),
                'name': d.name,
                'code': getattr(d, 'code', ''),
                'university': d.university.short_name or d.university.name,
                'university_slug': d.university.slug,
            }
            for d in directions
        ]
    })


@require_GET
def api_universities(request):
    """
    Universitetlar ro'yxati API (solishtirish uchun)
    GET /universities/api/list/
    """
    universities = University.objects.filter(is_active=True).order_by('name')

    return JsonResponse({
        'universities': [
            {
                'id': u.id,
                'name': u.name,
                'slug': u.slug,
                'logo': u.logo.url if u.logo else None,
                'region': u.region,
                'type': u.university_type,
            }
            for u in universities
        ]
    })


@require_GET
def api_directions(request, slug):
    """
    Universitet yo'nalishlari API (kalkulyator uchun)
    GET /universities/api/<slug>/directions/
    """
    university = get_object_or_404(University, slug=slug, is_active=True)

    directions = university.directions.filter(is_active=True).order_by('name')

    return JsonResponse({
        'directions': [
            {
                'id': d.id,
                'uuid': str(d.uuid),
                'name': d.name,
                'code': getattr(d, 'code', ''),
                'grant_score': getattr(d, 'grant_score', 180) or 180,
                'contract_score': getattr(d, 'contract_score', 140) or 140,
            }
            for d in directions
        ]
    })


@require_GET
def api_passing_scores(request, direction_id):
    """
    Yo'nalish o'tish ballari tarixi
    GET /universities/api/direction/<id>/scores/
    """
    scores = PassingScore.objects.filter(
        direction_id=direction_id
    ).order_by('-year').values(
        'year', 'grant_score', 'contract_score'
    )[:5]

    return JsonResponse({'scores': list(scores)})


@require_GET
def api_compare(request):
    """
    Universitetlarni solishtirish API
    GET /universities/api/compare/?uni1=slug1&uni2=slug2
    """
    uni1_slug = request.GET.get('uni1')
    uni2_slug = request.GET.get('uni2')

    if not uni1_slug or not uni2_slug:
        return JsonResponse({'error': 'Both universities required'}, status=400)

    uni1 = University.objects.filter(slug=uni1_slug, is_active=True).first()
    uni2 = University.objects.filter(slug=uni2_slug, is_active=True).first()

    if not uni1 or not uni2:
        return JsonResponse({'error': 'University not found'}, status=404)

    def uni_to_dict(u):
        return {
            'id': u.id,
            'name': u.name,
            'slug': u.slug,
            'type': u.university_type,
            'region': u.region,
            'directions_count': u.directions_count or 0,
            'student_count': u.student_count or 0,
            'faculty_count': u.faculty_count or 0,
            'rating': u.rating or 0,
            'established_year': u.established_year,
        }

    return JsonResponse({
        'uni1': uni_to_dict(uni1),
        'uni2': uni_to_dict(uni2),
    })


@require_POST
@login_required
def api_calculate_admission(request):
    """
    Qabul kalkulyatori API
    POST /universities/api/calculate/
    """
    import json

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    direction_id = data.get('direction_id')
    subject1 = float(data.get('subject1', 0))
    subject2 = float(data.get('subject2', 0))
    subject3 = float(data.get('subject3', 0))
    attestat = float(data.get('attestat', 4.0))
    additional = int(data.get('additional', 0))

    # Validate
    if not direction_id:
        return JsonResponse({'error': 'Direction required'}, status=400)

    # Get direction
    direction = Direction.objects.filter(id=direction_id, is_active=True).first()
    if not direction:
        return JsonResponse({'error': 'Direction not found'}, status=404)

    # Calculate score (DTM formula)
    # Test score: each subject max 30.1, coefficient 3.4
    test_score = (subject1 + subject2 + subject3) * 3.4

    # Attestat score: max 5, coefficient 3.7 = max 18.5
    attestat_score = attestat * 3.7

    # Total
    total_score = round(test_score + attestat_score + additional, 1)

    # Required scores
    grant_required = getattr(direction, 'grant_score', 180) or 180
    contract_required = getattr(direction, 'contract_score', 140) or 140

    # Determine result
    if total_score >= grant_required:
        status = 'grant'
        message = "Tabriklaymiz! Grantga o'tishingiz mumkin."
    elif total_score >= contract_required:
        status = 'contract'
        message = f"Kontraktga o'tishingiz mumkin. Grantga {grant_required - total_score:.1f} ball yetmayapti."
    else:
        status = 'fail'
        message = f"Kontraktga ham {contract_required - total_score:.1f} ball yetmayapti. Ko'proq tayyorlaning!"

    return JsonResponse({
        'total_score': total_score,
        'test_score': round(test_score, 1),
        'attestat_score': round(attestat_score, 1),
        'additional_score': additional,
        'grant_required': grant_required,
        'contract_required': contract_required,
        'status': status,
        'message': message,
        'direction': {
            'name': direction.name,
            'university': direction.university.name,
        }
    })