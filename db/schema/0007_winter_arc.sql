-- Winter Arc Program and Ebook Setup
-- Adds time-limited program support and Winter Arc products

-- Add end_date and payment type to programs
alter table if exists programs
  add column if not exists end_date timestamp with time zone,
  add column if not exists is_one_time_payment boolean default false;

create index if not exists idx_programs_end_date on programs(end_date);

-- Insert Winter Arc Program
-- Program runs from Nov 17, 2024 to Feb 9, 2025 (12 weeks)
insert into programs (title, description, banner_url, is_one_time_payment, end_date, stripe_price_standard_id)
values (
  'Winter Arc',
  '12 weeks of transformation. November 17th to February 9th. Join the private community, share your progress, and build accountability with fellow warriors on the same journey.',
  null, -- Add banner URL later
  true,
  '2025-02-09 23:59:59+00'::timestamp with time zone,
  null -- Will be filled with Stripe price ID
)
on conflict do nothing;

-- Insert Winter Arc Ebook
insert into ebooks (slug, title, description, cover_url, price_cents, program_id, stripe_price_id, program_combo_price_id)
values (
  'winter-arc',
  'The Winter Arc',
  'Complete training guide for your 12-week transformation. Covers training methodology, nutrition fundamentals, mindset shifts, and daily protocols.',
  null, -- Add cover URL later
  2700, -- $27
  (select id from programs where title = 'Winter Arc' limit 1),
  null, -- Ebook-only Stripe price ID
  null  -- Combo Stripe price ID ($97)
)
on conflict (slug) do update set
  program_id = excluded.program_id,
  price_cents = excluded.price_cents;

-- Note: After creating Stripe products, update the price IDs with:
-- UPDATE programs SET stripe_price_standard_id = 'price_xxx' WHERE title = 'Winter Arc';
-- UPDATE ebooks SET stripe_price_id = 'price_xxx', program_combo_price_id = 'price_yyy' WHERE slug = 'winter-arc';
