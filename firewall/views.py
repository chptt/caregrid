from web3 import Web3
import json
import os
from django.http import JsonResponse


# Connect to local Hardhat node
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Load ABI from JSON file
abi_path = os.path.join(os.path.dirname(__file__), 'abi/AccessControl.json')
with open(abi_path) as f:
    contract_json = json.load(f)
    abi = contract_json['abi']

# Contract address from deployment
contract_address = "0x5FbDB2315678afecb367f032d93F642f64180aa3"

# Create contract instance
access_control = w3.eth.contract(address=contract_address, abi=abi)

def block_ip_auto(ip):
    tx_hash = access_control.functions.addSuspiciousIP(ip).transact({'from': w3.eth.accounts[0]})
    w3.eth.wait_for_transaction_receipt(tx_hash)

def block_ip(request):
    ip = request.GET.get("ip")
    if not ip:
        return JsonResponse({"error": "Missing IP"}, status=400)

    tx_hash = access_control.functions.addSuspiciousIP(ip).transact({'from': w3.eth.accounts[0]})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return JsonResponse({"status": "blocked", "ip": ip})

def is_blocked(request):
    ip = request.GET.get("ip")
    blocked = access_control.functions.isBlocked(ip).call()
    return JsonResponse({"ip": ip, "blocked": blocked})

def unblock_ip(request):
    ip = request.GET.get("ip")
    tx_hash = access_control.functions.unblockIP(ip).transact({'from': w3.eth.accounts[0]})
    w3.eth.wait_for_transaction_receipt(tx_hash)
    return JsonResponse({"status": "unblocked", "ip": ip})