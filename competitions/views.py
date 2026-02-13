"""
TestMakon.uz - Competitions Views
Professional, production-ready competition system
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, F, Count, Avg, Sum
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.core.exceptions import PermissionDenied
from datetime import timedelta
import random
import json
import uuid as uuid_lib

from .models import (
    Competition, CompetitionParticipant, CompetitionPayment,
    Certificate, Battle, BattleInvitation, MatchmakingQueue,
    DailyChallenge, DailyChallengeParticipant,
    WeeklyLeague, WeeklyLeagueParticipant
)
from tests_app.models import Subject, Topic, Question, Answer, Test


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_user_stats(user):
    """Foydalanuvchi statistikasi"""
    stats = {
        'competitions_joined': CompetitionParticipant.objects.filter(user=user).count(),
        'competitions_won': CompetitionParticipant.objects.filter(user=user, rank=1).count(),
        'battles_won': Battle.objects.filter(winner=user).count(),
        'battles_total': Battle.objects.filter(
            Q(challenger=user) | Q(opponent=user),
            status='completed'
        ).count(),
        'total_xp_earned': CompetitionParticipant.objects.filter(user=user).aggregate(
            total=Coalesce(Sum('xp_earned'), 0)
        )['total'],
    }
    return stats


def generate_questions(subject=None, subjects=None, count=30, difficulty_dist=None):
    """
    Savollar generatsiya qilish

    Args:
        subject: Bitta fan (Subject instance)
        subjects: Ko'p fanlar (QuerySet)
        count: Jami savollar soni
        difficulty_dist: Qiyinlik taqsimoti {"easy": 30, "medium": 50, "hard": 20}

    Returns:
        list: Savollar data
    """
    questions_data = []

    # Default difficulty distribution
    if not difficulty_dist:
        difficulty_dist = {"easy": 30, "medium": 50, "hard": 20}

    # Fanlarni aniqlash
    if subjects and subjects.exists():
        # Ko'p fan - har biridan teng
        per_subject = count // subjects.count()
        remainder = count % subjects.count()

        for i, subj in enumerate(subjects):
            subj_count = per_subject + (1 if i < remainder else 0)
            subj_questions = get_questions_for_subject(subj, subj_count, difficulty_dist)
            questions_data.extend(subj_questions)
    elif subject:
        # Bitta fan
        questions_data = get_questions_for_subject(subject, count, difficulty_dist)
    else:
        # Barcha fanlardan
        all_questions = list(Question.objects.filter(is_active=True))
        random.shuffle(all_questions)
        selected = all_questions[:count]
        questions_data = format_questions(selected)

    return questions_data


def get_questions_for_subject(subject, count, difficulty_dist):
    """Bir fan uchun savollar"""
    questions = []

    # Qiyinlik bo'yicha taqsimlash
    total_percent = sum(difficulty_dist.values())

    for difficulty, percent in difficulty_dist.items():
        diff_count = int(count * percent / total_percent)
        diff_questions = list(
            Question.objects.filter(
                subject=subject,
                difficulty=difficulty,
                is_active=True
            )
        )
        random.shuffle(diff_questions)
        questions.extend(diff_questions[:diff_count])

    # Yetishmasa, qo'shimcha qo'shish
    if len(questions) < count:
        remaining = count - len(questions)
        existing_ids = [q.id for q in questions]
        extra = list(
            Question.objects.filter(
                subject=subject,
                is_active=True
            ).exclude(id__in=existing_ids)
        )
        random.shuffle(extra)
        questions.extend(extra[:remaining])

    random.shuffle(questions)
    return format_questions(questions[:count])


def format_questions(questions):
    """Savollarni JSON formatga o'tkazish"""
    data = []
    for q in questions:
        answers = list(q.answers.all().values('id', 'text', 'is_correct'))
        random.shuffle(answers)
        data.append({
            'id': q.id,
            'text': q.text,
            'image': q.image.url if q.image else None,
            'difficulty': q.difficulty,
            'subject_id': q.subject_id,
            'topic_id': q.topic_id,
            'answers': answers
        })
    return data


def calculate_score(answers_data, questions_data, xp_per_correct=10):
    """
    Natijani hisoblash

    Returns:
        dict: {score, correct, wrong, skipped, percentage, xp}
    """
    correct = 0
    wrong = 0
    skipped = 0

    answered_ids = {a['question_id']: a['answer_id'] for a in answers_data}

    for q in questions_data:
        q_id = q['id']
        if q_id not in answered_ids or answered_ids[q_id] is None:
            skipped += 1
            continue

        selected_id = answered_ids[q_id]
        correct_answer = next((a for a in q['answers'] if a['is_correct']), None)

        if correct_answer and correct_answer['id'] == selected_id:
            correct += 1
        else:
            wrong += 1

    total = len(questions_data)
    percentage = (correct / total * 100) if total > 0 else 0
    score = correct * xp_per_correct
    xp = correct * xp_per_correct

    return {
        'score': score,
        'correct': correct,
        'wrong': wrong,
        'skipped': skipped,
        'percentage': round(percentage, 2),
        'xp': xp,
        'total': total
    }


# ============================================================
# COMPETITION VIEWS
# ============================================================

def competitions_list(request):
    """Musobaqalar ro'yxati - bosh sahifa"""
    now = timezone.now()

    # Featured musobaqalar
    featured = Competition.objects.filter(
        is_active=True,
        is_featured=True,
        status__in=['upcoming', 'registration', 'active']
    ).order_by('start_time')[:3]

    # Faol musobaqalar
    active = Competition.objects.filter(
        status='active',
        is_active=True
    ).order_by('end_time')

    # Ro'yxatga olish ochiq
    registration_open = Competition.objects.filter(
        status__in=['upcoming', 'registration'],
        is_active=True,
        start_time__gt=now
    ).order_by('start_time')[:6]

    # Yaqinda tugagan
    finished = Competition.objects.filter(
        status='finished',
        is_active=True
    ).order_by('-end_time')[:6]

    # Kunlik challenge
    today = now.date()
    daily_challenge = DailyChallenge.objects.filter(date=today, is_active=True).first()
    daily_completed = False
    if daily_challenge and request.user.is_authenticated:
        daily_completed = DailyChallengeParticipant.objects.filter(
            challenge=daily_challenge,
            user=request.user
        ).exists()

    # User stats
    user_stats = None
    user_battles = None
    if request.user.is_authenticated:
        user_stats = get_user_stats(request.user)
        user_battles = Battle.objects.filter(
            Q(challenger=request.user) | Q(opponent=request.user),
            status__in=['pending', 'accepted', 'in_progress']
        ).select_related('challenger', 'opponent', 'subject')[:5]

    context = {
        'featured': featured,
        'active': active,
        'registration_open': registration_open,
        'finished': finished,
        'daily_challenge': daily_challenge,
        'daily_completed': daily_completed,
        'user_stats': user_stats,
        'user_battles': user_battles,
    }
    return render(request, 'competitions/competitions_list.html', context)


def competition_detail(request, slug):
    """Musobaqa tafsilotlari"""
    competition = get_object_or_404(
        Competition.objects.select_related('subject', 'test', 'created_by'),
        slug=slug,
        is_active=True
    )

    now = timezone.now()
    is_participant = False
    participant = None
    can_join = False
    can_start = False

    if request.user.is_authenticated:
        participant = CompetitionParticipant.objects.filter(
            competition=competition,
            user=request.user
        ).first()
        is_participant = participant is not None

        # Qo'shilish mumkinmi?
        can_join = (
                not is_participant and
                competition.status in ['upcoming', 'registration', 'active'] and
                (not competition.max_participants or competition.participants_count < competition.max_participants) and
                (competition.entry_type != 'premium_only' or request.user.is_premium)
        )

        # Boshlash mumkinmi?
        can_start = (
                is_participant and
                participant.status in ['registered', 'ready'] and
                competition.status == 'active' and
                competition.start_time <= now <= competition.end_time
        )

    # Top 10 leaderboard
    leaderboard = CompetitionParticipant.objects.filter(
        competition=competition,
        status='completed'
    ).select_related('user').order_by('rank')[:10]

    # Qatnashchilar soni
    participants_count = competition.participants_count

    # Vaqt hisoblash
    time_info = {}
    if competition.status == 'upcoming' and competition.start_time > now:
        delta = competition.start_time - now
        time_info = {
            'type': 'until_start',
            'days': delta.days,
            'hours': delta.seconds // 3600,
            'minutes': (delta.seconds % 3600) // 60
        }
    elif competition.status == 'active' and competition.end_time > now:
        delta = competition.end_time - now
        time_info = {
            'type': 'until_end',
            'days': delta.days,
            'hours': delta.seconds // 3600,
            'minutes': (delta.seconds % 3600) // 60
        }

    context = {
        'competition': competition,
        'is_participant': is_participant,
        'participant': participant,
        'can_join': can_join,
        'can_start': can_start,
        'leaderboard': leaderboard,
        'participants_count': participants_count,
        'time_info': time_info,
    }
    return render(request, 'competitions/competition_detail.html', context)


@login_required
def competition_join(request, slug):
    """Musobaqaga qo'shilish"""
    competition = get_object_or_404(
        Competition,
        slug=slug,
        is_active=True,
        status__in=['upcoming', 'registration', 'active']
    )

    # Allaqachon qatnashchimi?
    if CompetitionParticipant.objects.filter(competition=competition, user=request.user).exists():
        messages.info(request, "Siz allaqachon ro'yxatdan o'tgansiz!")
        return redirect('competitions:competition_detail', slug=slug)

    # Max qatnashchilar tekshirish
    if competition.max_participants and competition.participants_count >= competition.max_participants:
        messages.error(request, "Afsuski, joylar tugagan!")
        return redirect('competitions:competition_detail', slug=slug)

    # Premium tekshirish
    if competition.entry_type == 'premium_only' and not request.user.is_premium:
        messages.error(request, "Bu musobaqa faqat Premium foydalanuvchilar uchun!")
        return redirect('competitions:competition_detail', slug=slug)

    # Daraja tekshirish
    user_level = getattr(request.user, 'level', 1)
    if competition.min_level and user_level < competition.min_level:
        messages.error(request, f"Kamida {competition.min_level}-darajaga yetishingiz kerak!")
        return redirect('competitions:competition_detail', slug=slug)

    # Pullik musobaqa
    if competition.entry_type == 'paid' and competition.entry_fee > 0:
        # To'lov sahifasiga yo'naltirish
        return redirect('competitions:competition_payment', slug=slug)

    # Ro'yxatdan o'tkazish
    with transaction.atomic():
        participant = CompetitionParticipant.objects.create(
            competition=competition,
            user=request.user,
            status='registered'
        )
        competition.participants_count = F('participants_count') + 1
        competition.save(update_fields=['participants_count'])

    messages.success(request, "Musobaqaga muvaffaqiyatli ro'yxatdan o'tdingiz!")
    return redirect('competitions:competition_detail', slug=slug)


@login_required
def competition_payment(request, slug):
    """Pullik musobaqa uchun to'lov"""
    competition = get_object_or_404(
        Competition,
        slug=slug,
        is_active=True,
        entry_type='paid'
    )

    if request.method == 'POST':
        # To'lov integratsiyasi (Payme, Click, etc.)
        # Hozircha simulyatsiya

        with transaction.atomic():
            participant, created = CompetitionParticipant.objects.get_or_create(
                competition=competition,
                user=request.user,
                defaults={'status': 'registered'}
            )

            if created:
                competition.participants_count = F('participants_count') + 1
                competition.save(update_fields=['participants_count'])

            # To'lov yozuvi
            CompetitionPayment.objects.create(
                participant=participant,
                amount=competition.entry_fee,
                status='completed',
                payment_method='test',
                paid_at=timezone.now()
            )

        messages.success(request, "To'lov muvaffaqiyatli! Musobaqaga qo'shildingiz.")
        return redirect('competitions:competition_detail', slug=slug)

    context = {
        'competition': competition,
    }
    return render(request, 'competitions/competition_payment.html', context)


@login_required
def competition_start(request, slug):
    """Musobaqani boshlash"""
    competition = get_object_or_404(
        Competition,
        slug=slug,
        status='active',
        is_active=True
    )

    participant = get_object_or_404(
        CompetitionParticipant,
        competition=competition,
        user=request.user
    )

    now = timezone.now()

    # Vaqt tekshirish
    if now < competition.start_time:
        messages.error(request, "Musobaqa hali boshlanmagan!")
        return redirect('competitions:competition_detail', slug=slug)

    if now > competition.end_time:
        messages.error(request, "Musobaqa tugagan!")
        return redirect('competitions:competition_detail', slug=slug)

    # Allaqachon yakunlaganmi?
    if participant.status == 'completed':
        messages.info(request, "Siz allaqachon ishtirok etgansiz!")
        return redirect('competitions:competition_result', slug=slug)

    # Diskvalifikatsiya qilinganmi?
    if participant.status == 'disqualified':
        messages.error(request, "Siz diskvalifikatsiya qilingansiz!")
        return redirect('competitions:competition_detail', slug=slug)

    # Test mavjudmi yoki savollar generatsiya qilish kerakmi?
    if competition.test:
        # Tayyor test mavjud
        return redirect('tests_app:test_play', uuid=competition.test.uuid)

    # Savollar generatsiya qilish (session'da saqlash)
    if 'competition_questions' not in request.session or request.session.get('competition_id') != competition.id:
        if competition.test_format == 'dtm_block' and competition.subjects.exists():
            questions_data = generate_questions(
                subjects=competition.subjects.all(),
                count=competition.total_questions,
                difficulty_dist=competition.difficulty_distribution or None
            )
        elif competition.subject:
            questions_data = generate_questions(
                subject=competition.subject,
                count=competition.total_questions,
                difficulty_dist=competition.difficulty_distribution or None
            )
        else:
            questions_data = generate_questions(
                count=competition.total_questions,
                difficulty_dist=competition.difficulty_distribution or None
            )

        request.session['competition_questions'] = questions_data
        request.session['competition_id'] = competition.id
        request.session['competition_start_time'] = now.isoformat()

    # Participant statusini yangilash
    if participant.status in ['registered', 'ready']:
        participant.status = 'in_progress'
        participant.started_at = now
        participant.save(update_fields=['status', 'started_at'])

    return redirect('competitions:competition_play', slug=slug)


@login_required
def competition_play(request, slug):
    """Musobaqa o'yini"""
    competition = get_object_or_404(
        Competition,
        slug=slug,
        status='active',
        is_active=True
    )

    participant = get_object_or_404(
        CompetitionParticipant,
        competition=competition,
        user=request.user,
        status='in_progress'
    )

    # Session'dan savollarni olish
    questions_data = request.session.get('competition_questions', [])
    if not questions_data:
        messages.error(request, "Xatolik yuz berdi. Qaytadan boshlang.")
        return redirect('competitions:competition_start', slug=slug)

    # Vaqt hisoblash
    now = timezone.now()
    start_time_str = request.session.get('competition_start_time')
    if start_time_str:
        from datetime import datetime
        start_time = datetime.fromisoformat(start_time_str)
        if timezone.is_naive(start_time):
            start_time = timezone.make_aware(start_time)
        elapsed = (now - start_time).total_seconds()
    else:
        elapsed = 0

    total_time = competition.duration_minutes * 60
    remaining_time = max(0, total_time - elapsed)

    # Vaqt tugadimi?
    if remaining_time <= 0:
        return redirect('competitions:competition_submit', slug=slug)

    context = {
        'competition': competition,
        'participant': participant,
        'questions_data': questions_data,
        'remaining_time': int(remaining_time),
        'total_questions': len(questions_data),
        'anti_cheat': competition.anti_cheat_enabled,
    }
    return render(request, 'competitions/competition_play.html', context)


@login_required
@require_POST
def competition_submit(request, slug):
    """Musobaqa javoblarini yuborish"""
    competition = get_object_or_404(Competition, slug=slug)

    participant = get_object_or_404(
        CompetitionParticipant,
        competition=competition,
        user=request.user
    )

    if participant.status == 'completed':
        return redirect('competitions:competition_result', slug=slug)

    # Javoblarni olish
    try:
        answers_data = json.loads(request.POST.get('answers', '[]'))
    except json.JSONDecodeError:
        answers_data = []

    time_spent = int(request.POST.get('time_spent', 0))

    # Session'dan savollarni olish
    questions_data = request.session.get('competition_questions', [])

    # Natijani hisoblash
    result = calculate_score(
        answers_data,
        questions_data,
        xp_per_correct=competition.xp_per_correct
    )

    # Participant yangilash
    with transaction.atomic():
        participant.score = result['score']
        participant.percentage = result['percentage']
        participant.correct_answers = result['correct']
        participant.wrong_answers = result['wrong']
        participant.skipped_answers = result['skipped']
        participant.time_spent = time_spent
        participant.answers_data = answers_data
        participant.status = 'completed'
        participant.completed_at = timezone.now()
        participant.save()

        # Competition statsni yangilash
        competition.completed_count = F('completed_count') + 1
        competition.save(update_fields=['completed_count'])

    # Session tozalash
    request.session.pop('competition_questions', None)
    request.session.pop('competition_id', None)
    request.session.pop('competition_start_time', None)

    return redirect('competitions:competition_result', slug=slug)


@login_required
def competition_result(request, slug):
    """Musobaqa natijasi"""
    competition = get_object_or_404(Competition, slug=slug)

    participant = get_object_or_404(
        CompetitionParticipant,
        competition=competition,
        user=request.user
    )

    # Rank hisoblash (hali hisoblanmagan bo'lsa)
    if participant.rank is None and participant.status == 'completed':
        rank = CompetitionParticipant.objects.filter(
            competition=competition,
            status='completed',
            score__gt=participant.score
        ).count() + 1

        # Teng ballda vaqt bo'yicha
        same_score_better_time = CompetitionParticipant.objects.filter(
            competition=competition,
            status='completed',
            score=participant.score,
            time_spent__lt=participant.time_spent
        ).count()

        rank += same_score_better_time
        participant.rank = rank
        participant.save(update_fields=['rank'])

    # Leaderboard
    leaderboard = CompetitionParticipant.objects.filter(
        competition=competition,
        status='completed'
    ).select_related('user').order_by('-score', 'time_spent')[:20]

    # User rank in leaderboard
    user_rank_in_list = None
    for i, p in enumerate(leaderboard):
        if p.user_id == request.user.id:
            user_rank_in_list = i + 1
            break

    context = {
        'competition': competition,
        'participant': participant,
        'leaderboard': leaderboard,
        'user_rank_in_list': user_rank_in_list,
    }
    return render(request, 'competitions/competition_result.html', context)


def competition_leaderboard(request, slug):
    """Musobaqa to'liq reytingi"""
    competition = get_object_or_404(Competition, slug=slug)

    participants = CompetitionParticipant.objects.filter(
        competition=competition,
        status='completed'
    ).select_related('user').order_by('-score', 'time_spent')

    # Pagination
    paginator = Paginator(participants, 50)
    page = request.GET.get('page', 1)
    participants_page = paginator.get_page(page)

    # User position
    user_participant = None
    if request.user.is_authenticated:
        user_participant = CompetitionParticipant.objects.filter(
            competition=competition,
            user=request.user
        ).first()

    context = {
        'competition': competition,
        'participants': participants_page,
        'user_participant': user_participant,
    }
    return render(request, 'competitions/competition_leaderboard.html', context)


# ============================================================
# BATTLE VIEWS
# ============================================================

@login_required
def battles_list(request):
    """Janglar ro'yxati"""
    user = request.user

    # Kutilayotgan takliflar (menga kelgan)
    pending_received = Battle.objects.filter(
        opponent=user,
        status='pending'
    ).select_related('challenger', 'subject').order_by('-created_at')

    # Mening yuborgan takliflarim
    pending_sent = Battle.objects.filter(
        challenger=user,
        status='pending'
    ).select_related('opponent', 'subject').order_by('-created_at')

    # Faol janglar
    active = Battle.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status__in=['accepted', 'in_progress']
    ).select_related('challenger', 'opponent', 'subject').order_by('-created_at')

    # Yakunlangan janglar
    completed = Battle.objects.filter(
        Q(challenger=user) | Q(opponent=user),
        status='completed'
    ).select_related('challenger', 'opponent', 'winner', 'subject').order_by('-completed_at')[:20]

    # Do'stlar (battle uchun)
    friends = get_user_friends(user)

    # User battle stats
    stats = {
        'total': Battle.objects.filter(
            Q(challenger=user) | Q(opponent=user),
            status='completed'
        ).count(),
        'won': Battle.objects.filter(winner=user).count(),
        'lost': Battle.objects.filter(
            Q(challenger=user) | Q(opponent=user),
            status='completed'
        ).exclude(winner=user).exclude(is_draw=True).exclude(winner__isnull=True).count(),
        'draw': Battle.objects.filter(
            Q(challenger=user) | Q(opponent=user),
            status='completed',
            is_draw=True
        ).count(),
    }

    context = {
        'pending_received': pending_received,
        'pending_sent': pending_sent,
        'active': active,
        'completed': completed,
        'friends': friends,
        'stats': stats,
    }
    return render(request, 'competitions/battles_list.html', context)


def get_user_friends(user):
    """Foydalanuvchi do'stlarini olish"""
    try:
        from accounts.models import Friendship
        friendships = Friendship.objects.filter(
            Q(from_user=user) | Q(to_user=user),
            status='accepted'
        ).select_related('from_user', 'to_user')

        friends = []
        for f in friendships:
            friend = f.to_user if f.from_user == user else f.from_user
            friends.append(friend)
        return friends
    except ImportError:
        return []

@login_required
def battle_create(request):
    """Yangi jang yaratish"""
    if request.method == 'POST':
        opponent_type = request.POST.get('opponent_type', 'friend')
        opponent_id = request.POST.get('opponent_id')
        subject_id = request.POST.get('subject_id')
        question_count = int(request.POST.get('question_count', 10))
        bot_difficulty = request.POST.get('bot_difficulty', 'medium')

        subject = None
        if subject_id:
            subject = Subject.objects.filter(id=subject_id, is_active=True).first()

        opponent = None
        if opponent_type == 'friend' and opponent_id:
            from accounts.models import User
            opponent = User.objects.filter(id=opponent_id).first()
            if not opponent:
                messages.error(request, "Raqib topilmadi!")
                return redirect('competitions:battle_create')
        elif opponent_type == 'random':
            # Matchmaking queue'ga qo'shish
            # FIX: Agar fan tanlangan bo'lsa _subject URL ga, bo'lmasa oddiy URL ga yo'naltiramiz
            if subject_id:
                return redirect('competitions:battle_matchmaking_subject', subject_id=subject_id)
            else:
                return redirect('competitions:battle_matchmaking')

        # Savollarni generatsiya qilish
        questions_data = generate_questions(
            subject=subject,
            count=question_count
        )

        if len(questions_data) < question_count:
            messages.error(request, f"Yetarli savol topilmadi! ({len(questions_data)}/{question_count})")
            return redirect('competitions:battle_create')

        # Battle yaratish
        battle = Battle.objects.create(
            challenger=request.user,
            opponent=opponent,
            opponent_type=opponent_type,
            bot_difficulty=bot_difficulty if opponent_type == 'bot' else '',
            subject=subject,
            question_count=question_count,
            questions_data=questions_data,
            total_time=question_count * 30,  # 30 sekund per savol
            expires_at=timezone.now() + timedelta(hours=24)
        )

        # Bot bilan jang - darhol boshlash
        if opponent_type == 'bot':
            battle.status = 'accepted'
            battle.accepted_at = timezone.now()
            battle.save()
            messages.success(request, f"Bot ({battle.get_bot_difficulty_display()}) bilan jang boshlandi!")
            return redirect('competitions:battle_play', uuid=battle.uuid)

        messages.success(request, "Jang taklifi yuborildi!")
        return redirect('competitions:battle_detail', uuid=battle.uuid)

    # GET - forma ko'rsatish
    subjects = Subject.objects.filter(is_active=True)
    friends = get_user_friends(request.user)

    context = {
        'subjects': subjects,
        'friends': friends,
    }
    return render(request, 'competitions/battle_create.html', context)


@login_required
def battle_matchmaking(request, subject_id=None):
    """Random raqib topish"""
    subject = None
    if subject_id and subject_id != 0:
        subject = Subject.objects.filter(id=subject_id).first()

    user = request.user
    user_rating = getattr(user, 'rating', 1000)
    user_level = getattr(user, 'level', 1)

    # Avvalgi queue'ni o'chirish
    MatchmakingQueue.objects.filter(user=user).delete()

    # Mos raqib qidirish
    potential_match = MatchmakingQueue.objects.filter(
        is_matched=False,
        expires_at__gt=timezone.now(),
        user_rating__gte=user_rating - 200,
        user_rating__lte=user_rating + 200,
    ).exclude(user=user)

    if subject:
        potential_match = potential_match.filter(
            Q(subject=subject) | Q(subject__isnull=True)
        )

    match = potential_match.order_by('joined_at').first()

    if match:
        # Match topildi!
        questions_data = generate_questions(
            subject=subject or match.subject,
            count=match.question_count
        )

        battle = Battle.objects.create(
            challenger=match.user,
            opponent=user,
            opponent_type='random',
            subject=subject or match.subject,
            question_count=match.question_count,
            questions_data=questions_data,
            total_time=match.question_count * 30,
            status='accepted',
            accepted_at=timezone.now(),
            expires_at=timezone.now() + timedelta(hours=1)
        )

        # Queue yangilash
        match.is_matched = True
        match.matched_with = user
        match.battle = battle
        match.save()

        messages.success(request, f"Raqib topildi: {match.user.first_name}!")
        return redirect('competitions:battle_play', uuid=battle.uuid)

    # Queue'ga qo'shish
    queue_entry = MatchmakingQueue.objects.create(
        user=user,
        subject=subject,
        user_rating=user_rating,
        user_level=user_level,
        question_count=10,
        expires_at=timezone.now() + timedelta(minutes=5)
    )

    context = {
        'queue_entry': queue_entry,
        'subject': subject,
    }
    return render(request, 'competitions/battle_matchmaking.html', context)


@login_required
def battle_detail(request, uuid):
    """Jang tafsilotlari"""
    battle = get_object_or_404(Battle, uuid=uuid)

    # Faqat qatnashchilar ko'rishi mumkin
    if request.user not in [battle.challenger, battle.opponent] and battle.opponent is not None:
        messages.error(request, "Bu jangni ko'rish huquqingiz yo'q!")
        return redirect('competitions:battles_list')

    is_challenger = request.user == battle.challenger
    is_opponent = request.user == battle.opponent

    can_accept = is_opponent and battle.status == 'pending'
    can_play = battle.status in ['accepted', 'in_progress']

    # O'z navbatini kutayotganmi?
    waiting_for_opponent = False
    if battle.status in ['accepted', 'in_progress']:
        if is_challenger and battle.challenger_completed and not battle.opponent_completed:
            waiting_for_opponent = True
        elif is_opponent and battle.opponent_completed and not battle.challenger_completed:
            waiting_for_opponent = True

    context = {
        'battle': battle,
        'is_challenger': is_challenger,
        'is_opponent': is_opponent,
        'can_accept': can_accept,
        'can_play': can_play,
        'waiting_for_opponent': waiting_for_opponent,
    }
    return render(request, 'competitions/battle_detail.html', context)


@login_required
@require_POST
def battle_accept(request, uuid):
    """Jangni qabul qilish"""
    battle = get_object_or_404(
        Battle,
        uuid=uuid,
        opponent=request.user,
        status='pending'
    )

    # Muddati o'tganmi?
    if timezone.now() > battle.expires_at:
        battle.status = 'expired'
        battle.save()
        messages.error(request, "Taklif muddati o'tgan!")
        return redirect('competitions:battles_list')

    battle.status = 'accepted'
    battle.accepted_at = timezone.now()
    battle.save()

    messages.success(request, "Jang qabul qilindi! Boshlashingiz mumkin.")
    return redirect('competitions:battle_detail', uuid=uuid)


@login_required
@require_POST
def battle_reject(request, uuid):
    """Jangni rad etish"""
    battle = get_object_or_404(
        Battle,
        uuid=uuid,
        opponent=request.user,
        status='pending'
    )

    battle.status = 'rejected'
    battle.save()

    messages.info(request, "Jang rad etildi.")
    return redirect('competitions:battles_list')


@login_required
def battle_play(request, uuid):
    """Jang o'yini"""
    battle = get_object_or_404(Battle, uuid=uuid)

    # Tekshirishlar
    is_challenger = request.user == battle.challenger
    is_opponent = request.user == battle.opponent

    if not is_challenger and not is_opponent and battle.opponent_type != 'bot':
        messages.error(request, "Bu jangda qatnashmaysiz!")
        return redirect('competitions:battles_list')

    if battle.status not in ['accepted', 'in_progress']:
        return redirect('competitions:battle_detail', uuid=uuid)

    # Allaqachon yakunlaganmi?
    if is_challenger and battle.challenger_completed:
        if battle.opponent_type == 'bot' or battle.opponent_completed:
            return redirect('competitions:battle_result', uuid=uuid)
        messages.info(request, "Raqibingiz tugashini kuting.")
        return redirect('competitions:battle_detail', uuid=uuid)

    if is_opponent and battle.opponent_completed:
        if battle.challenger_completed:
            return redirect('competitions:battle_result', uuid=uuid)
        messages.info(request, "Raqibingiz tugashini kuting.")
        return redirect('competitions:battle_detail', uuid=uuid)

    # Status yangilash
    if battle.status == 'accepted':
        battle.status = 'in_progress'
        battle.started_at = timezone.now()
        battle.save()

    context = {
        'battle': battle,
        'questions': battle.questions_data,
        'is_challenger': is_challenger,
        'total_time': battle.total_time,
    }
    return render(request, 'competitions/battle_play.html', context)


@login_required
@require_POST
def battle_submit(request, uuid):
    """Jang javoblarini yuborish"""
    battle = get_object_or_404(Battle, uuid=uuid)

    is_challenger = request.user == battle.challenger

    # Javoblarni olish
    try:
        answers = json.loads(request.POST.get('answers', '[]'))
    except json.JSONDecodeError:
        answers = []

    time_spent = int(request.POST.get('time_spent', 0))

    # Natijani hisoblash
    correct = 0
    for ans in answers:
        q_data = next((q for q in battle.questions_data if q['id'] == ans.get('question_id')), None)
        if q_data:
            correct_answer = next((a for a in q_data['answers'] if a['is_correct']), None)
            if correct_answer and correct_answer['id'] == ans.get('answer_id'):
                correct += 1

    # Natijani saqlash
    with transaction.atomic():
        battle = Battle.objects.select_for_update().get(uuid=uuid)

        if is_challenger:
            battle.challenger_answers = answers
            battle.challenger_correct = correct
            battle.challenger_time = time_spent
            battle.challenger_score = correct * 10
            battle.challenger_completed = True
        else:
            battle.opponent_answers = answers
            battle.opponent_correct = correct
            battle.opponent_time = time_spent
            battle.opponent_score = correct * 10
            battle.opponent_completed = True

        battle.save()

        # Ikkalasi ham tugadimi?
        if battle.challenger_completed and (battle.opponent_completed or battle.opponent_type == 'bot'):
            battle.determine_winner()

    return redirect('competitions:battle_result', uuid=uuid)


@login_required
def battle_result(request, uuid):
    """Jang natijasi"""
    battle = get_object_or_404(Battle, uuid=uuid)

    is_challenger = request.user == battle.challenger

    # Bot natijasini hisoblash (agar hali hisoblanmagan bo'lsa)
    if battle.opponent_type == 'bot' and not battle.opponent_completed and battle.challenger_completed:
        battle.determine_winner()
        battle.refresh_from_db()

    # Natija hali tayyor emas
    if battle.status != 'completed':
        if is_challenger and battle.challenger_completed:
            messages.info(request, "Raqibingiz tugashini kuting...")
        return redirect('competitions:battle_detail', uuid=uuid)

    # User natijasi
    if is_challenger:
        user_correct = battle.challenger_correct
        user_time = battle.challenger_time
        opponent_correct = battle.opponent_correct
        opponent_time = battle.opponent_time
    else:
        user_correct = battle.opponent_correct
        user_time = battle.opponent_time
        opponent_correct = battle.challenger_correct
        opponent_time = battle.challenger_time

    # User yutdimi?
    user_won = battle.winner == request.user
    user_lost = not battle.is_draw and not user_won and battle.winner is not None

    context = {
        'battle': battle,
        'is_challenger': is_challenger,
        'user_correct': user_correct,
        'user_time': user_time,
        'opponent_correct': opponent_correct,
        'opponent_time': opponent_time,
        'user_won': user_won,
        'user_lost': user_lost,
        'is_draw': battle.is_draw,
        'total_questions': len(battle.questions_data),
    }
    return render(request, 'competitions/battle_result.html', context)


# ============================================================
# DAILY CHALLENGE VIEWS
# ============================================================

@login_required
def daily_challenge(request):
    """Kunlik challenge"""
    today = timezone.now().date()

    challenge = DailyChallenge.objects.filter(date=today, is_active=True).first()

    if not challenge:
        context = {'challenge': None}
        return render(request, 'competitions/daily_challenge.html', context)

    # User qatnashganmi?
    participant = DailyChallengeParticipant.objects.filter(
        challenge=challenge,
        user=request.user
    ).first()

    # Top 10 leaderboard
    leaderboard = DailyChallengeParticipant.objects.filter(
        challenge=challenge
    ).select_related('user').order_by('-score', 'time_spent')[:10]

    context = {
        'challenge': challenge,
        'participant': participant,
        'leaderboard': leaderboard,
        'completed': participant is not None,
    }
    return render(request, 'competitions/daily_challenge.html', context)


@login_required
def daily_challenge_start(request):
    """Kunlik challengeni boshlash"""
    today = timezone.now().date()

    challenge = get_object_or_404(DailyChallenge, date=today, is_active=True)

    # Allaqachon qatnashganmi?
    if DailyChallengeParticipant.objects.filter(challenge=challenge, user=request.user).exists():
        messages.info(request, "Siz bugun allaqachon ishtirok etgansiz!")
        return redirect('competitions:daily_challenge')

    # Savollarni session'ga saqlash
    questions = list(challenge.questions.all())
    questions_data = format_questions(questions)

    request.session['daily_challenge_questions'] = questions_data
    request.session['daily_challenge_id'] = challenge.id
    request.session['daily_challenge_start'] = timezone.now().isoformat()

    return redirect('competitions:daily_challenge_play')


@login_required
def daily_challenge_play(request):
    """Kunlik challenge o'yini"""
    questions_data = request.session.get('daily_challenge_questions', [])
    challenge_id = request.session.get('daily_challenge_id')

    if not questions_data or not challenge_id:
        return redirect('competitions:daily_challenge')

    challenge = get_object_or_404(DailyChallenge, id=challenge_id)

    # Vaqt
    start_str = request.session.get('daily_challenge_start')
    elapsed = 0
    if start_str:
        from datetime import datetime
        start = datetime.fromisoformat(start_str)
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        elapsed = (timezone.now() - start).total_seconds()

    remaining = max(0, challenge.time_limit * 60 - elapsed)

    context = {
        'challenge': challenge,
        'questions_data': questions_data,
        'remaining_time': int(remaining),
    }
    return render(request, 'competitions/daily_challenge_play.html', context)


@login_required
@require_POST
def daily_challenge_submit(request):
    """Kunlik challenge javoblarini yuborish"""
    challenge_id = request.session.get('daily_challenge_id')
    questions_data = request.session.get('daily_challenge_questions', [])

    if not challenge_id:
        return redirect('competitions:daily_challenge')

    challenge = get_object_or_404(DailyChallenge, id=challenge_id)

    # Allaqachon qatnashganmi?
    if DailyChallengeParticipant.objects.filter(challenge=challenge, user=request.user).exists():
        return redirect('competitions:daily_challenge')

    # Javoblar
    try:
        answers = json.loads(request.POST.get('answers', '[]'))
    except json.JSONDecodeError:
        answers = []

    time_spent = int(request.POST.get('time_spent', 0))

    # Natija
    result = calculate_score(answers, questions_data)

    # XP hisoblash
    xp = challenge.xp_reward if result['correct'] >= len(questions_data) // 2 else challenge.xp_reward // 2

    # Saqlash
    with transaction.atomic():
        participant = DailyChallengeParticipant.objects.create(
            challenge=challenge,
            user=request.user,
            score=result['score'],
            percentage=result['percentage'],
            correct_answers=result['correct'],
            wrong_answers=result['wrong'],
            time_spent=time_spent,
            xp_earned=xp,
            answers_data=answers
        )

        # Challenge stats
        challenge.participants_count = F('participants_count') + 1
        challenge.save()

        # User XP
        request.user.xp_points = F('xp_points') + xp
        request.user.save(update_fields=['xp_points'])

    # Session tozalash
    request.session.pop('daily_challenge_questions', None)
    request.session.pop('daily_challenge_id', None)
    request.session.pop('daily_challenge_start', None)

    return redirect('competitions:daily_challenge')


# ============================================================
# WEEKLY LEAGUE VIEWS
# ============================================================

@login_required
def weekly_league(request):
    """Haftalik liga"""
    today = timezone.now().date()

    # Joriy hafta ligasi
    current_league = WeeklyLeague.objects.filter(
        week_start__lte=today,
        week_end__gte=today,
        is_active=True
    ).first()

    user_participation = None
    leaderboard = []

    if current_league:
        user_participation = WeeklyLeagueParticipant.objects.filter(
            league=current_league,
            user=request.user
        ).first()

        leaderboard = WeeklyLeagueParticipant.objects.filter(
            league=current_league
        ).select_related('user').order_by('-xp_earned')[:20]

    # O'tgan haftalar
    past_leagues = WeeklyLeague.objects.filter(
        week_end__lt=today,
        is_processed=True
    ).order_by('-week_start')[:4]

    context = {
        'current_league': current_league,
        'user_participation': user_participation,
        'leaderboard': leaderboard,
        'past_leagues': past_leagues,
    }
    return render(request, 'competitions/weekly_league.html', context)


# ============================================================
# CERTIFICATE VIEWS
# ============================================================

@login_required
def my_certificates(request):
    """Mening sertifikatlarim"""
    certificates = Certificate.objects.filter(
        user=request.user
    ).select_related('competition').order_by('-issued_at')

    context = {
        'certificates': certificates,
    }
    return render(request, 'competitions/my_certificates.html', context)


def verify_certificate(request, code):
    """Sertifikatni tekshirish"""
    certificate = get_object_or_404(Certificate, verification_code=code)

    context = {
        'certificate': certificate,
    }
    return render(request, 'competitions/verify_certificate.html', context)


# ============================================================
# API VIEWS
# ============================================================

@login_required
@require_GET
def api_battle_status(request, uuid):
    """Jang holati API"""
    battle = get_object_or_404(Battle, uuid=uuid)

    data = {
        'status': battle.status,
        'challenger_completed': battle.challenger_completed,
        'opponent_completed': battle.opponent_completed,
        'winner_id': battle.winner.id if battle.winner else None,
        'winner_is_bot': battle.winner_is_bot,
        'is_draw': battle.is_draw,
    }
    return JsonResponse(data)


@login_required
@require_GET
def api_matchmaking_status(request):
    """Matchmaking holati API"""
    queue_entry = MatchmakingQueue.objects.filter(user=request.user).first()

    if not queue_entry:
        return JsonResponse({'status': 'not_in_queue'})

    if queue_entry.is_matched and queue_entry.battle:
        return JsonResponse({
            'status': 'matched',
            'battle_uuid': str(queue_entry.battle.uuid),
            'opponent_name': queue_entry.matched_with.first_name if queue_entry.matched_with else None
        })

    # Muddati o'tdimi?
    if timezone.now() > queue_entry.expires_at:
        queue_entry.delete()
        return JsonResponse({'status': 'expired'})

    return JsonResponse({
        'status': 'searching',
        'seconds_remaining': int((queue_entry.expires_at - timezone.now()).total_seconds())
    })


@login_required
@require_POST
def api_matchmaking_cancel(request):
    """Matchmaking bekor qilish"""
    MatchmakingQueue.objects.filter(user=request.user).delete()
    return JsonResponse({'status': 'cancelled'})


@login_required
@require_POST
def api_log_violation(request):
    """Anti-cheat violation log"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    competition_id = data.get('competition_id')
    violation_type = data.get('type')
    details = data.get('details')

    if competition_id:
        participant = CompetitionParticipant.objects.filter(
            competition_id=competition_id,
            user=request.user
        ).first()

        if participant:
            participant.add_violation(violation_type, details)
            return JsonResponse({
                'status': 'logged',
                'violations_count': participant.violations_count,
                'disqualified': participant.status == 'disqualified'
            })

    return JsonResponse({'status': 'ignored'})


@login_required
@require_GET
def api_leaderboard(request, slug):
    """Live leaderboard API"""
    competition = get_object_or_404(Competition, slug=slug)

    participants = CompetitionParticipant.objects.filter(
        competition=competition,
        status='completed'
    ).select_related('user').order_by('-score', 'time_spent')[:50]

    data = []
    for i, p in enumerate(participants, 1):
        data.append({
            'rank': i,
            'user_id': p.user.id,
            'name': p.user.full_name,
            'avatar': p.user.get_avatar_url() if hasattr(p.user, 'get_avatar_url') else None,
            'score': p.score,
            'correct': p.correct_answers,
            'time': p.time_spent,
        })

    return JsonResponse({'leaderboard': data})


@login_required
@require_GET
def api_online_friends(request):
    """Online do'stlar API"""
    friends = get_user_friends(request.user)

    data = []
    for friend in friends:
        # Online status check (simplified)
        is_online = False
        if hasattr(friend, 'last_activity'):
            is_online = (timezone.now() - friend.last_activity).total_seconds() < 300

        data.append({
            'id': friend.id,
            'name': friend.full_name if hasattr(friend, 'full_name') else friend.first_name,
            'avatar': friend.get_avatar_url() if hasattr(friend, 'get_avatar_url') else None,
            'is_online': is_online,
        })

    return JsonResponse({'friends': data})