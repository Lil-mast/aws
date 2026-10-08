# Database setup: local PostgreSQL and Neon

The FastAPI backend uses SQLAlchemy for database access and schema models.
Configure the `DATABASE_URL` in `backend/.env` with the pooled connection string
from Neon (or another PostgreSQL provider). Keep this credential in the backend
directory and out of source control.

For local development, `backend/run-local.sh` uses a SQLite database unless
`DATABASE_URL` is overridden in the shell. In development, FastAPI creates
missing tables from the SQLAlchemy models when it starts.

For production, configure the database before starting the API. Apply schema
changes explicitly as part of deployment; this repository does not include a
production migration tool yet.
