"""
Database Population Script

Fetches and stores:
1. Historical fixtures (2023-2025) for Elo training
2. Current season fixtures (2026) for predictions
3. Team statistics for all teams

Usage:
    python populate_database.py
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import structlog

from app.config import settings
from app.services.apifootball import APIFootballClient
from app.services.database import db_service

logger = structlog.get_logger()

# Top leagues to populate
LEAGUES = {
    # Europe - Top 5
    39: "Premier League",  # England
    140: "La Liga",  # Spain
    78: "Bundesliga",  # Germany
    135: "Serie A",  # Italy
    61: "Ligue 1",  # France
    # Europe - Secondary
    94: "Primeira Liga",  # Portugal
    88: "Eredivisie",  # Netherlands
    203: "Super Lig",  # Turkey
    144: "Belgian Pro League",  # Belgium
    # Latin America
    262: "Liga MX",  # Mexico - Apertura/Clausura
    128: "Liga Profesional",  # Argentina
    71: "Brasileirão Serie A",  # Brazil
    281: "Primera División",  # Peru
    239: "Primera A",  # Colombia
    # South America - International
    13: "Copa Libertadores",  # CONMEBOL
    11: "CONMEBOL Sudamericana",  # CONMEBOL
    # North America
    253: "MLS",  # USA/Canada
    # Asia & Oceania
    188: "A-League",  # Australia
    235: "Saudi Pro League",  # Saudi Arabia
    # Europe - Champions/Europa
    2: "Champions League",
    3: "Europa League",
    848: "Conference League",
}

# Seasons to fetch
HISTORICAL_SEASONS = [2025]  # Only 2025 season for initial population (faster)
# HISTORICAL_SEASONS = [2022, 2023, 2024, 2025]  # Uncomment for full historical
CURRENT_SEASON = 2025  # Current season (2024-2025)


class DatabasePopulator:
    """Populates database with fixtures and team stats"""

    def __init__(self):
        self.api = APIFootballClient()
        self.total_fixtures = 0
        self.total_teams = 0

    def fetch_and_store_fixtures(self, league_id: int, season: int, status: str = "FT") -> int:
        """
        Fetch finished fixtures for a league/season and store in DB

        Returns:
            Number of fixtures stored
        """
        logger.info(
            "Fetching fixtures",
            league=LEAGUES.get(league_id, league_id),
            season=season,
            status=status,
        )

        try:
            # Get fixtures from API
            fixtures = self.api.get_fixtures(league_id=league_id, season=season, status=status)

            if not fixtures:
                logger.warning("No fixtures found", league_id=league_id, season=season)
                return 0

            # Transform to database format
            db_fixtures = []
            for fixture in fixtures:
                fixture_data = fixture.get("fixture", {})
                teams = fixture.get("teams", {})
                goals = fixture.get("goals", {})
                league_info = fixture.get("league", {})

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
                }

                db_fixtures.append(db_fixture)

            # Store in database (batch upsert)
            count = db_service.upsert_fixtures(db_fixtures)

            logger.info(
                "Fixtures stored",
                league=LEAGUES.get(league_id, league_id),
                season=season,
                count=count,
            )

            return count

        except Exception as e:
            logger.error(
                "Error fetching/storing fixtures", league_id=league_id, season=season, error=str(e)
            )
            return 0

    def fetch_and_store_team_stats(self, league_id: int, season: int) -> int:
        """
        Fetch team statistics and store in DB

        Returns:
            Number of team stats stored
        """
        logger.info("Fetching team stats", league=LEAGUES.get(league_id, league_id), season=season)

        try:
            # Get teams from API
            fixtures = self.api.get_fixtures(league_id=league_id, season=season, status="FT")

            if not fixtures:
                return 0

            # Extract unique teams
            team_ids = set()
            for fixture in fixtures:
                teams = fixture.get("teams", {})
                home_id = teams.get("home", {}).get("id")
                away_id = teams.get("away", {}).get("id")
                if home_id:
                    team_ids.add(home_id)
                if away_id:
                    team_ids.add(away_id)

            # Fetch stats for each team
            stats_stored = 0
            for team_id in team_ids:
                try:
                    stats = self.api.get_team_statistics(
                        team_id=team_id, league_id=league_id, season=season
                    )

                    if stats:
                        # Store in database (column name is stats_data, not statistics)
                        db_service.upsert_team_statistics(
                            [
                                {
                                    "team_id": team_id,
                                    "league_id": league_id,
                                    "season": season,
                                    "stats_data": stats,  # Fixed: column name is stats_data
                                }
                            ]
                        )
                        stats_stored += 1

                except Exception as e:
                    logger.warning("Error fetching team stats", team_id=team_id, error=str(e))
                    continue

            logger.info(
                "Team stats stored",
                league=LEAGUES.get(league_id, league_id),
                season=season,
                count=stats_stored,
            )

            return stats_stored

        except Exception as e:
            logger.error(
                "Error fetching team stats", league_id=league_id, season=season, error=str(e)
            )
            return 0

    def populate_historical_data(self):
        """Populate database with historical fixtures (2023-2025)"""
        logger.info("Starting historical data population")

        total_fixtures = 0
        total_stats = 0

        for league_id, league_name in LEAGUES.items():
            for season in HISTORICAL_SEASONS:
                # Fetch finished fixtures
                count = self.fetch_and_store_fixtures(
                    league_id=league_id, season=season, status="FT"
                )
                total_fixtures += count

                # Fetch team stats
                if count > 0:
                    stats_count = self.fetch_and_store_team_stats(
                        league_id=league_id, season=season
                    )
                    total_stats += stats_count

        logger.info(
            "Historical data population complete",
            total_fixtures=total_fixtures,
            total_team_stats=total_stats,
        )

        return total_fixtures, total_stats

    def populate_current_season(self):
        """Populate database with 2026 fixtures (all statuses)"""
        logger.info("Starting 2026 season data population")

        total_fixtures = 0

        for league_id, league_name in LEAGUES.items():
            # Fetch ALL fixtures (FT, NS, LIVE, etc.)
            for status in ["FT", "NS", "LIVE", "PST"]:
                count = self.fetch_and_store_fixtures(
                    league_id=league_id, season=CURRENT_SEASON, status=status
                )
                total_fixtures += count

            # Fetch team stats for current season
            stats_count = self.fetch_and_store_team_stats(
                league_id=league_id, season=CURRENT_SEASON
            )

        logger.info("2026 season data population complete", total_fixtures=total_fixtures)

        return total_fixtures

    def populate_january_2026_detailed(self):
        """
        Populate December 2025 - January 2026 fixtures (current season)
        For backtesting purposes
        """
        logger.info("Fetching Dec 2025 - Jan 2026 fixtures for backtest")

        total = 0

        # Fetch fixtures from December 15, 2025 - January 29, 2026
        for league_id, league_name in LEAGUES.items():
            try:
                # Use date range for more specific fetching
                fixtures = self.api.get_fixtures(
                    league_id=league_id,
                    season=2025,
                    date_from="2025-12-15",
                    date_to="2026-01-29",
                    status="FT",
                )

                if fixtures:
                    # Transform and store
                    db_fixtures = []
                    for fixture in fixtures:
                        fixture_data = fixture.get("fixture", {})
                        teams = fixture.get("teams", {})
                        goals = fixture.get("goals", {})
                        league_info = fixture.get("league", {})

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
                        }

                        db_fixtures.append(db_fixture)

                    count = db_service.upsert_fixtures(db_fixtures)
                    total += count

                    logger.info("December-January fixtures stored", league=league_name, count=count)

            except Exception as e:
                logger.error("Error fetching Dec-Jan fixtures", league_id=league_id, error=str(e))
                continue

        logger.info("Dec 2025 - Jan 2026 population complete", total=total)
        return total


def main():
    """Main execution"""
    populator = DatabasePopulator()

    print("\n" + "=" * 60)
    print("GALAXY PARLAY - DATABASE POPULATION")
    print("=" * 60)

    # Step 1: Populate historical data (2023-2025)
    print("\n[1/3] Fetching historical fixtures (2023-2025)...")
    print("This will take 5-10 minutes...")
    historical_fixtures, historical_stats = populator.populate_historical_data()
    print(f"[OK] Stored {historical_fixtures} historical fixtures")
    print(f"[OK] Stored {historical_stats} team statistics")

    # Step 2: Populate 2026 season
    print("\n[2/3] Fetching 2026 season fixtures...")
    current_fixtures = populator.populate_current_season()
    print(f"[OK] Stored {current_fixtures} fixtures from 2026")

    # Step 3: Populate January 2026 specifically for backtest
    print("\n[3/3] Fetching January 15-29, 2026 (backtest period)...")
    january_fixtures = populator.populate_january_2026_detailed()
    print(f"[OK] Stored {january_fixtures} fixtures from Jan 15-29, 2026")

    # Summary
    print("\n" + "=" * 60)
    print("POPULATION COMPLETE")
    print("=" * 60)
    print(f"Total historical fixtures: {historical_fixtures}")
    print(f"Total 2026 fixtures: {current_fixtures}")
    print(f"Total January 2026 fixtures: {january_fixtures}")
    print(f"Total team statistics: {historical_stats}")
    print("\nDatabase is ready for:")
    print("  - Elo training")
    print("  - Predictions")
    print("  - Backtesting")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
