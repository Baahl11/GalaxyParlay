-- Team Elo Ratings Table
-- Version: 1.0.0
-- Date: 2026-01-27
-- Purpose: Store persistent Elo ratings for teams to improve prediction accuracy

-- ============================================================================
-- TEAM ELO RATINGS
-- ============================================================================

CREATE TABLE team_elo_ratings (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_id BIGINT NOT NULL,
  team_name TEXT NOT NULL,
  league_id BIGINT NOT NULL,
  
  -- Current rating
  elo_rating NUMERIC(7,2) NOT NULL DEFAULT 1500.00,
  
  -- Stats for tracking
  matches_played INT NOT NULL DEFAULT 0,
  wins INT NOT NULL DEFAULT 0,
  draws INT NOT NULL DEFAULT 0,
  losses INT NOT NULL DEFAULT 0,
  goals_for INT NOT NULL DEFAULT 0,
  goals_against INT NOT NULL DEFAULT 0,
  
  -- Peak tracking
  peak_rating NUMERIC(7,2) NOT NULL DEFAULT 1500.00,
  peak_date TIMESTAMPTZ,
  
  -- Last match info
  last_match_id BIGINT,
  last_match_date TIMESTAMPTZ,
  last_rating_change NUMERIC(5,2) DEFAULT 0,
  
  -- Metadata
  season INT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  -- Unique constraint: one rating per team per season
  UNIQUE (team_id, season)
);

-- Indexes for fast lookups
CREATE INDEX idx_elo_team ON team_elo_ratings(team_id);
CREATE INDEX idx_elo_league ON team_elo_ratings(league_id);
CREATE INDEX idx_elo_rating ON team_elo_ratings(elo_rating DESC);
CREATE INDEX idx_elo_season ON team_elo_ratings(season);

-- ============================================================================
-- ELO HISTORY (for tracking rating changes over time)
-- ============================================================================

CREATE TABLE team_elo_history (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  team_id BIGINT NOT NULL,
  fixture_id BIGINT REFERENCES fixtures(id) ON DELETE SET NULL,
  
  -- Rating change
  rating_before NUMERIC(7,2) NOT NULL,
  rating_after NUMERIC(7,2) NOT NULL,
  rating_change NUMERIC(5,2) NOT NULL,
  
  -- Match context
  opponent_id BIGINT NOT NULL,
  opponent_rating NUMERIC(7,2) NOT NULL,
  was_home BOOLEAN NOT NULL,
  goals_for INT NOT NULL,
  goals_against INT NOT NULL,
  result TEXT NOT NULL, -- 'W', 'D', 'L'
  
  -- Timing
  match_date TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_elo_history_team ON team_elo_history(team_id);
CREATE INDEX idx_elo_history_date ON team_elo_history(match_date);
CREATE INDEX idx_elo_history_fixture ON team_elo_history(fixture_id);

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Function to get current Elo for a team
CREATE OR REPLACE FUNCTION get_team_elo(p_team_id BIGINT, p_season INT DEFAULT 2025)
RETURNS NUMERIC AS $$
DECLARE
  v_rating NUMERIC;
BEGIN
  SELECT elo_rating INTO v_rating
  FROM team_elo_ratings
  WHERE team_id = p_team_id AND season = p_season;
  
  -- Return default if not found
  RETURN COALESCE(v_rating, 1500.00);
END;
$$ LANGUAGE plpgsql;

-- Function to get Elo rating label
CREATE OR REPLACE FUNCTION get_elo_tier(p_rating NUMERIC)
RETURNS TEXT AS $$
BEGIN
  RETURN CASE
    WHEN p_rating >= 1800 THEN 'Elite'
    WHEN p_rating >= 1700 THEN 'Top Tier'
    WHEN p_rating >= 1600 THEN 'Strong'
    WHEN p_rating >= 1500 THEN 'Average'
    WHEN p_rating >= 1400 THEN 'Below Average'
    ELSE 'Weak'
  END;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE team_elo_ratings IS 'Persistent Elo ratings for all teams, updated after each match';
COMMENT ON TABLE team_elo_history IS 'Historical record of all Elo rating changes for trend analysis';
COMMENT ON COLUMN team_elo_ratings.elo_rating IS 'Current Elo rating (1200-2000 range, 1500 = average)';
COMMENT ON COLUMN team_elo_ratings.peak_rating IS 'Highest Elo rating achieved this season';
