from collections import defaultdict
from django.utils.timezone import now

ip_attempts = defaultdict(list)

def track_login_attempt(ip):
    now_time = now()
    # Keep only attempts within the last 60 seconds
    ip_attempts[ip] = [t for t in ip_attempts[ip] if (now_time - t).seconds < 60]
    ip_attempts[ip].append(now_time)
    return len(ip_attempts[ip])