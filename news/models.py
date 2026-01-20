"""
TestMakon.uz - News Models
News, announcements, tips and articles
"""

from django.db import models
from django.conf import settings
import uuid


class Category(models.Model):
    """Yangilik kategoriyasi"""

    name = models.CharField('Nomi', max_length=100)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Tavsif', blank=True)
    icon = models.CharField('Ikonka', max_length=50, default='📰')
    color = models.CharField('Rang', max_length=7, default='#3498db')

    order = models.PositiveIntegerField('Tartib', default=0)
    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Kategoriya'
        verbose_name_plural = 'Kategoriyalar'
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Article(models.Model):
    """Yangilik/Maqola"""

    ARTICLE_TYPES = [
        ('news', 'Yangilik'),
        ('announcement', 'E\'lon'),
        ('tip', 'Maslahat'),
        ('guide', 'Qo\'llanma'),
        ('update', 'Yangilanish'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic info
    title = models.CharField('Sarlavha', max_length=300)
    slug = models.SlugField('Slug', unique=True)
    excerpt = models.TextField('Qisqa tavsif', max_length=500)
    content = models.TextField('Mazmun')

    # Type and category
    article_type = models.CharField(
        'Turi',
        max_length=20,
        choices=ARTICLE_TYPES,
        default='news'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles',
        verbose_name='Kategoriya'
    )

    # Media
    featured_image = models.ImageField(
        'Asosiy rasm',
        upload_to='news/images/',
        blank=True,
        null=True
    )

    # Related subject (for tips)
    subject = models.ForeignKey(
        'tests_app.Subject',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )

    # Author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='articles'
    )

    # SEO
    meta_title = models.CharField('Meta sarlavha', max_length=70, blank=True)
    meta_description = models.CharField('Meta tavsif', max_length=160, blank=True)

    # Stats
    views_count = models.PositiveIntegerField('Ko\'rishlar', default=0)
    likes_count = models.PositiveIntegerField('Yoqtirishlar', default=0)

    # Status
    is_featured = models.BooleanField('Tavsiya etilgan', default=False)
    is_pinned = models.BooleanField('Qadoqlangan', default=False)
    is_published = models.BooleanField('Nashr etilgan', default=False)

    published_at = models.DateTimeField('Nashr vaqti', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Maqola'
        verbose_name_plural = 'Maqolalar'
        ordering = ['-is_pinned', '-published_at']

    def __str__(self):
        return self.title

    def increment_views(self):
        self.views_count += 1
        self.save(update_fields=['views_count'])


class ArticleLike(models.Model):
    """Maqola yoqtirish"""

    article = models.ForeignKey(
        Article,
        on_delete=models.CASCADE,
        related_name='likes'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='article_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Yoqtirish'
        verbose_name_plural = 'Yoqtirishlar'
        unique_together = ['article', 'user']


class Notification(models.Model):
    """Bildirishnomalar"""

    NOTIFICATION_TYPES = [
        ('system', 'Tizim'),
        ('news', 'Yangilik'),
        ('competition', 'Musobaqa'),
        ('battle', 'Jang'),
        ('achievement', 'Yutuq'),
        ('friend', 'Do\'st'),
        ('reminder', 'Eslatma'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    notification_type = models.CharField(
        'Turi',
        max_length=20,
        choices=NOTIFICATION_TYPES
    )

    title = models.CharField('Sarlavha', max_length=200)
    message = models.TextField('Xabar')

    # Link
    link = models.CharField('Havola', max_length=500, blank=True)

    # Related objects (optional)
    related_id = models.PositiveIntegerField('Bog\'liq ID', null=True, blank=True)

    # Status
    is_read = models.BooleanField('O\'qilgan', default=False)
    read_at = models.DateTimeField('O\'qilgan vaqt', null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Bildirishnoma'
        verbose_name_plural = 'Bildirishnomalar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.title}"