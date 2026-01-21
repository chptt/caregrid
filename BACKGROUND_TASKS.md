# CareGrid Background Tasks

This document describes the background tasks implemented for the CareGrid blockchain healthcare security system.

## Overview

The system includes two main background tasks that handle maintenance and synchronization operations:

1. **Cleanup Task** - Removes expired IP blocks from blockchain and local database
2. **Blockchain Sync Task** - Syncs pending operations and retries failed transactions

## Task 1: Cleanup Expired Blocks

**Command:** `python manage.py cleanup_expired_blocks`

**Purpose:** Removes expired IP blocks from both the blockchain and local database to maintain system performance and accuracy.

### Features

- Calls blockchain `cleanupExpiredBlocks()` function
- Removes expired records from local `BlockedIP` model
- Supports dry-run mode for testing
- Can operate in local-only mode if blockchain is unavailable
- Provides detailed statistics and logging

### Usage Examples

```bash
# Basic cleanup (blockchain + local database)
python manage.py cleanup_expired_blocks

# Dry run to see what would be cleaned
python manage.py cleanup_expired_blocks --dry-run

# Local database only (skip blockchain)
python manage.py cleanup_expired_blocks --local-only

# Force cleanup even if blockchain is down
python manage.py cleanup_expired_blocks --force
```

### Requirements Addressed

- **Requirement 11.3:** Automatic removal of expired IP blocks

## Task 2: Blockchain Sync

**Command:** `python manage.py sync_blockchain`

**Purpose:** Syncs pending blockchain operations and retries failed transactions to ensure data consistency across the system.

### Features

- Syncs patient registrations to blockchain
- Syncs IP blocks to blockchain
- Syncs attack signatures to blockchain
- Configurable retry logic with exponential backoff
- Supports selective sync (patients-only, blocks-only, etc.)
- Comprehensive statistics and reporting

### Usage Examples

```bash
# Sync all pending operations
python manage.py sync_blockchain

# Dry run to see what would be synced
python manage.py sync_blockchain --dry-run

# Show statistics without syncing
python manage.py sync_blockchain --stats

# Sync only patient registrations
python manage.py sync_blockchain --patients-only

# Sync with custom retry settings
python manage.py sync_blockchain --max-retries 5 --retry-delay 10
```

### Requirements Addressed

- **Requirement 9.3:** Transaction confirmation and error handling
- **Requirement 12.5:** Offline queue and sync capabilities

## Scheduling Background Tasks

### Using Cron (Linux/macOS)

Add entries to your crontab (`crontab -e`):

```bash
# Cleanup expired blocks every hour
0 * * * * cd /path/to/caregrid && python manage.py cleanup_expired_blocks

# Sync blockchain operations every 15 minutes
*/15 * * * * cd /path/to/caregrid && python manage.py sync_blockchain

# Run comprehensive background tasks hourly
0 * * * * cd /path/to/caregrid && python scripts/run_background_tasks.py
```

### Using Windows Task Scheduler

Create scheduled tasks with these PowerShell commands:

```powershell
# Hourly cleanup
powershell.exe -Command "cd C:\caregrid; python manage.py cleanup_expired_blocks"

# 15-minute sync
powershell.exe -Command "cd C:\caregrid; python manage.py sync_blockchain"
```

### Using the Combined Script

The `scripts/run_background_tasks.py` script runs all background tasks in sequence:

```bash
python scripts/run_background_tasks.py
```

This script:
- Runs cleanup of expired blocks
- Runs blockchain sync operations
- Runs attack signature sync
- Provides comprehensive logging
- Returns appropriate exit codes for monitoring

## Monitoring and Logging

### Log Files

Background tasks write to several log files:

- `logs/caregrid.log` - General application logs
- `logs/background_tasks.log` - Combined background task logs (when using the script)
- Individual command output can be redirected to specific log files

### Exit Codes

Commands return standard exit codes:
- `0` - Success
- `1` - Partial failure (some operations failed)
- `2` - Complete failure

### Health Monitoring

Use the `--stats` flag to monitor system health:

```bash
# Check sync status
python manage.py sync_blockchain --stats

# Check what needs cleanup
python manage.py cleanup_expired_blocks --dry-run
```

## Error Handling

### Blockchain Connection Issues

- Tasks gracefully handle blockchain disconnections
- Cleanup task can operate in local-only mode
- Sync task will retry operations when connection is restored
- Comprehensive error logging for troubleshooting

### Transaction Failures

- Configurable retry logic with exponential backoff
- Failed operations remain in pending state for future retry
- Detailed error logging for each failure
- Statistics show success/failure rates

### Database Issues

- Atomic transactions prevent partial updates
- Proper error handling and rollback
- Detailed logging of database operations

## Performance Considerations

### Timing Recommendations

- **Cleanup Task:** Run hourly during low-traffic periods
- **Sync Task:** Run every 15-30 minutes for near real-time sync
- **Combined Script:** Run hourly for comprehensive maintenance

### Resource Usage

- Tasks include delays between operations to avoid overwhelming the blockchain
- Configurable retry delays to manage network load
- Efficient database queries with proper indexing

### Scalability

- Tasks can be run on multiple servers (they handle concurrency safely)
- Redis caching reduces blockchain query load
- Atomic operations prevent race conditions

## Troubleshooting

### Common Issues

1. **Blockchain Connection Failed**
   - Check if Hardhat network is running
   - Verify network configuration in settings
   - Use `--force` flag for cleanup if needed

2. **Transaction Timeouts**
   - Increase `BLOCKCHAIN_CONFIRMATION_TIMEOUT` in settings
   - Check network congestion
   - Use `--retry-delay` to space out operations

3. **Database Lock Errors**
   - Ensure only one instance of each task runs at a time
   - Check for long-running queries
   - Use proper scheduling intervals

### Debug Mode

Run tasks with increased verbosity:

```bash
python manage.py cleanup_expired_blocks -v 2
python manage.py sync_blockchain -v 3
```

### Manual Recovery

If tasks fail repeatedly:

1. Check blockchain connection: `python manage.py shell -c "from core.blockchain_service import get_blockchain_service; print(get_blockchain_service().health_check())"`
2. Clear caches: `python manage.py shell -c "from core.blockchain_service import get_blockchain_service; get_blockchain_service().clear_all_caches()"`
3. Run with dry-run first to identify issues
4. Use selective sync flags to isolate problems

## Security Considerations

- Tasks run with the same permissions as the Django application
- Blockchain operations use the configured account from Hardhat
- Sensitive data is properly hashed before blockchain storage
- Comprehensive audit logging for all operations

## Future Enhancements

Potential improvements for production deployment:

1. **Celery Integration** - Use Celery for distributed task processing
2. **Monitoring Dashboard** - Web interface for task status and statistics
3. **Alert System** - Notifications for task failures or blockchain issues
4. **Performance Metrics** - Detailed timing and throughput statistics
5. **Auto-scaling** - Dynamic task frequency based on system load