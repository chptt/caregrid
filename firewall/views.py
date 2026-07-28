"""
Firewall legacy views for IP management.

These endpoints provide basic IP block/unblock/check functionality.
They use lazy initialization to avoid crashing when the blockchain node is unavailable.
"""

import json
import logging
import os

from django.http import JsonResponse
from django.conf import settings

logger = logging.getLogger('blockchain')

_web3 = None
_access_control = None


def _get_web3():
    """Lazy-initialize Web3 connection."""
    global _web3
    if _web3 is None:
        from web3 import Web3
        _web3 = Web3(Web3.HTTPProvider(settings.BLOCKCHAIN_PROVIDER_URL))
    return _web3


def _get_access_control():
    """Lazy-load the AccessControl contract."""
    global _access_control
    if _access_control is not None:
        return _access_control

    try:
        from web3 import Web3
        w3 = _get_web3()

        abi_path = os.path.join(os.path.dirname(__file__), 'abi', 'AccessControl.json')
        with open(abi_path) as f:
            abi = json.load(f)['abi']

        deployment_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'caregrid_chain', 'deployments', 'all-contracts.json'
        )
        if os.path.exists(deployment_path):
            with open(deployment_path) as f:
                deployment = json.load(f)
            contract_address = deployment.get('AccessControl', settings.CONTRACT_ADDRESSES.get('PatientRegistry', ''))
        else:
            contract_address = settings.CONTRACT_ADDRESSES.get('PatientRegistry', '')

        if not contract_address:
            logger.warning("AccessControl contract address not configured")
            return None

        _access_control = w3.eth.contract(
            address=contract_address,
            abi=abi,
        )
        return _access_control
    except Exception as e:
        logger.error(f"Failed to load AccessControl contract: {e}")
        return None


def block_ip_auto(ip):
    """Block an IP address automatically via blockchain."""
    contract = _get_access_control()
    if contract is None:
        logger.warning(f"Cannot block IP {ip}: blockchain not available")
        return None

    w3 = _get_web3()
    tx_hash = contract.functions.addSuspiciousIP(ip).transact({'from': w3.eth.accounts[0]})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash


def block_ip(request):
    """Block an IP address via blockchain (admin endpoint)."""
    ip = request.GET.get('ip')
    if not ip:
        return JsonResponse({'error': 'Missing IP'}, status=400)

    contract = _get_access_control()
    if contract is None:
        return JsonResponse({'error': 'Blockchain not available'}, status=503)

    try:
        w3 = _get_web3()
        tx_hash = contract.functions.addSuspiciousIP(ip).transact({'from': w3.eth.accounts[0]})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return JsonResponse({'status': 'blocked', 'ip': ip})
    except Exception as e:
        logger.error(f"Failed to block IP {ip}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def is_blocked(request):
    """Check if an IP address is blocked on the blockchain."""
    ip = request.GET.get('ip')
    contract = _get_access_control()
    if contract is None:
        return JsonResponse({'error': 'Blockchain not available'}, status=503)

    try:
        blocked = contract.functions.isBlocked(ip).call()
        return JsonResponse({'ip': ip, 'blocked': blocked})
    except Exception as e:
        logger.error(f"Failed to check IP {ip}: {e}")
        return JsonResponse({'error': str(e)}, status=500)


def unblock_ip(request):
    """Unblock an IP address via blockchain."""
    ip = request.GET.get('ip')
    if not ip:
        return JsonResponse({'error': 'Missing IP'}, status=400)

    contract = _get_access_control()
    if contract is None:
        return JsonResponse({'error': 'Blockchain not available'}, status=503)

    try:
        w3 = _get_web3()
        tx_hash = contract.functions.unblockIP(ip).transact({'from': w3.eth.accounts[0]})
        w3.eth.wait_for_transaction_receipt(tx_hash)
        return JsonResponse({'status': 'unblocked', 'ip': ip})
    except Exception as e:
        logger.error(f"Failed to unblock IP {ip}: {e}")
        return JsonResponse({'error': str(e)}, status=500)
