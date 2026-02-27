"""
TestMakon.uz - Universities Models
University database with AI admission calculator support
"""
from django.core.validators import MinValueValidator,MaxValueValidator
from django.db import models
from django.conf import settings
import uuid


class University(models.Model):
    """Universitet"""

    UNIVERSITY_TYPES = [
        ('state', 'Davlat'),
        ('private', 'Xususiy'),
        ('foreign', 'Xorijiy filial'),
        ('joint', 'Qo\'shma'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    # Basic info
    name = models.CharField('Nomi', max_length=300)
    short_name = models.CharField('Qisqa nomi', max_length=200, blank=True)
    slug = models.SlugField('Slug', unique=True, max_length=200)

    university_type = models.CharField(
        'Turi',
        max_length=20,
        choices=UNIVERSITY_TYPES,
        default='state'
    )

    # Description
    description = models.TextField('Tavsif', blank=True)
    history = models.TextField('Tarix', blank=True)

    # Media
    logo = models.ImageField('Logo', upload_to='universities/logos/', blank=True, null=True)
    cover_image = models.ImageField('Muqova rasm', upload_to='universities/covers/', blank=True, null=True)

    # Contact
    website = models.URLField('Veb sayt', blank=True)
    email = models.EmailField('Email', blank=True)
    phone = models.CharField('Telefon', max_length=20, blank=True)

    # Address
    region = models.CharField('Viloyat', max_length=100)
    city = models.CharField('Shahar', max_length=100)
    address = models.TextField('Manzil', blank=True)

    # Stats
    established_year = models.PositiveIntegerField('Tashkil etilgan yil', null=True, blank=True)
    student_count = models.PositiveIntegerField('Talabalar soni', null=True, blank=True)
    faculty_count = models.PositiveIntegerField('Fakultetlar soni', null=True, blank=True)

    # Rating
    rating = models.FloatField('Reyting', default=0.0)
    reviews_count = models.PositiveIntegerField('Sharhlar soni', default=0)

    # For advertising
    is_partner = models.BooleanField('Hamkor', default=False)
    is_featured = models.BooleanField('Tavsiya etilgan', default=False)

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Universitet'
        verbose_name_plural = 'Universitetlar'
        ordering = ['name']

    def __str__(self):
        return self.short_name or self.name

    def get_logo_url(self):
        if self.logo:
            return self.logo.url
        return '/static/images/default-university.png'


class Faculty(models.Model):
    """Fakultet"""

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='faculties',
        verbose_name='Universitet'
    )
    name = models.CharField('Nomi', max_length=200)
    slug = models.SlugField('Slug')
    description = models.TextField('Tavsif', blank=True)

    is_active = models.BooleanField('Faol', default=True)

    class Meta:
        verbose_name = 'Fakultet'
        verbose_name_plural = 'Fakultetlar'
        unique_together = ['university', 'slug']
        ordering = ['name']

    def __str__(self):
        return f"{self.university.short_name} - {self.name}"


class Direction(models.Model):
    """Yo'nalish (Mutaxassislik)"""

    EDUCATION_FORMS = [
        ('full_time', 'Kunduzgi'),
        ('evening', 'Kechki'),
        ('distance', 'Sirtqi'),
    ]

    EDUCATION_TYPES = [
        ('grant', 'Grant'),
        ('contract', 'Kontrakt'),
        ('both', 'Grant va Kontrakt'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='directions',
        verbose_name='Universitet'
    )
    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='directions',
        verbose_name='Fakultet'
    )

    # Basic info
    code = models.CharField('Kod', max_length=20)
    name = models.CharField('Nomi', max_length=300)
    slug = models.SlugField('Slug')
    description = models.TextField('Tavsif', blank=True)

    # Education details
    education_form = models.CharField(
        'Ta\'lim shakli',
        max_length=20,
        choices=EDUCATION_FORMS,
        default='full_time'
    )
    education_type = models.CharField(
        'Ta\'lim turi',
        max_length=20,
        choices=EDUCATION_TYPES,
        default='both'
    )
    duration_years = models.PositiveIntegerField('Davomiyligi (yil)', default=4)

    # Required subjects for admission
    required_subjects = models.ManyToManyField(
        'tests_app.Subject',
        related_name='required_for_directions',
        verbose_name='Majburiy fanlar'
    )

    # Quota
    grant_quota = models.PositiveIntegerField('Grant kvotasi', default=0)
    contract_quota = models.PositiveIntegerField('Kontrakt kvotasi', default=0)

    # Price
    contract_price = models.DecimalField(
        'Kontrakt narxi',
        max_digits=12,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField('Faol', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Yo\'nalish'
        verbose_name_plural = 'Yo\'nalishlar'
        unique_together = ['university', 'code']
        ordering = ['university', 'name']

    def __str__(self):
        return f"{self.university.short_name} - {self.name}"

    @property
    def total_quota(self):
        return self.grant_quota + self.contract_quota


class PassingScore(models.Model):
    """O'tish ballari (yillar bo'yicha)"""

    direction = models.ForeignKey(
        Direction,
        on_delete=models.CASCADE,
        related_name='passing_scores',
        verbose_name='Yo\'nalish'
    )
    year = models.PositiveIntegerField('Yil')

    # Scores
    grant_score = models.FloatField('Grant bali', null=True, blank=True)
    contract_score = models.FloatField('Kontrakt bali', null=True, blank=True)

    # Applications stats
    total_applications = models.PositiveIntegerField('Jami arizalar', null=True, blank=True)
    grant_accepted = models.PositiveIntegerField('Grant qabul', null=True, blank=True)
    contract_accepted = models.PositiveIntegerField('Kontrakt qabul', null=True, blank=True)

    # Competition ratio
    competition_ratio = models.FloatField('Tanlov nisbati', null=True, blank=True)

    class Meta:
        verbose_name = 'O\'tish bali'
        verbose_name_plural = 'O\'tish ballari'
        unique_together = ['direction', 'year']
        ordering = ['-year']

    def __str__(self):
        return f"{self.direction} - {self.year}"


class UniversityReview(models.Model):
    """Universitet sharhlari"""

    university = models.ForeignKey(
        University,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Universitet'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='university_reviews'
    )

    rating = models.PositiveIntegerField(
        'Baho',
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField('Sarlavha', max_length=200)
    content = models.TextField('Sharh')

    # Aspects
    education_rating = models.PositiveIntegerField('Ta\'lim sifati', default=3)
    facility_rating = models.PositiveIntegerField('Jihozlanganlik', default=3)
    staff_rating = models.PositiveIntegerField('O\'qituvchilar', default=3)

    is_approved = models.BooleanField('Tasdiqlangan', default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Sharh'
        verbose_name_plural = 'Sharhlar'
        unique_together = ['university', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.university} ({self.rating}★)"


class AdmissionCalculation(models.Model):
    """AI qabul kalkulyatori natijalari"""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='admission_calculations'
    )

    # Input scores
    total_score = models.FloatField('Umumiy ball')
    subject_scores = models.JSONField('Fan ballari', default=dict)

    # AI Results
    recommendations = models.JSONField('Tavsiyalar', default=list)
    analysis = models.TextField('AI tahlili', blank=True)

    # Top matches
    top_directions = models.ManyToManyField(
        Direction,
        related_name='calculations',
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Qabul kalkulyatsiyasi'
        verbose_name_plural = 'Qabul kalkulyatsiyalari'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user} - {self.total_score} ball"