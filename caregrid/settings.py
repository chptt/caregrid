"""
Django settings for CareGrid project.

Environment-based configuration for development and production.
See .env.example for available environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')

# Security

SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'django-insecure-n046uykctxbt6c9ojaq!-govw9-u0$+&hklxavbjfw7=kf@vzm'
)

DEBUG = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost,testserver').split(',')
    if h.strip()
]

CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000').split(',')
    if o.strip()
]

# Application definition

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
    'caregrid.apps.ai',
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

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTH_USER_MODEL = 'users.CustomUser'

# Password validation

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files

STATIC_URL = 'static/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Redis

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_DB = int(os.environ.get('REDIS_DB', '0'))

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}',
    }
}

# Blockchain

BLOCKCHAIN_PROVIDER_URL = os.environ.get('BLOCKCHAIN_PROVIDER_URL', 'http://127.0.0.1:8545')
BLOCKCHAIN_NETWORK_ID = int(os.environ.get('BLOCKCHAIN_NETWORK_ID', '31337'))
BLOCKCHAIN_GAS_LIMIT = int(os.environ.get('BLOCKCHAIN_GAS_LIMIT', '500000'))
BLOCKCHAIN_CONFIRMATION_TIMEOUT = int(os.environ.get('BLOCKCHAIN_CONFIRMATION_TIMEOUT', '30'))

CONTRACT_ADDRESSES = {
    'PatientRegistry': os.environ.get('CONTRACT_PATIENT_REGISTRY_ADDRESS', ''),
    'BlockedIPRegistry': os.environ.get('CONTRACT_BLOCKED_IP_ADDRESS', ''),
    'AttackSignatureRegistry': os.environ.get('CONTRACT_ATTACK_SIGNATURE_ADDRESS', ''),
}

# Security thresholds

THREAT_SCORE_THRESHOLDS = {
    'LOW': 0,
    'MEDIUM': int(os.environ.get('THREAT_SCORE_MEDIUM', '40')),
    'HIGH': int(os.environ.get('THREAT_SCORE_HIGH', '61')),
}

RATE_LIMITS = {
    'UNAUTHENTICATED': int(os.environ.get('RATE_LIMIT_UNAUTHENTICATED', '100')),
    'AUTHENTICATED': int(os.environ.get('RATE_LIMIT_AUTHENTICATED', '500')),
}

AUTO_BLOCK_DURATION = int(os.environ.get('AUTO_BLOCK_DURATION', '86400'))
CAPTCHA_FAILURE_BLOCK_DURATION = int(os.environ.get('CAPTCHA_FAILURE_BLOCK_DURATION', '900'))
CAPTCHA_MAX_FAILURES = int(os.environ.get('CAPTCHA_MAX_FAILURES', '3'))

# Logging

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {funcName} {message}',
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
            'filename': BASE_DIR / 'logs' / 'app.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'blockchain_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'blockchain.log',
            'maxBytes': 10 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'error.log',
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

# AI Configuration
AI_LLM_PROVIDER = os.environ.get('AI_LLM_PROVIDER', 'openai')
AI_LLM_MODEL = os.environ.get('AI_LLM_MODEL', 'gpt-4o-mini')
AI_LLM_API_KEY = os.environ.get('AI_LLM_API_KEY', '')
AI_EMBEDDING_PROVIDER = os.environ.get('AI_EMBEDDING_PROVIDER', 'local')
AI_EMBEDDING_MODEL = os.environ.get('AI_EMBEDDING_MODEL', 'all-MiniLM-L6-v2')
AI_EMBEDDING_DIMENSION = int(os.environ.get('AI_EMBEDDING_DIMENSION', '384'))
AI_MAX_UPLOAD_SIZE_MB = int(os.environ.get('AI_MAX_UPLOAD_SIZE_MB', '10'))

# File upload settings for AI documents
FILE_UPLOAD_MAX_MEMORY_SIZE = int(os.environ.get('AI_MAX_UPLOAD_SIZE_MB', '10')) * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE

# Django REST Framework

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_THROTTLE_CLASSES': [],
    'DEFAULT_THROTTLE_RATES': {},
}
