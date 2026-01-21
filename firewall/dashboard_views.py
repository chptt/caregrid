"""
Security Dashboard API Views

Provides endpoints for real-time security monitoring dashboard.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Count, Q, Max
from django.db import models
from datetime import timedelta
import json

from .models import SecurityLog, BlockedIP, AttackPattern


@require_http_methods(["GET"])
def security_dashboard(request):
    """
    GET /api/security/dashboard/
    
    Returns comprehensive security dashboard data including:
    - Current request rate
    - Top 10 threats by IP
    - Time-series data for the last hour
    - Current blocked IPs count
    - Recent attack patterns
    
    Requirements: 7.1, 7.3, 7.4
    """
    try:
        now = timezone.now()
        one_hour_ago = now - timedelta(hours=1)
        one_minute_ago = now - timedelta(minutes=1)
        
        # Calculate current request rate (requests per minute)
        current_rate = SecurityLog.objects.filter(
            timestamp__gte=one_minute_ago
        ).count()
        
        # Get top 10 threats by IP (highest threat scores in last hour)
        top_threats = SecurityLog.objects.filter(
            timestamp__gte=one_hour_ago
        ).values('ip_address').annotate(
            max_threat_score=Max('threat_score'),
            request_count=Count('id'),
            latest_action=Max('action_taken')
        ).order_by('-max_threat_score')[:10]
        
        # Convert to list format for JSON response
        top_threats_list = []
        for threat in top_threats:
            top_threats_list.append({
                'ip_address': threat['ip_address'],
                'threat_score': threat['max_threat_score'],
                'request_count': threat['request_count'],
                'latest_action': threat['latest_action']
            })
        
        # Generate time-series data (requests per minute for last hour)
        time_series = []
        for i in range(60):  # 60 minutes
            minute_start = now - timedelta(minutes=i+1)
            minute_end = now - timedelta(minutes=i)
            
            minute_count = SecurityLog.objects.filter(
                timestamp__gte=minute_start,
                timestamp__lt=minute_end
            ).count()
            
            time_series.append({
                'timestamp': minute_start.isoformat(),
                'request_count': minute_count
            })
        
        # Reverse to get chronological order
        time_series.reverse()
        
        # Get current blocked IPs count
        blocked_ips_count = BlockedIP.objects.filter(
            expiry_time__gt=now
        ).count()
        
        # Get recent attack patterns (last 24 hours)
        recent_patterns = AttackPattern.objects.filter(
            detected_at__gte=now - timedelta(hours=24)
        ).order_by('-detected_at')[:5]
        
        patterns_list = []
        for pattern in recent_patterns:
            patterns_list.append({
                'pattern_hash': pattern.pattern_hash,
                'severity': pattern.severity,
                'ip_count': pattern.ip_count,
                'request_count': pattern.request_count,
                'detected_at': pattern.detected_at.isoformat(),
                'blockchain_synced': pattern.blockchain_synced
            })
        
        # Get threat level distribution for last hour
        threat_distribution = SecurityLog.objects.filter(
            timestamp__gte=one_hour_ago
        ).values('threat_level').annotate(
            count=Count('id')
        ).order_by('threat_level')
        
        distribution_dict = {item['threat_level']: item['count'] for item in threat_distribution}
        
        dashboard_data = {
            'current_request_rate': current_rate,
            'top_threats': top_threats_list,
            'time_series_data': time_series,
            'blocked_ips_count': blocked_ips_count,
            'recent_attack_patterns': patterns_list,
            'threat_distribution': {
                'low': distribution_dict.get('LOW', 0),
                'medium': distribution_dict.get('MEDIUM', 0),
                'high': distribution_dict.get('HIGH', 0)
            },
            'last_updated': now.isoformat()
        }
        
        return JsonResponse(dashboard_data)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch dashboard data',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def security_stats(request):
    """
    GET /api/security/stats/
    
    Returns basic security statistics for quick overview.
    """
    try:
        now = timezone.now()
        last_24h = now - timedelta(hours=24)
        
        stats = {
            'total_requests_24h': SecurityLog.objects.filter(
                timestamp__gte=last_24h
            ).count(),
            'blocked_requests_24h': SecurityLog.objects.filter(
                timestamp__gte=last_24h,
                action_taken='blocked'
            ).count(),
            'captcha_challenges_24h': SecurityLog.objects.filter(
                timestamp__gte=last_24h,
                action_taken='captcha'
            ).count(),
            'active_blocked_ips': BlockedIP.objects.filter(
                expiry_time__gt=now
            ).count(),
            'attack_patterns_detected': AttackPattern.objects.filter(
                detected_at__gte=last_24h
            ).count()
        }
        
        return JsonResponse(stats)
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch security stats',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def admin_block_ip(request):
    """
    POST /api/security/block/
    
    Manually block an IP address with admin privileges.
    Updates both blockchain and local database.
    
    Request body:
    {
        "ip_address": "192.168.1.100",
        "reason": "Manual block by admin",
        "duration_hours": 24
    }
    
    Requirements: 4.6, 7.6
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        ip_address = data.get('ip_address')
        reason = data.get('reason', 'Manual block by administrator')
        duration_hours = data.get('duration_hours', 24)
        
        if not ip_address:
            return JsonResponse({
                'error': 'IP address is required'
            }, status=400)
        
        # Validate IP address format
        try:
            import ipaddress
            ipaddress.ip_address(ip_address)
        except ValueError:
            return JsonResponse({
                'error': 'Invalid IP address format'
            }, status=400)
        
        # Check if IP is already blocked
        if BlockedIP.objects.filter(ip_address=ip_address, expiry_time__gt=timezone.now()).exists():
            return JsonResponse({
                'error': 'IP address is already blocked'
            }, status=409)
        
        # Calculate expiry time
        expiry_time = timezone.now() + timedelta(hours=duration_hours)
        
        # Generate IP hash for blockchain
        from web3 import Web3
        ip_hash = Web3.keccak(text=ip_address)
        
        # Initialize blockchain service
        from core.blockchain_service import BlockchainService
        blockchain_service = BlockchainService()
        
        # Block IP on blockchain
        tx_hash, success = blockchain_service.block_ip(
            ip_hash,
            duration_hours * 3600,  # Convert to seconds
            reason
        )
        
        # Create local database record
        blocked_ip = BlockedIP.objects.create(
            ip_address=ip_address,
            ip_hash=ip_hash.hex(),
            expiry_time=expiry_time,
            reason=reason,
            is_manual=True,
            blocked_by=request.user if hasattr(request, 'user') and request.user.is_authenticated else None,
            blockchain_synced=success,
            block_tx_hash=tx_hash or ''
        )
        
        response_data = {
            'success': True,
            'message': f'IP {ip_address} has been blocked',
            'blocked_ip': {
                'ip_address': blocked_ip.ip_address,
                'expiry_time': blocked_ip.expiry_time.isoformat(),
                'reason': blocked_ip.reason,
                'blockchain_synced': blocked_ip.blockchain_synced,
                'tx_hash': blocked_ip.block_tx_hash
            }
        }
        
        if not success:
            response_data['warning'] = 'IP blocked locally but blockchain sync failed'
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to block IP address',
            'details': str(e)
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def admin_unblock_ip(request):
    """
    POST /api/security/unblock/
    
    Manually unblock an IP address with admin privileges.
    Updates both blockchain and local database.
    
    Request body:
    {
        "ip_address": "192.168.1.100"
    }
    
    Requirements: 4.6, 7.6
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        ip_address = data.get('ip_address')
        
        if not ip_address:
            return JsonResponse({
                'error': 'IP address is required'
            }, status=400)
        
        # Find blocked IP record
        try:
            blocked_ip = BlockedIP.objects.get(
                ip_address=ip_address,
                expiry_time__gt=timezone.now()
            )
        except BlockedIP.DoesNotExist:
            return JsonResponse({
                'error': 'IP address is not currently blocked'
            }, status=404)
        
        # Initialize blockchain service
        from core.blockchain_service import BlockchainService
        blockchain_service = BlockchainService()
        
        # Unblock IP on blockchain
        from web3 import Web3
        ip_hash = Web3.keccak(text=ip_address)
        tx_hash, success = blockchain_service.unblock_ip(ip_hash)
        
        # Update local database record (set expiry to now to effectively unblock)
        blocked_ip.expiry_time = timezone.now()
        blocked_ip.save()
        
        # Log the unblock action
        SecurityLog.objects.create(
            ip_address=ip_address,
            threat_score=0,  # Reset threat score
            threat_level='LOW',
            endpoint='/api/security/unblock/',
            method='POST',
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            action_taken='unblocked',
            blocked_on_blockchain=False
        )
        
        response_data = {
            'success': True,
            'message': f'IP {ip_address} has been unblocked',
            'unblocked_ip': {
                'ip_address': blocked_ip.ip_address,
                'original_expiry': blocked_ip.expiry_time.isoformat(),
                'reason': blocked_ip.reason,
                'blockchain_synced': success,
                'tx_hash': tx_hash or ''
            }
        }
        
        if not success:
            response_data['warning'] = 'IP unblocked locally but blockchain sync failed'
        
        return JsonResponse(response_data)
        
    except json.JSONDecodeError:
        return JsonResponse({
            'error': 'Invalid JSON in request body'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to unblock IP address',
            'details': str(e)
        }, status=500)


@require_http_methods(["GET"])
def blocked_ips_list(request):
    """
    GET /api/security/blocked/
    
    Returns list of currently blocked IP addresses.
    """
    try:
        now = timezone.now()
        blocked_ips = BlockedIP.objects.filter(
            expiry_time__gt=now
        ).order_by('-block_time')
        
        blocked_list = []
        for blocked_ip in blocked_ips:
            blocked_list.append({
                'ip_address': blocked_ip.ip_address,
                'block_time': blocked_ip.block_time.isoformat(),
                'expiry_time': blocked_ip.expiry_time.isoformat(),
                'reason': blocked_ip.reason,
                'is_manual': blocked_ip.is_manual,
                'blocked_by': blocked_ip.blocked_by.username if blocked_ip.blocked_by else None,
                'blockchain_synced': blocked_ip.blockchain_synced
            })
        
        return JsonResponse({
            'blocked_ips': blocked_list,
            'total_count': len(blocked_list)
        })
        
    except Exception as e:
        return JsonResponse({
            'error': 'Failed to fetch blocked IPs',
            'details': str(e)
        }, status=500)