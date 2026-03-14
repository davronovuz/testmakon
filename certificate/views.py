"""
TestMakon.uz — Milliy Sertifikat Views
"""
import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Prefetch

from .models import (
    CertSubject, CertMock, CertQuestion, CertMockAttempt,
    CertAttemptAnswer, CertChoice, CertGroupedOption,
    CertGroupedItem, CertShortOpen, CertMultiPart,
    CertSavedQuestion,
)


def _update_user_stats(attempt):
    """Urinish tugagach user statistikasini yangilash"""
    try:
        from tests_app.models import DailyUserStats
        user = attempt.user
        today = timezone.now().date()

        # User umumiy statistikasi
        user.total_tests_taken = getattr(user, 'total_tests_taken', 0) + 1
        user.total_correct_answers = getattr(user, 'total_correct_answers', 0) + attempt.correct_answers
        user.total_wrong_answers = getattr(user, 'total_wrong_answers', 0) + attempt.wrong_answers
        # XP: har to'g'ri javob uchun 2 XP
        xp_gained = attempt.correct_answers * 2
        if hasattr(user, 'add_xp'):
            user.add_xp(xp_gained)
        else:
            user.xp_points = getattr(user, 'xp_points', 0) + xp_gained
        user.save(update_fields=[
            'total_tests_taken', 'total_correct_answers',
            'total_wrong_answers', 'xp_points'
        ])

        # Kunlik statistika
        daily, _ = DailyUserStats.objects.get_or_create(user=user, date=today)
        daily.tests_taken += 1
        daily.questions_answered += attempt.total_questions
        daily.correct_answers += attempt.correct_answers
        daily.wrong_answers += attempt.wrong_answers
        daily.total_time_spent += attempt.time_spent
        daily.xp_earned += xp_gained
        total_q = (daily.correct_answers + daily.wrong_answers) or 1
        daily.accuracy_rate = round((daily.correct_answers / total_q) * 100, 1)

        # Fan statistikasi
        subject_name = attempt.mock.cert_subject.subject.slug
        subjects_data = daily.subjects_practiced or {}
        if subject_name not in subjects_data:
            subjects_data[subject_name] = {'correct': 0, 'total': 0}
        subjects_data[subject_name]['correct'] += attempt.correct_answers
        subjects_data[subject_name]['total'] += attempt.total_questions
        daily.subjects_practiced = subjects_data
        daily.save()
    except Exception:
        pass  # Statistika xatosi asosiy oqimni to'xtatmasin


# ─────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────

def _check_premium_access(user, mock):
    """Premium tekshiruv — False qaytarsa user kira olmaydi"""
    if mock.is_free:
        return True
    return user.is_authenticated and (
        user.is_premium and
        (user.premium_until is None or user.premium_until > timezone.now())
    )


def _get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


# ─────────────────────────────────────────────────────────────
# 1. SUBJECTS LIST
# ─────────────────────────────────────────────────────────────

def subjects_list(request):
    subjects = CertSubject.objects.filter(is_active=True).select_related(
        'subject'
    ).prefetch_related(
        Prefetch('mocks', queryset=CertMock.objects.filter(is_active=True))
    ).order_by('order', 'subject__name')

    context = {
        'subjects': subjects,
        'page_title': 'Milliy Sertifikat',
    }
    return render(request, 'certificate/subjects_list.html', context)


# ─────────────────────────────────────────────────────────────
# 2. SUBJECT MOCKS LIST
# ─────────────────────────────────────────────────────────────

def subject_mocks(request, subject_slug):
    cert_subject = get_object_or_404(
        CertSubject,
        subject__slug=subject_slug,
        is_active=True
    )

    mocks = CertMock.objects.filter(
        cert_subject=cert_subject,
        is_active=True
    ).order_by('order', '-year')

    # User uchun attempt statuslari
    user_attempts = {}
    if request.user.is_authenticated:
        attempts = CertMockAttempt.objects.filter(
            user=request.user,
            mock__in=mocks
        ).order_by('-started_at')
        for att in attempts:
            if att.mock_id not in user_attempts:
                user_attempts[att.mock_id] = att

    mocks_with_status = []
    for mock in mocks:
        attempt = user_attempts.get(mock.id)
        has_access = _check_premium_access(request.user, mock)
        mocks_with_status.append({
            'mock': mock,
            'attempt': attempt,
            'has_access': has_access,
        })

    context = {
        'cert_subject': cert_subject,
        'mocks_with_status': mocks_with_status,
        'page_title': f"{cert_subject.subject.name} — Mocklar",
    }
    return render(request, 'certificate/subject_mocks.html', context)


# ─────────────────────────────────────────────────────────────
# 3. MOCK DETAIL / INSTRUCTION
# ─────────────────────────────────────────────────────────────

def mock_detail(request, subject_slug, mock_slug):
    cert_subject = get_object_or_404(CertSubject, subject__slug=subject_slug, is_active=True)
    mock = get_object_or_404(CertMock, cert_subject=cert_subject, slug=mock_slug, is_active=True)

    has_access = _check_premium_access(request.user, mock)
    user_attempts = []
    best_attempt = None

    if request.user.is_authenticated:
        user_attempts = CertMockAttempt.objects.filter(
            user=request.user, mock=mock, status='completed'
        ).order_by('-percentage')
        best_attempt = user_attempts.first()

    context = {
        'cert_subject': cert_subject,
        'mock': mock,
        'has_access': has_access,
        'user_attempts': user_attempts[:5],
        'best_attempt': best_attempt,
        'page_title': mock.title,
    }
    return render(request, 'certificate/mock_detail.html', context)


# ─────────────────────────────────────────────────────────────
# 4. MOCK START
# ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def mock_start(request, subject_slug, mock_slug):
    cert_subject = get_object_or_404(CertSubject, subject__slug=subject_slug, is_active=True)
    mock = get_object_or_404(CertMock, cert_subject=cert_subject, slug=mock_slug, is_active=True)

    if not _check_premium_access(request.user, mock):
        return redirect('subscriptions:pricing')

    # Max attempts tekshirish
    if mock.max_attempts > 0:
        existing = CertMockAttempt.objects.filter(
            user=request.user, mock=mock, status='completed'
        ).count()
        if existing >= mock.max_attempts:
            return redirect('certificate:mock_detail', subject_slug=subject_slug, mock_slug=mock_slug)

    # In-progress attempt bor bo'lsa davom ettir
    in_progress = CertMockAttempt.objects.filter(
        user=request.user, mock=mock, status__in=['started', 'in_progress']
    ).first()

    if in_progress:
        return redirect('certificate:mock_solve', attempt_uuid=in_progress.uuid)

    attempt = CertMockAttempt.objects.create(
        user=request.user,
        mock=mock,
        total_questions=mock.questions_count,
        total_points=mock.total_points,
        ip_address=_get_client_ip(request),
    )

    return redirect('certificate:mock_solve', attempt_uuid=attempt.uuid)


# ─────────────────────────────────────────────────────────────
# 5. MOCK SOLVE PAGE
# ─────────────────────────────────────────────────────────────

@login_required
def mock_solve(request, attempt_uuid):
    attempt = get_object_or_404(
        CertMockAttempt,
        uuid=attempt_uuid,
        user=request.user
    )

    if attempt.status == 'completed':
        return redirect('certificate:mock_result', attempt_uuid=attempt.uuid)

    mock = attempt.mock
    questions = mock.questions.filter(is_active=True).prefetch_related(
        'choices',
        'grouped_options',
        'grouped_items__correct_option',
        'parts',
        'short_open',
    ).order_by('number')

    # Mavjud javoblar
    raw_answers = CertAttemptAnswer.objects.filter(attempt=attempt).select_related(
        'selected_choice', 'question'
    )

    # Template uchun: answered question id lar (skipped emas)
    answered_ids = set()
    # JS pre-fill uchun JSON data
    prefill_data = {}
    for a in raw_answers:
        if not a.is_skipped:
            answered_ids.add(a.question_id)
        prefill_data[a.question_id] = {
            'choice_id': a.selected_choice_id,
            'text_answer': a.text_answer or '',
            'structured_answer': a.structured_answer or {},
        }

    # Vaqt qoldi (soniya)
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    time_limit_seconds = mock.time_limit * 60
    time_remaining = max(0, int(time_limit_seconds - elapsed))

    if time_remaining == 0 and attempt.status != 'completed':
        attempt.status = 'timeout'
        attempt.calculate_results()
        return redirect('certificate:mock_result', attempt_uuid=attempt.uuid)

    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(CertSavedQuestion.objects.filter(
            user=request.user,
            question__mock=mock
        ).values_list('question_id', flat=True))

    context = {
        'attempt': attempt,
        'mock': mock,
        'questions': questions,
        'answered_ids': answered_ids,
        'saved_ids': saved_ids,
        'prefill_json': json.dumps(prefill_data),
        'time_remaining': time_remaining,
        'total_questions': questions.count(),
        'page_title': f"{mock.title} — Ishlash",
    }
    return render(request, 'certificate/mock_solve.html', context)


# ─────────────────────────────────────────────────────────────
# 6. SUBMIT ANSWER (AJAX)
# ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def submit_answer(request, attempt_uuid):
    attempt = get_object_or_404(CertMockAttempt, uuid=attempt_uuid, user=request.user)

    if attempt.status == 'completed':
        return JsonResponse({'error': 'Test yakunlangan'}, status=400)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Noto\'g\'ri JSON'}, status=400)

    question_id = data.get('question_id')
    question = get_object_or_404(CertQuestion, id=question_id, mock=attempt.mock)

    answer, _ = CertAttemptAnswer.objects.get_or_create(
        attempt=attempt,
        question=question,
        defaults={'is_skipped': True}
    )

    qtype = question.question_type

    if data.get('skipped'):
        answer.is_skipped = True
        answer.selected_choice = None
        answer.text_answer = ''
        answer.structured_answer = None
    elif qtype == 'choice':
        choice_id = data.get('choice_id')
        try:
            choice = question.choices.get(id=choice_id)
            answer.selected_choice = choice
            answer.is_skipped = False
        except CertChoice.DoesNotExist:
            return JsonResponse({'error': 'Variant topilmadi'}, status=400)
    elif qtype == 'short_open':
        answer.text_answer = str(data.get('text_answer', '')).strip()
        answer.is_skipped = not bool(answer.text_answer)
    elif qtype in ('grouped_af', 'multi_part'):
        structured = data.get('structured_answer')
        if structured and isinstance(structured, dict):
            answer.structured_answer = structured
            answer.is_skipped = False
        else:
            answer.is_skipped = True

    answer.save()

    # Status update
    if attempt.status == 'started':
        attempt.status = 'in_progress'
        attempt.save(update_fields=['status'])

    return JsonResponse({
        'success': True,
        'question_id': question_id,
        'skipped': answer.is_skipped,
    })


# ─────────────────────────────────────────────────────────────
# 7. MOCK FINISH
# ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def mock_finish(request, attempt_uuid):
    attempt = get_object_or_404(CertMockAttempt, uuid=attempt_uuid, user=request.user)

    if attempt.status == 'completed':
        return redirect('certificate:mock_result', attempt_uuid=attempt.uuid)

    # Javob bermaganlarni skipped qilib qo'sh
    answered_ids = attempt.answers.values_list('question_id', flat=True)
    unanswered = attempt.mock.questions.filter(is_active=True).exclude(id__in=answered_ids)
    for q in unanswered:
        CertAttemptAnswer.objects.create(attempt=attempt, question=q, is_skipped=True)

    # Hammani auto-check
    for ans in attempt.answers.select_related('question', 'selected_choice').all():
        ans.auto_check()

    # Vaqt hisoblash
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    attempt.time_spent = int(elapsed)
    attempt.save(update_fields=['time_spent'])

    # Natijalar
    attempt.calculate_results()

    # Celery task orqali background statistika
    try:
        from .tasks import process_cert_attempt_results
        process_cert_attempt_results.delay(attempt.id)
    except Exception:
        _update_user_stats(attempt)  # fallback

    return redirect('certificate:mock_result', attempt_uuid=attempt.uuid)


# ─────────────────────────────────────────────────────────────
# 8. RESULT PAGE
# ─────────────────────────────────────────────────────────────

@login_required
def mock_result(request, attempt_uuid):
    attempt = get_object_or_404(
        CertMockAttempt,
        uuid=attempt_uuid,
        user=request.user
    )

    answers = attempt.answers.select_related(
        'question', 'question__topic', 'selected_choice'
    ).prefetch_related(
        'question__choices',
        'question__grouped_options',
        'question__grouped_items__correct_option',
        'question__parts',
    ).order_by('question__number')

    other_mocks = CertMock.objects.filter(
        cert_subject=attempt.mock.cert_subject,
        is_active=True
    ).exclude(id=attempt.mock.id)[:4]

    # answers_data — test_play_result ga o'xshash
    answers_data = []
    for ans in answers:
        correct_choice = None
        for ch in ans.question.choices.all():
            if ch.is_correct:
                correct_choice = ch
                break
        answers_data.append({
            'answer': ans,
            'correct_choice': correct_choice,
        })

    # Mavzu statistikasi
    topic_stats = {}
    for ans in answers:
        if ans.question.topic:
            tname = ans.question.topic.name
            if tname not in topic_stats:
                topic_stats[tname] = {'correct': 0, 'total': 0, 'topic': ans.question.topic}
            topic_stats[tname]['total'] += 1
            if ans.is_correct:
                topic_stats[tname]['correct'] += 1
    for t in topic_stats:
        st = topic_stats[t]
        st['percentage'] = round(st['correct'] / st['total'] * 100) if st['total'] else 0
        st['is_weak'] = st['percentage'] < 50

    # Saqlangan savollar
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(CertSavedQuestion.objects.filter(
            user=request.user,
            question__mock=attempt.mock
        ).values_list('question_id', flat=True))

    context = {
        'attempt': attempt,
        'mock': attempt.mock,
        'cert_subject': attempt.mock.cert_subject,
        'answers': answers,
        'answers_data': answers_data,
        'topic_stats': topic_stats,
        'other_mocks': other_mocks,
        'saved_ids': saved_ids,
        'passing_score': 46,
        'page_title': f"Natija — {attempt.mock.title}",
    }
    return render(request, 'certificate/mock_result.html', context)


# ─────────────────────────────────────────────────────────────
# 9. JSON EXPORT
# ─────────────────────────────────────────────────────────────

@login_required
def export_result_json(request, attempt_uuid):
    attempt = get_object_or_404(CertMockAttempt, uuid=attempt_uuid, user=request.user)

    answers_data = []
    for ans in attempt.answers.select_related('question', 'selected_choice').order_by('question__number'):
        ans_dict = {
            'question_number': ans.question.number,
            'question_type': ans.question.question_type,
            'question_text': ans.question.text,
            'is_correct': ans.is_correct,
            'is_skipped': ans.is_skipped,
            'earned_points': ans.earned_points,
        }
        if ans.selected_choice:
            ans_dict['selected_choice'] = ans.selected_choice.label
        if ans.text_answer:
            ans_dict['text_answer'] = ans.text_answer
        if ans.structured_answer:
            ans_dict['structured_answer'] = ans.structured_answer
        answers_data.append(ans_dict)

    data = {
        'mock': {
            'title': attempt.mock.title,
            'subject': attempt.mock.cert_subject.subject.name,
            'year': attempt.mock.year,
        },
        'user': {
            'full_name': attempt.user.get_full_name(),
            'phone': str(attempt.user.phone_number),
        },
        'result': {
            'status': attempt.status,
            'grade': attempt.grade,
            'feedback': attempt.feedback,
            'correct_answers': attempt.correct_answers,
            'wrong_answers': attempt.wrong_answers,
            'skipped_questions': attempt.skipped_questions,
            'total_questions': attempt.total_questions,
            'percentage': attempt.percentage,
            'earned_points': attempt.earned_points,
            'total_points': attempt.total_points,
            'time_spent_seconds': attempt.time_spent,
            'started_at': attempt.started_at.isoformat(),
            'completed_at': attempt.completed_at.isoformat() if attempt.completed_at else None,
        },
        'answers': answers_data,
    }

    response = HttpResponse(
        json.dumps(data, ensure_ascii=False, indent=2),
        content_type='application/json; charset=utf-8'
    )
    filename = f"natija_{attempt.mock.cert_subject.subject.slug}_{attempt.uuid}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────────────────────
# 10. SAVE / UNSAVE QUESTION (AJAX)
# ─────────────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_save_question(request, question_id):
    question = get_object_or_404(CertQuestion, id=question_id)
    obj, created = CertSavedQuestion.objects.get_or_create(
        user=request.user, question=question
    )
    if not created:
        obj.delete()
        saved = False
    else:
        saved = True

    # AJAX so'rovi — JSON qaytariladi
    if request.headers.get('Content-Type') == 'application/json':
        return JsonResponse({'saved': saved})
    # Oddiy form submit — saved_questions ga redirect
    return redirect('tests_app:saved_questions')
