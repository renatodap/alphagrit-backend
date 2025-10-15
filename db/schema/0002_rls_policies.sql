-- RLS Policies for WagnerFit schema (public)
-- Apply after 0001_base.sql

-- Helper: check if current user is admin
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

-- Enable RLS on all tables (idempotent)
alter table if exists users enable row level security;
alter table if exists user_profiles enable row level security;
alter table if exists ebooks enable row level security;
alter table if exists programs enable row level security;
alter table if exists user_programs enable row level security;
alter table if exists posts enable row level security;
alter table if exists user_metrics enable row level security;
alter table if exists purchases enable row level security;
alter table if exists affiliate_products enable row level security;

-- users: restrict to self or admin (note: consider using auth.users instead)
drop policy if exists "users self read" on users;
create policy "users self read" on users for select
  using (id = auth.uid() or auth_is_admin());

drop policy if exists "users admin manage" on users;
create policy "users admin manage" on users for all
  using (auth_is_admin()) with check (auth_is_admin());

-- user_profiles
drop policy if exists "profiles read" on user_profiles;
create policy "profiles read" on user_profiles for select
  using (user_id = auth.uid() or auth_is_admin());

drop policy if exists "profiles insert self" on user_profiles;
create policy "profiles insert self" on user_profiles for insert
  with check (user_id = auth.uid() or auth_is_admin());

drop policy if exists "profiles update self or admin" on user_profiles;
create policy "profiles update self or admin" on user_profiles for update
  using (user_id = auth.uid() or auth_is_admin())
  with check (user_id = auth.uid() or auth_is_admin());

drop policy if exists "profiles delete admin" on user_profiles;
create policy "profiles delete admin" on user_profiles for delete
  using (auth_is_admin());

-- ebooks: public read; admin manage
drop policy if exists "ebooks public read" on ebooks;
create policy "ebooks public read" on ebooks for select using (true);

drop policy if exists "ebooks admin manage" on ebooks;
create policy "ebooks admin manage" on ebooks for all
  using (auth_is_admin()) with check (auth_is_admin());

-- programs: public read; admin manage
drop policy if exists "programs public read" on programs;
create policy "programs public read" on programs for select using (true);

drop policy if exists "programs admin manage" on programs;
create policy "programs admin manage" on programs for all
  using (auth_is_admin()) with check (auth_is_admin());

-- user_programs: users read own; admin manage
drop policy if exists "user_programs read own or admin" on user_programs;
create policy "user_programs read own or admin" on user_programs for select
  using (user_id = auth.uid() or auth_is_admin());

drop policy if exists "user_programs admin manage" on user_programs;
create policy "user_programs admin manage" on user_programs for all
  using (auth_is_admin()) with check (auth_is_admin());

-- posts: visibility + membership rules
-- SELECT: admin OR (member of program AND (public OR (private AND author)))
drop policy if exists "posts visibility for members" on posts;
create policy "posts visibility for members" on posts for select
  using (
    auth_is_admin() OR (
      exists (
        select 1 from user_programs up
        where up.user_id = auth.uid() and up.program_id = posts.program_id
      )
      and (
        visibility = 'public' OR (visibility = 'private' and user_id = auth.uid())
      )
    )
  );

-- INSERT: must be member and author of own post
drop policy if exists "posts insert member author" on posts;
create policy "posts insert member author" on posts for insert
  with check (
    user_id = auth.uid() and exists (
      select 1 from user_programs up
      where up.user_id = auth.uid() and up.program_id = posts.program_id
    )
  );

-- UPDATE/DELETE: author or admin
drop policy if exists "posts author or admin update" on posts;
create policy "posts author or admin update" on posts for update
  using (user_id = auth.uid() or auth_is_admin())
  with check (user_id = auth.uid() or auth_is_admin());

drop policy if exists "posts author or admin delete" on posts;
create policy "posts author or admin delete" on posts for delete
  using (user_id = auth.uid() or auth_is_admin());

-- user_metrics: owner or admin
drop policy if exists "metrics read own or admin" on user_metrics;
create policy "metrics read own or admin" on user_metrics for select
  using (user_id = auth.uid() or auth_is_admin());

drop policy if exists "metrics insert own or admin" on user_metrics;
create policy "metrics insert own or admin" on user_metrics for insert
  with check (user_id = auth.uid() or auth_is_admin());

drop policy if exists "metrics update own or admin" on user_metrics;
create policy "metrics update own or admin" on user_metrics for update
  using (user_id = auth.uid() or auth_is_admin())
  with check (user_id = auth.uid() or auth_is_admin());

drop policy if exists "metrics delete own or admin" on user_metrics;
create policy "metrics delete own or admin" on user_metrics for delete
  using (user_id = auth.uid() or auth_is_admin());

-- purchases: user sees own; admin manage
drop policy if exists "purchases read own or admin" on purchases;
create policy "purchases read own or admin" on purchases for select
  using (user_id = auth.uid() or auth_is_admin());

drop policy if exists "purchases admin manage" on purchases;
create policy "purchases admin manage" on purchases for all
  using (auth_is_admin()) with check (auth_is_admin());

-- affiliate products: public read; admin manage
drop policy if exists "affiliate public read" on affiliate_products;
create policy "affiliate public read" on affiliate_products for select using (true);

drop policy if exists "affiliate admin manage" on affiliate_products;
create policy "affiliate admin manage" on affiliate_products for all
  using (auth_is_admin()) with check (auth_is_admin());

