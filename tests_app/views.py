"""
TestMakon.uz - Tests App Views
Professional Question Bank + Test System (OnePrep Style)
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Avg, Count, Q, Sum, F
from django.views.decorators.http import require_POST, require_GET
from django.core.paginator import Paginator
from datetime import timedelta
import random
import json

from .models import (
    Subject, Topic, Question, Answer, Test, TestQuestion,
    TestAttempt, AttemptAnswer, SavedQuestion,
    UserTopicPerformance, UserSubjectPerformance,
    DailyUserStats, UserActivityLog
)


# ============================================================
# QUESTION BANK (OnePrep 1-rasm kabi)
# ============================================================

def question_bank(request):
    """
    Asosiy Question Bank sahifasi
    Barcha fanlar va ularning mavzulari
    """
    subjects = Subject.objects.filter(is_active=True).order_by('order')

    # Har bir fan uchun statistika
    subjects_data = []
    for subject in subjects:
        # Savollar soni
        questions_count = Question.objects.filter(
            subject=subject,
            is_active=True
        ).count()

        # Mavzular
        topics = Topic.objects.filter(
            subject=subject,
            is_active=True,
            parent__isnull=True
        ).annotate(
            questions_count=Count('questions', filter=Q(questions__is_active=True))
        ).order_by('order')

        # User progress (agar login bo'lsa)
        user_progress = None
        if request.user.is_authenticated:
            perf = UserSubjectPerformance.objects.filter(
                user=request.user,
                subject=subject
            ).first()
            if perf:
                user_progress = {
                    'total_solved': perf.total_questions,
                    'accuracy': round(perf.average_score, 1),
                    'correct': perf.correct_answers,
                }

        subjects_data.append({
            'subject': subject,
            'questions_count': questions_count,
            'topics': topics,
            'user_progress': user_progress,
        })

    context = {
        'subjects_data': subjects_data,
    }

    return render(request, 'tests_app/question_bank.html', context)


def question_bank_subject(request, subject_slug):
    """
    Bitta fan uchun Question Bank
    Mavzular, filterlar, progress
    """
    subject = get_object_or_404(Subject, slug=subject_slug, is_active=True)

    # Barcha mavzular (parent va child)
    topics = Topic.objects.filter(
        subject=subject,
        is_active=True,
        parent__isnull=True
    ).prefetch_related('subtopics').annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    # Filterlar
    difficulty = request.GET.get('difficulty', '')
    solved = request.GET.get('solved', '')  # all, solved, unsolved
    bookmarked = request.GET.get('bookmarked', '')

    # User statistikasi
    user_stats = None
    topic_performances = {}

    if request.user.is_authenticated:
        # Umumiy fan statistikasi
        perf = UserSubjectPerformance.objects.filter(
            user=request.user,
            subject=subject
        ).first()

        if perf:
            user_stats = {
                'total_solved': perf.total_questions,
                'correct': perf.correct_answers,
                'accuracy': round(perf.average_score, 1) if perf.average_score else 0,
                'time_spent': perf.total_time_spent // 60,  # daqiqada
            }

        # Mavzu bo'yicha progress
        topic_perfs = UserTopicPerformance.objects.filter(
            user=request.user,
            subject=subject
        )
        for tp in topic_perfs:
            topic_performances[tp.topic_id] = {
                'solved': tp.total_questions,
                'correct': tp.correct_answers,
                'score': round(tp.current_score, 1),
                'is_weak': tp.is_weak,
                'is_strong': tp.is_strong,
            }

        # Bookmarked savollar soni
        bookmarked_count = SavedQuestion.objects.filter(
            user=request.user,
            question__subject=subject
        ).count()
    else:
        bookmarked_count = 0

    # Jami savollar soni
    total_questions = Question.objects.filter(
        subject=subject,
        is_active=True
    ).count()

    context = {
        'subject': subject,
        'topics': topics,
        'user_stats': user_stats,
        'topic_performances': topic_performances,
        'total_questions': total_questions,
        'bookmarked_count': bookmarked_count,
        'current_difficulty': difficulty,
        'current_solved': solved,
        'current_bookmarked': bookmarked,
    }

    return render(request, 'tests_app/question_bank_subject.html', context)


# ============================================================
# PRACTICE (Dinamik test yaratish)
# ============================================================

def practice_select(request):
    """
    Practice uchun fan tanlash sahifasi
    """
    subjects = Subject.objects.filter(is_active=True).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    context = {
        'subjects': subjects,
    }

    return render(request, 'tests_app/practice_select.html', context)


@login_required
def practice_subject(request, subject_slug):
    """
    Fan tanlangandan keyin mavzu va sozlamalar
    """
    subject = get_object_or_404(Subject, slug=subject_slug, is_active=True)

    topics = Topic.objects.filter(
        subject=subject,
        is_active=True,
        parent__isnull=True
    ).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    # Jami savollar
    total_questions = Question.objects.filter(
        subject=subject,
        is_active=True
    ).count()

    context = {
        'subject': subject,
        'topics': topics,
        'total_questions': total_questions,
    }

    return render(request, 'tests_app/practice_subject.html', context)


@login_required
def practice_topic(request, subject_slug, topic_slug):
    """
    Mavzu tanlangandan keyin sozlamalar
    """
    subject = get_object_or_404(Subject, slug=subject_slug, is_active=True)
    topic = get_object_or_404(Topic, slug=topic_slug, subject=subject, is_active=True)

    # Bu mavzudagi savollar soni
    questions_count = Question.objects.filter(
        topic=topic,
        is_active=True
    ).count()

    # Subtopics
    subtopics = topic.subtopics.filter(is_active=True).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    )

    # User progress
    user_progress = None
    if request.user.is_authenticated:
        perf = UserTopicPerformance.objects.filter(
            user=request.user,
            topic=topic
        ).first()
        if perf:
            user_progress = {
                'solved': perf.total_questions,
                'correct': perf.correct_answers,
                'score': round(perf.current_score, 1),
            }

    context = {
        'subject': subject,
        'topic': topic,
        'subtopics': subtopics,
        'questions_count': questions_count,
        'user_progress': user_progress,
    }

    return render(request, 'tests_app/practice_topic.html', context)


@login_required
@require_POST
def practice_start(request):
    """
    Practice testni boshlash
    POST parametrlari:
    - subject_id: Fan ID
    - topic_id: Mavzu ID (ixtiyoriy, bo'sh = barcha mavzular)
    - question_count: Savollar soni (10, 20, 30, 50)
    - difficulty: Qiyinlik (easy, medium, hard, all)
    - mode: Rejim (practice, timed, exam)
    """
    subject_id = request.POST.get('subject_id')
    topic_id = request.POST.get('topic_id', '')
    question_count = int(request.POST.get('question_count', 10))
    difficulty = request.POST.get('difficulty', 'all')
    mode = request.POST.get('mode', 'practice')

    # Validatsiya
    subject = get_object_or_404(Subject, id=subject_id, is_active=True)

    # Savollarni filter qilish
    questions = Question.objects.filter(
        subject=subject,
        is_active=True
    )

    # Mavzu bo'yicha filter
    if topic_id:
        topic = get_object_or_404(Topic, id=topic_id)
        # Topic va uning subtopic lari
        topic_ids = [topic.id] + list(topic.subtopics.values_list('id', flat=True))
        questions = questions.filter(topic_id__in=topic_ids)
    else:
        topic = None

    # Qiyinlik bo'yicha filter
    if difficulty and difficulty != 'all':
        questions = questions.filter(difficulty=difficulty)

    # Allaqachon yechilgan savollarni oxiriga qo'yish (yangi savollar birinchi)
    answered_ids = AttemptAnswer.objects.filter(
        attempt__user=request.user,
        question__subject=subject
    ).values_list('question_id', flat=True)

    # Savollarni tanlash
    questions = list(questions)

    if not questions:
        messages.error(request, "Savollar topilmadi. Boshqa parametrlar tanlang.")
        return redirect('tests_app:practice_subject', subject_slug=subject.slug)

    # Yangi savollarni birinchi, eskilarni keyingi
    new_questions = [q for q in questions if q.id not in answered_ids]
    old_questions = [q for q in questions if q.id in answered_ids]

    random.shuffle(new_questions)
    random.shuffle(old_questions)

    selected_questions = (new_questions + old_questions)[:question_count]

    if not selected_questions:
        messages.error(request, "Yetarli savol topilmadi.")
        return redirect('tests_app:practice_subject', subject_slug=subject.slug)

    # Test yaratish
    test_title = f"Practice - {subject.name}"
    if topic:
        test_title += f" - {topic.name}"

    # Vaqt limiti
    if mode == 'timed':
        time_limit = question_count * 2  # Har savolga 2 daqiqa
    elif mode == 'exam':
        time_limit = question_count * 1  # Har savolga 1 daqiqa (DTM formati)
    else:
        time_limit = 0  # Vaqt chegarasiz

    test = Test.objects.create(
        title=test_title,
        slug=f"practice-{request.user.id}-{timezone.now().timestamp()}",
        test_type='practice',
        subject=subject,
        time_limit=time_limit,
        question_count=len(selected_questions),
        shuffle_questions=False,  # Allaqachon aralashtirdik
        shuffle_answers=True,
        show_correct_answers=True,
        created_by=request.user
    )

    # Savollarni testga qo'shish
    for i, q in enumerate(selected_questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    # Test urinishini yaratish
    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(selected_questions),
        status='in_progress'
    )

    # Activity log
    UserActivityLog.objects.create(
        user=request.user,
        action='test_start',
        details={
            'test_id': test.id,
            'test_type': 'practice',
            'subject': subject.name,
            'topic': topic.name if topic else 'all',
            'question_count': len(selected_questions),
            'mode': mode,
        },
        subject=subject,
        topic=topic
    )

    return redirect('tests_app:test_play', uuid=attempt.uuid)


# ============================================================
# TEST PLAY (Professional UI - OnePrep 2-3 rasm kabi)
# ============================================================

@login_required
def test_play(request, uuid):
    """
    Professional test ishlash interfeysi
    OnePrep 2-3 rasm kabi
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    # Agar yakunlangan bo'lsa, natijaga yo'naltirish
    if attempt.status == 'completed':
        return redirect('tests_app:test_play_result', uuid=uuid)

    # Test va savollar
    test = attempt.test
    test_questions = TestQuestion.objects.filter(
        test=test
    ).select_related('question').order_by('order')

    questions_data = []
    for i, tq in enumerate(test_questions):
        q = tq.question
        answers = list(q.answers.all().order_by('order'))

        if test.shuffle_answers:
            random.shuffle(answers)

        # User javobini tekshirish
        user_answer = AttemptAnswer.objects.filter(
            attempt=attempt,
            question=q
        ).first()

        # Bookmark tekshirish
        is_bookmarked = SavedQuestion.objects.filter(
            user=request.user,
            question=q
        ).exists()

        questions_data.append({
            'index': i,
            'question': q,
            'answers': answers,
            'user_answer': user_answer,
            'is_bookmarked': is_bookmarked,
            'status': 'answered' if user_answer else 'unanswered',
        })

    # Vaqt hisoblash
    if test.time_limit > 0:
        elapsed = (timezone.now() - attempt.started_at).total_seconds()
        remaining = max(0, test.time_limit * 60 - elapsed)
    else:
        remaining = None  # Vaqt chegarasiz

    # Joriy savol (session dan yoki birinchi javob berilmagan)
    current_index = request.session.get(f'attempt_{uuid}_current', 0)

    # Subject uchun tool aniqlash
    subject_tools = get_subject_tools(test.subject)

    context = {
        'attempt': attempt,
        'test': test,
        'questions_data': questions_data,
        'current_index': current_index,
        'remaining_time': int(remaining) if remaining else None,
        'subject_tools': subject_tools,
    }

    return render(request, 'tests_app/test_play.html', context)


@login_required
@require_POST
def test_play_submit(request, uuid):
    """
    AJAX orqali javob yuborish
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user,
        status='in_progress'
    )

    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer_id = data.get('answer_id')
        time_spent = data.get('time_spent', 0)
        current_index = data.get('current_index', 0)
    except:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

    question = get_object_or_404(Question, id=question_id)

    # Javob null bo'lishi mumkin (skip)
    selected_answer = None
    is_correct = False

    if answer_id:
        selected_answer = get_object_or_404(Answer, id=answer_id)
        is_correct = selected_answer.is_correct

    # Javobni saqlash yoki yangilash
    attempt_answer, created = AttemptAnswer.objects.update_or_create(
        attempt=attempt,
        question=question,
        defaults={
            'selected_answer': selected_answer,
            'is_correct': is_correct,
            'time_spent': time_spent,
        }
    )

    # Question statistikasini yangilash
    if created:
        question.times_answered += 1
        if is_correct:
            question.times_correct += 1
        question.save(update_fields=['times_answered', 'times_correct'])

    # Session da joriy indexni saqlash
    request.session[f'attempt_{uuid}_current'] = current_index

    return JsonResponse({
        'success': True,
        'is_correct': is_correct,
        'correct_answer_id': question.answers.filter(is_correct=True).first().id if question.answers.filter(
            is_correct=True).exists() else None,
    })


@login_required
def test_play_finish(request, uuid):
    """
    Testni yakunlash
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    if attempt.status == 'completed':
        return redirect('tests_app:test_play_result', uuid=uuid)

    # Natijalarni hisoblash
    answers = AttemptAnswer.objects.filter(attempt=attempt)

    attempt.correct_answers = answers.filter(is_correct=True).count()
    attempt.wrong_answers = answers.filter(is_correct=False, selected_answer__isnull=False).count()
    attempt.skipped_questions = attempt.total_questions - answers.count()
    attempt.time_spent = int((timezone.now() - attempt.started_at).total_seconds())

    # Foiz va XP hisoblash
    if attempt.total_questions > 0:
        attempt.percentage = round((attempt.correct_answers / attempt.total_questions) * 100, 1)
    else:
        attempt.percentage = 0

    attempt.score = attempt.correct_answers

    # XP hisoblash
    base_xp = attempt.correct_answers * 10
    if attempt.percentage >= 90:
        base_xp = int(base_xp * 2)
    elif attempt.percentage >= 70:
        base_xp = int(base_xp * 1.5)
    attempt.xp_earned = base_xp

    attempt.status = 'completed'
    attempt.completed_at = timezone.now()
    attempt.save()

    # User statistikasini yangilash
    user = request.user
    user.total_tests_taken = F('total_tests_taken') + 1
    user.total_correct_answers = F('total_correct_answers') + attempt.correct_answers
    user.total_wrong_answers = F('total_wrong_answers') + attempt.wrong_answers
    user.xp_points = F('xp_points') + attempt.xp_earned
    user.save(update_fields=['total_tests_taken', 'total_correct_answers', 'total_wrong_answers', 'xp_points'])

    # Activity log
    UserActivityLog.objects.create(
        user=request.user,
        action='test_complete',
        details={
            'test_id': attempt.test.id,
            'score': attempt.percentage,
            'correct': attempt.correct_answers,
            'total': attempt.total_questions,
            'time_spent': attempt.time_spent,
            'xp_earned': attempt.xp_earned,
        },
        subject=attempt.test.subject
    )

    # Session tozalash
    session_key = f'attempt_{uuid}_current'
    if session_key in request.session:
        del request.session[session_key]

    return redirect('tests_app:test_play_result', uuid=uuid)


@login_required
def test_play_result(request, uuid):
    """
    Test natijasi sahifasi
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user,
        status='completed'
    )

    # Javoblar bilan savollar
    answers = AttemptAnswer.objects.filter(
        attempt=attempt
    ).select_related(
        'question', 'question__topic', 'selected_answer'
    ).order_by('answered_at')

    # To'g'ri javoblarni qo'shish
    answers_data = []
    for ans in answers:
        correct_answer = ans.question.answers.filter(is_correct=True).first()
        answers_data.append({
            'answer': ans,
            'correct_answer': correct_answer,
        })

    # Topic bo'yicha statistika
    topic_stats = {}
    for ans in answers:
        if ans.question.topic:
            topic_name = ans.question.topic.name
            if topic_name not in topic_stats:
                topic_stats[topic_name] = {'correct': 0, 'total': 0, 'topic': ans.question.topic}
            topic_stats[topic_name]['total'] += 1
            if ans.is_correct:
                topic_stats[topic_name]['correct'] += 1

    # Foizlarni hisoblash
    for topic in topic_stats:
        stats = topic_stats[topic]
        stats['percentage'] = round((stats['correct'] / stats['total']) * 100) if stats['total'] > 0 else 0
        stats['is_weak'] = stats['percentage'] < 50

    context = {
        'attempt': attempt,
        'answers_data': answers_data,
        'topic_stats': topic_stats,
    }

    return render(request, 'tests_app/test_play_result.html', context)


# ============================================================
# DTM SIMULATION
# ============================================================

@login_required
def dtm_simulation(request):
    """
    DTM simulyatsiya sahifasi
    Blok tanlash
    """
    subjects = Subject.objects.filter(is_active=True).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    ).order_by('order')

    # Oldindan belgilangan bloklar
    preset_blocks = [
        {
            'name': 'Aniq fanlar',
            'subjects': ['matematika', 'fizika', 'ingliz-tili'],
            'description': 'Matematika + Fizika + Ingliz tili',
        },
        {
            'name': 'Tabiiy fanlar',
            'subjects': ['biologiya', 'kimyo', 'ingliz-tili'],
            'description': 'Biologiya + Kimyo + Ingliz tili',
        },
        {
            'name': 'Ijtimoiy fanlar',
            'subjects': ['tarix', 'geografiya', 'ingliz-tili'],
            'description': 'Tarix + Geografiya + Ingliz tili',
        },
    ]

    context = {
        'subjects': subjects,
        'preset_blocks': preset_blocks,
    }

    return render(request, 'tests_app/dtm_simulation.html', context)

@login_required
@require_POST
def dtm_simulation_start(request):
    fan1_id = request.POST.get('fan1')
    fan2_id = request.POST.get('fan2')

    if not fan1_id or not fan2_id:
        messages.error(request, "Ikkita yo'nalish fanini tanlang")
        return redirect('tests_app:dtm_simulation')

    if fan1_id == fan2_id:
        messages.error(request, "Ikki xil fan tanlang")
        return redirect('tests_app:dtm_simulation')

    fan1 = get_object_or_404(Subject, id=fan1_id, is_active=True)
    fan2 = get_object_or_404(Subject, id=fan2_id, is_active=True)

    seen_ids = set()

    def get_questions(subject, count):
        """Fandan unique savollarni olish"""
        questions = list(Question.objects.filter(
            subject=subject,
            is_active=True
        ).exclude(id__in=seen_ids))
        random.shuffle(questions)
        selected = questions[:count]
        for q in selected:
            seen_ids.add(q.id)
        return selected

    # ==========================================
    # DTM TARTIB:
    # 1) 1-fan — 30 ta savol (93 ball)
    # 2) 2-fan — 30 ta savol (63 ball)
    # 3) Majburiy fanlar — 30 ta savol (33 ball)
    #    - Ona tili: 10 ta
    #    - Matematika: 10 ta
    #    - O'zbekiston tarixi: 10 ta
    # ==========================================

    all_questions = []

    # 1) YO'NALISH 1-FAN — 30 ta
    all_questions.extend(get_questions(fan1, 30))

    # 2) YO'NALISH 2-FAN — 30 ta
    all_questions.extend(get_questions(fan2, 30))

    # 3) MAJBURIY FANLAR — har biridan 10 ta
    mandatory_slugs = ['ona-tili', 'matematika', 'ozbekiston-tarixi']
    for slug in mandatory_slugs:
        subj = Subject.objects.filter(slug=slug, is_active=True).first()
        if not subj and slug == 'ozbekiston-tarixi':
            subj = Subject.objects.filter(slug='tarix', is_active=True).first()
        if subj:
            all_questions.extend(get_questions(subj, 10))

    if len(all_questions) < 20:
        messages.error(request, "Yetarli savol topilmadi. Boshqa fanlarni tanlang.")
        return redirect('tests_app:dtm_simulation')

    # TEST YARATISH
    test = Test.objects.create(
        title=f"DTM Simulyatsiya — {fan1.name} + {fan2.name}",
        slug=f"dtm-{request.user.id}-{timezone.now().timestamp()}",
        test_type='exam',
        time_limit=180,
        question_count=len(all_questions),
        shuffle_questions=False,   # ARALASHTIRILMAYDI — tartib muhim!
        shuffle_answers=True,
        show_correct_answers=True,
        created_by=request.user
    )

    # Fanlarni bog'lash
    subject_ids = set([fan1.id, fan2.id])
    for slug in mandatory_slugs:
        s = Subject.objects.filter(slug=slug, is_active=True).first()
        if not s and slug == 'ozbekiston-tarixi':
            s = Subject.objects.filter(slug='tarix', is_active=True).first()
        if s:
            subject_ids.add(s.id)
    test.subjects.set(Subject.objects.filter(id__in=subject_ids))

    # Savollarni TARTIB BILAN qo'shish (aralashtirilmaydi!)
    for i, q in enumerate(all_questions):
        TestQuestion.objects.create(test=test, question=q, order=i)

    # Attempt
    attempt = TestAttempt.objects.create(
        user=request.user,
        test=test,
        total_questions=len(all_questions),
        status='in_progress'
    )

    UserActivityLog.objects.create(
        user=request.user,
        action='test_start',
        details={
            'test_id': test.id,
            'test_type': 'dtm_simulation',
            'fan1': fan1.name,
            'fan2': fan2.name,
            'question_count': len(all_questions),
        },
        subject=fan1
    )

    return redirect('tests_app:test_play', uuid=attempt.uuid)


# ============================================================
# SUBJECT TOOLS (Calculator, Periodic Table, etc.)
# ============================================================

def get_subject_tools(subject):
    """
    Fan uchun kerakli toollarni qaytarish
    """
    if not subject:
        return []

    slug = subject.slug.lower()

    tools = {
        'matematika': [
            {'id': 'calculator', 'name': 'Kalkulyator', 'icon': 'bi-calculator', 'type': 'desmos'},
            {'id': 'formula', 'name': 'Formulalar', 'icon': 'bi-journal-text', 'type': 'sheet'},
        ],
        'fizika': [
            {'id': 'calculator', 'name': 'Kalkulyator', 'icon': 'bi-calculator', 'type': 'scientific'},
            {'id': 'formula', 'name': 'Formulalar', 'icon': 'bi-journal-text', 'type': 'sheet'},
            {'id': 'constants', 'name': 'Konstantalar', 'icon': 'bi-list-ul', 'type': 'sheet'},
        ],
        'kimyo': [
            {'id': 'periodic', 'name': 'Mendeleyev jadvali', 'icon': 'bi-grid-3x3', 'type': 'periodic'},
            {'id': 'calculator', 'name': 'Kalkulyator', 'icon': 'bi-calculator', 'type': 'scientific'},
        ],
        'biologiya': [
            {'id': 'anatomy', 'name': 'Anatomiya', 'icon': 'bi-heart-pulse', 'type': 'atlas'},
        ],
        'geografiya': [
            {'id': 'globe', 'name': 'Xarita', 'icon': 'bi-globe-americas', 'type': 'map'},
        ],
        'tarix': [
            {'id': 'timeline', 'name': 'Vaqt chizig\'i', 'icon': 'bi-calendar-range', 'type': 'timeline'},
        ],
        'ingliz-tili': [
            {'id': 'dictionary', 'name': 'Lug\'at', 'icon': 'bi-book', 'type': 'dictionary'},
        ],
        'ona-tili': [
            {'id': 'dictionary', 'name': 'Imlo lug\'ati', 'icon': 'bi-spellcheck', 'type': 'dictionary'},
        ],
    }

    return tools.get(slug, [])


# ============================================================
# API ENDPOINTS
# ============================================================

@login_required
@require_POST
def api_submit_answer(request, uuid):
    """
    AJAX orqali javob yuborish (test_play_submit bilan bir xil)
    """
    return test_play_submit(request, uuid)


@login_required
def api_test_status(request, uuid):
    """
    Test holatini olish
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    answers = AttemptAnswer.objects.filter(attempt=attempt)
    answered_count = answers.count()
    correct_count = answers.filter(is_correct=True).count()

    # Har bir savol uchun status
    questions_status = {}
    for ans in answers:
        questions_status[ans.question_id] = {
            'answered': True,
            'is_correct': ans.is_correct,
            'answer_id': ans.selected_answer_id,
        }

    # Bookmarked savollar
    bookmarked = list(SavedQuestion.objects.filter(
        user=request.user,
        question__tests=attempt.test
    ).values_list('question_id', flat=True))

    # Qolgan vaqt
    remaining = None
    if attempt.test.time_limit > 0:
        elapsed = (timezone.now() - attempt.started_at).total_seconds()
        remaining = max(0, attempt.test.time_limit * 60 - elapsed)

    return JsonResponse({
        'status': attempt.status,
        'total': attempt.total_questions,
        'answered': answered_count,
        'correct': correct_count,
        'remaining_time': int(remaining) if remaining else None,
        'questions_status': questions_status,
        'bookmarked': bookmarked,
    })


@login_required
def api_navigate(request, uuid):
    """
    Savol navigatsiyasi
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    index = request.GET.get('index', 0)

    try:
        index = int(index)
    except:
        index = 0

    # Session ga saqlash
    request.session[f'attempt_{uuid}_current'] = index

    return JsonResponse({'success': True, 'current_index': index})


@login_required
@require_POST
def api_bookmark(request, uuid, question_id):
    """
    Savolni bookmark qilish/olib tashlash
    """
    question = get_object_or_404(Question, id=question_id)

    saved, created = SavedQuestion.objects.get_or_create(
        user=request.user,
        question=question
    )

    if not created:
        saved.delete()
        is_bookmarked = False
    else:
        is_bookmarked = True

    return JsonResponse({
        'success': True,
        'is_bookmarked': is_bookmarked,
    })


@login_required
def api_time_sync(request, uuid):
    """
    Server bilan vaqtni sinxronlash
    """
    attempt = get_object_or_404(
        TestAttempt,
        uuid=uuid,
        user=request.user
    )

    if attempt.test.time_limit > 0:
        elapsed = (timezone.now() - attempt.started_at).total_seconds()
        remaining = max(0, attempt.test.time_limit * 60 - elapsed)

        # Vaqt tugagan bo'lsa
        if remaining <= 0 and attempt.status == 'in_progress':
            attempt.status = 'timeout'
            attempt.save(update_fields=['status'])
            return JsonResponse({
                'remaining': 0,
                'timeout': True,
            })
    else:
        remaining = None

    return JsonResponse({
        'remaining': int(remaining) if remaining else None,
        'timeout': False,
    })


def api_subjects(request):
    """
    Fanlar ro'yxati API
    """
    subjects = Subject.objects.filter(is_active=True).values(
        'id', 'name', 'slug', 'icon', 'color'
    ).order_by('order')

    return JsonResponse({'subjects': list(subjects)})


def api_topics(request, subject_id):
    """
    Fan mavzulari API
    """
    topics = Topic.objects.filter(
        subject_id=subject_id,
        is_active=True,
        parent__isnull=True
    ).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    ).values(
        'id', 'name', 'slug', 'questions_count'
    ).order_by('order')

    return JsonResponse({'topics': list(topics)})


def api_questions(request):
    """
    Savollar API (filter bilan)
    """
    subject_id = request.GET.get('subject')
    topic_id = request.GET.get('topic')
    difficulty = request.GET.get('difficulty')
    limit = min(int(request.GET.get('limit', 20)), 100)

    questions = Question.objects.filter(is_active=True)

    if subject_id:
        questions = questions.filter(subject_id=subject_id)

    if topic_id:
        questions = questions.filter(topic_id=topic_id)

    if difficulty:
        questions = questions.filter(difficulty=difficulty)

    questions = questions.values(
        'id', 'text', 'difficulty', 'subject__name', 'topic__name'
    )[:limit]

    return JsonResponse({'questions': list(questions)})


def api_get_tools(request, subject_slug):
    """
    Fan uchun toollar
    """
    subject = get_object_or_404(Subject, slug=subject_slug)
    tools = get_subject_tools(subject)

    return JsonResponse({'tools': tools})


@login_required
@require_POST
def api_save_question(request, question_id):
    """
    Savolni saqlash/o'chirish
    """
    question = get_object_or_404(Question, id=question_id)

    saved, created = SavedQuestion.objects.get_or_create(
        user=request.user,
        question=question
    )

    if not created:
        saved.delete()
        return JsonResponse({'saved': False})

    return JsonResponse({'saved': True})


@login_required
@require_POST
def api_log_violation(request):
    """
    Anti-cheat violation log
    """
    try:
        data = json.loads(request.body)
        violation_type = data.get('type', 'unknown')
        attempt_id = data.get('attemptId')

        UserActivityLog.objects.create(
            user=request.user,
            action='violation',
            details={
                'type': violation_type,
                'attempt_id': attempt_id,
                'timestamp': data.get('timestamp'),
            },
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        return JsonResponse({'logged': True})
    except:
        return JsonResponse({'logged': False}, status=400)


# ============================================================
# ESKI VIEWLAR (Backward compatibility)
# ============================================================

def subjects_list(request):
    """Fanlar ro'yxati (eski)"""
    return redirect('tests_app:question_bank')


def subject_detail(request, slug):
    """Fan tafsilotlari (eski)"""
    return redirect('tests_app:question_bank_subject', subject_slug=slug)


def tests_list(request):
    """Testlar ro'yxati"""
    tests = Test.objects.filter(
        is_active=True,
        test_type__in=['practice', 'exam', 'block']
    ).exclude(
        slug__startswith='practice-'
    ).exclude(
        slug__startswith='quick-'
    ).exclude(
        slug__startswith='dtm-'
    ).exclude(
        slug__startswith='block-'
    ).exclude(
        slug__startswith='wrong-'
    ).select_related('subject').order_by('-created_at')[:20]

    subjects = Subject.objects.filter(is_active=True)

    context = {
        'tests': tests,
        'subjects': subjects,
    }

    return render(request, 'tests_app/tests_list.html', context)


def test_detail(request, slug):
    """Test tafsilotlari"""
    test = get_object_or_404(Test, slug=slug, is_active=True)

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
    """Testni boshlash (eski)"""
    test = get_object_or_404(Test, slug=slug, is_active=True)

    # Mavjud tugallanmagan urinish bormi?
    existing = TestAttempt.objects.filter(
        user=request.user,
        test=test,
        status__in=['started', 'in_progress']
    ).first()

    if existing:
        return redirect('tests_app:test_play', uuid=existing.uuid)

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

    return redirect('tests_app:test_play', uuid=attempt.uuid)


@login_required
def quick_test(request):
    """Tezkor test sahifasi"""
    subjects = Subject.objects.filter(is_active=True).annotate(
        questions_count=Count('questions', filter=Q(questions__is_active=True))
    )

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

    # practice_start ga yo'naltirish
    request.POST = request.POST.copy()
    request.POST['mode'] = 'practice'

    return practice_start(request)


@login_required
def block_test(request):
    """Blok test sahifasi"""
    return redirect('tests_app:dtm_simulation')


@login_required
def block_test_start(request):
    """Blok testni boshlash"""
    return dtm_simulation_start(request)


def topic_test(request, subject_slug, topic_slug):
    """Mavzu bo'yicha test"""
    return redirect('tests_app:practice_topic', subject_slug=subject_slug, topic_slug=topic_slug)


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
        'total_correct': sum(a.correct_answers for a in attempts[:100]),
        'total_xp': sum(a.xp_earned for a in attempts[:100]),
    }

    # Paginator
    paginator = Paginator(attempts, 20)
    page = request.GET.get('page', 1)
    attempts_page = paginator.get_page(page)

    context = {
        'attempts': attempts_page,
        'stats': stats,
    }

    return render(request, 'tests_app/my_results.html', context)


@login_required
def result_detail(request, uuid):
    """Natija tafsilotlari"""
    return redirect('tests_app:test_play_result', uuid=uuid)


@login_required
def saved_questions(request):
    """Saqlangan savollar"""
    saved = SavedQuestion.objects.filter(
        user=request.user
    ).select_related('question', 'question__subject', 'question__topic').order_by('-created_at')

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
        'question', 'question__subject', 'question__topic', 'selected_answer'
    ).order_by('-answered_at')[:50]

    context = {
        'wrong_answers': wrong,
    }

    return render(request, 'tests_app/wrong_answers.html', context)


@login_required
def wrong_answers_practice(request):
    """Noto'g'ri javoblar ustida mashq"""
    wrong_question_ids = AttemptAnswer.objects.filter(
        attempt__user=request.user,
        is_correct=False
    ).values_list('question_id', flat=True).distinct()[:30]

    questions = list(Question.objects.filter(id__in=wrong_question_ids, is_active=True))

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
        shuffle_questions=False,
        shuffle_answers=True,
        show_correct_answers=True,
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

    return redirect('tests_app:test_play', uuid=attempt.uuid)


# ============================================================
# ESKI TEST VIEWLAR (eski URL lar uchun)
# ============================================================

@login_required
def test_question(request, uuid):
    """Eski test_question - yangi test_play ga redirect"""
    return redirect('tests_app:test_play', uuid=uuid)


@login_required
def test_submit_answer(request, uuid):
    """Eski submit - yangi API ga redirect"""
    return test_play_submit(request, uuid)


@login_required
def test_finish(request, uuid):
    """Eski finish - yangi ga redirect"""
    return redirect('tests_app:test_play_finish', uuid=uuid)


@login_required
def test_result(request, uuid):
    """Eski result - yangi ga redirect"""
    return redirect('tests_app:test_play_result', uuid=uuid)


@login_required
def api_test_progress(request, uuid):
    """Eski API - yangi ga redirect"""
    return api_test_status(request, uuid)