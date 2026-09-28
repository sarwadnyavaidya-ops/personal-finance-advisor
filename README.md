# 💰 Personal Finance Advisor Bot

> **An AI-powered, full-stack personal finance management and advisory platform built with Flask, SQLAlchemy, Chart.js, and Google Gemini AI.**

---

## 🌟 Overview

**Personal Finance Advisor Bot** is a production-ready web application engineered to help individuals and families achieve financial clarity and independence. Unlike static prototypes, this is a fully functional web system featuring secure authentication, income/expense management, automated budget monitoring, emergency fund calculations, multi-goal savings pacing, interactive Chart.js dashboards, and a contextual Google Gemini AI conversational financial advisor.

The application natively supports **four core user personas**:
1. **Salaried Professionals**: Predictable monthly income, rent/mortgage, daily transit, dining, automatic savings allocations.
2. **College Students**: Limited allowance and scholarships, education materials, tight discretionary spending limits.
3. **Freelancers**: Variable multi-client revenue, project expenses, quarterly tax cushions, rainy-day buffers.
4. **Household / Family Managers**: Multi-income tracking, groceries, childcare, schooling, utilities, and consolidated family statements.

---

## 🚀 Key Features

- **🔐 Robust Security & Authentication**:
  - Secure registration, password hashing via Werkzeug (`scrypt`/`pbkdf2`), session cookies with `HttpOnly` and `SameSite=Lax`.
  - Multi-tenant data isolation: strict database-level separation ensures users only ever access their own financial records.
  - XSS protection and SQL injection prevention via SQLAlchemy ORM.
- **📊 Comprehensive Financial Dashboard**:
  - Key financial KPIs: Total Inflow, Total Outflow, Net Cashflow, Retained Savings %, Remaining Budget.
  - **6 Interactive Chart.js Visualizations**:
    1. *Income vs Expense vs Savings* (Bar chart)
    2. *Expense by Category* (Doughnut chart with center cut-out)
    3. *6-Month Cashflow Trend* (Multi-line area chart)
    4. *Cumulative Savings Growth* (Timeline area chart)
    5. *Budget Limits vs Actual Outlay* (Grouped comparison bar chart)
    6. *Financial Goal Progress* (Stacked horizontal progress bar chart)
- **💵 Income Management**:
  - Categorized sources (*Salary, Freelance, Business, Scholarship, Allowance, Investment, Other*).
  - Date filtering, source breakdown, total calculations.
- **🧾 Expense Management & Categorization**:
  - Pre-seeded default categories (*Housing, Rent, Food, Groceries, Transportation, Education, Healthcare, Entertainment, Shopping, Utilities, Bills, Subscriptions, Travel, Personal Care, Other*).
  - Custom category builder (*Essential / Discretionary / Other*).
  - Search, sort by date/amount, recurring bill detection, payment methods.
- **🎯 Budget Planning Engine**:
  - Overall monthly budget envelopes & category-specific limits.
  - Real-time utilization calculation, variance detection, and overspending alerts.
- **💡 AI Advisor & Smart Heuristics**:
  - Powered by **Google Gemini API** (`gemini-2.5-flash` / `gemini-1.5-flash`).
  - **Zero-Failure Architecture**: If `GEMINI_API_KEY` is not supplied, the system seamlessly transitions to an **Intelligent Rule-Based Advisory Engine** calculating exact percentages, burn areas, and the 50/30/20 guideline without crashing.
  - Contextual AI chat answering queries like *"How can I reduce expenses?"*, *"Where am I overspending?"*, and *"How much should I save?"*.
- **❤️ Financial Health Evaluation**:
  - Diagnostic score (out of 100) and status (*Healthy*, *Needs Attention*, *Needs Improvement*).
  - Transparent explanations detailing *why* the score was generated based on savings rate, expense-to-income ratio, runway, and budget discipline.
- **🚨 Overspending Detection & Alerts Engine**:
  - Automated risk scans triggered upon expense entries: budget cap breach (>100%), threshold warnings (>80%), large single transactions, and low savings velocity.
- **🛡️ Emergency Fund Guidance**:
  - Target calculation based on 3–6 months of average monthly expenses.
  - Real-time runway indicator (months of living costs covered).
- **🏆 Multi-Goal Milestones**:
  - Remaining amount, percentage complete, and dynamic calculation of **required monthly savings** needed to hit target deadlines.
  - Direct 1-click goal contributions.
- **📑 Monthly Financial Reports**:
  - Month-over-month monitoring switcher.
  - Structured financial statement with archive history.
  - Print-ready and PDF-optimized layout (`window.print()` with clean `@media print` styling).
- **⚡ RESTful API**:
  - JSON endpoints for `/api/dashboard`, `/api/income`, `/api/expenses`, `/api/budget`, `/api/savings`, `/api/goals`, `/api/alerts`, and `/api/ai/chat`.

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.8+, Flask 3.x, Flask-Login, Flask-WTF, Werkzeug |
| **Database** | SQLite (default development), PostgreSQL-ready via SQLAlchemy ORM |
| **Frontend** | HTML5, CSS3, JavaScript (ES6+), Jinja2, Bootstrap 5.3, Bootstrap Icons |
| **Charts** | Chart.js 4.4 |
| **AI Integration** | Google Gemini API via `google-genai` & REST fallback + Heuristic Engine |
| **Testing** | Pytest 9.x |

---

## 📂 Project Structure

```
personal_finance_advisor/
│
├── app/
│   ├── __init__.py               # Flask application factory, error handlers, context processors
│   ├── extensions.py             # SQLAlchemy db and LoginManager setup
│   ├── models/
│   │   ├── __init__.py           # Model exports
│   │   ├── user.py               # User model, password hashing, profile targets
│   │   └── financial.py          # Income, Expense, Budget, Savings, Goal, Alert, Report, Chat models
│   ├── routes/
│   │   ├── __init__.py           # Route blueprint registrations
│   │   ├── auth.py               # Login, register, logout, profile, scenario switcher
│   │   ├── main.py               # Landing page, main dashboard controller
│   │   ├── income.py             # Income CRUD and source breakdowns
│   │   ├── expense.py            # Expense CRUD, search, category management
│   │   ├── budget.py             # Budget planning, limits, and utilization tracking
│   │   ├── savings.py            # Savings tracking, growth timeline
│   │   ├── goals.py              # Financial goals, contributions, required monthly pace
│   │   ├── analysis.py           # Spending analytics and financial health evaluation
│   │   ├── advisor.py            # AI Advisor chat interface and AJAX endpoints
│   │   ├── reports.py            # Monthly monitoring, statement archive, print/PDF view
│   │   ├── alerts.py             # Financial risk alerts and notifications
│   │   └── api.py                # Comprehensive REST API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   ├── finance_service.py    # Metric aggregations, budget comparisons, health diagnostics
│   │   ├── alert_service.py      # Automated overspending and threshold detection
│   │   └── demo_service.py       # Multi-scenario sample data generator
│   ├── ai/
│   │   ├── __init__.py
│   │   └── gemini_service.py     # Gemini API client with smart heuristic fallback engine
│   ├── utils/
│   │   ├── __init__.py
│   │   └── helpers.py            # Currency formatters, date parsers, category seeders
│   ├── templates/
│   │   ├── base.html             # FinTech layout with responsive navigation & sidebar
│   │   ├── auth/                 # login.html, register.html, profile.html
│   │   ├── dashboard/            # index.html (Main Dashboard), landing.html (Public Home)
│   │   ├── income/               # index.html, edit.html
│   │   ├── expense/              # index.html, edit.html
│   │   ├── budget/               # index.html
│   │   ├── savings/              # index.html, edit.html
│   │   ├── goals/                # index.html, edit.html
│   │   ├── analysis/             # spending.html, health.html
│   │   ├── advisor/              # chat.html
│   │   ├── reports/              # index.html, print_view.html
│   │   ├── alerts/               # index.html
│   │   └── errors/               # 403.html, 404.html, 500.html
│   └── static/
│       ├── css/style.css         # Modern FinTech design system
│       └── js/
│           ├── main.js           # Client UI interactions
│           ├── charts.js         # 6 Chart.js dashboard initializers
│           └── chat.js           # Real-time AJAX chat client
│
├── tests/
│   ├── conftest.py               # Fixtures, test client, user seeds
│   ├── test_auth.py              # Auth, registration, hashing, profile tests
│   ├── test_finance_crud.py      # Income, expense, savings, goal CRUD tests
│   ├── test_budget_engine.py     # Budget calculation and alert trigger tests
│   ├── test_isolation.py         # Multi-tenant cross-user security isolation tests
│   ├── test_ai_service.py        # Gemini service and heuristic calculation tests
│   └── test_api_routes.py        # REST API endpoint tests
│
├── instance/                     # Local SQLite database (finance.db)
├── run.py                        # Local execution server entrypoint
├── seed_demo.py                  # CLI demo data populator for all 4 scenarios
├── verify_e2e.py                 # Automated 20-point end-to-end integration verifier
├── requirements.txt              # Production and development dependencies
├── .env                          # Local environment variables
├── .env.example                  # Environment configuration template
├── .gitignore                    # Git ignore file
└── README.md                     # Documentation
```

---

## ⚡ Installation & Quick Start

### 1. Clone or Navigate to Project
```bash
cd personal_finance_advisor
```

### 2. Set Up a Virtual Environment
```bash
# macOS/Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Edit `.env` as desired:
```ini
SECRET_KEY=your-secure-random-secret-key
DATABASE_URL=sqlite:///finance.db
GEMINI_API_KEY=your_gemini_api_key_here  # Optional: app works with heuristic fallback if empty
FLASK_ENV=development
DEBUG=True
```

### 5. Seed Realistic Demo Data (Optional but Recommended)
You can populate data for any of the 4 user scenarios using the CLI:
```bash
# Available scenarios: salaried, student, freelancer, household
python seed_demo.py salaried
```
*Default Demo Credentials:*
- **Email**: `demo@example.com`
- **Password**: `password123`

### 6. Run the Application Locally
```bash
python run.py
```
Open your browser and navigate to:
👉 **`http://127.0.0.1:5000`**

---

## 🧪 Running the Automated Test Suite

Run pytest to verify all authentication, CRUD, tenant isolation, budget calculations, and REST APIs:

```bash
python -m pytest -v
```

All 15 automated test suites pass with 100% success rate:
- `test_auth.py`
- `test_finance_crud.py`
- `test_budget_engine.py`
- `test_isolation.py` (Verifies User A cannot access User B's records)
- `test_ai_service.py` (Verifies Gemini & Heuristic fallback)
- `test_api_routes.py` (Verifies JSON REST APIs)

To run the 20-point live end-to-end verifier:
```bash
python verify_e2e.py
```

---

## 🌐 Production Deployment

### 1. PostgreSQL Database Configuration
To switch from SQLite to PostgreSQL in production, update `DATABASE_URL` in `.env`:
```ini
DATABASE_URL=postgresql://username:password@localhost:5432/finance_db
```
SQLAlchemy handles the abstraction automatically without code changes.

### 2. WSGI Server Deployment

#### Linux / macOS (Gunicorn)
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app('production')"
```

#### Windows (Waitress)
```bash
pip install waitress
waitress-serve --port=8000 "run:app"
```

#### Systemd Service Template (`/etc/systemd/system/finance-advisor.service`)
```ini
[Unit]
Description=Personal Finance Advisor Bot
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/personal_finance_advisor
Environment="PATH=/var/www/personal_finance_advisor/venv/bin"
EnvironmentFile=/var/www/personal_finance_advisor/.env
ExecStart=/var/www/personal_finance_advisor/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 "app:create_app('production')"
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## ⚠️ Financial Safety & Educational Disclaimer

> **IMPORTANT**: Personal Finance Advisor Bot is an educational and personal financial tracking platform.
> - Recommendations generated by Gemini AI or the heuristic engine are for **informational and educational purposes only** and do not constitute formal investment, tax, legal, or professional financial advice.
> - The application does not execute trades, wire transfers, or financial transactions.
> - Users should exercise due diligence and consult certified financial planners (CFP) for specific tax or investment decisions.
