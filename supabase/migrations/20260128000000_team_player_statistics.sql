-- Team Statistics Table
-- Stores detailed team statistics from API-Football

CREATE TABLE IF NOT EXISTS team_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    team_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    stats_data JSONB NOT NULL,
    
    -- Denormalized for quick queries
    goals_scored_avg DECIMAL(4,2),
    goals_conceded_avg DECIMAL(4,2),
    clean_sheets_total INTEGER,
    yellow_cards_avg DECIMAL(4,2),
    red_cards_avg DECIMAL(4,2),
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(team_id, league_id, season)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_team_stats_team ON team_statistics(team_id);
CREATE INDEX IF NOT EXISTS idx_team_stats_league ON team_statistics(league_id);

-- Player Statistics Table (for player props markets)
CREATE TABLE IF NOT EXISTS player_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    -- Goals and assists
    goals INTEGER DEFAULT 0,
    assists INTEGER DEFAULT 0,
    goals_per_90 DECIMAL(4,2),
    
    -- Shots
    total_shots INTEGER DEFAULT 0,
    shots_on_target INTEGER DEFAULT 0,
    shots_per_90 DECIMAL(4,2),
    shots_on_target_per_90 DECIMAL(4,2),
    
    -- Cards
    yellow_cards INTEGER DEFAULT 0,
    red_cards INTEGER DEFAULT 0,
    
    -- Minutes
    games_played INTEGER DEFAULT 0,
    minutes_played INTEGER DEFAULT 0,
    
    stats_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(player_id, league_id, season)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_player_stats_team ON player_statistics(team_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_player ON player_statistics(player_id);
CREATE INDEX IF NOT EXISTS idx_player_stats_goals ON player_statistics(goals DESC);
CREATE INDEX IF NOT EXISTS idx_player_stats_shots ON player_statistics(total_shots DESC);

-- Corner Statistics Table (historical averages)
CREATE TABLE IF NOT EXISTS corner_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    team_id INTEGER NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    
    corners_for_avg DECIMAL(4,2),
    corners_against_avg DECIMAL(4,2),
    corners_total_avg DECIMAL(4,2),
    
    first_half_corners_avg DECIMAL(4,2),
    second_half_corners_avg DECIMAL(4,2),
    
    matches_analyzed INTEGER DEFAULT 0,
    
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(team_id, league_id, season)
);

CREATE INDEX IF NOT EXISTS idx_corner_stats_team ON corner_statistics(team_id);

-- Comments
COMMENT ON TABLE team_statistics IS 'Detailed team statistics from API-Football for multi-market predictions';
COMMENT ON TABLE player_statistics IS 'Player statistics for player props markets (goals, shots, cards)';
COMMENT ON TABLE corner_statistics IS 'Historical corner statistics per team for corner market predictions';
