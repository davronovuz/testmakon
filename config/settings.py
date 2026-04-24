"""
TestMakon.uz - AI Powered Ta'lim Platformasi
Django Settings
"""


from pathlib import Path
import os
import sentry_sdk
from decouple import config
from dj_database_url import parse as db_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-)a=p2h3jl%!hb+6@@^e@xih796ilgkx$6s_6xpkk-*2^6*)0l3')

# DEBUG = config('DEBUG', default=False, cast=bool)
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testmakon.uz', 'www.testmakon.uz']

# Development uchun — DEBUG=True bo'lganda barcha hostlar ruxsat
if DEBUG:
    ALLOWED_HOSTS = ['*']

# ─── Production xavfsizlik sozlamalari ───────────────────────────────────────
if not DEBUG:
    # nginx SSL ni boshqaradi — redirect loop oldini olish uchun False
    SECURE_SSL_REDIRECT = False
    # nginx HTTPS ni Django ga xabar beradi
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Cookie lar faqat HTTPS orqali
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # HSTS — brauzer 1 yil davomida faqat HTTPS ishlatadi
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    # CSRF faqat HTTPS (HTTP variantlari yo'q — production da HTTP bo'lmasin)
    CSRF_TRUSTED_ORIGINS = ['https://testmakon.uz', 'https://www.testmakon.uz']
else:
    CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Application definition
INSTALLED_APPS = [
    'daphne',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'django.contrib.sitemaps',
    'import_export',
    'channels',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',

    # Local apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'tests_app.apps.TestsAppConfig',
    'ai_core.apps.AiCoreConfig',
    'competitions.apps.CompetitionsConfig',
    'universities.apps.UniversitiesConfig',
    'news.apps.NewsConfig',
    'leaderboard.apps.LeaderboardConfig',
    'subscriptions.apps.SubscriptionsConfig',
    'tgbot.apps.TgbotConfig',
    'coding.apps.CodingConfig',
    'django_celery_beat',
    'api.apps.ApiConfig',
    'certificate.apps.CertificateConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.middleware.OnlinePresenceMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.system_banners',
                'core.context_processors.notifications_count',
                'core.context_processors.analytics_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# Redis bazaviy URL (DB raqamisiz) — har bir xizmat o'z DB'sini ishlatadi
# DB 1 = Cache, DB 2 = Channels, DB 3 = Celery
_redis_base = config('REDIS_URL', default='redis://localhost:6379/0').rsplit('/', 1)[0]
_channel_redis_url = _redis_base + '/2'
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [_channel_redis_url],
            'capacity': 1500,
            'expiry': 10,
        },
    },
}


# Database
DATABASES = {
    'default': config(
        'DATABASE_URL',
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        cast=db_url
    )
}

# Redis Cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': _redis_base + '/1',
        'TIMEOUT': 300,  # 5 daqiqa default
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'testmakon',
    }
}

# Session ham Redis da saqlash (ko'p user uchun tezroq)
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_CACHE_ALIAS = 'default'

# Celery + Redis
CELERY_BROKER_URL        = _redis_base + '/3'
CELERY_RESULT_BACKEND    = _redis_base + '/3'
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Asia/Tashkent'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT    = 60 * 60  # 1 soat max (broadcast uchun)

# Telegram Bot
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN', default='')
SITE_DOMAIN        = config('SITE_DOMAIN', default='https://testmakon.uz')

# Telegram adminlar — bot ichida /broadcast, /stats kabi buyruqlarni
# faqat shu ro'yxatdagi ID lar ishlata oladi. Vergul bilan ajratiladi.
TELEGRAM_ADMIN_IDS = [
    int(x.strip())
    for x in config('TELEGRAM_ADMIN_IDS', default='1879114908').split(',')
    if x.strip().isdigit()
]

# ─── Google OAuth 2.0 ────────────────────────────────────────────────────────
# Production: credentials .env fayldan olinadi. Agar bo'sh bo'lsa, Google
# tugmasi login/register sahifalarida ko'rsatilmaydi (sinmaydi).
GOOGLE_CLIENT_ID = config('GOOGLE_CLIENT_ID', default='')
GOOGLE_CLIENT_SECRET = config('GOOGLE_CLIENT_SECRET', default='')
# Redirect URI: Google Console'da ro'yxatdan o'tkazilgan bilan bir xil bo'lishi shart.
# Agar bo'sh bo'lsa, SITE_DOMAIN + /accounts/google/callback/ ishlatiladi.
GOOGLE_REDIRECT_URI = config(
    'GOOGLE_REDIRECT_URI',
    default=f"{SITE_DOMAIN.rstrip('/')}/accounts/google/callback/"
)
TELEGRAM_WELCOME_MESSAGE = (
    '👋 Salom! <b>TestMakon.uz</b> botiga xush kelibsiz!\n\n'
    '📚 O\'zingizni DTMga tayyorlang, testlar ishlang va '
    'natijalaringizni kuzating.\n\n'
    '🌐 Saytga o\'ting: <a href="https://testmakon.uz">testmakon.uz</a>'
)

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'cache-university-stats': {
        'task': 'universities.cache_university_stats',
        'schedule': 3600.0,  # har soatda
    },
    'daily-study-reminders': {
        'task': 'ai_core.tasks.send_daily_study_reminders',
        'schedule': crontab(hour=8, minute=0),  # 08:00 Toshkent
    },
    'weekly-ai-report': {
        'task': 'ai_core.tasks.generate_weekly_ai_report',
        'schedule': crontab(hour=9, minute=0, day_of_week=1),  # Dushanba 09:00
    },
    'smart-behavioral-notifications': {
        'task': 'ai_core.tasks.send_smart_behavioral_notifications',
        'schedule': crontab(hour=18, minute=0),  # 18:00 har kuni
    },
    'inactivity-check': {
        'task': 'ai_core.tasks.send_inactivity_reminders',
        'schedule': crontab(hour=10, minute=0),  # 10:00 har kuni
    },
    'check-subscriptions-expiry': {
        'task': 'subscriptions.tasks.check_all_subscriptions_expiry',
        'schedule': 3600.0,  # har soatda — muddati o'tgan obunalarni expired qiladi
    },
    'expiring-soon-notifications': {
        'task': 'subscriptions.tasks.send_expiring_soon_notifications',
        'schedule': crontab(hour=10, minute=30),  # har kuni 10:30 — 3 kun qolganida ogohlantirish
    },
    'cleanup-coding-containers': {
        'task': 'coding.tasks.cleanup_old_containers',
        'schedule': 1800.0,  # har 30 daqiqada
    },
}

# ─── Coding Sandbox (Docker) sozlamalari ─────────────────────────────────────
SANDBOX_TIME_LIMIT = 5       # sekundda (max)
SANDBOX_MEMORY_LIMIT = '256m'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization - O'zbek tili
LANGUAGE_CODE = 'uz'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files (Uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# Login/Logout URLs
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'tests_app:tests_list'
LOGOUT_REDIRECT_URL = 'core:home'

# AI Settings (Gemini API)
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# Telegram Bot (token faqat server .env dan — hardcoded bo'lmasin)
TELEGRAM_BOT_USERNAME = os.environ.get('TELEGRAM_BOT_USERNAME', 'testmakonaibot')

# Session settings
SESSION_COOKIE_AGE = 86400 * 30  # 30 days
SESSION_SAVE_EVERY_REQUEST = True

# Messages
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'secondary',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'danger',
}


# ============================================================
# SENTRY — xatolarni real vaqtda kuzatish
# DSN ni sentry.io dan oling
# ============================================================
SENTRY_DSN = os.environ.get('SENTRY_DSN', '')

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        send_default_pii=True,         # foydalanuvchi ma'lumotlari
        traces_sample_rate=0.2,        # 20% so'rovlarni kuzat (performance)
        environment='production' if not DEBUG else 'development',
    )

# ============================================================
# GOOGLE ANALYTICS 4
# Measurement ID ni analytics.google.com dan oling (G-XXXXXXXXXX)
# ============================================================
GOOGLE_ANALYTICS_ID = os.environ.get('GOOGLE_ANALYTICS_ID', 'G-B6NRGX93LD')

# ============================================================
# SEARCH ENGINE VERIFICATION
# Google Search Console: https://search.google.com/search-console
# Yandex Webmaster: https://webmaster.yandex.com
# Bing Webmaster: https://www.bing.com/webmasters
# ============================================================
GOOGLE_SITE_VERIFICATION = os.environ.get('GOOGLE_SITE_VERIFICATION', '')
YANDEX_VERIFICATION = os.environ.get('YANDEX_VERIFICATION', '')
BING_VERIFICATION = os.environ.get('BING_VERIFICATION', '')

JAZZMIN_SETTINGS = {
    # Oyna sarlavhasi
    "site_title": "TestMakon Admin",
    "site_header": "TestMakon",
    "site_brand": "TestMakon.uz",

    # Login sahifasi
    "welcome_sign": "Boshqaruv paneliga xush kelibsiz",
    "copyright": "TestMakon.uz © 2025",

    # Yuqori menyu
    "topmenu_links": [
        {"name": "Bosh sahifa", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Saytga o'tish", "url": "/", "new_window": True},
        {"model": "accounts.User"},
    ],

    # Foydalanuvchi menyusi (o'ng yuqori)
    "usermenu_links": [
        {"name": "Saytga o'tish", "url": "/", "new_window": True, "icon": "fas fa-external-link-alt"},
    ],

    # Sidebar
    "show_sidebar": True,
    "navigation_expanded": True,

    # Keraksiz modellarni yashirish
    "hide_apps": [],
    "hide_models": [
        "tests_app.DailyUserStats",
        "tests_app.UserActivityLog",
        "tests_app.UserTopicPerformance",
        "tests_app.UserSubjectPerformance",
        "tests_app.UserStudySession",
        "tests_app.UserAnalyticsSummary",
        "accounts.PhoneVerification",
        "accounts.UserActivity",
        "news.ArticleLike",
        "competitions.BattleInvitation",
        "competitions.MatchmakingQueue",
        "competitions.CompetitionQuestion",
        "competitions.DailyChallengeParticipant",
        "competitions.WeeklyLeagueParticipant",
        "leaderboard.SeasonalParticipant",
        "leaderboard.SubjectLeaderboard",
        "leaderboard.UserAchievement",
        "subscriptions.PromoCodeUsage",
        "subscriptions.UserDailyLimit",
        "ai_core.AIMessage",
        "ai_core.StudyPlanTask",
        "ai_core.WeakTopicAnalysis",
        "universities.AdmissionCalculation",
    ],

    # App va model ikonkalari (Font Awesome 5)
    "icons": {
        # Django auth
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",

        # Foydalanuvchilar
        "accounts": "fas fa-users",
        "accounts.User": "fas fa-user-circle",
        "accounts.Badge": "fas fa-medal",
        "accounts.UserBadge": "fas fa-award",
        "accounts.Friendship": "fas fa-user-friends",

        # Testlar
        "tests_app": "fas fa-clipboard-list",
        "tests_app.Subject": "fas fa-book",
        "tests_app.Topic": "fas fa-bookmark",
        "tests_app.Question": "fas fa-question-circle",
        "tests_app.Test": "fas fa-file-alt",
        "tests_app.TestAttempt": "fas fa-chart-bar",
        "tests_app.SavedQuestion": "fas fa-heart",

        # Yangiliklar
        "news": "fas fa-newspaper",
        "news.Article": "fas fa-newspaper",
        "news.Category": "fas fa-tags",
        "news.Notification": "fas fa-bell",
        "news.SystemBanner": "fas fa-bullhorn",

        # Musobaqalar
        "competitions": "fas fa-trophy",
        "competitions.Competition": "fas fa-trophy",
        "competitions.CompetitionParticipant": "fas fa-users",
        "competitions.CompetitionPayment": "fas fa-credit-card",
        "competitions.Certificate": "fas fa-certificate",
        "competitions.Battle": "fas fa-bolt",
        "competitions.DailyChallenge": "fas fa-calendar-day",
        "competitions.WeeklyLeague": "fas fa-calendar-week",

        # Obunalar
        "subscriptions": "fas fa-star",
        "subscriptions.SubscriptionPlan": "fas fa-layer-group",
        "subscriptions.Subscription": "fas fa-user-check",
        "subscriptions.Payment": "fas fa-money-bill-wave",
        "subscriptions.PromoCode": "fas fa-ticket-alt",

        # Universitetlar
        "universities": "fas fa-university",
        "universities.University": "fas fa-university",
        "universities.Faculty": "fas fa-building",
        "universities.Direction": "fas fa-graduation-cap",
        "universities.PassingScore": "fas fa-chart-line",
        "universities.UniversityReview": "fas fa-star-half-alt",

        # Reyting
        "leaderboard": "fas fa-list-ol",
        "leaderboard.GlobalLeaderboard": "fas fa-globe",
        "leaderboard.Achievement": "fas fa-medal",
        "leaderboard.UserStats": "fas fa-chart-pie",
        "leaderboard.SeasonalLeaderboard": "fas fa-calendar-alt",

        # AI
        "ai_core": "fas fa-robot",
        "ai_core.AIConversation": "fas fa-comments",
        "ai_core.AIRecommendation": "fas fa-lightbulb",
        "ai_core.StudyPlan": "fas fa-tasks",

        # Sozlamalar
        "core": "fas fa-cog",
        "core.SiteSettings": "fas fa-sliders-h",
        "core.ContactMessage": "fas fa-envelope",
        "core.Feedback": "fas fa-comment-alt",
        "core.FAQ": "fas fa-question",
        "core.Banner": "fas fa-image",
        "core.Partner": "fas fa-handshake",
    },

    # Default ikonkalar
    "default_icon_parents": "fas fa-folder",
    "default_icon_children": "fas fa-circle",

    # Related modal (tez qo'shish)
    "related_modal_active": True,

    # Qo'shimcha
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,

    # Sidebar tartib
    "order_with_respect_to": [
        "accounts",
        "tests_app",
        "news",
        "competitions",
        "subscriptions",
        "universities",
        "leaderboard",
        "ai_core",
        "core",
        "auth",
    ],

    # Form ko'rinishi
    "changeform_format": "horizontal_tabs",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": "navbar-success",
    "accent": "accent-success",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": True,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-success",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

# ============================================================
# REST FRAMEWORK — Mobile API uchun
# ============================================================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS — Mobile app uchun
CORS_ALLOW_ALL_ORIGINS = True  # Development uchun; production da specific origins qo'shiladi