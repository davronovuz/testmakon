"""
TestMakon.uz - Universities Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Avg

from .models import University, Faculty, Direction, PassingScore, UniversityReview


def universities_list(request):
    """Universitetlar ro'yxati"""
    universities = University.objects.filter(is_active=True)

    # Filters
    university_type = request.GET.get('type')
    region = request.GET.get('region')
    search = request.GET.get('q')

    if university_type:
        universities = universities.filter(university_type=university_type)

    if region:
        universities = universities.filter(region=region)

    if search:
        universities = universities.filter(
            Q(name__icontains=search) | Q(short_name__icontains=search)
        )

    featured = universities.filter(is_featured=True)[:5]
    regions = University.objects.values_list('region', flat=True).distinct()

    context = {
        'universities': universities,
        'featured': featured,
        'regions': list(regions),
        'current_type': university_type,
        'current_region': region,
        'search': search,
    }

    return render(request, 'universities/universities_list.html', context)


def university_detail(request, slug):
    """Universitet tafsilotlari"""
    university = get_object_or_404(University, slug=slug, is_active=True)

    faculties = university.faculties.filter(is_active=True)
    directions = university.directions.filter(is_active=True)[:10]
    reviews = university.reviews.filter(is_approved=True).order_by('-created_at')[:5]
    avg_rating = reviews.aggregate(Avg('rating'))['rating__avg']

    context = {
        'university': university,
        'faculties': faculties,
        'directions': directions,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
    }

    return render(request, 'universities/university_detail.html', context)


def university_directions(request, slug):
    """Universitet yo'nalishlari"""
    university = get_object_or_404(University, slug=slug, is_active=True)

    directions = university.directions.filter(is_active=True).select_related('faculty')

    faculty_id = request.GET.get('faculty')
    education_form = request.GET.get('form')

    if faculty_id:
        directions = directions.filter(faculty_id=faculty_id)

    if education_form:
        directions = directions.filter(education_form=education_form)

    context = {
        'university': university,
        'directions': directions,
        'faculties': university.faculties.filter(is_active=True),
    }

    return render(request, 'universities/university_directions.html', context)


def direction_detail(request, uuid):
    """Yo'nalish tafsilotlari"""
    direction = get_object_or_404(Direction, uuid=uuid, is_active=True)
    passing_scores = direction.passing_scores.all().order_by('-year')[:5]

    context = {
        'direction': direction,
        'passing_scores': passing_scores,
    }

    return render(request, 'universities/direction_detail.html', context)


@login_required
def add_review(request, slug):
    """Sharh qo'shish"""
    university = get_object_or_404(University, slug=slug)

    if request.method == 'POST':
        existing = UniversityReview.objects.filter(
            university=university,
            user=request.user
        ).first()

        if existing:
            messages.error(request, "Siz allaqachon sharh yozgansiz")
            return redirect('universities:university_detail', slug=slug)

        UniversityReview.objects.create(
            university=university,
            user=request.user,
            rating=int(request.POST.get('rating', 3)),
            title=request.POST.get('title', ''),
            content=request.POST.get('content', ''),
            education_rating=int(request.POST.get('education_rating', 3)),
            facility_rating=int(request.POST.get('facility_rating', 3)),
            staff_rating=int(request.POST.get('staff_rating', 3)),
        )

        messages.success(request, "Sharhingiz moderatsiyadan keyin ko'rinadi")
        return redirect('universities:university_detail', slug=slug)

    context = {'university': university}
    return render(request, 'universities/add_review.html', context)


def api_search(request):
    """Qidiruv API"""
    query = request.GET.get('q', '')

    if len(query) < 2:
        return JsonResponse({'results': []})

    universities = University.objects.filter(
        Q(name__icontains=query) | Q(short_name__icontains=query),
        is_active=True
    )[:10]

    directions = Direction.objects.filter(
        Q(name__icontains=query) | Q(code__icontains=query),
        is_active=True
    ).select_related('university')[:10]

    results = {
        'universities': [
            {'id': u.id, 'name': u.name, 'slug': u.slug}
            for u in universities
        ],
        'directions': [
            {'id': str(d.uuid), 'name': d.name, 'university': d.university.short_name}
            for d in directions
        ]
    }

    return JsonResponse(results)


def api_passing_scores(request, direction_id):
    """O'tish ballari API"""
    scores = PassingScore.objects.filter(
        direction_id=direction_id
    ).order_by('-year').values(
        'year', 'grant_score', 'contract_score', 'competition_ratio'
    )[:5]

    return JsonResponse({'scores': list(scores)})