import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings')

os.environ.setdefault('AI_LLM_PROVIDER', 'openai')
os.environ.setdefault('AI_LLM_MODEL', 'gpt-4o-mini')
os.environ.setdefault('AI_LLM_API_KEY', 'test-key')
os.environ.setdefault('AI_EMBEDDING_PROVIDER', 'test')

settings.CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

django.setup()


def pytest_configure():
    pass
