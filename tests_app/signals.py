"""
TestMakon.uz - Test App Signals
Avtomatik data yig'ish va analytics yangilash
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.db.models import Avg

from .models import (
    AttemptAnswer, TestAttempt,
    UserTopicPerformance, UserSubjectPerformance,
    DailyUserStats, UserActivityLog, UserAnalyticsSummary
)


@receiver(post_save, sender=AttemptAnswer)
def update_topic_performance(sender, instance, created, **kwargs):
    """Har bir javobda topic performance yangilanadi"""
    if not created:
        return

    question = instance.question
    user = instance.attempt.user

    # Topic bo'lmasa, skip
    if not question.topic:
        return

    # Topic performance olish yoki yaratish
    perf, _ = UserTopicPerformance.objects.get_or_create(
        user=user,
        topic=question.topic,
        defaults={'subject': question.subject}
    )

    # Statistikani yangilash
    perf.total_questions += 1
    perf.total_time_spent += instance.time_spent

    if instance.is_correct:
        perf.correct_answers += 1
    else:
        perf.wrong_answers += 1

    perf.last_practiced = timezone.now()
    perf.update_stats()


@receiver(post_save, sender=TestAttempt)
def update_subject_performance(sender, instance, **kwargs):
    """Test yakunlanganda subject performance yangilanadi"""
    if instance.status != 'completed':
        return

    user = instance.user
    subject = instance.test.subject

    if not subject:
        return

    # Subject performance olish yoki yaratish
    perf, _ = UserSubjectPerformance.objects.get_or_create(
        user=user,
        subject=subject
    )

    # Statistikani yangilash
    perf.total_tests += 1
    perf.total_questions += instance.total_questions
    perf.correct_answers += instance.correct_answers
    perf.total_time_spent += instance.time_spent

    perf.last_score = instance.percentage
    if instance.percentage > perf.best_score:
        perf.best_score = instance.percentage

    # O'rtacha hisoblash
    all_attempts = TestAttempt.objects.filter(
        user=user,
        test__subject=subject,
        status='completed'
    )
    perf.average_score = all_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0

    perf.last_practiced = timezone.now()
    perf.save()


@receiver(post_save, sender=TestAttempt)
def update_daily_stats(sender, instance, **kwargs):
    """Test yakunlanganda kunlik statistika yangilanadi"""
    if instance.status != 'completed':
        return

    user = instance.user
    today = timezone.now().date()

    # Kunlik stats olish yoki yaratish
    stats, _ = DailyUserStats.objects.get_or_create(
        user=user,
        date=today
    )

    # Yangilash
    stats.tests_taken += 1
    stats.questions_answered += instance.total_questions
    stats.correct_answers += instance.correct_answers
    stats.wrong_answers += instance.wrong_answers
    stats.total_time_spent += instance.time_spent
    stats.xp_earned += instance.xp_earned

    # Faollik soati
    current_hour = timezone.now().hour
    activity_hours = stats.activity_hours or {}
    activity_hours[str(current_hour)] = activity_hours.get(str(current_hour), 0) + 1
    stats.activity_hours = activity_hours

    # Eng faol soatni aniqlash
    if activity_hours:
        stats.most_active_hour = int(max(activity_hours, key=activity_hours.get))

    # Fan bo'yicha
    if instance.test.subject:
        subjects_practiced = stats.subjects_practiced or {}
        subj_name = instance.test.subject.slug
        if subj_name not in subjects_practiced:
            subjects_practiced[subj_name] = {'correct': 0, 'total': 0}
        subjects_practiced[subj_name]['correct'] += instance.correct_answers
        subjects_practiced[subj_name]['total'] += instance.total_questions
        stats.subjects_practiced = subjects_practiced

    stats.calculate_accuracy()


@receiver(post_save, sender=TestAttempt)
def log_test_activity(sender, instance, created, **kwargs):
    """Test boshlanganda va yakunlanganda log yozish"""
    if created:
        # Test boshlandi
        UserActivityLog.objects.create(
            user=instance.user,
            action='test_start',
            details={
                'test_id': instance.test.id,
                'test_title': instance.test.title,
                'test_type': instance.test.test_type,
            },
            subject=instance.test.subject
        )
    elif instance.status == 'completed':
        # Test yakunlandi
        UserActivityLog.objects.create(
            user=instance.user,
            action='test_complete',
            details={
                'test_id': instance.test.id,
                'test_title': instance.test.title,
                'score': instance.percentage,
                'correct': instance.correct_answers,
                'total': instance.total_questions,
                'time_spent': instance.time_spent,
                'xp_earned': instance.xp_earned,
            },
            subject=instance.test.subject
        )


@receiver(post_save, sender=AttemptAnswer)
def log_question_answer(sender, instance, created, **kwargs):
    """Har bir javobni log qilish"""
    if not created:
        return

    UserActivityLog.objects.create(
        user=instance.attempt.user,
        action='question_answer',
        details={
            'question_id': instance.question.id,
            'is_correct': instance.is_correct,
            'time_spent': instance.time_spent,
        },
        subject=instance.question.subject,
        topic=instance.question.topic
    )