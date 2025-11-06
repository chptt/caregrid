import time
from django.core.cache import cache
from django.http import JsonResponse

class IPMonitorMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.rate_limit = 20  # requests per minute
        self.block_duration = 300  # seconds

    def __call__(self, request):
        ip = self.get_client_ip(request)
        now = time.time()

        # Check if IP is blocked
        blocked_until = cache.get(f"blocked:{ip}")
        if blocked_until and now < blocked_until:
            return JsonResponse({'error': 'IP temporarily blocked'}, status=429)

        # Track request count
        history = cache.get(f"history:{ip}", [])
        history = [t for t in history if now - t < 60]  # keep last 60s
        history.append(now)
        cache.set(f"history:{ip}", history, timeout=60)

        if len(history) > self.rate_limit:
            cache.set(f"blocked:{ip}", now + self.block_duration, timeout=self.block_duration)
            return JsonResponse({'error': 'IP blocked due to suspicious activity'}, status=429)

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')