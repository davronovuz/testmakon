"""
TestMakon.uz - AI Powered Ta'lim Platformasi
Django Settings
"""

from pathlib import Path
import os
import sentry_sdk

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-)a=p2h3jl%!hb+6@@^e@xih796ilgkx$6s_6xpkk-*2^6*)0l3'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

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
    'subscriptions.apps.SubscriptionsConfig',  # <-- shu qatorni qo'shing

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
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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

# AI Settings (Anthropic Claude API)
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
    "site_title": "Admin",
    "site_header": "Admin",
    "site_brand": "Admin",
    "welcome_sign": "TestMakon  adminlar uchun",
    "copyright": "TestMakon",
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,
}