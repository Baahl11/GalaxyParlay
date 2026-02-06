"""
Test FIFA Player Ratings Scraper

Run this to test the FIFA scraper without needing API-Football data.
"""

import structlog

from app.services.fifa_scraper import TeamRatings, fifa_scraper

structlog.configure(
    wrapper_class=structlog.BoundLogger,
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer(),
    ],
)


def test_single_team():
    """Test getting ratings for a single team"""
    print("\n" + "=" * 70)
    print("TEST 1: Single Team Ratings")
    print("=" * 70)

    teams = ["Arsenal", "Liverpool", "Manchester City", "Real Madrid", "Barcelona"]

    for team in teams:
        print(f"\n{team}:")
        ratings = fifa_scraper.get_team_ratings(team)

        if ratings:
            print(f"  Overall Rating: {ratings.avg_overall:.1f}")
            print(f"  Attack Rating: {ratings.avg_attack:.1f}")
            print(f"  Defense Rating: {ratings.avg_defense:.1f}")
            print(f"  Pace: {ratings.avg_pace:.1f}")
            print(f"  Physical: {ratings.avg_physical:.1f}")
            print(f"  Top Player: {ratings.top_player_rating}")
            print(f"  Players Analyzed: {ratings.players_count}")
        else:
            print(f"  ❌ Could not fetch ratings")


def test_match_advantages():
    """Test calculating match advantages"""
    print("\n" + "=" * 70)
    print("TEST 2: Match Advantages")
    print("=" * 70)

    matches = [
        ("Arsenal", "Liverpool"),
        ("Manchester City", "Chelsea"),
        ("Real Madrid", "Barcelona"),
        ("Bayern Munich", "Borussia Dortmund"),
    ]

    for home, away in matches:
        print(f"\n{home} vs {away}:")
        advantages = fifa_scraper.calculate_match_advantages(home, away)

        if advantages:
            print(f"  Quality Advantage: {advantages['quality_advantage']:+.1f}")
            print(f"  Pace Advantage: {advantages['pace_advantage']:+.1f}")
            print(f"  Attack Advantage: {advantages['attack_advantage']:+.1f}")
            print(f"  Defense Advantage: {advantages['defense_advantage']:+.1f}")
            print(f"  Physical Advantage: {advantages['physical_advantage']:+.1f}")

            # Predict likely outcome
            if advantages["quality_advantage"] > 3:
                print(
                    f"  → Prediction: {home} favored (quality +{advantages['quality_advantage']:.1f})"
                )
            elif advantages["quality_advantage"] < -3:
                print(
                    f"  → Prediction: {away} favored (quality {advantages['quality_advantage']:.1f})"
                )
            else:
                print(f"  → Prediction: Balanced match")

            # Predict goals
            if advantages["attack_advantage"] > 5:
                print(f"  → Goals: Over 2.5 likely ({home} strong attack)")
            elif advantages["attack_advantage"] < -5:
                print(f"  → Goals: Over 2.5 likely ({away} strong attack)")

            # Predict pace
            avg_pace = (advantages["home_overall"] + advantages["away_overall"]) / 2
            if avg_pace > 84:
                print(f"  → Pace: Fast game expected (avg pace {avg_pace:.1f})")
                print(f"  → Corners: Over 10.5 likely")
            elif avg_pace < 78:
                print(f"  → Pace: Slow game expected (avg pace {avg_pace:.1f})")
                print(f"  → Corners: Under 9.5 likely")
        else:
            print(f"  ❌ Could not calculate advantages")


def test_cache_performance():
    """Test that caching works"""
    print("\n" + "=" * 70)
    print("TEST 3: Cache Performance")
    print("=" * 70)

    import time

    team = "Arsenal"

    # First call (should scrape)
    print(f"\nFirst call for {team} (scraping)...")
    start = time.time()
    ratings1 = fifa_scraper.get_team_ratings(team)
    time1 = time.time() - start
    print(f"  Time: {time1:.3f}s")

    # Second call (should use cache)
    print(f"\nSecond call for {team} (cached)...")
    start = time.time()
    ratings2 = fifa_scraper.get_team_ratings(team)
    time2 = time.time() - start
    print(f"  Time: {time2:.3f}s")

    if time2 < time1 / 10:
        print(f"  ✅ Cache working! {time1/time2:.0f}x faster")
    else:
        print(f"  ⚠️ Cache might not be working properly")

    # Verify same data
    if ratings1 and ratings2:
        if ratings1.avg_overall == ratings2.avg_overall:
            print(f"  ✅ Data consistency verified")
        else:
            print(f"  ❌ Data mismatch!")


def test_use_cases():
    """Test real-world use cases"""
    print("\n" + "=" * 70)
    print("TEST 4: Real-World Use Cases")
    print("=" * 70)

    # Use Case 1: Predict high-scoring game
    print("\n📊 Use Case 1: Predicting High-Scoring Games")
    print("-" * 70)

    home = "Manchester City"
    away = "Arsenal"

    home_ratings = fifa_scraper.get_team_ratings(home)
    away_ratings = fifa_scraper.get_team_ratings(away)

    if home_ratings and away_ratings:
        combined_attack = (home_ratings.avg_attack + away_ratings.avg_attack) / 2
        combined_defense = (home_ratings.avg_defense + away_ratings.avg_defense) / 2

        print(f"\n{home} vs {away}")
        print(f"  Combined Attack: {combined_attack:.1f}")
        print(f"  Combined Defense: {combined_defense:.1f}")

        if combined_attack > 85 and combined_defense > 82:
            print(f"  ✅ Both teams elite → Over 2.5 goals likely")
            print(f"  ✅ High tempo expected → Over 10.5 corners likely")
        elif combined_attack < 75:
            print(f"  ⚠️ Low attack quality → Under 2.5 goals possible")

    # Use Case 2: Identify pace-based predictions
    print("\n⚡ Use Case 2: Pace-Based Predictions")
    print("-" * 70)

    fast_teams = ["Liverpool", "Real Madrid"]
    slow_teams = ["Atletico Madrid", "Juventus"]

    print("\nFast Teams (Expected: More corners, cards, shots):")
    for team in fast_teams:
        ratings = fifa_scraper.get_team_ratings(team)
        if ratings:
            print(f"  {team}: Pace {ratings.avg_pace:.1f}")

    print("\nSlow Teams (Expected: Fewer corners, tactical play):")
    for team in slow_teams:
        ratings = fifa_scraper.get_team_ratings(team)
        if ratings:
            print(f"  {team}: Pace {ratings.avg_pace:.1f}")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("FIFA PLAYER RATINGS SCRAPER - TEST SUITE")
    print("=" * 70)
    print("\nThis will test the FIFA scraper without consuming API-Football quota.")
    print("Tests use cached data after first run (24h TTL).")

    try:
        test_single_team()
        test_match_advantages()
        test_cache_performance()
        test_use_cases()

        print("\n" + "=" * 70)
        print("✅ ALL TESTS COMPLETE")
        print("=" * 70)
        print("\nNext Steps:")
        print("1. Integrate FIFA ratings into dixon_coles.py")
        print("2. Add FIFA features to multi_market_predictor.py")
        print("3. Run backtest to measure accuracy improvement")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback

        traceback.print_exc()
