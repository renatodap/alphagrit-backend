-- Pricing integration: add Stripe Price IDs for products and combos

alter table if exists ebooks
  add column if not exists stripe_price_id text,
  add column if not exists program_combo_price_id text;

create index if not exists idx_ebooks_stripe_price on ebooks(stripe_price_id);
create index if not exists idx_ebooks_combo_price on ebooks(program_combo_price_id);

alter table if exists programs
  add column if not exists stripe_price_id text;

create index if not exists idx_programs_stripe_price on programs(stripe_price_id);
