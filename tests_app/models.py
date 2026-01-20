"""
TestMakon.uz - Test System Models
Production-ready test system with AI analysis support
"""

from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid


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