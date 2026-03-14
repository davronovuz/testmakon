"""
TestMakon.uz — Milliy Sertifikat Models
Universal architecture: barcha fanlar uchun bitta system
Question types: choice | grouped_af | short_open | multi_part
"""
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone


# ─────────────────────────────────────────────────────────────
# 1. SUBJECT (Fan)
# ─────────────────────────────────────────────────────────────

class CertSubject(models.Model):
    """Milliy sertifikat fanlari — mavjud Subject modeliga bog'liq"""

    subject = models.OneToOneField(
        'tests_app.Subject',
        on_delete=models.CASCADE,
        related_name='cert_subject',
        verbose_name='Fan'
    )
    description = models.TextField('Qo\'shimcha tavsif', blank=True)
    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    # Cached stats
    total_mocks = models.PositiveIntegerField('Jami mock testlar', default=0)
    free_mocks = models.PositiveIntegerField('Bepul mocklar', default=0)
    premium_mocks = models.PositiveIntegerField('Premium mocklar', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sertifikat Fani'
        verbose_name_plural = 'Sertifikat Fanlari'
        ordering = ['order', 'subject__name']

    def __str__(self):
        return self.subject.name

    def update_stats(self):
        mocks = self.mocks.filter(is_active=True)
        self.total_mocks = mocks.count()
        self.free_mocks = mocks.filter(is_free=True).count()
        self.premium_mocks = mocks.filter(is_free=False).count()
        self.save(update_fields=['total_mocks', 'free_mocks', 'premium_mocks'])


# ─────────────────────────────────────────────────────────────
# 2. MOCK TEST
# ─────────────────────────────────────────────────────────────

class CertMock(models.Model):
    """Mock test — har bir sertifikat imtihon varianti"""

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    cert_subject = models.ForeignKey(
        CertSubject,
        on_delete=models.CASCADE,
        related_name='mocks',
        verbose_name='Fan'
    )

    title = models.CharField('Mock nomi', max_length=200)
    slug = models.SlugField('Slug', max_length=200)
    description = models.TextField('Tavsif', blank=True)
    year = models.PositiveIntegerField('Yil', null=True, blank=True)
    version = models.CharField('Variant', max_length=20, blank=True)

    # Access control
    is_free = models.BooleanField('Bepul', default=False)
    is_active = models.BooleanField('Faol', default=True)

    # Config
    time_limit = models.PositiveIntegerField('Vaqt (daqiqa)', default=120)
    max_attempts = models.PositiveIntegerField('Max urinishlar (0=cheksiz)', default=0)

    # Cached
    questions_count = models.PositiveIntegerField('Savollar soni', default=0)
    total_points = models.PositiveIntegerField('Jami ball', default=0)

    order = models.PositiveIntegerField('Tartib', default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Mock Test'
        verbose_name_plural = 'Mock Testlar'
        ordering = ['cert_subject', 'order', '-year']
        unique_together = ['cert_subject', 'slug']

    def __str__(self):
        return f"{self.cert_subject.subject.name} — {self.title}"

    def update_cached_stats(self):
        qs = self.questions.filter(is_active=True)
        self.questions_count = qs.count()
        self.total_points = sum(q.points for q in qs)
        self.save(update_fields=['questions_count', 'total_points'])


# ─────────────────────────────────────────────────────────────
# 3. UNIVERSAL QUESTION
# ─────────────────────────────────────────────────────────────

class CertQuestion(models.Model):
    """
    Universal savol modeli.
    Type-ga qarab bog'liq detail model faollashadi:
    - choice      → CertChoice (FK)
    - grouped_af  → CertGroupedOption + CertGroupedItem
    - short_open  → CertShortOpen (OneToOne)
    - multi_part  → CertMultiPart (FK)
    """

    QUESTION_TYPES = [
        ('choice', 'A/B/C/D tanlov (1–32)'),
        ('grouped_af', 'A–F guruhlangan (33–35)'),
        ('short_open', 'Qisqa ochiq javob'),
        ('multi_part', 'Ko\'p qismli (a/b/c/d)'),
    ]

    DIFFICULTY_CHOICES = [
        ('easy',   'Oson'),
        ('medium', "O'rta"),
        ('hard',   'Qiyin'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    mock = models.ForeignKey(
        CertMock,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='Mock'
    )

    # Position
    number = models.PositiveIntegerField('Savol raqami')
    question_type = models.CharField('Savol turi', max_length=20, choices=QUESTION_TYPES)

    # Content
    text = models.TextField('Savol matni', blank=True)
    image = models.ImageField('Rasm', upload_to='cert/questions/', blank=True, null=True)

    # Metadata
    points = models.PositiveIntegerField('Ball', default=1)
    topic = models.ForeignKey(
        'tests_app.Topic',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Mavzu'
    )
    source = models.CharField('Manba', max_length=200, blank=True)
    year = models.PositiveIntegerField('Yil', null=True, blank=True)

    # Hints & explanation
    explanation = models.TextField('Tushuntirish', blank=True)
    hint = models.TextField('Maslahat', blank=True)

    # Difficulty & stats (IRT scoring uchun)
    difficulty = models.CharField('Qiyinlik', max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    times_answered = models.PositiveIntegerField('Javob berilgan', default=0)
    times_correct  = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)

    # Control
    requires_manual_check = models.BooleanField('Qo\'lda tekshirish', default=False)
    is_active = models.BooleanField('Faol', default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Savol'
        verbose_name_plural = 'Savollar'
        ordering = ['number']
        unique_together = ['mock', 'number']

    def __str__(self):
        return f"#{self.number} [{self.get_question_type_display()}] — {self.mock}"


# ─────────────────────────────────────────────────────────────
# 4. CHOICE (A/B/C/D)
# ─────────────────────────────────────────────────────────────

class CertChoice(models.Model):
    """choice type uchun variantlar"""

    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='choices',
        verbose_name='Savol'
    )
    label = models.CharField('Harf', max_length=1)   # A, B, C, D
    text = models.TextField('Matn')
    image = models.ImageField('Rasm', upload_to='cert/choices/', blank=True, null=True)
    is_correct = models.BooleanField('To\'g\'ri javob', default=False)
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Variant'
        verbose_name_plural = 'Variantlar'
        ordering = ['order', 'label']

    def __str__(self):
        return f"{self.label}) {self.text[:60]}"


# ─────────────────────────────────────────────────────────────
# 5. GROUPED A–F
# ─────────────────────────────────────────────────────────────

class CertGroupedOption(models.Model):
    """grouped_af: umumiy A–F variantlar"""

    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='grouped_options',
        verbose_name='Savol'
    )
    label = models.CharField('Harf', max_length=1)   # A, B, C, D, E, F
    text = models.TextField('Matn')
    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Guruh varianti'
        verbose_name_plural = 'Guruh variantlari'
        ordering = ['order', 'label']

    def __str__(self):
        return f"{self.label}) {self.text[:60]}"


class CertGroupedItem(models.Model):
    """grouped_af: har bir sub-item (33, 34, 35)"""

    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='grouped_items',
        verbose_name='Savol'
    )
    item_number = models.PositiveIntegerField('Item raqami')   # 1, 2, 3
    text = models.TextField('Item matni')
    image = models.ImageField('Rasm', upload_to='cert/grouped_items/', blank=True, null=True)
    correct_option = models.ForeignKey(
        CertGroupedOption,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='correct_for_items',
        verbose_name='To\'g\'ri variant'
    )

    class Meta:
        verbose_name = 'Guruh elementi'
        verbose_name_plural = 'Guruh elementlari'
        ordering = ['item_number']

    def __str__(self):
        return f"Item {self.item_number} — {self.question}"


# ─────────────────────────────────────────────────────────────
# 6. SHORT OPEN
# ─────────────────────────────────────────────────────────────

class CertShortOpen(models.Model):
    """short_open: qisqa ochiq javob"""

    ANSWER_TYPES = [
        ('text', 'Matn'),
        ('integer', 'Butun son'),
        ('float', 'Kasr son'),
        ('formula', 'Formula'),
    ]

    question = models.OneToOneField(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='short_open',
        verbose_name='Savol'
    )
    correct_answer = models.TextField('To\'g\'ri javob')
    answer_type = models.CharField('Javob turi', max_length=10, choices=ANSWER_TYPES, default='text')
    tolerance = models.FloatField('Og\'ish (float uchun)', default=0.0)
    case_sensitive = models.BooleanField('Katta-kichik harf', default=False)

    class Meta:
        verbose_name = 'Qisqa ochiq javob'
        verbose_name_plural = 'Qisqa ochiq javoblar'

    def __str__(self):
        return f"ShortOpen: {self.correct_answer[:40]}"


# ─────────────────────────────────────────────────────────────
# 7. MULTI PART (a/b/c/d)
# ─────────────────────────────────────────────────────────────

class CertMultiPart(models.Model):
    """multi_part: bitta umumiy context uchun sub-partlar"""

    ANSWER_TYPES = [
        ('text', 'Matn'),
        ('integer', 'Butun son'),
        ('float', 'Kasr son'),
        ('choice', 'Variant tanlov'),
    ]

    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='parts',
        verbose_name='Savol'
    )
    part_label = models.CharField('Part (a/b/c/d)', max_length=2)
    text = models.TextField('Part savoli')
    image = models.ImageField('Rasm', upload_to='cert/parts/', blank=True, null=True)
    points = models.PositiveIntegerField('Ball', default=1)

    # Answer
    correct_answer = models.TextField('To\'g\'ri javob', blank=True)
    answer_type = models.CharField('Javob turi', max_length=10, choices=ANSWER_TYPES, default='text')
    requires_manual_check = models.BooleanField('Qo\'lda tekshirish', default=False)
    tolerance = models.FloatField('Og\'ish', default=0.0)

    order = models.PositiveIntegerField('Tartib', default=0)

    class Meta:
        verbose_name = 'Part'
        verbose_name_plural = 'Partlar'
        ordering = ['order', 'part_label']

    def __str__(self):
        return f"Part {self.part_label} — {self.question}"


# ─────────────────────────────────────────────────────────────
# 8. MOCK ATTEMPT
# ─────────────────────────────────────────────────────────────

class CertMockAttempt(models.Model):
    """User mock-test urinishi"""

    STATUS_CHOICES = [
        ('started', 'Boshlangan'),
        ('in_progress', 'Davom etmoqda'),
        ('completed', 'Yakunlangan'),
        ('timeout', 'Vaqt tugagan'),
    ]

    GRADE_CHOICES = [
        ('A+', 'A+ — 70 ball va undan yuqori'),
        ('A',  'A — 65–69.9'),
        ('B+', 'B+ — 60–64.9'),
        ('B',  'B — 55–59.9'),
        ('C+', 'C+ — 50–54.9'),
        ('C',  'C — 46–49.9'),
        ('',   'Sertifikat yo\'q (45 va pastda)'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cert_attempts',
        verbose_name='Foydalanuvchi'
    )
    mock = models.ForeignKey(
        CertMock,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name='Mock'
    )
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='started')

    # Time
    started_at = models.DateTimeField('Boshlangan', auto_now_add=True)
    completed_at = models.DateTimeField('Yakunlangan', null=True, blank=True)
    time_spent = models.PositiveIntegerField('Sarflangan vaqt (soniya)', default=0)

    # Results
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    correct_answers = models.PositiveIntegerField('To\'g\'ri', default=0)
    wrong_answers = models.PositiveIntegerField('Noto\'g\'ri', default=0)
    skipped_questions = models.PositiveIntegerField('O\'tkazilgan', default=0)
    total_points = models.PositiveIntegerField('Jami ball', default=0)
    earned_points = models.PositiveIntegerField('Olingan ball', default=0)
    percentage = models.FloatField('Foiz', default=0.0)

    # Grade
    grade = models.CharField('Baho', max_length=2, choices=GRADE_CHOICES, blank=True)
    feedback = models.CharField('Fikr', max_length=300, blank=True)

    # Meta
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)

    class Meta:
        verbose_name = 'Mock Urinishi'
        verbose_name_plural = 'Mock Urinishlari'
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user} — {self.mock} ({self.status})"

    def calculate_results(self):
        """IRT asosida natijalarni hisoblash (maks 100 ball)"""
        answers = self.answers.select_related('question').all()
        correct  = answers.filter(is_correct=True).count()
        wrong    = answers.filter(is_correct=False, is_skipped=False).count()
        skipped  = answers.filter(is_skipped=True).count()
        total_q  = self.mock.questions_count or 1

        # IRT score (0–100)
        irt = self._compute_irt_score(answers, correct, total_q)

        self.correct_answers   = correct
        self.wrong_answers     = wrong
        self.skipped_questions = skipped
        self.total_questions   = total_q
        self.total_points      = 100
        self.earned_points     = irt
        self.percentage        = irt
        self.grade, self.feedback = self._compute_grade(irt)
        self.completed_at = timezone.now()
        self.status = 'completed'
        self.save()

    @staticmethod
    def _compute_irt_score(answers, correct_count, total_q):
        """
        1) To'g'ri javoblar sonidan bazaviy ball (jadval bo'yicha, 40 savolga o'lchab)
        2) Har savol qiyinligiga qarab IRT korreksiyasi
        """
        # --- Base score ---
        scale = 40  # standart asos
        if total_q and total_q != scale:
            scaled_correct = round(correct_count * scale / total_q)
        else:
            scaled_correct = correct_count

        if   scaled_correct >= 34: base = 70 + round((scaled_correct - 34) / 6 * 30)
        elif scaled_correct >= 31: base = 65 + round((scaled_correct - 31) / 3 * 5)
        elif scaled_correct >= 28: base = 60 + round((scaled_correct - 28) / 3 * 5)
        elif scaled_correct >= 25: base = 55 + round((scaled_correct - 25) / 3 * 5)
        elif scaled_correct >= 22: base = 50 + round((scaled_correct - 22) / 3 * 5)
        elif scaled_correct >= 19: base = 46 + round((scaled_correct - 19) / 3 * 4)
        elif scaled_correct > 0:   base = round(scaled_correct / 18 * 45)
        else:                      base = 0

        # --- IRT korreksiyasi (maks ±8 ball) ---
        adj = 0.0
        for ans in answers:
            q = ans.question
            if q.times_answered >= 10:
                cr = q.times_correct / q.times_answered   # 0–1, 1=koʻpchilik toʻgʻri
                difficulty = 1 - cr                        # 0=oson, 1=qiyin
            else:
                difficulty = 0.5  # neytral

            if ans.is_correct:
                adj += (difficulty - 0.3) * 4   # qiyin → katta bonus
            elif not ans.is_skipped:
                adj -= (0.7 - difficulty) * 3   # oson savolni xato → katta jarima

        # Normallash: ±8 ball
        if total_q:
            adj = max(-8, min(8, adj / total_q * 8))

        score = round(base + adj, 1)
        return max(0, min(100, score))

    @staticmethod
    def _compute_grade(score):
        if   score >= 70: return 'A+', "Ajoyib! Sertifikat olishga to'liq loyiqsiz!"
        elif score >= 65: return 'A',  "Zo'r natija! Sertifikat olasiz!"
        elif score >= 60: return 'B+', "Yaxshi! Sertifikat olasiz."
        elif score >= 55: return 'B',  "Qoniqarli. Sertifikat olasiz."
        elif score >= 50: return 'C+', "O'rtacha. Sertifikat olasiz."
        elif score >= 46: return 'C',  "Minimal daraja. Sertifikat olasiz."
        else:             return '',   "Sertifikat yo'q. Ko'proq tayyorlaning!"


# ─────────────────────────────────────────────────────────────
# 9. ATTEMPT ANSWER (Universal)
# ─────────────────────────────────────────────────────────────

class CertAttemptAnswer(models.Model):
    """
    Universal javob modeli — barcha savol turlari uchun.

    choice      → selected_choice (FK)
    short_open  → text_answer (CharField)
    grouped_af  → structured_answer (JSON): {"1": choice_id, "2": choice_id, "3": choice_id}
    multi_part  → structured_answer (JSON): {"a": "javob", "b": "javob"}
    """

    attempt = models.ForeignKey(
        CertMockAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name='Urinish'
    )
    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
        verbose_name='Savol'
    )

    # choice → FK
    selected_choice = models.ForeignKey(
        CertChoice,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Tanlangan variant'
    )

    # short_open → text
    text_answer = models.TextField('Matnli javob', blank=True)

    # grouped_af, multi_part → JSON
    # grouped_af: {item_id: option_id, ...}
    # multi_part: {part_label: answer_text, ...}
    structured_answer = models.JSONField('Tuzilgan javob', null=True, blank=True)

    # Result
    is_correct = models.BooleanField('To\'g\'ri', null=True, blank=True)
    is_skipped = models.BooleanField('O\'tkazildi', default=False)
    earned_points = models.FloatField('Olingan ball', default=0)
    requires_manual_check = models.BooleanField('Qo\'lda tekshirish', default=False)
    checked_at = models.DateTimeField('Tekshirilgan', null=True, blank=True)

    answered_at = models.DateTimeField('Javob vaqti', auto_now=True)

    class Meta:
        verbose_name = 'Urinish Javobi'
        verbose_name_plural = 'Urinish Javoblari'
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"Answer #{self.question.number} — attempt {self.attempt_id}"

    def auto_check(self):
        """Avtomatik tekshirish — question type ga qarab"""
        q = self.question
        qtype = q.question_type

        if self.is_skipped:
            self.is_correct = False
            self.earned_points = 0
            self.checked_at = timezone.now()
            self.save(update_fields=['is_correct', 'earned_points', 'checked_at'])
            return

        if qtype == 'choice':
            self.is_correct = (
                self.selected_choice is not None and
                self.selected_choice.is_correct
            )
            self.earned_points = q.points if self.is_correct else 0

        elif qtype == 'grouped_af':
            if not self.structured_answer:
                self.is_correct = False
                self.earned_points = 0
            else:
                items = q.grouped_items.select_related('correct_option').all()
                correct_count = 0
                for item in items:
                    user_choice_id = self.structured_answer.get(str(item.id))
                    if item.correct_option and str(item.correct_option.id) == str(user_choice_id):
                        correct_count += 1
                self.is_correct = (correct_count == items.count())
                self.earned_points = q.points if self.is_correct else 0

        elif qtype == 'short_open':
            try:
                detail = q.short_open
            except CertShortOpen.DoesNotExist:
                self.requires_manual_check = True
                self.save(update_fields=['requires_manual_check'])
                return

            user_ans = self.text_answer.strip()
            correct = detail.correct_answer.strip()

            if detail.answer_type == 'text':
                if not detail.case_sensitive:
                    self.is_correct = user_ans.lower() == correct.lower()
                else:
                    self.is_correct = user_ans == correct
            elif detail.answer_type in ('integer', 'float'):
                try:
                    diff = abs(float(user_ans) - float(correct))
                    self.is_correct = diff <= detail.tolerance
                except ValueError:
                    self.is_correct = False
            else:
                self.requires_manual_check = True
                self.save(update_fields=['requires_manual_check'])
                return

            self.earned_points = q.points if self.is_correct else 0

        elif qtype == 'multi_part':
            parts = q.parts.all()
            if any(p.requires_manual_check for p in parts):
                self.requires_manual_check = True
                self.save(update_fields=['requires_manual_check'])
                return

            if not self.structured_answer:
                self.is_correct = False
                self.earned_points = 0
            else:
                total_pts = 0
                all_correct = True
                for part in parts:
                    user_part = str(self.structured_answer.get(part.part_label, '')).strip()
                    correct_part = part.correct_answer.strip()
                    try:
                        diff = abs(float(user_part) - float(correct_part))
                        part_ok = diff <= part.tolerance
                    except ValueError:
                        part_ok = (user_part.lower() == correct_part.lower())
                    if part_ok:
                        total_pts += part.points
                    else:
                        all_correct = False
                self.is_correct = all_correct
                self.earned_points = total_pts

        self.checked_at = timezone.now()
        self.save(update_fields=['is_correct', 'earned_points', 'requires_manual_check', 'checked_at'])


# ─────────────────────────────────────────────────────────────
# 10. SAVED QUESTION
# ─────────────────────────────────────────────────────────────

class CertSavedQuestion(models.Model):
    """Foydalanuvchi saqlab qo'ygan sertifikat savollari"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cert_saved_questions',
        verbose_name='Foydalanuvchi'
    )
    question = models.ForeignKey(
        CertQuestion,
        on_delete=models.CASCADE,
        related_name='saved_by',
        verbose_name='Savol'
    )
    note = models.TextField('Eslatma', blank=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Saqlangan savol'
        verbose_name_plural = 'Saqlangan savollar'
        unique_together = ['user', 'question']
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user} — #{self.question.number}"
