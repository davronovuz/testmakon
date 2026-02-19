"""
TestMakon.uz - Accounts Models
Production-ready Custom User Model with gamification
"""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid


class UserManager(BaseUserManager):
    """Custom User Manager"""

    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('Telefon raqam kiritilishi shart')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser uchun is_staff=True bo\'lishi kerak')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser uchun is_superuser=True bo\'lishi kerak')

        return self.create_user(phone_number, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User Model - TestMakon.uz
    Phone-based authentication with full gamification support
    """

    # Remove default username field
    username = None

    # UUID for public identification
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Phone number as primary identifier
    phone_regex = RegexValidator(
        regex=r'^\+998\d{9}$',
        message="Telefon raqam +998XXXXXXXXX formatida bo'lishi kerak"
    )
    phone_number = models.CharField(
        'Telefon raqam',
        validators=[phone_regex],
        max_length=13,
        unique=True,
        db_index=True
    )

    # Personal information
    email = models.EmailField('Email', blank=True, null=True)
    # Telegram
    telegram_id = models.BigIntegerField('Telegram ID', unique=True, null=True, blank=True, db_index=True)
    telegram_username = models.CharField('Telegram username', max_length=100, blank=True)
    telegram_photo_url = models.URLField('Telegram foto', blank=True)

    first_name = models.CharField('Ism', max_length=50)
    last_name = models.CharField('Familiya', max_length=50)
    middle_name = models.CharField('Otasining ismi', max_length=50, blank=True)

    # Profile
    avatar = models.ImageField(
        'Profil rasmi',
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True
    )
    bio = models.TextField('Bio', max_length=500, blank=True)
    birth_date = models.DateField('Tug\'ilgan sana', blank=True, null=True)

    # Education info
    EDUCATION_CHOICES = [
        ('9', '9-sinf'),
        ('10', '10-sinf'),
        ('11', '11-sinf'),
        ('graduate', 'Bitiruvchi'),
        ('student', 'Talaba'),
        ('other', 'Boshqa'),
    ]
    education_level = models.CharField(
        'Ta\'lim darajasi',
        max_length=20,
        choices=EDUCATION_CHOICES,
        default='11'
    )
    school_name = models.CharField('Maktab/Kollej nomi', max_length=200, blank=True)
    region = models.CharField('Viloyat', max_length=100, blank=True)
    district = models.CharField('Tuman', max_length=100, blank=True)

    # Target university/direction
    target_university = models.ForeignKey(
        'universities.University',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_users',
        verbose_name='Maqsadli universitet'
    )
    target_direction = models.ForeignKey(
        'universities.Direction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='target_users',
        verbose_name='Maqsadli yo\'nalish'
    )

    # Gamification - XP & Levels
    LEVEL_CHOICES = [
        ('beginner', 'Boshlang\'ich'),
        ('elementary', 'Oddiy'),
        ('intermediate', 'O\'rta'),
        ('advanced', 'Yuqori'),
        ('expert', 'Ekspert'),
        ('master', 'Master'),
        ('legend', 'Legenda'),
    ]
    xp_points = models.PositiveIntegerField('XP ballari', default=0)
    level = models.CharField('Daraja', max_length=20, choices=LEVEL_CHOICES, default='beginner')

    # Streak system
    current_streak = models.PositiveIntegerField('Joriy streak', default=0)
    longest_streak = models.PositiveIntegerField('Eng uzun streak', default=0)
    last_activity_date = models.DateField('Oxirgi faollik', null=True, blank=True)

    # Statistics
    total_tests_taken = models.PositiveIntegerField('Jami testlar', default=0)
    total_correct_answers = models.PositiveIntegerField('To\'g\'ri javoblar', default=0)
    total_wrong_answers = models.PositiveIntegerField('Noto\'g\'ri javoblar', default=0)
    average_score = models.FloatField('O\'rtacha ball', default=0.0)

    # Competition stats
    competitions_participated = models.PositiveIntegerField('Musobaqalar soni', default=0)
    competitions_won = models.PositiveIntegerField('Yutilgan musobaqalar', default=0)

    # Ranking
    global_rank = models.PositiveIntegerField('Umumiy reyting', null=True, blank=True)
    weekly_rank = models.PositiveIntegerField('Haftalik reyting', null=True, blank=True)

    # Premium features
    is_premium = models.BooleanField('Premium foydalanuvchi', default=False)
    premium_until = models.DateTimeField('Premium muddati', null=True, blank=True)

    # Verification
    is_phone_verified = models.BooleanField('Telefon tasdiqlangan', default=False)
    is_email_verified = models.BooleanField('Email tasdiqlangan', default=False)

    # Timestamps
    created_at = models.DateTimeField('Ro\'yxatdan o\'tgan', auto_now_add=True)
    updated_at = models.DateTimeField('Yangilangan', auto_now=True)

    # Settings
    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = UserManager()

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['xp_points']),
            models.Index(fields=['global_rank']),
            models.Index(fields=['level']),
        ]

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """To'liq ism"""
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def accuracy_rate(self):
        """To'g'ri javoblar foizi"""
        total = self.total_correct_answers + self.total_wrong_answers
        if total == 0:
            return 0
        return round((self.total_correct_answers / total) * 100, 1)

    def add_xp(self, points):
        """XP qo'shish va level yangilash"""
        self.xp_points += points
        self.update_level()
        self.save()

    def update_level(self):
        """XP ga qarab level yangilash"""
        if self.xp_points >= 50000:
            self.level = 'legend'
        elif self.xp_points >= 25000:
            self.level = 'master'
        elif self.xp_points >= 10000:
            self.level = 'expert'
        elif self.xp_points >= 5000:
            self.level = 'advanced'
        elif self.xp_points >= 2000:
            self.level = 'intermediate'
        elif self.xp_points >= 500:
            self.level = 'elementary'
        else:
            self.level = 'beginner'

    def update_streak(self):
        """Streak yangilash"""
        today = timezone.now().date()

        if self.last_activity_date is None:
            self.current_streak = 1
        elif self.last_activity_date == today:
            pass  # Already updated today
        elif self.last_activity_date == today - timezone.timedelta(days=1):
            self.current_streak += 1
        else:
            self.current_streak = 1

        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_activity_date = today
        self.save()

    def get_avatar_url(self):
        """Avatar URL yoki default"""
        if self.avatar:
            return self.avatar.url
        return '/static/images/default-avatar.png'


class Badge(models.Model):
    """Yutuq nishonlari"""

    BADGE_TYPES = [
        ('streak', 'Streak'),
        ('test', 'Test'),
        ('competition', 'Musobaqa'),
        ('xp', 'XP'),
        ('special', 'Maxsus'),
    ]

    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif')
    badge_type = models.CharField('Turi', max_length=20, choices=BADGE_TYPES)
    icon = models.ImageField('Ikonka', upload_to='badges/')
    xp_reward = models.PositiveIntegerField('XP mukofot', default=0)
    requirement_value = models.PositiveIntegerField('Talab qilingan qiymat', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Badge'
        verbose_name_plural = 'Badgelar'
        ordering = ['badge_type', 'requirement_value']

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    """Foydalanuvchi badgelari"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField('Olingan vaqt', auto_now_add=True)

    class Meta:
        verbose_name = 'Foydalanuvchi badge'
        verbose_name_plural = 'Foydalanuvchi badgelari'
        unique_together = ['user', 'badge']
        ordering = ['-earned_at']

    def __str__(self):
        return f"{self.user} - {self.badge}"


class Friendship(models.Model):
    """Do'stlik tizimi"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('accepted', 'Qabul qilingan'),
        ('rejected', 'Rad etilgan'),
        ('blocked', 'Bloklangan'),
    ]

    from_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendships_sent'
    )
    to_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='friendships_received'
    )
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Do\'stlik'
        verbose_name_plural = 'Do\'stliklar'
        unique_together = ['from_user', 'to_user']

    def __str__(self):
        return f"{self.from_user} -> {self.to_user} ({self.status})"


class UserActivity(models.Model):
    """Foydalanuvchi faoliyati tarixi"""

    ACTIVITY_TYPES = [
        ('login', 'Kirish'),
        ('test_complete', 'Test yakunlash'),
        ('competition_join', 'Musobaqaga qo\'shilish'),
        ('badge_earn', 'Badge olish'),
        ('level_up', 'Level ko\'tarilish'),
        ('friend_add', 'Do\'st qo\'shish'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField('Faoliyat turi', max_length=30, choices=ACTIVITY_TYPES)
    description = models.TextField('Tavsif', blank=True)
    xp_earned = models.IntegerField('Olingan XP', default=0)
    metadata = models.JSONField('Qo\'shimcha ma\'lumot', default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Faoliyat'
        verbose_name_plural = 'Faoliyatlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.activity_type}"


class PhoneVerification(models.Model):
    """Telefon tasdiqlash kodlari"""

    phone_number = models.CharField('Telefon raqam', max_length=13)
    code = models.CharField('Kod', max_length=6)
    is_used = models.BooleanField('Ishlatilgan', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Amal qilish muddati')

    class Meta:
        verbose_name = 'Telefon tasdiqlash'
        verbose_name_plural = 'Telefon tasdiqlashlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.phone_number} - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired


class TelegramAuthCode(models.Model):
    """Telegram bot orqali autentifikatsiya kodlari"""

    telegram_id = models.BigIntegerField('Telegram ID')
    telegram_username = models.CharField('Username', max_length=100, blank=True, default='')
    telegram_first_name = models.CharField('Ism', max_length=100, blank=True, default='')
    code = models.CharField('Kod', max_length=6)
    is_used = models.BooleanField('Ishlatilgan', default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField('Amal qilish muddati')

    class Meta:
        verbose_name = 'Telegram auth kod'
        verbose_name_plural = 'Telegram auth kodlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"@{self.telegram_username or self.telegram_id} - {self.code}"

    @property
    def is_expired(self):
        return timezone.now() > self.expires_at

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired