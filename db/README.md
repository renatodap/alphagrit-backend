# Database Setup Guide

## Quick Start - Apply Community Schema

### 1. Run the migration in Supabase Dashboard

1. Go to your Supabase project dashboard
2. Navigate to **SQL Editor**
3. Copy and paste the contents of `schema/0002_community.sql`
4. Click **Run** to execute the migration

### 2. Enable Real-time (IMPORTANT!)

After running the migration, enable real-time for community features:

1. Go to **Database > Replication** in Supabase Dashboard
2. Enable the following tables for real-time:
   - `posts`
   - `community_comments`
   - `community_likes`

Alternatively, run these SQL commands:
```sql
alter publication supabase_realtime add table posts;
alter publication supabase_realtime add table community_comments;
alter publication supabase_realtime add table community_likes;
```

## What Was Created

### Tables
- **posts** (enhanced): Community posts with title, likes/comments counts
- **community_comments**: Nested comment system with replies
- **community_likes**: Like tracking with duplicate prevention
- **programs** (enhanced): Added start_date, end_date, slug for Winter Arc

### Storage
- **community bucket**: Public bucket for post images
  - Users can upload images to `community/{user_id}/{filename}`
  - Anyone can view images
  - Users can delete their own images

### Security (RLS Policies)
- Users can only view posts in programs they've joined
- Users can only create posts in their own programs
- Users can only edit/delete their own posts and comments
- Likes are tracked per user to prevent duplicates

### Database Functions & Triggers
- Auto-increment/decrement likes_count on posts
- Auto-increment/decrement comments_count on posts
- Automatic updated_at timestamps

### Winter Arc Program
- Created "Winter Arc" program (Nov 17, 2025 - Feb 9, 2026)
- Slug: `winter-arc`
- Access controlled via `user_programs` table

## Testing the Schema

### 1. Check if Winter Arc program exists
```sql
select * from programs where slug = 'winter-arc';
```

### 2. Grant yourself access (replace with your user_id)
```sql
insert into user_programs (user_id, program_id)
select 'YOUR_USER_UUID', id from programs where slug = 'winter-arc';
```

### 3. Create a test post
```sql
insert into posts (user_id, program_id, message, visibility)
values (
  'YOUR_USER_UUID',
  (select id from programs where slug = 'winter-arc'),
  'Welcome to the Winter Arc!',
  'public'
);
```

### 4. Verify RLS policies work
```sql
-- Should only show posts from programs you're in
select * from posts;
```

## Schema Files

- `0001_base.sql` - Base schema (users, profiles, ebooks, programs, etc.)
- `0002_community.sql` - Community features (comments, likes, RLS, real-time)

## Troubleshooting

### RLS blocking your queries?
Make sure you're authenticated in the SQL editor with a user that has `user_programs` entries.

### Real-time not working?
Check that tables are added to the `supabase_realtime` publication in Database > Replication.

### Storage upload failing?
Verify the `community` bucket exists and policies are active in Storage settings.
