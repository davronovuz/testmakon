"""
TestMakon.uz — Online Judge Models
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class ProgrammingLanguage(models.Model):
    """Dasturlash tili — har biri o'z Docker image'i bilan"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)
    docker_image = models.CharField(max_length=200, help_text="Docker image nomi, masalan: python:3.12-slim")
    compile_cmd = models.CharField(max_length=500, blank=True, help_text="Kompilatsiya buyrug'i (C++, Java). Bo'sh = interpretatsiya")
    run_cmd = models.CharField(max_length=500, help_text="Ishga tushirish buyrug'i")
    file_extension = models.CharField(max_length=10, help_text="Fayl kengaytmasi, masalan: .py")
    monaco_language = models.CharField(max_length=50, help_text="Monaco editor tili, masalan: python")
    is_active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Dasturlash tili'
        verbose_name_plural = 'Dasturlash tillari'

    def __str__(self):
        return self.name


class CodingCategory(models.Model):
    """Masala kategoriyasi — Array, String, Recursion, ..."""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='bi-code-slash', help_text="Bootstrap icon class")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'

    def __str__(self):
        return self.name


class CodingProblem(models.Model):
    """Dasturlash masalasi"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Oson'),
        ('medium', "O'rta"),
        ('hard', 'Qiyin'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=300, unique=True)
    description = models.TextField(help_text="Masala sharti (HTML)")
    input_format = models.TextField(help_text="Kirish formati")
    output_format = models.TextField(help_text="Chiqish formati")
    constraints = models.TextField(blank=True, help_text="Cheklovlar")
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='easy')
    category = models.ForeignKey(CodingCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='problems')
    languages = models.ManyToManyField(ProgrammingLanguage, related_name='problems', help_text="Qo'llab-quvvatlanadigan tillar")
    starter_code = models.JSONField(default=dict, blank=True, help_text='{"python": "def solve():\\n    pass", "cpp": "..."}')
    time_limit = models.PositiveIntegerField(default=2, help_text="Sekundda (har bir test case uchun)")
    memory_limit = models.PositiveIntegerField(default=256, help_text="MB da")
    # Stats
    total_submissions = models.PositiveIntegerField(default=0)
    accepted_submissions = models.PositiveIntegerField(default=0)
    # Meta
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['order', 'difficulty', 'title']
        verbose_name = 'Masala'
        verbose_name_plural = 'Masalalar'

    def __str__(self):
        return f"#{self.order} {self.title}"

    @property
    def acceptance_rate(self):
        if self.total_submissions == 0:
            return 0
        return round(self.accepted_submissions / self.total_submissions * 100, 1)


class TestCase(models.Model):
    """Masala uchun test case"""
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE, related_name='test_cases')
    input_data = models.TextField(help_text="Kirish ma'lumotlari")
    expected_output = models.TextField(help_text="Kutilgan chiqish")
    is_sample = models.BooleanField(default=False, help_text="Foydalanuvchiga ko'rinadigan namuna")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Test case'
        verbose_name_plural = 'Test case\'lar'

    def __str__(self):
        label = "Namuna" if self.is_sample else "Yashirin"
        return f"{label} #{self.order} — {self.problem.title}"


class CodeSubmission(models.Model):
    """Foydalanuvchi kodi — yuborish"""
    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('running', 'Ishlamoqda'),
        ('accepted', 'Qabul qilindi'),
        ('wrong_answer', "Noto'g'ri javob"),
        ('time_limit', 'Vaqt chegarasi'),
        ('memory_limit', 'Xotira chegarasi'),
        ('runtime_error', 'Runtime xato'),
        ('compilation_error', 'Kompilatsiya xatosi'),
        ('internal_error', 'Ichki xato'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='code_submissions')
    problem = models.ForeignKey(CodingProblem, on_delete=models.CASCADE, related_name='submissions')
    language = models.ForeignKey(ProgrammingLanguage, on_delete=models.CASCADE)
    code = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    # Results
    results = models.JSONField(default=list, blank=True, help_text="Har bir test case natijasi")
    passed_count = models.PositiveIntegerField(default=0)
    total_count = models.PositiveIntegerField(default=0)
    execution_time = models.FloatField(null=True, blank=True, help_text="Eng uzoq test case vaqti (ms)")
    memory_used = models.FloatField(null=True, blank=True, help_text="Eng ko'p xotira (MB)")
    error_message = models.TextField(blank=True)
    # Meta
    is_sample_run = models.BooleanField(default=False, help_text="Faqat namuna testlar uchun sinov")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Yuborish'
        verbose_name_plural = 'Yuborishlar'

    def __str__(self):
        return f"{self.user} — {self.problem.title} [{self.get_status_display()}]"


class UserCodingStats(models.Model):
    """Foydalanuvchi dasturlash statistikasi"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='coding_stats')
    problems_solved = models.PositiveIntegerField(default=0)
    problems_attempted = models.PositiveIntegerField(default=0)
    easy_solved = models.PositiveIntegerField(default=0)
    medium_solved = models.PositiveIntegerField(default=0)
    hard_solved = models.PositiveIntegerField(default=0)
    total_submissions = models.PositiveIntegerField(default=0)
    # Tillar bo'yicha
    language_stats = models.JSONField(default=dict, blank=True, help_text='{"python": {"solved": 5, "submitted": 10}, ...}')
    # Streak
    current_streak = models.PositiveIntegerField(default=0)
    max_streak = models.PositiveIntegerField(default=0)
    last_solved_date = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Foydalanuvchi statistikasi'
        verbose_name_plural = 'Foydalanuvchi statistikalari'

    def __str__(self):
        return f"{self.user} — {self.problems_solved} yechilgan"
