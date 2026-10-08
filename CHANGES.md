# Changes — Mula (pre-push summary)

> This document covers every meaningful change introduced between the
> `origin/main` baseline and the current `HEAD` (commits: `initial commit`,
> `backend almost`, and `well`).

---

## Project overview

**Mula** is a Kenya-first personal finance platform. Users record income and
spending, build monthly budgets, track savings goals, and chat with an
AI-powered money coach. The stack is:

- **Frontend:** React 18 + TypeScript + Vite, served at `localhost:5173`
- **Backend:** Python / FastAPI + SQLAlchemy (async), served at `localhost:8000`
- **Database:** SQLite for local development; PostgreSQL (Neon) in production
- **AI:** Amazon Bedrock (Nova Lite + Nova Micro) with a local keyword fallback

---

## Files added / modified by area

### Backend — core

| File | Status |
|---|---|
| `backend/hela_backend/main.py` | Added |
| `backend/hela_backend/core/config.py` | Added |
| `backend/hela_backend/core/database.py` | Added |
| `backend/hela_backend/core/security.py` | Added |
| `backend/hela_backend/requirements.txt` | Added |
| `backend/run-local.sh` | Added |
| `backend/.env.example` | Added |
| `backend/README.md` | Added |

### Backend — app modules

| File | Status |
|---|---|
| `backend/hela_backend/app/users/models.py` | Added |
| `backend/hela_backend/app/users/schemas/__init__.py` | Added |
| `backend/hela_backend/app/users/routes/__init__.py` | Added |
| `backend/hela_backend/app/transactions/models.py` | Added |
| `backend/hela_backend/app/transactions/schemas/__init__.py` | Added |
| `backend/hela_backend/app/transactions/routes/__init__.py` | Added |
| `backend/hela_backend/app/financial_planning/models.py` | Added |
| `backend/hela_backend/app/financial_planning/schemas/__init__.py` | Added |
| `backend/hela_backend/app/financial_planning/routes/__init__.py` | Added |
| `backend/hela_backend/app/ai_assistant/models.py` | Added |
| `backend/hela_backend/app/ai_assistant/schemas/__init__.py` | Added |
| `backend/hela_backend/app/ai_assistant/routes/__init__.py` | Added |
| `backend/hela_backend/app/ai_assistant/services/conversation_manager.py` | Added |
| `backend/hela_backend/app/ai_assistant/services/bedrock_client.py` | Added |
| `backend/hela_backend/app/credit_score/models.py` | Added |

### Frontend

| File | Status |
|---|---|
| `frontend/src/main.tsx` | Added |
| `frontend/src/App.tsx` | Added |
| `frontend/src/LandingPage.tsx` | Added |
| `frontend/src/api.ts` | Added |
| `frontend/src/styles.css` | Added |
| `frontend/package.json` | Added |
| `frontend/.env.example` | Added |

### Documentation

| File | Status |
|---|---|
| `README.md` | Added |
| `backend/README.md` | Added |
| `docs/database-and-neon.md` | Added |
| `docs/user-story.md` | Added |
| `docs/aws-builder-center-post.md` | Added |

---

## What changed in detail

### 1. Application entry point (`main.py`)

`FastAPI` app named `"Mula API"` (v0.1.0). CORS middleware is configured from
`settings.cors_origins`. Four routers are mounted:

| Router prefix | Module |
|---|---|
| `/api/v1/auth` | `app.users.routes` |
| `/api/v1/transactions` | `app.transactions.routes` |
| `/api/v1/financial` | `app.financial_planning.routes` |
| `/api/v1/assistant` | `app.ai_assistant.routes` |

A `GET /health` endpoint returns `{"status": "ok", "service": "mula-api"}`.

On startup (`lifespan`), if `APP_ENV=development` the app calls
`create_tables()` to auto-create all SQLAlchemy models. Production is
expected to apply schema changes explicitly.

---

### 2. Configuration (`core/config.py`)

`pydantic-settings` `Settings` class loaded from `backend/.env`.

| Variable | Default | Purpose |
|---|---|---|
| `APP_ENV` | `development` | Toggles dev behaviour (table creation, debug mode) |
| `SECRET_KEY` | (placeholder) | JWT signing key — **must be changed in production** |
| `ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |
| `DATABASE_URL` | `""` | Postgres URL; falls back to SQLite when empty |
| `ALLOWED_ORIGINS` | `localhost:5173,3000` | CORS origins (comma-separated) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | `""` | Google OAuth credentials |
| `AI_PROVIDER` | `local` | Set to `bedrock` to enable Bedrock inference |
| `BEDROCK_REGION` | `us-east-1` | AWS region |
| `BEDROCK_NOVA_LITE_MODEL_ID` | ARN | Amazon Nova Lite for reasoning tasks |
| `BEDROCK_NOVA_MICRO_MODEL_ID` | ARN | Amazon Nova Micro for fast tasks |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | `""` | IAM key pair for Bedrock |
| `AWS_BEARER_TOKEN_BEDROCK` | `""` | Optional Bedrock bearer token (alternative to IAM key pair) |
| `SCORE_ENGINE_VERSION` | `1` | Versioned rules engine identifier |
| `SCORE_MIN_DATA_DAYS` | `30` | Minimum history days required before scoring |

A `model_validator` raises `ValueError` if `SECRET_KEY` is still the
placeholder or `DEBUG=True` in production.

The `effective_database_url` property rewrites `postgres://` and
`postgresql://` connection strings to `postgresql+asyncpg://` (required by
SQLAlchemy's async engine) and converts `sslmode=` to `ssl=` for asyncpg
compatibility.

---

### 3. Database (`core/database.py`)

Async SQLAlchemy engine using `aiosqlite` for SQLite and `asyncpg` for
Postgres. `get_db()` is the per-request dependency (yields an
`AsyncSession`, commits on success, rolls back on exception).
`create_tables()` imports all five model modules before calling
`Base.metadata.create_all`.

---

### 4. Security (`core/security.py`)

- **Password hashing:** bcrypt via `passlib`.
- **JWT:** `python-jose`. Access tokens carry `{"sub": user_id, "type": "access"}`; refresh tokens carry `"type": "refresh"`.
- **`get_current_user` dependency:** extracts Bearer token from `Authorization` header, decodes it, verifies `type == "access"`, and loads the `User` row. Returns HTTP 401 if the token is invalid or the user is inactive.

---

### 5. Auth routes (`/api/v1/auth`)

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Creates a `User` + default `UserProfile`. Returns `id` and `email`. Rejects duplicate email with HTTP 400. |
| `POST` | `/login` | Email/password login. Returns access + refresh tokens. |
| `POST` | `/logout` | Marks the supplied refresh token as revoked. |
| `POST` | `/token/refresh` | Token rotation: revokes the old refresh token and issues a new pair. |
| `POST` | `/google` | Verifies a Google ID token via `google-auth`. Creates an account on first sign-in; links `oauth_subject` on subsequent sign-ins. |
| `GET` | `/profile` | Returns user and profile fields for the authenticated user. |
| `PUT` | `/profile/update` | Updates `User` fields (name, phone, currency) and `UserProfile` fields (bio, avatar, monthly income, employment type, score consent). |

Refresh tokens are stored as SHA-256 hashes (`refresh_tokens` table).
Rotation ensures a used refresh token cannot be replayed.

---

### 6. User data models

**`users` table:** `id` (UUID PK), `email` (unique), `hashed_password`
(nullable for OAuth), `full_name`, `phone_number`, `currency` (default KES),
`is_active`, `is_verified`, `oauth_provider`, `oauth_subject`.

**`user_profiles` table:** 1-to-1 with `users`. Stores `bio`, `avatar_url`,
`monthly_income`, `employment_type`, and `score_consent` (boolean, default
`false`).

**`refresh_tokens` table:** Stores hashed tokens with `revoked` flag and
`expires_at`. Used to enforce refresh-token rotation and logout.

---

### 7. Transaction routes (`/api/v1/transactions`)

| Method | Path | Description |
|---|---|---|
| `GET` | `/` | List transactions. Supports `skip`, `limit` (max 200), `transaction_type`, `category`, `from_date`, `to_date` query params. |
| `POST` | `/` | Create a transaction. |
| `GET` | `/summary` | Aggregated totals: `total_credits`, `total_debits`, `net`, `count`, `by_category`. Optional date range filters. |
| `GET` | `/{id}` | Fetch a single transaction (must belong to the authenticated user). |
| `DELETE` | `/{id}` | Delete a transaction. |

**`transactions` table fields of note:**
- `transaction_type`: `"credit"` or `"debit"`
- `source`: `"manual"` or `"mpesa"` (M-Pesa integration is planned, not yet live)
- `external_id`: unique, nullable — intended for deduplication of imported transactions
- Scoring flags: `is_bill_payment`, `is_loan_repayment`, `is_savings`, `is_fuliza`, `due_date`, `paid_early`

---

### 8. Financial planning routes (`/api/v1/financial`)

**Budgets:**

| Method | Path | Description |
|---|---|---|
| `GET` | `/budgets` | List the user's budgets (categories eager-loaded). |
| `POST` | `/budgets/create` | Create a budget with inline `BudgetCategory` rows. |
| `GET` | `/budgets/{id}` | Single budget with categories. |
| `DELETE` | `/budgets/{id}` | Delete budget (cascades to categories). |

Budget categories have a `category_type` of `needs`, `wants`, or `savings`
and track `allocated_amount` vs `spent_amount`.

**Income, Expenses, Savings:**

| Method | Path |
|---|---|
| `GET` / `POST` | `/incomes`, `/incomes/create` |
| `GET` / `POST` | `/expenses`, `/expenses/create` |
| `GET` / `POST` | `/savings`, `/savings/create` |
| `PATCH` | `/savings/{id}` — update `current_amount`, `is_completed`, `target_date` |

Default currency across all models is `KES`.

---

### 9. AI assistant (`/api/v1/assistant`)

**Single endpoint:**

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message; get an assistant reply. Accepts optional `conversation_id` to continue an existing conversation and `task_type` to route to the right model. |

**Conversation management (`conversation_manager.py`):**
- Resolves or creates a `Conversation` record.
- Loads up to the last 20 messages as history.
- Persists the user message, calls the AI client, persists the assistant reply with `model_used`, `input_tokens`, and `output_tokens`.
- Sets the conversation title to the first 80 characters of the first user message.

**Bedrock client (`bedrock_client.py`):**
- `AI_PROVIDER=bedrock` enables live Bedrock inference; any other value uses the local fallback.
- Task routing: `spending_category` → Nova Micro; all other task types → Nova Lite.
- **Rate limiting:** per-model token-bucket at 50 RPM.
- **Retries:** up to 5 attempts with exponential backoff + jitter for `ThrottlingException` and `ServiceUnavailableException`.
- **Timeout:** 30-second read timeout via `botocore.config.Config`.
- **Local fallback:** keyword-based static responses used when Bedrock is disabled or all retries are exhausted.
- AWS credentials: IAM key pair (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`) or a Bedrock bearer token (`AWS_BEARER_TOKEN_BEDROCK`). Bearer token is written to `os.environ["AWS_BEARER_TOKEN_BEDROCK"]` so boto3 picks it up.

**AI assistant data models:**
- `conversations`: multi-turn session records with `task_type` and `budget_step` (0–4 for the guided budget planning flow).
- `messages`: stores role (`user`/`assistant`/`system`), content, model used, and token counts.
- `ai_insights`: proactive AI-generated insights (not yet surfaced in routes).
- `financial_goals`: user-defined goals tracked by the coach (not yet surfaced in routes).

---

### 10. Mula Score models (`app/credit_score/models.py`)

Data models only — no scoring engine or API routes exist yet.

- **`score_snapshots`:** Point-in-time score records (`score` 300–850, `tier` string, `engine_version`). Indexed on `(user_id, calculated_at)`.
- **`score_factors`:** Five rows per snapshot, one per scoring dimension (`payment_consistency`, `savings_behavior`, `spending_discipline`, `debt_management`, `financial_stability`). Stores `weight`, `sub_score` (0–100), `weighted_contribution`, and `notes`.
- **`score_events`:** Individual events that moved the score (`points_delta`, `reason`, optional `source_ref`). Indexed on `(user_id, created_at)`.

The score algorithm is not implemented; these tables hold the schema for when it is built.

---

### 11. Frontend

**`LandingPage.tsx`:** Public marketing page at `/`. Three sections — hero,
feature overview, and a trust/disclaimer section. Calls `onOpenApp("login")`
or `onOpenApp("register")` to transition to the app.

**`App.tsx`:** Single-page app shell with client-side routing via
`window.history.pushState`. Four pages: Overview, Transactions, Budgets, and
Mula assistant. Key behaviour:

- Tokens stored in `localStorage` under `mula_access_token` /
  `mula_refresh_token`.
- On 401, automatically attempts a silent token refresh before retrying; clears
  the session if refresh fails.
- Dashboard loads profile, up to 50 transactions, current-month summary, and
  budgets in parallel on sign-in.
- Inline modals for adding a transaction and creating a budget.
- Chat maintains a `conversation_id` across messages so history is server-side
  persisted.

**`api.ts`:** Typed fetch wrapper. `request<T>()` handles token injection,
automatic refresh (guarded by a single in-flight promise to avoid races), JSON
parsing, and error extraction from FastAPI `detail` fields.

**Dependencies (`package.json`):**
- `react` 18, `react-dom`, `typescript` 5, `vite` 6
- `lucide-react` for icons
- `@vitejs/plugin-react`, `@types/react`, `@types/react-dom`

---

### 12. Environment variables summary

**Backend (`backend/.env`):**

```
APP_ENV, SECRET_KEY, DEBUG, ALLOWED_ORIGINS
DATABASE_URL
GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET
AI_PROVIDER, BEDROCK_REGION
BEDROCK_NOVA_LITE_MODEL_ID, BEDROCK_NOVA_MICRO_MODEL_ID
AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_BEARER_TOKEN_BEDROCK
SCORE_ENGINE_VERSION
```

**Frontend (`frontend/.env.local`):**

```
VITE_API_URL   # defaults to http://127.0.0.1:8000/api/v1
```

---

### 13. Local development

`backend/run-local.sh` forces `DATABASE_URL=sqlite+aiosqlite:///./mula_dev.db`
regardless of the `.env` file content, so local work never touches a configured
Neon database. Tables are created automatically at startup when
`APP_ENV=development`.

---

## Architectural decisions visible in the code

- **All primary keys are UUIDs** using PostgreSQL's native `UUID` column type.
  SQLite stores them as 16-byte blobs via SQLAlchemy's `PG_UUID(as_uuid=True)`.
- **Cascade deletes** on all foreign keys — deleting a user removes all
  associated transactions, budgets, conversations, score data, etc.
- **Async throughout:** `AsyncSession`, `asyncpg`/`aiosqlite`, FastAPI async
  route handlers.
- **Bedrock is opt-in:** `AI_PROVIDER=local` (the default) means the app runs
  fully offline without any AWS dependency.
- **Score consent is explicit:** `UserProfile.score_consent` defaults to
  `false`; the Mula Score engine is intended to run only with user permission
  and at least 30 days of history (`SCORE_MIN_DATA_DAYS`).
- **AI never touches score values:** The system prompt explicitly instructs the
  model to narrate score changes but never calculate or invent them.
- **Token rotation:** Every token refresh revokes the old refresh token and
  issues a new pair, limiting replay attacks.
- **Frontend is SPA without a router library:** routing is handled with
  `window.history.pushState` and `popstate`, keeping the bundle minimal.
