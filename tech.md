# Hela Tech Stack

A breakdown of the technologies behind Hela, why each was chosen, and how the new **Hela Score** fits into the architecture.

---

## Stack at a Glance

| Layer | Tools / Frameworks |
|-------|-------------------|
| Frontend | React, TypeScript, Vite, TailwindCSS, Framer Motion |
| Backend | Django, Django REST Framework |
| AI Layer | AWS Bedrock (Nova Lite + Nova Micro) with local fallback |
| Scoring Engine | Deterministic Python service inside Django (versioned rules) |
| Database | PostgreSQL (Neon) in production, SQLite in development |
| Cache | Redis |
| Task Queue | Celery + Celery Beat |
| Payments | Paystack |
| Integrations | M-Pesa, Google OAuth, M-Shwari, KCB M-Pesa, Ziidi |
| Hosting | Cloudflare Workers (frontend), Docker + Gunicorn + Nginx (backend) |
| Design | Figma |
| DevTools | VS Code, Git, Postman, pnpm |

---

## Frontend

| Tool | Purpose |
|------|---------|
| **React** | Component-based UI for the dashboard, budget, chat, and score pages |
| **TypeScript** | Type safety across components and API responses |
| **Vite** | Fast dev server and builds (runs on port 5173 locally) |
| **TailwindCSS** | Utility-first styling and a consistent design system |
| **Framer Motion** | Animations such as the score gauge, progress tracker, and tier transitions |
| **pnpm** | Fast, disk-efficient package management |

**Score-specific UI**
- `ScoreGauge`: animated 300 to 850 dial with tier colors
- `FactorBreakdown`: per-factor bars showing strengths and weak spots
- `DecisionFeed`: timeline of decisions and their point impact
- Score history chart (line chart showing progress over time)

---

## Backend

| Tool | Purpose |
|------|---------|
| **Django** | Core framework, ORM, admin, auth |
| **Django REST Framework** | REST API, serializers, permissions |
| **JWT (SimpleJWT)** | Stateless authentication with refresh tokens |
| **Gunicorn** | Production WSGI server |
| **Nginx** | Reverse proxy and static file serving |

**Django apps**

| App | Responsibility |
|-----|---------------|
| `users` | Registration, login, Google OAuth, profile |
| `ai_assistant` | Conversations, messages, insights, goals, Bedrock integration |
| `transactions` | Transaction storage, sync, and categorization |
| `financial_planning` | Budgets, income, expenses, savings plans |
| `payments` | Paystack integration |
| `credit_score` | Hela Score: snapshots, events, factors, simulator |

---

## AI Layer

| Component | Details |
|-----------|---------|
| **Provider** | AWS Bedrock, selected with the `AI_PROVIDER` env var |
| **Nova Lite** | Reasoning tasks: advice, budget planning, chat, transaction analysis, score coaching |
| **Nova Micro** | Fast tasks: spending categorization and quick lookups |
| **Rate limiting** | Per-model token bucket (50 RPM), exponential backoff with jitter, max 5 retries |
| **Timeout** | 30 seconds per request |
| **Fallback** | Keyword-based local responses for testing and offline use |

**Design principle:** numbers come from the backend, language comes from the model. The AI explains and coaches, but it never calculates or alters a score.

---

## Hela Score Engine

### Architecture

```
M-Pesa / Transactions ─┐
Budgets & Expenses ────┼──► Event Detector ──► Scoring Engine ──► ScoreSnapshot
Goals & Savings ───────┤         │                   │
Reminders & Bills ─────┘         ▼                   ▼
                           ScoreEvent          AI Coach (narration only)
```

### Components

| Component | Role |
|-----------|------|
| **Event Detector** | Watches transactions, budgets, and goals and emits score events (for example, `bill_paid_early`, `savings_target_met`, `fuliza_overuse`) |
| **Scoring Engine** | Applies versioned, weighted rules across five factors and produces the 300 to 850 score |
| **Simulator** | Runs the engine against a hypothetical change to project impact |
| **Celery Tasks** | Nightly recalculation, plus event-triggered updates after meaningful transactions |
| **AI Coach** | Turns score changes into plain-language explanations and next steps |

### Data Models

| Model | Key Fields |
|-------|-----------|
| `ScoreSnapshot` | user, score, tier, engine_version, calculated_at |
| `ScoreFactor` | snapshot, factor, weight, sub_score, notes |
| `ScoreEvent` | user, event_type, points_delta, reason, source_ref, created_at |

### Why Deterministic and Versioned

- **Explainability:** every point can be traced to a rule and an event
- **Fairness and auditability:** rule changes ship as a new `engine_version`, and old scores stay explainable
- **Cost control:** no LLM call is needed to compute a score
- **Trust:** users see consistent results, not model guesswork

### Factor Weights

| Factor | Weight |
|--------|--------|
| Payment Consistency | 30% |
| Savings Behavior | 25% |
| Spending Discipline | 20% |
| Debt Management | 15% |
| Financial Stability | 10% |

---

## Data Layer

| Tool | Purpose |
|------|---------|
| **PostgreSQL (Neon)** | Production database, serverless Postgres with branching |
| **SQLite** | Zero-config database for local development |
| **Redis** | Caching, Celery broker, and rate limit state |

**Indexing notes for scoring:** index `ScoreEvent` and `ScoreSnapshot` on `(user, created_at)` for fast history queries.

---

## Background Jobs

| Tool | Purpose |
|------|---------|
| **Celery** | Async tasks: transaction sync, categorization, score recalculation |
| **Celery Beat** | Scheduled jobs: nightly score recalculation, reminder dispatch, monthly reports |

---

## Payments and Integrations

| Integration | Status | Use |
|-------------|--------|-----|
| **M-Pesa** | In progress | Transaction syncing |
| **Paystack** | In progress | Payment processing and subscriptions |
| **Google OAuth** | In progress | Social login |
| **M-Shwari / KCB M-Pesa / Ziidi** | In progress | Live savings and investment updates |
| **Credit Reference Bureaus** | Planned | Optional, consent-based data enrichment for the score |

---

## Security and Privacy

| Area | Approach |
|------|----------|
| **Authentication** | JWT access and refresh tokens, token invalidation on logout |
| **Secrets** | Environment variables, never committed to the repo |
| **Transport** | HTTPS everywhere, enforced at Nginx and Cloudflare |
| **Data protection** | Aligned with Kenya's Data Protection Act, 2019: consent, minimization, purpose limitation |
| **Score data** | Opt-in sharing only, with user-controlled export and deletion |
| **Encryption** | Encrypt sensitive fields (phone numbers, account references) at rest |
| **Auditability** | Log score engine version and event source for every change |

---

## Deployment and Infrastructure

| Piece | Tool |
|-------|------|
| **Frontend hosting** | Cloudflare Workers |
| **Backend runtime** | Docker with Gunicorn behind Nginx |
| **Database** | Neon PostgreSQL |
| **Containers** | `docker-compose` for local and staging parity |
| **Static files** | `collectstatic` served through Nginx |

---

## Developer Experience

| Tool | Purpose |
|------|---------|
| **VS Code** | Primary editor |
| **Git** | Version control |
| **Postman** | API testing |
| **black / isort / flake8** | Python formatting and linting |
| **pnpm lint** | Frontend linting |
| **Figma** | UI and product design |

---

## Suggested Next Technical Steps for the Score

1. Create the `credit_score` Django app with `ScoreSnapshot`, `ScoreFactor`, and `ScoreEvent` models.
2. Build the event detector against existing transaction categories and budget data.
3. Implement the scoring engine with unit tests for every rule (golden-file tests per `engine_version`).
4. Add the `/api/v1/score/` endpoints and the `ScorePage` UI.
5. Wire the AI Coach `score_coaching` task to narrate score events.
6. Add the what-if simulator and Celery nightly recalculation.
7. Review consent flows and legal requirements before any lender-facing feature.