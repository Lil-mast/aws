# Mula: Intelligent Financial Clarity for All

**Mula** is an AI-powered personal and business finance platform built for individuals, families, professionals, and enterprises, starting in Kenya and scaling globally. Mula provides actionable insights, intelligent budgeting, smart reminders, automated goal tracking, and a **Mula Score** that shows how everyday money decisions shape financial health.

---

## Run the App

The application is under active development; run the backend locally using the steps below.

---

## Table of Contents

- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Mula Score](#mula-score)
- [Smart Budget Agent](#smart-budget-agent)
- [AI Assistant Architecture](#ai-assistant-architecture)
- [Integrations](#integrations-in-progress)
- [How It Works](#how-it-works)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Roadmap](#roadmap)
- [Development](#development)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

The full technology breakdown lives in [tech.md](./tech.md).

---

## Quick Start

### Prerequisites
- Node.js 20+ and [pnpm](https://pnpm.io/)
- Python 3.11+
- PostgreSQL 13+ (optional, SQLite is used in development by default)
- Redis 6+ (optional, for Celery)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mula
   ```

2. **Frontend Setup**
   ```bash
   # Project root (React frontend)
   pnpm install
   pnpm dev
   ```
   Frontend runs on: http://localhost:5173

3. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r hela_backend/requirements.txt
   cp .env.example .env
   # Edit backend/.env with local credentials as needed
   uvicorn main:app --app-dir hela_backend --reload
   ```
   Backend API runs on: http://localhost:8000 (docs at `/docs`; health at `/health`)

### Environment Variables
Create `backend/.env` from `backend/.env.example`:
```bash
# Mula API
APP_ENV=development
SECRET_KEY=replace-with-a-random-secret
DEBUG=True
ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000

# Database (blank uses local SQLite; configure PostgreSQL for production)
DATABASE_URL=

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# AWS Bedrock (for AI features)
AI_PROVIDER=local
BEDROCK_REGION=us-east-1
BEDROCK_NOVA_LITE_MODEL_ID=arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-lite-v1:0
BEDROCK_NOVA_MICRO_MODEL_ID=arn:aws:bedrock:us-east-1::foundation-model/amazon.nova-micro-v1:0
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key

# Redis / Celery
REDIS_URL=redis://localhost:6379/1

# Paystack
PAYSTACK_SECRET_KEY=your-paystack-secret-key

# Mula Score
SCORE_ENGINE_VERSION=1
```

---

## Core Features

### Mula for Personal Use
- **Dashboard**: Overview of finances, goals, savings, score, and tips
- **Transactions**: Sync with M-Pesa to view and label expenses
- **Budget**: Smart budget builder with the 50/30/20 rule, income and expense tracking
- **AI Coach**: Interactive chat with Mula's Smart Budget Agent for personalized financial guidance
- **Goals**: Track financial goals like an emergency fund, school fees, and more
- **Mula Score**: A living financial health score with a clear explanation of every change
- **Chat History**: Persistent conversation history, browse, load, and delete past chats
- **Reminders**: Get alerts for bills, savings, and tasks
- **Savings**: Link M-Shwari, KCB M-Pesa, and Ziidi for live savings updates
- **Learn Page**: Financial literacy with an interactive AI tutor
- **Settings**: Profile, preferences, plan, and subscription management

### Mula for Business (Coming Soon)
- Cash flow dashboards
- Expense categorization and insights
- AI-powered financial forecasting
- Custom analytics based on business type
- Business credit readiness score
- Team collaboration and reports

---

## Mula Score

Most people only learn about their credit standing when a loan is declined. Mula flips that. The **Mula Score** is a behavior-based financial health score that updates as you make decisions, so you can see the effect of a good choice the moment you make it.

> **Important:** The Mula Score is an educational, behavior-based score. It is **not** a credit bureau score (such as TransUnion, Metropol, or Creditinfo in Kenya) and does not replace one. Future phases may add bureau data and lender-facing reports with explicit user consent.

### The Idea

1. You make a money decision (pay a bill early, hit a savings target, stay within budget).
2. Mula detects it from your transactions, budget, and goals.
3. Your score moves, and Mula shows exactly why: *"+6 points: You paid your KPLC bill 3 days before the due date."*
4. The AI Coach explains what to do next to keep improving.

### Score Range and Tiers

The score runs from **300 to 850**, split into tiers:

| Tier | Range | Meaning |
|------|-------|---------|
| Building | 300 – 499 | Early stage. Small, consistent habits make the biggest difference. |
| Fair | 500 – 579 | Some good habits, with clear room to grow. |
| Good | 580 – 669 | Steady habits and manageable debt. |
| Strong | 670 – 739 | Reliable repayment and healthy savings. |
| Excellent | 740 – 850 | Highly disciplined, lender-ready behavior. |

New users start with a baseline score once they have at least **30 days** of synced data. Until then, Mula shows a "Score warming up" progress state instead of a number.

### Score Factors

| Factor | Weight | What Mula Looks At |
|--------|--------|--------------------|
| **Payment Consistency** | 30% | On-time bills, loan repayments, and subscription payments |
| **Savings Behavior** | 25% | Regular contributions, emergency fund progress, goal completion |
| **Spending Discipline** | 20% | Budget adherence, wants vs needs ratio, impulse spending patterns |
| **Debt Management** | 15% | Debt-to-income ratio, repayment pace, reliance on mobile loans such as Fuliza |
| **Financial Stability** | 10% | Income regularity, account activity, balance buffer |

Weights are versioned (`SCORE_ENGINE_VERSION`) so changes are transparent and past scores can be explained.

### Decision Impact Feed

Every score change is recorded as a **score event**. Examples:

| Decision | Example Impact |
|----------|----------------|
| Paid a bill before its due date | +4 to +8 |
| Hit a monthly savings target | +10 |
| Stayed within budget for a full month | +12 |
| Cleared a loan earlier than scheduled | +15 |
| Used Fuliza repeatedly in one month | -6 |
| Missed a bill or loan due date | -10 to -20 |
| Overspent a category beyond the budget | -4 |

Impact values are illustrative and are tuned through the scoring engine configuration.

### What-If Simulator

Before acting, users can ask: *"What happens to my score if I clear my Fuliza balance this week?"* The simulator runs the same scoring engine on a hypothetical change and returns the projected impact, so people can compare decisions before committing.

### AI Coach Integration

The score engine is **deterministic**: calculations happen in the backend using transparent rules. The AI (Nova Lite) only **narrates and coaches** around the numbers. It never invents or changes a score.

Example coaching:
- *"Your score rose 18 points this month, mostly from consistent savings. Your biggest opportunity now is reducing Fuliza use."*
- *"Clearing your M-Shwari loan 2 weeks early could add roughly 10 to 15 points."*

### Privacy, Consent, and Compliance

- Score data is used only with the user's explicit consent
- Users can view, export, or delete their score history at any time
- No score data is shared with third parties or lenders without opt-in consent
- Designed with Kenya's **Data Protection Act, 2019** in mind, with data minimization and purpose limitation
- Any move toward lender-facing credit products should be reviewed against **CBK digital credit** regulations and CRB requirements before launch

### Planned Score Phases

| Phase | Focus |
|-------|-------|
| **Phase 1** | Rule-based score from M-Pesa transactions, budgets, goals, and reminders. History chart and decision feed. |
| **Phase 2** | What-if simulator, score-linked goals and challenges, AI Coach explanations. |
| **Phase 3** | Opt-in sharing of a verified score report, partner lender pilots, bureau data enrichment. |
| **Phase 4** | Business credit readiness score, regional expansion beyond Kenya. |

---

## Smart Budget Agent

Mula includes an intelligent **Smart Budget Agent** that builds a complete personal budget plan interactively.

### How It Works

The agent follows a structured 5-step process, showing calculations after every answer:

| Step | What Happens |
|------|-------------|
| 1. **Income** | You tell the agent your monthly take-home income. It calculates 50/30/20 targets live. |
| 2. **Fixed Expenses** | You share rent, utilities, transport, loans. The agent tracks running totals against your needs budget. |
| 3. **Variable Expenses** | You discuss food, entertainment, shopping. The agent shows the remaining wants budget. |
| 4. **Savings & Goals** | The agent helps allocate savings toward an emergency fund, goals, or debt repayment. |
| 5. **Budget Plan** | A beautifully formatted complete budget plan is presented with category breakdown, totals, and surplus. |

### Key Behaviors
- Shows running math after each input: ✅ recorded + remaining budget
- Adapts to your currency (KES, NGN, USD, etc.)
- Detects debt and prioritizes repayment
- Recommends emergency fund building
- Handles overspending by suggesting cuts to wants, not needs
- Asks one question at a time for a natural conversation flow
- Shows how budget decisions affect your Mula Score

### Visual Progress Tracker
When chatting with the agent, a 5-stage progress bar shows your current position:
```
💰 Income → 📊 Fixed Expenses → 🛒 Variable Expenses → 🎯 Savings → 📋 Budget Plan
```
Completed stages light up green as you progress.

---

## AI Assistant Architecture

### Provider System
Mula supports pluggable AI providers. The provider is selected via the `AI_PROVIDER` env var:

| Provider | `AI_PROVIDER` value | Description |
|----------|-------------------|-------------|
| **AWS Bedrock Nova** | `bedrock` | Primary provider: Nova Lite (reasoning) + Nova Micro (speed) with strict rate limiting |
| **Local Fallback** | anything else | Keyword-based responses for testing and offline use |

### Bedrock Nova Routing
Tasks are automatically routed to the optimal model:

| Model | Used For | RPM Limit | Cost (per 1K tokens) |
|-------|----------|-----------|---------------------|
| **Nova Lite** | Financial advice, budget planning, chat, transaction analysis, score coaching | 50 | Input: $0.000060, Output: $0.000240 |
| **Nova Micro** | Spending categorization, quick lookups | 50 | Input: $0.000035, Output: $0.000140 |

### Rate Limiting
- Per-model token bucket rate limiters (50 RPM each)
- Exponential backoff with jitter on throttling (max 5 retries)
- Request timeout: 30 seconds

### Planned Tasks
The assistant recognizes the following task types:
- `chat`: General Q&A
- `budget_planning`: Interactive budget building (Smart Budget Agent)
- `financial_advice`: Personalized coaching and recommendations
- `transaction_analysis`: Spending pattern analysis
- `mpesa_assistance`: M-Pesa transaction guidance
- `payment_recommendations`: Secure payment advice
- `spending_category`: Transaction categorization
- `insight`: Quick personalized financial insight
- `score_coaching`: Explains score changes and suggests next steps (narration only, never calculates)

---

## Integrations (In Progress)
- **M-Pesa**: Transaction syncing
- **AWS Bedrock**: AI chat via Amazon Nova (Lite + Micro) with strict rate limiting and cost controls
- **Paystack**: Payment processing
- **Google OAuth**: Social login
- **Ziidi / KCB M-Pesa / M-Shwari**: Savings and investments
- **Credit Reference Bureaus** (planned): Optional, consent-based data enrichment for the Mula Score

---

## How It Works

1. **User signs up** (email or Google)
2. **Profile setup** to customize the experience
3. **Data sync**: Transactions pulled, labeled, categorized
4. **User selects or builds a budget plan** using the Smart Budget Agent
5. **Mula AI assistant** gives tips, reminders, and updates via conversation
6. **Mula Score** is calculated from behavior and updates after meaningful decisions
7. **User tracks savings goals**, receives reports and feedback
8. **Chat history** is saved so any past conversation can be revisited

---

## Project Structure

```bash
/
├── src/                    # React frontend
│   ├── components/         # UI components
│   │   ├── DashboardLayout.tsx
│   │   ├── CollapsibleSidebar.tsx
│   │   └── score/          # ScoreGauge, FactorBreakdown, DecisionFeed
│   ├── pages/              # Page components
│   │   ├── BudgetPage.tsx  # Budget tab + AI Coach with Smart Budget Agent
│   │   ├── ChatPage.tsx    # Full AI Coach with conversation history sidebar
│   │   ├── ScorePage.tsx   # Mula Score: gauge, history, factors, simulator
│   │   └── ...
│   ├── lib/
│   │   └── api.ts          # API client with auth headers
│   └── contexts/
│       └── AuthContext.tsx # Authentication state
│
├── public/                 # Static assets (favicon)
│
├── backend/
│   └── hela_backend/
│       ├── door/
│       │   ├── settings.py       # Legacy monolithic settings
│       │   └── settings/         # Settings package (base, development, production, testing)
│       │       ├── base.py
│       │       └── development.py
│       ├── users/                # User management + auth views
│       ├── ai_assistant/         # AI assistant app
│       │   ├── models.py         # Conversation, Message, AIInsight, FinancialGoal
│       │   ├── views.py          # Chat, analysis, conversation CRUD endpoints
│       │   ├── serializers.py
│       │   ├── urls.py
│       │   └── services/
│       │       ├── bedrock_client.py        # Bedrock Nova integration + rate limiting
│       │       └── conversation_manager.py  # Conversation orchestration + fallback
│       ├── credit_score/         # Mula Score app
│       │   ├── models.py         # ScoreSnapshot, ScoreEvent, ScoreFactor
│       │   ├── views.py          # Score, history, factors, events, simulate endpoints
│       │   ├── tasks.py          # Celery: scheduled and event-triggered recalculation
│       │   └── services/
│       │       ├── scoring_engine.py   # Deterministic, versioned scoring rules
│       │       ├── event_detector.py   # Turns transactions and budgets into score events
│       │       └── simulator.py        # What-if projections
│       ├── transactions/         # Transaction management
│       ├── financial_planning/   # Budget, SavingsPlan, Expense, Income models
│       ├── payments/             # Paystack integration
│       └── .env.example
│
├── .env.example             # Frontend env template
├── .gitignore
├── tech.md
└── README.md
```

---

## API Documentation

### Authentication Endpoints
- `POST /api/v1/auth/register`: User registration
- `POST /api/v1/auth/login`: User login (returns JWT tokens)
- `POST /api/v1/auth/google`: Google OAuth sign-in
- `POST /api/v1/auth/logout`: Invalidate refresh token
- `POST /api/v1/auth/token/refresh`: Refresh JWT access token
- `GET /api/v1/auth/profile`: Get user profile
- `PUT /api/v1/auth/profile/update`: Update profile

### AI Assistant Endpoints
- `POST /api/v1/assistant/chat`: Chat with Mula AI (supports `budget_planning`, `financial_advice`, `score_coaching`, and `chat`)
- The chat endpoint accepts `{ "message": "...", "conversation_id": null, "task_type": "chat" }` and requires a bearer access token.
- Other assistant endpoints are planned.

### Mula Score Endpoints (Planned)
- `GET /api/v1/score/`: Current score, tier, and change since last period
- `GET /api/v1/score/history/`: Score snapshots over time for charting
- `GET /api/v1/score/factors/`: Breakdown by factor with per-factor status
- `GET /api/v1/score/events/`: Decision impact feed (what moved the score and why)
- `POST /api/v1/score/simulate/`: What-if projection for a hypothetical decision
- `GET /api/v1/score/report/`: Exportable score report (opt-in sharing in later phases)
- `DELETE /api/v1/score/data/`: Delete score history (user data control)

### Budget & Financial Planning Endpoints
- `GET /api/v1/financial/budgets`: List budgets
- `POST /api/v1/financial/budgets/create`: Create a budget
- `GET /api/v1/financial/budgets/{id}`: Budget details with categories

The interactive API reference is available at `/docs`; the liveness endpoint is `GET /health`.
- `GET /api/v1/financial/savings/`: List savings plans
- `POST /api/v1/financial/savings/create/`: Create savings plan
- `GET /api/v1/financial/expenses/`: List expenses
- `POST /api/v1/financial/expenses/create/`: Record an expense
- `GET /api/v1/financial/incomes/`: List income entries
- `POST /api/v1/financial/incomes/create/`: Record income

### Transaction Endpoints
- `GET /api/v1/transactions/`: Get user transactions
- `POST /api/v1/transactions/`: Create new transaction
- `GET /api/v1/transactions/summary/`: Get transaction summary

---

## Roadmap

- [x] Smart Budget Agent with 5-step flow
- [x] Persistent AI chat history
- [x] Bedrock Nova routing with rate limiting
- [ ] M-Pesa live transaction sync
- [ ] **Mula Score Phase 1**: rule-based score, history, decision feed
- [ ] **Mula Score Phase 2**: what-if simulator and score-linked challenges
- [ ] Mula for Business
- [ ] **Mula Score Phase 3**: opt-in verified reports and lender pilots
- [ ] Regional expansion beyond Kenya

---

## Development

### Running Tests
```bash
# Backend tests (from backend/hela_backend)
cd backend
pytest
```

### Code Quality
```bash
# Frontend linting
pnpm lint

# Backend formatting
cd backend
black .
isort .
flake8
```

### Database Management
Production Alembic migration setup is pending. Development automatically creates tables in SQLite.

---

## Deployment

### Docker Deployment
```bash
docker-compose up -d
docker-compose logs -f
docker-compose down
```

### Production Setup
1. **Environment Configuration**
   - Set `DEBUG=False`
   - Configure production database (Neon PostgreSQL recommended)
   - Set up Redis for caching
   - Configure AWS Bedrock credentials for AI features

2. **Static Files**
   ```bash
   # Serve FastAPI with an ASGI server such as Uvicorn.
   ```

3. **Database**
   ```bash
   # Production database migration setup is pending.
   ```

4. **Start Services**
   ```bash
   uvicorn main:app --app-dir backend/hela_backend --host 0.0.0.0 --port 8000
   ```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the MIT License. See the LICENSE file for details.

## Support

For support and questions:
Contact details will be published when Mula launches.

---

**Built with ❤️ for Kenya and the world**
