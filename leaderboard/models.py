"""
TestMakon.uz - Leaderboard Models
Rankings, achievements, and statistics
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class GlobalLeaderboard(models.Model):
    """Umumiy reyting"""

    PERIOD_CHOICES = [
        ('daily', 'Kunlik'),
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('all_time', 'Barcha vaqt'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )

    period = models.CharField(
        'Davr',
        max_length=20,
        choices=PERIOD_CHOICES
    )
    period_start = models.DateField('Davr boshi')
    period_end = models.DateField('Davr oxiri')

    # Rank
    rank = models.PositiveIntegerField('O\'rin')
    previous_rank = models.PositiveIntegerField('Oldingi o\'rin', null=True, blank=True)

    # Stats
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)
    tests_completed = models.PositiveIntegerField('Testlar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    accuracy_rate = models.FloatField('Aniqlik (%)', default=0.0)
    streak_days = models.PositiveIntegerField('Streak kunlar', default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Umumiy reyting'
        verbose_name_plural = 'Umumiy reytinglar'
        unique_together = ['user', 'period', 'period_start']
        ordering = ['rank']
        indexes = [
            models.Index(fields=['period', 'period_start', 'rank']),
        ]

    def __str__(self):
        return f"{self.user} - #{self.rank} ({self.period})"

    @property
    def rank_change(self):
        """Reyting o'zgarishi"""
        if self.previous_rank is None:
            return None
        return self.previous_rank - self.rank


class SubjectLeaderboard(models.Model):
    """Fan bo'yicha reyting"""

    PERIOD_CHOICES = [
        ('weekly', 'Haftalik'),
        ('monthly', 'Oylik'),
        ('all_time', 'Barcha vaqt'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subject_rankings'
    )
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.CASCADE,
        related_name='leaderboard_entries'
    )

    period = models.CharField('Davr', max_length=20, choices=PERIOD_CHOICES)
    period_start = models.DateField('Davr boshi')

    rank = models.PositiveIntegerField('O\'rin')
    score = models.PositiveIntegerField('Ball', default=0)
    tests_completed = models.PositiveIntegerField('Testlar', default=0)
    accuracy_rate = models.FloatField('Aniqlik (%)', default=0.0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fan reytingi'
        verbose_name_plural = 'Fan reytinglari'
        unique_together = ['user', 'subject', 'period', 'period_start']
        ordering = ['rank']

    def __str__(self):
        return f"{self.user} - {self.subject} - #{self.rank}"


class Achievement(models.Model):
    """Yutuqlar (Achievements)"""

    ACHIEVEMENT_CATEGORIES = [
        ('streak', 'Streak'),
        ('test', 'Test'),
        ('score', 'Ball'),
        ('competition', 'Musobaqa'),
        ('social', 'Ijtimoiy'),
        ('special', 'Maxsus'),
    ]

    RARITY_CHOICES = [
        ('common', 'Oddiy'),
        ('uncommon', 'Noyob'),
        ('rare', 'Kam uchraydigan'),
        ('epic', 'Epik'),
        ('legendary', 'Afsonaviy'),
    ]

    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif')

    category = models.CharField(
        'Kategoriya',
        max_length=20,
        choices=ACHIEVEMENT_CATEGORIES
    )
    rarity = models.CharField(
        'Nodirligi',
        max_length=20,
        choices=RARITY_CHOICES,
        default='common'
    )

    # Visual
    icon = models.ImageField('Ikonka', upload_to='achievements/')
    color = models.CharField('Rang', max_length=7, default='#FFD700')

    # Requirements
    requirement_type = models.CharField('Talab turi', max_length=50)
    requirement_value = models.PositiveIntegerField('Talab qiymati')

    # Reward
    xp_reward = models.PositiveIntegerField('XP mukofot', default=0)

    # Stats
    total_earned = models.PositiveIntegerField('Jami olganlar', default=0)

    is_active = models.BooleanField('Faol', default=True)
    is_hidden = models.BooleanField('Yashirin', default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Yutuq'
        verbose_name_plural = 'Yutuqlar'
        ordering = ['category', 'requirement_value']

    def __str__(self):
        return self.name

    @property
    def earn_percentage(self):
        """Qancha foiz foydalanuvchi olgan"""
        from accounts.models import User
        total_users = User.objects.filter(is_active=True).count()
        if total_users == 0:
            return 0
        return round((self.total_earned / total_users) * 100, 1)


class UserAchievement(models.Model):
    """Foydalanuvchi yutuqlari"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='achievements'
    )
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        related_name='users'
    )

    earned_at = models.DateTimeField('Olingan vaqt', auto_now_add=True)
    is_notified = models.BooleanField('Xabar berilgan', default=False)

    class Meta:
        verbose_name = 'Foydalanuvchi yutuqi'
        verbose_name_plural = 'Foydalanuvchi yutuqlari'
        unique_together = ['user', 'achievement']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user} - {self.achievement}"


class UserStats(models.Model):
    """Foydalanuvchi statistikasi (cached)"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='stats'
    )

    # Test stats
    total_tests = models.PositiveIntegerField('Jami testlar', default=0)
    total_questions_answered = models.PositiveIntegerField('Jami javoblar', default=0)
    total_correct = models.PositiveIntegerField('To\'g\'ri', default=0)
    total_wrong = models.PositiveIntegerField('Noto\'g\'ri', default=0)

    # Time stats
    total_time_spent = models.PositiveIntegerField('Jami vaqt (daqiqa)', default=0)
    average_time_per_question = models.FloatField('O\'rtacha vaqt (soniya)', default=0.0)

    # Subject stats (JSON)
    subject_stats = models.JSONField('Fan statistikasi', default=dict)

    # Best performances
    best_score = models.FloatField('Eng yuqori ball', default=0.0)
    best_streak = models.PositiveIntegerField('Eng uzun streak', default=0)
    best_accuracy = models.FloatField('Eng yuqori aniqlik', default=0.0)

    # Competition stats
    battles_won = models.PositiveIntegerField('Yutilgan janglar', default=0)
    battles_lost = models.PositiveIntegerField('Yutqazilgan janglar', default=0)
    battles_draw = models.PositiveIntegerField('Durrang janglar', default=0)
    competitions_participated = models.PositiveIntegerField('Musobaqalar', default=0)
    competitions_top3 = models.PositiveIntegerField('Top 3 musobaqalar', default=0)

    # Weekly stats (for comparison)
    weekly_xp = models.PositiveIntegerField('Haftalik XP', default=0)
    weekly_tests = models.PositiveIntegerField('Haftalik testlar', default=0)
    weekly_correct = models.PositiveIntegerField('Haftalik to\'g\'ri', default=0)

    # Daily stats
    today_xp = models.PositiveIntegerField('Bugungi XP', default=0)
    today_tests = models.PositiveIntegerField('Bugungi testlar', default=0)
    today_correct = models.PositiveIntegerField('Bugungi to\'g\'ri', default=0)
    last_daily_reset = models.DateField('Oxirgi kunlik reset', null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Foydalanuvchi statistikasi'
        verbose_name_plural = 'Foydalanuvchi statistikalari'

    def __str__(self):
        return f"{self.user} stats"

    @property
    def accuracy_rate(self):
        """Umumiy aniqlik foizi"""
        total = self.total_correct + self.total_wrong
        if total == 0:
            return 0
        return round((self.total_correct / total) * 100, 1)

    @property
    def win_rate(self):
        """Jang yutish foizi"""
        total = self.battles_won + self.battles_lost + self.battles_draw
        if total == 0:
            return 0
        return round((self.battles_won / total) * 100, 1)

    def reset_daily_stats(self):
        """Kunlik statistikani reset qilish"""
        today = timezone.now().date()
        if self.last_daily_reset != today:
            self.today_xp = 0
            self.today_tests = 0
            self.today_correct = 0
            self.last_daily_reset = today
            self.save()

    def update_subject_stats(self, subject_id, correct, wrong):
        """Fan statistikasini yangilash"""
        subject_key = str(subject_id)
        if subject_key not in self.subject_stats:
            self.subject_stats[subject_key] = {
                'total': 0,
                'correct': 0,
                'wrong': 0
            }

        self.subject_stats[subject_key]['total'] += correct + wrong
        self.subject_stats[subject_key]['correct'] += correct
        self.subject_stats[subject_key]['wrong'] += wrong
        self.save()


class SeasonalLeaderboard(models.Model):
    """Mavsumiy reyting (Seasons)"""

    name = models.CharField('Mavsum nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif', blank=True)

    start_date = models.DateField('Boshlanish')
    end_date = models.DateField('Tugash')

    # Prizes
    prizes = models.JSONField('Sovrinlar', default=list)

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Mavsum'
        verbose_name_plural = 'Mavsumlar'
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    @property
    def is_ongoing(self):
        today = timezone.now().date()
        return self.start_date <= today <= self.end_date


class SeasonalParticipant(models.Model):
    """Mavsumiy ishtirokchi"""

    season = models.ForeignKey(
        SeasonalLeaderboard,
        on_delete=models.CASCADE,
        related_name='participants'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='seasonal_participations'
    )

    rank = models.PositiveIntegerField('O\'rin', null=True, blank=True)
    total_xp = models.PositiveIntegerField('Jami XP', default=0)
    total_tests = models.PositiveIntegerField('Jami testlar', default=0)
    total_correct = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    accuracy_rate = models.FloatField('Aniqlik (%)', default=0.0)

    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mavsum ishtirokchisi'
        verbose_name_plural = 'Mavsum ishtirokchilari'
        unique_together = ['season', 'user']
        ordering = ['rank']

    def __str__(self):
        return f"{self.user} - {self.season} (#{self.rank})"