"""
Django management command to sync pending blockchain operations.
This task retries failed transactions and updates sync status in database.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from core.models import Patient
from firewall.models import BlockedIP, AttackPattern
from core.blockchain_service import get_blockchain_service
import logging
import time

logger = logging.getLogger('blockchain')


class Command(BaseCommand):
    help = 'Sync pending blockchain operations and retry failed transactions'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be synced without making changes',
        )
        parser.add_argument(
            '--max-retries',
            type=int,
            default=3,
            help='Maximum number of retry attempts per operation (default: 3)',
        )
        parser.add_argument(
            '--retry-delay',
            type=int,
            default=5,
            help='Delay between retries in seconds (default: 5)',
        )
        parser.add_argument(
            '--patients-only',
            action='store_true',
            help='Only sync patient registrations',
        )
        parser.add_argument(
            '--blocks-only',
            action='store_true',
            help='Only sync IP blocks',
        )
        parser.add_argument(
            '--signatures-only',
            action='store_true',
            help='Only sync attack signatures',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show sync statistics without performing sync',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.max_retries = options['max_retries']
        self.retry_delay = options['retry_delay']
        self.patients_only = options['patients_only']
        self.blocks_only = options['blocks_only']
        self.signatures_only = options['signatures_only']
        
        if options['stats']:
            self.show_sync_statistics()
            return
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN MODE - No changes will be made"))
        
        # Get blockchain service
        blockchain_service = get_blockchain_service()
        
        # Check blockchain connection
        if not blockchain_service.is_connected():
            self.stdout.write(
                self.style.ERROR("Blockchain not available. Cannot perform sync operations.")
            )
            return
        
        # Initialize counters
        sync_results = {
            'patients_synced': 0,
            'patients_failed': 0,
            'blocks_synced': 0,
            'blocks_failed': 0,
            'signatures_synced': 0,
            'signatures_failed': 0
        }
        
        # Sync different types of operations
        if not self.blocks_only and not self.signatures_only:
            self.sync_patient_registrations(blockchain_service, sync_results)
        
        if not self.patients_only and not self.signatures_only:
            self.sync_ip_blocks(blockchain_service, sync_results)
        
        if not self.patients_only and not self.blocks_only:
            self.sync_attack_signatures(blockchain_service, sync_results)
        
        # Show summary
        self.show_sync_summary(sync_results)
    
    def sync_patient_registrations(self, blockchain_service, results):
        """Sync pending patient registrations to blockchain."""
        self.stdout.write("Syncing patient registrations...")
        
        try:
            # Find patients not yet registered on blockchain
            pending_patients = Patient.objects.filter(
                Q(blockchain_registered=False) | Q(registration_tx_hash='')
            )
            
            count = pending_patients.count()
            if count == 0:
                self.stdout.write("  No pending patient registrations found")
                return
            
            self.stdout.write(f"  Found {count} pending patient registrations")
            
            for patient in pending_patients:
                success = self.sync_single_patient(blockchain_service, patient)
                if success:
                    results['patients_synced'] += 1
                else:
                    results['patients_failed'] += 1
                
                # Small delay between operations
                if not self.dry_run:
                    time.sleep(1)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error during patient sync: {e}")
            )
            logger.error(f"Patient sync error: {e}")
    
    def sync_single_patient(self, blockchain_service, patient):
        """Sync a single patient registration."""
        try:
            self.stdout.write(f"    Syncing patient: {patient.name} (ID: {patient.blockchain_id})")
            
            if self.dry_run:
                self.stdout.write("      [DRY RUN] Would register patient on blockchain")
                return True
            
            # Check if already registered on blockchain
            if blockchain_service.is_patient_registered(patient.blockchain_id):
                self.stdout.write("      Already registered on blockchain, updating local record")
                patient.blockchain_registered = True
                patient.save(update_fields=['blockchain_registered'])
                return True
            
            # Attempt registration with retries
            for attempt in range(self.max_retries):
                try:
                    tx_hash, success = blockchain_service.register_patient(patient.blockchain_id)
                    
                    if success:
                        # Update patient record
                        with transaction.atomic():
                            patient.blockchain_registered = True
                            patient.registration_tx_hash = tx_hash
                            patient.save(update_fields=['blockchain_registered', 'registration_tx_hash'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"      Registered successfully. TX: {tx_hash}")
                        )
                        return True
                    else:
                        raise Exception("Registration failed")
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        self.stdout.write(f"      Attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(self.retry_delay)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"      Failed after {self.max_retries} attempts: {e}")
                        )
                        logger.error(f"Patient registration failed for {patient.id}: {e}")
                        return False
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"      Error syncing patient {patient.id}: {e}")
            )
            logger.error(f"Patient sync error for {patient.id}: {e}")
            return False
    
    def sync_ip_blocks(self, blockchain_service, results):
        """Sync pending IP blocks to blockchain."""
        self.stdout.write("Syncing IP blocks...")
        
        try:
            # Find blocks not yet synced to blockchain
            pending_blocks = BlockedIP.objects.filter(
                Q(blockchain_synced=False) | Q(block_tx_hash='')
            )
            
            count = pending_blocks.count()
            if count == 0:
                self.stdout.write("  No pending IP blocks found")
                return
            
            self.stdout.write(f"  Found {count} pending IP blocks")
            
            for block in pending_blocks:
                success = self.sync_single_block(blockchain_service, block)
                if success:
                    results['blocks_synced'] += 1
                else:
                    results['blocks_failed'] += 1
                
                # Small delay between operations
                if not self.dry_run:
                    time.sleep(1)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error during IP block sync: {e}")
            )
            logger.error(f"IP block sync error: {e}")
    
    def sync_single_block(self, blockchain_service, block):
        """Sync a single IP block."""
        try:
            self.stdout.write(f"    Syncing IP block: {block.ip_address}")
            
            if self.dry_run:
                self.stdout.write("      [DRY RUN] Would sync IP block to blockchain")
                return True
            
            # Check if block has expired
            if block.is_expired:
                self.stdout.write("      Block has expired, skipping sync")
                return True
            
            # Check if already blocked on blockchain
            if blockchain_service.is_ip_blocked(block.ip_hash):
                self.stdout.write("      Already blocked on blockchain, updating local record")
                block.blockchain_synced = True
                block.save(update_fields=['blockchain_synced'])
                return True
            
            # Calculate remaining duration
            now = timezone.now()
            remaining_duration = int((block.expiry_time - now).total_seconds())
            
            if remaining_duration <= 0:
                self.stdout.write("      Block has expired, skipping sync")
                return True
            
            # Attempt blocking with retries
            for attempt in range(self.max_retries):
                try:
                    tx_hash, success = blockchain_service.block_ip(
                        block.ip_hash,
                        remaining_duration,
                        block.reason,
                        block.is_manual
                    )
                    
                    if success:
                        # Update block record
                        with transaction.atomic():
                            block.blockchain_synced = True
                            block.block_tx_hash = tx_hash
                            block.save(update_fields=['blockchain_synced', 'block_tx_hash'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"      Synced successfully. TX: {tx_hash}")
                        )
                        return True
                    else:
                        raise Exception("Block sync failed")
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        self.stdout.write(f"      Attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(self.retry_delay)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"      Failed after {self.max_retries} attempts: {e}")
                        )
                        logger.error(f"IP block sync failed for {block.id}: {e}")
                        return False
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"      Error syncing IP block {block.id}: {e}")
            )
            logger.error(f"IP block sync error for {block.id}: {e}")
            return False
    
    def sync_attack_signatures(self, blockchain_service, results):
        """Sync pending attack signatures to blockchain."""
        self.stdout.write("Syncing attack signatures...")
        
        try:
            # Find signatures not yet synced to blockchain
            pending_signatures = AttackPattern.objects.filter(
                Q(blockchain_synced=False) | Q(signature_tx_hash='')
            )
            
            count = pending_signatures.count()
            if count == 0:
                self.stdout.write("  No pending attack signatures found")
                return
            
            self.stdout.write(f"  Found {count} pending attack signatures")
            
            for signature in pending_signatures:
                success = self.sync_single_signature(blockchain_service, signature)
                if success:
                    results['signatures_synced'] += 1
                else:
                    results['signatures_failed'] += 1
                
                # Small delay between operations
                if not self.dry_run:
                    time.sleep(1)
                    
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  Error during signature sync: {e}")
            )
            logger.error(f"Attack signature sync error: {e}")
    
    def sync_single_signature(self, blockchain_service, signature):
        """Sync a single attack signature."""
        try:
            self.stdout.write(f"    Syncing signature: {signature.pattern_hash[:16]}...")
            
            if self.dry_run:
                self.stdout.write("      [DRY RUN] Would sync signature to blockchain")
                return True
            
            # Check if already exists on blockchain
            if blockchain_service.has_attack_signature(signature.pattern_hash):
                self.stdout.write("      Already exists on blockchain, updating local record")
                signature.blockchain_synced = True
                signature.save(update_fields=['blockchain_synced'])
                return True
            
            # Prepare pattern JSON
            import json
            pattern_json = json.dumps(signature.pattern_data)
            
            # Attempt sync with retries
            for attempt in range(self.max_retries):
                try:
                    tx_hash, success = blockchain_service.add_attack_signature(
                        pattern_json,
                        signature.severity
                    )
                    
                    if success:
                        # Update signature record
                        with transaction.atomic():
                            signature.blockchain_synced = True
                            signature.signature_tx_hash = tx_hash
                            signature.save(update_fields=['blockchain_synced', 'signature_tx_hash'])
                        
                        self.stdout.write(
                            self.style.SUCCESS(f"      Synced successfully. TX: {tx_hash}")
                        )
                        return True
                    else:
                        raise Exception("Signature sync failed")
                        
                except Exception as e:
                    if attempt < self.max_retries - 1:
                        self.stdout.write(f"      Attempt {attempt + 1} failed: {e}. Retrying...")
                        time.sleep(self.retry_delay)
                    else:
                        self.stdout.write(
                            self.style.ERROR(f"      Failed after {self.max_retries} attempts: {e}")
                        )
                        logger.error(f"Signature sync failed for {signature.id}: {e}")
                        return False
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"      Error syncing signature {signature.id}: {e}")
            )
            logger.error(f"Signature sync error for {signature.id}: {e}")
            return False
    
    def show_sync_statistics(self):
        """Show statistics about pending sync operations."""
        self.stdout.write("Blockchain Sync Statistics:")
        self.stdout.write("=" * 40)
        
        try:
            # Patient statistics
            pending_patients = Patient.objects.filter(
                Q(blockchain_registered=False) | Q(registration_tx_hash='')
            ).count()
            
            total_patients = Patient.objects.count()
            synced_patients = total_patients - pending_patients
            
            self.stdout.write(f"Patients:")
            self.stdout.write(f"  Total: {total_patients}")
            self.stdout.write(f"  Synced: {synced_patients}")
            self.stdout.write(f"  Pending: {pending_patients}")
            
            # IP block statistics
            pending_blocks = BlockedIP.objects.filter(
                Q(blockchain_synced=False) | Q(block_tx_hash='')
            ).count()
            
            total_blocks = BlockedIP.objects.count()
            synced_blocks = total_blocks - pending_blocks
            
            self.stdout.write(f"\nIP Blocks:")
            self.stdout.write(f"  Total: {total_blocks}")
            self.stdout.write(f"  Synced: {synced_blocks}")
            self.stdout.write(f"  Pending: {pending_blocks}")
            
            # Attack signature statistics
            pending_signatures = AttackPattern.objects.filter(
                Q(blockchain_synced=False) | Q(signature_tx_hash='')
            ).count()
            
            total_signatures = AttackPattern.objects.count()
            synced_signatures = total_signatures - pending_signatures
            
            self.stdout.write(f"\nAttack Signatures:")
            self.stdout.write(f"  Total: {total_signatures}")
            self.stdout.write(f"  Synced: {synced_signatures}")
            self.stdout.write(f"  Pending: {pending_signatures}")
            
            # Overall statistics
            total_pending = pending_patients + pending_blocks + pending_signatures
            self.stdout.write(f"\nOverall:")
            self.stdout.write(f"  Total pending operations: {total_pending}")
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error getting statistics: {e}")
            )
    
    def show_sync_summary(self, results):
        """Show summary of sync operations."""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write("SYNC SUMMARY:")
        
        self.stdout.write(f"Patients:")
        self.stdout.write(f"  Synced: {results['patients_synced']}")
        self.stdout.write(f"  Failed: {results['patients_failed']}")
        
        self.stdout.write(f"IP Blocks:")
        self.stdout.write(f"  Synced: {results['blocks_synced']}")
        self.stdout.write(f"  Failed: {results['blocks_failed']}")
        
        self.stdout.write(f"Attack Signatures:")
        self.stdout.write(f"  Synced: {results['signatures_synced']}")
        self.stdout.write(f"  Failed: {results['signatures_failed']}")
        
        total_synced = (results['patients_synced'] + 
                       results['blocks_synced'] + 
                       results['signatures_synced'])
        
        total_failed = (results['patients_failed'] + 
                       results['blocks_failed'] + 
                       results['signatures_failed'])
        
        self.stdout.write(f"\nTotal:")
        self.stdout.write(f"  Synced: {total_synced}")
        self.stdout.write(f"  Failed: {total_failed}")
        
        if self.dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN - No actual changes were made"))
        elif total_failed == 0:
            self.stdout.write(self.style.SUCCESS("All sync operations completed successfully"))
        elif total_synced > 0:
            self.stdout.write(self.style.WARNING("Some sync operations failed - check logs for details"))
        else:
            self.stdout.write(self.style.ERROR("All sync operations failed - check blockchain connection"))