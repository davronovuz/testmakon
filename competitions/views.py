"""
TestMakon.uz - Competitions Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta
import random
import json

from .models import (
    Competition, CompetitionParticipant, Battle,
    DailyChallenge, DailyChallengeParticipant
)
from tests_app.models import Subject, Question
from accounts.models import User, Friendship


def competitions_list(request):
    """Musobaqalar ro'yxati"""
    active = Competition.objects.filter(status='active', is_active=True).order_by('end_time')
    upcoming = Competition.objects.filter(status='upcoming', is_active=True).order_by('start_time')[:5]
    finished = Competition.objects.filter(status='finished', is_active=True).order_by('-end_time')[:10]

    context = {
        'active': active,
        'upcoming': upcoming,
        'finished': finished,
    }
    return render(request, 'competitions/competitions_list.html', context)


def competition_detail(request, slug):
    """Musobaqa tafsilotlari"""
    competition = get_object_or_404(Competition, slug=slug)

    is_participant = False
    participant = None

    if request.user.is_authenticated:
        participant = CompetitionParticipant.objects.filter(
            competition=competition, user=request.user
        ).first()
        is_participant = participant is not None

    top_participants = CompetitionParticipant.objects.filter(
        competition=competition, is_completed=True
    ).order_by('rank')[:10]

    context = {
        'competition': competition,
        'is_participant': is_participant,
        'participant': participant,
        'top_participants': top_participants,
    }
    return render(request, 'competitions/competition_detail.html', context)


@login_required
def competition_join(request, slug):
    """Musobaqaga qo'shilish"""
    competition = get_object_or_404(Competition, slug=slug, status__in=['upcoming', 'active'])

    participant, created = CompetitionParticipant.objects.get_or_create(
        competition=competition, user=request.user
    )

    if created:
        competition.participants_count += 1
        competition.save()
        messages.success(request, "Musobaqaga qo'shildingiz!")

    return redirect('competitions:competition_detail', slug=slug)


@login_required
def competition_start(request, slug):
    """Musobaqani boshlash"""
    competition = get_object_or_404(Competition, slug=slug, status='active')
    participant = get_object_or_404(CompetitionParticipant, competition=competition, user=request.user)

    if participant.is_completed:
        messages.info(request, "Siz allaqachon ishtirok etgansiz")
        return redirect('competitions:competition_detail', slug=slug)

    participant.is_started = True
    participant.started_at = timezone.now()
    participant.save()

    if competition.test:
        return redirect('tests_app:test_start', slug=competition.test.slug)

    return redirect('competitions:competition_detail', slug=slug)


def competition_leaderboard(request, slug):
    """Musobaqa reytingi"""
    competition = get_object_or_404(Competition, slug=slug)
    participants = CompetitionParticipant.objects.filter(
        competition=competition, is_completed=True
    ).select_related('user').order_by('rank')

    context = {
        'competition': competition,
        'participants': participants,
    }
    return render(request, 'competitions/competition_leaderboard.html', context)


@login_required
def battles_list(request):
    """Janglar ro'yxati"""
    pending = Battle.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user),
        status='pending'
    ).select_related('challenger', 'opponent', 'subject')

    active = Battle.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user),
        status__in=['accepted', 'in_progress']
    ).select_related('challenger', 'opponent', 'subject')

    completed = Battle.objects.filter(
        Q(challenger=request.user) | Q(opponent=request.user),
        status='completed'
    ).select_related('challenger', 'opponent', 'winner').order_by('-completed_at')[:10]

    friendships = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )
    friends = []
    for f in friendships:
        friend = f.to_user if f.from_user == request.user else f.from_user
        friends.append(friend)

    context = {
        'pending': pending,
        'active': active,
        'completed': completed,
        'friends': friends,
    }
    return render(request, 'competitions/battles_list.html', context)


@login_required
def battle_create(request):
    """Jang yaratish"""
    if request.method == 'POST':
        opponent_id = request.POST.get('opponent_id')
        subject_id = request.POST.get('subject_id')
        question_count = int(request.POST.get('question_count', 10))

        opponent = get_object_or_404(User, id=opponent_id)
        subject = Subject.objects.filter(id=subject_id).first()

        questions = list(
            Question.objects.filter(subject=subject, is_active=True) if subject else Question.objects.filter(
                is_active=True))
        random.shuffle(questions)
        questions = questions[:question_count]

        questions_data = []
        for q in questions:
            answers = list(q.answers.all().values('id', 'text', 'is_correct'))
            random.shuffle(answers)
            questions_data.append({'id': q.id, 'text': q.text, 'answers': answers})

        battle = Battle.objects.create(
            challenger=request.user,
            opponent=opponent,
            subject=subject,
            question_count=question_count,
            questions_data=questions_data,
            expires_at=timezone.now() + timedelta(hours=24)
        )

        messages.success(request, f"{opponent.first_name}ga jang so'rovi yuborildi!")
        return redirect('competitions:battle_detail', uuid=battle.uuid)

    subjects = Subject.objects.filter(is_active=True)
    friendships = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )
    friends = []
    for f in friendships:
        friend = f.to_user if f.from_user == request.user else f.from_user
        friends.append(friend)

    context = {'subjects': subjects, 'friends': friends}
    return render(request, 'competitions/battle_create.html', context)


@login_required
def battle_detail(request, uuid):
    """Jang tafsilotlari"""
    battle = get_object_or_404(Battle, uuid=uuid)

    if request.user not in [battle.challenger, battle.opponent]:
        messages.error(request, "Bu jangda ishtirok etmaysiz")
        return redirect('competitions:battles_list')

    context = {
        'battle': battle,
        'is_challenger': request.user == battle.challenger,
    }
    return render(request, 'competitions/battle_detail.html', context)


@login_required
def battle_accept(request, uuid):
    """Jangni qabul qilish"""
    battle = get_object_or_404(Battle, uuid=uuid, opponent=request.user, status='pending')
    battle.status = 'accepted'
    battle.accepted_at = timezone.now()
    battle.save()

    messages.success(request, "Jang qabul qilindi!")
    return redirect('competitions:battle_detail', uuid=uuid)


@login_required
def battle_reject(request, uuid):
    """Jangni rad etish"""
    battle = get_object_or_404(Battle, uuid=uuid, opponent=request.user, status='pending')
    battle.status = 'rejected'
    battle.save()

    messages.info(request, "Jang rad etildi")
    return redirect('competitions:battles_list')


@login_required
def battle_play(request, uuid):
    """Jang o'yini"""
    battle = get_object_or_404(Battle, uuid=uuid)

    if request.user not in [battle.challenger, battle.opponent]:
        return redirect('competitions:battles_list')

    if battle.status not in ['accepted', 'in_progress']:
        return redirect('competitions:battle_detail', uuid=uuid)

    is_challenger = request.user == battle.challenger

    if is_challenger and battle.challenger_completed:
        messages.info(request, "Raqibni kuting")
        return redirect('competitions:battle_detail', uuid=uuid)

    if not is_challenger and battle.opponent_completed:
        messages.info(request, "Raqibni kuting")
        return redirect('competitions:battle_detail', uuid=uuid)

    if battle.status == 'accepted':
        battle.status = 'in_progress'
        battle.started_at = timezone.now()
        battle.save()

    context = {
        'battle': battle,
        'questions': battle.questions_data,
        'is_challenger': is_challenger,
    }
    return render(request, 'competitions/battle_play.html', context)


@login_required
def battle_submit(request, uuid):
    """Jang javoblarini yuborish"""
    if request.method != 'POST':
        return redirect('competitions:battle_play', uuid=uuid)

    battle = get_object_or_404(Battle, uuid=uuid)
    is_challenger = request.user == battle.challenger

    answers = json.loads(request.POST.get('answers', '[]'))
    time_spent = int(request.POST.get('time_spent', 0))

    correct = 0
    for ans in answers:
        q_data = next((q for q in battle.questions_data if q['id'] == ans['question_id']), None)
        if q_data:
            correct_ans = next((a for a in q_data['answers'] if a['is_correct']), None)
            if correct_ans and correct_ans['id'] == ans['answer_id']:
                correct += 1

    if is_challenger:
        battle.challenger_answers = answers
        battle.challenger_correct = correct
        battle.challenger_time = time_spent
        battle.challenger_completed = True
    else:
        battle.opponent_answers = answers
        battle.opponent_correct = correct
        battle.opponent_time = time_spent
        battle.opponent_completed = True

    battle.save()

    if battle.challenger_completed and battle.opponent_completed:
        battle.determine_winner()

    return redirect('competitions:battle_result', uuid=uuid)


@login_required
def battle_result(request, uuid):
    """Jang natijasi"""
    battle = get_object_or_404(Battle, uuid=uuid)

    context = {
        'battle': battle,
        'is_challenger': request.user == battle.challenger,
    }
    return render(request, 'competitions/battle_result.html', context)


@login_required
def daily_challenge(request):
    """Kunlik challenge"""
    today = timezone.now().date()
    challenge = DailyChallenge.objects.filter(date=today, is_active=True).first()

    participant = None
    if challenge and request.user.is_authenticated:
        participant = DailyChallengeParticipant.objects.filter(
            challenge=challenge, user=request.user
        ).first()

    top_participants = []
    if challenge:
        top_participants = DailyChallengeParticipant.objects.filter(
            challenge=challenge
        ).select_related('user').order_by('-score', 'time_spent')[:10]

    context = {
        'challenge': challenge,
        'participant': participant,
        'top_participants': top_participants,
    }
    return render(request, 'competitions/daily_challenge.html', context)


@login_required
def daily_challenge_start(request):
    """Kunlik challengeni boshlash"""
    today = timezone.now().date()
    challenge = get_object_or_404(DailyChallenge, date=today, is_active=True)

    existing = DailyChallengeParticipant.objects.filter(challenge=challenge, user=request.user).first()
    if existing:
        messages.info(request, "Siz bugun allaqachon ishtirok etgansiz")
        return redirect('competitions:daily_challenge')

    messages.success(request, "Challenge boshlandi!")
    return redirect('competitions:daily_challenge')


@login_required
def api_battle_status(request, uuid):
    """Jang holati API"""
    battle = get_object_or_404(Battle, uuid=uuid)

    data = {
        'status': battle.status,
        'challenger_completed': battle.challenger_completed,
        'opponent_completed': battle.opponent_completed,
        'winner_id': battle.winner.id if battle.winner else None,
        'is_draw': battle.is_draw,
    }
    return JsonResponse(data)


@login_required
def api_online_friends(request):
    """Online do'stlar API"""
    friendships = Friendship.objects.filter(
        Q(from_user=request.user) | Q(to_user=request.user),
        status='accepted'
    )

    friends = []
    for f in friendships:
        friend = f.to_user if f.from_user == request.user else f.from_user
        friends.append({
            'id': friend.id,
            'name': friend.full_name,
            'avatar': friend.get_avatar_url(),
        })

    return JsonResponse({'friends': friends})