"""
AI Core — Test Suite
Qamrov: views (university_dashboard, progress_dashboard, behavioral_insights,
         smart_test_generate), tasks (send_smart_behavioral_notifications,
         send_inactivity_reminders, generate_weekly_ai_report)
"""

import json
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tests_app.models import (
    Subject, Topic, Question, Test, TestQuestion, TestAttempt,
    UserAnalyticsSummary, UserSubjectPerformance, UserTopicPerformance,
    DailyUserStats,
)
from universities.models import University, Direction, PassingScore
from news.models import Notification
from ai_core.models import WeakTopicAnalysis, AIRecommendation

User = get_user_model()


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_user(phone='+998901234567', password='testpass123', **kwargs):
    return User.objects.create_user(
        phone_number=phone, password=password,
        first_name='Test', last_name='User', **kwargs
    )


def make_subject(name='Matematika', slug='matematika'):
    return Subject.objects.create(name=name, slug=slug, is_active=True)


def make_topic(subject, name='Algebra', slug='algebra'):
    return Topic.objects.create(subject=subject, name=name, slug=slug)


def make_question(subject, topic=None):
    return Question.objects.create(
        subject=subject, topic=topic,
        text='Test savol matni',
        is_active=True,
    )


def make_test(user, subject, slug='test-slug', question_count=5):
    return Test.objects.create(
        title='Test', slug=slug,
        test_type='practice', subject=subject,
        time_limit=10, question_count=question_count,
        created_by=user,
    )


def make_attempt(user, test, status='completed', percentage=75.0):
    return TestAttempt.objects.create(
        user=user, test=test,
        total_questions=test.question_count,
        correct_answers=int(test.question_count * percentage / 100),
        status=status,
        percentage=percentage,
    )


def make_analytics(user, predicted_dtm=120, accuracy=70.0, streak=5,
                   avg_session=45, avg_qpd=20.0, weak_count=3):
    return UserAnalyticsSummary.objects.create(
        user=user,
        predicted_dtm_score=predicted_dtm,
        overall_accuracy=accuracy,
        current_streak=streak,
        avg_session_duration=avg_session,
        avg_questions_per_day=avg_qpd,
        weak_topics_count=weak_count,
    )


def make_university_chain(grant_score=110, contract_score=80, year=2024):
    uni = University.objects.create(name='Test Universiteti', slug='test-uni')
    direction = Direction.objects.create(
        university=uni, name='Informatika', slug='informatika', is_active=True
    )
    ps = PassingScore.objects.create(
        direction=direction, year=year,
        grant_score=grant_score, contract_score=contract_score
    )
    return uni, direction, ps


# ─────────────────────────────────────────────────────────────
# VIEW TESTS
# ─────────────────────────────────────────────────────────────

class UniversityDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_core:university_dashboard')
        self.user = make_user()

    def test_login_required(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/', resp['Location'])

    def test_renders_200_without_analytics(self):
        """Analytics yo'q bo'lsa ham sahifa ochilishi kerak."""
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ai_core/university_dashboard.html')

    def test_renders_with_analytics(self):
        make_analytics(self.user, predicted_dtm=150)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.context['predicted_dtm'], 150)

    def test_safe_category_correct(self):
        """predicted_dtm=150, grant_score=130 → gap=20 → ishonchli."""
        make_analytics(self.user, predicted_dtm=150)
        make_university_chain(grant_score=130, year=2024)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        # 150 >= 130 + 10 → safe
        self.assertEqual(len(resp.context['safe_unis']), 1)
        self.assertEqual(len(resp.context['borderline_unis']), 0)
        self.assertEqual(len(resp.context['reach_unis']), 0)

    def test_borderline_category_correct(self):
        """predicted_dtm=140, grant_score=145 → gap=-5 → chegara."""
        make_analytics(self.user, predicted_dtm=140)
        make_university_chain(grant_score=145, year=2024)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        # 140 < 145+10 and 140 >= 145-15 → borderline
        self.assertEqual(len(resp.context['borderline_unis']), 1)
        self.assertEqual(len(resp.context['safe_unis']), 0)

    def test_reach_category_correct(self):
        """predicted_dtm=100, grant_score=125 → gap=-25 → maqsad."""
        make_analytics(self.user, predicted_dtm=100)
        make_university_chain(grant_score=125, year=2024)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        # 100 < 125-15=110 and 100 >= 125-40=85 → reach
        self.assertEqual(len(resp.context['reach_unis']), 1)
        self.assertEqual(len(resp.context['safe_unis']), 0)
        self.assertEqual(len(resp.context['borderline_unis']), 0)

    def test_zero_dtm_all_empty(self):
        """DTM=0 bo'lsa hech qaysi kategoriyaga tushmaydi."""
        make_analytics(self.user, predicted_dtm=0)
        make_university_chain(grant_score=100, year=2024)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['safe_unis'], [])
        self.assertEqual(resp.context['borderline_unis'], [])
        self.assertEqual(resp.context['reach_unis'], [])


class ProgressDashboardViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_core:progress_dashboard')
        self.user = make_user()
        self.subject = make_subject()

    def test_login_required(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_renders_200_empty_data(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ai_core/progress_dashboard.html')

    def test_chart_data_serialized(self):
        """Chart labels va scores JSON formatida context'da bo'lishi kerak."""
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        # JSON parseable bo'lishi kerak
        labels = json.loads(resp.context['chart_labels'])
        scores = json.loads(resp.context['chart_scores'])
        self.assertIsInstance(labels, list)
        self.assertIsInstance(scores, list)

    def test_peer_rank_calculated(self):
        """Bir xil education_level da 2 user → rank 1 yoki 2."""
        user2 = make_user(phone='+998902222222')
        make_analytics(self.user, predicted_dtm=130)
        make_analytics(user2, predicted_dtm=100)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        # user predicted_dtm 130 > user2 100 → rank=1
        self.assertEqual(resp.context['peer_rank'], 1)
        self.assertEqual(resp.context['peer_total'], 2)

    def test_weak_topics_in_context(self):
        topic = make_topic(self.subject)
        UserTopicPerformance.objects.create(
            user=self.user, subject=self.subject, topic=topic,
            is_weak=True, current_score=30.0,
        )
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.context['weak_topic_perfs']), 1)

    def test_subject_perfs_in_context(self):
        UserSubjectPerformance.objects.create(
            user=self.user, subject=self.subject, average_score=65.0,
        )
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['subject_perfs'].count(), 1)


class BehavioralInsightsViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_core:behavioral_insights')
        self.user = make_user()

    def test_login_required(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 302)

    def test_renders_200(self):
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, 200)
        self.assertTemplateUsed(resp, 'ai_core/behavioral_insights.html')

    def test_burnout_risk_high(self):
        """avg_session>90 + avg_qpd>50 → high."""
        make_analytics(self.user, avg_session=120, avg_qpd=60.0)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['burnout_risk'], 'high')

    def test_burnout_risk_medium(self):
        """Faqat avg_session>90 → medium."""
        make_analytics(self.user, avg_session=100, avg_qpd=30.0)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['burnout_risk'], 'medium')

    def test_burnout_risk_low(self):
        """Normal qiymatlar → low."""
        make_analytics(self.user, avg_session=45, avg_qpd=20.0)
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['burnout_risk'], 'low')

    def test_week_activity_has_7_items(self):
        """Oxirgi 7 kun har doim 7 ta element bo'lishi kerak."""
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.context['week_activity']), 7)

    def test_hourly_activity_has_24_items(self):
        """24 soat grid."""
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(len(resp.context['hourly_activity']), 24)

    def test_daily_stats_activity_hours_parsed(self):
        """DailyUserStats activity_hours → hourly_activity ga yig'iladi."""
        today = timezone.localdate()
        DailyUserStats.objects.create(
            user=self.user, date=today,
            activity_hours={'20': 15, '21': 8},
        )
        self.client.force_login(self.user)
        resp = self.client.get(self.url)
        self.assertEqual(resp.context['hourly_activity'][20], 15)
        self.assertEqual(resp.context['hourly_activity'][21], 8)


class SmartTestGenerateViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('ai_core:smart_test_generate')
        self.user = make_user()
        self.subject = make_subject()
        self.topic = make_topic(self.subject)

    def test_login_required(self):
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/accounts/', resp['Location'])

    def test_creates_test_and_redirects(self):
        """Savollar mavjud bo'lsa Test + TestAttempt yaratib test_play ga redirect."""
        for i in range(5):
            make_question(self.subject, self.topic)
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)
        # TestAttempt yaratilganini tekshirish
        attempt = TestAttempt.objects.filter(user=self.user).first()
        self.assertIsNotNone(attempt)
        self.assertIn(str(attempt.uuid), resp['Location'])

    def test_subject_filter_works(self):
        """subject_id berilsa faqat o'sha fandan savollar."""
        subj2 = make_subject(name='Fizika', slug='fizika')
        for i in range(5):
            make_question(self.subject, self.topic)
        for i in range(5):
            make_question(subj2)
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {'subject_id': self.subject.id})
        self.assertEqual(resp.status_code, 302)
        test = Test.objects.filter(created_by=self.user).first()
        self.assertIsNotNone(test)
        # Test faqat matematika savollaridan iborat
        self.assertEqual(test.subject, self.subject)

    def test_no_questions_redirects_to_weak_topics(self):
        """Savollar yo'q → weak_topics ga redirect + error."""
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('weak-topics', resp['Location'])

    def test_weak_topics_used_first(self):
        """WeakTopicAnalysis mavjud → sust mavzu savollari prioritet oladi."""
        topic2 = make_topic(self.subject, name='Geometriya', slug='geometriya')
        for i in range(10):
            make_question(self.subject, self.topic)
        WeakTopicAnalysis.objects.create(
            user=self.user, subject=self.subject, topic=self.topic,
            accuracy_rate=30.0, total_questions=20, correct_answers=6,
        )
        self.client.force_login(self.user)
        resp = self.client.post(self.url, {})
        self.assertEqual(resp.status_code, 302)
        self.assertTrue(TestAttempt.objects.filter(user=self.user).exists())

    def test_test_type_is_practice(self):
        """Yaratilgan test har doim practice turida bo'ladi."""
        for i in range(5):
            make_question(self.subject)
        self.client.force_login(self.user)
        self.client.post(self.url, {})
        test = Test.objects.filter(created_by=self.user).first()
        self.assertEqual(test.test_type, 'practice')

    def test_attempt_status_is_in_progress(self):
        """Yaratilgan attempt in_progress holatida bo'ladi."""
        for i in range(5):
            make_question(self.subject)
        self.client.force_login(self.user)
        self.client.post(self.url, {})
        attempt = TestAttempt.objects.filter(user=self.user).first()
        self.assertEqual(attempt.status, 'in_progress')


class SmartTestStatusViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = make_user()

    def test_login_required(self):
        resp = self.client.get(reverse('ai_core:smart_test_status', args=['fake-id']))
        self.assertEqual(resp.status_code, 302)

    @patch('ai_core.views.api_task_status')
    def test_delegates_to_api_task_status(self, mock_status):
        """smart_test_status api_task_status ga delegate qiladi."""
        mock_status.return_value = MagicMock(status_code=200)
        self.client.force_login(self.user)
        self.client.get(reverse('ai_core:smart_test_status', args=['test-task-id']))
        mock_status.assert_called_once()


# ─────────────────────────────────────────────────────────────
# TASK TESTS
# ─────────────────────────────────────────────────────────────

class SendSmartBehavioralNotificationsTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.subject = make_subject()

    def _run(self):
        from ai_core.tasks import send_smart_behavioral_notifications
        send_smart_behavioral_notifications()

    def test_achievement_notification_created_for_today_test(self):
        """Bugun test ishlaganda achievement notification yaratiladi."""
        test = make_test(self.user, self.subject, slug='ach-test')
        make_attempt(self.user, test, percentage=80.0)
        self._run()
        notif = Notification.objects.filter(
            user=self.user, notification_type='achievement'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('80', notif.message)

    def test_no_duplicate_achievement_today(self):
        """Ikkita ishlatilganda faqat 1 ta notification yaratiladi."""
        test = make_test(self.user, self.subject, slug='dup-test')
        make_attempt(self.user, test, percentage=70.0)
        self._run()
        self._run()
        count = Notification.objects.filter(
            user=self.user, notification_type='achievement'
        ).count()
        self.assertEqual(count, 1)

    def test_streak_notification_for_3plus_streak(self):
        """3+ kunlik streak va bugun faol → streak notification."""
        self.user.current_streak = 5
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run()
        notif = Notification.objects.filter(
            user=self.user, notification_type='system',
            title__startswith='🔥'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('5', notif.title)

    def test_no_streak_notification_for_low_streak(self):
        """1 kunlik streak → streak notification yaratilmaydi."""
        self.user.current_streak = 1
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run()
        notif = Notification.objects.filter(
            user=self.user, title__startswith='🔥'
        ).first()
        self.assertIsNone(notif)

    def test_improvement_notification(self):
        """Bu hafta avg > o'tgan hafta avg + 5 → improvement notification."""
        test = make_test(self.user, self.subject, slug='imp-test')
        # O'tgan hafta: 50%
        last_week = timezone.now() - timedelta(days=10)
        att1 = TestAttempt.objects.create(
            user=self.user, test=test, status='completed',
            total_questions=10, correct_answers=5, percentage=50.0,
        )
        TestAttempt.objects.filter(id=att1.id).update(created_at=last_week)

        # Bu hafta: 80%
        test2 = make_test(self.user, self.subject, slug='imp-test2')
        make_attempt(self.user, test2, percentage=80.0)

        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run()

        notif = Notification.objects.filter(
            user=self.user, title__startswith='📈'
        ).first()
        self.assertIsNotNone(notif)

    def test_no_improvement_notification_if_not_improved(self):
        """Natija yaxshilanmagan → improvement notification yaratilmaydi."""
        test = make_test(self.user, self.subject, slug='no-imp-test')
        # O'tgan hafta: 80%
        last_week = timezone.now() - timedelta(days=10)
        att1 = TestAttempt.objects.create(
            user=self.user, test=test, status='completed',
            total_questions=10, correct_answers=8, percentage=80.0,
        )
        TestAttempt.objects.filter(id=att1.id).update(created_at=last_week)

        # Bu hafta: 60%
        test2 = make_test(self.user, self.subject, slug='no-imp-test2')
        make_attempt(self.user, test2, percentage=60.0)

        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run()

        notif = Notification.objects.filter(
            user=self.user, title__startswith='📈'
        ).first()
        self.assertIsNone(notif)


class SendInactivityRemindersTest(TestCase):
    def setUp(self):
        self.user = make_user()

    def _run(self):
        from ai_core.tasks import send_inactivity_reminders
        send_inactivity_reminders()

    def test_reminder_for_2_day_inactive(self):
        """3 kun faol bo'lmagan user → reminder notification."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=3)
        self.user.save()
        self._run()
        notif = Notification.objects.filter(
            user=self.user, notification_type='reminder'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('Testlar sizi kutmoqda', notif.title)

    def test_no_reminder_for_active_user(self):
        """Bugun faol user → eslatma yaratilmaydi."""
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run()
        self.assertFalse(
            Notification.objects.filter(user=self.user, notification_type='reminder').exists()
        )

    def test_stronger_reminder_for_5_day_inactive(self):
        """6 kun faol bo'lmagan → warning notification."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=6)
        self.user.save()
        self._run()
        notif = Notification.objects.filter(
            user=self.user, notification_type='reminder'
        ).first()
        self.assertIsNotNone(notif)
        self.assertIn('Uzoq vaqt', notif.title)

    def test_no_duplicate_reminder_same_day(self):
        """Ikki marta ishlatilsa faqat 1 ta notification."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=3)
        self.user.save()
        self._run()
        self._run()
        count = Notification.objects.filter(user=self.user, notification_type='reminder').count()
        self.assertEqual(count, 1)

    @patch('requests.post')
    def test_telegram_sent_for_5day_inactive_with_telegram_id(self, mock_post):
        """6 kun faol bo'lmagan + telegram_id → requests.post chaqiriladi."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=6)
        self.user.telegram_id = 123456789
        self.user.save()
        self._run()
        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        self.assertIn('sendMessage', call_args[0][0])

    @patch('requests.post')
    def test_no_telegram_for_2day_inactive(self, mock_post):
        """2-4 kun inactive → Telegram xabar yuborilmaydi."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=3)
        self.user.telegram_id = 123456789
        self.user.save()
        self._run()
        self.assertFalse(mock_post.called)

    def test_user_without_last_activity_skipped(self):
        """last_activity_date=None bo'lsa 5-day check'dan o'tkazilmaydi."""
        self.user.last_activity_date = None
        self.user.save()
        self._run()
        self.assertFalse(
            Notification.objects.filter(user=self.user).exists()
        )


class GenerateWeeklyAiReportTest(TestCase):
    def setUp(self):
        self.user = make_user()
        self.subject = make_subject()

    def _run(self, user_id=None):
        from ai_core.tasks import generate_weekly_ai_report
        with patch('ai_core.tasks.get_ai_response', return_value='AI hisobot matni.'):
            generate_weekly_ai_report(user_id=user_id)

    def _make_this_week_attempt(self, percentage=70.0, slug='weekly-test'):
        test = make_test(self.user, self.subject, slug=slug)
        return make_attempt(self.user, test, percentage=percentage)

    def test_creates_recommendation_and_notification(self):
        """Bu hafta test ishlagan user → AIRecommendation + Notification."""
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._make_this_week_attempt(slug='wk-test-1')
        self._run(user_id=self.user.id)

        rec = AIRecommendation.objects.filter(
            user=self.user, recommendation_type='motivation'
        ).first()
        self.assertIsNotNone(rec)
        self.assertIn('Haftalik hisobot', rec.title)
        self.assertEqual(rec.content, 'AI hisobot matni.')

        notif = Notification.objects.filter(
            user=self.user, notification_type='system',
            title__startswith='📊 Haftalik'
        ).first()
        self.assertIsNotNone(notif)

    def test_skips_user_with_no_tests_this_week(self):
        """Bu hafta test ishlamagan → hech narsa yaratilmaydi."""
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._run(user_id=self.user.id)
        self.assertFalse(
            AIRecommendation.objects.filter(user=self.user).exists()
        )

    def test_no_duplicate_notification(self):
        """Ikki marta ishlatilsa faqat 1 ta notification."""
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._make_this_week_attempt(slug='wk-dup-1')
        self._run(user_id=self.user.id)
        self._run(user_id=self.user.id)
        count = Notification.objects.filter(
            user=self.user, title__startswith='📊 Haftalik'
        ).count()
        self.assertEqual(count, 1)

    def test_bulk_mode_processes_active_users(self):
        """user_id=None → last 7 kun faol userlar bilan ishlaydi."""
        user2 = make_user(phone='+998903333333')
        # user1: faol + test bor
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._make_this_week_attempt(slug='bulk-1')
        # user2: faol lekin test yo'q
        user2.last_activity_date = timezone.localdate()
        user2.save()
        self._run()
        # Faqat user1 uchun yaratilishi kerak
        self.assertTrue(
            AIRecommendation.objects.filter(user=self.user).exists()
        )
        self.assertFalse(
            AIRecommendation.objects.filter(user=user2).exists()
        )

    def test_ai_response_saved_in_recommendation(self):
        """get_ai_response qaytargan matn AIRecommendation.content ga saqlanadi."""
        self.user.last_activity_date = timezone.localdate()
        self.user.save()
        self._make_this_week_attempt(slug='wk-content-1')
        self._run(user_id=self.user.id)
        rec = AIRecommendation.objects.filter(user=self.user).first()
        self.assertEqual(rec.content, 'AI hisobot matni.')

    def test_inactive_user_not_processed_in_bulk(self):
        """last_activity 8 kun oldin → bulk mode da o'tkaziladi."""
        self.user.last_activity_date = timezone.localdate() - timedelta(days=8)
        self.user.save()
        self._make_this_week_attempt(slug='wk-old-1')
        self._run()
        self.assertFalse(
            AIRecommendation.objects.filter(user=self.user).exists()
        )
