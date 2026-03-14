"""
TestMakon — Milliy Sertifikat Celery Tasks
"""
from celery import shared_task


@shared_task(bind=True, max_retries=3, default_retry_delay=10)
def update_cert_question_stats(self, question_id, is_correct):
    """Savol statistikasini background da yangilash (IRT uchun)"""
    try:
        from .models import CertQuestion
        CertQuestion.objects.filter(pk=question_id).update(
            times_answered=__import__('django.db.models', fromlist=['F']).F('times_answered') + 1,
        )
        if is_correct:
            CertQuestion.objects.filter(pk=question_id).update(
                times_correct=__import__('django.db.models', fromlist=['F']).F('times_correct') + 1,
            )
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=15)
def process_cert_attempt_results(self, attempt_id):
    """
    Mock yakunlangandan so'ng background da:
    1. Har savol statistikasini yangilash (IRT)
    2. User umumiy statistikasini yangilash
    3. Sust mavzularni aniqlash
    """
    try:
        from django.db.models import F
        from .models import CertMockAttempt, CertQuestion

        attempt = CertMockAttempt.objects.select_related(
            'user', 'mock__cert_subject__subject'
        ).get(pk=attempt_id)

        answers = attempt.answers.select_related('question__topic').all()

        # 1. Har savol stats yangilash
        for ans in answers:
            q = ans.question
            CertQuestion.objects.filter(pk=q.pk).update(
                times_answered=F('times_answered') + 1
            )
            if ans.is_correct:
                CertQuestion.objects.filter(pk=q.pk).update(
                    times_correct=F('times_correct') + 1
                )

        # 2. User umumiy statistikasi
        _update_user_cert_stats(attempt, answers)

    except Exception as exc:
        raise self.retry(exc=exc)


def _update_user_cert_stats(attempt, answers):
    """User statistikasini yangilash — sust mavzularni aniqlash"""
    try:
        from django.utils import timezone
        from tests_app.models import DailyUserStats

        user = attempt.user
        today = timezone.now().date()

        # XP: to'g'ri har javob uchun 3 XP
        xp = attempt.correct_answers * 3
        if attempt.earned_points >= 70:
            xp = int(xp * 1.5)  # A+ uchun bonus

        if hasattr(user, 'add_xp'):
            user.add_xp(xp)
        else:
            user.xp_points = getattr(user, 'xp_points', 0) + xp
            user.save(update_fields=['xp_points'])

        # Kunlik statistika
        daily, _ = DailyUserStats.objects.get_or_create(user=user, date=today)
        daily.tests_taken       += 1
        daily.questions_answered += attempt.total_questions
        daily.correct_answers   += attempt.correct_answers
        daily.wrong_answers     += attempt.wrong_answers
        daily.xp_earned         += xp
        total_q = (daily.correct_answers + daily.wrong_answers) or 1
        daily.accuracy_rate = round(daily.correct_answers / total_q * 100, 1)
        daily.save()

    except Exception:
        pass  # statistika xatosi asosiy oqimni to'xtatmasin
