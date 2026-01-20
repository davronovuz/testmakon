"""
TestMakon.uz - Subscriptions Models
Premium subscription and payment system
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
import uuid


class SubscriptionPlan(models.Model):
    """Obuna paketlari"""

    PLAN_TYPES = [
        ('free', 'Bepul'),
        ('basic', 'Basic'),
        ('premium', 'Premium'),
        ('pro', 'Pro'),
    ]

    DURATION_CHOICES = [
        (7, '1 hafta'),
        (30, '1 oy'),
        (90, '3 oy'),
        (180, '6 oy'),
        (365, '1 yil'),
    ]

    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    plan_type = models.CharField('Paket turi', max_length=20, choices=PLAN_TYPES, default='premium')

    # Narx
    price = models.PositiveIntegerField('Narxi (so\'m)', default=0)
    original_price = models.PositiveIntegerField('Asl narxi (chegirma uchun)', null=True, blank=True)
    duration_days = models.PositiveIntegerField('Muddat (kun)', choices=DURATION_CHOICES, default=30)

    # Imkoniyatlar
    features = models.JSONField('Imkoniyatlar', default=list)

    # Cheklovlar
    daily_test_limit = models.PositiveIntegerField('Kunlik test limiti', null=True, blank=True,
                                                   help_text='NULL = cheksiz')
    daily_ai_chat_limit = models.PositiveIntegerField('Kunlik AI chat limiti', null=True, blank=True)
    can_access_analytics = models.BooleanField('Tahlil sahifasi', default=False)
    can_access_ai_mentor = models.BooleanField('AI Mentor', default=False)
    can_download_pdf = models.BooleanField('PDF yuklab olish', default=False)
    can_access_competitions = models.BooleanField('Musobaqalar', default=True)
    ad_free = models.BooleanField('Reklama yo\'q', default=False)

    # Status
    is_active = models.BooleanField('Faol', default=True)
    is_featured = models.BooleanField('Tavsiya etilgan', default=False)
    order = models.PositiveIntegerField('Tartib', default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Obuna paketi'
        verbose_name_plural = 'Obuna paketlari'
        ordering = ['order', 'price']

    def __str__(self):
        return f"{self.name} - {self.price:,} so'm/{self.duration_days} kun"

    @property
    def monthly_price(self):
        """Oylik narx (taqqoslash uchun)"""
        if self.duration_days == 0:
            return 0
        return round(self.price / self.duration_days * 30)

    @property
    def discount_percent(self):
        """Chegirma foizi"""
        if self.original_price and self.original_price > self.price:
            return round((1 - self.price / self.original_price) * 100)
        return 0


class Subscription(models.Model):
    """Foydalanuvchi obunasi"""

    STATUS_CHOICES = [
        ('active', 'Faol'),
        ('expired', 'Muddati tugagan'),
        ('cancelled', 'Bekor qilingan'),
        ('pending', 'Kutilmoqda'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='subscriptions'
    )

    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')

    # Vaqtlar
    started_at = models.DateTimeField('Boshlangan', null=True, blank=True)
    expires_at = models.DateTimeField('Tugash vaqti', null=True, blank=True)
    cancelled_at = models.DateTimeField('Bekor qilingan', null=True, blank=True)

    # Auto-renewal
    auto_renew = models.BooleanField('Avtomatik uzaytirish', default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Obuna'
        verbose_name_plural = 'Obunalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.plan.name} ({self.status})"

    @property
    def is_active(self):
        """Obuna faolmi"""
        if self.status != 'active':
            return False
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    @property
    def days_remaining(self):
        """Qolgan kunlar"""
        if not self.expires_at:
            return 0
        delta = self.expires_at - timezone.now()
        return max(0, delta.days)

    def activate(self):
        """Obunani faollashtirish"""
        self.status = 'active'
        self.started_at = timezone.now()
        self.expires_at = timezone.now() + timezone.timedelta(days=self.plan.duration_days)
        self.save()

        # User ni premium qilish
        self.user.is_premium = True
        self.user.premium_until = self.expires_at
        self.user.save()

    def cancel(self):
        """Obunani bekor qilish"""
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renew = False
        self.save()

    def check_and_expire(self):
        """Muddati o'tganini tekshirish"""
        if self.status == 'active' and self.expires_at and self.expires_at < timezone.now():
            self.status = 'expired'
            self.save()

            # User premium ni o'chirish
            self.user.is_premium = False
            self.user.premium_until = None
            self.user.save()
            return True
        return False


class Payment(models.Model):
    """To'lovlar"""

    STATUS_CHOICES = [
        ('pending', 'Kutilmoqda'),
        ('processing', 'Jarayonda'),
        ('completed', 'Muvaffaqiyatli'),
        ('failed', 'Muvaffaqiyatsiz'),
        ('cancelled', 'Bekor qilingan'),
        ('refunded', 'Qaytarilgan'),
    ]

    PROVIDER_CHOICES = [
        ('click', 'Click'),
        ('payme', 'Payme'),
        ('uzum', 'Uzum Bank'),
        ('manual', 'Qo\'lda'),
        ('promo', 'Promo kod'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order_id = models.CharField('Buyurtma ID', max_length=50, unique=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='payments'
    )

    # To'lov ma'lumotlari
    amount = models.PositiveIntegerField('Summa (so\'m)')
    provider = models.CharField('To\'lov tizimi', max_length=20, choices=PROVIDER_CHOICES)
    status = models.CharField('Holat', max_length=20, choices=STATUS_CHOICES, default='pending')

    # Provider ma'lumotlari
    provider_transaction_id = models.CharField('Provider transaction ID', max_length=100, blank=True)
    provider_response = models.JSONField('Provider javobi', default=dict, blank=True)

    # Qo'shimcha
    description = models.TextField('Tavsif', blank=True)
    ip_address = models.GenericIPAddressField('IP manzil', null=True, blank=True)
    user_agent = models.TextField('User Agent', blank=True)

    # Vaqtlar
    paid_at = models.DateTimeField('To\'langan vaqt', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'To\'lov'
        verbose_name_plural = 'To\'lovlar'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['order_id']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['provider', 'status']),
        ]

    def __str__(self):
        return f"{self.order_id} - {self.user} - {self.amount:,} so'm ({self.status})"

    def save(self, *args, **kwargs):
        if not self.order_id:
            self.order_id = f"TM-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def mark_as_paid(self):
        """To'lov muvaffaqiyatli"""
        self.status = 'completed'
        self.paid_at = timezone.now()
        self.save()

        # Subscription yaratish yoki faollashtirish
        if not self.subscription:
            self.subscription = Subscription.objects.create(
                user=self.user,
                plan=self.plan,
                status='pending'
            )
            self.save()

        self.subscription.activate()

    def mark_as_failed(self, reason=''):
        """To'lov muvaffaqiyatsiz"""
        self.status = 'failed'
        self.description = reason
        self.save()


class PromoCode(models.Model):
    """Promo kodlar"""

    DISCOUNT_TYPES = [
        ('percent', 'Foiz'),
        ('fixed', 'Qat\'iy summa'),
        ('free_days', 'Bepul kunlar'),
    ]

    code = models.CharField('Kod', max_length=50, unique=True, db_index=True)
    description = models.TextField('Tavsif', blank=True)

    discount_type = models.CharField('Chegirma turi', max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.PositiveIntegerField('Chegirma qiymati')

    # Cheklovlar
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text='Faqat shu paket uchun'
    )
    max_uses = models.PositiveIntegerField('Maksimum ishlatish', null=True, blank=True)
    max_uses_per_user = models.PositiveIntegerField('Har bir user uchun max', default=1)
    current_uses = models.PositiveIntegerField('Hozirgi ishlatishlar', default=0)

    # Vaqt
    valid_from = models.DateTimeField('Boshlanish vaqti')
    valid_until = models.DateTimeField('Tugash vaqti')

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Promo kod'
        verbose_name_plural = 'Promo kodlar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.code} - {self.discount_value}{'%' if self.discount_type == 'percent' else ' som'}"

    @property
    def is_valid(self):
        """Kod hali amalda mi"""
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_until:
            return False
        if self.max_uses and self.current_uses >= self.max_uses:
            return False
        return True

    def apply_discount(self, original_price):
        """Chegirmani qo'llash"""
        if self.discount_type == 'percent':
            return original_price * (100 - self.discount_value) // 100
        elif self.discount_type == 'fixed':
            return max(0, original_price - self.discount_value)
        return original_price

    def use(self):
        """Kodni ishlatish"""
        self.current_uses += 1
        self.save()


class PromoCodeUsage(models.Model):
    """Promo kod ishlatish tarixi"""

    promo_code = models.ForeignKey(PromoCode, on_delete=models.CASCADE, related_name='usages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    discount_amount = models.PositiveIntegerField('Chegirma summasi')
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Promo kod ishlatish'
        verbose_name_plural = 'Promo kod ishlatishlar'
        unique_together = ['promo_code', 'user', 'payment']


class UserDailyLimit(models.Model):
    """Kunlik limitlarni kuzatish"""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    date = models.DateField('Sana')

    tests_taken = models.PositiveIntegerField('Yechilgan testlar', default=0)
    ai_chats_used = models.PositiveIntegerField('AI chat ishlatilgan', default=0)

    class Meta:
        verbose_name = 'Kunlik limit'
        verbose_name_plural = 'Kunlik limitlar'
        unique_together = ['user', 'date']

    def __str__(self):
        return f"{self.user} - {self.date}"

    @classmethod
    def get_or_create_today(cls, user):
        """Bugungi limitni olish yoki yaratish"""
        today = timezone.now().date()
        obj, created = cls.objects.get_or_create(user=user, date=today)
        return obj

    def can_take_test(self, plan):
        """Test yechish mumkinmi"""
        if plan.daily_test_limit is None:
            return True
        return self.tests_taken < plan.daily_test_limit

    def can_use_ai_chat(self, plan):
        """AI chat ishlatish mumkinmi"""
        if plan.daily_ai_chat_limit is None:
            return True
        return self.ai_chats_used < plan.daily_ai_chat_limit