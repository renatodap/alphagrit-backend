-- Supabase Storage buckets and RLS policies for media
-- Ensure admin helper exists (idempotent; matches definition in 0002_rls_policies.sql)
create or replace function auth_is_admin()
returns boolean
language sql
security definer
set search_path = public
stable
as $$
  select exists (
    select 1 from user_profiles up
    where up.user_id = auth.uid() and coalesce(up.is_admin, false) = true
  );
$$;
-- Buckets
insert into storage.buckets (id, name, public)
values ('post-photos', 'post-photos', false)
on conflict (id) do nothing;

insert into storage.buckets (id, name, public)
values ('metrics-photos', 'metrics-photos', false)
on conflict (id) do nothing;

-- Helpers to parse IDs from object path
-- post-photos path: program_{program_id}/user_{user_uuid}/post_{post_id}/filename
create or replace function storage_post_program_id(name text)
returns bigint
language sql
immutable
as $$
  select nullif(regexp_replace(split_part(name,'/',1), '^program_',''), '')::bigint
$$;

create or replace function storage_post_user_uuid(name text)
returns uuid
language sql
immutable
as $$
  select nullif(regexp_replace(split_part(name,'/',2), '^user_',''), '')::uuid
$$;

create or replace function storage_post_id(name text)
returns bigint
language sql
immutable
as $$
  select nullif(regexp_replace(split_part(name,'/',3), '^post_',''), '')::bigint
$$;

-- metrics-photos path: user_{user_uuid}/metric_{metric_id}/filename
create or replace function storage_metric_user_uuid(name text)
returns uuid
language sql
immutable
as $$
  select nullif(regexp_replace(split_part(name,'/',1), '^user_',''), '')::uuid
$$;

create or replace function storage_metric_id(name text)
returns bigint
language sql
immutable
as $$
  select nullif(regexp_replace(split_part(name,'/',2), '^metric_',''), '')::bigint
$$;

-- Policies for storage.objects
-- POST PHOTOS
drop policy if exists "post photos select" on storage.objects;
create policy "post photos select" on storage.objects for select to authenticated
  using (
    bucket_id = 'post-photos'
    and (
      auth_is_admin()
      or (
        exists (
          select 1 from user_programs up
          where up.user_id = auth.uid() and up.program_id = storage_post_program_id(name)
        )
        and exists (
          select 1 from posts p
          where p.id = storage_post_id(name)
            and (
              p.visibility = 'public' or p.user_id = auth.uid() or auth_is_admin()
            )
        )
      )
    )
  );

drop policy if exists "post photos insert" on storage.objects;
create policy "post photos insert" on storage.objects for insert to authenticated
  with check (
    bucket_id = 'post-photos'
    and storage_post_user_uuid(name) = auth.uid()
    and exists (
      select 1 from user_programs up
      where up.user_id = auth.uid() and up.program_id = storage_post_program_id(name)
    )
  );

drop policy if exists "post photos update" on storage.objects;
create policy "post photos update" on storage.objects for update to authenticated
  using (
    bucket_id = 'post-photos'
    and (auth_is_admin() or storage_post_user_uuid(name) = auth.uid())
  ) with check (
    bucket_id = 'post-photos'
    and (auth_is_admin() or storage_post_user_uuid(name) = auth.uid())
  );

drop policy if exists "post photos delete" on storage.objects;
create policy "post photos delete" on storage.objects for delete to authenticated
  using (
    bucket_id = 'post-photos'
    and (auth_is_admin() or storage_post_user_uuid(name) = auth.uid())
  );

-- METRICS PHOTOS
drop policy if exists "metrics photos select" on storage.objects;
create policy "metrics photos select" on storage.objects for select to authenticated
  using (
    bucket_id = 'metrics-photos'
    and (auth_is_admin() or storage_metric_user_uuid(name) = auth.uid())
  );

drop policy if exists "metrics photos insert" on storage.objects;
create policy "metrics photos insert" on storage.objects for insert to authenticated
  with check (
    bucket_id = 'metrics-photos'
    and (auth_is_admin() or storage_metric_user_uuid(name) = auth.uid())
  );

drop policy if exists "metrics photos update" on storage.objects;
create policy "metrics photos update" on storage.objects for update to authenticated
  using (
    bucket_id = 'metrics-photos'
    and (auth_is_admin() or storage_metric_user_uuid(name) = auth.uid())
  ) with check (
    bucket_id = 'metrics-photos'
    and (auth_is_admin() or storage_metric_user_uuid(name) = auth.uid())
  );

drop policy if exists "metrics photos delete" on storage.objects;
create policy "metrics photos delete" on storage.objects for delete to authenticated
  using (
    bucket_id = 'metrics-photos'
    and (auth_is_admin() or storage_metric_user_uuid(name) = auth.uid())
  );
