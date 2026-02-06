"""
Supabase Database Service
Handles all database operations
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import structlog
from supabase import Client, create_client

from app.config import settings

logger = structlog.get_logger()


class DatabaseService:
    """Service for database operations via Supabase"""

    def __init__(self):
        self._client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """Lazy-load Supabase client"""
        if self._client is None:
            if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
                raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are required")

            self._client = create_client(
                supabase_url=settings.SUPABASE_URL, supabase_key=settings.SUPABASE_SERVICE_ROLE_KEY
            )
        return self._client

    # ========================================================================
    # FIXTURES
    # ========================================================================

    def upsert_fixtures(self, fixtures: List[Dict[str, Any]]) -> int:
        """
        Upsert fixtures (insert or update if exists)

        Returns:
            Number of fixtures upserted
        """
        try:
            result = self.client.table("fixtures").upsert(fixtures, on_conflict="id").execute()

            count = len(result.data) if result.data else 0
            logger.info("fixtures_upserted", count=count)
            return count
        except Exception as e:
            logger.error("fixtures_upsert_error", error=str(e))
            raise

    def get_fixtures(
        self, league_id: Optional[int] = None, status: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get fixtures with optional filters"""
        query = self.client.table("fixtures").select("*")

        if league_id:
            query = query.eq("league_id", league_id)
        if status:
            query = query.eq("status", status)

        query = query.order("kickoff_time").limit(limit)

        result = query.execute()
        return result.data

    def get_fixture_by_id(self, fixture_id: int) -> Optional[Dict[str, Any]]:
        """Get single fixture by ID"""
        result = self.client.table("fixtures").select("*").eq("id", fixture_id).execute()
        return result.data[0] if result.data else None

    # ========================================================================
    # TEAM STATISTICS
    # ========================================================================

    def upsert_team_statistics(self, team_stats: List[Dict[str, Any]]) -> int:
        """
        Upsert team statistics (insert or update if exists)

        Args:
            team_stats: List of team stat dictionaries with keys:
                - team_id: int
                - league_id: int
                - season: int
                - statistics: dict (API response)

        Returns:
            Number of team stats upserted
        """
        try:
            result = (
                self.client.table("team_statistics")
                .upsert(team_stats, on_conflict="team_id,league_id,season")
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.info("team_statistics_upserted", count=count)
            return count
        except Exception as e:
            logger.error("team_statistics_upsert_error", error=str(e))
            raise

    def get_team_statistics(
        self, team_id: int, league_id: int, season: int
    ) -> Optional[Dict[str, Any]]:
        """Get team statistics for a specific league/season"""
        result = (
            self.client.table("team_statistics")
            .select("*")
            .eq("team_id", team_id)
            .eq("league_id", league_id)
            .eq("season", season)
            .execute()
        )
        return result.data[0] if result.data else None

    # ========================================================================
    # ODDS
    # ========================================================================

    def insert_odds_snapshots(self, snapshots: List[Dict[str, Any]]) -> int:
        """
        Insert odds snapshots

        Returns:
            Number of snapshots inserted
        """
        try:
            result = self.client.table("odds_snapshots").insert(snapshots).execute()
            count = len(result.data) if result.data else 0
            logger.info("odds_snapshots_inserted", count=count)
            return count
        except Exception as e:
            logger.error("odds_insert_error", error=str(e))
            raise

    def get_latest_odds(
        self, fixture_id: int, market_key: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get latest odds for a fixture"""
        query = self.client.table("odds_snapshots").select("*").eq("fixture_id", fixture_id)

        if market_key:
            query = query.eq("market_key", market_key)

        query = query.order("snapshot_at", desc=True).limit(10)

        result = query.execute()
        return result.data

    # ========================================================================
    # PREDICTIONS
    # ========================================================================

    def upsert_predictions(self, predictions: List[Dict[str, Any]]) -> int:
        """
        Insert model predictions (deletes existing for same fixture first)

        Returns:
            Number of predictions inserted
        """
        try:
            # Get unique fixture IDs
            fixture_ids = list(set(p["fixture_id"] for p in predictions))

            # Delete existing predictions for these fixtures
            for fid in fixture_ids:
                self.client.table("model_predictions").delete().eq("fixture_id", fid).execute()

            # Insert new predictions
            result = self.client.table("model_predictions").insert(predictions).execute()
            count = len(result.data) if result.data else 0
            logger.info("predictions_inserted", count=count)
            return count
        except Exception as e:
            logger.error("predictions_insert_error", error=str(e))
            raise

    def get_predictions(
        self, fixture_id: Optional[int] = None, quality_grade: Optional[str] = None, limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get predictions with optional filters"""
        query = self.client.table("model_predictions").select("*")

        if fixture_id:
            query = query.eq("fixture_id", fixture_id)
        if quality_grade:
            query = query.eq("quality_grade", quality_grade)

        query = query.order("confidence_score", desc=True).limit(limit)

        result = query.execute()
        return result.data

    # ========================================================================
    # QUALITY SCORES
    # ========================================================================

    def upsert_quality_scores(self, scores: List[Dict[str, Any]]) -> int:
        """
        Insert quality scores (deletes existing for same fixture first)

        Returns:
            Number of scores inserted
        """
        try:
            # Get unique fixture IDs
            fixture_ids = list(set(s["fixture_id"] for s in scores))

            # Delete existing scores for these fixtures
            for fid in fixture_ids:
                self.client.table("quality_scores").delete().eq("fixture_id", fid).execute()

            # Insert new scores
            result = self.client.table("quality_scores").insert(scores).execute()
            count = len(result.data) if result.data else 0
            logger.info("quality_scores_inserted", count=count)
            return count
        except Exception as e:
            logger.error("quality_scores_insert_error", error=str(e))
            raise

    # ========================================================================
    # LEAGUES
    # ========================================================================

    def get_active_leagues(self) -> List[Dict[str, Any]]:
        """Get all active leagues"""
        result = self.client.table("leagues").select("*").eq("is_active", True).execute()
        return result.data

    def get_league_by_id(self, league_id: int) -> Optional[Dict[str, Any]]:
        """Get league by ID"""
        result = self.client.table("leagues").select("*").eq("id", league_id).execute()
        return result.data[0] if result.data else None

    # ========================================================================
    # ELO RATINGS
    # ========================================================================

    def get_team_elo(self, team_id: int, season: int = 2025) -> Optional[Dict[str, Any]]:
        """Get current Elo rating for a team"""
        result = (
            self.client.table("team_elo_ratings")
            .select("*")
            .eq("team_id", team_id)
            .eq("season", season)
            .execute()
        )
        return result.data[0] if result.data else None

    def get_all_team_elos(self, season: int = 2025) -> List[Dict[str, Any]]:
        """Get all Elo ratings for a season"""
        result = (
            self.client.table("team_elo_ratings")
            .select("*")
            .eq("season", season)
            .order("elo_rating", desc=True)
            .execute()
        )
        return result.data

    def upsert_team_elo(self, elo_data: Dict[str, Any]) -> bool:
        """
        Upsert team Elo rating

        Args:
            elo_data: Dict with team_id, team_name, league_id, elo_rating, etc.

        Returns:
            True if successful
        """
        try:
            # Add updated_at timestamp
            elo_data["updated_at"] = datetime.utcnow().isoformat()

            result = (
                self.client.table("team_elo_ratings")
                .upsert(elo_data, on_conflict="team_id,season")
                .execute()
            )

            return bool(result.data)
        except Exception as e:
            logger.error("elo_upsert_error", error=str(e), team_id=elo_data.get("team_id"))
            raise

    def bulk_upsert_team_elos(self, elo_list: List[Dict[str, Any]]) -> int:
        """
        Bulk upsert team Elo ratings

        Returns:
            Number of ratings upserted
        """
        try:
            now = datetime.utcnow().isoformat()
            for elo in elo_list:
                elo["updated_at"] = now

            result = (
                self.client.table("team_elo_ratings")
                .upsert(elo_list, on_conflict="team_id,season")
                .execute()
            )

            count = len(result.data) if result.data else 0
            logger.info("elo_ratings_upserted", count=count)
            return count
        except Exception as e:
            logger.error("elo_bulk_upsert_error", error=str(e))
            raise

    def insert_elo_history(self, history_records: List[Dict[str, Any]]) -> int:
        """
        Insert Elo history records

        Returns:
            Number of records inserted
        """
        try:
            result = self.client.table("team_elo_history").insert(history_records).execute()
            count = len(result.data) if result.data else 0
            logger.info("elo_history_inserted", count=count)
            return count
        except Exception as e:
            logger.error("elo_history_insert_error", error=str(e))
            raise

    def get_finished_fixtures(
        self, league_id: Optional[int] = None, season: Optional[int] = None, limit: int = 500
    ) -> List[Dict[str, Any]]:
        """Get finished fixtures from database for Elo calculation"""
        query = self.client.table("fixtures").select("*").eq("status", "FT")

        if season:
            query = query.eq("season", season)

        if league_id:
            query = query.eq("league_id", league_id)

        query = query.order("kickoff_time").limit(limit)

        result = query.execute()
        return result.data


# Singleton instance
db_service = DatabaseService()
