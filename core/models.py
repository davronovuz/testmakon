"""
TestMakon.uz - Core Models
Site settings, contact, feedback, and general models
"""

from django.db import models
from django.conf import settings


class SiteSettings(models.Model):
    """Sayt sozlamalari (Singleton)"""

    site_name = models.CharField('Sayt nomi', max_length=100, default='TestMakon.uz')
    site_tagline = models.CharField('Slogan', max_length=200, default='AI Powered Ta\'lim Platformasi')
    site_description = models.TextField('Tavsif', blank=True)

    # Contact
    contact_email = models.EmailField('Email', blank=True)
    contact_phone = models.CharField('Telefon', max_length=20, blank=True)
    contact_address = models.TextField('Manzil', blank=True)

    # Social
    telegram_url = models.URLField('Telegram', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    youtube_url = models.URLField('YouTube', blank=True)
    facebook_url = models.URLField('Facebook', blank=True)

    # SEO
    meta_title = models.CharField('Meta sarlavha', max_length=70, blank=True)
    meta_description = models.CharField('Meta tavsif', max_length=160, blank=True)
    meta_keywords = models.CharField('Meta kalit so\'zlar', max_length=255, blank=True)

    # Analytics
    google_analytics_id = models.CharField('Google Analytics ID', max_length=50, blank=True)
    yandex_metrika_id = models.CharField('Yandex Metrika ID', max_length=50, blank=True)

    # Features
    is_registration_open = models.BooleanField('Ro\'yxatdan o\'tish ochiq', default=True)
    is_maintenance_mode = models.BooleanField('Texnik ishlar rejimi', default=False)
    maintenance_message = models.TextField('Texnik ishlar xabari', blank=True)

    # Stats (cached)
    total_users = models.PositiveIntegerField('Jami foydalanuvchilar', default=0)
    total_tests = models.PositiveIntegerField('Jami testlar', default=0)
    total_questions = models.PositiveIntegerField('Jami savollar', default=0)
    total_attempts = models.PositiveIntegerField('Jami urinishlar', default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Sayt sozlamalari'
        verbose_name_plural = 'Sayt sozlamalari'

    def __str__(self):
        return self.site_name

    def save(self, *args, **kwargs):
        # Singleton pattern - faqat bitta yozuv bo'lishi kerak
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        """Sozlamalarni olish"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj


class ContactMessage(models.Model):
    """Aloqa xabarlari"""

    STATUS_CHOICES = [
        ('new', 'Yangi'),
        ('read', 'O\'qilgan'),
        ('replied', 'Javob berilgan'),
        ('closed', 'Yopilgan'),
    ]

    name = models.CharField('Ism', max_length=100)
    email = models.EmailField('Email')
    phone = models.CharField('Telefon', max_length=20, blank=True)
    subject = models.CharField('Mavzu', max_length=200)
    message = models.TextField('Xabar')

    # Optional user link
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages'
    )

    status = models.CharField(
        'Holat',
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    admin_notes = models.TextField('Admin eslatmalari', blank=True)
    replied_at = models.DateTimeField('Javob vaqti', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Aloqa xabari'
        verbose_name_plural = 'Aloqa xabarlari'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


class Feedback(models.Model):
    """Fikr-mulohaza"""

    FEEDBACK_TYPES = [
        ('bug', 'Xatolik'),
        ('feature', 'Yangi imkoniyat'),
        ('improvement', 'Yaxshilash'),
        ('complaint', 'Shikoyat'),
        ('praise', 'Maqtov'),
        ('other', 'Boshqa'),
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
        related_name='feedbacks'
    )

    feedback_type = models.CharField(
        'Turi',
        max_length=20,
        choices=FEEDBACK_TYPES
    )
    priority = models.CharField(
        'Muhimlik',
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    subject = models.CharField('Mavzu', max_length=200)
    message = models.TextField('Xabar')

    # Screenshot or attachment
    attachment = models.FileField(
        'Fayl',
        upload_to='feedbacks/',
        blank=True,
        null=True
    )

    # Page where feedback was submitted
    page_url = models.URLField('Sahifa URL', blank=True)

    # Status
    is_resolved = models.BooleanField('Hal qilingan', default=False)
    admin_response = models.TextField('Admin javobi', blank=True)
    resolved_at = models.DateTimeField('Hal qilingan vaqt', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Fikr-mulohaza'
        verbose_name_plural = 'Fikr-mulohazalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.subject}"


class FAQ(models.Model):
    """Ko'p beriladigan savollar"""

    CATEGORY_CHOICES = [
        ('general', 'Umumiy'),
        ('account', 'Hisob'),
        ('test', 'Testlar'),
        ('competition', 'Musobaqalar'),
        ('payment', 'To\'lov'),
        ('technical', 'Texnik'),
    ]

    question = models.TextField('Savol')
    answer = models.TextField('Javob')

    category = models.CharField(
        'Kategoriya',
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general'
    )

    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    views_count = models.PositiveIntegerField('Ko\'rishlar', default=0)
    helpful_count = models.PositiveIntegerField('Foydali', default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQlar'
        ordering = ['category', 'order']

    def __str__(self):
        return self.question[:50]


class Banner(models.Model):
    """Bannerlar (reklama, e'lonlar)"""

    POSITION_CHOICES = [
        ('home_hero', 'Bosh sahifa Hero'),
        ('home_middle', 'Bosh sahifa O\'rta'),
        ('sidebar', 'Yon panel'),
        ('test_page', 'Test sahifasi'),
        ('result_page', 'Natija sahifasi'),
    ]

    title = models.CharField('Sarlavha', max_length=200)
    subtitle = models.CharField('Qo\'shimcha matn', max_length=300, blank=True)

    image = models.ImageField('Rasm', upload_to='banners/')
    mobile_image = models.ImageField(
        'Mobil rasm',
        upload_to='banners/mobile/',
        blank=True,
        null=True
    )

    link = models.URLField('Havola', blank=True)
    button_text = models.CharField('Tugma matni', max_length=50, blank=True)

    position = models.CharField(
        'Joylashuv',
        max_length=20,
        choices=POSITION_CHOICES
    )

    # Scheduling
    start_date = models.DateTimeField('Boshlanish', null=True, blank=True)
    end_date = models.DateTimeField('Tugash', null=True, blank=True)

    # Stats
    views_count = models.PositiveIntegerField('Ko\'rishlar', default=0)
    clicks_count = models.PositiveIntegerField('Bosishlar', default=0)

    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Banner'
        verbose_name_plural = 'Bannerlar'
        ordering = ['position', 'order']

    def __str__(self):
        return self.title

    @property
    def ctr(self):
        """Click-through rate"""
        if self.views_count == 0:
            return 0
        return round((self.clicks_count / self.views_count) * 100, 2)


class Partner(models.Model):
    """Hamkorlar"""

    name = models.CharField('Nomi', max_length=200)
    logo = models.ImageField('Logo', upload_to='partners/')
    website = models.URLField('Veb sayt', blank=True)
    description = models.TextField('Tavsif', blank=True)

    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Hamkor'
        verbose_name_plural = 'Hamkorlar'
        ordering = ['order']

    def __str__(self):
        return self.name