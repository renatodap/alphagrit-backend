-- Migration 0008: Winter Arc Tracking System
-- Creates tables for Winter Arc program progress tracking, checklists, leaderboard, and achievements
-- Run this migration in Supabase SQL Editor
-- After running, enable realtime: alter publication supabase_realtime add table winter_arc_daily_checklists;
-- After running, enable realtime: alter publication supabase_realtime add table winter_arc_weekly_checklists;

-- ============================================================================
-- 1. WINTER ARC USER PROGRESS (Main tracking table)
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_user_progress (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

  -- Mission Statement
  mission_statement TEXT,

  -- Macro Calculator Data
  current_weight_kg NUMERIC(5,2),
  height_cm NUMERIC(5,2),
  age INTEGER,
  gender TEXT CHECK (gender IN ('male', 'female')),
  activity_level TEXT CHECK (activity_level IN ('sedentary', 'lightly_active', 'moderately_active', 'very_active', 'extremely_active')),
  goal TEXT CHECK (goal IN ('cut', 'maintain', 'build')),
  bmr NUMERIC(6,2),
  tdee NUMERIC(6,2),
  target_calories NUMERIC(6,2),
  protein_g NUMERIC(5,2),
  carbs_g NUMERIC(5,2),
  fat_g NUMERIC(5,2),

  -- Streaks & Statistics
  current_daily_streak INTEGER DEFAULT 0,
  longest_daily_streak INTEGER DEFAULT 0,
  current_weekly_streak INTEGER DEFAULT 0,
  longest_weekly_streak INTEGER DEFAULT 0,
  total_days_completed INTEGER DEFAULT 0,
  total_weeks_completed INTEGER DEFAULT 0,

  -- Timer tracking
  three_min_timer_completions INTEGER DEFAULT 0,
  total_timer_minutes INTEGER DEFAULT 0,

  -- Leaderboard score (calculated field)
  leaderboard_score NUMERIC(10,2) DEFAULT 0,
  leaderboard_rank INTEGER,

  -- Privacy settings
  show_on_leaderboard BOOLEAN DEFAULT FALSE,
  profile_visibility TEXT DEFAULT 'private' CHECK (profile_visibility IN ('private', 'program', 'public')),

  -- Timestamps
  started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints
  UNIQUE(user_id, program_id)
);

-- Index for fast lookups
CREATE INDEX IF NOT EXISTS idx_winter_arc_user_progress_user ON winter_arc_user_progress(user_id);
CREATE INDEX IF NOT EXISTS idx_winter_arc_user_progress_program ON winter_arc_user_progress(program_id);
CREATE INDEX IF NOT EXISTS idx_winter_arc_leaderboard ON winter_arc_user_progress(program_id, leaderboard_score DESC, show_on_leaderboard) WHERE show_on_leaderboard = TRUE;

-- ============================================================================
-- 2. DAILY CHECKLISTS (Date-based tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_daily_checklists (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  checklist_date DATE NOT NULL,

  -- 10 Daily Checklist Items (boolean for each)
  wake_up_early BOOLEAN DEFAULT FALSE,
  ten_min_silence BOOLEAN DEFAULT FALSE,
  morning_hydration BOOLEAN DEFAULT FALSE,
  workout BOOLEAN DEFAULT FALSE,
  clean_eating BOOLEAN DEFAULT FALSE,
  review_mission BOOLEAN DEFAULT FALSE,
  small_sacrifice BOOLEAN DEFAULT FALSE,
  moment_silence BOOLEAN DEFAULT FALSE,
  act_of_honor BOOLEAN DEFAULT FALSE,
  small_overcoming BOOLEAN DEFAULT FALSE,

  -- Summary
  items_completed INTEGER DEFAULT 0,
  total_items INTEGER DEFAULT 10,
  completion_percentage NUMERIC(5,2) DEFAULT 0,
  is_fully_completed BOOLEAN DEFAULT FALSE,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints: One checklist per user per day per program
  UNIQUE(user_id, program_id, checklist_date)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_daily_checklist_user_date ON winter_arc_daily_checklists(user_id, checklist_date DESC);
CREATE INDEX IF NOT EXISTS idx_daily_checklist_program_date ON winter_arc_daily_checklists(program_id, checklist_date DESC);

-- ============================================================================
-- 3. WEEKLY CHECKLISTS (Week-based tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_weekly_checklists (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  week_start_date DATE NOT NULL, -- Monday of the week
  week_end_date DATE NOT NULL,   -- Sunday of the week
  year INTEGER NOT NULL,
  week_number INTEGER NOT NULL,  -- ISO week number (1-53)

  -- 8 Weekly Checklist Items
  strength_workouts_3_4 BOOLEAN DEFAULT FALSE,
  cardio_sessions_2_3 BOOLEAN DEFAULT FALSE,
  meal_prep BOOLEAN DEFAULT FALSE,
  progress_review BOOLEAN DEFAULT FALSE,
  plan_adjustment BOOLEAN DEFAULT FALSE,
  monk_mode_period BOOLEAN DEFAULT FALSE,
  reflection_on_principles BOOLEAN DEFAULT FALSE,
  planning_next_week BOOLEAN DEFAULT FALSE,

  -- Summary
  items_completed INTEGER DEFAULT 0,
  total_items INTEGER DEFAULT 8,
  completion_percentage NUMERIC(5,2) DEFAULT 0,
  is_fully_completed BOOLEAN DEFAULT FALSE,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  -- Constraints: One checklist per user per week per program
  UNIQUE(user_id, program_id, year, week_number)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_weekly_checklist_user_week ON winter_arc_weekly_checklists(user_id, week_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_weekly_checklist_program_week ON winter_arc_weekly_checklists(program_id, year DESC, week_number DESC);

-- ============================================================================
-- 4. PROGRESS SNAPSHOTS (Historical tracking)
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_progress_snapshots (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  snapshot_date DATE NOT NULL,

  -- Body Measurements
  weight_kg NUMERIC(5,2),
  body_fat_percentage NUMERIC(4,2),
  chest_cm NUMERIC(5,2),
  waist_cm NUMERIC(5,2),
  hips_cm NUMERIC(5,2),
  arms_cm NUMERIC(5,2),
  thighs_cm NUMERIC(5,2),

  -- Performance Metrics
  max_pushups INTEGER,
  max_squats INTEGER,
  plank_seconds INTEGER,

  -- Notes
  notes TEXT,
  mood TEXT CHECK (mood IN ('excellent', 'good', 'okay', 'struggling', 'difficult')),
  energy_level INTEGER CHECK (energy_level >= 1 AND energy_level <= 10),

  -- Photos (URLs to storage)
  photo_front_url TEXT,
  photo_side_url TEXT,
  photo_back_url TEXT,

  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_snapshots_user_date ON winter_arc_progress_snapshots(user_id, snapshot_date DESC);
CREATE INDEX IF NOT EXISTS idx_snapshots_program ON winter_arc_progress_snapshots(program_id, snapshot_date DESC);

-- ============================================================================
-- 5. ACHIEVEMENTS & BADGES
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_achievements (
  id BIGSERIAL PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  badge_icon TEXT, -- URL or icon name
  category TEXT CHECK (category IN ('streak', 'completion', 'milestone', 'special')),
  points INTEGER DEFAULT 0,

  -- Requirements (JSONB for flexibility)
  requirements JSONB DEFAULT '{}'::JSONB,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default achievements
INSERT INTO winter_arc_achievements (code, name, description, category, points, requirements) VALUES
  ('first_day', 'First Step', 'Complete your first daily checklist', 'milestone', 10, '{"daily_completions": 1}'),
  ('week_warrior', 'Week Warrior', 'Complete a full week of daily checklists', 'streak', 50, '{"daily_streak": 7}'),
  ('month_master', 'Month Master', 'Complete 30 days of Winter Arc', 'streak', 200, '{"total_days": 30}'),
  ('perfect_week', 'Perfect Week', 'Complete 100% of daily AND weekly checklist in one week', 'completion', 100, '{"weekly_completion": 100, "daily_completion": 100}'),
  ('iron_discipline', 'Iron Discipline', '21-day streak (habit formation)', 'streak', 300, '{"daily_streak": 21}'),
  ('seasonal_warrior', 'Seasonal Warrior', 'Complete the full 60-day Winter Arc', 'milestone', 500, '{"total_days": 60}'),
  ('early_riser', 'Early Riser', 'Wake up early 30 times', 'special', 75, '{"wake_up_early_count": 30}'),
  ('monk_mode', 'Monk Mode Master', 'Complete 7-day Monk Mode challenge', 'special', 150, '{"monk_mode": true}'),
  ('three_min_champion', '3-Min Champion', 'Complete 50 timer sessions', 'special', 100, '{"timer_completions": 50}')
ON CONFLICT (code) DO NOTHING;

-- User achievements (earned badges)
CREATE TABLE IF NOT EXISTS winter_arc_user_achievements (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,
  achievement_id BIGINT NOT NULL REFERENCES winter_arc_achievements(id) ON DELETE CASCADE,

  earned_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

  UNIQUE(user_id, program_id, achievement_id)
);

CREATE INDEX IF NOT EXISTS idx_user_achievements ON winter_arc_user_achievements(user_id, program_id);

-- ============================================================================
-- 6. POST SUGGESTIONS (Community integration triggers)
-- ============================================================================
CREATE TABLE IF NOT EXISTS winter_arc_post_suggestions (
  id BIGSERIAL PRIMARY KEY,
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES programs(id) ON DELETE CASCADE,

  trigger_type TEXT NOT NULL CHECK (trigger_type IN ('daily_complete', 'weekly_complete', 'streak_milestone', 'achievement_earned', 'progress_snapshot')),
  trigger_data JSONB DEFAULT '{}'::JSONB,

  suggested_title TEXT,
  suggested_content TEXT,

  is_dismissed BOOLEAN DEFAULT FALSE,
  is_posted BOOLEAN DEFAULT FALSE,
  post_id BIGINT REFERENCES posts(id) ON DELETE SET NULL,

  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  dismissed_at TIMESTAMP WITH TIME ZONE,
  posted_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_post_suggestions_user ON winter_arc_post_suggestions(user_id, created_at DESC) WHERE is_dismissed = FALSE AND is_posted = FALSE;

-- ============================================================================
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS
ALTER TABLE winter_arc_user_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_daily_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_weekly_checklists ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_progress_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_user_achievements ENABLE ROW LEVEL SECURITY;
ALTER TABLE winter_arc_post_suggestions ENABLE ROW LEVEL SECURITY;

-- User Progress Policies
CREATE POLICY "Users can view their own progress"
  ON winter_arc_user_progress FOR SELECT
  USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own progress"
  ON winter_arc_user_progress FOR INSERT
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own progress"
  ON winter_arc_user_progress FOR UPDATE
  USING (auth.uid() = user_id);

CREATE POLICY "Users can view public leaderboard entries"
  ON winter_arc_user_progress FOR SELECT
  USING (show_on_leaderboard = TRUE);

-- Daily Checklist Policies
CREATE POLICY "Users can manage their own daily checklists"
  ON winter_arc_daily_checklists FOR ALL
  USING (auth.uid() = user_id);

-- Weekly Checklist Policies
CREATE POLICY "Users can manage their own weekly checklists"
  ON winter_arc_weekly_checklists FOR ALL
  USING (auth.uid() = user_id);

-- Progress Snapshots Policies
CREATE POLICY "Users can manage their own snapshots"
  ON winter_arc_progress_snapshots FOR ALL
  USING (auth.uid() = user_id);

-- Achievements Policies (public read, no write for users)
CREATE POLICY "Anyone can view achievements"
  ON winter_arc_achievements FOR SELECT
  TO authenticated
  USING (true);

-- User Achievements Policies
CREATE POLICY "Users can view their own earned achievements"
  ON winter_arc_user_achievements FOR SELECT
  USING (auth.uid() = user_id);

-- Post Suggestions Policies
CREATE POLICY "Users can manage their own post suggestions"
  ON winter_arc_post_suggestions FOR ALL
  USING (auth.uid() = user_id);

-- ============================================================================
-- 8. FUNCTIONS & TRIGGERS
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_winter_arc_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_user_progress_timestamp
  BEFORE UPDATE ON winter_arc_user_progress
  FOR EACH ROW
  EXECUTE FUNCTION update_winter_arc_updated_at();

CREATE TRIGGER update_daily_checklist_timestamp
  BEFORE UPDATE ON winter_arc_daily_checklists
  FOR EACH ROW
  EXECUTE FUNCTION update_winter_arc_updated_at();

CREATE TRIGGER update_weekly_checklist_timestamp
  BEFORE UPDATE ON winter_arc_weekly_checklists
  FOR EACH ROW
  EXECUTE FUNCTION update_winter_arc_updated_at();

-- Function to calculate daily checklist completion
CREATE OR REPLACE FUNCTION calculate_daily_completion()
RETURNS TRIGGER AS $$
BEGIN
  NEW.items_completed := (
    (CASE WHEN NEW.wake_up_early THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.ten_min_silence THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.morning_hydration THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.workout THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.clean_eating THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.review_mission THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.small_sacrifice THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.moment_silence THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.act_of_honor THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.small_overcoming THEN 1 ELSE 0 END)
  );

  NEW.completion_percentage := (NEW.items_completed::NUMERIC / NEW.total_items::NUMERIC) * 100;
  NEW.is_fully_completed := (NEW.items_completed = NEW.total_items);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_daily_completion_trigger
  BEFORE INSERT OR UPDATE ON winter_arc_daily_checklists
  FOR EACH ROW
  EXECUTE FUNCTION calculate_daily_completion();

-- Function to calculate weekly checklist completion
CREATE OR REPLACE FUNCTION calculate_weekly_completion()
RETURNS TRIGGER AS $$
BEGIN
  NEW.items_completed := (
    (CASE WHEN NEW.strength_workouts_3_4 THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.cardio_sessions_2_3 THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.meal_prep THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.progress_review THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.plan_adjustment THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.monk_mode_period THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.reflection_on_principles THEN 1 ELSE 0 END) +
    (CASE WHEN NEW.planning_next_week THEN 1 ELSE 0 END)
  );

  NEW.completion_percentage := (NEW.items_completed::NUMERIC / NEW.total_items::NUMERIC) * 100;
  NEW.is_fully_completed := (NEW.items_completed = NEW.total_items);

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER calculate_weekly_completion_trigger
  BEFORE INSERT OR UPDATE ON winter_arc_weekly_checklists
  FOR EACH ROW
  EXECUTE FUNCTION calculate_weekly_completion();

-- ============================================================================
-- 9. HELPER VIEWS
-- ============================================================================

-- Leaderboard view (public entries only)
CREATE OR REPLACE VIEW winter_arc_leaderboard AS
SELECT
  wap.id,
  wap.user_id,
  u.email,
  u.raw_user_meta_data->>'name' as user_name,
  wap.program_id,
  wap.leaderboard_score,
  wap.leaderboard_rank,
  wap.current_daily_streak,
  wap.longest_daily_streak,
  wap.total_days_completed,
  wap.total_weeks_completed,
  wap.started_at,
  wap.last_activity_at
FROM winter_arc_user_progress wap
JOIN auth.users u ON wap.user_id = u.id
WHERE wap.show_on_leaderboard = TRUE
ORDER BY wap.leaderboard_score DESC, wap.total_days_completed DESC;

-- Grant select on view
GRANT SELECT ON winter_arc_leaderboard TO authenticated;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Enable realtime on daily/weekly checklists:
--    alter publication supabase_realtime add table winter_arc_daily_checklists;
--    alter publication supabase_realtime add table winter_arc_weekly_checklists;
-- 2. Test the schema with sample data
-- 3. Implement backend services to interact with these tables
