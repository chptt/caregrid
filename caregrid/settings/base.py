"""
Base Django settings for CareGrid.

Shared by all environments. Do not put secrets or environment-specific
values here — use production.py (or a local override) for those.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # repo root

load_dotenv(BASE_DIR / '.env')

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-change-me-in-production',
)

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
    if h.strip()
]

# ---------------------------------------------------------------------------
# Application definition
# ---------------------------------------------------------------------------

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'core',
    'users',
    'firewall',
    'backend.apps.ai',
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
    'core.middleware.SecurityMiddleware',
]

ROOT_URLCONF = 'caregrid.urls'

LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'caregrid.wsgi.application'
ASGI_APPLICATION = 'caregrid.asgi.application'

# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

AUTH_USER_MODEL = 'users.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ---------------------------------------------------------------------------
# Database — defaults to SQLite for local dev
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ---------------------------------------------------------------------------
# Static and media files
# ---------------------------------------------------------------------------

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STATICFILES_DIRS = [
    BASE_DIR / 'backend' / 'apps' / 'ai' / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ---------------------------------------------------------------------------
# Redis — base URL built once, reused by cache and session backends
# ---------------------------------------------------------------------------

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB   = int(os.environ.get('REDIS_DB', '0'))
REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')

# Full Redis URL — used by django-redis and raw redis.Redis() clients
_redis_auth = f':{REDIS_PASSWORD}@' if REDIS_PASSWORD else ''
REDIS_URL = os.environ.get(
    'REDIS_URL',
    f'redis://{_redis_auth}{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
)

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            # Surface Redis errors rather than silently falling back
            'IGNORE_EXCEPTIONS': False,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
        },
        'KEY_PREFIX': 'caregrid',
        'TIMEOUT': 300,
    }
}

# Store sessions in Redis so they survive Gunicorn worker restarts
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    if o.strip()
]

# Allow credentials (cookies) across origins — required for session auth
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-captcha-token',   # used by CareGrid security middleware
]

# ---------------------------------------------------------------------------
# Django REST Framework
# ---------------------------------------------------------------------------

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
    'EXCEPTION_HANDLER': 'core.views.api_exception_handler',
}

# ---------------------------------------------------------------------------
# Blockchain
# ---------------------------------------------------------------------------

BLOCKCHAIN_PROVIDER_URL       = os.environ.get('BLOCKCHAIN_PROVIDER_URL', 'http://127.0.0.1:8545')
BLOCKCHAIN_NETWORK_ID         = int(os.environ.get('BLOCKCHAIN_NETWORK_ID', '31337'))
BLOCKCHAIN_GAS_LIMIT          = int(os.environ.get('BLOCKCHAIN_GAS_LIMIT', '500000'))
BLOCKCHAIN_CONFIRMATION_TIMEOUT = int(os.environ.get('BLOCKCHAIN_CONFIRMATION_TIMEOUT', '30'))

CONTRACT_ADDRESSES = {
    'PatientRegistry':        os.environ.get('CONTRACT_PATIENT_REGISTRY_ADDRESS', ''),
    'BlockedIPRegistry':      os.environ.get('CONTRACT_BLOCKED_IP_ADDRESS', ''),
    'AttackSignatureRegistry': os.environ.get('CONTRACT_ATTACK_SIGNATURE_ADDRESS', ''),
}

# ---------------------------------------------------------------------------
# Security thresholds (CareGrid threat engine)
# ---------------------------------------------------------------------------

THREAT_SCORE_THRESHOLDS = {
    'LOW':    0,
    'MEDIUM': int(os.environ.get('THREAT_SCORE_MEDIUM', '40')),
    'HIGH':   int(os.environ.get('THREAT_SCORE_HIGH', '61')),
}

RATE_LIMITS = {
    'UNAUTHENTICATED': int(os.environ.get('RATE_LIMIT_UNAUTHENTICATED', '100')),
    'AUTHENTICATED':   int(os.environ.get('RATE_LIMIT_AUTHENTICATED', '500')),
}

AUTO_BLOCK_DURATION            = int(os.environ.get('AUTO_BLOCK_DURATION', '86400'))
CAPTCHA_FAILURE_BLOCK_DURATION = int(os.environ.get('CAPTCHA_FAILURE_BLOCK_DURATION', '900'))
CAPTCHA_MAX_FAILURES           = int(os.environ.get('CAPTCHA_MAX_FAILURES', '3'))

# ---------------------------------------------------------------------------
# AI
# ---------------------------------------------------------------------------

AI_LLM_PROVIDER        = os.environ.get('AI_LLM_PROVIDER', 'openai')
AI_LLM_MODEL           = os.environ.get('AI_LLM_MODEL', 'gpt-4o-mini')
AI_LLM_API_KEY         = os.environ.get('AI_LLM_API_KEY', '')
AI_EMBEDDING_PROVIDER  = os.environ.get('AI_EMBEDDING_PROVIDER', 'local')
AI_EMBEDDING_MODEL     = os.environ.get('AI_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
AI_EMBEDDING_DIMENSION = int(os.environ.get('AI_EMBEDDING_DIMENSION', '384'))
AI_MAX_UPLOAD_SIZE_MB  = int(os.environ.get('AI_MAX_UPLOAD_SIZE_MB', '10'))
AI_OLLAMA_BASE_URL     = os.environ.get('AI_OLLAMA_BASE_URL', 'http://localhost:11434')

FILE_UPLOAD_MAX_MEMORY_SIZE = AI_MAX_UPLOAD_SIZE_MB * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE

# ---------------------------------------------------------------------------
# Logging — console + rotating files (files are kept in production too,
# but a log aggregator like Datadog/Papertrail should tail them)
# ---------------------------------------------------------------------------

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

_LOG_DIR = BASE_DIR / 'logs'
_LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {funcName} {process:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'app_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': _LOG_DIR / 'app.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': _LOG_DIR / 'security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'blockchain_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': _LOG_DIR / 'blockchain.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': _LOG_DIR / 'error.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'level': 'ERROR',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'core': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'blockchain': {
            'handlers': ['console', 'blockchain_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'security': {
            'handlers': ['console', 'security_file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'ai': {
            'handlers': ['console', 'app_file', 'error_file'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}
