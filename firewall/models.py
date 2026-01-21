from django.db import models
from django.conf import settings

class SecurityLog(models.Model):
    THREAT_LEVEL_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]
    
    # Basic request information
    ip_address = models.GenericIPAddressField()
    threat_score = models.IntegerField()
    threat_level = models.CharField(max_length=10, choices=THREAT_LEVEL_CHOICES)
    endpoint = models.CharField(max_length=255)
    method = models.CharField(max_length=10)
    user_agent = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Threat factors
    rate_score = models.IntegerField(default=0)
    pattern_score = models.IntegerField(default=0)
    session_score = models.IntegerField(default=0)
    entropy_score = models.IntegerField(default=0)
    auth_failure_score = models.IntegerField(default=0)
    
    # Action taken
    action_taken = models.CharField(max_length=50)  # 'allowed', 'captcha', 'blocked'
    
    # Blockchain sync fields
    blocked_on_blockchain = models.BooleanField(default=False)
    block_tx_hash = models.CharField(max_length=66, blank=True)

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['threat_level']),
        ]

    def __str__(self):
        return f"{self.ip_address} - {self.threat_level} ({self.threat_score}) at {self.timestamp}"


class BlockedIP(models.Model):
    # IP address and hash fields
    ip_address = models.GenericIPAddressField(unique=True)
    ip_hash = models.CharField(max_length=66)  # Blockchain hash
    
    # Timing fields
    block_time = models.DateTimeField(auto_now_add=True)
    expiry_time = models.DateTimeField()
    
    # Block details
    reason = models.TextField()
    is_manual = models.BooleanField(default=False)  # Manual vs automatic flag
    blocked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Blockchain sync fields
    blockchain_synced = models.BooleanField(default=False)
    block_tx_hash = models.CharField(max_length=66, blank=True)

    class Meta:
        ordering = ['-block_time']
        indexes = [
            models.Index(fields=['ip_address']),
            models.Index(fields=['expiry_time']),
            models.Index(fields=['blockchain_synced']),
        ]

    def __str__(self):
        return f"{self.ip_address} blocked until {self.expiry_time}"

    @property
    def is_expired(self):
        """Check if the block has expired"""
        from django.utils import timezone
        return timezone.now() > self.expiry_time


class AttackPattern(models.Model):
    # Pattern hash and JSON data fields
    pattern_hash = models.CharField(max_length=66, unique=True)
    pattern_data = models.JSONField()  # Store pattern characteristics
    
    # Detection time and severity
    detected_at = models.DateTimeField(auto_now_add=True)
    severity = models.IntegerField()  # 1-10 scale
    
    # IP and request counts
    ip_count = models.IntegerField()  # Number of IPs involved
    request_count = models.IntegerField()  # Total requests in pattern
    
    # Blockchain sync fields
    blockchain_synced = models.BooleanField(default=False)
    signature_tx_hash = models.CharField(max_length=66, blank=True)

    class Meta:
        ordering = ['-detected_at']
        indexes = [
            models.Index(fields=['pattern_hash']),
            models.Index(fields=['detected_at']),
            models.Index(fields=['severity']),
            models.Index(fields=['blockchain_synced']),
        ]

    def __str__(self):
        return f"Attack pattern {self.pattern_hash[:8]}... (severity {self.severity})"
