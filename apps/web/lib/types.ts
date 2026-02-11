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
  prediction:
    | MatchWinnerPrediction
    | OverUnderPrediction
    | BothTeamsScorePrediction;
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

export type MarketKey =
  | "match_winner"
  | "over_under_2.5"
  | "over_under_3.5"
  | "both_teams_score";
export type QualityGrade = "A" | "B" | "C" | "D" | "F";
export type FixtureStatus =
  | "NS"
  | "LIVE"
  | "1H"
  | "HT"
  | "2H"
  | "FT"
  | "AET"
  | "PEN"
  | "PST"
  | "CANC"
  | "ABD";

// Multi-Market Prediction Types
export interface MultiMarketPrediction {
  fixture_id: number;
  home_team: string;
  away_team: string;
  kickoff_time: string;
  league_id: number;
  is_cup: boolean;
  quality_score?: number; // Optional - may not be in backend response
  predictions: {
    over_under: Record<string, { over: number; under: number; line: number }>;
    team_goals: Record<
      string,
      { over: number; under: number; team: string; line: number }
    >;
    btts: { yes: number; no: number };
    corners: {
      expected: { home: number; away: number; total: number };
      [key: string]:
        | { over?: number; under?: number }
        | { home: number; away: number; total: number };
    };
    cards: {
      expected: {
        home_yellow: number;
        away_yellow: number;
        total_yellow: number;
        referee?: string;
        referee_avg?: number;
      };
      [key: string]:
        | { over?: number; under?: number }
        | { 
            home_yellow: number; 
            away_yellow: number; 
            total_yellow: number; 
            referee?: string; 
            referee_avg?: number; 
          };
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
    offsides?: {
      expected?: { home: number; away: number; total: number };
      features?: {
        home_tempo: number;
        away_tempo: number;
        home_defensive_line: number;
        away_defensive_line: number;
      };
      [key: string]: any; // Flexible index for dynamic prediction keys
    };
    exact_scores: Array<{
      home: number;
      away: number;
      score: string;
      probability: number;
    }>;
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
  data?: Fixture[]; // Legacy format
  fixtures?: Fixture[]; // Backend Railway format
  total?: number;
  count?: number;
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
  // Europa - Primera División
  39: "Premier League",
  140: "La Liga",
  78: "Bundesliga",
  135: "Serie A",
  61: "Ligue 1",
  94: "Primeira Liga",
  88: "Eredivisie",
  203: "Süper Lig",
  144: "Jupiler Pro League",
  235: "Russian Premier League",
  // Europa - Segunda División
  40: "Championship",
  141: "LaLiga 2",
  136: "Serie B",
  79: "2. Bundesliga",
  62: "Ligue 2",
  // Copas nacionales
  48: "FA Cup",
  81: "DFB Pokal",
  137: "Coppa Italia",
  143: "Copa del Rey",
  66: "Coupe de France",
  // LATAM
  262: "Liga MX",
  274: "Primera División Chile",
  273: "Primera División Uruguay",
  271: "Primera División Venezuela",
  71: "Brasileirão",
  128: "Liga Argentina",
  253: "MLS",
  // Asia
  307: "Saudi Pro League",
  188: "J1 League",
  // Copas internacionales
  2: "Champions League",
  3: "Europa League",
  848: "Conference League",
  13: "Copa Libertadores",
  11: "Copa Sudamericana",
  16: "CONCACAF Champions",
};

// League ID to country flag emoji
export const LEAGUE_FLAGS: Record<number, string> = {
  39: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  140: "🇪🇸",
  78: "🇩🇪",
  135: "🇮🇹",
  61: "🇫🇷",
  94: "🇵🇹",
  88: "🇳🇱",
  203: "🇹🇷",
  144: "🇧🇪",
  235: "🇷🇺",
  // Europa - Segunda División
  40: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  141: "🇪🇸",
  136: "🇮🇹",
  79: "🇩🇪",
  62: "🇫🇷",
  2: "🇪🇺",
  3: "🇪🇺",
  // Copas nacionales
  48: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  81: "🇩🇪",
  137: "🇮🇹",
  143: "🇪🇸",
  66: "🇫🇷",
  // LATAM
  262: "🇲🇽",
  274: "🇨🇱",
  273: "🇺🇾",
  271: "🇻🇪",
  71: "🇧🇷",
  128: "🇦🇷",
  253: "🇺🇸",
  // Asia
  307: "🇸🇦",
  188: "🇯🇵",
  // Copas internacionales
  848: "🇪🇺",
  13: "🌎",
  11: "🌎",
  16: "🌎",
};

// League ID to country mapping
export const LEAGUE_COUNTRIES: Record<number, string> = {
  39: "England",
  140: "Spain",
  78: "Germany",
  135: "Italy",
  61: "France",
  94: "Portugal",
  88: "Netherlands",
  203: "Turkey",
  144: "Belgium",
  235: "Russia",
  40: "England",
  141: "Spain",
  136: "Italy",
  79: "Germany",
  62: "France",
  2: "Europe",
  3: "Europe",
  48: "England",
  81: "Germany",
  137: "Italy",
  143: "Spain",
  66: "France",
  262: "Mexico",
  274: "Chile",
  273: "Uruguay",
  271: "Venezuela",
  71: "Brazil",
  128: "Argentina",
  253: "USA",
  307: "Saudi Arabia",
  188: "Japan",
  848: "Europe",
  13: "South America",
  11: "South America",
  16: "North America",
};

// League detailed info
export const LEAGUE_INFO: Record<
  number,
  { name: string; country: string; logo?: string }
> = {
  39: {
    name: "Premier League",
    country: "England",
    logo: "https://media.api-sports.io/football/leagues/39.png",
  },
  140: {
    name: "La Liga",
    country: "Spain",
    logo: "https://media.api-sports.io/football/leagues/140.png",
  },
  78: {
    name: "Bundesliga",
    country: "Germany",
    logo: "https://media.api-sports.io/football/leagues/78.png",
  },
  135: {
    name: "Serie A",
    country: "Italy",
    logo: "https://media.api-sports.io/football/leagues/135.png",
  },
  61: {
    name: "Ligue 1",
    country: "France",
    logo: "https://media.api-sports.io/football/leagues/61.png",
  },
  94: {
    name: "Primeira Liga",
    country: "Portugal",
    logo: "https://media.api-sports.io/football/leagues/94.png",
  },
  88: {
    name: "Eredivisie",
    country: "Netherlands",
    logo: "https://media.api-sports.io/football/leagues/88.png",
  },
  203: {
    name: "Süper Lig",
    country: "Turkey",
    logo: "https://media.api-sports.io/football/leagues/203.png",
  },
  2: {
    name: "Champions League",
    country: "Europe",
    logo: "https://media.api-sports.io/football/leagues/2.png",
  },
  3: {
    name: "Europa League",
    country: "Europe",
    logo: "https://media.api-sports.io/football/leagues/3.png",
  },
  48: {
    name: "FA Cup",
    country: "England",
    logo: "https://media.api-sports.io/football/leagues/48.png",
  },
  81: {
    name: "DFB Pokal",
    country: "Germany",
    logo: "https://media.api-sports.io/football/leagues/81.png",
  },
  137: {
    name: "Coppa Italia",
    country: "Italy",
    logo: "https://media.api-sports.io/football/leagues/137.png",
  },
  143: {
    name: "Copa del Rey",
    country: "Spain",
    logo: "https://media.api-sports.io/football/leagues/143.png",
  },
  66: {
    name: "Coupe de France",
    country: "France",
    logo: "https://media.api-sports.io/football/leagues/66.png",
  },
  40: {
    name: "Championship",
    country: "England",
    logo: "https://media.api-sports.io/football/leagues/40.png",
  },
  141: {
    name: "LaLiga 2",
    country: "Spain",
    logo: "https://media.api-sports.io/football/leagues/141.png",
  },
  136: {
    name: "Serie B",
    country: "Italy",
    logo: "https://media.api-sports.io/football/leagues/136.png",
  },
  79: {
    name: "2. Bundesliga",
    country: "Germany",
    logo: "https://media.api-sports.io/football/leagues/79.png",
  },
  62: {
    name: "Ligue 2",
    country: "France",
    logo: "https://media.api-sports.io/football/leagues/62.png",
  },
  144: {
    name: "Jupiler Pro League",
    country: "Belgium",
    logo: "https://media.api-sports.io/football/leagues/144.png",
  },
  235: {
    name: "Russian Premier League",
    country: "Russia",
    logo: "https://media.api-sports.io/football/leagues/235.png",
  },
  262: {
    name: "Liga MX",
    country: "Mexico",
    logo: "https://media.api-sports.io/football/leagues/262.png",
  },
  274: {
    name: "Primera División Chile",
    country: "Chile",
    logo: "https://media.api-sports.io/football/leagues/274.png",
  },
  273: {
    name: "Primera División Uruguay",
    country: "Uruguay",
    logo: "https://media.api-sports.io/football/leagues/273.png",
  },
  271: {
    name: "Primera División Venezuela",
    country: "Venezuela",
    logo: "https://media.api-sports.io/football/leagues/271.png",
  },
  71: {
    name: "Brasileirão",
    country: "Brazil",
    logo: "https://media.api-sports.io/football/leagues/71.png",
  },
  128: {
    name: "Liga Argentina",
    country: "Argentina",
    logo: "https://media.api-sports.io/football/leagues/128.png",
  },
  253: {
    name: "MLS",
    country: "USA",
    logo: "https://media.api-sports.io/football/leagues/253.png",
  },
  188: {
    name: "J1 League",
    country: "Japan",
    logo: "https://media.api-sports.io/football/leagues/188.png",
  },
  307: {
    name: "Saudi Pro League",
    country: "Saudi Arabia",
    logo: "https://media.api-sports.io/football/leagues/307.png",
  },
  848: {
    name: "Conference League",
    country: "Europe",
    logo: "https://media.api-sports.io/football/leagues/848.png",
  },
  13: {
    name: "Copa Libertadores",
    country: "South America",
    logo: "https://media.api-sports.io/football/leagues/13.png",
  },
  11: {
    name: "Copa Sudamericana",
    country: "South America",
    logo: "https://media.api-sports.io/football/leagues/11.png",
  },
  16: {
    name: "CONCACAF Champions",
    country: "North America",
    logo: "https://media.api-sports.io/football/leagues/16.png",
  },
};
