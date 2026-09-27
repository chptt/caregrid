# CareGrid

Blockchain-secured healthcare management system with AI-powered clinical decision support, real-time threat detection, and Ethereum smart contract integration.

## What's Built

### Core Healthcare System
- **Patient management** — register patients, search, retrieve records. Each patient gets a deterministic blockchain ID derived from name + DOB + email (keccak256 hash), auto-registered on-chain.
- **Appointment management** — create and list appointments linking patients, doctors, and hospital branches
- **14-role user system** — Admin, Doctor, Patient, Receptionist, Lab Technician, Nursing Station, Pharmacy, Operation Theatre, Scanning Room, Room Allocation Manager, Billing, Medical Records Officer, Dietician, Sanitation Manager
- **Multi-branch support** — patients, doctors, and appointments are scoped to hospital branches

### AI Module
Two purpose-built agents backed by a pluggable LLM provider layer:

**Doctor Agent** — clinical decision support
- Summarizes patient history, appointments, prescriptions, and uploaded documents
- Highlights abnormal findings across records
- Suggests differential diagnoses and follow-up tests
- Every response appends "AI Suggestion — Requires Doctor Verification" and an explanation panel (reasoning, confidence, disclaimer, follow-up)
- RAG pipeline retrieves relevant context from FAISS vector store before every LLM call

**Medical Records Agent** — document intelligence
- Extracts structured data from uploaded PDF/DOCX/TXT files: diseases, medications, allergies, vital signs, lab values, doctor names, visit dates
- Generates concise document summaries
- Analyzes documents for suggested diagnoses and tests
- Never writes directly to patient records — all suggestions require doctor approval

**LLM Providers** — OpenAI, Google Gemini, Ollama (local). Configured via `AI_LLM_PROVIDER` / `AI_LLM_MODEL` / `AI_LLM_API_KEY` env vars.

**Embeddings** — local sentence-transformers (`all-MiniLM-L6-v2`, 384-dim) or OpenAI (`text-embedding-3-small`). Vectors stored in FAISS.

**Document processing pipeline**:
1. Upload PDF/DOCX/TXT (max 10 MB, validated by type and size)
2. Text extraction via PyPDF2 / python-docx
3. HTML sanitization
4. Configurable chunking (size + overlap)
5. Embedding generation → FAISS ingestion
6. Chunk metadata stored in `EmbeddingMetadata` for retrieval tracing

**Audit trail** — every AI action (summary, diagnosis suggestion, test recommendation, document extraction) is logged to `AuditTrail` with doctor, patient, timestamp, AI model used, input/output summaries, confidence score, and SHA-256 blockchain hash.

**Data models**: `AuditTrail`, `MedicalRecord`, `Conversation`, `Message`, `UploadedDocument`, `EmbeddingMetadata`, `AISummary`

### Blockchain Integration
Three Solidity smart contracts deployed on a local Hardhat node:

| Contract | Purpose |
|---|---|
| `PatientRegistry` | Registers patients on-chain by keccak256 ID hash |
| `BlockedIPRegistry` | Stores blocked IPs with expiry times and block reasons |
| `AttackSignatureRegistry` | Stores attack pattern signatures with severity 1–10 |

`BlockchainService` wraps web3.py with:
- Transaction retry logic (3 attempts, exponential backoff)
- Redis caching for read calls (5-minute TTL for patient/IP lookups, 1-minute for block status)
- Graceful offline mode — the system runs normally if the blockchain node is unavailable

### Security System
All requests pass through `SecurityMiddleware` which computes a 0–100 threat score from six factors:

| Factor | Max Points | Description |
|---|---|---|
| Request rate | 20 | Requests per minute via Redis sliding window |
| Endpoint repetition | 25 | Ratio of repeated endpoint hits in last 20 requests |
| Session behavior | 20 | No session/cookies signals bot traffic |
| User-Agent entropy | 15 | Single UA = likely bot; too many UAs = rotation |
| Auth failures | 10 | Failed login attempts in 10-minute window |
| Blockchain signature match | 30 | Match against on-chain attack patterns |

**Actions by score:**
- `< 40` — allow
- `40–60` — require CAPTCHA (math challenge, Redis token, 5-min expiry)
- `60–80` — block request
- `≥ 80` — auto-block: write IP to blockchain + local `BlockedIP` table with 24-hour expiry

**Anomaly detector** — identifies coordinated attacks across multiple IPs; boosts threat score by 30 if detected.

**Rate limiting** — configurable per-request thresholds for unauthenticated (`100/min` default) and authenticated (`500/min`) users.

**IP tracking** — tracks request rates, patterns, and auth failures per IP in Redis. Blocked IPs sync to `BlockedIPRegistry` contract.

**Security dashboard** — REST endpoints for viewing security logs, blocked IPs, stats, and manually blocking/unblocking IPs.

### Logging
Four rotating log files (10 MB max, 5–10 backups):
- `logs/app.log` — general application logs
- `logs/security.log` — all security events with IP, threat score, factors, action
- `logs/blockchain.log` — all on-chain transactions and connection events
- `logs/error.log` — errors only, across all loggers

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      CareGrid Platform                       │
├─────────────────────────────────────────────────────────────┤
│             Django REST API + Django Templates               │
│          (Session auth, rate limiting, CAPTCHA)              │
├───────────────────┬──────────────────┬──────────────────────┤
│    AI Module      │  Core Services   │  Blockchain          │
│                   │                  │                      │
│  Doctor Agent     │  Patients        │  PatientRegistry     │
│  MedRecords Agent │  Appointments    │  BlockedIPRegistry   │
│  RAG Pipeline     │  Security MW     │  AttackSignatureReg  │
│  FAISS Store      │  Threat Score    │  web3.py + Hardhat   │
│  LLM Providers    │  Anomaly Detect  │                      │
├───────────────────┴──────────────────┴──────────────────────┤
│           SQLite (dev) / PostgreSQL (prod)                   │
│                      Redis Cache                             │
│               File Storage (PDF/DOCX/TXT)                    │
└─────────────────────────────────────────────────────────────┘
```

## Technology Stack

| Component | Technology |
|---|---|
| Backend | Django 5.2, Django REST Framework 3.15 |
| AI / LLM | OpenAI, Google Gemini, Ollama |
| Vector Store | FAISS (via faiss-cpu) |
| Embeddings | sentence-transformers, OpenAI |
| Document Processing | PyPDF2, python-docx |
| Cache | Redis 7 |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Blockchain | Hardhat, Solidity 0.8, web3.py, OpenZeppelin |
| Security | Rate limiting, IP blocking, CAPTCHA, threat scoring |
| Deployment | Docker, Gunicorn, Nginx |
| Testing | pytest, pytest-django, hypothesis (property-based) |

## API Endpoints

### Health
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/ready` | Readiness check (DB + cache) |

### Authentication
| Method | Endpoint | Description |
|---|---|---|
| POST | `/login/` | Django session login |
| POST | `/logout/` | Django session logout |
| POST | `/api/users/register/` | Register new user |

### Patients
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/patients/` | Register patient (auto-generates blockchain ID) |
| GET | `/api/patients/search/?q=` | Search patients |
| GET | `/api/patients/<id>/` | Get patient details |
| GET | `/api/branches/` | List hospital branches |

### Appointments
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/appointments/` | Create appointment |
| GET | `/api/appointments/list/` | List appointments |
| GET | `/api/appointments/<id>/` | Get appointment details |
| GET | `/api/appointments/patient/<id>/` | Patient's appointments |
| GET | `/api/doctors/` | List doctors |

### AI
| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/ai/doctor/chat` | Doctor AI chat — body: `{message, patient_id, conversation_id}` |
| POST | `/api/v1/ai/medical-records/chat` | Medical records agent — body: `{action, document_text, filename, patient_id}` — `action` is `extract`, `summarize`, or `analyze` |
| POST | `/api/v1/ai/upload-document` | Upload document (multipart/form-data) — extracts text, chunks, embeds, ingests into FAISS |
| GET | `/api/v1/ai/documents` | List uploaded documents |
| GET | `/api/v1/ai/documents/<id>` | Document detail with extracted text |
| GET | `/api/v1/ai/conversations` | List conversations (`?search=&agent_type=&page=&page_size=`) |
| GET | `/api/v1/ai/history/<id>` | Conversation history with all messages |
| DELETE | `/api/v1/ai/history/<id>` | Soft-delete conversation |

### Security
| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/security/captcha/` | Get CAPTCHA challenge |
| POST | `/api/security/captcha/` | Submit CAPTCHA answer |
| GET | `/api/security/dashboard/` | Security dashboard data |
| GET | `/api/security/stats/` | Security statistics |
| POST | `/api/security/block/` | Manually block IP (admin) |
| POST | `/api/security/unblock/` | Unblock IP (admin) |

## Quick Start

### Local Development

```bash
git clone https://github.com/chptt/caregrid.git
cd caregrid

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env — set AI_LLM_API_KEY for LLM features

python manage.py migrate
python setup_test_data.py
python manage.py runserver
```

Blockchain (optional, for on-chain features):
```bash
# Terminal 1 — start Hardhat node
cd caregrid_chain && npm install && npx hardhat node

# Terminal 2 — deploy contracts
cd caregrid_chain && npx hardhat run scripts/deploy-all.ts --network localhost
```

### Docker

```bash
docker compose up --build
```

Starts Redis, Hardhat node, contract deployment, migrations, and the Django server.

### Production

```bash
docker compose -f docker-compose.prod.yml up --build -d
docker compose -f docker-compose.prod.yml run --rm migrate
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DJANGO_SECRET_KEY` | insecure dev key | Django secret key |
| `DEBUG` | `False` | Debug mode |
| `ALLOWED_HOSTS` | `127.0.0.1,localhost` | Comma-separated allowed hosts |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REDIS_DB` | `0` | Redis database index |
| `BLOCKCHAIN_PROVIDER_URL` | `http://127.0.0.1:8545` | Hardhat RPC URL |
| `BLOCKCHAIN_NETWORK_ID` | `31337` | Hardhat network ID |
| `BLOCKCHAIN_GAS_LIMIT` | `500000` | Gas limit per transaction |
| `BLOCKCHAIN_CONFIRMATION_TIMEOUT` | `30` | Transaction timeout (seconds) |
| `CONTRACT_PATIENT_REGISTRY_ADDRESS` | — | Deployed PatientRegistry address |
| `CONTRACT_BLOCKED_IP_ADDRESS` | — | Deployed BlockedIPRegistry address |
| `CONTRACT_ATTACK_SIGNATURE_ADDRESS` | — | Deployed AttackSignatureRegistry address |
| `THREAT_SCORE_MEDIUM` | `40` | Medium threat threshold (CAPTCHA trigger) |
| `THREAT_SCORE_HIGH` | `61` | High threat threshold (block trigger) |
| `RATE_LIMIT_UNAUTHENTICATED` | `100` | Requests/min for unauthenticated users |
| `RATE_LIMIT_AUTHENTICATED` | `500` | Requests/min for authenticated users |
| `AUTO_BLOCK_DURATION` | `86400` | Auto-block duration in seconds (24h) |
| `CAPTCHA_FAILURE_BLOCK_DURATION` | `900` | Block duration after CAPTCHA failures (15m) |
| `CAPTCHA_MAX_FAILURES` | `3` | Max CAPTCHA failures before block |
| `LOG_LEVEL` | `INFO` | Logging level |
| `AI_LLM_PROVIDER` | `openai` | LLM provider: `openai`, `gemini`, `ollama` |
| `AI_LLM_MODEL` | `gpt-4o-mini` | LLM model name |
| `AI_LLM_API_KEY` | — | API key for chosen LLM provider |
| `AI_EMBEDDING_PROVIDER` | `local` | Embedding provider: `local`, `openai` |
| `AI_EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model name |
| `AI_EMBEDDING_DIMENSION` | `384` | Embedding vector dimension |
| `AI_MAX_UPLOAD_SIZE_MB` | `10` | Max document upload size in MB |
| `AI_OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |

## Project Structure

```
caregrid/
├── backend/apps/ai/            AI module
│   ├── agents/                 Doctor and Medical Records agents
│   ├── api/                    REST views and health endpoints
│   ├── core/                   Agent registry and exceptions
│   ├── document_processing/    PDF/DOCX/TXT extraction, cleaning, chunking
│   ├── embeddings/             Local (sentence-transformers) and OpenAI embeddings
│   ├── memory/                 Conversation memory management
│   ├── models.py               AuditTrail, Conversation, Message, UploadedDocument, etc.
│   ├── prompts/templates/      Prompt files for doctor and medical records agents
│   ├── providers/              LLM provider abstraction (OpenAI, Gemini, Ollama)
│   ├── rag/                    RAG pipeline (ingest + retrieve)
│   ├── serializers/            Chat, conversation, document serializers
│   ├── services/               Audit service, blockchain hash service
│   ├── tests/                  AI-specific unit and integration tests
│   └── vectorstore/            FAISS vector store abstraction
├── caregrid/                   Django project config (settings, urls, wsgi, asgi)
├── core/                       Patients, appointments, security middleware, threat calculator
├── users/                      Custom user model with 14 hospital roles
├── firewall/                   IP blocking, attack patterns, security dashboard
├── caregrid_chain/             Solidity contracts + Hardhat config
│   └── contracts/              PatientRegistry, BlockedIPRegistry, AttackSignatureRegistry
├── tests/
│   ├── unit/                   Unit tests for models, threat calculator, rate limiting
│   ├── api/                    API endpoint tests for patients, appointments
│   └── property/               Hypothesis property-based tests for blockchain, security
├── templates/                  login.html, dashboard.html
├── nginx/                      Nginx config for production
├── scripts/                    Docker helpers, contract deployment, setup scripts
├── docs/                       API, setup, security, deployment, Docker guides
├── Dockerfile
├── docker-compose.yml
├── docker-compose.prod.yml
└── requirements.txt
```

## Testing

```bash
# All tests
pytest

# Unit tests
pytest tests/unit/ -v

# API tests
pytest tests/api/ -v

# Property-based tests (blockchain, security, threat calculator)
pytest tests/property/ -v

# AI module tests
pytest backend/apps/ai/tests/ -v

# With coverage
pytest --cov=backend.apps.ai backend/apps/ai/tests/ -v
```

## Documentation

- [Setup Guide](docs/SETUP.md)
- [API Documentation](docs/API.md)
- [Security Dashboard](docs/SECURITY.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Docker Guide](docs/DOCKER.md)

## License

MIT License. See [LICENSE](LICENSE) for details.
