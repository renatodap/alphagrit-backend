-- Membership tiers and user notification preferences

-- user_programs: add tier
alter table if exists user_programs
  add column if not exists tier text not null default 'standard' check (tier in ('standard','premium'));

create index if not exists idx_user_programs_user_program_tier on user_programs(user_id, program_id, tier);

-- programs: price IDs for tiers
alter table if exists programs
  add column if not exists stripe_price_standard_id text,
  add column if not exists stripe_price_premium_id text;

create index if not exists idx_programs_price_std on programs(stripe_price_standard_id);
create index if not exists idx_programs_price_prem on programs(stripe_price_premium_id);

-- ebooks: optional premium combo price
alter table if exists ebooks
  add column if not exists program_combo_premium_price_id text;

create index if not exists idx_ebooks_combo_premium on ebooks(program_combo_premium_price_id);

-- purchases: store selected tier when applicable
alter table if exists purchases
  add column if not exists tier text;

create index if not exists idx_purchases_tier on purchases(tier);

-- user_profiles: notification preferences
alter table if exists user_profiles
  add column if not exists notify_email_summaries boolean default false,
  add column if not exists notify_replies boolean default true,
  add column if not exists notify_coach_responses boolean default true;

