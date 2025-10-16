-- Community features for Winter Arc (Nov 17 - Feb 9)
-- Migration: 0002_community.sql

-- Add Winter Arc specific fields to programs table
alter table programs add column if not exists start_date timestamp with time zone;
alter table programs add column if not exists end_date timestamp with time zone;
alter table programs add column if not exists slug text unique;

-- Update posts table for enhanced community features
alter table posts add column if not exists title text;
alter table posts add column if not exists likes_count integer default 0;
alter table posts add column if not exists comments_count integer default 0;
alter table posts add column if not exists is_pinned boolean default false;
alter table posts add column if not exists updated_at timestamp with time zone default now();

-- Create community_comments table
create table if not exists community_comments (
  id bigint generated always as identity primary key,
  post_id bigint not null references posts(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  content text not null,
  parent_comment_id bigint references community_comments(id) on delete cascade,
  created_at timestamp with time zone default now(),
  updated_at timestamp with time zone default now()
);

-- Create community_likes table (for posts)
create table if not exists community_likes (
  id bigint generated always as identity primary key,
  post_id bigint not null references posts(id) on delete cascade,
  user_id uuid not null references users(id) on delete cascade,
  created_at timestamp with time zone default now(),
  unique(post_id, user_id)
);

-- Create storage bucket for community images
insert into storage.buckets (id, name, public)
values ('community', 'community', true)
on conflict (id) do nothing;

-- Storage policies for community bucket
create policy "Users can upload community images"
on storage.objects for insert
with check (
  bucket_id = 'community'
  and auth.uid() is not null
);

create policy "Anyone can view community images"
on storage.objects for select
using (bucket_id = 'community');

create policy "Users can delete their own images"
on storage.objects for delete
using (
  bucket_id = 'community'
  and auth.uid()::text = (storage.foldername(name))[1]
);

-- Indexes for performance
create index if not exists idx_community_comments_post_id on community_comments(post_id, created_at desc);
create index if not exists idx_community_comments_user_id on community_comments(user_id);
create index if not exists idx_community_likes_post_id on community_likes(post_id);
create index if not exists idx_community_likes_user_id on community_likes(user_id);
create index if not exists idx_posts_visibility_created on posts(visibility, created_at desc);
create index if not exists idx_user_programs_program_user on user_programs(program_id, user_id);

-- ============================================
-- Row Level Security (RLS) Policies
-- ============================================

-- Enable RLS on all tables
alter table posts enable row level security;
alter table community_comments enable row level security;
alter table community_likes enable row level security;

-- Posts Policies
create policy "Users can view posts in their programs"
on posts for select
using (
  visibility = 'public'
  and exists (
    select 1 from user_programs up
    where up.user_id = auth.uid()
      and up.program_id = posts.program_id
  )
);

create policy "Users can create posts in their programs"
on posts for insert
with check (
  exists (
    select 1 from user_programs up
    where up.user_id = auth.uid()
      and up.program_id = program_id
  )
  and user_id = auth.uid()
);

create policy "Users can update their own posts"
on posts for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "Users can delete their own posts"
on posts for delete
using (user_id = auth.uid());

-- Comments Policies
create policy "Users can view comments on posts they can see"
on community_comments for select
using (
  exists (
    select 1 from posts p
    join user_programs up on up.program_id = p.program_id
    where p.id = post_id
      and up.user_id = auth.uid()
  )
);

create policy "Users can create comments on posts in their programs"
on community_comments for insert
with check (
  exists (
    select 1 from posts p
    join user_programs up on up.program_id = p.program_id
    where p.id = post_id
      and up.user_id = auth.uid()
  )
  and user_id = auth.uid()
);

create policy "Users can update their own comments"
on community_comments for update
using (user_id = auth.uid())
with check (user_id = auth.uid());

create policy "Users can delete their own comments"
on community_comments for delete
using (user_id = auth.uid());

-- Likes Policies
create policy "Users can view likes"
on community_likes for select
using (true);

create policy "Users can like posts in their programs"
on community_likes for insert
with check (
  exists (
    select 1 from posts p
    join user_programs up on up.program_id = p.program_id
    where p.id = post_id
      and up.user_id = auth.uid()
  )
  and user_id = auth.uid()
);

create policy "Users can unlike posts"
on community_likes for delete
using (user_id = auth.uid());

-- ============================================
-- Database Functions
-- ============================================

-- Function to update post counts on new comment
create or replace function increment_post_comments_count()
returns trigger as $$
begin
  update posts
  set comments_count = comments_count + 1,
      updated_at = now()
  where id = NEW.post_id;
  return NEW;
end;
$$ language plpgsql security definer;

-- Function to update post counts on comment deletion
create or replace function decrement_post_comments_count()
returns trigger as $$
begin
  update posts
  set comments_count = greatest(0, comments_count - 1),
      updated_at = now()
  where id = OLD.post_id;
  return OLD;
end;
$$ language plpgsql security definer;

-- Function to update post counts on new like
create or replace function increment_post_likes_count()
returns trigger as $$
begin
  update posts
  set likes_count = likes_count + 1,
      updated_at = now()
  where id = NEW.post_id;
  return NEW;
end;
$$ language plpgsql security definer;

-- Function to update post counts on like removal
create or replace function decrement_post_likes_count()
returns trigger as $$
begin
  update posts
  set likes_count = greatest(0, likes_count - 1),
      updated_at = now()
  where id = OLD.post_id;
  return OLD;
end;
$$ language plpgsql security definer;

-- ============================================
-- Triggers
-- ============================================

-- Trigger for comment count
drop trigger if exists trg_increment_post_comments on community_comments;
create trigger trg_increment_post_comments
  after insert on community_comments
  for each row
  execute function increment_post_comments_count();

drop trigger if exists trg_decrement_post_comments on community_comments;
create trigger trg_decrement_post_comments
  after delete on community_comments
  for each row
  execute function decrement_post_comments_count();

-- Trigger for like count
drop trigger if exists trg_increment_post_likes on community_likes;
create trigger trg_increment_post_likes
  after insert on community_likes
  for each row
  execute function increment_post_likes_count();

drop trigger if exists trg_decrement_post_likes on community_likes;
create trigger trg_decrement_post_likes
  after delete on community_likes
  for each row
  execute function decrement_post_likes_count();

-- ============================================
-- Winter Arc Program Setup
-- ============================================

-- Insert/Update Winter Arc program
insert into programs (title, description, slug, start_date, end_date)
values (
  'Winter Arc',
  'Transform winter into your strongest season. 12-week brutal accountability program.',
  'winter-arc',
  '2025-11-17 00:00:00+00'::timestamp with time zone,
  '2026-02-09 23:59:59+00'::timestamp with time zone
)
on conflict (slug) do update
set start_date = excluded.start_date,
    end_date = excluded.end_date,
    description = excluded.description;

-- ============================================
-- Real-time Setup (run these in Supabase Dashboard)
-- ============================================

-- Enable real-time for posts
-- alter publication supabase_realtime add table posts;

-- Enable real-time for comments
-- alter publication supabase_realtime add table community_comments;

-- Enable real-time for likes
-- alter publication supabase_realtime add table community_likes;
