-- Migration 0009: Winter Arc Tier System
-- Adds tier support for E-book + Community product with Premium tier (Wagner guarantee)
-- Author: Claude Code
-- Date: 2025

-- ============================================================================
-- 1. Add tier column to user_programs
-- ============================================================================

-- Add tier field: 'standard' or 'premium'
-- NULL for ebook-only purchases (no community access)
ALTER TABLE user_programs
ADD COLUMN IF NOT EXISTS tier VARCHAR(20) DEFAULT 'standard'
CHECK (tier IN ('standard', 'premium') OR tier IS NULL);

-- Add product_type field to track what was purchased
ALTER TABLE user_programs
ADD COLUMN IF NOT EXISTS product_type VARCHAR(30) DEFAULT 'bundle'
CHECK (product_type IN ('ebook_only', 'community_standard', 'community_premium'));

COMMENT ON COLUMN user_programs.tier IS 'Community tier: standard (default) or premium (Wagner-guaranteed responses). NULL for ebook-only purchases.';
COMMENT ON COLUMN user_programs.product_type IS 'Product purchased: ebook_only, community_standard, or community_premium';

-- ============================================================================
-- 2. Create indexes for performance
-- ============================================================================

-- Index for admin queries (Wagner viewing premium posts)
CREATE INDEX IF NOT EXISTS idx_user_programs_tier
ON user_programs(program_id, tier, enrolled_at DESC)
WHERE tier IS NOT NULL;

-- Index for access control checks
CREATE INDEX IF NOT EXISTS idx_user_programs_access
ON user_programs(user_id, program_id, product_type);

-- ============================================================================
-- 3. Update existing enrollments
-- ============================================================================

-- Set existing enrollments to community_standard with standard tier
UPDATE user_programs
SET tier = 'standard',
    product_type = 'community_standard'
WHERE tier IS NULL
  AND product_type IS NULL;

-- ============================================================================
-- 4. Add responded tracking for premium posts
-- ============================================================================

-- Add table to track which premium posts Wagner has responded to
CREATE TABLE IF NOT EXISTS winter_arc_premium_responses (
  id BIGSERIAL PRIMARY KEY,
  post_id BIGINT NOT NULL REFERENCES posts(id) ON DELETE CASCADE,
  responded_by UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  responded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  -- Unique constraint: one response record per post
  UNIQUE(post_id)
);

COMMENT ON TABLE winter_arc_premium_responses IS 'Tracks Wagner responses to premium tier user posts';
COMMENT ON COLUMN winter_arc_premium_responses.post_id IS 'Post that was responded to';
COMMENT ON COLUMN winter_arc_premium_responses.responded_by IS 'Admin who responded (Wagner or delegate)';
COMMENT ON COLUMN winter_arc_premium_responses.notes IS 'Optional internal notes about the response';

-- Index for admin queries
CREATE INDEX IF NOT EXISTS idx_premium_responses_post
ON winter_arc_premium_responses(post_id);

-- ============================================================================
-- 5. Row Level Security (RLS)
-- ============================================================================

-- Enable RLS on new table
ALTER TABLE winter_arc_premium_responses ENABLE ROW LEVEL SECURITY;

-- Admin can read/write all
CREATE POLICY "Admins can manage premium responses"
ON winter_arc_premium_responses
FOR ALL
TO authenticated
USING (
  auth.uid() IN (
    SELECT id FROM users WHERE role = 'admin'
  )
);

-- Users can see if their post was responded to
CREATE POLICY "Users can see responses to own posts"
ON winter_arc_premium_responses
FOR SELECT
TO authenticated
USING (
  post_id IN (
    SELECT id FROM posts WHERE user_id = auth.uid()
  )
);

-- ============================================================================
-- 6. Helper function: Check if user has premium tier
-- ============================================================================

CREATE OR REPLACE FUNCTION is_premium_user(check_user_id UUID, check_program_id INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  RETURN EXISTS (
    SELECT 1
    FROM user_programs
    WHERE user_id = check_user_id
      AND program_id = check_program_id
      AND tier = 'premium'
  );
END;
$$;

COMMENT ON FUNCTION is_premium_user IS 'Check if user has premium tier access for a program';

-- ============================================================================
-- 7. Helper function: Check ebook access
-- ============================================================================

CREATE OR REPLACE FUNCTION has_ebook_access(check_user_id UUID, check_program_id INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check if user has any purchase (ebook_only, community_standard, or community_premium)
  RETURN EXISTS (
    SELECT 1
    FROM user_programs
    WHERE user_id = check_user_id
      AND program_id = check_program_id
      AND product_type IN ('ebook_only', 'community_standard', 'community_premium')
  );
END;
$$;

COMMENT ON FUNCTION has_ebook_access IS 'Check if user has purchased ebook (any tier)';

-- ============================================================================
-- 8. Helper function: Check community access
-- ============================================================================

CREATE OR REPLACE FUNCTION has_community_access(check_user_id UUID, check_program_id INT)
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
BEGIN
  -- Check if user has community access (standard or premium, but not ebook_only)
  RETURN EXISTS (
    SELECT 1
    FROM user_programs
    WHERE user_id = check_user_id
      AND program_id = check_program_id
      AND product_type IN ('community_standard', 'community_premium')
  );
END;
$$;

COMMENT ON FUNCTION has_community_access IS 'Check if user has purchased community access';

-- ============================================================================
-- 9. View: Premium posts needing response
-- ============================================================================

CREATE OR REPLACE VIEW winter_arc_premium_posts_queue AS
SELECT
  p.id as post_id,
  p.user_id,
  p.title,
  p.content,
  p.created_at as posted_at,
  u.full_name as user_name,
  u.avatar_url as user_avatar,
  up.tier,
  CASE
    WHEN wpr.id IS NOT NULL THEN true
    ELSE false
  END as has_response,
  wpr.responded_at,
  wpr.responded_by,
  wpr.notes
FROM posts p
INNER JOIN users u ON p.user_id = u.id
INNER JOIN user_programs up ON u.id = up.user_id
LEFT JOIN winter_arc_premium_responses wpr ON p.id = wpr.post_id
WHERE up.tier = 'premium'
  AND p.program_id = 1  -- Winter Arc program
ORDER BY
  CASE WHEN wpr.id IS NULL THEN 0 ELSE 1 END,  -- Unresponded first
  p.created_at DESC;

COMMENT ON VIEW winter_arc_premium_posts_queue IS 'Wagner admin view: Premium posts with response status, unresponded first';

-- ============================================================================
-- 10. Grant permissions
-- ============================================================================

-- Grant execute on functions to authenticated users
GRANT EXECUTE ON FUNCTION is_premium_user TO authenticated;
GRANT EXECUTE ON FUNCTION has_ebook_access TO authenticated;
GRANT EXECUTE ON FUNCTION has_community_access TO authenticated;

-- Grant select on view to admins
-- Note: May need to set up admin role in your Supabase project

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Verify migration
DO $$
BEGIN
  RAISE NOTICE 'Migration 0009 completed successfully!';
  RAISE NOTICE 'Added: tier and product_type columns to user_programs';
  RAISE NOTICE 'Added: winter_arc_premium_responses table';
  RAISE NOTICE 'Added: Helper functions for access control';
  RAISE NOTICE 'Added: View for premium posts queue';
  RAISE NOTICE 'Next steps:';
  RAISE NOTICE '1. Configure Stripe products with metadata';
  RAISE NOTICE '2. Update webhook to set tier based on product';
  RAISE NOTICE '3. Implement frontend access control';
END $$;
