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

DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['*', 'localhost', '127.0.0.1', 'testmakon.uz', 'www.testmakon.uz']

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'import_export',

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
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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


CSRF_TRUSTED_ORIGINS = [
    'https://testmakon.uz',
    'https://www.testmakon.uz',
    'http://testmakon.uz',
    'http://www.testmakon.uz',
]

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
        'LOCATION': config('REDIS_URL', default='redis://localhost:6379/1'),
        'TIMEOUT': 300,  # 5 daqiqa default
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'testmakon',
    }
}

# Session ham Redis da saqlash (ko'p user uchun tezroq)
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Celery + Redis
CELERY_BROKER_URL        = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND    = config('REDIS_URL', default='redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT    = ['json']
CELERY_TASK_SERIALIZER   = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE          = 'Asia/Tashkent'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT    = 30 * 60  # 30 daqiqa max

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

# Telegram Bot
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '8205738917:AAHIVL5FvDqOg-AM_6Qwe22_ey1JAcG_h78')
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
SENTRY_DSN = os.environ.get('SENTRY_DSN', 'https://3781979e4fc948a9411faa1a67ded53e@o4510917351440384.ingest.de.sentry.io/4510917390827600')

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