"""
TestMakon.uz — Coding Views
"""

import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.core.cache import cache
from django.utils import timezone

from .models import (
    ProgrammingLanguage, CodingCategory, CodingProblem,
    CodeSubmission, UserCodingStats,
)
from .tasks import execute_code_submission

MAX_CODE_SIZE = 50 * 1024  # 50KB
SUBMIT_RATE_LIMIT = 10  # per minute
RUN_RATE_LIMIT = 20  # per minute


def _check_rate_limit(user_id, action, limit):
    """Rate limit tekshirish — Redis cache"""
    key = f"coding_rate_{action}_{user_id}"
    count = cache.get(key, 0)
    if count >= limit:
        return False
    cache.set(key, count + 1, 60)  # 1 daqiqa
    return True


def problems_list(request):
    """Masalalar ro'yxati — filtrlash bilan"""
    problems = CodingProblem.objects.filter(is_active=True).select_related('category')

    # Filtrlar
    difficulty = request.GET.get('difficulty')
    category_slug = request.GET.get('category')
    search = request.GET.get('q')
    status_filter = request.GET.get('status')

    if difficulty:
        problems = problems.filter(difficulty=difficulty)
    if category_slug:
        problems = problems.filter(category__slug=category_slug)
    if search:
        problems = problems.filter(Q(title__icontains=search) | Q(description__icontains=search))

    # Foydalanuvchi yechimlari
    solved_ids = set()
    attempted_ids = set()
    if request.user.is_authenticated:
        solved_ids = set(
            CodeSubmission.objects.filter(
                user=request.user, status='accepted', is_sample_run=False
            ).values_list('problem_id', flat=True)
        )
        attempted_ids = set(
            CodeSubmission.objects.filter(
                user=request.user, is_sample_run=False
            ).values_list('problem_id', flat=True)
        ) - solved_ids

        if status_filter == 'solved':
            problems = problems.filter(id__in=solved_ids)
        elif status_filter == 'attempted':
            problems = problems.filter(id__in=attempted_ids)
        elif status_filter == 'new':
            problems = problems.exclude(id__in=solved_ids | attempted_ids)

    # Pagination
    paginator = Paginator(problems, 30)
    page = paginator.get_page(request.GET.get('page'))

    categories = CodingCategory.objects.all()

    # Stats
    stats = None
    if request.user.is_authenticated:
        stats = UserCodingStats.objects.filter(user=request.user).first()

    context = {
        'page_obj': page,
        'categories': categories,
        'solved_ids': solved_ids,
        'attempted_ids': attempted_ids,
        'current_difficulty': difficulty,
        'current_category': category_slug,
        'current_search': search or '',
        'current_status': status_filter,
        'stats': stats,
        'total_problems': CodingProblem.objects.filter(is_active=True).count(),
    }
    return render(request, 'coding/problems_list.html', context)


@login_required
def problem_detail(request, slug):
    """Masala sahifasi — Monaco editor bilan"""
    problem = get_object_or_404(
        CodingProblem.objects.prefetch_related('languages', 'test_cases'),
        slug=slug, is_active=True
    )
    languages = problem.languages.filter(is_active=True)
    sample_cases = problem.test_cases.filter(is_sample=True)

    # Foydalanuvchi oxirgi kodi
    last_submission = CodeSubmission.objects.filter(
        user=request.user, problem=problem, is_sample_run=False
    ).first()

    # Bu masala yechildimi?
    is_solved = CodeSubmission.objects.filter(
        user=request.user, problem=problem, status='accepted', is_sample_run=False
    ).exists()

    context = {
        'problem': problem,
        'languages': languages,
        'sample_cases': sample_cases,
        'last_submission': last_submission,
        'is_solved': is_solved,
        'starter_code_json': json.dumps(problem.starter_code),
    }
    return render(request, 'coding/problem_detail.html', context)


@login_required
@require_POST
def api_submit_code(request):
    """Kod yuborish — AJAX"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Noto'g'ri ma'lumot"}, status=400)

    problem_id = data.get('problem_id')
    language_id = data.get('language_id')
    code = data.get('code', '')

    if not all([problem_id, language_id, code]):
        return JsonResponse({'error': "Barcha maydonlar to'ldirilishi shart"}, status=400)

    if len(code) > MAX_CODE_SIZE:
        return JsonResponse({'error': f"Kod hajmi {MAX_CODE_SIZE // 1024}KB dan oshmasligi kerak"}, status=400)

    if not _check_rate_limit(request.user.id, 'submit', SUBMIT_RATE_LIMIT):
        return JsonResponse({'error': "Juda ko'p so'rov. 1 daqiqa kuting"}, status=429)

    problem = get_object_or_404(CodingProblem, id=problem_id, is_active=True)
    language = get_object_or_404(ProgrammingLanguage, id=language_id, is_active=True)

    submission = CodeSubmission.objects.create(
        user=request.user,
        problem=problem,
        language=language,
        code=code,
        status='pending',
        is_sample_run=False,
    )

    # Celery task
    execute_code_submission.delay(submission.id)

    return JsonResponse({
        'submission_id': submission.id,
        'status': 'pending',
    })


@login_required
@require_POST
def api_run_sample(request):
    """Namuna testlarni ishlatish — AJAX"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': "Noto'g'ri ma'lumot"}, status=400)

    problem_id = data.get('problem_id')
    language_id = data.get('language_id')
    code = data.get('code', '')

    if not all([problem_id, language_id, code]):
        return JsonResponse({'error': "Barcha maydonlar to'ldirilishi shart"}, status=400)

    if len(code) > MAX_CODE_SIZE:
        return JsonResponse({'error': f"Kod hajmi {MAX_CODE_SIZE // 1024}KB dan oshmasligi kerak"}, status=400)

    if not _check_rate_limit(request.user.id, 'run', RUN_RATE_LIMIT):
        return JsonResponse({'error': "Juda ko'p so'rov. 1 daqiqa kuting"}, status=429)

    problem = get_object_or_404(CodingProblem, id=problem_id, is_active=True)
    language = get_object_or_404(ProgrammingLanguage, id=language_id, is_active=True)

    submission = CodeSubmission.objects.create(
        user=request.user,
        problem=problem,
        language=language,
        code=code,
        status='pending',
        is_sample_run=True,
    )

    # Celery task
    execute_code_submission.delay(submission.id)

    return JsonResponse({
        'submission_id': submission.id,
        'status': 'pending',
    })


@login_required
def api_submission_status(request, pk):
    """Submission holatini tekshirish — AJAX polling"""
    try:
        submission = CodeSubmission.objects.get(id=pk, user=request.user)
    except CodeSubmission.DoesNotExist:
        return JsonResponse({'error': 'Topilmadi'}, status=404)

    data = {
        'id': submission.id,
        'status': submission.status,
        'status_display': submission.get_status_display(),
        'passed_count': submission.passed_count,
        'total_count': submission.total_count,
        'execution_time': submission.execution_time,
        'error_message': submission.error_message,
        'results': submission.results if submission.status not in ('pending', 'running') else [],
    }
    return JsonResponse(data)


@login_required
def my_submissions(request):
    """Foydalanuvchi yuborishlari tarixi"""
    submissions = CodeSubmission.objects.filter(
        user=request.user, is_sample_run=False
    ).select_related('problem', 'language')

    # Filtrlar
    problem_slug = request.GET.get('problem')
    status = request.GET.get('status')
    if problem_slug:
        submissions = submissions.filter(problem__slug=problem_slug)
    if status:
        submissions = submissions.filter(status=status)

    paginator = Paginator(submissions, 25)
    page = paginator.get_page(request.GET.get('page'))

    context = {
        'page_obj': page,
        'current_status': status,
    }
    return render(request, 'coding/my_submissions.html', context)


@login_required
def submission_detail(request, pk):
    """Yuborish tafsilotlari"""
    submission = get_object_or_404(
        CodeSubmission.objects.select_related('problem', 'language'),
        id=pk, user=request.user
    )
    context = {
        'submission': submission,
    }
    return render(request, 'coding/submission_detail.html', context)


def coding_leaderboard(request):
    """Dasturlash reytingi"""
    stats = UserCodingStats.objects.select_related('user').filter(
        problems_solved__gt=0
    ).order_by('-problems_solved', '-hard_solved', '-medium_solved')[:100]

    # User rank
    user_rank = None
    user_stats = None
    if request.user.is_authenticated:
        user_stats = UserCodingStats.objects.filter(user=request.user).first()
        if user_stats and user_stats.problems_solved > 0:
            user_rank = UserCodingStats.objects.filter(
                problems_solved__gt=user_stats.problems_solved
            ).count() + 1

    context = {
        'stats_list': stats,
        'user_rank': user_rank,
        'user_stats': user_stats,
    }
    return render(request, 'coding/leaderboard.html', context)
