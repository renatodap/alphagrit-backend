# Supabase Storage Buckets & Policies

Buckets

- `post-photos` (private)
  - Path: `program_{program_id}/user_{user_uuid}/post_{post_id}/<filename>`
  - Read: admin OR program member AND post is `public`, or author
  - Write: author only, must be program member
  - Update/Delete: author or admin

- `metrics-photos` (private)
  - Path: `user_{user_uuid}/metric_{metric_id}/<filename>`
  - Read/Write/Update/Delete: owner or admin

Apply Policies

- Run migrations in Supabase SQL editor in order:
  1. `db/schema/0001_base.sql`
  2. `db/schema/0002_rls_policies.sql`
  3. `db/schema/0003_storage_buckets.sql`

Uploading From Frontend

- Use Supabase JS client with the authenticated user session.
- Ensure you write to the exact path expected by policies.
- Examples:

  - Public post photo (still private bucket, but readable by members):
    - Bucket: `post-photos`
    - Key: `program_42/user_{user.id}/post_{postId}/image.jpg`

  - Private post photo (only author/admin can read):
    - Same bucket and path; visibility is enforced by DB via the `posts` row

  - Metrics photo:
    - Bucket: `metrics-photos`
    - Key: `user_{user.id}/metric_{metricId}/image.jpg`

Notes

- Enforced via SQL functions that parse IDs from object names; keep naming convention consistent.
- For pre-upload (when `post_id` is unknown), you can upload to a temp path and move the object after creating the `posts` row, or create the post first and then upload.
- Signed URLs are still supported; they will obey the same RLS.
