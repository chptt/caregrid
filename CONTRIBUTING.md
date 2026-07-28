# Contributing to CareGrid

## Development Setup

1. Fork and clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy `.env.example` to `.env`
5. Run migrations: `python manage.py migrate`
6. Start the development server: `python manage.py runserver`

## Code Style

- Follow PEP 8 for Python code
- Use type hints where practical
- Keep views/controllers lightweight; move business logic to service classes
- Write meaningful docstrings for public APIs

## Testing

All contributions must include tests where applicable:

```bash
# Run the full test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=core --cov=firewall --cov=users
```

- Unit tests go in `tests/unit/`
- API/endpoint tests go in `tests/api/`
- Property-based tests go in `tests/property/`
- Integration tests go in `tests/integration/`

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes with tests
3. Ensure all tests pass
4. Update documentation if needed
5. Submit a pull request with a clear description

## Reporting Issues

Use GitHub Issues to report bugs or request features. Include:
- Steps to reproduce
- Expected vs actual behavior
- Environment details
