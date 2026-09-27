"""
Production settings for CareGrid.

Inherits everything from base.py and overrides/adds production-only config.

Usage:
    DJANGO_SETTINGS_MODULE=caregrid.settings.production

Every secret loaded here must come from environment variables.
No hardcoded credentials, no fallback values for secrets.
"""

import os

from .base import *  # noqa: F401, F403 — intentional settings inheritance

# ---------------------------------------------------------------------------
# Core security — these MUST be set in the environment
# ---------------------------------------------------------------------------

SECRET_KEY = os.environ['DJANGO_SECRET_KEY']  # Raise KeyError if missing

DEBUG = False

# Accept the Vercel deployment domain plus any custom domain.
# Example: ALLOWED_HOSTS=caregrid.vercel.app,api.caregrid.com
ALLOWED_HOSTS = [
    h.strip()
    for h in os.environ.get('ALLOWED_HOSTS', '').split(',')
    if h.strip()
]

if not ALLOWED_HOSTS:
    raise RuntimeError(
        'ALLOWED_HOSTS must be set in production. '
        'Example: caregrid.vercel.app,api.caregrid.com'
    )

# ---------------------------------------------------------------------------
# HTTPS / HSTS
# ---------------------------------------------------------------------------

SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT', 'True').lower() in ('true', '1', 'yes')

# Tell Django it's behind a TLS-terminating proxy (Nginx, Vercel edge, etc.)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# HSTS — tell browsers to use HTTPS for 1 year, include subdomains, allow preload
SECURE_HSTS_SECONDS           = int(os.environ.get('SECURE_HSTS_SECONDS', '31536000'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD           = True

# ---------------------------------------------------------------------------
# Cookie security
# ---------------------------------------------------------------------------

SESSION_COOKIE_SECURE   = True   # Only send session cookie over HTTPS
SESSION_COOKIE_HTTPONLY = True   # Block JS access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection while allowing top-level nav
SESSION_COOKIE_AGE      = 28800  # 8 hours

CSRF_COOKIE_SECURE   = True
CSRF_COOKIE_HTTPONLY = False  # Must be False — JS reads the CSRF token value
CSRF_COOKIE_SAMESITE = 'Lax'

# Trust the CSRF token from Vercel/Nginx proxy
CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',')
    if o.strip()
]

# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------

SECURE_CONTENT_TYPE_NOSNIFF = True  # X-Content-Type-Options: nosniff
SECURE_BROWSER_XSS_FILTER   = True  # X-XSS-Protection (legacy browsers)
X_FRAME_OPTIONS              = 'DENY'

# Content Security Policy — tighten as needed for your frontend
# This default allows same-origin resources and OpenAI API calls
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ---------------------------------------------------------------------------
# Database — PostgreSQL (required in production)
# ---------------------------------------------------------------------------

# Accept either a full DATABASE_URL (Railway, Render, Heroku style)
# or individual DB_* variables.

_database_url = os.environ.get('DATABASE_URL', '')

if _database_url:
    # Parse postgres://user:pass@host:port/dbname
    import urllib.parse as _up

    _u = _up.urlparse(_database_url)
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     _u.path.lstrip('/'),
            'USER':     _u.username or '',
            'PASSWORD': _u.password or '',
            'HOST':     _u.hostname or 'localhost',
            'PORT':     str(_u.port or 5432),
            'OPTIONS': {
                'sslmode': os.environ.get('DB_SSLMODE', 'require'),
            },
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
        }
    }
else:
    # Fall back to individual variables
    DATABASES = {
        'default': {
            'ENGINE':   'django.db.backends.postgresql',
            'NAME':     os.environ['DB_NAME'],
            'USER':     os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST':     os.environ.get('DB_HOST', 'localhost'),
            'PORT':     os.environ.get('DB_PORT', '5432'),
            'OPTIONS': {
                'sslmode': os.environ.get('DB_SSLMODE', 'require'),
            },
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            'CONN_HEALTH_CHECKS': True,
        }
    }

# ---------------------------------------------------------------------------
# Redis — production URL almost always comes as a single REDIS_URL
# ---------------------------------------------------------------------------

REDIS_URL = os.environ.get('REDIS_URL', '')
if not REDIS_URL:
    # Build from parts if REDIS_URL is not provided
    _host = os.environ.get('REDIS_HOST', 'localhost')
    _port = os.environ.get('REDIS_PORT', '6379')
    _db   = os.environ.get('REDIS_DB', '0')
    _pw   = os.environ.get('REDIS_PASSWORD', '')
    _auth = f':{_pw}@' if _pw else ''
    REDIS_URL = f'redis://{_auth}{_host}:{_port}/{_db}'

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS':  'django_redis.client.DefaultClient',
            'IGNORE_EXCEPTIONS': False,
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'CONNECTION_POOL_KWARGS': {'max_connections': 50},
            # Re-use connections across requests in the same thread
            'REDIS_CLIENT_KWARGS': {'health_check_interval': 30},
        },
        'KEY_PREFIX': 'caregrid',
        'TIMEOUT': 300,
    }
}

# Sessions stored in Redis (no DB round-trips per request)
SESSION_ENGINE     = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ---------------------------------------------------------------------------
# CORS — production origins only
# ---------------------------------------------------------------------------

# Example: CORS_ALLOWED_ORIGINS=https://caregrid.vercel.app,https://app.caregrid.com
CORS_ALLOWED_ORIGINS = [
    o.strip()
    for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
    if o.strip()
]

if not CORS_ALLOWED_ORIGINS:
    raise RuntimeError(
        'CORS_ALLOWED_ORIGINS must be set in production. '
        'Example: https://caregrid.vercel.app'
    )

CORS_ALLOW_CREDENTIALS = True

# Vercel preview deployments use random subdomains — allow them via regex
_cors_regex = os.environ.get('CORS_ALLOWED_ORIGIN_REGEXES', '')
if _cors_regex:
    CORS_ALLOWED_ORIGIN_REGEXES = [r.strip() for r in _cors_regex.split(',') if r.strip()]

# ---------------------------------------------------------------------------
# Static files — served by Nginx (or WhiteNoise as fallback)
# ---------------------------------------------------------------------------

STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # noqa: F405 — imported from base

# WhiteNoise handles serving compressed static files from staticfiles/
# Insert it right after SecurityMiddleware so it runs before everything else
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')  # noqa: F405

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

# ---------------------------------------------------------------------------
# Email — used for admin error emails (500s)
# ---------------------------------------------------------------------------

EMAIL_BACKEND  = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT     = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'noreply@caregrid.com')

ADMINS = [
    ('CareGrid Admin', os.environ.get('ADMIN_EMAIL', 'admin@caregrid.com')),
]

# ---------------------------------------------------------------------------
# Logging — production: console only (stdout → log aggregator)
# Rotate file handlers are still here for deployments that have a persistent
# disk (Railway, Fly.io, VPS). Remove the file handlers if on a read-only FS.
# ---------------------------------------------------------------------------

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'WARNING')

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            # Structured JSON logs are easier to parse in Datadog / CloudWatch
            '()': 'django.utils.log.ServerFormatter',
            'format': '%(levelname)s %(asctime)s %(module)s %(funcName)s %(process)d %(message)s',
        },
        'verbose': {
            'format': '{levelname} {asctime} {module} {funcName} {process:d} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'filters': ['require_debug_false'],
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'mail_admins'],
            'level': LOG_LEVEL,
            'propagate': True,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'blockchain': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'security': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'ai': {
            'handlers': ['console'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
    },
}

# ---------------------------------------------------------------------------
# AI — same as base, but key is required in production
# ---------------------------------------------------------------------------

AI_LLM_API_KEY = os.environ.get('AI_LLM_API_KEY', '')
if not AI_LLM_API_KEY and os.environ.get('AI_LLM_PROVIDER', 'openai') != 'ollama':
    import warnings
    warnings.warn(
        'AI_LLM_API_KEY is not set. LLM features will fail for non-Ollama providers.',
        RuntimeWarning,
        stacklevel=1,
    )

# ---------------------------------------------------------------------------
# Blockchain — same as base, warn if contracts are missing
# ---------------------------------------------------------------------------

_missing_contracts = [
    name for name, addr in CONTRACT_ADDRESSES.items() if not addr  # noqa: F405
]
if _missing_contracts:
    import warnings
    warnings.warn(
        f'Contract addresses not set for: {_missing_contracts}. '
        'Blockchain features will run in offline mode.',
        RuntimeWarning,
        stacklevel=1,
    )

# ---------------------------------------------------------------------------
# Performance
# ---------------------------------------------------------------------------

# Cache the default password hasher iterations (expensive on every login)
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]
