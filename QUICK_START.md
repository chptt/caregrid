# 🚀 MediChain Quick Start Guide

Get MediChain running in 5 minutes!

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8+ installed
- ✅ Node.js 16+ installed  
- ✅ Git installed
- ✅ Redis server available

## 1-Minute Setup

### Step 1: Clone and Install
```bash
# Clone the repository
git clone https://github.com/yourusername/medichain.git
cd medichain

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
cd caregrid_chain && npm install && cd ..
```

### Step 2: Start Services
```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Blockchain
cd caregrid_chain && npx hardhat node

# Terminal 3: Setup Database and Start Django
python manage.py migrate
python setup_test_data.py
python manage.py runserver
```

### Step 3: Deploy Contracts (New Terminal)
```bash
cd caregrid_chain
npm run deploy
```

### Step 4: Access Dashboard
- Open `frontend/index.html` in your browser
- Or visit: `http://localhost:8000/admin` for Django admin

## 🎯 What You Get

### Immediate Access To:
- **Patient Management** - Register and search patients
- **Appointment System** - Schedule and manage appointments  
- **Security Dashboard** - Monitor threats and system health
- **Blockchain Integration** - Patient identity verification
- **API Endpoints** - Full REST API access

### Test Data Included:
- 3 Sample patients with blockchain IDs
- 5 Sample appointments
- 1 Doctor (Dr. Test - General Medicine)
- 2 Hospital branches

## 🔧 Quick Configuration

### Environment Setup
```bash
# Copy example environment file
cp .env.example .env

# Edit with your settings (optional for development)
nano .env
```

### Default Credentials
- **Django Admin**: Create with `python manage.py createsuperuser`
- **Test User**: username: `testuser`, password: `testpass123`

## 📱 Using the System

### Frontend Dashboard
1. Open `frontend/index.html`
2. Use the navigation tabs:
   - **Patients** - Register/search patients
   - **Appointments** - Create/view appointments
   - **Security** - Monitor system security
   - **Doctors** - View available doctors

### API Testing
```bash
# Test appointment listing
curl http://127.0.0.1:8000/api/appointments/list/

# Test doctor listing  
curl http://127.0.0.1:8000/api/doctors/

# Create new appointment
curl -X POST http://127.0.0.1:8000/api/appointments/ \
  -H "Content-Type: application/json" \
  -d '{"patient":1,"doctor":1,"date":"2026-01-25","time":"10:00:00","branch":2}'
```

## 🐛 Troubleshooting

### Common Issues:

**Redis Connection Error:**
```bash
# Install Redis (Windows)
# Download from: https://redis.io/download

# Install Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Install Redis (macOS)
brew install redis
```

**Port Already in Use:**
```bash
# Change Django port
python manage.py runserver 8001

# Change Hardhat port
npx hardhat node --port 8546
```

**Database Issues:**
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
python setup_test_data.py
```

## 🎉 Success Indicators

You'll know everything is working when:
- ✅ Django server starts without errors
- ✅ Frontend loads patient/appointment data
- ✅ Security dashboard shows system metrics
- ✅ Blockchain contracts are deployed
- ✅ Redis is connected (no cache errors)

## 📚 Next Steps

1. **Explore the API** - Check `API_DOCUMENTATION.md`
2. **Customize Security** - Modify threat thresholds in settings
3. **Add More Data** - Register additional patients/doctors
4. **Deploy to Production** - See `DEPLOYMENT_GUIDE.md`
5. **Run Tests** - Execute `python -m pytest`

## 🆘 Need Help?

- **Setup Issues**: Check `COMPLETE_SETUP_GUIDE.md`
- **API Questions**: See `API_DOCUMENTATION.md`  
- **Security Config**: Read `SECURITY_DASHBOARD_API.md`
- **Docker Deployment**: Follow `DOCKER_README.md`

---

**Happy coding with MediChain!** 🏥⛓️