"""
TestMakon.uz - Test System Models
Production-ready test system with AI analysis support
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid
from PIL import Image
import os


class Subject(models.Model):
    """Fan (Matematika, Fizika, va hokazo)"""

    name = models.CharField('Fan nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif', blank=True)
    icon = models.CharField('Ikonka (emoji yoki class)', max_length=50, default='📚')
    color = models.CharField('Rang (hex)', max_length=7, default='#3498db')
    image = models.ImageField('Rasm', upload_to='subjects/', blank=True, null=True)

    # Ordering
    order = models.PositiveIntegerField('Tartib', default=0)

    # Stats
    total_tests = models.PositiveIntegerField('Jami testlar', default=0)
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fan'
        verbose_name_plural = 'Fanlar'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            path = self.image.path
            img = Image.open(path)
            if img.width > 400 or img.height > 400:
                img.thumbnail((400, 400), Image.LANCZOS)
                img.save(path, optimize=True, quality=85)


class Topic(models.Model):
    """Mavzu (Fan ichidagi mavzular)"""

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='topics',
        verbose_name='Fan'
    )
    name = models.CharField('Mavzu nomi', max_length=200)
    slug = models.SlugField('Slug')
    description = models.TextField('Tavsif', blank=True)

    # Hierarchy
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subtopics',
        verbose_name='Yuqori mavzu'
    )

    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Mavzu'
        verbose_name_plural = 'Mavzular'
        ordering = ['subject', 'order', 'name']
        unique_together = ['subject', 'slug']

    def __str__(self):
        return f"{self.subject.name} - {self.name}"


class Question(models.Model):
    """Test savoli"""

    DIFFICULTY_CHOICES = [
        ('easy', 'Oson'),
        ('medium', 'O\'rta'),
        ('hard', 'Qiyin'),
        ('expert', 'Ekspert'),
    ]

    QUESTION_TYPES = [
        ('single', 'Bitta to\'g\'ri javob'),
        ('multiple', 'Ko\'p to\'g\'ri javob'),
        ('true_false', 'To\'g\'ri/Noto\'g\'ri'),
        ('fill_blank', 'Bo\'sh joyni to\'ldiring'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Fan'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='questions',
        verbose_name='Mavzu'
    )

    # Question content
    text = models.TextField('Savol matni')
    image = models.ImageField('Rasm', upload_to='questions/', blank=True, null=True)

    # Question metadata
    question_type = models.CharField(
        'Savol turi',
        max_length=20,
        choices=QUESTION_TYPES,
        default='single'
    )
    difficulty = models.CharField(
        'Qiyinlik',
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='medium'
    )

    # Points and time
    points = models.PositiveIntegerField('Ball', default=1)
    time_limit = models.PositiveIntegerField('Vaqt (soniya)', default=60)

    # Explanation for AI and users
    explanation = models.TextField('Tushuntirish', blank=True)
    hint = models.TextField('Maslahat', blank=True)

    # Stats
    times_answered = models.PositiveIntegerField('Javob berilgan', default=0)
    times_correct = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)

    # Source
    source = models.CharField('Manba', max_length=200, blank=True)
    year = models.PositiveIntegerField('Yil', null=True, blank=True)

    is_active = models.BooleanField('Faol', default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_questions'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subject', 'difficulty']),
            models.Index(fields=['topic']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.subject.name}: {self.text[:50]}..."

    @property
    def correct_rate(self):
        """To'g'ri javob foizi"""
        if self.times_answered == 0:
            return 0
        return round((self.times_correct / self.times_answered) * 100, 1)


class Answer(models.Model):
    """Javob varianti"""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Savol'
    )
    text = models.TextField('Javob matni')
    image = models.ImageField('Rasm', upload_to='answers/', blank=True, null=True)
    is_correct = models.BooleanField('To\'g\'ri javob', default=False)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Javob'
        verbose_name_plural = 'Javoblar'
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:30]}... ({'✓' if self.is_correct else '✗'})"


class Test(models.Model):
    """Test to'plami"""

    TEST_TYPES = [
        ('practice', 'Mashq'),
        ('exam', 'Imtihon'),
        ('block', 'Blok test'),
        ('topic', 'Mavzu bo\'yicha'),
        ('quick', 'Tezkor test'),
        ('competition', 'Musobaqa'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    title = models.CharField('Sarlavha', max_length=200)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif', blank=True)

    # Test type and subject
    test_type = models.CharField(
        'Test turi',
        max_length=20,
        choices=TEST_TYPES,
        default='practice'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='tests',
        verbose_name='Fan',
        null=True,
        blank=True
    )

    # For block tests - multiple subjects
    subjects = models.ManyToManyField(
        Subject,
        related_name='block_tests',
        blank=True,
        verbose_name='Fanlar (blok test uchun)'
    )

    # Questions
    questions = models.ManyToManyField(
        Question,
        through='TestQuestion',
        related_name='tests',
        verbose_name='Savollar'
    )

    # Settings
    time_limit = models.PositiveIntegerField('Vaqt (daqiqa)', default=60)
    question_count = models.PositiveIntegerField('Savollar soni', default=30)
    passing_score = models.PositiveIntegerField('O\'tish bali (%)', default=60)
    shuffle_questions = models.BooleanField('Savollarni aralashtirish', default=True)
    shuffle_answers = models.BooleanField('Javoblarni aralashtirish', default=True)
    show_correct_answers = models.BooleanField('To\'g\'ri javoblarni ko\'rsatish', default=True)

    # Availability
    is_active = models.BooleanField('Faol', default=True)
    is_premium = models.BooleanField('Premium', default=False)
    start_date = models.DateTimeField('Boshlanish vaqti', null=True, blank=True)
    end_date = models.DateTimeField('Tugash vaqti', null=True, blank=True)

    # Stats
    total_attempts = models.PositiveIntegerField('Jami urinishlar', default=0)
    average_score = models.FloatField('O\'rtacha ball', default=0.0)

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tests'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Test'
        verbose_name_plural = 'Testlar'
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_available(self):
        """Test hozir mavjudmi"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        return True


class TestQuestion(models.Model):
    """Test va savol o'rtasidagi bog'lanish"""

    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Test savoli'
        verbose_name_plural = 'Test savollari'
        ordering = ['order']
        unique_together = ['test', 'question']


class TestAttempt(models.Model):
    """Test urinishi"""

    STATUS_CHOICES = [
        ('started', 'Boshlangan'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlangan'),
        ('timeout', 'Vaqt tugagan'),
        ('abandoned', 'Tashlab ketilgan'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='test_attempts',
        verbose_name='Foydalanuvchi'
    )
    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Test'
    )

    # Progress
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='started'
    )
    current_question = models.PositiveIntegerField('Joriy savol', default=0)

    # Results
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri javoblar', default=0)
    skipped_questions = models.PositiveIntegerField('O\'tkazib yuborilgan', default=0)

    # Score
    score = models.FloatField('Ball', default=0.0)
    percentage = models.FloatField('Foiz', default=0.0)
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)

    # Time
    time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)
    started_at = models.DateTimeField('Boshlangan vaqt', auto_now_add=True)
    completed_at = models.DateTimeField('Yakunlangan vaqt', null=True, blank=True)

    # AI Analysis
    ai_analysis = models.TextField('AI tahlili', blank=True)
    ai_recommendations = models.JSONField('AI tavsiyalari', default=list, blank=True)
    weak_topics = models.JSONField('Sust mavzular', default=list, blank=True)
    strong_topics = models.JSONField('Kuchli mavzular', default=list, blank=True)

    class Meta:
        verbose_name = 'Test urinishi'
        verbose_name_plural = 'Test urinishlari'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'test']),
            models.Index(fields=['status']),
            models.Index(fields=['started_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.test} ({self.percentage}%)"

    def calculate_results(self):
        """Natijalarni hisoblash"""
        self.percentage = round((self.correct_answers / self.total_questions) * 100,
                                1) if self.total_questions > 0 else 0
        self.score = self.correct_answers

        # XP hisoblash
        base_xp = self.correct_answers * 10
        if self.percentage >= 90:
            base_xp *= 2  # Bonus for excellent score
        elif self.percentage >= 70:
            base_xp *= 1.5
        self.xp_earned = int(base_xp)

        self.save()


class AttemptAnswer(models.Model):
    """Test urinishidagi javoblar"""

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Urinish'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
        verbose_name='Savol'
    )
    selected_answer = models.ForeignKey(
        Answer,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='selections',
        verbose_name='Tanlangan javob'
    )
    is_correct = models.BooleanField('To\'g\'ri', default=False)
    time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)
    answered_at = models.DateTimeField('Javob vaqti', auto_now_add=True)

    class Meta:
        verbose_name = 'Javob'
        verbose_name_plural = 'Javoblar'
        ordering = ['answered_at']
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user} - Q{self.question.id} - {'✓' if self.is_correct else '✗'}"


class SavedQuestion(models.Model):
    """Saqlangan savollar (keyinroq qaytish uchun)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_questions'
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='saved_by'
    )
    note = models.TextField('Eslatma', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saqlangan savol'
        verbose_name_plural = 'Saqlangan savollar'
        unique_together = ['user', 'question']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.question.id}"


# ============================================================
# ANALYTICS MODELS - AI va Data Collection uchun
# ============================================================

class UserTopicPerformance(models.Model):
    """Foydalanuvchining mavzu bo'yicha natijasi (avtomatik yangilanadi)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='topic_performances'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='user_performances'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='user_performances'
    )

    # Statistika
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri javoblar', default=0)

    # Vaqt
    total_time_spent = models.PositiveIntegerField('Jami vaqt (soniya)', default=0)
    avg_time_per_question = models.FloatField('O\'rtacha vaqt', default=0)

    # Score
    current_score = models.FloatField('Joriy ball (%)', default=0)
    best_score = models.FloatField('Eng yaxshi ball (%)', default=0)

    # Trend
    TREND_CHOICES = [
        ('improving', 'Yaxshilanmoqda'),
        ('stable', 'Barqaror'),
        ('declining', 'Pasaymoqda'),
    ]
    score_trend = models.CharField('Trend', max_length=20, choices=TREND_CHOICES, default='stable')

    # Status
    is_weak = models.BooleanField('Kuchsiz mavzu', default=False)
    is_strong = models.BooleanField('Kuchli mavzu', default=False)
    is_mastered = models.BooleanField('O\'zlashtirilgan', default=False)

    # Vaqt
    last_practiced = models.DateTimeField('Oxirgi mashq', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mavzu natijasi'
        verbose_name_plural = 'Mavzu natijalari'
        unique_together = ['user', 'topic']
        ordering = ['current_score']

    def __str__(self):
        return f"{self.user} - {self.topic} ({self.current_score}%)"

    def update_stats(self):
        """Statistikani yangilash"""
        if self.total_questions > 0:
            self.current_score = round((self.correct_answers / self.total_questions) * 100, 1)
            self.avg_time_per_question = round(self.total_time_spent / self.total_questions, 1)

        # Best score
        if self.current_score > self.best_score:
            self.best_score = self.current_score

        # Weak/Strong aniqlash
        if self.total_questions >= 10:
            self.is_weak = self.current_score < 50
            self.is_strong = self.current_score >= 80
            self.is_mastered = self.current_score >= 90 and self.total_questions >= 30

        self.save()


class UserSubjectPerformance(models.Model):
    """Foydalanuvchining fan bo'yicha umumiy natijasi"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subject_performances'
    )
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='user_subject_performances'
    )

    # Statistika
    total_tests = models.PositiveIntegerField('Jami testlar', default=0)
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)

    # Score
    average_score = models.FloatField('O\'rtacha ball (%)', default=0)
    best_score = models.FloatField('Eng yaxshi ball (%)', default=0)
    last_score = models.FloatField('Oxirgi ball (%)', default=0)

    # Vaqt
    total_time_spent = models.PositiveIntegerField('Jami vaqt (soniya)', default=0)

    # Rank
    subject_rank = models.PositiveIntegerField('Fan reytingi', null=True, blank=True)

    # Predicted
    predicted_dtm_score = models.FloatField('Bashorat DTM ball', default=0)

    last_practiced = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Fan natijasi'
        verbose_name_plural = 'Fan natijalari'
        unique_together = ['user', 'subject']

    def __str__(self):
        return f"{self.user} - {self.subject} ({self.average_score}%)"


class DailyUserStats(models.Model):
    """Kunlik statistika (har kuni avtomatik yaratiladi)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='daily_stats'
    )
    date = models.DateField('Sana')

    # Test statistikasi
    tests_taken = models.PositiveIntegerField('Testlar soni', default=0)
    questions_answered = models.PositiveIntegerField('Javob berilgan', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri', default=0)

    # Vaqt
    total_time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)
    sessions_count = models.PositiveIntegerField('Sessiyalar', default=0)

    # XP
    xp_earned = models.PositiveIntegerField('Olingan XP', default=0)

    # Faollik vaqti
    most_active_hour = models.PositiveIntegerField('Eng faol soat', null=True, blank=True)
    activity_hours = models.JSONField('Faollik soatlari', default=dict, blank=True)
    # {"08": 5, "09": 12, "20": 25, "21": 18}

    # Fan bo'yicha
    subjects_practiced = models.JSONField('Fanlar', default=dict, blank=True)
    # {"matematika": {"correct": 15, "total": 20}, "fizika": {...}}

    # Accuracy
    accuracy_rate = models.FloatField('Aniqlik (%)', default=0)

    class Meta:
        verbose_name = 'Kunlik statistika'
        verbose_name_plural = 'Kunlik statistikalar'
        unique_together = ['user', 'date']
        ordering = ['-date']

    def __str__(self):
        return f"{self.user} - {self.date}"

    def calculate_accuracy(self):
        if self.questions_answered > 0:
            self.accuracy_rate = round((self.correct_answers / self.questions_answered) * 100, 1)
        self.save()


class UserStudySession(models.Model):
    """O'qish sessiyasi (platformaga kirish-chiqish)"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_sessions'
    )

    # Vaqt
    started_at = models.DateTimeField('Boshlangan', auto_now_add=True)
    ended_at = models.DateTimeField('Tugagan', null=True, blank=True)
    duration = models.PositiveIntegerField('Davomiyligi (soniya)', default=0)

    # Faollik
    tests_taken = models.PositiveIntegerField('Testlar', default=0)
    questions_answered = models.PositiveIntegerField('Savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri', default=0)

    # Device
    device_type = models.CharField('Qurilma', max_length=20, default='unknown')
    # mobile, desktop, tablet

    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)

    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'O\'qish sessiyasi'
        verbose_name_plural = 'O\'qish sessiyalari'
        ordering = ['-started_at']

    def end_session(self):
        self.ended_at = timezone.now()
        self.duration = int((self.ended_at - self.started_at).total_seconds())
        self.is_active = False
        self.save()




class UserActivityLog(models.Model):
    """Foydalanuvchi harakatlari logi (barchasi)"""

    ACTION_TYPES = [
        ('login', 'Kirish'),
        ('logout', 'Chiqish'),
        ('test_start', 'Test boshlash'),
        ('test_complete', 'Test yakunlash'),
        ('question_answer', 'Savolga javob'),
        ('page_view', 'Sahifa ko\'rish'),
        ('ai_chat', 'AI suhbat'),
        ('competition_join', 'Musobaqaga qo\'shilish'),
        ('battle_start', 'Jang boshlash'),
        ('profile_update', 'Profil yangilash'),
        ('achievement_earn', 'Yutuqqa erishish'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='activity_logs'
    )

    action = models.CharField('Harakat', max_length=30, choices=ACTION_TYPES)

    # Details
    details = models.JSONField('Tafsilotlar', default=dict, blank=True)
    # {"test_id": 5, "score": 85, "time_spent": 1200}

    # Related objects
    subject = models.ForeignKey(Subject, on_delete=models.SET_NULL, null=True, blank=True)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, null=True, blank=True)

    # Meta
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    device_type = models.CharField(max_length=20, default='unknown')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Faoliyat logi'
        verbose_name_plural = 'Faoliyat loglari'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'action']),
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user} - {self.action} - {self.created_at}"


class UserAnalyticsSummary(models.Model):
    """Foydalanuvchi umumiy analytics (har kuni yangilanadi)"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='analytics_summary'
    )

    # Umumiy statistika
    total_study_time = models.PositiveIntegerField('Jami o\'qish vaqti (soat)', default=0)
    total_questions_solved = models.PositiveIntegerField('Jami savollar', default=0)
    total_tests_completed = models.PositiveIntegerField('Jami testlar', default=0)

    # O'rtacha ko'rsatkichlar
    overall_accuracy = models.FloatField('Umumiy aniqlik (%)', default=0)
    avg_session_duration = models.PositiveIntegerField('O\'rtacha sessiya (daqiqa)', default=0)
    avg_questions_per_day = models.FloatField('Kunlik savollar', default=0)

    # Eng yaxshi vaqt
    best_study_hours = models.JSONField('Eng yaxshi soatlar', default=list, blank=True)
    # [20, 21, 22] — kechqurun eng samarali

    best_study_days = models.JSONField('Eng yaxshi kunlar', default=list, blank=True)
    # ["monday", "wednesday", "saturday"]

    # Kuchli/kuchsiz
    weak_topics_count = models.PositiveIntegerField('Kuchsiz mavzular', default=0)
    strong_topics_count = models.PositiveIntegerField('Kuchli mavzular', default=0)
    mastered_topics_count = models.PositiveIntegerField('O\'zlashtirilgan', default=0)

    # Predicted
    predicted_dtm_score = models.PositiveIntegerField('Bashorat DTM ball', default=0)
    university_match_count = models.PositiveIntegerField('Mos universitetlar', default=0)

    # Streak
    current_streak = models.PositiveIntegerField('Joriy streak', default=0)
    longest_streak = models.PositiveIntegerField('Eng uzun streak', default=0)

    # Learning style (AI aniqlaydi)
    LEARNING_STYLES = [
        ('visual', 'Vizual'),
        ('reading', 'O\'qish'),
        ('practice', 'Amaliy'),
        ('mixed', 'Aralash'),
    ]
    learning_style = models.CharField('O\'qish uslubi', max_length=20, choices=LEARNING_STYLES, default='mixed')

    # Fatigue pattern
    avg_fatigue_time = models.PositiveIntegerField('Charchash vaqti (daqiqa)', default=45)

    last_calculated = models.DateTimeField('Oxirgi hisoblash', auto_now=True)

    class Meta:
        verbose_name = 'Analytics xulosa'
        verbose_name_plural = 'Analytics xulosalar'

    def __str__(self):
        return f"{self.user} - Analytics"