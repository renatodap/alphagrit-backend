**Overview**
- Pattern: API Routers → Service Layer → Infra (Supabase, Stripe) → Database
- Dependency-injected, modular, testable.

**Key Modules**
- `app/api/v1`: Route handlers; thin, call services.
- `app/services/*`: Business logic per domain.
- `app/infra/*`: External clients (Supabase, Stripe).
- `app/core/*`: Config, logging, errors, rate limiting.
- `app/shared/i18n`: Localization.
- `db/schema`: SQL migrations for Supabase.

**Request Lifecycle**
- Middlewares: CORS → Rate limit → Request logger
- Handlers return data or raise; errors wrapped into standard envelope.

**Auth**
- Supabase JWT via `Authorization: Bearer`.
- Stubbed token parsing; production should verify JWKS.

**Observability**
- Structlog JSON logs with method, path, status, client.

**Rate Limits**
- In-memory per IP+path window; swap to Redis for production.
