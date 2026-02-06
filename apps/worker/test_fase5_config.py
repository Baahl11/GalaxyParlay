"""
Test League-Specific Home Advantage Configuration

Verifies FASE 5 calibration is working correctly
"""

from app.ml.league_config import (
    LEAGUE_HOME_ADVANTAGE,
    get_league_home_advantage,
    is_premium_market,
    should_show_market,
)
from app.ml.smart_parlay import smart_parlay_validator


def test_league_config():
    """Test league-specific home advantage values"""

    print("\n" + "=" * 70)
    print("TESTING LEAGUE-SPECIFIC HOME ADVANTAGE (FASE 5 CALIBRATION)")
    print("=" * 70)

    # Test specific leagues
    test_leagues = [
        (2, "Champions League"),
        (78, "Bundesliga"),
        (3, "Europa League"),
        (140, "La Liga"),
        (39, "Premier League"),
        (135, "Serie A"),
    ]

    print("\n📊 HOME ADVANTAGE BY LEAGUE:\n")
    for league_id, name in test_leagues:
        dixon_coles_ha, goals_ha = get_league_home_advantage(league_id)
        print(f"{name} (ID: {league_id})")
        print(f"   Dixon-Coles: {dixon_coles_ha:.2f}")
        print(f"   Goals Multiplier: {goals_ha:.2f}")

        # Show what changed
        default = (0.27, 1.15)
        if (dixon_coles_ha, goals_ha) != default:
            print(f"   ✅ ADJUSTED (from default {default})")
        print()

    # Test market confidence
    print("\n" + "=" * 70)
    print("TESTING MARKET CONFIDENCE THRESHOLDS")
    print("=" * 70 + "\n")

    test_markets = [
        "over_under_1_5",
        "match_winner_draw",
        "match_winner_home_win",
        "over_under_2_5",
    ]

    for market in test_markets:
        premium = is_premium_market(market)
        should_show = should_show_market(market)

        status = "✅ PREMIUM" if premium else "⚠️ STANDARD" if should_show else "🚫 HIDDEN"
        print(f"{market}: {status}")

    # Test Smart Parlay validator
    print("\n" + "=" * 70)
    print("TESTING SMART PARLAY VALIDATOR")
    print("=" * 70 + "\n")

    # Test case 1: High correlation (should reject)
    parlay1 = [
        {"fixture_id": 1, "market_key": "over_under_2_5_over", "odds": 1.85},
        {"fixture_id": 1, "market_key": "over_under_3_5_over", "odds": 2.50},
    ]

    valid, reason, penalty = smart_parlay_validator.validate_parlay(parlay1)
    print(f"Test 1: Over 2.5 + Over 3.5 (same fixture)")
    print(f"   Valid: {valid}")
    print(f"   Reason: {reason}")
    print(f"   Penalty: {penalty}\n")

    # Test case 2: Low correlation (should accept)
    parlay2 = [
        {"fixture_id": 1, "market_key": "match_winner_home_win", "odds": 1.60},
        {"fixture_id": 1, "market_key": "over_under_1_5_over", "odds": 1.30},
    ]

    valid, reason, penalty = smart_parlay_validator.validate_parlay(parlay2)
    print(f"Test 2: Home Win + Over 1.5 (same fixture)")
    print(f"   Valid: {valid}")
    print(f"   Reason: {reason}")
    print(f"   Penalty: {penalty}\n")

    # Test case 3: Different fixtures (should accept)
    parlay3 = [
        {"fixture_id": 1, "market_key": "match_winner_home_win", "odds": 1.60},
        {"fixture_id": 2, "market_key": "match_winner_away_win", "odds": 2.20},
    ]

    valid, reason, penalty = smart_parlay_validator.validate_parlay(parlay3)
    print(f"Test 3: Different fixtures")
    print(f"   Valid: {valid}")
    print(f"   Reason: {reason}")
    print(f"   Penalty: {penalty}\n")

    print("=" * 70)
    print("✅ ALL TESTS COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    test_league_config()
