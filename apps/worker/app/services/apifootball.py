"""
API-Football Service
Handles all interactions with API-Football API
WITH IN-MEMORY CACHING to reduce API calls and costs
"""

import hashlib
import json
from datetime import datetime, timedelta
from functools import lru_cache
from typing import Any, Dict, List, Optional

import httpx
import structlog

from app.config import settings

logger = structlog.get_logger()


# In-memory cache for API responses (session-level)
_API_CACHE: Dict[str, Any] = {}


class APIFootballClient:
    """Client for API-Football API v3 - Synchronous version with caching"""

    def __init__(self):
        self.base_url = settings.APIFOOTBALL_BASE_URL
        self.api_key = settings.APIFOOTBALL_API_KEY
        self.headers = {
            "x-rapidapi-key": self.api_key,
            "x-rapidapi-host": "v3.football.api-sports.io",
        }
        self._client = httpx.Client(timeout=30.0)

    def _get_cache_key(self, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key from endpoint and params"""
        # Sort params for consistent keys
        sorted_params = json.dumps(params, sort_keys=True)
        key_string = f"{endpoint}:{sorted_params}"
        return hashlib.md5(key_string.encode()).hexdigest()

    def _request(
        self, endpoint: str, params: Dict[str, Any], cache_ttl: int = 3600
    ) -> Dict[str, Any]:
        """
        Make authenticated request to API-Football with caching

        Args:
            endpoint: API endpoint
            params: Query parameters
            cache_ttl: Cache time-to-live in seconds (default 1 hour, 0 = no cache)
        """
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)

        if cache_ttl > 0 and cache_key in _API_CACHE:
            cached_data, cached_time = _API_CACHE[cache_key]
            age = (datetime.now() - cached_time).total_seconds()

            if age < cache_ttl:
                logger.info(
                    "apifootball_cache_hit",
                    endpoint=endpoint,
                    params=params,
                    cache_age_seconds=int(age),
                )
                return cached_data

        # Cache miss - make API call
        url = f"{self.base_url}/{endpoint}"

        try:
            response = self._client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            logger.info(
                "apifootball_request",
                endpoint=endpoint,
                params=params,
                results=data.get("results", 0),
                cached=False,
            )

            # Store in cache
            if cache_ttl > 0:
                _API_CACHE[cache_key] = (data, datetime.now())

            return data
        except httpx.HTTPError as e:
            logger.error("apifootball_error", endpoint=endpoint, error=str(e))
            raise

    def get_fixtures(
        self,
        league_id: int,
        season: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        status: str = "NS",  # Not Started
    ) -> List[Dict[str, Any]]:
        """
        Get fixtures for a league

        Args:
            league_id: League ID (e.g., 39 for Premier League)
            season: Season year (e.g., 2025)
            date_from: Start date (YYYY-MM-DD)
            date_to: End date (YYYY-MM-DD)
            status: Match status (NS, LIVE, FT, etc.)
        """
        params = {"league": league_id, "season": season, "status": status}

        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to

        # Cache based on status: FT=24h (finished), NS=5min (upcoming), LIVE=no cache
        cache_ttl = 86400 if status == "FT" else (300 if status == "NS" else 0)
        data = self._request("fixtures", params, cache_ttl=cache_ttl)
        return data.get("response", [])

    def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        """Get single fixture by ID (cached 1 hour)"""
        params = {"id": fixture_id}
        data = self._request("fixtures", params, cache_ttl=3600)
        results = data.get("response", [])
        return results[0] if results else None

    def get_odds(self, fixture_id: int, bookmaker_id: int = 8) -> List[Dict[str, Any]]:  # Bet365
        """
        Get odds for a fixture

        Args:
            fixture_id: Fixture ID
            bookmaker_id: Bookmaker ID (8 = Bet365, 11 = Pinnacle)
        """
        params = {"fixture": fixture_id, "bookmaker": bookmaker_id}

        # Odds change frequently, cache only 5 minutes
        data = self._request("odds", params, cache_ttl=300)
        return data.get("response", [])

    def get_team_statistics(
        self, team_id: int, league_id: int, season: int
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics for a season"""
        params = {"team": team_id, "league": league_id, "season": season}

        # Team stats don't change during season, cache 24 hours
        data = self._request("teams/statistics", params, cache_ttl=86400)
        return data.get("response")

    def get_h2h(self, team1_id: int, team2_id: int, last: int = 10) -> List[Dict[str, Any]]:
        """Get head-to-head matches between two teams"""
        params = {"h2h": f"{team1_id}-{team2_id}", "last": last}

        # H2H history doesn't change often, cache 24 hours
        data = self._request("fixtures/headtohead", params, cache_ttl=86400)
        return data.get("response", [])

    def get_finished_fixtures(
        self, league_id: int, season: int, last: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get finished fixtures for a league to build historical Elo ratings

        Args:
            league_id: League ID (e.g., 39 for Premier League)
            season: Season year (e.g., 2024, 2025)
            last: Number of most recent finished matches to retrieve
        """
        params = {
            "league": league_id,
            "season": season,
            "status": "FT",  # Finished matches only
            "last": last,
        }

        # Finished fixtures never change, cache 24 hours
        data = self._request("fixtures", params, cache_ttl=86400)
        return data.get("response", [])

    def get_all_season_results(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Get ALL finished fixtures for a full season (for comprehensive Elo calculation)

        Args:
            league_id: League ID
            season: Season year

        Returns:
            All finished matches sorted by date (oldest first for Elo calculation)
        """
        params = {"league": league_id, "season": season, "status": "FT"}

        data = self._request("fixtures", params)
        results = data.get("response", [])

        # Sort by date ascending (oldest first) for proper Elo calculation
        results.sort(key=lambda x: x.get("fixture", {}).get("date", ""))

        return results

    def get_players_statistics(self, team_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Get all player statistics for a team in a season

        Returns shots, goals, assists, cards, minutes per player
        """
        params = {"team": team_id, "season": season}

        data = self._request("players", params)
        return data.get("response", [])

    def get_fixture_statistics(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed match statistics (shots, corners, cards, xG, etc.)
        for a specific fixture

        CACHED PERMANENTLY: Finished match stats never change
        """
        params = {"fixture": fixture_id}

        # Fixture statistics (especially xG) never change after match ends
        # Cache permanently (7 days = 604800 seconds)
        data = self._request("fixtures/statistics", params, cache_ttl=604800)
        return data.get("response", [])

    def get_fixture_xg(self, fixture_id: int) -> Dict[str, Optional[float]]:
        """
        NEW: Extract Expected Goals (xG) from fixture statistics

        Returns:
            Dict with 'home_xg' and 'away_xg', or None if not available

        xG is available for:
        - Premier League, La Liga, Serie A, Bundesliga, Ligue 1
        - Champions League, Europa League
        - After match completion or sometimes pre-match from bookmakers
        """
        stats = self.get_fixture_statistics(fixture_id)

        result = {"home_xg": None, "away_xg": None}

        if not stats or len(stats) < 2:
            return result

        # Stats array has [0] = home team, [1] = away team
        home_stats = stats[0].get("statistics", [])
        away_stats = stats[1].get("statistics", [])

        # Find xG in statistics (usually labeled as "Expected Goals")
        for stat in home_stats:
            if stat.get("type") == "expected_goals":
                value = stat.get("value")
                if value is not None:
                    try:
                        result["home_xg"] = float(value)
                    except (ValueError, TypeError):
                        pass

        for stat in away_stats:
            if stat.get("type") == "expected_goals":
                value = stat.get("value")
                if value is not None:
                    try:
                        result["away_xg"] = float(value)
                    except (ValueError, TypeError):
                        pass

        logger.info(
            "xg_extracted",
            fixture_id=fixture_id,
            home_xg=result["home_xg"],
            away_xg=result["away_xg"],
        )

        return result

    def get_fixture_events(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Get match events (goals, cards, substitutions)
        """
        params = {"fixture": fixture_id}

        data = self._request("fixtures/events", params)
        return data.get("response", [])

    def get_top_scorers(self, league_id: int, season: int) -> List[Dict[str, Any]]:
        """Get top scorers for a league"""
        params = {"league": league_id, "season": season}

        data = self._request("players/topscorers", params)
        return data.get("response", [])

    def get_fixture_lineups(self, fixture_id: int) -> List[Dict[str, Any]]:
        """Get lineups for a fixture (when available)"""
        params = {"fixture": fixture_id}

        data = self._request("fixtures/lineups", params)
        return data.get("response", [])

    def get_team_players(self, team_id: int, season: int) -> List[Dict[str, Any]]:
        """
        Get all players with statistics for a team.

        Returns player data including:
        - goals, assists
        - shots total, shots on target
        - cards (yellow, red)
        - minutes played
        """
        params = {"team": team_id, "season": season}

        data = self._request("players", params)

        # API returns paginated data, get all players
        players = []
        response = data.get("response", [])

        for player_data in response:
            player = player_data.get("player", {})
            stats = player_data.get("statistics", [])

            players.append(
                {
                    "id": player.get("id"),
                    "name": player.get("name"),
                    "firstname": player.get("firstname"),
                    "lastname": player.get("lastname"),
                    "age": player.get("age"),
                    "nationality": player.get("nationality"),
                    "position": player.get("position"),
                    "photo": player.get("photo"),
                    "statistics": stats,
                }
            )

        return players

    def get_fixture_statistics(self, fixture_id: int) -> List[Dict[str, Any]]:
        """
        Get detailed statistics for a finished fixture.

        Returns stats like:
        - Shots (total, on target, off target)
        - Corners
        - Fouls, cards
        - Possession
        """
        params = {"fixture": fixture_id}

        data = self._request("fixtures/statistics", params)
        return data.get("response", [])


def transform_fixture_to_db(api_fixture: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform API-Football fixture format to our DB schema

    Args:
        api_fixture: Fixture data from API-Football

    Returns:
        Dict ready for insertion into fixtures table
    """
    fixture = api_fixture["fixture"]
    league = api_fixture["league"]
    teams = api_fixture["teams"]
    goals = api_fixture["goals"]

    return {
        "id": fixture["id"],
        "league_id": league["id"],
        "season": league["season"],
        "kickoff_time": fixture["date"],
        "status": fixture["status"]["short"],
        "venue": fixture["venue"]["name"] if fixture["venue"] else None,
        "referee": fixture["referee"],
        "home_team_id": teams["home"]["id"],
        "home_team_name": teams["home"]["name"],
        "away_team_id": teams["away"]["id"],
        "away_team_name": teams["away"]["name"],
        "home_score": goals["home"],
        "away_score": goals["away"],
        "round": league["round"],
        "last_synced_at": datetime.utcnow().isoformat(),
    }


def transform_odds_to_db(api_odds: Dict[str, Any], fixture_id: int) -> List[Dict[str, Any]]:
    """
    Transform API-Football odds format to our DB schema

    Args:
        api_odds: Odds data from API-Football
        fixture_id: Fixture ID

    Returns:
        List of odds snapshots ready for insertion
    """
    snapshots = []

    if not api_odds or "bookmakers" not in api_odds:
        return snapshots

    for bookmaker_data in api_odds.get("bookmakers", []):
        bookmaker_name = bookmaker_data["name"]

        for bet in bookmaker_data.get("bets", []):
            market_key = _normalize_market_key(bet["name"])
            odds_data = {}

            # Transform values to our format
            for value in bet.get("values", []):
                # Handle both string and numeric value keys
                val_key = str(value["value"]).lower()
                odds_data[val_key] = float(value["odd"])

            snapshots.append(
                {
                    "fixture_id": fixture_id,
                    "bookmaker": bookmaker_name,
                    "market_key": market_key,
                    "odds_data": odds_data,
                    "snapshot_at": datetime.utcnow().isoformat(),
                }
            )

    return snapshots


def clear_api_cache():
    """Clear all cached API responses (useful for testing or forcing fresh data)"""
    global _API_CACHE
    cache_size = len(_API_CACHE)
    _API_CACHE.clear()
    logger.info("api_cache_cleared", entries_removed=cache_size)
    return cache_size


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics"""
    return {
        "total_entries": len(_API_CACHE),
        "cache_keys": list(_API_CACHE.keys())[:10],  # Show first 10 keys
    }


def _normalize_market_key(api_market_name: str) -> str:
    """Normalize API-Football market names to our standard keys"""
    market_map = {
        "Match Winner": "match_winner",
        "Home/Away": "match_winner",
        "Goals Over/Under": "over_under_2.5",
        "Both Teams Score": "both_teams_score",
        "Double Chance": "double_chance",
        "Asian Handicap": "asian_handicap",
    }

    return market_map.get(api_market_name, api_market_name.lower().replace(" ", "_"))


# Global singleton instance with caching
api_football_client = APIFootballClient()
