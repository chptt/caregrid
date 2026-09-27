#!/usr/bin/env bash
# =============================================================================
# CareGrid — Vercel build script
#
# Vercel installs requirements.txt automatically before this runs.
# This script:
#   1. Collects static files into staticfiles/ (WhiteNoise serves these)
#   2. Runs migrations into db_seed.sqlite3
#   3. Seeds demo data (branches, doctors, admin/doctor users)
#
# api/index.py copies db_seed.sqlite3 → /tmp/db.sqlite3 on every cold start.
# =============================================================================

set -euo pipefail

export DJANGO_SETTINGS_MODULE=caregrid.settings.vercel

echo "=== CareGrid Vercel Build ==="

# ---------------------------------------------------------------------------
# 1. Static files
# ---------------------------------------------------------------------------
echo "--- Collecting static files ---"
python manage.py collectstatic --noinput --clear

# ---------------------------------------------------------------------------
# 2. Migrations + seed into db_seed.sqlite3
#    Override the DB path so we write to the repo root (bundled with deploy)
#    rather than /tmp (not available during Vercel's build step).
# ---------------------------------------------------------------------------
echo "--- Running migrations ---"
python - <<'PYEOF'
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'caregrid.settings.vercel'
from django.conf import settings
settings._setup()
settings.DATABASES['default']['NAME'] = 'db_seed.sqlite3'
django.setup()
from django.core.management import call_command
call_command('migrate', '--run-syncdb', verbosity=1)
print('Migrations complete.')
PYEOF

# ---------------------------------------------------------------------------
# 3. Seed demo data
# ---------------------------------------------------------------------------
echo "--- Seeding demo data ---"
python - <<'PYEOF'
import os, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'caregrid.settings.vercel'
from django.conf import settings
settings._setup()
settings.DATABASES['default']['NAME'] = 'db_seed.sqlite3'
django.setup()

from django.contrib.auth import get_user_model
from core.models import Branch, Doctor

User = get_user_model()

branches = {}
for name, location in [
    ('Main Hospital',  'Downtown Medical Center'),
    ('North Branch',   'North District Clinic'),
    ('South Branch',   'South Side Medical Center'),
]:
    b, created = Branch.objects.get_or_create(name=name, defaults={'location': location})
    branches[name] = b
    if created:
        print(f'  + Branch: {name}')

for name, spec, branch_name in [
    ('Dr. Sarah Johnson',   'Cardiology',      'Main Hospital'),
    ('Dr. Michael Chen',    'Neurology',        'Main Hospital'),
    ('Dr. Emily Rodriguez', 'Pediatrics',       'Main Hospital'),
    ('Dr. David Wilson',    'General Medicine', 'North Branch'),
    ('Dr. Lisa Thompson',   'Dermatology',      'North Branch'),
    ('Dr. James Brown',     'Orthopedics',      'South Branch'),
    ('Dr. Maria Garcia',    'Gynecology',       'South Branch'),
]:
    _, created = Doctor.objects.get_or_create(
        name=name, defaults={'specialization': spec, 'branch': branches[branch_name]}
    )
    if created:
        print(f'  + Doctor: {name}')

if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin', password='caregrid2024',
        email='admin@caregrid.demo', role='admin',
        branch=branches['Main Hospital'],
    )
    print('  + User: admin / caregrid2024')

if not User.objects.filter(username='doctor').exists():
    User.objects.create_user(
        username='doctor', password='caregrid2024',
        email='doctor@caregrid.demo', role='doctor',
        branch=branches['Main Hospital'],
    )
    print('  + User: doctor / caregrid2024')

print('Seed complete.')
PYEOF

echo "=== Build complete ==="
