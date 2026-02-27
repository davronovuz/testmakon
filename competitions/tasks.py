"""
Competitions — Celery Tasks
Matchmaking queue processor (har 5 soniyada)
"""

from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='competitions.tasks.process_matchmaking_queue', bind=True, max_retries=0)
def process_matchmaking_queue(self):
    """
    Matchmaking navbatini qayta ishlash.
    Celery Beat tomonidan har 5 soniyada chaqiriladi.
    Rating ±300 oralig'ida juftlaydi va ikkala foydalanuvchiga
    WebSocket orqali match_found xabar yuboradi.
    """
    try:
        from .models import MatchmakingQueue, Battle
        from tests_app.models import Subject

        now = timezone.now()

        # Muddati o'tmagan, juftlanmagan queue yozuvlari
        queue_qs = MatchmakingQueue.objects.filter(
            is_matched=False,
            expires_at__gt=now,
        ).select_related('user', 'subject').order_by('joined_at')

        processed_ids = set()
        matched_count = 0

        for entry in queue_qs:
            if entry.id in processed_ids:
                continue

            # Mos raqib qidirish
            candidates = queue_qs.filter(
                user_rating__gte=entry.user_rating - 300,
                user_rating__lte=entry.user_rating + 300,
            ).exclude(user=entry.user).exclude(id__in=processed_ids)

            if entry.subject:
                from django.db.models import Q
                candidates = candidates.filter(
                    Q(subject=entry.subject) | Q(subject__isnull=True)
                )

            opponent_entry = candidates.first()
            if not opponent_entry:
                continue

            # Match topildi — Battle yaratish
            try:
                # Circular import oldini olish — generate_questions ni bu yerda implement qilamiz
                from tests_app.models import Question as Q2
                subj = entry.subject or opponent_entry.subject
                qs = Q2.objects.filter(is_active=True)
                if subj:
                    qs = qs.filter(subject=subj)
                qs = list(qs.order_by('?')[:entry.question_count].prefetch_related('answers'))
                questions_data = []
                for q in qs:
                    answers = list(q.answers.values('id', 'answer_text', 'is_correct'))
                    questions_data.append({
                        'id': q.id,
                        'text': q.question_text,
                        'subject': subj.name if subj else '',
                        'answers': answers,
                    })
            except Exception:
                questions_data = []

            battle = Battle.objects.create(
                challenger=entry.user,
                opponent=opponent_entry.user,
                opponent_type='random',
                subject=entry.subject or opponent_entry.subject,
                question_count=entry.question_count,
                questions_data=questions_data,
                total_time=entry.question_count * 30,
                status='accepted',
                accepted_at=now,
                expires_at=now + timedelta(hours=1),
            )

            # Queue'larni yangilash
            MatchmakingQueue.objects.filter(
                id__in=[entry.id, opponent_entry.id]
            ).update(is_matched=True, matched_with=None, battle=battle)

            processed_ids.add(entry.id)
            processed_ids.add(opponent_entry.id)
            matched_count += 1

            # WebSocket orqali ikkala foydalanuvchiga xabar
            _notify_match_found(entry.user, opponent_entry.user, battle)
            _notify_match_found(opponent_entry.user, entry.user, battle)

        if matched_count:
            logger.info(f'Matchmaking: {matched_count} juft topildi')

        # Muddati o'tgan queue yozuvlarini o'chirish
        MatchmakingQueue.objects.filter(
            is_matched=False,
            expires_at__lte=now,
        ).delete()

    except Exception as exc:
        logger.error(f'Matchmaking task xatosi: {exc}')


def _notify_match_found(user, opponent, battle):
    """WebSocket orqali match_found xabar yuborish"""
    try:
        from asgiref.sync import async_to_sync
        from channels.layers import get_channel_layer
        channel_layer = get_channel_layer()
        if not channel_layer:
            return
        async_to_sync(channel_layer.group_send)(
            f'user_{user.id}',
            {
                'type': 'match.found',
                'battle_uuid': str(battle.uuid),
                'opponent': {
                    'id': opponent.id,
                    'name': f'{opponent.first_name} {opponent.last_name}',
                    'avatar': opponent.get_avatar_url(),
                    'rating': getattr(opponent, 'rating', 1000),
                },
            }
        )
    except Exception as e:
        logger.warning(f'WebSocket match_found yuborishda xato: {e}')
