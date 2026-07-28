#!/usr/bin/env python3
"""
Script to verify that all dependencies are installed correctly
"""

import sys
import importlib

def check_module(module_name, package_name=None):
    """Check if a Python module is installed"""
    try:
        importlib.import_module(module_name)
        print(f"✓ {package_name or module_name} is installed")
        return True
    except ImportError:
        print(f"✗ {package_name or module_name} is NOT installed")
        return False

def main():
    print("=== Verifying MediChain Dependencies ===\n")
    
    all_ok = True
    
    # Check Python version
    print("Python Version:")
    print(f"  {sys.version}")
    if sys.version_info < (3, 11):
        print("  ⚠ Warning: Python 3.11+ is recommended")
    print()
    
    # Check Django and related packages
    print("Django Packages:")
    all_ok &= check_module("django", "Django")
    all_ok &= check_module("rest_framework", "Django REST Framework")
    all_ok &= check_module("corsheaders", "django-cors-headers")
    print()
    
    # Check blockchain packages
    print("Blockchain Packages:")
    all_ok &= check_module("web3", "Web3.py")
    all_ok &= check_module("eth_tester", "eth-tester")
    print()
    
    # Check Redis packages
    print("Redis Packages:")
    all_ok &= check_module("redis", "redis")
    all_ok &= check_module("django_redis", "django-redis")
    all_ok &= check_module("fakeredis", "fakeredis")
    print()
    
    # Check testing packages
    print("Testing Packages:")
    all_ok &= check_module("pytest", "pytest")
    all_ok &= check_module("pytest_django", "pytest-django")
    all_ok &= check_module("pytest_cov", "pytest-cov")
    all_ok &= check_module("hypothesis", "hypothesis")
    print()
    
    # Check utilities
    print("Utilities:")
    all_ok &= check_module("dotenv", "python-dotenv")
    print()
    
    # Check Redis connection
    print("Redis Connection:")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0)
        r.ping()
        print("✓ Redis is running and accessible")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        print("  Make sure Redis is running: redis-server")
        all_ok = False
    print()
    
    # Summary
    print("=" * 50)
    if all_ok:
        print("✓ All dependencies are installed and configured!")
        print("\nNext steps:")
        print("1. Start blockchain: ./scripts/start-blockchain.sh")
        print("2. Deploy contracts: cd caregrid_chain && npm run deploy")
        print("3. Update settings: python scripts/update_contract_addresses.py")
        print("4. Run migrations: python manage.py migrate")
        print("5. Start server: python manage.py runserver")
    else:
        print("✗ Some dependencies are missing or not configured")
        print("\nPlease run: pip install -r requirements.txt")
        print("And ensure Redis is installed and running")
        sys.exit(1)

if __name__ == "__main__":
    main()
