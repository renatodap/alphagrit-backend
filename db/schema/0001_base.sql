-- Base schema for WagnerFit (Supabase Postgres)

create table if not exists users (
  id uuid primary key default gen_random_uuid(),
  email text unique not null,
  created_at timestamp with time zone default now()
);

create table if not exists user_profiles (
  id bigint generated always as identity primary key,
  user_id uuid not null references users(id) on delete cascade,
  name text,
  bio text,
  avatar_url text,
  language text default 'en',
  unit_preference text default 'kg',
  is_admin boolean default false,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

create table if not exists ebooks (
  id bigint generated always as identity primary key,
  slug text unique not null,
  title text not null,
  description text,
  cover_url text,
  price_cents integer not null,
  program_id bigint,
  created_at timestamp with time zone default now()
);

create table if not exists programs (
  id bigint generated always as identity primary key,
  title text not null,
  description text,
  banner_url text,
  created_at timestamp with time zone default now()
);

create table if not exists user_programs (
  id bigint generated always as identity primary key,
  user_id uuid not null references users(id) on delete cascade,
  program_id bigint not null references programs(id) on delete cascade,
  created_at timestamp with time zone default now(),
  unique(user_id, program_id)
);

create table if not exists posts (
  id bigint generated always as identity primary key,
  user_id uuid not null references users(id) on delete cascade,
  program_id bigint not null references programs(id) on delete cascade,
  message text,
  photo_url text,
  visibility text not null default 'public', -- public | private
  created_at timestamp with time zone default now()
);

create table if not exists user_metrics (
  id bigint generated always as identity primary key,
  user_id uuid not null references users(id) on delete cascade,
  date date not null,
  weight numeric(6,2),
  body_fat numeric(5,2),
  photo_url text,
  note text,
  created_at timestamp with time zone default now(),
  unique(user_id, date)
);

create table if not exists purchases (
  id bigint generated always as identity primary key,
  user_id uuid not null references users(id) on delete cascade,
  item_type text not null, -- ebook | program | combo
  item_id bigint,
  price_cents integer default 0,
  stripe_session_id text,
  stripe_payment_intent text,
  status text not null default 'pending', -- pending | paid | failed | refunded
  created_at timestamp with time zone default now()
);

create table if not exists affiliate_products (
  id bigint generated always as identity primary key,
  name text not null,
  category text,
  amazon_url text not null,
  image_url text,
  created_at timestamp with time zone default now()
);

-- Example indexes
create index if not exists idx_posts_program_id_created on posts(program_id, created_at desc);
create index if not exists idx_purchases_user_status on purchases(user_id, status);
