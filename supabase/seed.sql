-- ParlayGalaxy Seed Data
-- Adds sample data for development and testing

-- Clear existing data (be careful in production!)
TRUNCATE fixtures, odds_snapshots, model_predictions, quality_scores, watchlists CASCADE;

-- Insert sample fixtures for testing (Premier League - Week 23, Jan 2026)
INSERT INTO fixtures (id, league_id, season, kickoff_time, status, home_team_id, home_team_name, away_team_id, away_team_name, venue, round) VALUES
  -- Saturday, Jan 25, 2026
  (1234501, 39, 2025, '2026-01-25 12:30:00+00', 'NS', 33, 'Manchester United', 50, 'Manchester City', 'Old Trafford', 'Regular Season - 23'),
  (1234502, 39, 2025, '2026-01-25 15:00:00+00', 'NS', 40, 'Liverpool', 42, 'Arsenal', 'Anfield', 'Regular Season - 23'),
  (1234503, 39, 2025, '2026-01-25 15:00:00+00', 'NS', 49, 'Chelsea', 47, 'Tottenham', 'Stamford Bridge', 'Regular Season - 23'),
  (1234504, 39, 2025, '2026-01-25 17:30:00+00', 'NS', 34, 'Newcastle', 35, 'Aston Villa', 'St James Park', 'Regular Season - 23'),
  
  -- Sunday, Jan 26, 2026
  (1234505, 39, 2025, '2026-01-26 14:00:00+00', 'NS', 39, 'Wolverhampton', 45, 'Everton', 'Molineux', 'Regular Season - 23'),
  (1234506, 39, 2025, '2026-01-26 16:30:00+00', 'NS', 51, 'Brighton', 36, 'West Ham', 'Amex Stadium', 'Regular Season - 23'),
  
  -- La Liga - Same weekend
  (1234507, 140, 2025, '2026-01-25 20:00:00+00', 'NS', 529, 'Barcelona', 530, 'Real Madrid', 'Camp Nou', 'Regular Season - 21'),
  (1234508, 140, 2025, '2026-01-26 18:00:00+00', 'NS', 532, 'Atletico Madrid', 533, 'Sevilla', 'Wanda Metropolitano', 'Regular Season - 21'),
  
  -- Bundesliga
  (1234509, 78, 2025, '2026-01-25 14:30:00+00', 'NS', 157, 'Bayern Munich', 165, 'Borussia Dortmund', 'Allianz Arena', 'Regular Season - 19'),
  (1234510, 78, 2025, '2026-01-25 17:30:00+00', 'NS', 173, 'RB Leipzig', 168, 'Bayer Leverkusen', 'Red Bull Arena', 'Regular Season - 19');

-- Insert sample odds snapshots
INSERT INTO odds_snapshots (fixture_id, bookmaker, market_key, odds_data, snapshot_at) VALUES
  -- Manchester United vs Manchester City
  (1234501, 'Bet365', 'match_winner', '{"home": 3.20, "draw": 3.40, "away": 2.10}'::jsonb, NOW() - INTERVAL '2 hours'),
  (1234501, 'Bet365', 'over_under_2.5', '{"over": 1.85, "under": 2.00}'::jsonb, NOW() - INTERVAL '2 hours'),
  (1234501, 'Bet365', 'both_teams_score', '{"yes": 1.70, "no": 2.20}'::jsonb, NOW() - INTERVAL '2 hours'),
  
  -- Liverpool vs Arsenal
  (1234502, 'Bet365', 'match_winner', '{"home": 1.95, "draw": 3.60, "away": 3.80}'::jsonb, NOW() - INTERVAL '2 hours'),
  (1234502, 'Bet365', 'over_under_2.5', '{"over": 1.75, "under": 2.15}'::jsonb, NOW() - INTERVAL '2 hours'),
  
  -- Barcelona vs Real Madrid
  (1234507, 'Bet365', 'match_winner', '{"home": 2.30, "draw": 3.30, "away": 2.90}'::jsonb, NOW() - INTERVAL '3 hours'),
  (1234507, 'Bet365', 'over_under_3.5', '{"over": 2.50, "under": 1.55}'::jsonb, NOW() - INTERVAL '3 hours'),
  
  -- Bayern vs Dortmund
  (1234509, 'Bet365', 'match_winner', '{"home": 1.70, "draw": 3.80, "away": 4.50}'::jsonb, NOW() - INTERVAL '4 hours');

-- Insert sample predictions
INSERT INTO model_predictions (fixture_id, model_version, model_name, market_key, prediction, confidence_score, quality_grade) VALUES
  -- Manchester United vs Manchester City
  (1234501, 'v1.0.0', 'ensemble_xgb_elo', 'match_winner', 
   '{"home_win": 0.28, "draw": 0.30, "away_win": 0.42}'::jsonb, 0.75, 'A'),
  (1234501, 'v1.0.0', 'ensemble_xgb_elo', 'over_under_2.5', 
   '{"over": 0.58, "under": 0.42}'::jsonb, 0.68, 'B'),
  (1234501, 'v1.0.0', 'ensemble_xgb_elo', 'both_teams_score', 
   '{"yes": 0.65, "no": 0.35}'::jsonb, 0.72, 'A'),
  
  -- Liverpool vs Arsenal
  (1234502, 'v1.0.0', 'ensemble_xgb_elo', 'match_winner', 
   '{"home_win": 0.48, "draw": 0.28, "away_win": 0.24}'::jsonb, 0.82, 'A'),
  (1234502, 'v1.0.0', 'ensemble_xgb_elo', 'over_under_2.5', 
   '{"over": 0.62, "under": 0.38}'::jsonb, 0.71, 'A'),
  
  -- Chelsea vs Tottenham
  (1234503, 'v1.0.0', 'ensemble_xgb_elo', 'match_winner', 
   '{"home_win": 0.42, "draw": 0.30, "away_win": 0.28}'::jsonb, 0.65, 'B'),
  
  -- Barcelona vs Real Madrid
  (1234507, 'v1.0.0', 'ensemble_xgb_elo', 'match_winner', 
   '{"home_win": 0.38, "draw": 0.29, "away_win": 0.33}'::jsonb, 0.78, 'A'),
  
  -- Bayern vs Dortmund
  (1234509, 'v1.0.0', 'ensemble_xgb_elo', 'match_winner', 
   '{"home_win": 0.55, "draw": 0.25, "away_win": 0.20}'::jsonb, 0.80, 'A');

-- Insert quality scores
INSERT INTO quality_scores (fixture_id, market_key, data_coverage_score, model_confidence, historical_accuracy, final_grade, reasoning) VALUES
  (1234501, 'match_winner', 0.95, 0.75, 0.62, 'A', 'High data coverage, strong model confidence, good historical accuracy'),
  (1234501, 'over_under_2.5', 0.90, 0.68, 0.58, 'B', 'Good coverage but slightly lower confidence'),
  (1234502, 'match_winner', 0.98, 0.82, 0.65, 'A', 'Excellent data quality, high confidence'),
  (1234503, 'match_winner', 0.85, 0.65, 0.54, 'B', 'Moderate confidence due to recent form volatility'),
  (1234507, 'match_winner', 0.92, 0.78, 0.60, 'A', 'Classic fixture with rich historical data'),
  (1234509, 'match_winner', 0.94, 0.80, 0.63, 'A', 'Top-tier matchup with comprehensive stats');

-- Note: Watchlist entries will be added by authenticated users through the app
-- This seed file doesn't include watchlist data as it requires auth.uid()

-- Add comments
COMMENT ON TABLE fixtures IS 'Sample fixtures loaded for development';
COMMENT ON TABLE odds_snapshots IS 'Sample odds from major bookmakers';
COMMENT ON TABLE model_predictions IS 'Sample predictions from ensemble model v1.0.0';
