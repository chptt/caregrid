"""
Django management command to sync attack signatures to blockchain.
"""

from django.core.management.base import BaseCommand
from core.anomaly_tasks import sync_attack_signatures, cleanup_expired_patterns, get_attack_statistics


class Command(BaseCommand):
    help = 'Sync pending attack signatures to blockchain and clean up expired patterns'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--cleanup-only',
            action='store_true',
            help='Only clean up expired patterns, do not sync signatures',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show attack statistics',
        )
    
    def handle(self, *args, **options):
        if options['stats']:
            self.show_statistics()
            return
        
        if options['cleanup_only']:
            self.cleanup_patterns()
        else:
            self.sync_signatures()
            self.cleanup_patterns()
    
    def sync_signatures(self):
        """Sync pending attack signatures to blockchain."""
        self.stdout.write("Syncing attack signatures to blockchain...")
        
        try:
            synced_count = sync_attack_signatures()
            
            if synced_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully synced {synced_count} attack signatures')
                )
            else:
                self.stdout.write("No pending signatures to sync")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error syncing signatures: {e}')
            )
    
    def cleanup_patterns(self):
        """Clean up expired pattern data."""
        self.stdout.write("Cleaning up expired patterns...")
        
        try:
            cleaned_count = cleanup_expired_patterns()
            
            if cleaned_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Cleaned up {cleaned_count} expired patterns')
                )
            else:
                self.stdout.write("No expired patterns to clean up")
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error cleaning up patterns: {e}')
            )
    
    def show_statistics(self):
        """Show attack detection statistics."""
        self.stdout.write("Attack Detection Statistics:")
        self.stdout.write("=" * 40)
        
        try:
            stats = get_attack_statistics()
            
            self.stdout.write(f"Total attack patterns detected: {stats.get('total_patterns', 0)}")
            self.stdout.write(f"Patterns detected in last 24h: {stats.get('patterns_24h', 0)}")
            self.stdout.write(f"Patterns detected in last 7d: {stats.get('patterns_7d', 0)}")
            self.stdout.write(f"Patterns synced to blockchain: {stats.get('synced_patterns', 0)}")
            self.stdout.write(f"Patterns pending sync: {stats.get('pending_sync', 0)}")
            self.stdout.write(f"High severity patterns (8+): {stats.get('high_severity_patterns', 0)}")
            self.stdout.write(f"Average severity: {stats.get('average_severity', 0)}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error getting statistics: {e}')
            )