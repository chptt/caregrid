"""
Django management command to clean up expired IP blocks.
This task removes expired IPs from both blockchain and local database.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from firewall.models import BlockedIP
from core.blockchain_service import get_blockchain_service
import logging

logger = logging.getLogger('security')


class Command(BaseCommand):
    help = 'Clean up expired IP blocks from blockchain and local database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned up without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force cleanup even if blockchain is not available',
        )
        parser.add_argument(
            '--local-only',
            action='store_true',
            help='Only clean up local database, skip blockchain cleanup',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']
        self.local_only = options['local_only']
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Check blockchain connection
        if not self.local_only and not blockchain_service.is_connected() and not self.force:
            self.stdout.write(
                self.style.ERROR(
                    "Blockchain not available. Use --force to cleanup local database only, "
                    "or --local-only to skip blockchain cleanup."
                )
            )
            return
        
        # Clean up blockchain first (if connected and not local-only)
        blockchain_cleaned = 0
        if not self.local_only:
            blockchain_cleaned = self.cleanup_blockchain_blocks(blockchain_service)
        
        # Clean up local database
        local_cleaned = self.cleanup_local_blocks()
        
        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("CLEANUP SUMMARY:")
        if not self.local_only:
            self.stdout.write(f"Blockchain blocks cleaned: {blockchain_cleaned}")
        self.stdout.write(f"Local database records cleaned: {local_cleaned}")
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No actual changes were made"))
        else:
            self.stdout.write(self.style.SUCCESS("Cleanup completed successfully"))
    
    def cleanup_blockchain_blocks(self, blockchain_service):
        """Clean up expired blocks on blockchain."""
        self.stdout.write("Cleaning up expired blocks on blockchain...")
        
        try:
            if self.dry_run:
                self.stdout.write("  [DRY RUN] Would call blockchain cleanup function")
                return 0
            
            # Call blockchain cleanup function
            tx_hash, success = blockchain_service.cleanup_expired_blocks()
            
            if success:
                self.stdout.write(
                    self.style.SUCCESS(f"  Blockchain cleanup successful. TX: {tx_hash}")
                )
                return 1  # We don't know exact count from blockchain
            else:
                self.stdout.write(
                    self.style.ERROR("  Blockchain cleanup failed")
                )
                return 0
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error during blockchain cleanup: {e}")
            )
            logger.error(f"Blockchain cleanup error: {e}")
            return 0
    
    def cleanup_local_blocks(self):
        """Clean up expired blocks in local database."""
        self.stdout.write("Cleaning up expired blocks in local database...")
        
        try:
            # Find expired blocks
            now = timezone.now()
            expired_blocks = BlockedIP.objects.filter(expiry_time__lt=now)
            
            count = expired_blocks.count()
            
            if count == 0:
                self.stdout.write("  No expired blocks found in local database")
                return 0
            
            # Show what will be cleaned
            self.stdout.write(f"  Found {count} expired blocks:")
            for block in expired_blocks[:10]:  # Show first 10
                expired_duration = now - block.expiry_time
                self.stdout.write(
                    f"    - {block.ip_address} (expired {expired_duration} ago)"
                )
            
            if count > 10:
                self.stdout.write(f"    ... and {count - 10} more")
            
            if self.dry_run:
                self.stdout.write("  [DRY RUN] Would delete these expired blocks")
                return count
            
            # Delete expired blocks
            with transaction.atomic():
                deleted_count, _ = expired_blocks.delete()
                
            self.stdout.write(
                self.style.SUCCESS(f"  Deleted {deleted_count} expired blocks from local database")
            )
            
            return deleted_count
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error during local cleanup: {e}")
            )
            logger.error(f"Local cleanup error: {e}")
            return 0
    
    def get_cleanup_statistics(self):
        """Get statistics about blocks that need cleanup."""
        try:
            now = timezone.now()
            
            # Count expired blocks
            expired_count = BlockedIP.objects.filter(expiry_time__lt=now).count()
            
            # Count blocks expiring soon (next 24 hours)
            soon_expiry = now + timezone.timedelta(hours=24)
            expiring_soon_count = BlockedIP.objects.filter(
                expiry_time__gte=now,
                expiry_time__lt=soon_expiry
            ).count()
            
            # Count manual vs automatic blocks
            manual_expired = BlockedIP.objects.filter(
                expiry_time__lt=now,
                is_manual=True
            ).count()
            
            auto_expired = expired_count - manual_expired
            
            return {
                'expired_total': expired_count,
                'expiring_soon': expiring_soon_count,
                'expired_manual': manual_expired,
                'expired_automatic': auto_expired
            }
            
        except Exception as e:
            logger.error(f"Error getting cleanup statistics: {e}")
            return {}