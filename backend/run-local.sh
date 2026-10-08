#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

python_bin=".venv/bin/python"
if [ ! -x "$python_bin" ]; then
  echo "Backend environment is missing. Run: python3.12 -m venv .venv" >&2
  echo "Then activate it and install: python -m pip install -r hela_backend/requirements.txt" >&2
  exit 1
fi

if ! "$python_bin" -c 'import uvicorn' >/dev/null 2>&1; then
  echo "Backend dependencies are missing. Run: .venv/bin/python -m pip install -r hela_backend/requirements.txt" >&2
  exit 1
fi

# Use a local database for this dev server, even if backend/.env points to Neon.
exec env DATABASE_URL="sqlite+aiosqlite:///./mula_dev.db" \
  "$python_bin" -m uvicorn main:app --app-dir hela_backend \
  --reload --host 127.0.0.1 --port 8000
