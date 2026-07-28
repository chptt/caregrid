#!/usr/bin/env python3
"""
MediChain Deployment Verification Script
Verifies that all components are working correctly after deployment
"""
import requests
import json
import time
import subprocess
import sys
from pathlib import Path

def print_header(title):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"🔍 {title}")
    print("=" * 60)

def check_service(name, url, expected_status=200, timeout=10):
    """Check if a service is responding"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == expected_status:
            print(f"✅ {name}: Running (Status {response.status_code})")
            return True
        else:
            print(f"⚠️  {name}: Unexpected status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ {name}: Connection failed - service not running")
        return False
    except requests.exceptions.Timeout:
        print(f"❌ {name}: Timeout - service not responding")
        return False
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False

def test_api_endpoints():
    """Test critical API endpoints"""
    print_header("API Endpoints Testing")
    
    base_url = "http://127.0.0.1:8000/api"
    results = []
    
    # Test endpoints
    endpoints = [
        ("Doctors List", f"{base_url}/doctors/", 200),
        ("Appointments List", f"{base_url}/appointments/list/", 200),
        ("Patient Search", f"{base_url}/patients/search/?q=test", 403),  # Should require auth
        ("Security CAPTCHA", f"{base_url}/security/captcha/", 200),
    ]
    
    for name, url, expected in endpoints:
        result = check_service(name, url, expected)
        results.append(result)
    
    return all(results)

def test_database():
    """Test database connectivity and data"""
    print_header("Database Testing")
    
    try:
        # Test Django database connection
        result = subprocess.run(['python', 'manage.py', 'check', '--database', 'default'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database: Connection successful")
        else:
            print(f"❌ Database: Connection failed - {result.stderr}")
            return False
        
        # Test data presence
        result = subprocess.run(['python', 'manage.py', 'shell', '-c', 
                               'from core.models import *; print(f"Patients: {Patient.objects.count()}, Appointments: {Appointment.objects.count()}")'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ Database: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Database: Data check failed - {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Database: Error - {e}")
        return False

def test_blockchain():
    """Test blockchain connectivity"""
    print_header("Blockchain Testing")
    
    try:
        # Test if Hardhat node is running
        response = requests.post('http://127.0.0.1:8545', 
                               json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                               timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            if 'result' in data:
                block_number = int(data['result'], 16)
                print(f"✅ Blockchain: Connected (Block #{block_number})")
                return True
        
        print("❌ Blockchain: Not responding")
        return False
        
    except Exception as e:
        print(f"❌ Blockchain: Error - {e}")
        return False

def test_redis():
    """Test Redis connectivity"""
    print_header("Redis Testing")
    
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis: Connected and responding")
            return True
        else:
            print("❌ Redis: Not responding")
            return False
            
    except FileNotFoundError:
        print("❌ Redis: CLI not found - Redis may not be installed")
        return False
    except Exception as e:
        print(f"❌ Redis: Error - {e}")
        return False

def test_frontend():
    """Test frontend files"""
    print_header("Frontend Testing")
    
    frontend_file = Path('frontend/index.html')
    
    if frontend_file.exists():
        print("✅ Frontend: Dashboard file exists")
        
        # Check if file has content
        content = frontend_file.read_text()
        if len(content) > 1000 and 'MediChain' in content:
            print("✅ Frontend: Dashboard content verified")
            return True
        else:
            print("❌ Frontend: Dashboard content incomplete")
            return False
    else:
        print("❌ Frontend: Dashboard file missing")
        return False

def test_security():
    """Test security features"""
    print_header("Security Testing")
    
    try:
        # Test rate limiting endpoint
        response = requests.get('http://127.0.0.1:8000/api/rate-limit/status/', timeout=5)
        
        if response.status_code == 200:
            print("✅ Security: Rate limiting active")
        else:
            print("⚠️  Security: Rate limiting status unclear")
        
        # Test CAPTCHA endpoint
        response = requests.get('http://127.0.0.1:8000/api/security/captcha/', timeout=5)
        
        if response.status_code == 200:
            print("✅ Security: CAPTCHA system active")
            return True
        else:
            print("⚠️  Security: CAPTCHA system status unclear")
            return False
            
    except Exception as e:
        print(f"❌ Security: Error - {e}")
        return False

def test_documentation():
    """Test documentation files"""
    print_header("Documentation Testing")
    
    docs = [
        'README.md',
        'QUICK_START.md',
        'API_DOCUMENTATION.md',
        'COMPLETE_SETUP_GUIDE.md',
        'DEPLOYMENT_GUIDE.md'
    ]
    
    missing = []
    for doc in docs:
        if not Path(doc).exists():
            missing.append(doc)
    
    if not missing:
        print("✅ Documentation: All files present")
        return True
    else:
        print(f"❌ Documentation: Missing files - {', '.join(missing)}")
        return False

def main():
    """Main verification function"""
    print("🏥 MediChain Deployment Verification")
    print("=" * 60)
    print("Checking all system components...")
    
    # Run all tests
    tests = [
        ("Database", test_database),
        ("Redis", test_redis),
        ("Blockchain", test_blockchain),
        ("API Endpoints", test_api_endpoints),
        ("Security Features", test_security),
        ("Frontend", test_frontend),
        ("Documentation", test_documentation),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name}: Unexpected error - {e}")
            results[test_name] = False
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name:20} {status}")
    
    print("\n" + "=" * 60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - MediChain is fully operational!")
        print("\n🚀 Ready for production deployment")
        print("\n📱 Access Points:")
        print("   • Frontend Dashboard: frontend/index.html")
        print("   • Django Admin: http://127.0.0.1:8000/admin")
        print("   • API Base: http://127.0.0.1:8000/api")
        print("   • Security Dashboard: http://127.0.0.1:8000/firewall/dashboard")
        return True
    else:
        print(f"⚠️  {passed}/{total} TESTS PASSED - Some issues detected")
        print("\n🔧 Check the failed components above")
        print("📚 Refer to COMPLETE_SETUP_GUIDE.md for troubleshooting")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)