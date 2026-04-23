-- Referee Statistics Table
-- Stores referee-level cards bias and strictness for cards/fouls markets

CREATE TABLE IF NOT EXISTS referee_statistics (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    referee_id INTEGER,
    referee_name TEXT NOT NULL,
    league_id INTEGER NOT NULL,
    season INTEGER NOT NULL,

    total_games INTEGER DEFAULT 0,
    avg_yellow_cards DECIMAL(4,2),
    avg_red_cards DECIMAL(4,3),
    strictness_score DECIMAL(4,2),
    consistency_score DECIMAL(4,2),
    home_bias DECIMAL(4,2),

    stats_data JSONB,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(referee_name, league_id, season)
);

CREATE INDEX IF NOT EXISTS idx_referee_stats_name ON referee_statistics(referee_name);
CREATE INDEX IF NOT EXISTS idx_referee_stats_league ON referee_statistics(league_id);

COMMENT ON TABLE referee_statistics IS 'Referee statistics for cards/fouls bias modeling';
