-- Add statistics columns to fixtures table
-- These are needed to verify predictions for corners, cards, shots, offsides, etc.

ALTER TABLE fixtures
ADD COLUMN corners_home INT,
ADD COLUMN corners_away INT,
ADD COLUMN cards_home INT,
ADD COLUMN cards_away INT,
ADD COLUMN shots_on_target_home INT,
ADD COLUMN shots_on_target_away INT,
ADD COLUMN offsides_home INT,
ADD COLUMN offsides_away INT,
ADD COLUMN half_time_home_score INT,
ADD COLUMN half_time_away_score INT;

-- Add indexes for common queries
CREATE INDEX idx_fixtures_corners ON fixtures(corners_home, corners_away) WHERE corners_home IS NOT NULL;
CREATE INDEX idx_fixtures_cards ON fixtures(cards_home, cards_away) WHERE cards_home IS NOT NULL;

-- Comment on columns
COMMENT ON COLUMN fixtures.corners_home IS 'Total corner kicks for home team';
COMMENT ON COLUMN fixtures.corners_away IS 'Total corner kicks for away team';
COMMENT ON COLUMN fixtures.cards_home IS 'Total yellow + red cards for home team';
COMMENT ON COLUMN fixtures.cards_away IS 'Total yellow + red cards for away team';
COMMENT ON COLUMN fixtures.shots_on_target_home IS 'Shots on target for home team';
COMMENT ON COLUMN fixtures.shots_on_target_away IS 'Shots on target for away team';
COMMENT ON COLUMN fixtures.offsides_home IS 'Total offsides for home team';
COMMENT ON COLUMN fixtures.offsides_away IS 'Total offsides for away team';
COMMENT ON COLUMN fixtures.half_time_home_score IS 'Home team score at half time';
COMMENT ON COLUMN fixtures.half_time_away_score IS 'Away team score at half time';
