// ParlayGalaxy Type Definitions

export interface Fixture {
  id: number;
  league_id: number;
  season: number;
  kickoff_time: string;
  status: string;
  venue: string | null;
  referee: string | null;
  home_team_id: number;
  home_team_name: string;
  away_team_id: number;
  away_team_name: string;
  home_score: number | null;
  away_score: number | null;
  round: string | null;
  last_synced_at: string;
  created_at: string;
  updated_at: string;
  // Enriched data from Galaxy API
  predictions?: Prediction[];
  quality_scores?: QualityScore[];
  odds?: OddsSnapshot[];
}

export interface Prediction {
  id: string;
  fixture_id: number;
  model_version: string;
  model_name: string;
  market_key: MarketKey;
  prediction: MatchWinnerPrediction | OverUnderPrediction | BothTeamsScorePrediction;
  confidence_score: number;
  quality_grade: QualityGrade;
  features_used: Record<string, unknown> | null;
  predicted_at: string;
  created_at: string;
}

export interface MatchWinnerPrediction {
  home_win: number;
  draw: number;
  away_win: number;
}

export interface OverUnderPrediction {
  over: number;
  under: number;
}

export interface BothTeamsScorePrediction {
  yes: number;
  no: number;
}

export interface QualityScore {
  id: string;
  fixture_id: number;
  market_key: MarketKey;
  data_coverage_score: number;
  model_confidence: number;
  historical_accuracy: number;
  final_grade: QualityGrade;
  reasoning: string;
  calculated_at: string;
  created_at: string;
}

export interface OddsSnapshot {
  id: string;
  fixture_id: number;
  bookmaker: string;
  market_key: MarketKey;
  odds_data: MatchWinnerOdds | OverUnderOdds | BothTeamsScoreOdds;
  minutes_before_kickoff: number | null;
  snapshot_at: string;
  created_at: string;
}

export interface MatchWinnerOdds {
  home: number;
  draw: number;
  away: number;
}

export interface OverUnderOdds {
  over: number;
  under: number;
}

export interface BothTeamsScoreOdds {
  yes: number;
  no: number;
}

export interface League {
  id: number;
  name: string;
  country: string;
  logo_url: string | null;
  is_active: boolean;
}

export type MarketKey = 'match_winner' | 'over_under_2.5' | 'over_under_3.5' | 'both_teams_score';
export type QualityGrade = 'A' | 'B' | 'C' | 'D' | 'F';
export type FixtureStatus = 'NS' | 'LIVE' | '1H' | 'HT' | '2H' | 'FT' | 'AET' | 'PEN' | 'PST' | 'CANC' | 'ABD';

// Multi-Market Prediction Types
export interface MultiMarketPrediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  kickoff_time: string;
  league_id: number;
  is_cup: boolean;
  quality_score: number;
  predictions: {
    over_under: Record<string, { over: number; under: number; line: number }>;
    team_goals: Record<string, { over: number; under: number; team: string; line: number }>;
    btts: { yes: number; no: number };
    corners: {
      expected: { home: number; away: number; total: number };
      [key: string]: { over?: number; under?: number } | { home: number; away: number; total: number };
    };
    cards: {
      expected: { home_yellow: number; away_yellow: number; total_yellow: number };
      [key: string]: { over?: number; under?: number } | { home_yellow: number; away_yellow: number; total_yellow: number };
    };
    shots: {
      expected: { 
        home_shots: number; 
        away_shots: number; 
        total_shots: number;
        home_shots_on_target: number;
        away_shots_on_target: number;
        total_shots_on_target: number;
      };
      [key: string]: { over?: number; under?: number } | object;
    };
    exact_scores: Array<{ home: number; away: number; score: string; probability: number }>;
    half_time: { home: number; draw: number; away: number };
    expected: { home_goals: number; away_goals: number; total_goals: number };
  };
}

// Player Stats Types
export interface PlayerStats {
  player_id: number;
  player_name: string;
  team_id: number;
  team_name: string;
  goals: number;
  assists: number;
  total_shots: number;
  shots_on_target: number;
  goals_per_90: number;
  shots_per_90?: number;
  shots_on_target_per_90?: number;
  appearances: number;
  games_played: number;
  minutes_played: number;
  yellow_cards?: number;
  red_cards?: number;
}

export interface TopPlayersResponse {
  status: string;
  count: number;
  total_players: number;
  total_teams: number;
  players: PlayerStats[];
}

// API Response types
export interface FixturesResponse {
  data: Fixture[];
  total?: number;
}

export interface StatsResponse {
  // New API format
  fixtures?: {
    total: number;
    upcoming: number;
    live: number;
  };
  predictions?: {
    total: number;
    grade_a: number;
    high_confidence: number;
  };
  leagues?: {
    active: number;
  };
  // Legacy format
  total_fixtures?: number;
  total_predictions?: number;
  avg_confidence?: number | null;
  grade_distribution?: Record<QualityGrade, number>;
}

// League ID to name mapping
export const LEAGUE_NAMES: Record<number, string> = {
  39: 'Premier League',
  140: 'La Liga',
  78: 'Bundesliga',
  135: 'Serie A',
  61: 'Ligue 1',
  94: 'Primeira Liga',
  88: 'Eredivisie',
  203: 'Süper Lig',
  2: 'Champions League',
  3: 'Europa League',
};

// League ID to country flag emoji
export const LEAGUE_FLAGS: Record<number, string> = {
  39: '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
  140: '🇪🇸',
  78: '🇩🇪',
  135: '🇮🇹',
  61: '🇫🇷',
  94: '🇵🇹',
  88: '🇳🇱',
  203: '🇹🇷',
  2: '🇪🇺',
  3: '🇪🇺',
};
