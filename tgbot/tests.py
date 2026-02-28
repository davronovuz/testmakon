"""
Telegram Bot — Test Suite
Qamrov: webhook handler + /result, /streak, /weaktest, /help, /start buyruqlari
"""

import json
from unittest.mock import patch, call

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone
from django.contrib.auth import get_user_model

from tgbot.models import TelegramUser
from tests_app.models import (
    Subject, Topic, Question, Test, TestQuestion, TestAttempt,
    UserAnalyticsSummary,
)
from ai_core.models import WeakTopicAnalysis

User = get_user_model()

TEST_TOKEN = 'test-bot-token-12345'
WEBHOOK_URL = f'/tgbot/webhook/{TEST_TOKEN}/'


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def make_user(phone='+998901234567', tg_id=None, streak=0, **kwargs):
    u = User.objects.create_user(
        phone_number=phone, password='testpass', first_name='Ali', **kwargs
    )
    if tg_id:
        u.telegram_id = tg_id
        u.current_streak = streak
        u.last_activity_date = timezone.localdate()
        u.save()
    return u


def make_subject():
    return Subject.objects.create(name='Matematika', slug='mat', is_active=True)


def make_topic(subj):
    return Topic.objects.create(subject=subj, name='Algebra', slug='alg')


def make_question(subj, topic=None):
    return Question.objects.create(
        subject=subj, topic=topic, text='Test savol', is_active=True,
    )


def tg_message(text, tg_id=111111, chat_id=111111, fname='Ali'):
    """Telegram webhook payload yasash."""
    return {
        'message': {
            'chat': {'id': chat_id, 'type': 'private'},
            'from': {
                'id': tg_id,
                'username': 'testuser',
                'first_name': fname,
                'last_name': '',
                'language_code': 'uz',
            },
            'text': text,
        }
    }


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class TgbotWebhookBaseTest(TestCase):
    """Barcha bot testlar uchun asosiy klass."""

    def setUp(self):
        self.client = Client()

    def post(self, payload):
        return self.client.post(
            WEBHOOK_URL,
            data=json.dumps(payload),
            content_type='application/json',
        )

    def send_command(self, command, tg_id=111111):
        return self.post(tg_message(command, tg_id=tg_id))


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class WebhookSecurityTest(TgbotWebhookBaseTest):

    def test_wrong_token_returns_403(self):
        resp = self.client.post(
            '/tgbot/webhook/WRONG-TOKEN/',
            data=json.dumps(tg_message('/start')),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 403)

    def test_correct_token_returns_200(self):
        resp = self.send_command('/start')
        self.assertEqual(resp.status_code, 200)

    def test_invalid_json_returns_400(self):
        resp = self.client.post(
            WEBHOOK_URL, data='not-json',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 400)

    def test_non_private_chat_ignored(self):
        """Group chat xabarlari ignore qilinadi."""
        payload = tg_message('/start')
        payload['message']['chat']['type'] = 'group'
        resp = self.post(payload)
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(TelegramUser.objects.exists())

    def test_no_message_returns_200(self):
        """callback_query kabi event → 200 OK."""
        resp = self.post({'callback_query': {'id': '1'}})
        self.assertEqual(resp.status_code, 200)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class StartCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_start_creates_telegram_user(self, mock_send):
        self.send_command('/start', tg_id=222222)
        self.assertTrue(TelegramUser.objects.filter(telegram_id=222222).exists())

    @patch('tgbot.views._tg_send')
    def test_start_sends_welcome(self, mock_send):
        self.send_command('/start', tg_id=223344)
        self.assertTrue(mock_send.called)
        sent_text = mock_send.call_args[0][1]
        self.assertIn('TestMakon', sent_text)

    @patch('tgbot.views._tg_send')
    def test_start_updates_existing_user(self, mock_send):
        """Mavjud TelegramUser — yangilanadi, yangi yaratilmaydi."""
        TelegramUser.objects.create(telegram_id=333333, username='old')
        self.send_command('/start', tg_id=333333)
        self.assertEqual(TelegramUser.objects.filter(telegram_id=333333).count(), 1)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class ResultCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_result_unlinked_user(self, mock_send):
        """/result — accounts.User bilan bog'lanmagan → error xabar."""
        self.send_command('/result', tg_id=999999)
        text = mock_send.call_args[0][1]
        self.assertIn("bog'lanmagan", text)

    @patch('tgbot.views._tg_send')
    def test_result_linked_user_no_analytics(self, mock_send):
        """/result — User bor, analytics yo'q → 0 ballik xabar."""
        make_user(phone='+998901111111', tg_id=444444)
        self.send_command('/result', tg_id=444444)
        text = mock_send.call_args[0][1]
        self.assertIn('DTM bashorat', text)
        self.assertIn('0', text)

    @patch('tgbot.views._tg_send')
    def test_result_shows_predicted_dtm(self, mock_send):
        """/result — analytics bor → predicted DTM ko'rinadi."""
        user = make_user(phone='+998901122334', tg_id=555555)
        UserAnalyticsSummary.objects.create(
            user=user, predicted_dtm_score=145, overall_accuracy=72.0,
        )
        self.send_command('/result', tg_id=555555)
        text = mock_send.call_args[0][1]
        self.assertIn('145', text)
        self.assertIn('72', text)

    @patch('tgbot.views._tg_send')
    def test_result_shows_last_attempt(self, mock_send):
        """/result — oxirgi test natijasi ham ko'rinadi."""
        user = make_user(phone='+998901234001', tg_id=556677)
        subj = make_subject()
        test = Test.objects.create(
            title='Son Test', slug='son-test', test_type='practice',
            subject=subj, time_limit=10, question_count=10, created_by=user,
        )
        TestAttempt.objects.create(
            user=user, test=test, status='completed',
            total_questions=10, correct_answers=8, percentage=80.0,
        )
        self.send_command('/result', tg_id=556677)
        text = mock_send.call_args[0][1]
        self.assertIn('80', text)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class StreakCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_streak_unlinked_user(self, mock_send):
        self.send_command('/streak', tg_id=888888)
        text = mock_send.call_args[0][1]
        self.assertIn("bog'lanmagan", text)

    @patch('tgbot.views._tg_send')
    def test_streak_zero(self, mock_send):
        """streak=0 → uyg'otuvchi xabar."""
        make_user(phone='+998901112222', tg_id=600001, streak=0)
        self.send_command('/streak', tg_id=600001)
        text = mock_send.call_args[0][1]
        self.assertIn('faol streak yo\'q', text)

    @patch('tgbot.views._tg_send')
    def test_streak_small(self, mock_send):
        """streak=2 → boshlanish xabari."""
        make_user(phone='+998901112223', tg_id=600002, streak=2)
        self.send_command('/streak', tg_id=600002)
        text = mock_send.call_args[0][1]
        self.assertIn('2', text)
        self.assertIn('Ajoyib boshlanish', text)

    @patch('tgbot.views._tg_send')
    def test_streak_medium(self, mock_send):
        """streak=5 → haftalik maqsad xabari."""
        make_user(phone='+998901112224', tg_id=600003, streak=5)
        self.send_command('/streak', tg_id=600003)
        text = mock_send.call_args[0][1]
        self.assertIn('5', text)
        # 7-5=2 kun qoldi
        self.assertIn('2 kun', text)

    @patch('tgbot.views._tg_send')
    def test_streak_high(self, mock_send):
        """streak=15 → zo'r yutuq xabari."""
        make_user(phone='+998901112225', tg_id=600004, streak=15)
        self.send_command('/streak', tg_id=600004)
        text = mock_send.call_args[0][1]
        self.assertIn('15', text)
        self.assertIn('katta yutuq', text)

    @patch('tgbot.views._tg_send')
    def test_streak_mega(self, mock_send):
        """streak=35 → MEGA streak xabari."""
        make_user(phone='+998901112226', tg_id=600005, streak=35)
        self.send_command('/streak', tg_id=600005)
        text = mock_send.call_args[0][1]
        self.assertIn('35', text)
        self.assertIn('MEGA', text)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class WeaktestCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_weaktest_unlinked_user(self, mock_send):
        self.send_command('/weaktest', tg_id=777777)
        text = mock_send.call_args[0][1]
        self.assertIn("bog'lanmagan", text)

    @patch('tgbot.views._tg_send')
    def test_weaktest_no_questions(self, mock_send):
        """Savollar yo'q → error xabar."""
        make_user(phone='+998901119999', tg_id=700001)
        self.send_command('/weaktest', tg_id=700001)
        # Ikki marta chaqiriladi: "tahlil qilyapti" + error
        calls = mock_send.call_args_list
        texts = [c[0][1] for c in calls]
        self.assertTrue(any('topilmadi' in t or 'xatolik' in t for t in texts))

    @patch('tgbot.views._tg_send')
    def test_weaktest_creates_test_and_sends_url(self, mock_send):
        """Savollar mavjud → Test + TestAttempt yaratib URL yuboradi."""
        user = make_user(phone='+998901118888', tg_id=700002)
        subj = Subject.objects.create(name='Fizika', slug='fiz2', is_active=True)
        for i in range(5):
            Question.objects.create(
                subject=subj, text=f'Savol {i}', is_active=True,
            )
        self.send_command('/weaktest', tg_id=700002)

        # TestAttempt yaratilganini tekshirish
        self.assertTrue(TestAttempt.objects.filter(user=user).exists())

        # URL yuborilganini tekshirish (inline markup bilan)
        last_call = mock_send.call_args
        # reply_markup argument
        markup = last_call[1].get('reply_markup') or (
            last_call[0][3] if len(last_call[0]) > 3 else None
        )
        self.assertIsNotNone(markup)
        buttons = markup['inline_keyboard'][0]
        self.assertEqual(len(buttons), 1)
        self.assertIn('/tests/play/', buttons[0]['url'])

    @patch('tgbot.views._tg_send')
    def test_weaktest_uses_weak_topics_first(self, mock_send):
        """WeakTopicAnalysis mavjud → sust mavzu savollari prioritet oladi."""
        user = make_user(phone='+998901117777', tg_id=700003)
        subj = Subject.objects.create(name='Kimyo', slug='kim2', is_active=True)
        topic = Topic.objects.create(subject=subj, name='Reaksiyalar', slug='rea2')
        for i in range(10):
            Question.objects.create(
                subject=subj, topic=topic, text=f'Savol {i}', is_active=True,
            )
        WeakTopicAnalysis.objects.create(
            user=user, subject=subj, topic=topic,
            accuracy_rate=25.0, total_questions=20, correct_answers=5,
        )
        self.send_command('/weaktest', tg_id=700003)
        self.assertTrue(TestAttempt.objects.filter(user=user).exists())

    @patch('tgbot.views._tg_send')
    def test_weaktest_attempt_status_in_progress(self, mock_send):
        """Yaratilgan attempt in_progress holatida."""
        user = make_user(phone='+998901116666', tg_id=700004)
        subj = Subject.objects.create(name='Tarix', slug='tar2', is_active=True)
        for i in range(5):
            Question.objects.create(
                subject=subj, text=f'Tarix savol {i}', is_active=True,
            )
        self.send_command('/weaktest', tg_id=700004)
        attempt = TestAttempt.objects.filter(user=user).first()
        self.assertEqual(attempt.status, 'in_progress')


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class HelpCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_help_lists_all_commands(self, mock_send):
        """/help → barcha buyruqlar ko'rinadi."""
        self.send_command('/help', tg_id=800001)
        text = mock_send.call_args[0][1]
        for cmd in ['/start', '/result', '/streak', '/weaktest', '/help']:
            self.assertIn(cmd, text, f'{cmd} /help matnida yo\'q')

    @patch('tgbot.views._tg_send')
    def test_help_returns_200(self, mock_send):
        resp = self.send_command('/help', tg_id=800002)
        self.assertEqual(resp.status_code, 200)


@override_settings(TELEGRAM_BOT_TOKEN=TEST_TOKEN)
class UnknownCommandTest(TgbotWebhookBaseTest):

    @patch('tgbot.views._tg_send')
    def test_unknown_command_no_response(self, mock_send):
        """Noma'lum buyruq → bot javob bermaydi."""
        self.send_command('/unknown_xyz', tg_id=900001)
        self.assertFalse(mock_send.called)

    @patch('tgbot.views._tg_send')
    def test_plain_text_no_response(self, mock_send):
        """Oddiy matn → bot javob bermaydi."""
        self.send_command('salom bu bot', tg_id=900002)
        self.assertFalse(mock_send.called)
