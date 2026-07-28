# Changelog

All notable changes to CareGrid will be documented in this file.

## [1.0.0] - Unreleased

### Added
- Environment-based configuration (all secrets via env vars)
- Structured logging with separate files for app, security, blockchain, and errors
- Rotating log handlers for production readiness
- Standardized API response helpers (`core/response_helpers.py`)
- Docker support with full-stack orchestration (Redis, Hardhat, Django)
- Multi-stage Dockerfile with non-root user
- Comprehensive `.dockerignore`
- Test suite organized into `tests/unit/`, `tests/property/`, `tests/api/`, `tests/integration/`
- `CONTRIBUTING.md` and `CHANGELOG.md`
- Consolidated documentation under `docs/`

### Changed
- Flattened `caregrid-main/` subdirectory to repository root
- Refactored `firewall/views.py` to use lazy initialization (no crash on missing blockchain)
- Renamed Docker containers from `medichain_*` to `caregrid_*`
- Updated `.gitignore` to prevent committing generated artifacts
- Updated CI pipeline to Python 3.11 and Node 18

### Removed
- Duplicate root-level project files (early version)
- Committed `node_modules/`, `__pycache__/`, Hardhat build artifacts
- Committed SQLite database files
- Redundant documentation files (consolidated into `docs/`)
- Empty placeholder test files
- Empty frontend directory (mature version had no frontend)

### Fixed
- `firewall/views.py` module-level blockchain connection causing crash when Hardhat is unavailable
- Bare `except:` clause in `blockchain_service.py`
- Hardcoded `SECRET_KEY` now loaded from environment
- `DEBUG` flag now configurable via environment
- `corsheaders` properly added to `INSTALLED_APPS`
