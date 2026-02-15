"""
TestMakon.uz - Competition Models (Updated)
Bepul + Pullik musobaqalar, Bot, Matchmaking, Sertifikatlar
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid
import random


class Competition(models.Model):
    """Admin tomonidan tashkil etilgan musobaqalar"""

    COMPETITION_TYPES = [
        ('daily', 'Kunlik'),
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('special', 'Maxsus'),
        ('olympiad', 'Olimpiada'),
        ('tournament', 'Turnir'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Qoralama'),
        ('upcoming', 'Kutilmoqda'),
        ('registration', 'Ro\'yxatdan o\'tish'),
        ('active', 'Faol'),
        ('finished', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    ENTRY_TYPES = [
        ('free', 'Bepul'),
        ('premium_only', 'Faqat Premium'),
        ('paid', 'Pullik'),
    ]

    TEST_FORMATS = [
        ('single_subject', 'Bitta fan'),
        ('multi_subject', 'Ko\'p fan'),
        ('dtm_block', 'DTM blok'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic info
    title = models.CharField('Sarlavha', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif')
    rules = models.TextField('Qoidalar', blank=True)
    short_description = models.CharField('Qisqa tavsif', max_length=300, blank=True)

    # Type and status
    competition_type = models.CharField(
        'Turi',
        max_length=20,
        choices=COMPETITION_TYPES,
        default='weekly'
    )
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Entry type
    entry_type = models.CharField(
        'Kirish turi',
        max_length=20,
        choices=ENTRY_TYPES,
        default='free'
    )
    entry_fee = models.PositiveIntegerField('Kirish narxi (so\'m)', default=0)

    # Test format
    test_format = models.CharField(
        'Test formati',
        max_length=20,
        choices=TEST_FORMATS,
        default='single_subject'
    )

    # Media
    banner = models.ImageField('Banner', upload_to='competitions/banners/', blank=True, null=True)
    icon = models.CharField('Icon (emoji)', max_length=10, default='🏆')

    # Subject/Test
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competitions',
        verbose_name='Fan'
    )
    subjects = models.ManyToManyField(
        'tests_app.Subject',
        blank=True,
        related_name='multi_competitions',
        verbose_name='Fanlar (DTM blok)'
    )
    test = models.ForeignKey(
        'tests_app.Test',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competitions',
        verbose_name='Test'
    )

    # Question settings
    questions_per_subject = models.PositiveIntegerField('Har fandan savollar', default=30)
    total_questions = models.PositiveIntegerField('Jami savollar', default=30)
    difficulty_distribution = models.JSONField(
        'Qiyinlik taqsimoti',
        default=dict,
        blank=True,
        help_text='{"easy": 30, "medium": 50, "hard": 20}'
    )

    # Time settings
    registration_start = models.DateTimeField('Ro\'yxat boshlanishi', null=True, blank=True)
    registration_end = models.DateTimeField('Ro\'yxat tugashi', null=True, blank=True)
    start_time = models.DateTimeField('Boshlanish vaqti')
    end_time = models.DateTimeField('Tugash vaqti')
    duration_minutes = models.PositiveIntegerField('Davomiyligi (daqiqa)', default=60)

    # Participation limits
    max_participants = models.PositiveIntegerField('Max qatnashchilar', null=True, blank=True)
    min_participants = models.PositiveIntegerField('Min qatnashchilar', default=1)
    min_level = models.PositiveIntegerField('Min daraja', default=0)
    min_rating = models.PositiveIntegerField('Min reyting', default=0)

    # Prizes (TestMakon tomonidan)
    prize_pool = models.PositiveIntegerField('Sovrin fondi (so\'m)', default=0)
    prizes = models.JSONField(
        'Sovrinlar',
        default=list,
        blank=True,
        help_text='[{"place": 1, "amount": 500000, "description": "1-o\'rin"}, ...]'
    )

    # XP rewards
    xp_reward_first = models.PositiveIntegerField('1-o\'rin XP', default=500)
    xp_reward_second = models.PositiveIntegerField('2-o\'rin XP', default=300)
    xp_reward_third = models.PositiveIntegerField('3-o\'rin XP', default=100)
    xp_participation = models.PositiveIntegerField('Qatnashish XP', default=20)
    xp_per_correct = models.PositiveIntegerField('To\'g\'ri javob XP', default=5)

    # Stats
    participants_count = models.PositiveIntegerField('Qatnashchilar soni', default=0)
    completed_count = models.PositiveIntegerField('Yakunlaganlar soni', default=0)
    average_score = models.FloatField('O\'rtacha ball', default=0)

    # Features
    show_live_leaderboard = models.BooleanField('Live reyting ko\'rsatish', default=True)
    show_answers_after = models.BooleanField('Javoblarni ko\'rsatish', default=True)
    allow_review = models.BooleanField('Tahlil qilishga ruxsat', default=True)
    certificate_enabled = models.BooleanField('Sertifikat berish', default=False)
    anti_cheat_enabled = models.BooleanField('Anti-cheat yoqish', default=True)

    # Sponsors
    sponsors = models.JSONField(
        'Homiylar',
        default=list,
        blank=True,
        help_text='[{"name": "...", "logo": "...", "url": "..."}]'
    )

    # Savol manbasi
    QUESTION_SOURCE_CHOICES = [
        ('auto', 'Avtomatik (bankdan)'),
        ('manual', 'Qo\'lda tanlangan'),
        ('mixed', 'Aralash'),
    ]
    question_source = models.CharField(
        'Savol manbasi',
        max_length=10,
        choices=QUESTION_SOURCE_CHOICES,
        default='auto',
        help_text='Avtomatik = bankdan tasodifiy. Qo\'lda = faqat tanlangan savollar.'
    )

    is_active = models.BooleanField('Faol', default=True)
    is_featured = models.BooleanField('Tanlanganlar', default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_competitions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Musobaqa'
        verbose_name_plural = 'Musobaqalar'
        ordering = ['-start_time']

    def __str__(self):
        return self.title

    @property
    def is_registration_open(self):
        now = timezone.now()
        if self.registration_start and self.registration_end:
            return self.registration_start <= now <= self.registration_end
        return self.status in ['upcoming', 'registration']

    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time and self.status == 'active'

    @property
    def is_finished(self):
        return timezone.now() > self.end_time or self.status == 'finished'

    @property
    def time_until_start(self):
        if self.status != 'upcoming':
            return None
        return self.start_time - timezone.now()

    @property
    def time_remaining(self):
        if self.is_finished:
            return None
        return self.end_time - timezone.now()

    @property
    def spots_left(self):
        if not self.max_participants:
            return None
        return max(0, self.max_participants - self.participants_count)

    def get_prize_for_rank(self, rank):
        """O'rin bo'yicha sovrinni olish"""
        for prize in self.prizes:
            if prize.get('place') == rank:
                return prize
        return None

    def has_manual_questions(self):
        """Qo'lda biriktirilgan savollar bormi?"""
        return self.competition_questions.exists()

    def get_manual_questions(self):
        """Qo'lda biriktirilgan savollar ro'yxati"""
        return [
            cq.question for cq in
            self.competition_questions.select_related(
                'question__subject', 'question__topic'
            ).prefetch_related('question__answers').order_by('order')
        ]


class CompetitionQuestion(models.Model):
    """Musobaqaga biriktirilgan savol"""

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='competition_questions',
        verbose_name='Musobaqa'
    )
    question = models.ForeignKey(
        'tests_app.Question',
        on_delete=models.CASCADE,
        related_name='competition_assignments',
        verbose_name='Savol'
    )
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Musobaqa savoli'
        verbose_name_plural = 'Musobaqa savollari'
        ordering = ['order']
        unique_together = ['competition', 'question']

    def __str__(self):
        return f"{self.competition.title} - #{self.order}"


class CompetitionParticipant(models.Model):
    """Musobaqa qatnashchisi"""

    STATUS_CHOICES = [
        ('registered', 'Ro\'yxatdan o\'tgan'),
        ('ready', 'Tayyor'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlagan'),
        ('disqualified', 'Diskvalifikatsiya'),
    ]

    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name='Musobaqa'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='competition_participations'
    )

    # Status
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='registered'
    )

    # Result
    score = models.FloatField('Ball', default=0)
    percentage = models.FloatField('Foiz', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri javoblar', default=0)
    skipped_answers = models.PositiveIntegerField('O\'tkazib yuborilgan', default=0)
    time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)

    # Answers data
    answers_data = models.JSONField('Javoblar', default=list, blank=True)

    # Rank
    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)
    prize_amount = models.PositiveIntegerField('Sovrin (so\'m)', default=0)

    # Timing
    started_at = models.DateTimeField('Boshlangan vaqt', null=True, blank=True)
    completed_at = models.DateTimeField('Yakunlangan vaqt', null=True, blank=True)

    # Anti-cheat
    violations_count = models.PositiveIntegerField('Qoidabuzarlik soni', default=0)
    violations_log = models.JSONField('Qoidabuzarlik logi', default=list, blank=True)
    is_suspected = models.BooleanField('Shubhali', default=False)

    joined_at = models.DateTimeField('Qo\'shilgan vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Qatnashchi'
        verbose_name_plural = 'Qatnashchilar'
        unique_together = ['competition', 'user']
        ordering = ['rank', '-score', 'time_spent']

    def __str__(self):
        return f"{self.user} - {self.competition} (#{self.rank})"

    def add_violation(self, violation_type, details=None):
        """Qoidabuzarlik qo'shish"""
        self.violations_count += 1
        self.violations_log.append({
            'type': violation_type,
            'details': details,
            'timestamp': timezone.now().isoformat()
        })
        if self.violations_count >= 3:
            self.status = 'disqualified'
        self.save()


class CompetitionPayment(models.Model):
    """Pullik musobaqa to'lovlari"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('completed', 'To\'langan'),
        ('failed', 'Muvaffaqiyatsiz'),
        ('refunded', 'Qaytarilgan'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    participant = models.OneToOneField(
        CompetitionParticipant,
        on_delete=models.CASCADE,
        related_name='payment'
    )

    amount = models.PositiveIntegerField('Summa (so\'m)')
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')

    payment_method = models.CharField('To\'lov usuli', max_length=50, blank=True)
    transaction_id = models.CharField('Tranzaksiya ID', max_length=100, blank=True)

    paid_at = models.DateTimeField('To\'langan vaqt', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'

    def __str__(self):
        return f"{self.participant.user} - {self.amount} so'm"


class Certificate(models.Model):
    """Sertifikatlar"""

    CERTIFICATE_TYPES = [
        ('participation', 'Ishtirok sertifikati'),
        ('winner', 'G\'olib sertifikati'),
        ('top3', 'Top 3 sertifikati'),
        ('top10', 'Top 10 sertifikati'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    competition = models.ForeignKey(
        Competition,
        on_delete=models.CASCADE,
        related_name='certificates'
    )
    participant = models.OneToOneField(
        CompetitionParticipant,
        on_delete=models.CASCADE,
        related_name='certificate',
        null=True,
        blank=True
    )

    certificate_type = models.CharField(
        'Turi',
        max_length=20,
        choices=CERTIFICATE_TYPES,
        default='participation'
    )

    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)
    score = models.FloatField('Ball', default=0)

    # Certificate file
    file = models.FileField('Fayl', upload_to='certificates/', blank=True, null=True)

    issued_at = models.DateTimeField('Berilgan vaqt', auto_now_add=True)

    # Verification
    verification_code = models.CharField('Tasdiqlash kodi', max_length=20, unique=True)
    is_verified = models.BooleanField('Tasdiqlangan', default=True)

    class Meta:
        verbose_name = 'Sertifikat'
        verbose_name_plural = 'Sertifikatlar'
        unique_together = ['user', 'competition']

    def __str__(self):
        return f"{self.user} - {self.competition} ({self.certificate_type})"

    def save(self, *args, **kwargs):
        if not self.verification_code:
            self.verification_code = f"TM-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)


class Battle(models.Model):
    """1v1 do'st/random/bot bilan musobaqa"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('searching', 'Raqib qidirilmoqda'),
        ('accepted', 'Qabul qilingan'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlangan'),
        ('rejected', 'Rad etilgan'),
        ('expired', 'Muddati o\'tgan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    OPPONENT_TYPES = [
        ('friend', 'Do\'st'),
        ('random', 'Random'),
        ('bot', 'Bot'),
    ]

    BOT_DIFFICULTIES = [
        ('easy', 'Oson'),
        ('medium', 'O\'rta'),
        ('hard', 'Qiyin'),
        ('expert', 'Ekspert'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Players
    challenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='battles_challenged',
        verbose_name='Chaqiruvchi'
    )
    opponent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='battles_received',
        verbose_name='Raqib',
        null=True,
        blank=True
    )

    # Opponent type
    opponent_type = models.CharField(
        'Raqib turi',
        max_length=10,
        choices=OPPONENT_TYPES,
        default='friend'
    )
    bot_difficulty = models.CharField(
        'Bot qiyinligi',
        max_length=10,
        choices=BOT_DIFFICULTIES,
        blank=True
    )

    # Battle settings
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='battles',
        verbose_name='Fan'
    )
    is_dtm_format = models.BooleanField('DTM formati', default=False)
    question_count = models.PositiveIntegerField('Savollar soni', default=10)
    time_per_question = models.PositiveIntegerField('Savol uchun vaqt (soniya)', default=30)
    total_time = models.PositiveIntegerField('Jami vaqt (soniya)', default=300)

    # Questions (stored as JSON for quick access)
    questions_data = models.JSONField('Savollar', default=list)

    # Status
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # Challenger results
    challenger_score = models.PositiveIntegerField('Chaqiruvchi bali', default=0)
    challenger_correct = models.PositiveIntegerField('Chaqiruvchi to\'g\'ri', default=0)
    challenger_time = models.PositiveIntegerField('Chaqiruvchi vaqti', default=0)
    challenger_answers = models.JSONField('Chaqiruvchi javoblari', default=list)
    challenger_completed = models.BooleanField('Chaqiruvchi yakunladi', default=False)

    # Opponent results
    opponent_score = models.PositiveIntegerField('Raqib bali', default=0)
    opponent_correct = models.PositiveIntegerField('Raqib to\'g\'ri', default=0)
    opponent_time = models.PositiveIntegerField('Raqib vaqti', default=0)
    opponent_answers = models.JSONField('Raqib javoblari', default=list)
    opponent_completed = models.BooleanField('Raqib yakunladi', default=False)

    # Winner
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='battles_won',
        verbose_name='G\'olib'
    )
    is_draw = models.BooleanField('Durrang', default=False)
    winner_is_bot = models.BooleanField('Bot yutdi', default=False)

    # XP rewards
    winner_xp = models.PositiveIntegerField('G\'olib XP', default=50)
    loser_xp = models.PositiveIntegerField('Yutqazuvchi XP', default=10)
    xp_awarded = models.BooleanField('XP berildi', default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField('Qabul qilingan', null=True, blank=True)
    started_at = models.DateTimeField('Boshlangan', null=True, blank=True)
    completed_at = models.DateTimeField('Yakunlangan', null=True, blank=True)
    expires_at = models.DateTimeField('Amal qilish muddati')
    # Invite link orqali taklif
    invite_code = models.CharField(
        'Taklif kodi',
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        help_text='Havola orqali taklif uchun unikal kod'
    )

    def save(self, *args, **kwargs):
        if not self.invite_code and self.opponent_type == 'friend':
            self.invite_code = uuid.uuid4().hex[:10].upper()
        super().save(*args, **kwargs)

    @property
    def invite_url(self):
        """Taklif havolasini qaytarish"""
        if self.invite_code:
            return f"/competitions/battles/join/{self.invite_code}/"
        return None

    class Meta:
        verbose_name = 'Jang'
        verbose_name_plural = 'Janglar'
        ordering = ['-created_at']

    def __str__(self):
        opponent_name = self.opponent.full_name if self.opponent else f"Bot ({self.bot_difficulty})"
        return f"{self.challenger} vs {opponent_name}"

    def simulate_bot_answers(self):
        """Bot javoblarini simulyatsiya qilish"""
        if self.opponent_type != 'bot':
            return

        # Bot accuracy based on difficulty
        accuracy_map = {
            'easy': (0.4, 0.6),  # 40-60%
            'medium': (0.6, 0.8),  # 60-80%
            'hard': (0.8, 0.9),  # 80-90%
            'expert': (0.9, 0.98),  # 90-98%
        }

        min_acc, max_acc = accuracy_map.get(self.bot_difficulty, (0.5, 0.7))
        accuracy = random.uniform(min_acc, max_acc)

        bot_answers = []
        correct_count = 0
        total_time = 0

        for q in self.questions_data:
            # Tasodifiy javob (accuracy asosida)
            correct_answer = next((a for a in q['answers'] if a['is_correct']), None)

            if random.random() < accuracy and correct_answer:
                selected_id = correct_answer['id']
                is_correct = True
                correct_count += 1
            else:
                wrong_answers = [a for a in q['answers'] if not a['is_correct']]
                selected_id = random.choice(wrong_answers)['id'] if wrong_answers else None
                is_correct = False

            # Tasodifiy vaqt (tezroq = qiyinroq bot)
            time_range = {
                'easy': (15, 28),
                'medium': (10, 22),
                'hard': (5, 15),
                'expert': (3, 10),
            }
            min_t, max_t = time_range.get(self.bot_difficulty, (10, 25))
            q_time = random.randint(min_t, max_t)
            total_time += q_time

            bot_answers.append({
                'question_id': q['id'],
                'answer_id': selected_id,
                'is_correct': is_correct,
                'time': q_time
            })

        self.opponent_answers = bot_answers
        self.opponent_correct = correct_count
        self.opponent_time = total_time
        self.opponent_score = correct_count * 10
        self.opponent_completed = True
        self.save()

    def determine_winner(self):
        """G'olibni aniqlash"""
        if not self.challenger_completed:
            return

        if self.opponent_type == 'bot' and not self.opponent_completed:
            self.simulate_bot_answers()
        elif not self.opponent_completed:
            return

        if self.challenger_correct > self.opponent_correct:
            self.winner = self.challenger
        elif self.opponent_correct > self.challenger_correct:
            if self.opponent_type == 'bot':
                self.winner_is_bot = True
            else:
                self.winner = self.opponent
        elif self.challenger_time < self.opponent_time:
            self.winner = self.challenger
        elif self.opponent_time < self.challenger_time:
            if self.opponent_type == 'bot':
                self.winner_is_bot = True
            else:
                self.winner = self.opponent
        else:
            self.is_draw = True

        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()

        # XP berish
        self.award_xp()

    def award_xp(self):
        """XP mukofotini berish"""
        if self.xp_awarded:
            return

        from django.db.models import F

        if self.is_draw:
            draw_xp = (self.winner_xp + self.loser_xp) // 2
            self.challenger.xp_points = F('xp_points') + draw_xp
            self.challenger.save(update_fields=['xp_points'])
            if self.opponent:
                self.opponent.xp_points = F('xp_points') + draw_xp
                self.opponent.save(update_fields=['xp_points'])

        elif self.winner_is_bot:
            # Bot yutdi - challenger faqat loser XP oladi
            self.challenger.xp_points = F('xp_points') + self.loser_xp
            self.challenger.save(update_fields=['xp_points'])

        elif self.winner == self.challenger:
            # Challenger yutdi
            self.challenger.xp_points = F('xp_points') + self.winner_xp
            self.challenger.save(update_fields=['xp_points'])
            if self.opponent:
                self.opponent.xp_points = F('xp_points') + self.loser_xp
                self.opponent.save(update_fields=['xp_points'])

        elif self.opponent and self.winner == self.opponent:
            # Opponent (real user) yutdi
            self.opponent.xp_points = F('xp_points') + self.winner_xp
            self.opponent.save(update_fields=['xp_points'])
            self.challenger.xp_points = F('xp_points') + self.loser_xp
            self.challenger.save(update_fields=['xp_points'])

        self.xp_awarded = True
        self.save(update_fields=['xp_awarded'])


class MatchmakingQueue(models.Model):
    """Random raqib topish navbati"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matchmaking_queue'
    )

    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # User stats for matching
    user_rating = models.PositiveIntegerField('Reyting', default=1000)
    user_level = models.PositiveIntegerField('Daraja', default=1)

    # Settings
    question_count = models.PositiveIntegerField('Savollar soni', default=10)
    rating_range = models.PositiveIntegerField('Reyting oralig\'i', default=200)

    joined_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Muddati')

    is_matched = models.BooleanField('Topildi', default=False)
    matched_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matched_by'
    )
    battle = models.ForeignKey(
        Battle,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = 'Matchmaking navbat'
        verbose_name_plural = 'Matchmaking navbatlar'

    def __str__(self):
        return f"{self.user} - {self.subject or 'Any'}"

    @classmethod
    def find_match(cls, user, subject=None, question_count=10):
        """Mos raqib topish"""
        from datetime import timedelta

        user_rating = user.rating if hasattr(user, 'rating') else 1000
        user_level = user.level if hasattr(user, 'level') else 1

        # Navbatda turgan mos foydalanuvchilarni qidirish
        potential_matches = cls.objects.filter(
            is_matched=False,
            expires_at__gt=timezone.now(),
            user_rating__gte=user_rating - 200,
            user_rating__lte=user_rating + 200,
        ).exclude(user=user)

        if subject:
            potential_matches = potential_matches.filter(
                models.Q(subject=subject) | models.Q(subject__isnull=True)
            )

        match = potential_matches.order_by('joined_at').first()

        if match:
            # Match topildi - Battle yaratish
            return match

        return None


class BattleInvitation(models.Model):
    """Jang taklifnomalari"""

    battle = models.ForeignKey(
        Battle,
        on_delete=models.CASCADE,
        related_name='invitations'
    )

    sent_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    # Notification
    notification_sent = models.BooleanField('Xabar yuborildi', default=False)
    invited_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='battle_invitations_received',
        verbose_name='Taklif qilingan',
        null=True,
        blank=True
    )
    status = models.CharField(
        'Holat',
        max_length=10,
        choices=[
            ('pending', 'Kutilmoqda'),
            ('accepted', 'Qabul qilingan'),
            ('declined', 'Rad etilgan'),
            ('expired', 'Muddati o\'tgan'),
        ],
        default='pending'
    )

    class Meta:
        verbose_name = 'Jang taklifi'
        verbose_name_plural = 'Jang takliflari'


class DailyChallenge(models.Model):
    """Kunlik challenge"""

    date = models.DateField('Sana', unique=True)

    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        related_name='daily_challenges'
    )
    questions = models.ManyToManyField(
        'tests_app.Question',
        related_name='daily_challenges'
    )

    # Settings
    question_count = models.PositiveIntegerField('Savollar soni', default=10)
    time_limit = models.PositiveIntegerField('Vaqt limiti (daqiqa)', default=15)

    # Rewards
    xp_reward = models.PositiveIntegerField('XP mukofot', default=100)
    bonus_xp_top10 = models.PositiveIntegerField('Top 10 bonus XP', default=50)

    # Stats
    participants_count = models.PositiveIntegerField('Qatnashchilar', default=0)
    average_score = models.FloatField('O\'rtacha ball', default=0)

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Kunlik challenge'
        verbose_name_plural = 'Kunlik challengelar'
        ordering = ['-date']

    def __str__(self):
        return f"Challenge - {self.date}"


class DailyChallengeParticipant(models.Model):
    """Kunlik challenge qatnashchisi"""

    challenge = models.ForeignKey(
        DailyChallenge,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_challenge_participations'
    )

    score = models.PositiveIntegerField('Ball', default=0)
    percentage = models.FloatField('Foiz', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri', default=0)
    time_spent = models.PositiveIntegerField('Vaqt (soniya)', default=0)

    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)

    answers_data = models.JSONField('Javoblar', default=list, blank=True)

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Challenge qatnashchisi'
        verbose_name_plural = 'Challenge qatnashchilari'
        unique_together = ['challenge', 'user']
        ordering = ['-score', 'time_spent']

    def __str__(self):
        return f"{self.user} - {self.challenge.date}"


class WeeklyLeague(models.Model):
    """Haftalik liga"""

    LEAGUE_TIERS = [
        ('bronze', 'Bronza'),
        ('silver', 'Kumush'),
        ('gold', 'Oltin'),
        ('platinum', 'Platina'),
        ('diamond', 'Olmos'),
        ('master', 'Master'),
        ('grandmaster', 'Grandmaster'),
    ]

    week_start = models.DateField('Hafta boshlanishi')
    week_end = models.DateField('Hafta tugashi')

    tier = models.CharField('Daraja', max_length=20, choices=LEAGUE_TIERS, default='bronze')

    # Rewards
    xp_reward_first = models.PositiveIntegerField('1-o\'rin XP', default=300)
    xp_reward_top3 = models.PositiveIntegerField('Top 3 XP', default=200)
    xp_reward_top10 = models.PositiveIntegerField('Top 10 XP', default=100)

    # Promotion/Demotion
    promotion_count = models.PositiveIntegerField('Ko\'tarilish soni', default=3)
    demotion_count = models.PositiveIntegerField('Tushish soni', default=3)

    is_active = models.BooleanField('Faol', default=True)
    is_processed = models.BooleanField('Hisoblangan', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Haftalik liga'
        verbose_name_plural = 'Haftalik ligalar'
        ordering = ['-week_start', 'tier']

    def __str__(self):
        return f"{self.get_tier_display()} Liga - {self.week_start}"


class WeeklyLeagueParticipant(models.Model):
    """Haftalik liga qatnashchisi"""

    league = models.ForeignKey(
        WeeklyLeague,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weekly_leagues'
    )

    # Stats
    xp_earned = models.PositiveIntegerField('Yig\'ilgan XP', default=0)
    tests_completed = models.PositiveIntegerField('Testlar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)

    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)

    # Status
    is_promoted = models.BooleanField('Ko\'tarildi', default=False)
    is_demoted = models.BooleanField('Tushdi', default=False)

    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Liga qatnashchisi'
        verbose_name_plural = 'Liga qatnashchilari'
        unique_together = ['league', 'user']
        ordering = ['rank', '-xp_earned']

    def __str__(self):
        return f"{self.user} - {self.league}"





# ============================================================
# 3. YANGI MODEL - WeeklyLeagueParticipant dan KEYIN qo'shing:
# ============================================================

class Friendship(models.Model):
    """Do'stlik tizimi"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilingan'),
        ('declined', 'Rad etilgan'),
        ('blocked', 'Bloklangan'),
    ]

    from_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_friendships',
        verbose_name='Yuboruvchi'
    )
    to_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_friendships',
        verbose_name='Qabul qiluvchi'
    )
    status = models.CharField(
        'Holat',
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    created_at = models.DateTimeField('Yaratilgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)

    class Meta:
        verbose_name = 'Do\'stlik'
        verbose_name_plural = 'Do\'stliklar'
        unique_together = ['from_user', 'to_user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.from_user} → {self.to_user} ({self.get_status_display()})"

    @classmethod
    def are_friends(cls, user1, user2):
        """Ikki foydalanuvchi do'stmi tekshirish"""
        return cls.objects.filter(
            models.Q(from_user=user1, to_user=user2, status='accepted') |
            models.Q(from_user=user2, to_user=user1, status='accepted')
        ).exists()

    @classmethod
    def get_friends(cls, user):
        """Foydalanuvchining barcha do'stlarini olish"""
        from django.db.models import Q
        friendships = cls.objects.filter(
            Q(from_user=user, status='accepted') |
            Q(to_user=user, status='accepted')
        )
        friend_ids = set()
        for f in friendships:
            if f.from_user == user:
                friend_ids.add(f.to_user_id)
            else:
                friend_ids.add(f.from_user_id)

        from django.contrib.auth import get_user_model
        User = get_user_model()
        return User.objects.filter(id__in=friend_ids)

    @classmethod
    def get_pending_requests(cls, user):
        """Kutilayotgan do'stlik so'rovlari"""
        return cls.objects.filter(to_user=user, status='pending')

    @classmethod
    def send_request(cls, from_user, to_user):
        """Do'stlik so'rovi yuborish"""
        if from_user == to_user:
            return None, "O'zingizga so'rov yubora olmaysiz"

        # Allaqachon do'stmi?
        if cls.are_friends(from_user, to_user):
            return None, "Allaqachon do'stsiz"

        # Allaqachon so'rov bormi?
        existing = cls.objects.filter(
            models.Q(from_user=from_user, to_user=to_user) |
            models.Q(from_user=to_user, to_user=from_user)
        ).first()

        if existing:
            if existing.status == 'pending':
                # Agar raqib yuborgan bo'lsa, avtomatik qabul
                if existing.from_user == to_user:
                    existing.status = 'accepted'
                    existing.save()
                    return existing, "Do'stlik qabul qilindi!"
                return None, "So'rov allaqachon yuborilgan"
            elif existing.status == 'declined':
                existing.status = 'pending'
                existing.from_user = from_user
                existing.to_user = to_user
                existing.save()
                return existing, "So'rov qayta yuborildi"

        friendship = cls.objects.create(
            from_user=from_user,
            to_user=to_user,
            status='pending'
        )
        return friendship, "Do'stlik so'rovi yuborildi!"