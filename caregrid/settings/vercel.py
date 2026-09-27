"""
Vercel deployment settings for CareGrid.

Constraints:
  - Filesystem is read-only EXCEPT /tmp  → SQLite lives at /tmp/db.sqlite3
  - No Redis available                   → use LocMemCache (in-process)
  - No persistent disk                   → uploads and logs go to /tmp
  - Function timeout is 60s (Pro)        → blockchain/heavy AI disabled
  - Static files collected at build time → served by WhiteNoise

Set in Vercel dashboard:
  DJANGO_SETTINGS_MODULE = caregrid.settings.vercel
  DJANGO_SECRET_KEY      = <strong random string>
  AI_LLM_API_KEY         = <your OpenAI key>
"""

import os
from .base import *  # noqa: F401, F403

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------

DEBUG = False

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'vercel-change-me-in-dashboard')

# Vercel injects the deployment URL as VERCEL_URL (no https://)
_vercel_url = os.environ.get('VERCEL_URL', '')
_extra_hosts = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', '').split(',') if h.strip()]

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.vercel.app']
if _vercel_url:
    ALLOWED_HOSTS.append(_vercel_url)
ALLOWED_HOSTS += _extra_hosts

CSRF_TRUSTED_ORIGINS = [
    f'https://{_vercel_url}' if _vercel_url else 'https://localhost',
] + [
    o.strip()
    for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if o.strip()
]

# ---------------------------------------------------------------------------
# Database — SQLite in /tmp (writable on Vercel, wiped between cold starts)
# Data is pre-seeded at build time via build_files.sh and copied to /tmp
# ---------------------------------------------------------------------------

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/db.sqlite3',
    }
}

# ---------------------------------------------------------------------------
# Cache — in-process memory (no Redis on Vercel)
# Good enough for session storage and rate limiting in a single function
# ---------------------------------------------------------------------------

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'caregrid-vercel',
    }
}

# Sessions stored in cache (LocMemCache — per process, not shared)
SESSION_ENGINE     = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Also expose Redis vars as no-ops so middleware doesn't crash on missing attrs
REDIS_HOST     = 'localhost'
REDIS_PORT     = 6379
REDIS_DB       = 0
REDIS_PASSWORD = ''
REDIS_URL      = ''

# ---------------------------------------------------------------------------
# Static files — WhiteNoise serves pre-collected files from staticfiles/
# build_files.sh runs collectstatic before Vercel deploys
# ---------------------------------------------------------------------------

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',     # must be second
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.SecurityMiddleware',
]

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405 — from base

# Media uploads go to /tmp on Vercel (not persistent, but functional)
MEDIA_ROOT = '/tmp/media'
MEDIA_URL  = '/media/'

# Document uploads (AI module)
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = FILE_UPLOAD_MAX_MEMORY_SIZE

# ---------------------------------------------------------------------------
# CORS — allow the Vercel deployment domain
# ---------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS = [
    f'https://{_vercel_url}' if _vercel_url else 'http://localhost:3000',
] + [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if o.strip()
]
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER        = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT            = False   # Vercel handles TLS termination
SECURE_HSTS_SECONDS            = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD            = True
SECURE_CONTENT_TYPE_NOSNIFF    = True
SECURE_BROWSER_XSS_FILTER      = True
X_FRAME_OPTIONS                = 'DENY'
SESSION_COOKIE_SECURE          = True
SESSION_COOKIE_HTTPONLY        = True
SESSION_COOKIE_SAMESITE        = 'Lax'
CSRF_COOKIE_SECURE             = True

# ---------------------------------------------------------------------------
# Logging — stdout only (Vercel captures stdout as function logs)
# No file handlers — /tmp is writable but Vercel doesn't persist logs
# ---------------------------------------------------------------------------

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'simple': {
            'format': '{levelname} {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django':     {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'core':       {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'blockchain': {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'security':   {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
        'ai':         {'handlers': ['console'], 'level': 'WARNING', 'propagate': False},
    },
}

# ---------------------------------------------------------------------------
# AI — OpenAI only (no local sentence-transformers, no FAISS on Vercel)
# faiss-cpu and sentence-transformers are excluded from requirements-vercel.txt
# ---------------------------------------------------------------------------

AI_LLM_PROVIDER        = 'openai'
AI_LLM_MODEL           = os.environ.get('AI_LLM_MODEL', 'gpt-4o-mini')
AI_LLM_API_KEY         = os.environ.get('AI_LLM_API_KEY', '')
AI_EMBEDDING_PROVIDER  = 'openai'   # local embeddings need sentence-transformers
AI_EMBEDDING_MODEL     = os.environ.get('AI_OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
AI_EMBEDDING_DIMENSION = 1536       # text-embedding-3-small dimension

# ---------------------------------------------------------------------------
# Blockchain — offline mode (no Hardhat node on Vercel)
# BlockchainService.__init__ already handles connection failures gracefully
# ---------------------------------------------------------------------------

BLOCKCHAIN_PROVIDER_URL = os.environ.get('BLOCKCHAIN_PROVIDER_URL', 'http://127.0.0.1:8545')
CONTRACT_ADDRESSES = {
    'PatientRegistry':        os.environ.get('CONTRACT_PATIENT_REGISTRY_ADDRESS', ''),
    'BlockedIPRegistry':      os.environ.get('CONTRACT_BLOCKED_IP_ADDRESS', ''),
    'AttackSignatureRegistry': os.environ.get('CONTRACT_ATTACK_SIGNATURE_ADDRESS', ''),
}

# ---------------------------------------------------------------------------
# Password hashers — skip Argon2 (requires argon2-cffi, keep deps minimal)
# ---------------------------------------------------------------------------

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
