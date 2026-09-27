import logging

logger = logging.getLogger('ai')


class AISummaryBlockchainService:
    """Interface for hashing AI summaries for blockchain audit trail.

    This service prepares hashes for future on-chain storage.
    Smart contracts are NOT modified by this service.
    """

    @staticmethod
    def hash_summary(content: str) -> str:
        """Generate a SHA-256 hash for AI summary content."""
        import hashlib
        return '0x' + hashlib.sha256(content.encode()).hexdigest()

    @staticmethod
    def store_hash(summary_id: str, content_hash: str) -> dict:
        """Prepare hash for blockchain storage (placeholder - not on-chain)."""
        logger.info("Blockchain hash prepared: entity=%s hash=%s", summary_id, content_hash)
        return {
            'status': 'hash_prepared',
            'entity_id': summary_id,
            'hash': content_hash,
            'message': 'Hash prepared for future blockchain storage. Smart contracts not modified.',
        }

    @staticmethod
    def verify_hash(summary_id: str, content: str, onchain_hash: str) -> bool:
        """Verify content integrity against a stored hash."""
        computed = AISummaryBlockchainService.hash_summary(content)
        return computed == onchain_hash

    @staticmethod
    def get_audit_entry_hash(audit_entry) -> str:
        """Generate a blockchain-ready hash from an audit trail entry."""
        import hashlib
        data = f"{audit_entry.id}{audit_entry.action_type}{audit_entry.created_at.isoformat()}{audit_entry.output_summary}"
        return '0x' + hashlib.sha256(data.encode()).hexdigest()
