"""
Simple fixture population - NO team stats
Only loads finished fixtures from all 24 leagues
"""

import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.apifootball import APIFootballClient
from app.services.database import db_service

logger = structlog.get_logger()

# All 24 leagues
LEAGUES = {
    # Europe - Top 5
    39: "Premier League",
    140: "La Liga",
    78: "Bundesliga",
    135: "Serie A",
    61: "Ligue 1",
    # Europe - Secondary
    94: "Primeira Liga",
    88: "Eredivisie",
    203: "Super Lig",
    144: "Belgian Pro League",
    # Latin America
    262: "Liga MX",
    128: "Liga Profesional",
    71: "Brasileirão Serie A",
    281: "Primera División",
    239: "Primera A",
    # South America - International
    13: "Copa Libertadores",
    11: "CONMEBOL Sudamericana",
    # North America
    253: "MLS",
    # Asia & Oceania
    188: "A-League",
    235: "Saudi Pro League",
    # Europe - Champions/Europa
    2: "Champions League",
    3: "Europa League",
    848: "Conference League",
}

api = APIFootballClient()

print("\n" + "=" * 70)
print("FIXTURE POPULATION - 24 LEAGUES (2025 SEASON ONLY)")
print("=" * 70)
print(f"\nTotal leagues: {len(LEAGUES)}")
print("This will take 10-15 minutes due to API rate limits...")
print("\n")

total_fixtures = 0

for i, (league_id, league_name) in enumerate(LEAGUES.items(), 1):
    print(f"[{i}/{len(LEAGUES)}] {league_name:<30}", end="", flush=True)

    try:
        # Fetch finished fixtures only
        fixtures = api.get_fixtures(league_id=league_id, season=2025, status="FT")

        if not fixtures:
            print("❌ No fixtures")
            continue

        # Convert to DB format
        db_fixtures = []
        for fixture in fixtures:
            fixture_data = fixture.get("fixture", {})
            teams = fixture.get("teams", {})
            goals = fixture.get("goals", {})
            league_info = fixture.get("league", {})
            score = fixture.get("score", {})

            # Get statistics
            statistics = fixture.get("statistics", [])
            home_stats = {}
            away_stats = {}

            if statistics:
                for stat in statistics:
                    team_name = stat.get("team", {}).get("name", "")
                    stats_data = {s.get("type"): s.get("value") for s in stat.get("statistics", [])}

                    if team_name == teams.get("home", {}).get("name"):
                        home_stats = stats_data
                    elif team_name == teams.get("away", {}).get("name"):
                        away_stats = stats_data

            db_fixture = {
                "id": fixture_data.get("id"),
                "kickoff_time": fixture_data.get("date"),
                "home_team_id": teams.get("home", {}).get("id"),
                "home_team_name": teams.get("home", {}).get("name"),
                "away_team_id": teams.get("away", {}).get("id"),
                "away_team_name": teams.get("away", {}).get("name"),
                "league_id": league_info.get("id"),
                "season": league_info.get("season"),
                "round": league_info.get("round"),
                "status": fixture_data.get("status", {}).get("short"),
                "venue": fixture_data.get("venue", {}).get("name"),
                "referee": fixture_data.get("referee"),
                "home_score": goals.get("home"),
                "away_score": goals.get("away"),
                # Half-time scores
                "half_time_home_score": score.get("halftime", {}).get("home"),
                "half_time_away_score": score.get("halftime", {}).get("away"),
                # Statistics
                "corners_home": home_stats.get("Corner Kicks"),
                "corners_away": away_stats.get("Corner Kicks"),
                "cards_home": (home_stats.get("Yellow Cards") or 0)
                + (home_stats.get("Red Cards") or 0),
                "cards_away": (away_stats.get("Yellow Cards") or 0)
                + (away_stats.get("Red Cards") or 0),
                "shots_on_target_home": home_stats.get("Shots on Goal"),
                "shots_on_target_away": away_stats.get("Shots on Goal"),
                "offsides_home": home_stats.get("Offsides"),
                "offsides_away": away_stats.get("Offsides"),
            }
            db_fixtures.append(db_fixture)

        # Upsert to DB
        count = db_service.upsert_fixtures(db_fixtures)
        total_fixtures += count

        print(f"✅ {count} fixtures")

    except Exception as e:
        print(f"❌ Error: {e}")

print("\n" + "=" * 70)
print(f"✅ COMPLETE - {total_fixtures} fixtures loaded from {len(LEAGUES)} leagues")
print("=" * 70)
print("\nNext steps:")
print("1. Verify fixtures: Check Supabase dashboard")
print("2. Run backtest: python -m app.ml.run_backtest")
print()
