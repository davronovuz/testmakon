"""
TestMakon.uz - Competitions App Tests
Barcha modellar va viewlar uchun mukammal testlar
"""

import json
import uuid
from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from tests_app.models import Answer, Question, Subject, Topic

from .models import (
    Battle,
    BattleInvitation,
    Certificate,
    Competition,
    CompetitionParticipant,
    CompetitionPayment,
    CompetitionQuestion,
    DailyChallenge,
    DailyChallengeParticipant,
    Friendship,
    MatchmakingQueue,
    WeeklyLeague,
    WeeklyLeagueParticipant,
)

User = get_user_model()


# ==============================================================
# BASE TEST CASE - Umumiy fixture yaratuvchi
# ==============================================================

class BaseTestCase(TestCase):
    """Barcha testlar uchun umumiy setup"""

    def setUp(self):
        self.client = Client()

        # Foydalanuvchilar
        self.user = User.objects.create_user(
            phone_number='+998901234567',
            password='testpass123',
            first_name='Ali',
            last_name='Valiyev',
        )
        self.user2 = User.objects.create_user(
            phone_number='+998901234568',
            password='testpass123',
            first_name='Vali',
            last_name='Aliyev',
        )
        self.user3 = User.objects.create_user(
            phone_number='+998901234569',
            password='testpass123',
            first_name='Soli',
            last_name='Karimov',
        )

        # Fan
        self.subject = Subject.objects.create(
            name='Matematika',
            slug='matematika',
            icon='📐',
            color='#3498db',
        )

        # Savollar va javoblar
        self.question1 = Question.objects.create(
            subject=self.subject,
            text='2 + 2 nechaga teng?',
            difficulty='easy',
        )
        self.answer_correct = Answer.objects.create(
            question=self.question1,
            text='4',
            is_correct=True,
            order=1,
        )
        self.answer_wrong = Answer.objects.create(
            question=self.question1,
            text='5',
            is_correct=False,
            order=2,
        )

        self.question2 = Question.objects.create(
            subject=self.subject,
            text='3 * 3 nechaga teng?',
            difficulty='easy',
        )
        self.answer2_correct = Answer.objects.create(
            question=self.question2,
            text='9',
            is_correct=True,
            order=1,
        )
        self.answer2_wrong = Answer.objects.create(
            question=self.question2,
            text='6',
            is_correct=False,
            order=2,
        )

        # Musobaqalar
        now = timezone.now()
        self.competition_upcoming = Competition.objects.create(
            title='Matematika Olimpiadasi',
            slug='matematika-olimpiadasi',
            description='Test musobaqasi',
            competition_type='olympiad',
            status='upcoming',
            entry_type='free',
            subject=self.subject,
            start_time=now + timedelta(hours=2),
            end_time=now + timedelta(hours=4),
            duration_minutes=120,
            created_by=self.user,
        )

        self.competition_active = Competition.objects.create(
            title='Faol Musobaqa',
            slug='faol-musobaqa',
            description='Faol musobaqa',
            competition_type='daily',
            status='active',
            entry_type='free',
            subject=self.subject,
            start_time=now - timedelta(hours=1),
            end_time=now + timedelta(hours=3),
            duration_minutes=60,
            created_by=self.user,
        )

        self.competition_finished = Competition.objects.create(
            title='Tugagan Musobaqa',
            slug='tugagan-musobaqa',
            description='Tugagan musobaqa',
            competition_type='weekly',
            status='finished',
            entry_type='free',
            subject=self.subject,
            start_time=now - timedelta(days=2),
            end_time=now - timedelta(days=1),
            duration_minutes=60,
            created_by=self.user,
        )

    def login(self, user=None):
        """Foydalanuvchini tizimga kirgazish"""
        if user is None:
            user = self.user
        self.client.login(
            username=user.phone_number,
            password='testpass123',
        )

    def make_battle(self, challenger=None, opponent=None, opponent_type='friend',
                    status='pending', bot_difficulty=''):
        """Battle yaratish uchun helper"""
        if challenger is None:
            challenger = self.user
        now = timezone.now()
        battle = Battle.objects.create(
            challenger=challenger,
            opponent=opponent,
            opponent_type=opponent_type,
            bot_difficulty=bot_difficulty,
            subject=self.subject,
            question_count=2,
            time_per_question=30,
            total_time=60,
            status=status,
            expires_at=now + timedelta(hours=1),
            questions_data=[
                {
                    'id': self.question1.id,
                    'text': self.question1.text,
                    'answers': [
                        {'id': self.answer_correct.id, 'text': '4', 'is_correct': True},
                        {'id': self.answer_wrong.id, 'text': '5', 'is_correct': False},
                    ],
                },
                {
                    'id': self.question2.id,
                    'text': self.question2.text,
                    'answers': [
                        {'id': self.answer2_correct.id, 'text': '9', 'is_correct': True},
                        {'id': self.answer2_wrong.id, 'text': '6', 'is_correct': False},
                    ],
                },
            ],
        )
        return battle


# ==============================================================
# MODEL TESTS
# ==============================================================

class CompetitionModelTest(BaseTestCase):
    """Competition modeli testlari"""

    def test_str(self):
        self.assertEqual(str(self.competition_upcoming), 'Matematika Olimpiadasi')

    def test_is_registration_open_by_status(self):
        """Status orqali ro'yxat ochiqligini tekshirish"""
        comp = self.competition_upcoming
        comp.status = 'registration'
        comp.registration_start = None
        comp.registration_end = None
        comp.save()
        self.assertTrue(comp.is_registration_open)

    def test_is_registration_open_by_dates(self):
        """Sana orqali ro'yxat ochiqligini tekshirish"""
        now = timezone.now()
        comp = self.competition_upcoming
        comp.registration_start = now - timedelta(hours=1)
        comp.registration_end = now + timedelta(hours=1)
        comp.save()
        self.assertTrue(comp.is_registration_open)

    def test_is_registration_closed(self):
        """Ro'yxat yopiq bo'lganda"""
        now = timezone.now()
        comp = self.competition_upcoming
        comp.registration_start = now - timedelta(hours=2)
        comp.registration_end = now - timedelta(hours=1)
        comp.save()
        self.assertFalse(comp.is_registration_open)

    def test_is_ongoing_true(self):
        """Davom etayotgan musobaqa"""
        self.assertTrue(self.competition_active.is_ongoing)

    def test_is_ongoing_false_status(self):
        """Status active bo'lmasa ongoing emas"""
        self.assertFalse(self.competition_upcoming.is_ongoing)

    def test_is_finished_true(self):
        """Tugagan musobaqa"""
        self.assertTrue(self.competition_finished.is_finished)

    def test_is_finished_by_time(self):
        """Vaqti o'tgan bo'lsa tugagan"""
        comp = self.competition_active
        comp.end_time = timezone.now() - timedelta(minutes=1)
        comp.save()
        self.assertTrue(comp.is_finished)

    def test_is_finished_false(self):
        """Tugamagan musobaqa"""
        self.assertFalse(self.competition_active.is_finished)

    def test_time_until_start_upcoming(self):
        """Kelayotgan musobaqada vaqt mavjud"""
        result = self.competition_upcoming.time_until_start
        self.assertIsNotNone(result)
        self.assertGreater(result.total_seconds(), 0)

    def test_time_until_start_not_upcoming(self):
        """Active musobaqada time_until_start None"""
        self.assertIsNone(self.competition_active.time_until_start)

    def test_time_remaining_active(self):
        """Davom etayotganda qolgan vaqt"""
        result = self.competition_active.time_remaining
        self.assertIsNotNone(result)
        self.assertGreater(result.total_seconds(), 0)

    def test_time_remaining_finished(self):
        """Tugaganda time_remaining None"""
        self.assertIsNone(self.competition_finished.time_remaining)

    def test_spots_left_unlimited(self):
        """Max qatnashchilar yo'q - None qaytaradi"""
        self.assertIsNone(self.competition_active.spots_left)

    def test_spots_left_limited(self):
        """Max qatnashchilar bor"""
        self.competition_active.max_participants = 100
        self.competition_active.participants_count = 40
        self.competition_active.save()
        self.assertEqual(self.competition_active.spots_left, 60)

    def test_spots_left_zero_when_full(self):
        """Joy qolmagan - 0 qaytaradi"""
        self.competition_active.max_participants = 10
        self.competition_active.participants_count = 10
        self.competition_active.save()
        self.assertEqual(self.competition_active.spots_left, 0)

    def test_get_prize_for_rank_found(self):
        """Mavjud o'rin uchun sovrin topiladi"""
        self.competition_active.prizes = [
            {'place': 1, 'amount': 500000, 'description': "1-o'rin"},
            {'place': 2, 'amount': 300000, 'description': "2-o'rin"},
        ]
        self.competition_active.save()
        prize = self.competition_active.get_prize_for_rank(1)
        self.assertIsNotNone(prize)
        self.assertEqual(prize['amount'], 500000)

    def test_get_prize_for_rank_not_found(self):
        """Mavjud bo'lmagan o'rin uchun None"""
        self.competition_active.prizes = [{'place': 1, 'amount': 500000}]
        self.competition_active.save()
        self.assertIsNone(self.competition_active.get_prize_for_rank(99))

    def test_has_manual_questions_false(self):
        """Qo'lda savol yo'q"""
        self.assertFalse(self.competition_active.has_manual_questions())

    def test_has_manual_questions_true(self):
        """Qo'lda savol bor"""
        CompetitionQuestion.objects.create(
            competition=self.competition_active,
            question=self.question1,
            order=1,
        )
        self.assertTrue(self.competition_active.has_manual_questions())

    def test_get_manual_questions_returns_list(self):
        """Qo'lda savollar ro'yxati to'g'ri qaytariladi"""
        CompetitionQuestion.objects.create(
            competition=self.competition_active,
            question=self.question1,
            order=1,
        )
        questions = self.competition_active.get_manual_questions()
        self.assertEqual(len(questions), 1)
        self.assertEqual(questions[0], self.question1)

    def test_uuid_auto_generated(self):
        """UUID avtomatik yaratiladi"""
        self.assertIsNotNone(self.competition_active.uuid)

    def test_default_fields(self):
        """Default maydonlar to'g'ri"""
        self.assertEqual(self.competition_active.participants_count, 0)
        self.assertEqual(self.competition_active.completed_count, 0)
        self.assertEqual(self.competition_active.average_score, 0)
        self.assertTrue(self.competition_active.show_live_leaderboard)
        self.assertTrue(self.competition_active.anti_cheat_enabled)

    def test_ordering_by_start_time_desc(self):
        """Musobaqalar start_time kamayish tartibida"""
        comps = list(Competition.objects.all())
        times = [c.start_time for c in comps]
        self.assertEqual(times, sorted(times, reverse=True))


class CompetitionQuestionModelTest(BaseTestCase):
    """CompetitionQuestion modeli testlari"""

    def setUp(self):
        super().setUp()
        self.comp_question = CompetitionQuestion.objects.create(
            competition=self.competition_active,
            question=self.question1,
            order=1,
        )

    def test_str(self):
        result = str(self.comp_question)
        self.assertIn('Faol Musobaqa', result)
        self.assertIn('#1', result)

    def test_unique_together_prevents_duplicate(self):
        """Bir musobaqaga bir savol ikki marta kiritilmaydi"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CompetitionQuestion.objects.create(
                competition=self.competition_active,
                question=self.question1,
                order=2,
            )

    def test_ordering_by_order_field(self):
        """order maydoni bo'yicha saralash"""
        CompetitionQuestion.objects.create(
            competition=self.competition_active,
            question=self.question2,
            order=2,
        )
        qs = list(CompetitionQuestion.objects.filter(competition=self.competition_active))
        self.assertEqual(qs[0].order, 1)
        self.assertEqual(qs[1].order, 2)


class CompetitionParticipantModelTest(BaseTestCase):
    """CompetitionParticipant modeli testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='registered',
        )

    def test_str(self):
        result = str(self.participant)
        self.assertIn(str(self.user), result)

    def test_add_violation_increments_count(self):
        """Qoidabuzarlik soni ortishi"""
        self.participant.add_violation('tab_switch', 'Tab almashtirildi')
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.violations_count, 1)

    def test_add_violation_saves_log(self):
        """Qoidabuzarlik loga yoziladi"""
        self.participant.add_violation('copy_paste', {'text': 'test'})
        self.participant.refresh_from_db()
        self.assertEqual(len(self.participant.violations_log), 1)
        self.assertEqual(self.participant.violations_log[0]['type'], 'copy_paste')
        self.assertIn('timestamp', self.participant.violations_log[0])

    def test_disqualified_after_3_violations(self):
        """3 qoidabuzarlikdan keyin diskvalifikatsiya"""
        self.participant.add_violation('type1')
        self.participant.add_violation('type2')
        self.participant.add_violation('type3')
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'disqualified')

    def test_not_disqualified_after_2_violations(self):
        """2 qoidabuzarlikda diskvalifikatsiya yo'q"""
        self.participant.add_violation('type1')
        self.participant.add_violation('type2')
        self.participant.refresh_from_db()
        self.assertNotEqual(self.participant.status, 'disqualified')

    def test_unique_together_prevents_duplicate(self):
        """Bir foydalanuvchi bir musobaqaga bir marta"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CompetitionParticipant.objects.create(
                competition=self.competition_active,
                user=self.user,
            )

    def test_default_status_registered(self):
        """Default status - registered"""
        self.assertEqual(self.participant.status, 'registered')

    def test_default_score_zero(self):
        """Default ball - 0"""
        self.assertEqual(self.participant.score, 0)
        self.assertEqual(self.participant.correct_answers, 0)


class CompetitionPaymentModelTest(BaseTestCase):
    """CompetitionPayment modeli testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='registered',
        )
        self.payment = CompetitionPayment.objects.create(
            participant=self.participant,
            amount=50000,
            status='pending',
        )

    def test_str_contains_amount(self):
        result = str(self.payment)
        self.assertIn('50000', result)
        self.assertIn("so'm", result)

    def test_uuid_auto_generated(self):
        self.assertIsNotNone(self.payment.uuid)

    def test_status_update(self):
        """To'lov holati yangilanadi"""
        self.payment.status = 'completed'
        self.payment.save()
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, 'completed')

    def test_default_status_pending(self):
        """Default holat - pending"""
        self.assertEqual(self.payment.status, 'pending')


class CertificateModelTest(BaseTestCase):
    """Certificate modeli testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_finished,
            user=self.user,
            status='completed',
            score=85,
            rank=1,
        )

    def _make_cert(self, **kwargs):
        defaults = dict(
            user=self.user,
            competition=self.competition_finished,
            participant=self.participant,
            certificate_type='participation',
            score=70,
        )
        defaults.update(kwargs)
        return Certificate.objects.create(**defaults)

    def test_verification_code_auto_generated(self):
        """Tasdiqlash kodi avtomatik yaratiladi"""
        cert = self._make_cert()
        self.assertTrue(cert.verification_code.startswith('TM-'))
        self.assertGreater(len(cert.verification_code), 3)

    def test_str_contains_user_and_competition(self):
        cert = self._make_cert()
        result = str(cert)
        self.assertIn(str(self.user), result)
        self.assertIn('Tugagan Musobaqa', result)

    def test_unique_together_user_competition(self):
        """Bir foydalanuvchi bir musobaqaga faqat bitta sertifikat"""
        from django.db import IntegrityError
        self._make_cert()
        with self.assertRaises(IntegrityError):
            Certificate.objects.create(
                user=self.user,
                competition=self.competition_finished,
                certificate_type='winner',
                score=85,
            )

    def test_verification_code_not_overwritten_on_save(self):
        """Mavjud kod qayta yozilmaydi"""
        cert = self._make_cert()
        original_code = cert.verification_code
        cert.score = 80
        cert.save()
        self.assertEqual(cert.verification_code, original_code)

    def test_default_is_verified_true(self):
        """Default - tasdiqlangan"""
        cert = self._make_cert()
        self.assertTrue(cert.is_verified)


class BattleModelTest(BaseTestCase):
    """Battle modeli testlari"""

    def test_str_with_real_opponent(self):
        """Haqiqiy raqib bilan __str__"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        result = str(battle)
        self.assertIn('vs', result)

    def test_invite_code_auto_generated_for_friend(self):
        """Do'stga taklif uchun kod yaratiladi"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        self.assertIsNotNone(battle.invite_code)
        self.assertEqual(len(battle.invite_code), 10)

    def test_invite_code_not_generated_for_random(self):
        """Random battle uchun invite_code yo'q"""
        battle = self.make_battle(opponent_type='random')
        self.assertIsNone(battle.invite_code)

    def test_invite_url_with_code(self):
        """Invite URL kodi mavjud bo'lganda"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        url = battle.invite_url
        self.assertIsNotNone(url)
        self.assertIn(battle.invite_code, url)

    def test_invite_url_without_code_is_none(self):
        """Invite kod yo'q bo'lganda URL None"""
        battle = self.make_battle(opponent_type='random')
        self.assertIsNone(battle.invite_url)

    def test_simulate_bot_answers_easy(self):
        """Oson bot javoblarini simulyatsiya qiladi"""
        battle = self.make_battle(opponent_type='bot', bot_difficulty='easy')
        battle.simulate_bot_answers()
        battle.refresh_from_db()
        self.assertTrue(battle.opponent_completed)
        self.assertEqual(len(battle.opponent_answers), 2)
        self.assertGreaterEqual(battle.opponent_correct, 0)
        self.assertLessEqual(battle.opponent_correct, 2)

    def test_simulate_bot_answers_expert(self):
        """Ekspert bot ko'proq to'g'ri javob beradi (probabilistik)"""
        correct_counts = []
        for _ in range(10):
            battle = self.make_battle(opponent_type='bot', bot_difficulty='expert')
            battle.simulate_bot_answers()
            battle.refresh_from_db()
            correct_counts.append(battle.opponent_correct)
            battle.delete()
        avg_correct = sum(correct_counts) / len(correct_counts)
        # Ekspert bot o'rtacha kamida 1 to'g'ri javob berishi kerak (2 savoldan)
        self.assertGreaterEqual(avg_correct, 1.0)

    def test_simulate_bot_skipped_for_non_bot(self):
        """Bot emas battle uchun simulyatsiya ishlamaydi"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.simulate_bot_answers()
        battle.refresh_from_db()
        self.assertFalse(battle.opponent_completed)

    def test_determine_winner_challenger_more_correct(self):
        """Challenger ko'proq to'g'ri javob - yutuvchi"""
        battle = self.make_battle(opponent_type='bot', bot_difficulty='easy')
        battle.challenger_completed = True
        battle.challenger_correct = 2
        battle.challenger_time = 50
        battle.opponent_answers = [
            {'question_id': self.question1.id, 'answer_id': self.answer_wrong.id,
             'is_correct': False, 'time': 10},
            {'question_id': self.question2.id, 'answer_id': self.answer2_wrong.id,
             'is_correct': False, 'time': 10},
        ]
        battle.opponent_correct = 0
        battle.opponent_time = 20
        battle.opponent_completed = True
        battle.save()
        battle.determine_winner()
        battle.refresh_from_db()
        self.assertEqual(battle.status, 'completed')
        self.assertEqual(battle.winner, self.user)

    def test_determine_winner_by_time_on_tie(self):
        """Ball teng bo'lsa tezroq vaqt - yutuvchi"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.challenger_completed = True
        battle.challenger_correct = 1
        battle.challenger_time = 20  # Tezroq
        battle.opponent_completed = True
        battle.opponent_correct = 1
        battle.opponent_time = 40  # Sekinroq
        battle.save()
        battle.determine_winner()
        battle.refresh_from_db()
        self.assertEqual(battle.winner, self.user)

    def test_determine_winner_draw(self):
        """Durrang holati"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.challenger_completed = True
        battle.challenger_correct = 1
        battle.challenger_time = 30
        battle.opponent_completed = True
        battle.opponent_correct = 1
        battle.opponent_time = 30
        battle.save()
        battle.determine_winner()
        battle.refresh_from_db()
        self.assertTrue(battle.is_draw)
        self.assertEqual(battle.status, 'completed')

    def test_determine_winner_not_called_if_incomplete(self):
        """Challenger tugamasa winner aniqlanmaydi"""
        battle = self.make_battle(opponent=self.user2)
        battle.determine_winner()
        battle.refresh_from_db()
        self.assertNotEqual(battle.status, 'completed')

    def test_award_xp_winner_receives_more(self):
        """G'olib ko'proq XP oladi"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.winner_xp = 50
        battle.loser_xp = 10
        battle.winner = self.user
        battle.is_draw = False
        battle.status = 'completed'
        battle.challenger_completed = True
        battle.opponent_completed = True
        battle.save()

        initial_user1 = self.user.xp_points
        initial_user2 = self.user2.xp_points
        battle.award_xp()

        self.user.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertEqual(self.user.xp_points, initial_user1 + 50)
        self.assertEqual(self.user2.xp_points, initial_user2 + 10)

    def test_award_xp_draw_equal_distribution(self):
        """Durrangda teng XP"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.winner_xp = 50
        battle.loser_xp = 10
        battle.is_draw = True
        battle.save()

        draw_xp = (50 + 10) // 2
        initial_user1 = self.user.xp_points
        initial_user2 = self.user2.xp_points
        battle.award_xp()

        self.user.refresh_from_db()
        self.user2.refresh_from_db()
        self.assertEqual(self.user.xp_points, initial_user1 + draw_xp)
        self.assertEqual(self.user2.xp_points, initial_user2 + draw_xp)

    def test_award_xp_not_awarded_twice(self):
        """XP ikki marta berilmaydi"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.winner = self.user
        battle.xp_awarded = True
        battle.winner_xp = 50
        battle.save()
        initial_xp = self.user.xp_points
        battle.award_xp()
        self.user.refresh_from_db()
        self.assertEqual(self.user.xp_points, initial_xp)

    def test_uuid_auto_generated(self):
        """UUID avtomatik yaratiladi"""
        battle = self.make_battle()
        self.assertIsNotNone(battle.uuid)

    def test_ordering_by_created_at_desc(self):
        """Janglar created_at kamayish tartibida"""
        b1 = self.make_battle(challenger=self.user)
        b2 = self.make_battle(challenger=self.user2)
        battles = list(Battle.objects.all())
        self.assertGreaterEqual(battles[0].created_at, battles[-1].created_at)


class MatchmakingQueueModelTest(BaseTestCase):
    """MatchmakingQueue modeli testlari"""

    def test_str(self):
        queue = MatchmakingQueue.objects.create(
            user=self.user,
            subject=self.subject,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        result = str(queue)
        self.assertIn(str(self.user), result)

    def test_find_match_returns_none_when_empty(self):
        """Navbat bo'sh - None qaytaradi"""
        result = MatchmakingQueue.find_match(self.user, self.subject)
        self.assertIsNone(result)

    def test_find_match_returns_opponent(self):
        """Mos raqib topiladi"""
        MatchmakingQueue.objects.create(
            user=self.user2,
            subject=self.subject,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
            is_matched=False,
        )
        result = MatchmakingQueue.find_match(self.user, self.subject)
        self.assertIsNotNone(result)
        self.assertEqual(result.user, self.user2)

    def test_find_match_excludes_self(self):
        """O'zini raqib sifatida topmaydi"""
        MatchmakingQueue.objects.create(
            user=self.user,
            subject=self.subject,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        result = MatchmakingQueue.find_match(self.user, self.subject)
        self.assertIsNone(result)

    def test_find_match_excludes_expired(self):
        """Muddati o'tgan navbat chiqarib tashlanadi"""
        MatchmakingQueue.objects.create(
            user=self.user2,
            subject=self.subject,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() - timedelta(seconds=1),
        )
        result = MatchmakingQueue.find_match(self.user)
        self.assertIsNone(result)

    def test_find_match_excludes_already_matched(self):
        """Allaqachon topilgan chiqarib tashlanadi"""
        MatchmakingQueue.objects.create(
            user=self.user2,
            subject=self.subject,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
            is_matched=True,
        )
        result = MatchmakingQueue.find_match(self.user)
        self.assertIsNone(result)

    def test_find_match_rating_range(self):
        """Reyting oralig'idan tashqari - topilmaydi"""
        MatchmakingQueue.objects.create(
            user=self.user2,
            subject=self.subject,
            user_rating=1500,  # 200 dan ko'p farq
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
            is_matched=False,
        )
        # user ning reyting 1000 (default), 1500 - 1000 = 500 > 200
        result = MatchmakingQueue.find_match(self.user)
        self.assertIsNone(result)


class BattleInvitationModelTest(BaseTestCase):
    """BattleInvitation modeli testlari"""

    def test_create_invitation(self):
        """Taklif yaratish"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        invitation = BattleInvitation.objects.create(
            battle=battle,
            invited_user=self.user2,
            status='pending',
        )
        self.assertEqual(invitation.status, 'pending')
        self.assertEqual(invitation.battle, battle)
        self.assertFalse(invitation.notification_sent)

    def test_default_status_pending(self):
        """Default holat - pending"""
        battle = self.make_battle(opponent=self.user2)
        inv = BattleInvitation.objects.create(battle=battle, invited_user=self.user2)
        self.assertEqual(inv.status, 'pending')


class DailyChallengeModelTest(BaseTestCase):
    """DailyChallenge modeli testlari"""

    def setUp(self):
        super().setUp()
        today = timezone.now().date()
        self.challenge = DailyChallenge.objects.create(
            date=today,
            subject=self.subject,
            question_count=10,
            time_limit=15,
            xp_reward=100,
        )
        self.challenge.questions.add(self.question1, self.question2)

    def test_str(self):
        result = str(self.challenge)
        self.assertIn('Challenge', result)
        self.assertIn(str(self.challenge.date), result)

    def test_unique_date_constraint(self):
        """Bir kunda faqat bitta challenge"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DailyChallenge.objects.create(
                date=self.challenge.date,
                subject=self.subject,
                question_count=5,
                time_limit=10,
            )

    def test_questions_m2m_count(self):
        """Savollar M2M bog'lanishi ishlaydi"""
        self.assertEqual(self.challenge.questions.count(), 2)

    def test_is_active_default_true(self):
        """Default - faol"""
        self.assertTrue(self.challenge.is_active)

    def test_ordering_by_date_desc(self):
        """Sana kamayish tartibida"""
        yesterday = timezone.now().date() - timedelta(days=1)
        old_challenge = DailyChallenge.objects.create(
            date=yesterday,
            question_count=5,
            time_limit=10,
        )
        challenges = list(DailyChallenge.objects.all())
        self.assertEqual(challenges[0], self.challenge)


class DailyChallengeParticipantModelTest(BaseTestCase):
    """DailyChallengeParticipant modeli testlari"""

    def setUp(self):
        super().setUp()
        today = timezone.now().date()
        self.challenge = DailyChallenge.objects.create(
            date=today,
            subject=self.subject,
            question_count=5,
            time_limit=10,
        )
        self.dc_participant = DailyChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user,
            score=80,
            correct_answers=8,
            wrong_answers=2,
        )

    def test_str(self):
        result = str(self.dc_participant)
        self.assertIn(str(self.user), result)
        self.assertIn(str(self.challenge.date), result)

    def test_unique_together_prevents_duplicate(self):
        """Bir foydalanuvchi bir challengega bir marta"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            DailyChallengeParticipant.objects.create(
                challenge=self.challenge,
                user=self.user,
                score=50,
            )

    def test_default_values(self):
        """Default maydonlar"""
        p = DailyChallengeParticipant.objects.create(
            challenge=self.challenge,
            user=self.user2,
        )
        self.assertEqual(p.score, 0)
        self.assertEqual(p.xp_earned, 0)


class WeeklyLeagueModelTest(BaseTestCase):
    """WeeklyLeague modeli testlari"""

    def setUp(self):
        super().setUp()
        today = date.today()
        self.league = WeeklyLeague.objects.create(
            week_start=today,
            week_end=today + timedelta(days=6),
            tier='gold',
            xp_reward_first=300,
        )

    def test_str_contains_tier_and_date(self):
        result = str(self.league)
        self.assertIn('Oltin', result)
        self.assertIn('Liga', result)

    def test_tier_display_uzbek(self):
        """Daraja o'zbekcha ko'rinadi"""
        self.assertEqual(self.league.get_tier_display(), 'Oltin')

    def test_ordering_newest_first(self):
        """Yangi ligalar birinchi"""
        today = date.today()
        old_league = WeeklyLeague.objects.create(
            week_start=today - timedelta(weeks=1),
            week_end=today - timedelta(days=1),
            tier='silver',
        )
        leagues = list(WeeklyLeague.objects.all())
        self.assertEqual(leagues[0], self.league)

    def test_default_is_active_true(self):
        """Default - faol"""
        self.assertTrue(self.league.is_active)

    def test_default_is_processed_false(self):
        """Default - hisoblanmagan"""
        self.assertFalse(self.league.is_processed)


class WeeklyLeagueParticipantModelTest(BaseTestCase):
    """WeeklyLeagueParticipant modeli testlari"""

    def setUp(self):
        super().setUp()
        today = date.today()
        self.league = WeeklyLeague.objects.create(
            week_start=today,
            week_end=today + timedelta(days=6),
            tier='bronze',
        )
        self.league_participant = WeeklyLeagueParticipant.objects.create(
            league=self.league,
            user=self.user,
            xp_earned=500,
            tests_completed=10,
        )

    def test_str(self):
        result = str(self.league_participant)
        self.assertIn(str(self.user), result)

    def test_unique_together_prevents_duplicate(self):
        """Bir foydalanuvchi bir ligaga bir marta"""
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            WeeklyLeagueParticipant.objects.create(
                league=self.league,
                user=self.user,
                xp_earned=100,
            )

    def test_default_promotion_demotion_false(self):
        """Default - ko'tarilmagan, tushmagan"""
        self.assertFalse(self.league_participant.is_promoted)
        self.assertFalse(self.league_participant.is_demoted)


class FriendshipModelTest(BaseTestCase):
    """Friendship modeli testlari"""

    def test_str_contains_both_users(self):
        friendship = Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='pending',
        )
        result = str(friendship)
        self.assertIn(str(self.user), result)
        self.assertIn(str(self.user2), result)

    def test_are_friends_accepted_both_directions(self):
        """Do'stlar bo'lsa har ikki tomonda True"""
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted',
        )
        self.assertTrue(Friendship.are_friends(self.user, self.user2))
        self.assertTrue(Friendship.are_friends(self.user2, self.user))

    def test_are_friends_false_when_pending(self):
        """Pending status - do'st emas"""
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='pending',
        )
        self.assertFalse(Friendship.are_friends(self.user, self.user2))

    def test_are_friends_false_no_relation(self):
        """Munosabat yo'q - False"""
        self.assertFalse(Friendship.are_friends(self.user, self.user2))

    def test_get_friends_both_directions(self):
        """Do'stlar ro'yxati (from va to yo'nalishlarida)"""
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted',
        )
        Friendship.objects.create(
            from_user=self.user3,
            to_user=self.user,
            status='accepted',
        )
        friends = Friendship.get_friends(self.user)
        self.assertIn(self.user2, friends)
        self.assertIn(self.user3, friends)
        self.assertNotIn(self.user, friends)

    def test_get_friends_empty_list(self):
        """Do'st yo'q - bo'sh queryset"""
        friends = Friendship.get_friends(self.user)
        self.assertEqual(friends.count(), 0)

    def test_get_pending_requests(self):
        """Kutilayotgan so'rovlar"""
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user,
            status='pending',
        )
        Friendship.objects.create(
            from_user=self.user3,
            to_user=self.user,
            status='pending',
        )
        pending = Friendship.get_pending_requests(self.user)
        self.assertEqual(pending.count(), 2)

    def test_send_request_new_friendship(self):
        """Yangi do'stlik so'rovi"""
        friendship, msg = Friendship.send_request(self.user, self.user2)
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, 'pending')
        self.assertEqual(friendship.from_user, self.user)

    def test_send_request_to_self_returns_none(self):
        """O'ziga so'rov - None"""
        result, msg = Friendship.send_request(self.user, self.user)
        self.assertIsNone(result)

    def test_send_request_already_friends_returns_none(self):
        """Allaqachon do'st - None"""
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='accepted',
        )
        result, msg = Friendship.send_request(self.user, self.user2)
        self.assertIsNone(result)

    def test_send_request_auto_accept_reverse(self):
        """Raqib yuborgan so'rovga avtomatik qabul"""
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user,
            status='pending',
        )
        friendship, msg = Friendship.send_request(self.user, self.user2)
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, 'accepted')

    def test_send_request_resend_after_decline(self):
        """Rad etilgan so'rovni qayta yuborish"""
        Friendship.objects.create(
            from_user=self.user2,
            to_user=self.user,
            status='declined',
        )
        friendship, msg = Friendship.send_request(self.user, self.user2)
        self.assertIsNotNone(friendship)
        self.assertEqual(friendship.status, 'pending')

    def test_unique_together_prevents_duplicate(self):
        """Bir juftlik ikki marta yaratilmaydi"""
        from django.db import IntegrityError
        Friendship.objects.create(
            from_user=self.user,
            to_user=self.user2,
            status='pending',
        )
        with self.assertRaises(IntegrityError):
            Friendship.objects.create(
                from_user=self.user,
                to_user=self.user2,
                status='pending',
            )


# ==============================================================
# VIEW TESTS
# ==============================================================

class CompetitionsListViewTest(BaseTestCase):
    """competitions_list view testlari"""

    def test_status_200_anonymous(self):
        """Tizimga kirmagan ham ko'radi"""
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertEqual(response.status_code, 200)

    def test_status_200_authenticated(self):
        """Tizimga kirgan ham ko'radi"""
        self.login()
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertEqual(response.status_code, 200)

    def test_all_context_keys_present(self):
        """Barcha context kalitlari mavjud"""
        self.login()
        response = self.client.get(reverse('competitions:competitions_list'))
        for key in ['featured', 'active', 'registration_open', 'finished',
                    'daily_challenge', 'daily_completed', 'user_stats', 'user_battles']:
            self.assertIn(key, response.context, f"'{key}' context da yo'q")

    def test_active_competitions_in_context(self):
        """Faol musobaqalar contextda"""
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertIn(self.competition_active, list(response.context['active']))

    def test_finished_competitions_in_context(self):
        """Tugagan musobaqalar contextda"""
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertIn(self.competition_finished, list(response.context['finished']))

    def test_daily_challenge_shown_in_context(self):
        """Kunlik challenge contextda"""
        today = timezone.now().date()
        challenge = DailyChallenge.objects.create(
            date=today, subject=self.subject, question_count=5, time_limit=10,
        )
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertEqual(response.context['daily_challenge'], challenge)

    def test_daily_completed_false_for_new_user(self):
        """Yangi foydalanuvchi uchun daily_completed False"""
        today = timezone.now().date()
        DailyChallenge.objects.create(
            date=today, subject=self.subject, question_count=5, time_limit=10,
        )
        self.login()
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertFalse(response.context['daily_completed'])

    def test_daily_completed_true_when_done(self):
        """Qatnashgan bo'lsa daily_completed True"""
        today = timezone.now().date()
        challenge = DailyChallenge.objects.create(
            date=today, subject=self.subject, question_count=5, time_limit=10,
        )
        DailyChallengeParticipant.objects.create(
            challenge=challenge, user=self.user, score=80,
        )
        self.login()
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertTrue(response.context['daily_completed'])

    def test_user_stats_none_for_anonymous(self):
        """Anonim foydalanuvchi uchun user_stats None"""
        response = self.client.get(reverse('competitions:competitions_list'))
        self.assertIsNone(response.context['user_stats'])


class CompetitionDetailViewTest(BaseTestCase):
    """competition_detail view testlari"""

    def test_status_200_existing_competition(self):
        """Mavjud musobaqani ko'rish"""
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_status_404_nonexistent_competition(self):
        """Mavjud bo'lmagan musobaqa - 404"""
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': 'mavjud-emas'})
        )
        self.assertEqual(response.status_code, 404)

    def test_status_404_inactive_competition(self):
        """Faol bo'lmagan musobaqa - 404"""
        self.competition_active.is_active = False
        self.competition_active.save()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_all_context_keys_present(self):
        """Barcha context kalitlari"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        for key in ['competition', 'is_participant', 'participant',
                    'can_join', 'can_start', 'leaderboard',
                    'participants_count', 'time_info']:
            self.assertIn(key, response.context, f"'{key}' context da yo'q")

    def test_is_participant_false_for_non_member(self):
        """Qatnashchi bo'lmagan - False"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertFalse(response.context['is_participant'])

    def test_is_participant_true_for_member(self):
        """Qatnashchi bo'lgan - True"""
        CompetitionParticipant.objects.create(
            competition=self.competition_active, user=self.user,
        )
        self.login()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertTrue(response.context['is_participant'])

    def test_can_join_true_for_free_active_competition(self):
        """Bepul faol musobaqaga qo'shilish mumkin"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertTrue(response.context['can_join'])

    def test_can_join_false_if_already_participant(self):
        """Allaqachon qatnashchi bo'lsa can_join False"""
        CompetitionParticipant.objects.create(
            competition=self.competition_active, user=self.user,
        )
        self.login()
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertFalse(response.context['can_join'])

    def test_competition_in_context(self):
        """Musobaqa objecti contextda"""
        response = self.client.get(
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.context['competition'], self.competition_active)


class CompetitionJoinViewTest(BaseTestCase):
    """competition_join view testlari"""

    def test_redirects_to_login_if_anonymous(self):
        """Login talab qilinadi"""
        response = self.client.post(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertRedirects(
            response,
            f'/accounts/login/?next=/competitions/{self.competition_upcoming.slug}/join/',
            fetch_redirect_response=False,
        )

    def test_join_creates_participant(self):
        """Qo'shilish participant yaratadi"""
        self.login()
        self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertTrue(
            CompetitionParticipant.objects.filter(
                competition=self.competition_upcoming,
                user=self.user,
            ).exists()
        )

    def test_join_participant_status_registered(self):
        """Qo'shilgandan so'ng status - registered"""
        self.login()
        self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        p = CompetitionParticipant.objects.get(
            competition=self.competition_upcoming, user=self.user,
        )
        self.assertEqual(p.status, 'registered')

    def test_cannot_join_twice(self):
        """Ikki marta qo'shilish mumkin emas"""
        self.login()
        CompetitionParticipant.objects.create(
            competition=self.competition_upcoming, user=self.user,
        )
        response = self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertRedirects(
            response,
            reverse('competitions:competition_detail',
                    kwargs={'slug': self.competition_upcoming.slug}),
            fetch_redirect_response=False,
        )
        self.assertEqual(
            CompetitionParticipant.objects.filter(
                competition=self.competition_upcoming, user=self.user,
            ).count(), 1,
        )

    def test_cannot_join_when_full(self):
        """Joy tugagan - qo'shilish mumkin emas"""
        self.competition_upcoming.max_participants = 1
        self.competition_upcoming.participants_count = 1
        self.competition_upcoming.save()
        self.login()
        self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertFalse(
            CompetitionParticipant.objects.filter(
                competition=self.competition_upcoming, user=self.user,
            ).exists()
        )

    def test_premium_only_blocks_free_user(self):
        """Premium musobaqaga oddiy foydalanuvchi kira olmaydi"""
        self.competition_upcoming.entry_type = 'premium_only'
        self.competition_upcoming.save()
        self.user.is_premium = False
        self.user.save()
        self.login()
        self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertFalse(
            CompetitionParticipant.objects.filter(
                competition=self.competition_upcoming, user=self.user,
            ).exists()
        )

    def test_paid_competition_redirects_to_payment(self):
        """Pullik musobaqa - to'lov sahifasiga"""
        self.competition_upcoming.entry_type = 'paid'
        self.competition_upcoming.entry_fee = 50000
        self.competition_upcoming.save()
        self.login()
        response = self.client.get(
            reverse('competitions:competition_join',
                    kwargs={'slug': self.competition_upcoming.slug})
        )
        self.assertRedirects(
            response,
            reverse('competitions:competition_payment',
                    kwargs={'slug': self.competition_upcoming.slug}),
            fetch_redirect_response=False,
        )


class CompetitionSubmitViewTest(BaseTestCase):
    """competition_submit view testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='in_progress',
        )

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.post(
            reverse('competitions:competition_submit',
                    kwargs={'slug': self.competition_active.slug}),
            data={'answers': '[]', 'time_spent': '60'},
        )
        self.assertEqual(response.status_code, 302)

    def test_submit_marks_participant_completed(self):
        """Submit - participant 'completed' holatiga o'tadi"""
        self.login()
        session = self.client.session
        session['competition_questions'] = [
            {
                'id': self.question1.id,
                'answers': [
                    {'id': self.answer_correct.id, 'is_correct': True},
                    {'id': self.answer_wrong.id, 'is_correct': False},
                ],
            }
        ]
        session['competition_id'] = self.competition_active.id
        session.save()

        answers_data = json.dumps([
            {'question_id': self.question1.id, 'answer_id': self.answer_correct.id}
        ])
        self.client.post(
            reverse('competitions:competition_submit',
                    kwargs={'slug': self.competition_active.slug}),
            data={'answers': answers_data, 'time_spent': '120'},
        )
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.status, 'completed')

    def test_submit_redirects_to_result(self):
        """Submit - result sahifasiga yo'naltiradi"""
        self.login()
        session = self.client.session
        session['competition_questions'] = []
        session.save()

        response = self.client.post(
            reverse('competitions:competition_submit',
                    kwargs={'slug': self.competition_active.slug}),
            data={'answers': '[]', 'time_spent': '0'},
        )
        self.assertRedirects(
            response,
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug}),
            fetch_redirect_response=False,
        )

    def test_already_completed_redirects_to_result(self):
        """Allaqachon tugallangan - result sahifasiga"""
        self.login()
        self.participant.status = 'completed'
        self.participant.save()
        response = self.client.post(
            reverse('competitions:competition_submit',
                    kwargs={'slug': self.competition_active.slug}),
            data={'answers': '[]', 'time_spent': '0'},
        )
        self.assertRedirects(
            response,
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug}),
            fetch_redirect_response=False,
        )

    def test_correct_answers_counted(self):
        """To'g'ri javoblar hisoblanadi"""
        self.login()
        session = self.client.session
        session['competition_questions'] = [
            {
                'id': self.question1.id,
                'answers': [
                    {'id': self.answer_correct.id, 'is_correct': True},
                    {'id': self.answer_wrong.id, 'is_correct': False},
                ],
            }
        ]
        session.save()
        answers_data = json.dumps([
            {'question_id': self.question1.id, 'answer_id': self.answer_correct.id}
        ])
        self.client.post(
            reverse('competitions:competition_submit',
                    kwargs={'slug': self.competition_active.slug}),
            data={'answers': answers_data, 'time_spent': '60'},
        )
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.correct_answers, 1)


class CompetitionResultViewTest(BaseTestCase):
    """competition_result view testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='completed',
            score=75,
            percentage=75.0,
            correct_answers=6,
            wrong_answers=2,
            time_spent=300,
        )

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_status_200(self):
        """Natija sahifasi 200"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_rank_auto_calculated(self):
        """Rank avtomatik hisoblanadi"""
        self.login()
        self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.participant.refresh_from_db()
        self.assertIsNotNone(self.participant.rank)

    def test_context_keys_present(self):
        """Context kalitlari"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        for key in ['competition', 'participant', 'leaderboard', 'user_rank_in_list']:
            self.assertIn(key, response.context, f"'{key}' context da yo'q")

    def test_non_participant_returns_404(self):
        """Qatnashchi bo'lmagan foydalanuvchi - 404"""
        self.login(self.user2)
        response = self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 404)

    def test_rank_1_when_alone(self):
        """Yolg'iz qatnashchi - 1-o'rin"""
        self.login()
        self.client.get(
            reverse('competitions:competition_result',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.rank, 1)


class CompetitionLeaderboardViewTest(BaseTestCase):
    """competition_leaderboard view testlari"""

    def test_status_200_anonymous(self):
        """Tizimga kirmagan ham ko'radi"""
        response = self.client.get(
            reverse('competitions:competition_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_status_200_authenticated(self):
        """Tizimga kirgan ham ko'radi"""
        self.login()
        response = self.client.get(
            reverse('competitions:competition_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_context_keys_present(self):
        """Context kalitlari"""
        response = self.client.get(
            reverse('competitions:competition_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        for key in ['competition', 'participants', 'user_participant']:
            self.assertIn(key, response.context)

    def test_pagination_page_1(self):
        """Birinchi sahifa"""
        response = self.client.get(
            reverse('competitions:competition_leaderboard',
                    kwargs={'slug': self.competition_active.slug}) + '?page=1'
        )
        self.assertEqual(response.status_code, 200)

    def test_user_participant_shown_when_authenticated(self):
        """Login qilgan foydalanuvchining participant ko'rinadi"""
        participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='completed',
            score=80,
        )
        self.login()
        response = self.client.get(
            reverse('competitions:competition_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.context['user_participant'], participant)


class BattlesListViewTest(BaseTestCase):
    """battles_list view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:battles_list'))
        self.assertEqual(response.status_code, 302)

    def test_status_200_authenticated(self):
        """Tizimga kirgan ko'radi"""
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        self.assertEqual(response.status_code, 200)

    def test_all_context_keys_present(self):
        """Barcha context kalitlari"""
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        for key in ['pending_received', 'pending_sent', 'active', 'completed', 'friends', 'stats']:
            self.assertIn(key, response.context, f"'{key}' context da yo'q")

    def test_pending_received_shows_incoming(self):
        """Kelgan takliflar ko'rinadi"""
        self.make_battle(challenger=self.user2, opponent=self.user, status='pending')
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        self.assertEqual(len(response.context['pending_received']), 1)

    def test_pending_sent_shows_outgoing(self):
        """Yuborilgan takliflar ko'rinadi"""
        self.make_battle(challenger=self.user, opponent=self.user2, status='pending')
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        self.assertEqual(len(response.context['pending_sent']), 1)

    def test_stats_keys_present(self):
        """Stats kalitlari"""
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        stats = response.context['stats']
        for key in ['total', 'won', 'lost', 'draw']:
            self.assertIn(key, stats)

    def test_stats_won_count_correct(self):
        """G'alaba soni to'g'ri"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2, status='completed')
        battle.winner = self.user
        battle.save()
        self.login()
        response = self.client.get(reverse('competitions:battles_list'))
        self.assertEqual(response.context['stats']['won'], 1)


class BattleCreateViewTest(BaseTestCase):
    """battle_create view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:battle_create'))
        self.assertEqual(response.status_code, 302)

    def test_get_form_page(self):
        """Forma sahifasi 200"""
        self.login()
        response = self.client.get(reverse('competitions:battle_create'))
        self.assertEqual(response.status_code, 200)

    def test_create_bot_battle(self):
        """Bot bilan battle yaratish"""
        self.login()
        self.client.post(
            reverse('competitions:battle_create'),
            data={
                'opponent_type': 'bot',
                'bot_difficulty': 'medium',
                'subject_id': self.subject.id,
                'question_count': 10,
            },
        )
        self.assertTrue(
            Battle.objects.filter(
                challenger=self.user,
                opponent_type='bot',
            ).exists()
        )


class BattleDetailViewTest(BaseTestCase):
    """battle_detail view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2)
        response = self.client.get(
            reverse('competitions:battle_detail', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 302)

    def test_status_200(self):
        """Battle tafsilotlari 200"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2)
        self.login()
        response = self.client.get(
            reverse('competitions:battle_detail', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 200)

    def test_nonexistent_battle_returns_404(self):
        """Mavjud bo'lmagan battle - 404"""
        self.login()
        response = self.client.get(
            reverse('competitions:battle_detail', kwargs={'uuid': uuid.uuid4()})
        )
        self.assertEqual(response.status_code, 404)


class BattleAcceptViewTest(BaseTestCase):
    """battle_accept view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle(challenger=self.user2, opponent=self.user)
        response = self.client.post(
            reverse('competitions:battle_accept', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 302)

    def test_accept_changes_status(self):
        """Qabul qilish - status 'accepted' bo'ladi"""
        battle = self.make_battle(challenger=self.user2, opponent=self.user, status='pending')
        self.login()
        self.client.post(
            reverse('competitions:battle_accept', kwargs={'uuid': battle.uuid})
        )
        battle.refresh_from_db()
        self.assertEqual(battle.status, 'accepted')


class BattleRejectViewTest(BaseTestCase):
    """battle_reject view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle(challenger=self.user2, opponent=self.user)
        response = self.client.post(
            reverse('competitions:battle_reject', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 302)

    def test_reject_changes_status(self):
        """Rad etish - status o'zgaradi"""
        battle = self.make_battle(challenger=self.user2, opponent=self.user, status='pending')
        self.login()
        self.client.post(
            reverse('competitions:battle_reject', kwargs={'uuid': battle.uuid})
        )
        battle.refresh_from_db()
        self.assertIn(battle.status, ['rejected', 'cancelled'])


class BattleSubmitViewTest(BaseTestCase):
    """battle_submit view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle()
        response = self.client.post(
            reverse('competitions:battle_submit', kwargs={'uuid': battle.uuid}),
            data={'answers': '[]', 'time_spent': '60'},
        )
        self.assertEqual(response.status_code, 302)

    def test_submit_correct_answers(self):
        """To'g'ri javoblar yuborish"""
        battle = self.make_battle(opponent_type='bot', bot_difficulty='easy', status='in_progress')
        self.login()
        answers = json.dumps([
            {'question_id': self.question1.id, 'answer_id': self.answer_correct.id},
            {'question_id': self.question2.id, 'answer_id': self.answer2_correct.id},
        ])
        self.client.post(
            reverse('competitions:battle_submit', kwargs={'uuid': battle.uuid}),
            data={'answers': answers, 'time_spent': '60'},
        )
        battle.refresh_from_db()
        self.assertEqual(battle.challenger_correct, 2)
        self.assertTrue(battle.challenger_completed)

    def test_submit_wrong_answers_score_zero(self):
        """Noto'g'ri javoblar - 0 ball"""
        battle = self.make_battle(opponent_type='bot', bot_difficulty='easy', status='in_progress')
        self.login()
        answers = json.dumps([
            {'question_id': self.question1.id, 'answer_id': self.answer_wrong.id},
        ])
        self.client.post(
            reverse('competitions:battle_submit', kwargs={'uuid': battle.uuid}),
            data={'answers': answers, 'time_spent': '30'},
        )
        battle.refresh_from_db()
        self.assertEqual(battle.challenger_correct, 0)

    def test_submit_redirects_to_result(self):
        """Submit - result sahifasiga"""
        battle = self.make_battle(opponent_type='bot', bot_difficulty='easy', status='in_progress')
        self.login()
        response = self.client.post(
            reverse('competitions:battle_submit', kwargs={'uuid': battle.uuid}),
            data={'answers': '[]', 'time_spent': '60'},
        )
        self.assertRedirects(
            response,
            reverse('competitions:battle_result', kwargs={'uuid': battle.uuid}),
            fetch_redirect_response=False,
        )


class BattleResultViewTest(BaseTestCase):
    """battle_result view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle()
        response = self.client.get(
            reverse('competitions:battle_result', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 302)

    def test_completed_battle_shows_result_page(self):
        """Tugallangan battle - natija sahifasi 200"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.status = 'completed'
        battle.challenger_completed = True
        battle.opponent_completed = True
        battle.winner = self.user
        battle.challenger_correct = 2
        battle.opponent_correct = 0
        battle.save()
        self.login()
        response = self.client.get(
            reverse('competitions:battle_result', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 200)

    def test_incomplete_battle_redirects_to_detail(self):
        """Tugallanmagan battle - detail sahifasiga"""
        battle = self.make_battle(opponent=self.user2, status='in_progress')
        self.login()
        response = self.client.get(
            reverse('competitions:battle_result', kwargs={'uuid': battle.uuid})
        )
        self.assertRedirects(
            response,
            reverse('competitions:battle_detail', kwargs={'uuid': battle.uuid}),
            fetch_redirect_response=False,
        )

    def test_context_keys_for_completed_battle(self):
        """Tugallangan battle context kalitlari"""
        battle = self.make_battle(opponent=self.user2, opponent_type='friend')
        battle.status = 'completed'
        battle.challenger_completed = True
        battle.opponent_completed = True
        battle.winner = self.user
        battle.save()
        self.login()
        response = self.client.get(
            reverse('competitions:battle_result', kwargs={'uuid': battle.uuid})
        )
        for key in ['battle', 'is_challenger', 'user_correct', 'user_time',
                    'opponent_correct', 'opponent_time', 'user_won', 'user_lost', 'is_draw']:
            self.assertIn(key, response.context, f"'{key}' context da yo'q")


class DailyChallengeViewTest(BaseTestCase):
    """daily_challenge view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:daily_challenge'))
        self.assertEqual(response.status_code, 302)

    def test_status_200_no_challenge_today(self):
        """Bugun challenge yo'q - 200"""
        self.login()
        response = self.client.get(reverse('competitions:daily_challenge'))
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['challenge'])

    def test_challenge_shown_in_context(self):
        """Bugun challenge bor - contextda ko'rinadi"""
        today = timezone.now().date()
        challenge = DailyChallenge.objects.create(
            date=today, subject=self.subject, question_count=5, time_limit=10,
        )
        self.login()
        response = self.client.get(reverse('competitions:daily_challenge'))
        self.assertEqual(response.context['challenge'], challenge)


class DailyChallengeStartViewTest(BaseTestCase):
    """daily_challenge_start view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:daily_challenge_start'))
        self.assertEqual(response.status_code, 302)

    def test_redirects_when_no_challenge(self):
        """Challenge yo'q - yo'naltiriladi"""
        self.login()
        response = self.client.get(reverse('competitions:daily_challenge_start'))
        # 302 bo'lishi kerak
        self.assertEqual(response.status_code, 302)

    def test_redirects_when_already_completed(self):
        """Allaqachon qatnashgan - yo'naltiriladi"""
        today = timezone.now().date()
        challenge = DailyChallenge.objects.create(
            date=today, subject=self.subject, question_count=5, time_limit=10,
        )
        DailyChallengeParticipant.objects.create(
            challenge=challenge, user=self.user, score=80,
        )
        self.login()
        response = self.client.get(reverse('competitions:daily_challenge_start'))
        self.assertEqual(response.status_code, 302)


class WeeklyLeagueViewTest(BaseTestCase):
    """weekly_league view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:weekly_league'))
        self.assertEqual(response.status_code, 302)

    def test_status_200_authenticated(self):
        """Tizimga kirgan ko'radi"""
        self.login()
        response = self.client.get(reverse('competitions:weekly_league'))
        self.assertEqual(response.status_code, 200)


class MyCertificatesViewTest(BaseTestCase):
    """my_certificates view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:my_certificates'))
        self.assertEqual(response.status_code, 302)

    def test_status_200_authenticated(self):
        """Tizimga kirgan ko'radi"""
        self.login()
        response = self.client.get(reverse('competitions:my_certificates'))
        self.assertEqual(response.status_code, 200)

    def test_user_certificate_shown(self):
        """Foydalanuvchiga tegishli sertifikat ko'rinadi"""
        participant = CompetitionParticipant.objects.create(
            competition=self.competition_finished,
            user=self.user,
            status='completed',
            score=90,
            rank=1,
        )
        cert = Certificate.objects.create(
            user=self.user,
            competition=self.competition_finished,
            participant=participant,
            certificate_type='winner',
            score=90,
            rank=1,
        )
        self.login()
        response = self.client.get(reverse('competitions:my_certificates'))
        self.assertEqual(response.status_code, 200)


class VerifyCertificateViewTest(BaseTestCase):
    """verify_certificate view testlari"""

    def setUp(self):
        super().setUp()
        participant = CompetitionParticipant.objects.create(
            competition=self.competition_finished,
            user=self.user,
            status='completed',
            score=90,
        )
        self.certificate = Certificate.objects.create(
            user=self.user,
            competition=self.competition_finished,
            participant=participant,
            certificate_type='participation',
            score=90,
        )

    def test_valid_code_returns_200(self):
        """To'g'ri kod - 200"""
        response = self.client.get(
            reverse('competitions:verify_certificate',
                    kwargs={'code': self.certificate.verification_code})
        )
        self.assertEqual(response.status_code, 200)

    def test_invalid_code_returns_404(self):
        """Noto'g'ri kod - 404"""
        response = self.client.get(
            reverse('competitions:verify_certificate',
                    kwargs={'code': 'TM-NOTEXIST'})
        )
        self.assertEqual(response.status_code, 404)

    def test_no_login_required(self):
        """Login talab qilinmaydi (public sahifa)"""
        response = self.client.get(
            reverse('competitions:verify_certificate',
                    kwargs={'code': self.certificate.verification_code})
        )
        self.assertNotEqual(response.status_code, 302)


# ==============================================================
# API ENDPOINT TESTS
# ==============================================================

class ApiBattleStatusViewTest(BaseTestCase):
    """api_battle_status view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2)
        response = self.client.get(
            reverse('competitions:api_battle_status', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 302)

    def test_returns_json_200(self):
        """JSON javob 200"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2, status='pending')
        self.login()
        response = self.client.get(
            reverse('competitions:api_battle_status', kwargs={'uuid': battle.uuid})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')

    def test_status_field_in_response(self):
        """Javobda status maydoni bor"""
        battle = self.make_battle(challenger=self.user, opponent=self.user2, status='pending')
        self.login()
        response = self.client.get(
            reverse('competitions:api_battle_status', kwargs={'uuid': battle.uuid})
        )
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'pending')

    def test_nonexistent_battle_returns_404(self):
        """Mavjud bo'lmagan battle - 404"""
        self.login()
        response = self.client.get(
            reverse('competitions:api_battle_status', kwargs={'uuid': uuid.uuid4()})
        )
        self.assertEqual(response.status_code, 404)


class ApiMatchmakingStatusViewTest(BaseTestCase):
    """api_matchmaking_status view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:api_matchmaking_status'))
        self.assertEqual(response.status_code, 302)

    def test_returns_json_200(self):
        """JSON javob 200"""
        self.login()
        response = self.client.get(reverse('competitions:api_matchmaking_status'))
        self.assertEqual(response.status_code, 200)

    def test_not_in_queue_response(self):
        """Navbatda bo'lmasa in_queue False"""
        self.login()
        response = self.client.get(reverse('competitions:api_matchmaking_status'))
        data = json.loads(response.content)
        self.assertIn('in_queue', data)
        self.assertFalse(data['in_queue'])

    def test_in_queue_response(self):
        """Navbatda bo'lganda in_queue True"""
        MatchmakingQueue.objects.create(
            user=self.user,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        self.login()
        response = self.client.get(reverse('competitions:api_matchmaking_status'))
        data = json.loads(response.content)
        self.assertTrue(data.get('in_queue', False))


class ApiMatchmakingCancelViewTest(BaseTestCase):
    """api_matchmaking_cancel view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.post(reverse('competitions:api_matchmaking_cancel'))
        self.assertEqual(response.status_code, 302)

    def test_cancel_removes_from_queue(self):
        """Bekor qilish - navbatdan chiqaradi"""
        MatchmakingQueue.objects.create(
            user=self.user,
            user_rating=1000,
            user_level=1,
            expires_at=timezone.now() + timedelta(minutes=5),
        )
        self.login()
        self.client.post(reverse('competitions:api_matchmaking_cancel'))
        self.assertFalse(MatchmakingQueue.objects.filter(user=self.user).exists())

    def test_cancel_when_not_in_queue(self):
        """Navbatda bo'lmasa - xatoliksiz ishlaydi"""
        self.login()
        response = self.client.post(reverse('competitions:api_matchmaking_cancel'))
        self.assertEqual(response.status_code, 200)


class ApiLeaderboardViewTest(BaseTestCase):
    """api_leaderboard view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(
            reverse('competitions:api_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 302)

    def test_returns_json_200(self):
        """JSON javob 200"""
        self.login()
        response = self.client.get(
            reverse('competitions:api_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_response_is_list_or_dict(self):
        """Javob list yoki dict"""
        self.login()
        response = self.client.get(
            reverse('competitions:api_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        data = json.loads(response.content)
        self.assertIsInstance(data, (list, dict))

    def test_participants_in_response(self):
        """Qatnashchilar javobda"""
        CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='completed',
            score=90,
            rank=1,
        )
        self.login()
        response = self.client.get(
            reverse('competitions:api_leaderboard',
                    kwargs={'slug': self.competition_active.slug})
        )
        data = json.loads(response.content)
        # Ro'yxat bo'lsa - elementlar bor
        if isinstance(data, list):
            self.assertGreater(len(data), 0)


class ApiLogViolationViewTest(BaseTestCase):
    """api_log_violation view testlari"""

    def setUp(self):
        super().setUp()
        self.participant = CompetitionParticipant.objects.create(
            competition=self.competition_active,
            user=self.user,
            status='in_progress',
        )

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.post(
            reverse('competitions:api_log_violation'),
            data=json.dumps({'competition_id': self.competition_active.id, 'type': 'tab_switch'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_returns_json_200(self):
        """JSON javob 200"""
        self.login()
        response = self.client.post(
            reverse('competitions:api_log_violation'),
            data=json.dumps({
                'competition_id': self.competition_active.id,
                'type': 'tab_switch',
            }),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)

    def test_success_field_in_response(self):
        """Javobda success maydoni"""
        self.login()
        response = self.client.post(
            reverse('competitions:api_log_violation'),
            data=json.dumps({
                'competition_id': self.competition_active.id,
                'type': 'tab_switch',
            }),
            content_type='application/json',
        )
        data = json.loads(response.content)
        self.assertIn('success', data)

    def test_violation_recorded_in_participant(self):
        """Qoidabuzarlik participant da saqlanadi"""
        self.login()
        self.client.post(
            reverse('competitions:api_log_violation'),
            data=json.dumps({
                'competition_id': self.competition_active.id,
                'type': 'copy_paste',
            }),
            content_type='application/json',
        )
        self.participant.refresh_from_db()
        self.assertGreater(self.participant.violations_count, 0)


class ApiOnlineFriendsViewTest(BaseTestCase):
    """api_online_friends view testlari"""

    def test_requires_login(self):
        """Login talab qilinadi"""
        response = self.client.get(reverse('competitions:api_online_friends'))
        self.assertEqual(response.status_code, 302)

    def test_returns_json_200(self):
        """JSON javob 200"""
        self.login()
        response = self.client.get(reverse('competitions:api_online_friends'))
        self.assertEqual(response.status_code, 200)

    def test_response_is_list_or_dict(self):
        """Javob list yoki dict"""
        self.login()
        response = self.client.get(reverse('competitions:api_online_friends'))
        data = json.loads(response.content)
        self.assertIsInstance(data, (list, dict))
