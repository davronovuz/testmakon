"""
TestMakon.uz - AI Core Models
AI Mentor, Recommendations, Study Plans
"""

from django.db import models
from django.conf import settings
import uuid


class AIConversation(models.Model):
    """AI Mentor bilan suhbat"""

    CONVERSATION_TYPES = [
        ('mentor', 'AI Mentor'),
        ('tutor', 'Mavzu tushuntirish'),
        ('advisor', 'Universitet maslahati'),
        ('analyzer', 'Test tahlili'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_conversations'
    )

    conversation_type = models.CharField(
        'Suhbat turi',
        max_length=20,
        choices=CONVERSATION_TYPES,
        default='mentor'
    )

    title = models.CharField('Sarlavha', max_length=200, blank=True)

    # Related objects
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    topic = models.ForeignKey(
        'tests_app.Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )
    test_attempt = models.ForeignKey(
        'tests_app.TestAttempt',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ai_conversations'
    )

    # Stats
    message_count = models.PositiveIntegerField('Xabarlar soni', default=0)

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'AI Suhbat'
        verbose_name_plural = 'AI Suhbatlar'
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user} - {self.conversation_type} - {self.title or 'Yangi suhbat'}"


class AIMessage(models.Model):
    """AI suhbatidagi xabar"""

    ROLE_CHOICES = [
        ('user', 'Foydalanuvchi'),
        ('assistant', 'AI'),
        ('system', 'Tizim'),
    ]

    conversation = models.ForeignKey(
        AIConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    role = models.CharField('Rol', max_length=20, choices=ROLE_CHOICES)
    content = models.TextField('Matn')

    # For assistant messages
    model_used = models.CharField('Ishlatilgan model', max_length=50, blank=True)
    tokens_used = models.PositiveIntegerField('Tokenlar', default=0)

    # Feedback
    is_helpful = models.BooleanField('Foydali', null=True, blank=True)
    feedback = models.TextField('Fikr-mulohaza', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'AI Xabar'
        verbose_name_plural = 'AI Xabarlar'
        ordering = ['created_at']

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class AIRecommendation(models.Model):
    """AI tavsiyalari"""

    RECOMMENDATION_TYPES = [
        ('study', 'O\'qish tavsiyasi'),
        ('topic', 'Mavzu tavsiyasi'),
        ('university', 'Universitet tavsiyasi'),
        ('strategy', 'Strategiya'),
        ('motivation', 'Motivatsiya'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Past'),
        ('medium', 'O\'rta'),
        ('high', 'Yuqori'),
        ('critical', 'Muhim'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ai_recommendations'
    )

    recommendation_type = models.CharField(
        'Turi',
        max_length=20,
        choices=RECOMMENDATION_TYPES
    )
    priority = models.CharField(
        'Muhimlik',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    title = models.CharField('Sarlavha', max_length=200)
    content = models.TextField('Mazmun')

    # Related objects
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    topic = models.ForeignKey(
        'tests_app.Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Action
    action_url = models.CharField('Havola', max_length=500, blank=True)
    action_text = models.CharField('Tugma matni', max_length=100, blank=True)

    # Status
    is_read = models.BooleanField('O\'qilgan', default=False)
    is_dismissed = models.BooleanField('Yopilgan', default=False)
    is_completed = models.BooleanField('Bajarilgan', default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Amal qilish muddati', null=True, blank=True)

    class Meta:
        verbose_name = 'AI Tavsiya'
        verbose_name_plural = 'AI Tavsiyalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"


class StudyPlan(models.Model):
    """AI tomonidan yaratilgan o'quv rejasi"""

    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('paused', 'To\'xtatilgan'),
        ('completed', 'Yakunlangan'),
        ('abandoned', 'Tashlab ketilgan'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='study_plans'
    )

    title = models.CharField('Sarlavha', max_length=200)
    description = models.TextField('Tavsif', blank=True)

    # Target
    target_exam_date = models.DateField('Imtihon sanasi', null=True, blank=True)
    target_score = models.PositiveIntegerField('Maqsadli ball', null=True, blank=True)
    target_university = models.ForeignKey(
        'universities.University',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    target_direction = models.ForeignKey(
        'universities.Direction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Subjects to study
    subjects = models.ManyToManyField(
        'tests_app.Subject',
        related_name='study_plans'
    )

    # Schedule
    daily_hours = models.FloatField('Kunlik soatlar', default=2.0)
    weekly_days = models.PositiveIntegerField('Haftalik kunlar', default=6)

    # Status
    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    # Progress
    total_tasks = models.PositiveIntegerField('Jami vazifalar', default=0)
    completed_tasks = models.PositiveIntegerField('Bajarilgan vazifalar', default=0)
    progress_percentage = models.FloatField('Progress (%)', default=0.0)

    # AI generated content
    ai_analysis = models.TextField('AI tahlili', blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'O\'quv reja'
        verbose_name_plural = 'O\'quv rejalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"

    def update_progress(self):
        """Progressni yangilash"""
        if self.total_tasks > 0:
            self.progress_percentage = round(
                (self.completed_tasks / self.total_tasks) * 100, 1
            )
            self.save()


class StudyPlanTask(models.Model):
    """O'quv reja vazifalari"""

    TASK_TYPES = [
        ('study', 'O\'qish'),
        ('test', 'Test yechish'),
        ('review', 'Takrorlash'),
        ('practice', 'Mashq'),
    ]

    study_plan = models.ForeignKey(
        StudyPlan,
        on_delete=models.CASCADE,
        related_name='tasks'
    )

    title = models.CharField('Sarlavha', max_length=200)
    description = models.TextField('Tavsif', blank=True)
    task_type = models.CharField(
        'Turi',
        max_length=20,
        choices=TASK_TYPES,
        default='study'
    )

    # Related content
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    topic = models.ForeignKey(
        'tests_app.Topic',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    test = models.ForeignKey(
        'tests_app.Test',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    # Schedule
    scheduled_date = models.DateField('Rejalashtirilgan sana')
    estimated_minutes = models.PositiveIntegerField('Taxminiy vaqt (daqiqa)', default=30)
    questions_count = models.PositiveIntegerField('Savollar soni', null=True, blank=True)

    # Status
    is_completed = models.BooleanField('Bajarilgan', default=False)
    completed_at = models.DateTimeField('Bajarilgan vaqt', null=True, blank=True)
    actual_minutes = models.PositiveIntegerField('Sarflangan vaqt', null=True, blank=True)

    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Reja vazifasi'
        verbose_name_plural = 'Reja vazifalari'
        ordering = ['scheduled_date', 'order']

    def __str__(self):
        return f"{self.study_plan.user} - {self.title}"


class WeakTopicAnalysis(models.Model):
    """Sust mavzular tahlili"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='weak_topics'
    )

    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.CASCADE
    )
    topic = models.ForeignKey(
        'tests_app.Topic',
        on_delete=models.CASCADE
    )

    # Stats
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    accuracy_rate = models.FloatField('To\'g\'rilik (%)', default=0.0)

    # AI recommendation
    recommendation = models.TextField('AI tavsiyasi', blank=True)
    priority_score = models.FloatField('Muhimlik bali', default=0.0)

    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sust mavzu'
        verbose_name_plural = 'Sust mavzular'
        unique_together = ['user', 'topic']
        ordering = ['accuracy_rate']

    def __str__(self):
        return f"{self.user} - {self.topic} ({self.accuracy_rate}%)"