from celery import shared_task
from django.db import transaction
from django.db.models import F
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def update_question_stats(self, question_id, is_correct):
    """
    Savol statistikasini background'da yangilash.
    test_play_submit da har javobda chaqiriladi — DB lock qilmaydi.
    """
    try:
        from tests_app.models import Question
        if is_correct:
            Question.objects.filter(id=question_id).update(
                times_answered=F('times_answered') + 1,
                times_correct=F('times_correct') + 1,
            )
        else:
            Question.objects.filter(id=question_id).update(
                times_answered=F('times_answered') + 1,
            )
    except Exception as exc:
        logger.error(f"update_question_stats xato: question_id={question_id}, {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def process_user_stats_after_test(self, attempt_id):
    """
    Test tugagandan keyin og'ir ishlarni background'da bajarish:
    - User xp, to'g'ri/noto'g'ri javoblar statistikasi
    - Activity log yozish
    - Cache tozalash
    User bularni kutmasdan natija sahifasini ko'radi.
    """
    try:
        from tests_app.models import TestAttempt, UserActivityLog

        attempt = TestAttempt.objects.select_related('user', 'test').get(id=attempt_id)
        user = attempt.user

        with transaction.atomic():
            # User statistikasini yangilash (F() bilan — race condition yo'q)
            user.__class__.objects.filter(id=user.id).update(
                total_tests_taken=F('total_tests_taken') + 1,
                total_correct_answers=F('total_correct_answers') + attempt.correct_answers,
                total_wrong_answers=F('total_wrong_answers') + attempt.wrong_answers,
                xp_points=F('xp_points') + attempt.xp_earned,
            )

            # Activity log
            UserActivityLog.objects.create(
                user=user,
                action='test_complete',
                details={
                    'test_id': attempt.test.id,
                    'score': attempt.percentage,
                    'correct': attempt.correct_answers,
                    'total': attempt.total_questions,
                    'time_spent': attempt.time_spent,
                    'xp_earned': attempt.xp_earned,
                },
                subject=attempt.test.subject,
            )

        # User natijalar cache ni tozalash
        invalidate_results_cache.delay(user.id)

        logger.info(f"process_user_stats_after_test OK: attempt_id={attempt_id}, user={user.id}")

    except Exception as exc:
        logger.error(f"process_user_stats_after_test xato: attempt_id={attempt_id}, {exc}")
        raise self.retry(exc=exc)


@shared_task
def invalidate_results_cache(user_id):
    """
    Foydalanuvchi natijalar cache ni tozalash.
    Yangi test tugagach my_results sahifasi yangi ma'lumot ko'rsatadi.
    """
    from django.core.cache import cache
    cache.delete(f'my_results_{user_id}')
    cache.delete(f'user_stats_{user_id}')
    logger.info(f"Cache tozalandi: user_id={user_id}")
