# Mula FastAPI backend

This directory contains the Python API. It runs independently from the React
frontend; Node.js and pnpm are not needed to start the backend.

## Requirements

- Python 3.12
- `pip` (included with standard Python installations)

## First-time setup

Run these commands from the repository root:

```sh
cd backend
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r hela_backend/requirements.txt
test -f .env || cp .env.example .env
```

On Windows PowerShell, activate the environment with
`.venv\Scripts\Activate.ps1`. Keep credentials and other private values in
`backend/.env`; do not commit that file. The example config defaults to the
local AI provider, so AWS credentials are optional for local development.

## Run with the local development database

From `backend/`, with the virtual environment active, start the API:

```sh
./run-local.sh
```

The script listens on `127.0.0.1:8000` and uses SQLite at
`backend/mula_dev.db`. It deliberately selects SQLite even if `DATABASE_URL` in
`backend/.env` points to a hosted database, so local work does not write to that
database. Development startup creates missing tables from the SQLAlchemy
models.

Check that the API is running:

```sh
curl http://127.0.0.1:8000/health
```

Expected response: `{"status":"ok","service":"mula-api"}`. Interactive API
documentation is at <http://127.0.0.1:8000/docs>. API routes use the
`/api/v1` prefix.

## Use a configured database

To connect to a database configured by `DATABASE_URL` in `backend/.env`, start
Uvicorn directly instead of using `run-local.sh`:

```sh
cd backend
source .venv/bin/activate
python -m uvicorn main:app --app-dir hela_backend --reload --host 127.0.0.1 --port 8000
```

Set `APP_ENV=development` for local use; the app creates missing tables in
development. Production schema migrations are not configured in this
repository yet, so do not rely on startup table creation for production.

## Stop the server

Press `Ctrl+C` in the terminal running Uvicorn. Start the frontend separately
from `frontend/`; its development server typically runs at
<http://localhost:5173> and calls this API at port 8000.
