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
    - Analytics yangilash (UserTopicPerformance, UserSubjectPerformance, WeakTopicAnalysis)
    User bularni kutmasdan natija sahifasini ko'radi.
    """
    try:
        from tests_app.models import TestAttempt, UserActivityLog

        attempt = TestAttempt.objects.select_related('user', 'test', 'test__subject').get(id=attempt_id)
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

        # Leaderboard cache ham yangilanishi kerak
        from leaderboard.tasks import invalidate_leaderboard_cache
        invalidate_leaderboard_cache.delay()

        # Analytics yangilash (mavzu, fan, sust mavzular, DTM ball)
        update_user_analytics.delay(attempt_id)

        logger.info(f"process_user_stats_after_test OK: attempt_id={attempt_id}, user={user.id}")

    except Exception as exc:
        logger.error(f"process_user_stats_after_test xato: attempt_id={attempt_id}, {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, default_retry_delay=60)
def update_user_analytics(self, attempt_id):
    """
    Test natijasidan keyin barcha user analytics modellarini yangilash:
    1. UserTopicPerformance — har bir mavzu uchun
    2. UserSubjectPerformance — fan uchun
    3. WeakTopicAnalysis — sust mavzularni aniqlash va saqlash
    4. UserAnalyticsSummary — predicted_dtm_score va umumiy ko'rsatkichlar
    """
    try:
        from tests_app.models import (
            TestAttempt, AttemptAnswer,
            UserTopicPerformance, UserSubjectPerformance, UserAnalyticsSummary
        )
        from ai_core.models import WeakTopicAnalysis
        from django.utils import timezone

        attempt = TestAttempt.objects.select_related(
            'user', 'test', 'test__subject'
        ).get(id=attempt_id)
        user = attempt.user
        subject = attempt.test.subject if attempt.test else None

        # Javoblarni mavzu bo'yicha guruhlash
        answers = AttemptAnswer.objects.filter(attempt=attempt).select_related(
            'question__topic', 'question__subject'
        )

        topic_data = {}  # {topic_id: {'topic': obj, 'subject': obj, 'correct': int, 'total': int, 'time': int}}
        for ans in answers:
            topic = ans.question.topic
            if not topic:
                continue
            subj = ans.question.subject
            tid = topic.id
            if tid not in topic_data:
                topic_data[tid] = {
                    'topic': topic,
                    'subject': subj,
                    'correct': 0,
                    'total': 0,
                    'time': 0,
                }
            topic_data[tid]['total'] += 1
            topic_data[tid]['time'] += ans.time_spent
            if ans.is_correct:
                topic_data[tid]['correct'] += 1

        # --- 1. UserTopicPerformance yangilash ---
        for tid, data in topic_data.items():
            perf, _ = UserTopicPerformance.objects.get_or_create(
                user=user,
                topic=data['topic'],
                defaults={'subject': data['subject']}
            )
            perf.total_questions = F('total_questions') + data['total']
            perf.correct_answers = F('correct_answers') + data['correct']
            perf.wrong_answers = F('wrong_answers') + (data['total'] - data['correct'])
            perf.total_time_spent = F('total_time_spent') + data['time']
            perf.last_practiced = timezone.now()
            perf.save(update_fields=[
                'total_questions', 'correct_answers', 'wrong_answers',
                'total_time_spent', 'last_practiced'
            ])
            # Refresh va update_stats chaqirish
            perf.refresh_from_db()
            perf.update_stats()

        # --- 2. UserSubjectPerformance yangilash ---
        if subject:
            subj_perf, _ = UserSubjectPerformance.objects.get_or_create(
                user=user,
                subject=subject
            )
            subj_perf.total_tests = F('total_tests') + 1
            subj_perf.total_questions = F('total_questions') + attempt.total_questions
            subj_perf.correct_answers = F('correct_answers') + attempt.correct_answers
            subj_perf.total_time_spent = F('total_time_spent') + attempt.time_spent
            subj_perf.last_practiced = timezone.now()
            subj_perf.save(update_fields=[
                'total_tests', 'total_questions', 'correct_answers',
                'total_time_spent', 'last_practiced'
            ])
            subj_perf.refresh_from_db()

            # average_score, best_score, last_score, predicted_dtm_score
            if subj_perf.total_questions > 0:
                new_avg = round((subj_perf.correct_answers / subj_perf.total_questions) * 100, 1)
                subj_perf.average_score = new_avg
                subj_perf.last_score = attempt.percentage
                if attempt.percentage > subj_perf.best_score:
                    subj_perf.best_score = attempt.percentage
                # DTM bali: fan uchun o'rtacha ball × 0.3 (balllar tizimi: 30 ball = 100%)
                subj_perf.predicted_dtm_score = round(new_avg * 0.3, 1)
                subj_perf.save(update_fields=[
                    'average_score', 'best_score', 'last_score', 'predicted_dtm_score'
                ])

        # --- 3. WeakTopicAnalysis yangilash ---
        # Faqat kamida 5 ta savol ishlangan mavzularni tekshirish
        weak_threshold = 65.0  # 65% dan past = kuchsiz mavzu
        for tid, data in topic_data.items():
            perf = UserTopicPerformance.objects.filter(user=user, topic_id=tid).first()
            if not perf or perf.total_questions < 5:
                continue  # Yetarli data yo'q

            accuracy = perf.current_score  # update_stats() dan keyin

            if accuracy < weak_threshold:
                # Sust mavzu — WeakTopicAnalysis da saqlash
                priority = round((weak_threshold - accuracy) / weak_threshold * 10, 1)
                WeakTopicAnalysis.objects.update_or_create(
                    user=user,
                    topic=data['topic'],
                    defaults={
                        'subject': data['subject'],
                        'total_questions': perf.total_questions,
                        'correct_answers': perf.correct_answers,
                        'accuracy_rate': accuracy,
                        'priority_score': priority,
                    }
                )
            else:
                # Endi kuchsiz emas — o'chirish
                WeakTopicAnalysis.objects.filter(user=user, topic_id=tid).delete()

        # --- 4. UserAnalyticsSummary yangilash ---
        _update_analytics_summary(user)

        # --- 5. Agar DTM test bo'lsa — AI universitet tavsiyasi ---
        test_type = attempt.test.test_type if attempt.test else None
        if test_type in ('exam', 'block') and attempt.percentage >= 40:
            from ai_core.tasks import generate_university_recommendation
            generate_university_recommendation.delay(user.id, attempt_id)

        logger.info(f"update_user_analytics OK: attempt_id={attempt_id}, user={user.id}, topics={len(topic_data)}")

    except Exception as exc:
        logger.error(f"update_user_analytics xato: attempt_id={attempt_id}, {exc}")
        raise self.retry(exc=exc)


def _update_analytics_summary(user):
    """UserAnalyticsSummary ni yangilash — predicted_dtm_score va boshqa ko'rsatkichlar."""
    try:
        from django.db.models import Sum, Count, Avg
        from tests_app.models import (
            UserSubjectPerformance, UserTopicPerformance, UserAnalyticsSummary, TestAttempt
        )

        summary, _ = UserAnalyticsSummary.objects.get_or_create(user=user)

        # Umumiy statistika — aggregation bilan (DB dan bir so'rovda)
        agg = TestAttempt.objects.filter(user=user, status='completed').aggregate(
            total_tests=Count('id'),
            total_correct=Sum('correct_answers'),
            total_questions=Sum('total_questions'),
            total_time=Sum('time_spent'),
        )
        total_tests = agg['total_tests'] or 0
        total_correct = agg['total_correct'] or 0
        total_questions = agg['total_questions'] or 0
        total_time = agg['total_time'] or 0

        summary.total_tests_completed = total_tests
        summary.total_questions_solved = total_questions
        summary.total_study_time = total_time // 3600  # soatga o'girish

        if total_questions > 0:
            summary.overall_accuracy = round((total_correct / total_questions) * 100, 1)

        # Mavzu statistikasi
        from ai_core.models import WeakTopicAnalysis
        summary.weak_topics_count = WeakTopicAnalysis.objects.filter(user=user).count()

        topic_perfs = UserTopicPerformance.objects.filter(user=user)
        summary.strong_topics_count = topic_perfs.filter(is_strong=True).count()
        summary.mastered_topics_count = topic_perfs.filter(is_mastered=True).count()

        # DTM ball bashorati — fan natijalari asosida
        # DTM tizimi: max 189 ball. Sodda formula: umumiy o'rtacha foiz / 100 × 189
        subject_avg = UserSubjectPerformance.objects.filter(
            user=user, total_questions__gte=10
        ).aggregate(avg=Avg('average_score'))['avg']

        if subject_avg:
            summary.predicted_dtm_score = round((subject_avg / 100) * 189)

        summary.save()

    except Exception as e:
        logger.error(f"_update_analytics_summary xato: user={user.id}, {e}")


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
