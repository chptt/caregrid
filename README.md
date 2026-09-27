# CareGrid X

**Enterprise AI-Native Healthcare Platform**

CareGrid X is a production-ready healthcare platform that integrates AI-powered clinical decision support, medical document processing, blockchain-based audit trails, and enterprise-grade security.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            CareGrid X Platform                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                              React Frontend                                  │
│                         (Bootstrap 5 / Django Templates)                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                            Django REST API                                    │
│                    (Authentication, Rate Limiting, Captcha)                   │
├───────────────────────┬─────────────────────────┬────────────────────────────┤
│      AI Module        │   Core Services         │   Blockchain Interface     │
│                       │                         │                            │
│  ┌─────────────────┐  │  ┌───────────────────┐  │  ┌────────────────────┐   │
│  │ Doctor Agent     │  │  │ Patients          │  │  │ Web3.py            │   │
│  │ Medical Records  │  │  │ Appointments      │  │  │ SHA-256 Hashing    │   │
│  │ Agent            │  │  │ Security/Firewall │  │  │ Audit Trail        │   │
│  └─────────────────┘  │  │ Rate Limiting     │  │  │ Smart Contracts    │   │
│                       │  │ Captcha            │  │  │ (placeholder)      │   │
│  ┌─────────────────┐  │  └───────────────────┘  │  └────────────────────┘   │
│  │ LLM Providers    │  │                         │                            │
│  │ OpenAI/Anthropic │  │  ┌───────────────────┐  │  ┌────────────────────┐   │
│  │ Gemini/Ollama    │  │  │ Audit Service     │  │  │ Firewall Module    │   │
│  └─────────────────┘  │  │ IP Tracking       │  │  │ IP Blocking        │   │
│                       │  │ Anomaly Detection  │  │  │ Threat Scoring     │   │
│  ┌─────────────────┐  │  └───────────────────┘  │  └────────────────────┘   │
│  │ Vector Store     │  │                         │                            │
│  │ FAISS (abst.)    │  │                         │                            │
│  └─────────────────┘  │                         │                            │
├───────────────────────┴─────────────────────────┴────────────────────────────┤
│                              PostgreSQL / SQLite                              │
│                              Redis Cache                                      │
│                              File Storage (PDF/DOCX/TXT)                     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AI Workflow

```
┌──────────┐    ┌──────────────────┐    ┌──────────────┐    ┌─────────────────┐
│  User    │───▶│  Doctor Agent /  │───▶│    LLM       │───▶│   RAG Pipeline  │
│  Input   │    │  Medical Records │    │  Provider     │    │                 │
│          │    │  Agent           │    │  OpenAI       │    │  Retrieve from  │
└──────────┘    └──────────────────┘    │  Anthropic    │    │  Vector Store   │
                                        │  Gemini       │    │                 │
                                        │  Ollama       │    └────────┬────────┘
                                        └──────────────┘             │
                                                                     ▼
                                        ┌─────────────────────────────────────┐
                                        │          Vector Store (FAISS)        │
                                        │  ┌─────────┐ ┌─────────┐ ┌────────┐ │
                                        │  │ Document│ │ Medical │ │Patient │ │
                                        │  │Chunks   │ │ Records │ │History │ │
                                        │  └─────────┘ └─────────┘ └────────┘ │
                                        └─────────────────────────────────────┘
                                                                     │
                                                                     ▼
┌──────────┐    ┌──────────────────┐    ┌──────────────────────────────────────┐
│  Audit   │◀───│  Response with   │◀───│       AI Processing Pipeline         │
│  Trail   │    │  Explanation     │    │                                      │
│  SHA-256 │    │  Panel           │    │  Reasoning / Confidence / Disclaimer │
│  Hash    │    │                  │    │  / Recommended Follow-up             │
└──────────┘    └──────────────────┘    └──────────────────────────────────────┘
```

## Doctor Workflow

1. **Login** - Authenticate via the secure login portal
2. **Dashboard** - View patient stats, recent AI activity
3. **AI Summary** - Select a patient and generate AI-powered clinical summaries
4. **Medical Records** - Upload PDF/DOCX/TXT documents for AI extraction (diseases, medications, allergies, vitals, lab values)
5. **AI Suggestions** - Review suggested diagnoses, tests, and findings
6. **Conversations** - Continue previous AI conversations, search history, delete conversations
7. **Verify** - Every AI response includes "AI Suggestion — Requires Doctor Verification"

## Medical Records Workflow

1. Upload PDF/DOCX/TXT (validated for type and size <10MB)
2. Text extraction via PyPDF2/python-docx
3. HTML sanitization
4. Text chunking (configurable size/overlap)
5. Embedding generation (OpenAI/local)
6. Vector storage (FAISS)
7. AI extraction of: diseases, medications, allergies, vital signs, lab values, doctor names, visit dates
8. Structured JSON output with confidence scores
9. Doctor review required before any data is saved to patient records

## Blockchain Workflow

1. AI generates a summary/diagnosis/test recommendation
2. SHA-256 hash is computed
3. Audit trail entry is created with hash
4. Hash is prepared for future on-chain storage
5. Smart contracts are NOT modified by the AI module

## API Reference

### Health
- `GET /api/health` - Health check
- `GET /api/ready` - Readiness check (DB + cache)

### Authentication
- `POST /login/` - Django login
- `POST /logout/` - Django logout

### AI Chat
- `POST /api/v1/ai/doctor/chat` - Doctor AI chat
  - Body: `{ "message": "...", "patient_id": 1, "conversation_id": "uuid" }`
  - Response: `{ "conversation_id": "uuid", "response": "...", "explanation": {...} }`

- `POST /api/v1/ai/medical-records/chat` - Medical Records Agent
  - Body: `{ "action": "extract|summarize|analyze", "document_text": "...", "filename": "...", "patient_id": 1 }`

### Documents
- `POST /api/v1/ai/upload-document` - Upload medical document (multipart/form-data)
- `GET /api/v1/ai/documents` - List documents
- `GET /api/v1/ai/documents/{id}` - Document detail with extracted text

### Conversations
- `GET /api/v1/ai/conversations?search=&agent_type=&page=1&page_size=20` - List conversations
- `GET /api/v1/ai/history/{id}` - Conversation history with messages
- `DELETE /api/v1/ai/history/{id}` - Delete (soft-delete) conversation

### Audit
- Audit records are created automatically for every AI summary, diagnosis suggestion, test recommendation, and record extraction

## AI Agents

### Doctor Agent
- Summarizes patient history, appointments, prescriptions, documents
- Highlights abnormal findings
- Suggests diagnoses (differential)
- Suggests follow-up tests
- Every response includes: Reasoning, Confidence, Medical Disclaimer, Recommended Follow-up

### Medical Records Agent
- Extracts structured data from uploaded medical documents
- Detects: diseases, medications, allergies, vital signs, lab values, doctor names, visit dates
- Generates structured JSON with confidence scores
- Generates concise AI summaries
- Analyzes for suggested diagnoses and tests
- Never writes directly to patient records

## AI Explanation Panel

Every AI response includes:
- **Reasoning**: Step-by-step explanation of the AI's analysis
- **Confidence**: Confidence score/assessment
- **Medical Disclaimer**: "AI Suggestion — Requires Doctor Verification"
- **Recommended Follow-up**: Suggested next steps for the doctor

## Audit Trail

All AI actions are logged with:
- Doctor, patient, timestamp
- Document and conversation IDs
- AI model used
- SHA-256 hash for integrity
- Blockchain interface (placeholder)
- Action type: summary, diagnosis_suggestion, test_recommendation, record_extraction

## Technology Stack

| Component            | Technology                                      |
|----------------------|-------------------------------------------------|
| **Backend**          | Django 5.2, Django REST Framework 3.15          |
| **AI/LLM**           | OpenAI, Anthropic, Google Gemini, Ollama        |
| **Vector Store**     | FAISS (abstraction layer for future migration)  |
| **Document Proc.**   | PyPDF2, python-docx                             |
| **Frontend**         | Bootstrap 5, Django Templates                   |
| **Cache**            | Redis                                           |
| **Database**         | SQLite (dev) / PostgreSQL (prod)                |
| **Blockchain**       | Hardhat, Solidity 0.8, Web3.py, OpenZeppelin    |
| **Security**         | Rate limiting, IP blocking, Captcha, Firewall   |
| **Deployment**       | Docker, Gunicorn, Nginx                         |
| **Testing**          | pytest, pytest-django, hypothesis               |

## Environment Variables

| Variable                              | Default                            | Description                           |
|---------------------------------------|------------------------------------|---------------------------------------|
| `DEBUG`                               | `True`                             | Debug mode                            |
| `DJANGO_SECRET_KEY`                   | `your-secret-key-here...`          | Django secret key                     |
| `ALLOWED_HOSTS`                       | `127.0.0.1,localhost`              | Comma-separated allowed hosts         |
| `CORS_ALLOWED_ORIGINS`                | `http://localhost:3000`            | CORS allowed origins                  |
| `REDIS_HOST`                          | `localhost`                        | Redis host                            |
| `REDIS_PORT`                          | `6379`                             | Redis port                            |
| `REDIS_DB`                            | `0`                                | Redis database index                  |
| `BLOCKCHAIN_PROVIDER_URL`             | `http://127.0.0.1:8545`            | Blockchain RPC URL                    |
| `BLOCKCHAIN_NETWORK_ID`               | `31337`                            | Blockchain network ID                 |
| `BLOCKCHAIN_GAS_LIMIT`                | `500000`                           | Blockchain gas limit                  |
| `BLOCKCHAIN_CONFIRMATION_TIMEOUT`     | `30`                               | Blockchain confirmation timeout       |
| `CONTRACT_PATIENT_REGISTRY_ADDRESS`   | ``                                 | Patient registry contract address     |
| `CONTRACT_BLOCKED_IP_ADDRESS`         | ``                                 | Blocked IP contract address           |
| `CONTRACT_ATTACK_SIGNATURE_ADDRESS`   | ``                                 | Attack signature contract address     |
| `THREAT_SCORE_MEDIUM`                 | `40`                               | Medium threat score threshold         |
| `THREAT_SCORE_HIGH`                   | `61`                               | High threat score threshold           |
| `RATE_LIMIT_UNAUTHENTICATED`          | `100`                              | Rate limit for unauthenticated users  |
| `RATE_LIMIT_AUTHENTICATED`            | `500`                              | Rate limit for authenticated users    |
| `AUTO_BLOCK_DURATION`                 | `86400`                            | Auto-block duration (seconds)         |
| `CAPTCHA_FAILURE_BLOCK_DURATION`      | `900`                              | Captcha failure block duration        |
| `CAPTCHA_MAX_FAILURES`                | `3`                                | Max captcha failures before block     |
| `LOG_LEVEL`                           | `INFO`                             | Logging level                         |
| `AI_LLM_PROVIDER`                     | `openai`                           | LLM provider (`openai`, `anthropic`, `ollama`, `azure`, `gemini`) |
| `AI_LLM_MODEL`                        | `gpt-4o-mini`                      | LLM model name                        |
| `AI_LLM_API_KEY`                      | ``                                 | API key for the chosen LLM provider   |
| `AI_EMBEDDING_PROVIDER`               | `local`                            | Embedding provider (`local`, `openai`)|
| `AI_EMBEDDING_MODEL`                  | `all-MiniLM-L6-v2`                 | Embedding model name                  |
| `AI_EMBEDDING_DIMENSION`              | `384`                              | Embedding vector dimension            |
| `AI_MAX_UPLOAD_SIZE_MB`               | `10`                               | Max document upload size (MB)         |
| `AI_OLLAMA_BASE_URL`                  | `http://localhost:11434`           | Ollama base URL                       |
| `AI_AZURE_ENDPOINT`                   | ``                                 | Azure OpenAI endpoint                 |
| `AI_AZURE_API_VERSION`                | `2024-02-15-preview`               | Azure API version                     |
| `AI_OPENAI_EMBEDDING_MODEL`           | `text-embedding-3-small`           | OpenAI embedding model                |

## Quick Start

### Development

```bash
# Clone the repository
git clone https://github.com/chptt/caregrid.git
cd caregrid

# Set up environment
cp .env.example .env
# Edit .env with your settings (AI_LLM_API_KEY required for LLM features)

# Run with Docker
docker compose up --build

# Or run locally
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Production

```bash
# Build and start production stack
docker compose -f docker-compose.prod.yml up --build -d

# Run migrations
docker compose -f docker-compose.prod.yml run --rm migrate

# Create superuser
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

## Project Structure

```
caregrid/
├── backend/
│   └── apps/
│       └── ai/                          AI module
│           ├── agents/                  AI agent implementations
│           │   ├── base/                Base agent class
│           │   ├── doctor/              Doctor AI agent
│           │   └── medical_records/     Medical records extraction agent
│           ├── api/                     API views and health endpoints
│           ├── core/                    Exceptions and agent registry
│           ├── document_processing/     PDF/DOCX/TXT extraction, chunking, cleaning
│           ├── embeddings/              Embedding generation (local, OpenAI)
│           ├── memory/                  Conversation memory management
│           ├── prompts/                 Prompt templates and management
│           │   └── templates/           Doctor and medical records prompt files
│           ├── providers/               LLM provider abstraction (OpenAI, Anthropic, Ollama, Gemini, Azure)
│           ├── rag/                     Retrieval-augmented generation pipeline
│           ├── serializers/             Chat, conversation, document serializers
│           ├── services/                Audit and blockchain services
│           ├── utils/                   Logging utilities
│           ├── vectorstore/             Vector storage abstraction (FAISS)
│           ├── models.py                AI data models
│           ├── urls.py                  AI route definitions
│           ├── tests/                   AI-specific tests
│           ├── templates/ai/            AI frontend templates
│           └── static/ai/               AI static assets
├── caregrid/                            Django project configuration
│   ├── apps/                            Django app registry
│   ├── settings.py                      Django settings
│   ├── urls.py                          Root URL configuration
│   ├── wsgi.py                          WSGI entry point
│   └── asgi.py                          ASGI entry point
├── core/                                Main application
│   ├── models.py                        Patient, appointment, blockchain models
│   ├── views.py                         Core API views
│   ├── patient_views.py                 Patient management endpoints
│   ├── appointment_views.py             Appointment management endpoints
│   ├── captcha_views.py                 CAPTCHA challenge/verification
│   ├── blockchain_service.py            Blockchain integration service
│   ├── anomaly_detector.py              Security anomaly detection
│   ├── anomaly_tasks.py                 Background anomaly tasks
│   ├── ip_tracker.py                    IP tracking middleware
│   ├── middleware.py                    Security middleware
│   ├── rate_limiting.py                 Rate limiting logic
│   ├── threat_calculator.py             Threat score computation
│   ├── permissions.py                   Custom permission classes
│   ├── response_helpers.py              API response utilities
│   ├── serializers.py                   Core serializers
│   ├── urls.py                          Core URL routing
│   ├── admin.py                         Admin interface
│   ├── management/                      Custom management commands
│   └── migrations/                      Database migrations
├── users/                               Custom user management with 14 hospital roles
│   ├── models.py                        User model with role-based access
│   ├── views.py                         Authentication views
│   ├── urls.py                          User URL routing
│   ├── middleware/                      User-specific middleware
│   └── migrations/                      User model migrations
├── firewall/                            Security monitoring and IP management
│   ├── models.py                        Blocked IP, attack signature models
│   ├── views.py                         Firewall API views
│   ├── dashboard_views.py               Security dashboard
│   ├── urls.py                          Firewall URL routing
│   ├── abi/                             Smart contract ABI files
│   └── migrations/                      Firewall migrations
├── caregrid_chain/                      Solidity smart contracts (Hardhat)
│   ├── contracts/                       PatientRegistry, BlockedIP, AttackSignatureRegistry
│   ├── scripts/                         Deploy and utility scripts
│   ├── test/                            Solidity contract tests
│   ├── foundry-tests/                   Foundry-based contract tests
│   ├── deployments/                     Deployed contract addresses
│   ├── ignition/                        Hardhat ignition modules
│   ├── hardhat.config.ts                Hardhat configuration
│   └── package.json                     Node.js dependencies
├── templates/                           Django templates
│   ├── dashboard.html                   Dashboard template
│   └── login.html                       Login template
├── nginx/                               Nginx configuration
│   ├── nginx.conf                       Main nginx config
│   └── conf.d/caregrid.conf             Site-specific config
├── tests/                               Comprehensive test suite
│   ├── unit/                            Unit tests (ai, core, firewall, users)
│   ├── api/                             API endpoint tests (ai, appointments, patients)
│   ├── integration/                     Integration tests
│   ├── property/                        Property-based tests (blockchain, blocklist, security)
│   └── conftest.py                      Shared test fixtures
├── scripts/                             Deployment and utility scripts
│   ├── docker-start.sh / .bat           Docker startup scripts
│   ├── docker-stop.sh / .bat            Docker stop scripts
│   ├── docker-deploy-contracts.sh       Contract deployment script
│   ├── docker-migrate.sh                Migration script
│   ├── start-blockchain.sh / .bat       Blockchain node startup
│   ├── setup.sh / .bat                  Environment setup
│   ├── run_background_tasks.py          Background task runner
│   ├── update_contract_addresses.py     Contract address updater
│   └── verify_setup.py                  Setup verification
├── docs/                                Project documentation
│   ├── API.md                           API reference
│   ├── SETUP.md                         Setup guide
│   ├── SECURITY.md                      Security dashboard docs
│   ├── DEPLOYMENT.md                    Deployment guide
│   └── DOCKER.md                        Docker guide
├── .github/workflows/ci.yml             CI/CD pipeline
├── Dockerfile                           Multi-stage production build
├── docker-compose.yml                   Full-stack service orchestration
├── docker-compose.prod.yml              Production Docker stack
├── manage.py                            Django entry point
├── requirements.txt                     Python dependencies
├── pytest.ini                           Pytest configuration
├── setup_test_data.py                   Test data setup
├── verify_deployment.py                 Deployment verification
├── start.py                             Application entry script
├── .env.example                         Environment template
└── MediChain_API.postman_collection.json Postman API collection
```

## Security

- All AI responses include medical disclaimer
- AI never modifies patient records automatically
- All API endpoints require authentication
- Rate limiting on all API endpoints
- IP blocking for suspicious activity
- CAPTCHA for sensitive operations
- Blockchain-based integrity verification (placeholder)
- Threat score calculation with medium/high thresholds
- Anomaly detection on access patterns
- IP tracking and auto-blocking middleware

## Testing

```bash
# Run all tests
pytest

# Run AI-specific tests
pytest backend/apps/ai/tests/ -v

# Run with coverage
pytest --cov=backend.apps.ai backend/apps/ai/tests/ -v

# Unit tests
pytest tests/unit/ -v

# Property-based tests
pytest tests/property/ -v

# API tests
pytest tests/api/ -v
```

## Future Agents (Placeholders)

- **Security Agent** - Threat detection and response
- **Compliance Agent** - Regulatory compliance checking
- **Patient Agent** - Patient-facing chatbot
- **Pharmacy Agent** - Medication interaction checking
- **Analytics Agent** - Population health analytics
