"""
Background tasks for anomaly detection and attack signature management.
"""

import logging
from typing import Optional

from .anomaly_detector import AnomalyDetector
from .blockchain_service import get_blockchain_service

logger = logging.getLogger(__name__)


def sync_attack_signatures() -> int:
    """
    Sync pending attack signatures to blockchain.
    
    This function can be called periodically by a background task scheduler
    like Celery or Django-RQ to ensure attack signatures are eventually
    stored on the blockchain even if the initial attempt failed.
    
    Returns:
        Number of signatures successfully synced
    """
    try:
        import redis
        from django.conf import settings
        
        # Initialize Redis client
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # Initialize blockchain service and anomaly detector
        blockchain_service = get_blockchain_service()
        anomaly_detector = AnomalyDetector(redis_client, blockchain_service)
        
        # Sync pending signatures
        synced_count = anomaly_detector.sync_pending_signatures()
        
        if synced_count > 0:
            logger.info(f"Background sync completed: {synced_count} signatures synced")
        
        return synced_count
        
    except Exception as e:
        logger.error(f"Error in background signature sync: {e}")
        return 0


def cleanup_expired_patterns() -> int:
    """
    Clean up expired pattern data from Redis.
    
    This function removes old pattern tracking data to prevent Redis
    from growing indefinitely.
    
    Returns:
        Number of patterns cleaned up
    """
    try:
        import redis
        from django.conf import settings
        
        # Initialize Redis client
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True
        )
        
        # Initialize blockchain service and anomaly detector
        blockchain_service = get_blockchain_service()
        anomaly_detector = AnomalyDetector(redis_client, blockchain_service)
        
        # Clean up expired patterns
        cleaned_count = anomaly_detector.cleanup_expired_patterns()
        
        if cleaned_count > 0:
            logger.info(f"Pattern cleanup completed: {cleaned_count} patterns cleaned")
        
        return cleaned_count
        
    except Exception as e:
        logger.error(f"Error in pattern cleanup: {e}")
        return 0


def get_attack_statistics() -> dict:
    """
    Get statistics about detected attacks and patterns.
    
    Returns:
        Dictionary with attack statistics
    """
    try:
        from firewall.models import AttackPattern
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        last_7d = now - timedelta(days=7)
        
        stats = {
            'total_patterns': AttackPattern.objects.count(),
            'patterns_24h': AttackPattern.objects.filter(detected_at__gte=last_24h).count(),
            'patterns_7d': AttackPattern.objects.filter(detected_at__gte=last_7d).count(),
            'synced_patterns': AttackPattern.objects.filter(blockchain_synced=True).count(),
            'pending_sync': AttackPattern.objects.filter(blockchain_synced=False).count(),
            'high_severity_patterns': AttackPattern.objects.filter(severity__gte=8).count(),
        }
        
        # Calculate average severity
        patterns = AttackPattern.objects.all()
        if patterns.exists():
            total_severity = sum(p.severity for p in patterns)
            stats['average_severity'] = round(total_severity / patterns.count(), 2)
        else:
            stats['average_severity'] = 0
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting attack statistics: {e}")
        return {}