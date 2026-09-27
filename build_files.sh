#!/usr/bin/env bash
# =============================================================================
# CareGrid — Vercel build script
#
# Vercel runs this as the Build Command before deploying the lambda.
# What it does:
#   1. Installs Vercel-compatible Python deps
#   2. Runs collectstatic → staticfiles/ (WhiteNoise serves these)
#   3. Runs migrations into db_seed.sqlite3 (bundled with the deploy)
#   4. Seeds demo data (branches, doctors, admin/doctor users)
#
# api/index.py copies db_seed.sqlite3 → /tmp/db.sqlite3 on every cold start.
# =============================================================================

set -euo pipefail

echo "=== CareGrid Vercel Build ==="

# ---------------------------------------------------------------------------
# 1. Install deps
# ---------------------------------------------------------------------------
pip install -r requirements-vercel.txt

# ---------------------------------------------------------------------------
# 2. Static files
# ---------------------------------------------------------------------------
export DJANGO_SETTINGS_MODULE=caregrid.settings.vercel

echo "--- Collecting static files ---"
python manage.py collectstatic --noinput --clear

# ---------------------------------------------------------------------------
# 3. Migrations into db_seed.sqlite3
#    We override the DB path at build time so the seed file ends up in the
#    repo root (read-only after deploy) rather than /tmp (not available during
#    the build step on Vercel's build worker).
# ---------------------------------------------------------------------------
echo "--- Running migrations ---"
python - <<'PYEOF'
import os, django

os.environ['DJANGO_SETTINGS_MODULE'] = 'caregrid.settings.vercel'

import django.conf as conf
# Import settings first so we can patch before setup()
from django.conf import settings
# settings is lazy — force load
settings._setup()
# Point DB at build-time seed file in repo root
settings.DATABASES['default']['NAME'] = 'db_seed.sqlite3'

django.setup()
from django.core.management import call_command
call_command('migrate', '--run-syncdb', verbosity=1)
print('Migrations complete.')
PYEOF

# ---------------------------------------------------------------------------
# 4. Seed demo data into db_seed.sqlite3
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

# --- Branches ---
branch_data = [
    ('Main Hospital',  'Downtown Medical Center'),
    ('North Branch',   'North District Clinic'),
    ('South Branch',   'South Side Medical Center'),
]
branches = {}
for name, location in branch_data:
    b, created = Branch.objects.get_or_create(name=name, defaults={'location': location})
    branches[name] = b
    if created:
        print(f'  + Branch: {name}')

# --- Doctors ---
doctor_data = [
    ('Dr. Sarah Johnson',   'Cardiology',      'Main Hospital'),
    ('Dr. Michael Chen',    'Neurology',        'Main Hospital'),
    ('Dr. Emily Rodriguez', 'Pediatrics',       'Main Hospital'),
    ('Dr. David Wilson',    'General Medicine', 'North Branch'),
    ('Dr. Lisa Thompson',   'Dermatology',      'North Branch'),
    ('Dr. James Brown',     'Orthopedics',      'South Branch'),
    ('Dr. Maria Garcia',    'Gynecology',       'South Branch'),
]
for name, spec, branch_name in doctor_data:
    _, created = Doctor.objects.get_or_create(
        name=name,
        defaults={'specialization': spec, 'branch': branches[branch_name]},
    )
    if created:
        print(f'  + Doctor: {name}')

# --- Demo users ---
# admin / caregrid2024
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser(
        username='admin',
        password='caregrid2024',
        email='admin@caregrid.demo',
        role='admin',
        branch=branches['Main Hospital'],
    )
    print('  + User: admin (password: caregrid2024)')

# doctor / caregrid2024
if not User.objects.filter(username='doctor').exists():
    User.objects.create_user(
        username='doctor',
        password='caregrid2024',
        email='doctor@caregrid.demo',
        role='doctor',
        branch=branches['Main Hospital'],
    )
    print('  + User: doctor (password: caregrid2024)')

print('Seed complete.')
PYEOF

echo "=== Build complete ==="
