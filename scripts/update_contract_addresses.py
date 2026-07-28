#!/usr/bin/env python3
"""
Script to update Django settings with deployed contract addresses
"""

import json
import os
import sys
from pathlib import Path

def update_contract_addresses():
    """Read deployed contract addresses and update Django settings"""
    
    # Get project root directory
    project_root = Path(__file__).parent.parent
    
    # Path to deployment file
    deployment_file = project_root / "caregrid_chain" / "deployments" / "all-contracts.json"
    
    if not deployment_file.exists():
        print(f"Error: Deployment file not found at {deployment_file}")
        print("Please deploy contracts first using: npm run deploy")
        sys.exit(1)
    
    # Read deployment data
    with open(deployment_file, 'r') as f:
        deployments = json.load(f)
    
    print("=== Deployed Contract Addresses ===")
    print(f"PatientRegistry: {deployments['PatientRegistry']}")
    print(f"BlockedIPRegistry: {deployments['BlockedIPRegistry']}")
    print(f"AttackSignatureRegistry: {deployments['AttackSignatureRegistry']}")
    print(f"Network: {deployments['network']}")
    print(f"Deployed at: {deployments['timestamp']}")
    
    # Path to settings file
    settings_file = project_root / "caregrid" / "settings.py"
    
    # Read current settings
    with open(settings_file, 'r') as f:
        settings_content = f.read()
    
    # Update CONTRACT_ADDRESSES section
    new_addresses = f"""CONTRACT_ADDRESSES = {{
    'PatientRegistry': '{deployments['PatientRegistry']}',
    'BlockedIPRegistry': '{deployments['BlockedIPRegistry']}',
    'AttackSignatureRegistry': '{deployments['AttackSignatureRegistry']}',
}}"""
    
    # Replace the CONTRACT_ADDRESSES section
    import re
    pattern = r"CONTRACT_ADDRESSES = \{[^}]*\}"
    if re.search(pattern, settings_content):
        settings_content = re.sub(pattern, new_addresses, settings_content)
        
        # Write updated settings
        with open(settings_file, 'w') as f:
            f.write(settings_content)
        
        print("\n✓ Django settings updated successfully!")
        print(f"✓ Settings file: {settings_file}")
    else:
        print("\nWarning: Could not find CONTRACT_ADDRESSES in settings.py")
        print("Please manually add the following to your settings.py:")
        print(new_addresses)

if __name__ == "__main__":
    update_contract_addresses()
