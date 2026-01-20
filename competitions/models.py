"""
TestMakon.uz - Competition Models
1v1 battles, tournaments, and admin competitions
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class Competition(models.Model):
    """Admin tomonidan tashkil etilgan musobaqalar"""

    COMPETITION_TYPES = [
        ('daily', 'Kunlik'),
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('special', 'Maxsus'),
        ('olympiad', 'Olimpiada'),
    ]

    STATUS_CHOICES = [
        ('upcoming', 'Kutilmoqda'),
        ('active', 'Faol'),
        ('finished', 'Yakunlangan'),
        ('cancelled', 'Bekor qilingan'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic info
    title = models.CharField('Sarlavha', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif')
    rules = models.TextField('Qoidalar', blank=True)

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
        default='upcoming'
    )

    # Media
    banner = models.ImageField('Banner', upload_to='competitions/banners/', blank=True, null=True)

    # Subject/Test
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competitions',
        verbose_name='Fan'
    )
    test = models.ForeignKey(
        'tests_app.Test',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='competitions',
        verbose_name='Test'
    )

    # Time settings
    start_time = models.DateTimeField('Boshlanish vaqti')
    end_time = models.DateTimeField('Tugash vaqti')
    duration_minutes = models.PositiveIntegerField('Davomiyligi (daqiqa)', default=60)

    # Participation
    max_participants = models.PositiveIntegerField('Max qatnashchilar', null=True, blank=True)
    min_level = models.CharField('Min daraja', max_length=20, blank=True)
    is_premium_only = models.BooleanField('Faqat Premium', default=False)

    # Prizes
    prizes = models.JSONField('Sovrinlar', default=list, blank=True)
    xp_reward_first = models.PositiveIntegerField('1-o\'rin XP', default=500)
    xp_reward_second = models.PositiveIntegerField('2-o\'rin XP', default=300)
    xp_reward_third = models.PositiveIntegerField('3-o\'rin XP', default=100)
    xp_participation = models.PositiveIntegerField('Qatnashish XP', default=20)

    # Stats
    participants_count = models.PositiveIntegerField('Qatnashchilar soni', default=0)

    is_active = models.BooleanField('Faol', default=True)
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
    def is_ongoing(self):
        now = timezone.now()
        return self.start_time <= now <= self.end_time

    @property
    def is_finished(self):
        return timezone.now() > self.end_time

    @property
    def time_remaining(self):
        if self.is_finished:
            return None
        return self.end_time - timezone.now()


class CompetitionParticipant(models.Model):
    """Musobaqa qatnashchisi"""

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

    # Result
    score = models.FloatField('Ball', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri javoblar', default=0)
    time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)

    # Rank
    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)

    # Status
    is_started = models.BooleanField('Boshlangan', default=False)
    is_completed = models.BooleanField('Yakunlangan', default=False)
    started_at = models.DateTimeField('Boshlangan vaqt', null=True, blank=True)
    completed_at = models.DateTimeField('Yakunlangan vaqt', null=True, blank=True)

    joined_at = models.DateTimeField('Qo\'shilgan vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Qatnashchi'
        verbose_name_plural = 'Qatnashchilar'
        unique_together = ['competition', 'user']
        ordering = ['rank', '-score']

    def __str__(self):
        return f"{self.user} - {self.competition} (#{self.rank})"


class Battle(models.Model):
    """1v1 do'st bilan musobaqa"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilingan'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlangan'),
        ('rejected', 'Rad etilgan'),
        ('expired', 'Muddati o\'tgan'),
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
        verbose_name='Raqib'
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
    is_block_test = models.BooleanField('Blok test', default=False)
    question_count = models.PositiveIntegerField('Savollar soni', default=10)
    time_per_question = models.PositiveIntegerField('Savol uchun vaqt (soniya)', default=30)

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

    # XP rewards
    winner_xp = models.PositiveIntegerField('G\'olib XP', default=50)
    loser_xp = models.PositiveIntegerField('Yutqazuvchi XP', default=10)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField('Qabul qilingan', null=True, blank=True)
    started_at = models.DateTimeField('Boshlangan', null=True, blank=True)
    completed_at = models.DateTimeField('Yakunlangan', null=True, blank=True)
    expires_at = models.DateTimeField('Amal qilish muddati')

    class Meta:
        verbose_name = 'Jang'
        verbose_name_plural = 'Janglar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.challenger} vs {self.opponent}"

    def determine_winner(self):
        """G'olibni aniqlash"""
        if not self.challenger_completed or not self.opponent_completed:
            return

        if self.challenger_correct > self.opponent_correct:
            self.winner = self.challenger
        elif self.opponent_correct > self.challenger_correct:
            self.winner = self.opponent
        elif self.challenger_time < self.opponent_time:
            # Teng ball, lekin tezroq
            self.winner = self.challenger
        elif self.opponent_time < self.challenger_time:
            self.winner = self.opponent
        else:
            self.is_draw = True

        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class BattleInvitation(models.Model):
    """Jang taklifnomalari (push notification uchun)"""

    battle = models.ForeignKey(
        Battle,
        on_delete=models.CASCADE,
        related_name='invitations'
    )
    sent_at = models.DateTimeField(auto_now_add=True)
    seen_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

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

    xp_reward = models.PositiveIntegerField('XP mukofot', default=100)
    participants_count = models.PositiveIntegerField('Qatnashchilar', default=0)

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
        related_name='daily_challenges'
    )

    score = models.PositiveIntegerField('Ball', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri', default=0)
    time_spent = models.PositiveIntegerField('Vaqt (soniya)', default=0)
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Challenge qatnashchisi'
        verbose_name_plural = 'Challenge qatnashchilari'
        unique_together = ['challenge', 'user']
        ordering = ['-score', 'time_spent']