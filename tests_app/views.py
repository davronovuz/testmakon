"""
TestMakon.uz - Tests App Views
Subjects, tests, questions, results with AI analysis
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q
import random
import json

from .models import (
    Subject, Topic, Question, Answer, Test, TestQuestion,
    TestAttempt, AttemptAnswer, SavedQuestion
)
from accounts.models import UserActivity


def subjects_list(request):
    """Fanlar ro'yxati"""
    subjects = Subject.objects.filter(is_active=True).order_by('order')

    # Har bir fan uchun statistika
    for subject in subjects:
        subject.tests_count = Test.objects.filter(
            subject=subject,
            is_active=True
        ).count()
        subject.questions_count = Question.objects.filter(
            subject=subject,
            is_active=True
        ).count()

    context = {
        'subjects': subjects,
    }

    return render(request, 'tests_app/subjects_list.html', context)


def subject_detail(request, slug):
    """Fan tafsilotlari"""
    subject = get_object_or_404(Subject, slug=slug, is_active=True)

    # Mavzular
    topics = Topic.objects.filter(
        subject=subject,
        is_active=True,
        parent__isnull=True
    ).prefetch_related('subtopics')

    # Testlar
    tests = Test.objects.filter(
        subject=subject,
        is_active=True
    ).order_by('-created_at')[:10]

    # Foydalanuvchi statistikasi (agar login qilgan bo'lsa)
    user_stats = None
    if request.user.is_authenticated:
        attempts = TestAttempt.objects.filter(
            user=request.user,
            test__subject=subject,
            status='completed'
        )
        if attempts.exists():
            user_stats = {
                'tests_taken': attempts.count(),
                'avg_score': round(attempts.aggregate(Avg('percentage'))['percentage__avg'], 1),
                'total_correct': sum(a.correct_answers for a in attempts),
            }

    context = {
        'subject': subject,
        'topics': topics,
        'tests': tests,
        'user_stats': user_stats,
    }

    return render(request, 'tests_app/subject_detail.html', context)


def tests_list(request):
    """Testlar ro'yxati"""
    tests = Test.objects.filter(is_active=True)

    # Filters
    subject_slug = request.GET.get('subject')
    test_type = request.GET.get('type')

    if subject_slug:
        tests = tests.filter(subject__slug=subject_slug)

    if test_type:
        tests = tests.filter(test_type=test_type)

    tests = tests.order_by('-created_at')[:20]

    # Fanlar (filter uchun)
    subjects = Subject.objects.filter(is_active=True)

    context = {
        'tests': tests,
        'subjects': subjects,
        'current_subject': subject_slug,
        'current_type': test_type,
    }

    return render(request, 'tests_app/tests_list.html', context)


def test_detail(request, slug):
    """Test tafsilotlari"""
    test = get_object_or_404(Test, slug=slug, is_active=True)

    # Foydalanuvchi urinishlari
    user_attempts = []
    if request.user.is_authenticated:
        user_attempts = TestAttempt.objects.filter(
            user=request.user,
            test=test
        ).order_by('-started_at')[:5]

    context = {
        'test': test,
        'user_attempts': user_attempts,
    }

    return render(request, 'tests_app/test_detail.html', context)


@login_required
def test_start(request, slug):
    """Testni boshlash"""
    test = get_object_or_404(Test, slug=slug, is_active=True)

    # Mavjud tugallanmagan urinish bormi?
    existing = TestAttempt.objects.filter(
        user=request.user,
        test=test,
        status__in=['started', 'in_progress']
    ).first()

    if existing:
        return redirect('tests_app:test_question', uuid=existing.uuid)

    # Savollarni tanlash
    questions = list(test.questions.filter(is_active=True))

    if test.shuffle_questions:
        random.shuffle(questions)

    questions = questions[:test.question_count]

    if not questions:
        messages.error(request, "Bu testda savollar yo'q")
        return redirect('tests_app:test_detail', slug=slug)

    # Yangi urinish yaratish
    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(questions),
        status='in_progress'
    )

    # Savollarni urinishga bog'lash (session orqali)
    request.session[f'attempt_{attempt.uuid}_questions'] = [q.id for q in questions]
    request.session[f'attempt_{attempt.uuid}_current'] = 0

    return redirect('tests_app:test_question', uuid=attempt.uuid)


@login_required
def test_question(request, uuid):
    """Joriy savol"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user,
        status='in_progress'
    )

    # Session dan savollarni olish
    question_ids = request.session.get(f'attempt_{uuid}_questions', [])
    current_index = request.session.get(f'attempt_{uuid}_current', 0)

    if current_index >= len(question_ids):
        return redirect('tests_app:test_finish', uuid=uuid)

    question = get_object_or_404(Question, id=question_ids[current_index])
    answers = list(question.answers.all())

    if attempt.test.shuffle_answers:
        random.shuffle(answers)

    # Vaqt hisoblash
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    remaining = max(0, attempt.test.time_limit * 60 - elapsed)

    # Oldingi javobni tekshirish
    previous_answer = AttemptAnswer.objects.filter(
        attempt=attempt,
        question=question
    ).first()

    context = {
        'attempt': attempt,
        'question': question,
        'answers': answers,
        'current_index': current_index,
        'total_questions': len(question_ids),
        'remaining_time': int(remaining),
        'previous_answer': previous_answer,
    }

    return render(request, 'tests_app/test_question.html', context)


@login_required
def test_submit_answer(request, uuid):
    """Javobni yuborish"""
    if request.method != 'POST':
        return redirect('tests_app:test_question', uuid=uuid)

    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user,
        status='in_progress'
    )

    question_id = request.POST.get('question_id')
    answer_id = request.POST.get('answer_id')
    time_spent = int(request.POST.get('time_spent', 0))

    question = get_object_or_404(Question, id=question_id)
    selected_answer = get_object_or_404(Answer, id=answer_id) if answer_id else None

    # Javob to'g'rimi?
    is_correct = selected_answer.is_correct if selected_answer else False

    # Javobni saqlash
    AttemptAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'selected_answer': selected_answer,
            'is_correct': is_correct,
            'time_spent': time_spent,
        }
    )

    # Question statistikasini yangilash
    question.times_answered += 1
    if is_correct:
        question.times_correct += 1
    question.save()

    # Keyingi savolga
    current = request.session.get(f'attempt_{uuid}_current', 0)
    request.session[f'attempt_{uuid}_current'] = current + 1

    # Oxirgi savolmi?
    question_ids = request.session.get(f'attempt_{uuid}_questions', [])
    if current + 1 >= len(question_ids):
        return redirect('tests_app:test_finish', uuid=uuid)

    return redirect('tests_app:test_question', uuid=uuid)


@login_required
def test_finish(request, uuid):
    """Testni yakunlash"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    if attempt.status == 'completed':
        return redirect('tests_app:test_result', uuid=uuid)

    # Natijalarni hisoblash
    answers = AttemptAnswer.objects.filter(attempt=attempt)

    attempt.correct_answers = answers.filter(is_correct=True).count()
    attempt.wrong_answers = answers.filter(is_correct=False).count()
    attempt.skipped_questions = attempt.total_questions - answers.count()
    attempt.time_spent = int((timezone.now() - attempt.started_at).total_seconds())

    attempt.calculate_results()

    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.save()

    # User statistikasini yangilash
    user = request.user
    user.total_tests_taken += 1
    user.total_correct_answers += attempt.correct_answers
    user.total_wrong_answers += attempt.wrong_answers
    user.add_xp(attempt.xp_earned)
    user.update_streak()
    user.save()

    # Activity log
    UserActivity.objects.create(
        user=user,
        activity_type='test_complete',
        description=f"{attempt.test.title} - {attempt.percentage}%",
        xp_earned=attempt.xp_earned
    )

    # Session tozalash
    keys_to_delete = [k for k in request.session.keys() if str(uuid) in k]
    for key in keys_to_delete:
        del request.session[key]

    return redirect('tests_app:test_result', uuid=uuid)


@login_required
def test_result(request, uuid):
    """Test natijasi"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user,
        status='completed'
    )

    # Javoblar bilan savollar
    answers = AttemptAnswer.objects.filter(
        attempt=attempt
    ).select_related('question', 'selected_answer')

    # Topic bo'yicha statistika
    topic_stats = {}
    for ans in answers:
        if ans.question.topic:
            topic_name = ans.question.topic.name
            if topic_name not in topic_stats:
                topic_stats[topic_name] = {'correct': 0, 'total': 0}
            topic_stats[topic_name]['total'] += 1
            if ans.is_correct:
                topic_stats[topic_name]['correct'] += 1

    # Foizlarni hisoblash
    for topic in topic_stats:
        stats = topic_stats[topic]
        stats['percentage'] = round((stats['correct'] / stats['total']) * 100)

    context = {
        'attempt': attempt,
        'answers': answers,
        'topic_stats': topic_stats,
    }

    return render(request, 'tests_app/test_result.html', context)


@login_required
def quick_test(request):
    """Tezkor test sahifasi"""
    subjects = Subject.objects.filter(is_active=True)

    context = {
        'subjects': subjects,
    }

    return render(request, 'tests_app/quick_test.html', context)


@login_required
def quick_test_start(request):
    """Tezkor testni boshlash"""
    if request.method != 'POST':
        return redirect('tests_app:quick_test')

    subject_id = request.POST.get('subject_id')
    question_count = int(request.POST.get('question_count', 10))
    difficulty = request.POST.get('difficulty', '')

    subject = get_object_or_404(Subject, id=subject_id)

    # Savollarni tanlash
    questions = Question.objects.filter(
        subject=subject,
        is_active=True
    )

    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    questions = list(questions)
    random.shuffle(questions)
    questions = questions[:question_count]

    if not questions:
        messages.error(request, "Savollar topilmadi")
        return redirect('tests_app:quick_test')

    # Test va urinish yaratish
    test = Test.objects.create(
        title=f"Tezkor test - {subject.name}",
        slug=f"quick-{request.user.id}-{timezone.now().timestamp()}",
        test_type='quick',
        subject=subject,
        time_limit=question_count * 2,  # Har bir savol uchun 2 daqiqa
        question_count=question_count,
        created_by=request.user
    )

    for i, q in enumerate(questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(questions),
        status='in_progress'
    )

    request.session[f'attempt_{attempt.uuid}_questions'] = [q.id for q in questions]
    request.session[f'attempt_{attempt.uuid}_current'] = 0

    return redirect('tests_app:test_question', uuid=attempt.uuid)


@login_required
def block_test(request):
    """Blok test sahifasi"""
    subjects = Subject.objects.filter(is_active=True)

    context = {
        'subjects': subjects,
    }

    return render(request, 'tests_app/block_test.html', context)


@login_required
def block_test_start(request):
    """Blok testni boshlash"""
    if request.method != 'POST':
        return redirect('tests_app:block_test')

    subject_ids = request.POST.getlist('subjects')
    questions_per_subject = int(request.POST.get('questions_per_subject', 10))

    if len(subject_ids) < 2:
        messages.error(request, "Kamida 2 ta fan tanlang")
        return redirect('tests_app:block_test')

    all_questions = []
    subjects = Subject.objects.filter(id__in=subject_ids)

    for subject in subjects:
        questions = list(Question.objects.filter(
            subject=subject,
            is_active=True
        ))
        random.shuffle(questions)
        all_questions.extend(questions[:questions_per_subject])

    if not all_questions:
        messages.error(request, "Savollar topilmadi")
        return redirect('tests_app:block_test')

    # Test yaratish
    test = Test.objects.create(
        title=f"Blok test - {', '.join([s.name for s in subjects])}",
        slug=f"block-{request.user.id}-{timezone.now().timestamp()}",
        test_type='block',
        time_limit=len(all_questions) * 2,
        question_count=len(all_questions),
        created_by=request.user
    )
    test.subjects.set(subjects)

    random.shuffle(all_questions)
    for i, q in enumerate(all_questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(all_questions),
        status='in_progress'
    )

    request.session[f'attempt_{attempt.uuid}_questions'] = [q.id for q in all_questions]
    request.session[f'attempt_{attempt.uuid}_current'] = 0

    return redirect('tests_app:test_question', uuid=attempt.uuid)


def topic_test(request, subject_slug, topic_slug):
    """Mavzu bo'yicha test"""
    subject = get_object_or_404(Subject, slug=subject_slug)
    topic = get_object_or_404(Topic, slug=topic_slug, subject=subject)

    # Bu mavzu bo'yicha savollar
    questions_count = Question.objects.filter(
        topic=topic,
        is_active=True
    ).count()

    context = {
        'subject': subject,
        'topic': topic,
        'questions_count': questions_count,
    }

    return render(request, 'tests_app/topic_test.html', context)


@login_required
def my_results(request):
    """Mening natijalarim"""
    attempts = TestAttempt.objects.filter(
        user=request.user,
        status='completed'
    ).select_related('test', 'test__subject').order_by('-completed_at')

    # Statistika
    stats = {
        'total': attempts.count(),
        'avg_score': round(attempts.aggregate(Avg('percentage'))['percentage__avg'] or 0, 1),
        'total_correct': sum(a.correct_answers for a in attempts),
        'total_xp': sum(a.xp_earned for a in attempts),
    }

    context = {
        'attempts': attempts[:20],
        'stats': stats,
    }

    return render(request, 'tests_app/my_results.html', context)


@login_required
def result_detail(request, uuid):
    """Natija tafsilotlari"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    answers = AttemptAnswer.objects.filter(
        attempt=attempt
    ).select_related('question', 'selected_answer', 'question__topic')

    context = {
        'attempt': attempt,
        'answers': answers,
    }

    return render(request, 'tests_app/result_detail.html', context)


@login_required
def saved_questions(request):
    """Saqlangan savollar"""
    saved = SavedQuestion.objects.filter(
        user=request.user
    ).select_related('question', 'question__subject')

    context = {
        'saved': saved,
    }

    return render(request, 'tests_app/saved_questions.html', context)


@login_required
def save_question(request, question_id):
    """Savolni saqlash"""
    question = get_object_or_404(Question, id=question_id)

    SavedQuestion.objects.get_or_create(
        user=request.user,
        question=question
    )

    messages.success(request, "Savol saqlandi")

    # Qaytish
    next_url = request.GET.get('next', 'tests_app:saved_questions')
    return redirect(next_url)


@login_required
def unsave_question(request, question_id):
    """Savolni o'chirish"""
    SavedQuestion.objects.filter(
        user=request.user,
        question_id=question_id
    ).delete()

    messages.info(request, "Savol o'chirildi")
    return redirect('tests_app:saved_questions')


@login_required
def wrong_answers(request):
    """Noto'g'ri javoblar"""
    wrong = AttemptAnswer.objects.filter(
        attempt__user=request.user,
        is_correct=False
    ).select_related(
        'question', 'question__subject', 'selected_answer'
    ).order_by('-answered_at')[:50]

    context = {
        'wrong_answers': wrong,
    }

    return render(request, 'tests_app/wrong_answers.html', context)


@login_required
def wrong_answers_practice(request):
    """Noto'g'ri javoblar ustida mashq"""
    # Noto'g'ri javob berilgan savollarni olish
    wrong_question_ids = AttemptAnswer.objects.filter(
        attempt__user=request.user,
        is_correct=False
    ).values_list('question_id', flat=True).distinct()[:20]

    questions = list(Question.objects.filter(id__in=wrong_question_ids))

    if not questions:
        messages.info(request, "Noto'g'ri javoblar yo'q")
        return redirect('tests_app:my_results')

    random.shuffle(questions)

    # Test yaratish
    test = Test.objects.create(
        title="Xatolar ustida ishlash",
        slug=f"wrong-{request.user.id}-{timezone.now().timestamp()}",
        test_type='practice',
        time_limit=len(questions) * 3,
        question_count=len(questions),
        created_by=request.user
    )

    for i, q in enumerate(questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(questions),
        status='in_progress'
    )

    request.session[f'attempt_{attempt.uuid}_questions'] = [q.id for q in questions]
    request.session[f'attempt_{attempt.uuid}_current'] = 0

    return redirect('tests_app:test_question', uuid=attempt.uuid)


# API Views

def api_subjects(request):
    """Fanlar API"""
    subjects = Subject.objects.filter(is_active=True).values(
        'id', 'name', 'slug', 'icon', 'color'
    )

    return JsonResponse({'subjects': list(subjects)})


@login_required
def api_test_progress(request, uuid):
    """Test progress API"""
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    answered = AttemptAnswer.objects.filter(attempt=attempt).count()

    data = {
        'total': attempt.total_questions,
        'answered': answered,
        'remaining': attempt.total_questions - answered,
        'elapsed': int((timezone.now() - attempt.started_at).total_seconds()),
    }

    return JsonResponse(data)