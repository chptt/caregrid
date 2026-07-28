FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=caregrid.settings
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r caregrid && useradd -r -g caregrid caregrid

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY . .

RUN mkdir -p logs static && chown -R caregrid:caregrid logs static

RUN chown -R caregrid:caregrid /app

USER caregrid

RUN python manage.py collectstatic --noinput --clear || true

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/admin/ || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
