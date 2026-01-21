# MediChain - Blockchain Healthcare Security System

A comprehensive healthcare management system with blockchain integration, advanced security features, and real-time threat monitoring.

## 🏥 Features

### Hospital Management
- **Patient Registration** with blockchain ID generation
- **Appointment Management** with doctor scheduling
- **Patient Search** by name, email, or blockchain ID
- **Doctor Management** with specialization tracking
- **Branch-based Access Control**

### Security & Blockchain
- **Blockchain Integration** for patient identity verification
- **Real-time Threat Monitoring** with adaptive security
- **IP-based Access Control** with automatic blocking
- **CAPTCHA Protection** for medium/high threat levels
- **Rate Limiting** to prevent abuse
- **Attack Signature Detection**

### Frontend Dashboard
- **Interactive Web Interface** for all operations
- **Real-time Security Monitoring**
- **Patient and Appointment Management**
- **System Status and Analytics**

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Redis Server
- Git

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/medichain.git
   cd medichain
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies:**
   ```bash
   cd caregrid_chain
   npm install
   cd ..
   ```

4. **Start Redis server:**
   ```bash
   # On Windows (if installed via installer)
   redis-server
   
   # On Linux/Mac
   sudo systemctl start redis
   # or
   redis-server
   ```

5. **Setup the database:**
   ```bash
   python manage.py migrate
   python setup_test_data.py
   ```

6. **Start the blockchain network:**
   ```bash
   cd caregrid_chain
   npx hardhat node
   ```

7. **Deploy smart contracts (in new terminal):**
   ```bash
   cd caregrid_chain
   npm run deploy
   ```

8. **Start the Django server:**
   ```bash
   python manage.py runserver
   ```

9. **Access the frontend:**
   - Open `frontend/index.html` in your browser
   - Or serve it: `cd frontend && python -m http.server 8080`

## 📖 Documentation

- **[Complete Setup Guide](COMPLETE_SETUP_GUIDE.md)** - Detailed installation instructions
- **[API Documentation](API_DOCUMENTATION.md)** - REST API endpoints
- **[Security Dashboard API](SECURITY_DASHBOARD_API.md)** - Security monitoring endpoints
- **[Deployment Guide](DEPLOYMENT_GUIDE.md)** - Production deployment
- **[Docker Setup](DOCKER_README.md)** - Containerized deployment

## 🏗️ Architecture

```
MediChain/
├── core/                   # Main Django app
│   ├── models.py          # Patient, Appointment, Doctor models
│   ├── views.py           # API endpoints
│   ├── middleware.py      # Security middleware
│   └── blockchain_service.py
├── users/                 # User management
├── firewall/              # Security monitoring
├── caregrid_chain/        # Blockchain contracts
│   ├── contracts/         # Solidity smart contracts
│   └── scripts/           # Deployment scripts
├── frontend/              # Web dashboard
└── tests/                 # Comprehensive test suite
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file:
```env
DEBUG=True
SECRET_KEY=your-secret-key
REDIS_HOST=localhost
REDIS_PORT=6379
BLOCKCHAIN_PROVIDER_URL=http://127.0.0.1:8545
```

### Security Settings
Configure in `caregrid/settings.py`:
- Threat score thresholds
- Rate limiting rules
- CAPTCHA settings
- Auto-block durations

## 🧪 Testing

Run the comprehensive test suite:
```bash
# Unit tests
python -m pytest tests/unit/

# Property-based tests
python -m pytest tests/property/

# Integration tests
python -m pytest tests/integration/

# All tests
python -m pytest
```

## 📊 API Endpoints

### Patient Management
- `POST /api/patients/` - Register new patient
- `GET /api/patients/search/?q=query` - Search patients
- `GET /api/patients/{id}/` - Get patient details

### Appointment Management
- `POST /api/appointments/` - Create appointment
- `GET /api/appointments/list/` - List appointments
- `GET /api/appointments/{id}/` - Get appointment details
- `GET /api/appointments/patient/{id}/` - Patient appointments

### Security
- `GET /api/security/captcha/` - Get CAPTCHA challenge
- `POST /api/security/captcha/` - Verify CAPTCHA
- `GET /firewall/dashboard/` - Security dashboard data

## 🔒 Security Features

### Threat Detection
- **IP-based monitoring** with automatic scoring
- **Rate limiting** per endpoint
- **CAPTCHA challenges** for suspicious activity
- **Automatic IP blocking** for high threats

### Blockchain Security
- **Patient identity verification** via blockchain IDs
- **Immutable audit trails** for critical operations
- **Smart contract validation** for data integrity

### Access Control
- **Role-based permissions** (Admin, Doctor, Nurse, Receptionist)
- **Branch-based access** restrictions
- **Authentication required** for sensitive operations

## 🐳 Docker Deployment

Use Docker for easy deployment:
```bash
# Build and start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📈 Monitoring

### System Health
- Real-time threat monitoring
- Performance metrics
- Error tracking and logging
- Blockchain synchronization status

### Security Dashboard
Access the security dashboard at `/firewall/dashboard/` for:
- Active threats and blocked IPs
- Attack signature detection
- System security metrics
- Real-time monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Report bugs and request features via GitHub Issues
- **Documentation**: Check the `/docs` folder for detailed guides
- **Setup Help**: See `COMPLETE_SETUP_GUIDE.md` for troubleshooting

## 🏆 Features Highlights

- ✅ **Production Ready** - Comprehensive error handling and logging
- ✅ **Scalable Architecture** - Microservices with Docker support
- ✅ **Security First** - Advanced threat detection and prevention
- ✅ **Blockchain Integration** - Ethereum-compatible smart contracts
- ✅ **Real-time Monitoring** - Live security and system metrics
- ✅ **Comprehensive Testing** - Unit, integration, and property-based tests
- ✅ **API Documentation** - Complete REST API with examples
- ✅ **Frontend Dashboard** - Interactive web interface

---

**MediChain** - Securing Healthcare Data with Blockchain Technology 🏥⛓️