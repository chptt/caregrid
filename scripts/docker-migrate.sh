#!/bin/bash

# Script to run Django migrations in Docker environment

set -e

echo "🗄️  Starting Django migrations..."

# Wait for Redis to be ready
echo "⏳ Waiting for Redis to be ready..."
timeout=30
counter=0

while [ $counter -lt $timeout ]; do
    if redis-cli -h redis ping > /dev/null 2>&1; then
        echo "✅ Redis is ready!"
        break
    fi
    echo "⏳ Waiting for Redis... ($counter/$timeout)"
    sleep 2
    counter=$((counter + 2))
done

if [ $counter -ge $timeout ]; then
    echo "❌ Timeout waiting for Redis"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p /app/logs

# Run Django migrations
echo "🔄 Creating migrations..."
python manage.py makemigrations

echo "🔄 Applying migrations..."
python manage.py migrate

# Create superuser if it doesn't exist
echo "👤 Creating superuser (if needed)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "✅ Django migrations completed!"