# Frontend Contract (WagnerFit)

- Auth: Supabase JWT in `Authorization: Bearer <token>`.
- Base URL: `/api/v1`.
- JSON only; responses use snake_case.
- Errors: `{ "error": { "code": "XYZ", "message": "..." } }` and HTTP status.
- i18n: `Accept-Language: en|pt` (errors/messages reserved for future use).

Key Endpoints

- GET `/ebooks`
  - Response: `Array<{ id, slug, title, description, price_cents, program_id, created_at }>`

- GET `/ebooks/{slug}` (auth)
  - Response: `{ ...ebook, owned: boolean }`

- POST `/ebooks/checkout/ebooks/{id}` (auth)
  - Response: `{ checkout_url: string }`
  - Opens Stripe Checkout; webhook will set purchase to `paid`.

- GET `/programs`
  - Response: `Array<{ id, title, description, banner_url, created_at }>`

- GET `/programs/{id}` (auth)
  - Response: `{ ...program, member: boolean }`

- GET `/programs/{id}/posts` (auth)
  - Response: `Array<Post>`, where `Post = { id, user_id, program_id, message, photo_url, visibility, created_at }`
  - Visibility rules: `public` visible to members; `private` visible to author and admin only.

- POST `/programs/{id}/posts` (auth)
  - Body: `{ message: string, photo_url?: string, visibility?: 'public'|'private' }`
  - Response: `Post`

- GET `/me/metrics` (auth)
  - Response: `Array<{ id, user_id, date, weight, body_fat, photo_url, note, created_at }>`

- POST `/me/metrics` (auth)
  - Body: `{ date: 'YYYY-MM-DD', weight?: number, body_fat?: number, photo_url?: string, note?: string }`
  - Response: created metric

- DELETE `/me/metrics/{id}` (auth)
  - Response: `{ id, deleted: true }`

- GET `/affiliate/products`
  - Response: list of affiliate products

- POST/PUT/DELETE `/affiliate/products*` (admin)
  - Requires `roles` claim containing `admin` in JWT payload.

- Admin Analytics (admin)
  - GET `/admin/analytics/sales` → `{ total_revenue_cents, paid_orders }`
  - GET `/admin/analytics/programs` → `{ memberships }`
  - DELETE `/admin/posts/{id}` → `{ id, deleted: true }`

Stripe Webhook

- POST `/webhooks/stripe` (server-side only)
  - On `checkout.session.completed`, sets matching `purchases.status = 'paid'` and grants `user_programs` membership for program/combo purchases.

Notes

- Supabase RLS should enforce ownership checks in production.
- For local dev without Supabase keys, many endpoints return empty lists or stubs, enabling frontend integration without DB.
