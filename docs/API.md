# WagnerFit Backend API (v1)

- Base URL: `/api/v1`
- Auth: All non-webhook endpoints require `Authorization: Bearer <jwt>` from Supabase.
- i18n: Set `Accept-Language: en` or `pt` to localize error messages.

Endpoints

- Health
  - `GET /healthz` → `{ "status": "ok" }`
  - `GET /readyz` → `{ "ready": true }`

- Webhooks
  - `POST /api/v1/webhooks/stripe` → `{ received: true }`

- Users
  - `GET /api/v1/users/me`
  - `PUT /api/v1/users/me` (partial profile)

- Ebooks
  - `GET /api/v1/ebooks` → list
  - `GET /api/v1/ebooks/{slug}` → details + ownership
  - `POST /api/v1/ebooks/checkout/ebooks/{ebook_id}` → checkout
  - `POST /api/v1/ebooks/checkout/combo/{ebook_id}?tier=standard|premium` → combo checkout (ebook + linked program)

- Programs
  - `GET /api/v1/programs` → list
  - `GET /api/v1/programs/{id}` → details + membership
  - `GET /api/v1/programs/{id}/posts` → feed (public + private)
  - `POST /api/v1/programs/{id}/posts` → create post
  - `POST /api/v1/programs/{id}/checkout?tier=standard|premium` → program checkout

- Metrics (Me)
  - `GET /api/v1/me/metrics` → list
  - `POST /api/v1/me/metrics` → create
  - `DELETE /api/v1/me/metrics/{metric_id}` → delete

- Uploads
  - `POST /api/v1/uploads/posts` → `{ program_id, post_id, filename }` → `{ bucket, path, signed_url? }`
  - `POST /api/v1/uploads/metrics` → `{ metric_id, filename }` → `{ bucket, path, signed_url? }`
  - `GET /api/v1/uploads/download?bucket=...&path=...` → `{ bucket, path, signed_url? }`
  - `POST /api/v1/waitlist` → `{ email, language }` → creates or 409 if exists
  - Signed URLs may not be available; fallback to authenticated uploads with returned `bucket`/`path`.

- Affiliate
  - `GET /api/v1/affiliate/products`
  - `POST /api/v1/affiliate/products` (admin)
  - `PUT /api/v1/affiliate/products/{id}` (admin)
  - `DELETE /api/v1/affiliate/products/{id}` (admin)

- Admin
  - `GET /api/v1/admin/analytics/sales`
  - `GET /api/v1/admin/analytics/programs`
  - `DELETE /api/v1/admin/posts/{id}`

Errors

- Standardized as `{ "error": { "code": "XYZ", "message": "..." } }`
