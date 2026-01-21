#!/usr/bin/env python
"""
Script to run background tasks for the CareGrid blockchain healthcare security system.
This script can be run periodically via cron or task scheduler.
"""

import os
import sys
import subprocess
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/background_tasks.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def run_django_command(command, args=None):
    """Run a Django management command."""
    try:
        cmd = ['python', 'manage.py', command]
        if args:
            cmd.extend(args)
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"Command '{command}' completed successfully")
            if result.stdout:
                logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"Command '{command}' failed with return code {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        logger.error(f"Command '{command}' timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}")
        return False


def cleanup_expired_blocks():
    """Clean up expired IP blocks."""
    logger.info("Starting cleanup of expired IP blocks...")
    return run_django_command('cleanup_expired_blocks')


def sync_blockchain_operations():
    """Sync pending blockchain operations."""
    logger.info("Starting blockchain sync operations...")
    return run_django_command('sync_blockchain')


def sync_attack_signatures():
    """Sync attack signatures to blockchain."""
    logger.info("Starting attack signature sync...")
    return run_django_command('sync_attack_signatures')


def main():
    """Main function to run all background tasks."""
    logger.info("=" * 60)
    logger.info("Starting CareGrid background tasks")
    logger.info(f"Timestamp: {datetime.now()}")
    logger.info("=" * 60)
    
    success_count = 0
    total_tasks = 3
    
    # Task 1: Clean up expired blocks
    if cleanup_expired_blocks():
        success_count += 1
    
    # Task 2: Sync blockchain operations
    if sync_blockchain_operations():
        success_count += 1
    
    # Task 3: Sync attack signatures
    if sync_attack_signatures():
        success_count += 1
    
    # Summary
    logger.info("=" * 60)
    logger.info(f"Background tasks completed: {success_count}/{total_tasks} successful")
    
    if success_count == total_tasks:
        logger.info("All background tasks completed successfully")
        return 0
    elif success_count > 0:
        logger.warning("Some background tasks failed - check logs for details")
        return 1
    else:
        logger.error("All background tasks failed")
        return 2


if __name__ == '__main__':
    # Change to the directory containing manage.py
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_dir = os.path.dirname(script_dir)
    os.chdir(project_dir)
    
    # Run the tasks
    exit_code = main()
    sys.exit(exit_code)