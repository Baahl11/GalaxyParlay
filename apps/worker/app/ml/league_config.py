"""
League-specific configuration for prediction parameters

Based on FASE 5 backtest analysis (1,000 fixtures, 10 leagues)
"""

# Home advantage multipliers by league
# Format: league_id: (home_advantage_dixon_coles, home_advantage_goals)
LEAGUE_HOME_ADVANTAGE = {
    # Europe - Top 5 (performing well, keep base values)
    39: (0.27, 1.15),  # Premier League - 71.89% accuracy
    140: (0.27, 1.15),  # La Liga - 74.81% accuracy ✅ Best
    78: (0.35, 1.20),  # Bundesliga - 68.50% ⚠️ Needs boost
    135: (0.27, 1.15),  # Serie A - 73.90% accuracy ✅
    61: (0.27, 1.15),  # Ligue 1 - 71.94% accuracy
    # Europe - Secondary (good performance)
    94: (0.27, 1.15),  # Primeira Liga - 73.37% accuracy ✅
    88: (0.27, 1.15),  # Eredivisie - 73.45% accuracy ✅
    203: (0.30, 1.17),  # Super Lig - 70.13% (slight boost)
    144: (0.27, 1.15),  # Belgian Pro League
    # Latin America (use higher home advantage - traditionally strong)
    262: (0.32, 1.18),  # Liga MX - home advantage culture
    128: (0.32, 1.18),  # Liga Profesional (Argentina)
    71: (0.32, 1.18),  # Brasileirão Serie A
    281: (0.32, 1.18),  # Primera División (Peru)
    239: (0.32, 1.18),  # Primera A (Colombia)
    # International Competitions (lower home advantage, higher upsets)
    13: (0.25, 1.12),  # Copa Libertadores - international
    11: (0.25, 1.12),  # CONMEBOL Sudamericana
    2: (0.35, 1.20),  # Champions League - 63.89% ⚠️ CRITICAL - Needs boost
    3: (0.35, 1.18),  # Europa League - 68.75% ⚠️ Needs boost
    848: (0.32, 1.17),  # Conference League
    # North America + Others
    253: (0.28, 1.16),  # MLS
    188: (0.28, 1.16),  # A-League
    235: (0.30, 1.17),  # Saudi Pro League
}

# Default values for leagues not in the map
DEFAULT_HOME_ADVANTAGE = (0.27, 1.15)

# Smart Parlay correlation thresholds (from FASE 5 analysis)
SMART_PARLAY_CONFIG = {
    # Correlation thresholds
    "high_correlation_threshold": 0.70,  # Reject if > 0.70
    "moderate_correlation_threshold": 0.30,  # Warn if 0.30-0.70
    "low_correlation_threshold": 0.30,  # Good if < 0.30
    # Penalties for moderate correlations
    "moderate_correlation_penalty": 0.95,  # Multiply odds by 0.95
    # Maximum parlays per user per day (rate limiting)
    "max_parlays_per_day": 50,
}

# Known high correlations (from backtest analysis)
# These pairs should NEVER be combined in parlays
HIGH_CORRELATION_PAIRS = {
    # Over/Under markets with similar thresholds
    ("over_under_2_5_over", "over_under_3_5_over"): 0.681,
    ("over_under_2_5_over", "over_under_1_5_over"): 0.580,
    ("over_under_2_5_under", "over_under_3_5_under"): 0.681,
    ("over_under_2_5_under", "over_under_1_5_under"): 0.580,
    # Inverse markets (perfectly correlated)
    ("over_under_2_5_over", "over_under_2_5_under"): -1.0,
    ("over_under_1_5_over", "over_under_1_5_under"): -1.0,
    ("over_under_3_5_over", "over_under_3_5_under"): -1.0,
    # Match winner mutually exclusive
    ("match_winner_home_win", "match_winner_draw"): -0.516,
    ("match_winner_home_win", "match_winner_away_win"): -0.563,
    ("match_winner_draw", "match_winner_away_win"): -0.418,
}

# Recommended parlay combinations (low correlation)
RECOMMENDED_PARLAY_COMBINATIONS = [
    ("match_winner", "over_under_1_5"),  # Correlation: -0.021 to 0.063
    ("match_winner", "over_under_3_5"),  # Correlation: 0.042 to 0.055
    ("match_winner_home_win", "over_1_5"),  # Almost independent
    ("match_winner_away_win", "over_3_5"),  # Very low correlation
]

# Market accuracy thresholds (from FASE 5 results)
MARKET_ACCURACY = {
    "over_under_1_5": 0.799,  # 79.9% - Premium market ✅
    "match_winner_draw": 0.723,  # 72.3% - Good
    "over_under_3_5": 0.714,  # 71.4% - Acceptable
    "over_under_2_5": 0.714,  # 71.4% - Acceptable
    "match_winner_away_win": 0.700,  # 70.0% - Acceptable
    "match_winner_home_win": 0.617,  # 61.7% - ⚠️ Below target
}

# Minimum confidence thresholds for display
MIN_CONFIDENCE_DISPLAY = 0.60  # Don't show predictions < 60% accuracy market
PREMIUM_CONFIDENCE = 0.75  # Markets >= 75% accuracy get "Premium" badge


def get_league_home_advantage(league_id: int) -> tuple[float, float]:
    """
    Get home advantage parameters for a specific league

    Args:
        league_id: League ID from API-Football

    Returns:
        Tuple of (dixon_coles_home_advantage, goals_home_advantage)
    """
    return LEAGUE_HOME_ADVANTAGE.get(league_id, DEFAULT_HOME_ADVANTAGE)


def is_premium_market(market_key: str) -> bool:
    """Check if a market has premium accuracy (>= 75%)"""
    accuracy = MARKET_ACCURACY.get(market_key, 0.0)
    return accuracy >= PREMIUM_CONFIDENCE


def should_show_market(market_key: str) -> bool:
    """Check if a market meets minimum confidence threshold"""
    accuracy = MARKET_ACCURACY.get(market_key, 0.70)
    return accuracy >= MIN_CONFIDENCE_DISPLAY
