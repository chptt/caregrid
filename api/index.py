"""
Vercel serverless entry point for CareGrid.

Vercel's Python runtime looks for `app` (WSGI) or `handler` in api/index.py.

On cold start:
  - Adds repo root to sys.path
  - Sets DJANGO_SETTINGS_MODULE to the Vercel settings
  - Copies the pre-seeded db_seed.sqlite3 (bundled at build time) to
    /tmp/db.sqlite3 (the writable path the Vercel settings point at)
  - Returns the Django WSGI application as `app`
"""

import os
import sys
import shutil
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — repo root must be on sys.path for Django to find all modules
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent   # d:/caregrid/
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'caregrid.settings.vercel')

# ---------------------------------------------------------------------------
# Copy seed DB to /tmp on every cold start
# db_seed.sqlite3 is built by build_files.sh and bundled as a read-only file.
# /tmp/db.sqlite3 is the writable path Django writes to at runtime.
# ---------------------------------------------------------------------------
_seed = ROOT / 'db_seed.sqlite3'
_live = Path('/tmp/db.sqlite3')

if _seed.exists() and not _live.exists():
    _live.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(_seed), str(_live))

# Also ensure /tmp/media exists for any runtime uploads
Path('/tmp/media').mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Django WSGI app — Vercel expects the callable named `app`
# ---------------------------------------------------------------------------
from django.core.wsgi import get_wsgi_application  # noqa: E402

app = get_wsgi_application()
