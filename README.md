# My Finance — Personal Finance Tracker

A Django-powered personal finance management dashboard for tracking expenses, recurring obligations (EMIs/subscriptions), and personal loans — all wrapped in a premium glassmorphism "Vault Glass" dark-theme UI.

## Features

### Dashboard
- **Stat cards** — total spent, total income, pending dues, net balance with month-over-month trends
- **Trend line chart** — 12-month cash flow visualization (SVG-based, server-rendered)
- **Category breakdown donut** — colour-coded expense distribution by category
- **Upcoming recurring dues** — next-due items with radial progress rings (EMIs) or due-date indicators (subscriptions)
- **Loan portfolio snapshot** — owed-to-you vs. you-owe aggregates with repayment progress bars

### Expense Tracking
- CRUD for transactions (income/expense) with categories, notes, and date
- Custom category management with colour picker
- Recurring item support — EMIs, subscriptions, and yearly renewals, unified in one model
- Cycle-by-cycle payment tracking (`recurring_payments`) linked to transactions
- One-click "mark as paid" that creates the transaction + updates payment status

### Loan/Lending Management
- Contact address book
- Full loan lifecycle — log money given or taken, track repayments
- Auto-calculated settlement status (open → partially settled → settled)
- Per-contact net balance (who owes whom)

### UI/UX
- **Vault Glass design system** — frosted-glass panels with animated gradient mesh backdrop
- **Dark theme** with a glassmorphism aesthetic (blur + inset highlights + drop shadows)
- **Responsive** — sidebar collapses on tablet, full mobile card layout below 640px
- **Flatpickr** date picker with custom glass-themed dark styling
- **Canvas bar chart** and **SVG trend line** for data visualization
- **Counter animations** on dashboard stat values
- **Hover tooltips** on collapsed sidebar items
- Reduced-motion support via `prefers-reduced-motion`

### Security
- Row-level multi-tenancy — every model scoped by `user_id`
- Global login-required middleware (whitelist exempt paths)
- 3-hour inactivity timeout with sliding session expiry
- Custom obscured cookie names (`billing_sessionid`, `billing_csrftoken`)
- HSTS, X-Frame-Options, Content-Type sniffing protection
- Secure proxy header handling for Cloudflare/TLS termination
- Router-friendly admin URL via `ADMIN_URL` env var

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, Django 5.2 |
| Database | PostgreSQL (production), SQLite (tests, in-memory) |
| Frontend | Django Templates, vanilla CSS/JS |
| Fonts | Space Grotesk (headings), Inter (body), JetBrains Mono (numbers) |
| Icons | Material Symbols Outlined (Google Fonts) |
| Date picker | Flatpickr (CDN) |
| PDF generation | WeasyPrint (for invoice/report export) |
| Config management | python-decouple (`.env` file) |

## Project Structure

```
Finance/
├── Finance/                  # Django project settings
│   ├── settings.py           # Config, DB, security, logging
│   ├── urls.py               # Root URL routing
│   └── wsgi.py / asgi.py
├── base/                     # Auth, dashboard, middleware, utilities
│   ├── views.py              # home_view (dashboard), CustomLoginView, logout
│   ├── models.py             # (uses Django's built-in auth)
│   ├── middleware.py          # LoginRequiredMiddleware
│   ├── forms.py              # CustomLoginForm
│   ├── custom_filters.py     # Template filters (currency, currency_abbreviation)
│   ├── manager.py            # SoftDeleteModel base
│   └── utility.py            # StringProcessor helper
├── expense/                  # Expense tracking app
│   ├── models.py             # Category, Transaction, RecurringItem, RecurringPayment
│   ├── views.py              # CRUD + recurring payment toggling
│   ├── forms.py
│   └── managers.py
├── ledger/                   # Loan/contact management app
│   ├── models.py             # Contact, Transaction, TransactionPayment
│   ├── views.py              # CRUD + payment logging
│   └── forms.py
├── user/                     # Custom user model
│   └── models.py             # CustomUser (phone_number, full_name)
├── templates/                # Shared templates
│   ├── base.html             # Root layout (sidebar, topbar, mesh bg, scripts)
│   └── _navigation.html      # Sidebar nav with sections
├── static/
│   ├── css/
│   │   ├── style.css         # Main design system (~3400 lines)
│   │   └── login.css         # Login page styles
│   └── js/
│       ├── script.js         # Sidebar, alerts, dashboard logic, chart, inputs
│       ├── login.js          # Login form interactions
│       ├── fetchData.js      # HTMX/API data fetching utilities
│       └── pages/
│           └── dashboard.js  # Dashboard-specific chart rendering
├── design_guide.md           # Full frontend design specification
├── finance_tracker_schema.md # Database schema documentation
├── require.txt               # Python dependencies
├── .env                      # Environment variables (SECRET_KEY, DB creds, etc.)
└── manage.py
```

## Database Schema

```
users (Django auth)
  ├── categories          — user-defined expense categories with colour
  ├── transactions        — income/expense ledger (expense app)
  ├── recurring_items     — EMIs, subscriptions, renewals (unified)
  │     └── recurring_payments  — one row per due cycle
  ├── contacts            — personal address book
  │     └── transactions  — loans (given/taken) with status tracking
  │           └── transaction_payments — repayment events
```

See `finance_tracker_schema.md` for full schema documentation and design rationale.

## Getting Started

### Prerequisites

- Python 3.10+
- PostgreSQL 14+
- Virtual environment (recommended)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd Finance

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r require.txt

# Configure environment
cp .env.example .env  # if you have a template; otherwise create .env manually
# Edit .env with your SECRET_KEY, DB credentials, etc.

# Run migrations
python manage.py migrate

# Create a superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic --noinput

# Start the development server
python manage.py runserver 0.0.0.0:8000
```

### Environment Variables (`.env`)

| Variable | Required | Default | Description |
|---|---|---|---|
| `SECRET_KEY` | Yes | — | Django secret key |
| `DEBUG` | Yes | `False` | Debug mode (set `True` for dev) |
| `ALLOWED_HOSTS` | Yes | `localhost,127.0.0.1` | Comma-separated hostnames |
| `DB_NAME` | Yes | — | PostgreSQL database name |
| `DB_USER` | Yes | — | PostgreSQL username |
| `DB_PASSWORD` | Yes | — | PostgreSQL password |
| `DB_HOST` | Yes | `127.0.0.1` | PostgreSQL host |
| `DB_PORT` | No | `5432` | PostgreSQL port |
| `ADMIN_URL` | No | `admin/` | Custom admin panel path |
| `CSRF_TRUSTED_ORIGINS` | No | — | Comma-separated trusted origins |
| `SECURE_SSL_REDIRECT` | No | `not DEBUG` | Force HTTPS redirect |
| `SESSION_COOKIE_SECURE` | No | `False` | Secure cookie flag |
| `CSRF_COOKIE_SECURE` | No | `False` | Secure CSRF cookie flag |

### Running Tests

```bash
python manage.py test
```

Tests use an in-memory SQLite database — no PostgreSQL needed.

## Deployment

### Production Checklist

1. Set `DEBUG=False` in `.env`
2. Generate a strong `SECRET_KEY`
3. Set `ALLOWED_HOSTS` to your domain(s)
4. Configure `CSRF_TRUSTED_ORIGINS` for your HTTPS domain
5. Set `SECURE_SSL_REDIRECT=True` if behind TLS termination (Cloudflare, Nginx)
6. Run `python manage.py collectstatic --noinput` and serve `staticfiles/` via Nginx/CDN
7. Use a production-grade WSGI server (Gunicorn + Nginx, or uWSGI)
8. Set `ADMIN_URL` to a non-guessable path
9. Ensure PostgreSQL is configured with strong credentials

### Example Gunicorn Command

```bash
gunicorn Finance.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120 \
  --access-logfile /var/log/finance/access.log \
  --error-logfile /var/log/finance/error.log
```

### Nginx Static Files

```nginx
location /static/ {
    alias /path/to/Finance/staticfiles/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location /media/ {
    alias /path/to/Finance/media/;
}
```

### Logging

Logs are written to `logs/` directory with rotation:
- `debug.log` — DEBUG-level messages (10 MB, 5 backups)
- `info.log` — INFO-level messages (10 MB, 5 backups)
- `error.log` — ERROR-level messages (10 MB, 5 backups)
- `security.log` — Django security warnings (10 MB, 10 backups)

## Design Principles

1. **Row-level multi-tenancy** — every table has `user_id`; querysets filter by `request.user`
2. **Unified recurring model** — EMIs, subscriptions, and renewals share one table (`recurring_items`)
3. **Rule vs. history separation** — `recurring_items` describes the rule, `recurring_payments` records what happened
4. **Debts ≠ spending** — loans are asset/liability, not income/expense; they live in their own tables
5. **Glassmorphism everywhere** — consistent frosted-glass panels, blur, inset highlights, and the animated gradient mesh backdrop
6. **Utility-first CSS** — standardized utility classes (.text-12, .d-flex, .gap-12, etc.) eliminate inline styles across templates

## Browser Support

| Browser | Status |
|---|---|
| Chrome 90+ | Fully supported |
| Firefox 90+ | Fully supported |
| Safari 15+ | Fully supported |
| Edge 90+ | Fully supported |
| Mobile Safari (iOS 15+) | Supported (mobile card layout) |
| Chrome Android | Supported (mobile card layout) |

`backdrop-filter` is used for the glass effect — older browsers will see a solid dark background fallback.

## License

Private project — contact the repository owner for usage rights.
