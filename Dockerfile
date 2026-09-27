FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt gunicorn

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=caregrid.settings
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y \
    curl libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r caregrid && useradd -r -g caregrid caregrid

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY . .

RUN mkdir -p logs staticfiles media ai_uploads && \
    chown -R caregrid:caregrid logs staticfiles media ai_uploads

USER caregrid

RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["gunicorn", "caregrid.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-"]
