-- ParlayGalaxy Initial Schema Migration
-- Version: 1.0.0
-- Date: 2026-01-23

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For fuzzy text search

-- ============================================================================
-- TABLES
-- ============================================================================

-- Leagues (official competitions)
CREATE TABLE leagues (
  id BIGINT PRIMARY KEY,
  name TEXT NOT NULL,
  country TEXT NOT NULL,
  logo_url TEXT,
  season INT NOT NULL,
  coverage JSONB NOT NULL DEFAULT '{}',
  is_active BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (id, season)
);

CREATE INDEX idx_leagues_active ON leagues(is_active) WHERE is_active = true;
CREATE INDEX idx_leagues_country ON leagues(country);
CREATE INDEX idx_leagues_season ON leagues(season);


-- Fixtures (matches)
CREATE TABLE fixtures (
  id BIGINT PRIMARY KEY,
  league_id BIGINT NOT NULL REFERENCES leagues(id),
  season INT NOT NULL,
  
  -- Match details
  kickoff_time TIMESTAMPTZ NOT NULL,
  status TEXT NOT NULL, -- 'NS', 'TBD', 'LIVE', 'FT', 'CANC'
  venue TEXT,
  referee TEXT,
  
  -- Teams
  home_team_id BIGINT NOT NULL,
  home_team_name TEXT NOT NULL,
  away_team_id BIGINT NOT NULL,
  away_team_name TEXT NOT NULL,
  
  -- Score (null for pre-match)
  home_score INT,
  away_score INT,
  
  -- Metadata
  round TEXT, -- e.g., "Regular Season - 23"
  last_synced_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fixtures_kickoff ON fixtures(kickoff_time);
CREATE INDEX idx_fixtures_league ON fixtures(league_id);
CREATE INDEX idx_fixtures_status ON fixtures(status);
CREATE INDEX idx_fixtures_teams ON fixtures(home_team_id, away_team_id);
CREATE INDEX idx_fixtures_week ON fixtures(kickoff_time, league_id) 
  WHERE status IN ('NS', 'TBD');


-- Odds snapshots (historical odds data)
CREATE TABLE odds_snapshots (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fixture_id BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  
  -- Odds data
  bookmaker TEXT NOT NULL,
  market_key TEXT NOT NULL, -- 'match_winner', 'over_under_2.5', etc.
  odds_data JSONB NOT NULL, -- { "home": 2.1, "draw": 3.4, "away": 3.2 }
  
  -- Timing
  snapshot_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  minutes_before_kickoff INT, -- Calculated field
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_odds_fixture ON odds_snapshots(fixture_id);
CREATE INDEX idx_odds_market ON odds_snapshots(market_key);
CREATE INDEX idx_odds_fixture_market ON odds_snapshots(fixture_id, market_key);
CREATE INDEX idx_odds_snapshot_time ON odds_snapshots(snapshot_at);


-- Model predictions
CREATE TABLE model_predictions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fixture_id BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  
  -- Model info
  model_version TEXT NOT NULL, -- 'v1.2.3'
  model_name TEXT NOT NULL, -- 'ensemble_xgb_elo'
  
  -- Prediction
  market_key TEXT NOT NULL,
  prediction JSONB NOT NULL, -- { "home_win": 0.45, "draw": 0.30, "away_win": 0.25 }
  
  -- Confidence & Quality
  confidence_score DECIMAL(3,2), -- 0.00 to 1.00
  quality_grade TEXT, -- 'A', 'B', 'C'
  
  -- Metadata
  predicted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  features_used JSONB, -- Store feature values for debugging
  
  created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_predictions_fixture ON model_predictions(fixture_id);
CREATE INDEX idx_predictions_market ON model_predictions(market_key);
CREATE INDEX idx_predictions_quality ON model_predictions(quality_grade);
CREATE INDEX idx_predictions_version ON model_predictions(model_version);


-- Quality scores (per fixture/market)
CREATE TABLE quality_scores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  fixture_id BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  market_key TEXT NOT NULL,
  
  -- Quality components
  data_coverage_score DECIMAL(3,2) NOT NULL, -- 0.00 to 1.00
  model_confidence DECIMAL(3,2) NOT NULL,
  historical_accuracy DECIMAL(3,2),
  
  -- Final grade
  final_grade TEXT NOT NULL, -- 'A', 'B', 'C'
  reasoning TEXT, -- Human-readable explanation
  
  calculated_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (fixture_id, market_key)
);

CREATE INDEX idx_quality_fixture ON quality_scores(fixture_id);
CREATE INDEX idx_quality_grade ON quality_scores(final_grade);


-- Watchlist (user's favorite fixtures)
CREATE TABLE watchlists (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  fixture_id BIGINT NOT NULL REFERENCES fixtures(id) ON DELETE CASCADE,
  
  -- Preferences
  markets_of_interest TEXT[] DEFAULT ARRAY[]::TEXT[], -- ['match_winner', 'over_2.5']
  notes TEXT,
  
  added_at TIMESTAMPTZ DEFAULT NOW(),
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE (user_id, fixture_id)
);

CREATE INDEX idx_watchlist_user ON watchlists(user_id);
CREATE INDEX idx_watchlist_fixture ON watchlists(fixture_id);


-- ============================================================================
-- FUNCTIONS
-- ============================================================================

-- Auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Calculate minutes before kickoff for odds
CREATE OR REPLACE FUNCTION calculate_minutes_before_kickoff()
RETURNS TRIGGER AS $$
BEGIN
  NEW.minutes_before_kickoff := EXTRACT(EPOCH FROM (
    (SELECT kickoff_time FROM fixtures WHERE id = NEW.fixture_id) - NEW.snapshot_at
  ))::INT / 60;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================================
-- TRIGGERS
-- ============================================================================

-- Auto-update timestamps
CREATE TRIGGER update_leagues_updated_at
  BEFORE UPDATE ON leagues
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER update_fixtures_updated_at
  BEFORE UPDATE ON fixtures
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Calculate minutes before kickoff
CREATE TRIGGER calc_odds_minutes_before
  BEFORE INSERT ON odds_snapshots
  FOR EACH ROW EXECUTE FUNCTION calculate_minutes_before_kickoff();


-- ============================================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS
ALTER TABLE leagues ENABLE ROW LEVEL SECURITY;
ALTER TABLE fixtures ENABLE ROW LEVEL SECURITY;
ALTER TABLE odds_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE model_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE quality_scores ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;

-- Public read for non-sensitive tables
CREATE POLICY "Public read leagues"
  ON leagues FOR SELECT
  TO anon, authenticated
  USING (is_active = true);

CREATE POLICY "Public read fixtures"
  ON fixtures FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Public read odds"
  ON odds_snapshots FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Public read predictions"
  ON model_predictions FOR SELECT
  TO anon, authenticated
  USING (true);

CREATE POLICY "Public read quality"
  ON quality_scores FOR SELECT
  TO anon, authenticated
  USING (true);

-- Watchlist: users can only see their own
CREATE POLICY "Users see own watchlist"
  ON watchlists FOR SELECT
  TO authenticated
  USING (auth.uid() = user_id);

CREATE POLICY "Users insert own watchlist"
  ON watchlists FOR INSERT
  TO authenticated
  WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users delete own watchlist"
  ON watchlists FOR DELETE
  TO authenticated
  USING (auth.uid() = user_id);

-- Service role bypasses RLS (for worker)


-- ============================================================================
-- GRANTS
-- ============================================================================

-- Grant service role full access
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO service_role;

-- Grant anon limited read access
GRANT SELECT ON leagues TO anon;
GRANT SELECT ON fixtures TO anon;
GRANT SELECT ON odds_snapshots TO anon;
GRANT SELECT ON model_predictions TO anon;
GRANT SELECT ON quality_scores TO anon;

-- Grant authenticated users read + watchlist management
GRANT SELECT ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT INSERT, UPDATE, DELETE ON watchlists TO authenticated;


-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- Seed Top 10 Leagues (V1 Scope)
INSERT INTO leagues (id, name, country, season, is_active) VALUES
  (39, 'Premier League', 'England', 2025, true),
  (140, 'La Liga', 'Spain', 2025, true),
  (61, 'Ligue 1', 'France', 2025, true),
  (78, 'Bundesliga', 'Germany', 2025, true),
  (135, 'Serie A', 'Italy', 2025, true),
  (94, 'Primeira Liga', 'Portugal', 2025, true),
  (88, 'Eredivisie', 'Netherlands', 2025, true),
  (203, 'Süper Lig', 'Turkey', 2025, true),
  (2, 'UEFA Champions League', 'Europe', 2025, true),
  (3, 'UEFA Europa League', 'Europe', 2025, true)
ON CONFLICT (id, season) DO NOTHING;


-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON TABLE leagues IS 'Official football leagues/competitions';
COMMENT ON TABLE fixtures IS 'Football matches with pre-match and live data';
COMMENT ON TABLE odds_snapshots IS 'Historical odds data from bookmakers';
COMMENT ON TABLE model_predictions IS 'ML model predictions for fixtures';
COMMENT ON TABLE quality_scores IS 'Data quality scoring per fixture/market';
COMMENT ON TABLE watchlists IS 'User watchlist for tracking favorite fixtures';

COMMENT ON COLUMN fixtures.status IS 'Match status: NS=Not Started, TBD=To Be Defined, LIVE=In Progress, FT=Full Time, CANC=Cancelled';
COMMENT ON COLUMN model_predictions.quality_grade IS 'A=High confidence, B=Medium, C=Low/Unreliable';
