# WagnerFit Backend (FastAPI + Supabase + Stripe)

Production-grade FastAPI backend implementing the WagnerFit PRD: ebooks, programs, posts, metrics, affiliate store, admin analytics, i18n, logging, rate limiting.

## Quick Start

```bash
# 1) Create folder and venv
cd wagnerfit-backend
python -m venv .venv
# Linux/macOS
source .venv/bin/activate
# Windows PowerShell
# .venv\Scripts\Activate.ps1

# 2) Install
pip install -r requirements.txt

# 3) Configure env
cp .env.example .env
# Fill SUPABASE_URL, SUPABASE_SERVICE_KEY, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET

# 4) Run
uvicorn app.main:app --reload
# Visit http://localhost:8000/healthz → {"status": "ok"}
```

## Project Structure

```
app/
  api/v1/
    deps/
    dto/
    routers/
  core/
  domain/models/
  infra/
    payments/
    supabase/
  services/
    admin/
    affiliate/
    ebooks/
    metrics/
    posts/
    programs/
    users/
  shared/i18n/
 db/schema/
 docs/
 tests/
```

## Tooling

- Black, Ruff, Isort, Mypy configured via `pyproject.toml`.
- Pre-commit hooks: `pre-commit install` then `pre-commit run --all-files`.

## Environment Variables

- See `.env.example`. Pydantic Settings loads `.env` automatically.

## Running Tests

```bash
pytest -q
```

## Docker

```bash
docker build -t wagnerfit-backend .
docker run -p 8000:8000 --env-file .env wagnerfit-backend
```

## API Overview

See `docs/API.md` for endpoint list. All protected routes require Supabase JWT.

## Database Schema

- Apply migrations in order using the Supabase SQL editor:
  - `db/schema/0001_base.sql`
  - `db/schema/0002_rls_policies.sql` (enables RLS and defines policies)
  - `db/schema/0003_storage_buckets.sql` (creates storage buckets + RLS policies)
  - `db/schema/0004_prices.sql` (Stripe Price ID columns)
  - `db/schema/0005_tiers_and_prefs.sql` (membership tiers + user prefs)
  - `db/schema/0006_rls_update_tiers.sql` (private posts require premium)

## Deployment Options

- Fly.io: simple Docker deployment
- Render/Heroku: Docker or buildpack
- Vercel Functions: extract FastAPI routes (or use serverless adapter)

## Notes

- Supabase/Stripe clients are lazy: the app runs locally even without keys; actions that require them will no-op or return stubs.
- Replace the JWT verification stub with Supabase JWKS validation in production.
- Storage policies and path conventions documented in `docs/STORAGE.md`.
