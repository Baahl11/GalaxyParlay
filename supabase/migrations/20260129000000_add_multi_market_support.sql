-- Migration: Add support for multiple betting markets
-- Date: 2026-01-29
-- Description: Expand market_key validation to include corners, cards, offsides, shots

-- Drop existing constraint if it exists
ALTER TABLE predictions 
DROP CONSTRAINT IF EXISTS predictions_market_key_check;

-- Add new constraint with ALL supported markets
ALTER TABLE predictions
ADD CONSTRAINT predictions_market_key_check 
CHECK (market_key IN (
    -- Core markets
    'match_winner',
    'over_under_2.5',
    'both_teams_score',
    
    -- Additional goal lines
    'over_under_0_5',
    'over_under_1_5',
    'over_under_3_5',
    'over_under_4_5',
    
    -- Corners
    'corners_over_under_7_5',
    'corners_over_under_8_5',
    'corners_over_under_9_5',
    'corners_over_under_10_5',
    'corners_over_under_11_5',
    'corners_over_under_12_5',
    
    -- Cards
    'cards_over_under_2_5',
    'cards_over_under_3_5',
    'cards_over_under_4_5',
    'cards_over_under_5_5',
    'cards_over_under_6_5',
    
    -- Shots on Target
    'shots_on_target_over_under_6_5',
    'shots_on_target_over_under_7_5',
    'shots_on_target_over_under_8_5',
    'shots_on_target_over_under_9_5',
    'shots_on_target_over_under_10_5',
    
    -- Offsides
    'offsides_over_under_3_5',
    'offsides_over_under_4_5',
    'offsides_over_under_5_5',
    'offsides_over_under_6_5',
    
    -- Team-specific goals
    'home_team_over_under_0_5',
    'home_team_over_under_1_5',
    'home_team_over_under_2_5',
    'away_team_over_under_0_5',
    'away_team_over_under_1_5',
    'away_team_over_under_2_5',
    
    -- First Half
    'first_half_over_under_0_5',
    'first_half_over_under_1_5'
));

-- Same for quality_scores table
ALTER TABLE quality_scores
DROP CONSTRAINT IF EXISTS quality_scores_market_key_check;

ALTER TABLE quality_scores
ADD CONSTRAINT quality_scores_market_key_check 
CHECK (market_key IN (
    -- Core markets
    'match_winner',
    'over_under_2.5',
    'both_teams_score',
    
    -- Additional goal lines
    'over_under_0_5',
    'over_under_1_5',
    'over_under_3_5',
    'over_under_4_5',
    
    -- Corners
    'corners_over_under_7_5',
    'corners_over_under_8_5',
    'corners_over_under_9_5',
    'corners_over_under_10_5',
    'corners_over_under_11_5',
    'corners_over_under_12_5',
    
    -- Cards
    'cards_over_under_2_5',
    'cards_over_under_3_5',
    'cards_over_under_4_5',
    'cards_over_under_5_5',
    'cards_over_under_6_5',
    
    -- Shots on Target
    'shots_on_target_over_under_6_5',
    'shots_on_target_over_under_7_5',
    'shots_on_target_over_under_8_5',
    'shots_on_target_over_under_9_5',
    'shots_on_target_over_under_10_5',
    
    -- Offsides
    'offsides_over_under_3_5',
    'offsides_over_under_4_5',
    'offsides_over_under_5_5',
    'offsides_over_under_6_5',
    
    -- Team-specific goals
    'home_team_over_under_0_5',
    'home_team_over_under_1_5',
    'home_team_over_under_2_5',
    'away_team_over_under_0_5',
    'away_team_over_under_1_5',
    'away_team_over_under_2_5',
    
    -- First Half
    'first_half_over_under_0_5',
    'first_half_over_under_1_5'
));

-- Create index for faster market_key queries
CREATE INDEX IF NOT EXISTS idx_predictions_market_key 
ON predictions(market_key);

CREATE INDEX IF NOT EXISTS idx_quality_scores_market_key 
ON quality_scores(market_key);

-- Create composite index for fixture + market queries (common query pattern)
CREATE INDEX IF NOT EXISTS idx_predictions_fixture_market 
ON predictions(fixture_id, market_key);

CREATE INDEX IF NOT EXISTS idx_quality_scores_fixture_market 
ON quality_scores(fixture_id, market_key);

-- Comment for documentation
COMMENT ON CONSTRAINT predictions_market_key_check ON predictions IS 
'Validates betting market types. Updated 2026-01-29 to include corners, cards, offsides, shots markets.';

COMMENT ON CONSTRAINT quality_scores_market_key_check ON quality_scores IS 
'Validates betting market types for quality scores. Updated 2026-01-29 to include corners, cards, offsides, shots markets.';
