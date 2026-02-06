-- Add International Leagues - Latin America, Asia, Oceania
-- Version: 1.1.0
-- Date: 2026-01-30

-- Insert new leagues with active status
INSERT INTO leagues (id, name, country, season, coverage, is_active) VALUES
-- Europe - Secondary Leagues
(94, 'Primeira Liga', 'Portugal', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(88, 'Eredivisie', 'Netherlands', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(203, 'Super Lig', 'Turkey', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(144, 'Belgian Pro League', 'Belgium', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),

-- Latin America - Major Leagues
(262, 'Liga MX', 'Mexico', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(128, 'Liga Profesional', 'Argentina', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(71, 'Brasileirão Serie A', 'Brazil', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(281, 'Primera División', 'Peru', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(239, 'Primera A', 'Colombia', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),

-- South America - International
(13, 'Copa Libertadores', 'South America', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(11, 'CONMEBOL Sudamericana', 'South America', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),

-- North America
(253, 'MLS', 'USA', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),

-- Asia & Oceania
(188, 'A-League', 'Australia', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),
(235, 'Saudi Pro League', 'Saudi Arabia', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true),

-- Europe - Conference League
(848, 'Conference League', 'Europe', 2025, '{"fixtures": true, "odds": true, "standings": true}'::jsonb, true)

ON CONFLICT (id, season) DO UPDATE SET
  name = EXCLUDED.name,
  country = EXCLUDED.country,
  coverage = EXCLUDED.coverage,
  is_active = EXCLUDED.is_active,
  updated_at = NOW();

-- Add index for country-based queries (optimize league filtering by region)
CREATE INDEX IF NOT EXISTS idx_leagues_country_active 
ON leagues(country, is_active) 
WHERE is_active = true;

-- Add comment for documentation
COMMENT ON TABLE leagues IS 'Official football leagues and competitions. Now includes 24 leagues across Europe, Latin America, North America, Asia, and Oceania.';
