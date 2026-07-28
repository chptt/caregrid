#!/usr/bin/env python3
"""
MediChain Startup Script
Automated startup for the complete MediChain system
"""
import os
import sys
import subprocess
import time
import requests
import json
from pathlib import Path

def print_banner():
    """Print MediChain startup banner"""
    print("=" * 60)
    print("🏥 MediChain - Blockchain Healthcare Security System")
    print("=" * 60)
    print()

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    try:
        python_version = sys.version_info
        if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 8):
            print("❌ Python 3.8+ required")
            return False
        print(f"✅ Python {python_version.major}.{python_version.minor}")
    except Exception as e:
        print(f"❌ Python check failed: {e}")
        return False
    
    # Check Node.js
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js {result.stdout.strip()}")
        else:
            print("❌ Node.js not found")
            return False
    except FileNotFoundError:
        print("❌ Node.js not installed")
        return False
    
    # Check Redis
    try:
        result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True)
        if result.returncode == 0 and 'PONG' in result.stdout:
            print("✅ Redis server running")
        else:
            print("⚠️  Redis server not running - please start it manually")
            print("   Windows: redis-server")
            print("   Linux/Mac: sudo systemctl start redis")
    except FileNotFoundError:
        print("⚠️  Redis not installed - please install it")
        print("   Windows: Download from https://redis.io/download")
        print("   Ubuntu: sudo apt-get install redis-server")
        print("   macOS: brew install redis")
    
    return True

def setup_database():
    """Setup Django database"""
    print("\n📊 Setting up database...")
    
    try:
        # Run migrations
        result = subprocess.run(['python', 'manage.py', 'migrate'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database migrations completed")
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
        
        # Setup test data
        if Path('setup_test_data.py').exists():
            result = subprocess.run(['python', 'setup_test_data.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Test data loaded")
            else:
                print(f"⚠️  Test data setup failed: {result.stderr}")
        
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        return False

def install_dependencies():
    """Install Python and Node.js dependencies"""
    print("\n📦 Installing dependencies...")
    
    # Install Python dependencies
    try:
        result = subprocess.run(['pip', 'install', '-r', 'requirements.txt'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Python dependencies installed")
        else:
            print(f"❌ Python dependencies failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Python dependencies error: {e}")
        return False
    
    # Install Node.js dependencies
    try:
        os.chdir('caregrid_chain')
        result = subprocess.run(['npm', 'install'], capture_output=True, text=True)
        os.chdir('..')
        
        if result.returncode == 0:
            print("✅ Node.js dependencies installed")
        else:
            print(f"❌ Node.js dependencies failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Node.js dependencies error: {e}")
        return False
    
    return True

def start_blockchain():
    """Start the blockchain network"""
    print("\n⛓️  Starting blockchain network...")
    
    try:
        # Start Hardhat node in background
        os.chdir('caregrid_chain')
        process = subprocess.Popen(['npx', 'hardhat', 'node'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        os.chdir('..')
        
        # Wait for blockchain to start
        time.sleep(5)
        
        if process.poll() is None:
            print("✅ Blockchain network started")
            return process
        else:
            print("❌ Blockchain failed to start")
            return None
    except Exception as e:
        print(f"❌ Blockchain startup error: {e}")
        return None

def deploy_contracts():
    """Deploy smart contracts"""
    print("\n📜 Deploying smart contracts...")
    
    try:
        os.chdir('caregrid_chain')
        result = subprocess.run(['npm', 'run', 'deploy'], 
                              capture_output=True, text=True)
        os.chdir('..')
        
        if result.returncode == 0:
            print("✅ Smart contracts deployed")
            return True
        else:
            print(f"❌ Contract deployment failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Contract deployment error: {e}")
        return False

def start_django():
    """Start Django development server"""
    print("\n🌐 Starting Django server...")
    
    try:
        process = subprocess.Popen(['python', 'manage.py', 'runserver'], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE)
        
        # Wait for Django to start
        time.sleep(3)
        
        # Test if Django is running
        try:
            response = requests.get('http://127.0.0.1:8000/api/appointments/list/', timeout=5)
            if response.status_code in [200, 403]:  # 403 is expected due to security middleware
                print("✅ Django server started")
                return process
        except:
            pass
        
        if process.poll() is None:
            print("✅ Django server started (waiting for full initialization)")
            return process
        else:
            print("❌ Django failed to start")
            return None
    except Exception as e:
        print(f"❌ Django startup error: {e}")
        return None

def test_system():
    """Test if the system is working"""
    print("\n🧪 Testing system...")
    
    try:
        # Test API endpoints
        response = requests.get('http://127.0.0.1:8000/api/doctors/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API working - {len(data.get('doctors', []))} doctors found")
        else:
            print(f"⚠️  API test returned status {response.status_code}")
        
        # Test appointments
        response = requests.get('http://127.0.0.1:8000/api/appointments/list/', timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Appointments working - {data.get('count', 0)} appointments found")
        else:
            print(f"⚠️  Appointments test returned status {response.status_code}")
        
        return True
    except Exception as e:
        print(f"⚠️  System test failed: {e}")
        return False

def main():
    """Main startup function"""
    print_banner()
    
    # Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing components.")
        return False
    
    # Install dependencies
    if not install_dependencies():
        print("\n❌ Dependency installation failed.")
        return False
    
    # Setup database
    if not setup_database():
        print("\n❌ Database setup failed.")
        return False
    
    # Start blockchain
    blockchain_process = start_blockchain()
    if not blockchain_process:
        print("\n❌ Blockchain startup failed.")
        return False
    
    # Deploy contracts
    if not deploy_contracts():
        print("\n❌ Contract deployment failed.")
        blockchain_process.terminate()
        return False
    
    # Start Django
    django_process = start_django()
    if not django_process:
        print("\n❌ Django startup failed.")
        blockchain_process.terminate()
        return False
    
    # Test system
    test_system()
    
    # Success message
    print("\n" + "=" * 60)
    print("🎉 MediChain is now running!")
    print("=" * 60)
    print("📱 Frontend Dashboard: Open frontend/index.html in your browser")
    print("🌐 Django Admin: http://127.0.0.1:8000/admin")
    print("📊 API Docs: Check API_DOCUMENTATION.md")
    print("🔒 Security Dashboard: http://127.0.0.1:8000/firewall/dashboard")
    print("=" * 60)
    print("\nPress Ctrl+C to stop all services")
    
    try:
        # Keep processes running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if blockchain_process.poll() is not None:
                print("⚠️  Blockchain process stopped")
                break
            if django_process.poll() is not None:
                print("⚠️  Django process stopped")
                break
                
    except KeyboardInterrupt:
        print("\n\n🛑 Shutting down MediChain...")
        blockchain_process.terminate()
        django_process.terminate()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()