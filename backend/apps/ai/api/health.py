import logging
import os
from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger('ai')


def health(request):
    return JsonResponse({
        'status': 'healthy',
        'service': 'CareGrid AI',
        'version': '1.0.0',
    })


def ready(request):
    db_ok = True
    cache_ok = True
    errors = []

    try:
        from django.db import connections
        connections['default'].cursor().execute('SELECT 1')
    except Exception as e:
        db_ok = False
        errors.append(f'database: {e}')

    try:
        from django.core.cache import cache
        cache.set('health_check', 'ok', 5)
        if cache.get('health_check') != 'ok':
            raise ValueError('Cache readback failed')
    except Exception as e:
        cache_ok = False
        errors.append(f'cache: {e}')

    status = 200 if db_ok and cache_ok else 503
    return JsonResponse({
        'status': 'ready' if status == 200 else 'not_ready',
        'database': 'connected' if db_ok else 'error',
        'cache': 'connected' if cache_ok else 'error',
        'errors': errors,
    }, status=status)
