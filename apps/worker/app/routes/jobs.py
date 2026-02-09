"""
Job endpoints for worker tasks
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

import structlog
from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.ml import MatchPredictor, QualityScorer
from app.ml.dixon_coles import DixonColesModel, dixon_coles_model
from app.ml.elo import DEFAULT_RATINGS, TOP_TEAM_BONUSES, EloRatingSystem
from app.services.apifootball import (
    api_football_client,
    transform_fixture_to_db,
    transform_odds_to_db,
)
from app.services.database import db_service

router = APIRouter(prefix="/jobs", tags=["jobs"])
logger = structlog.get_logger()

# ML instances
predictor = MatchPredictor()
quality_scorer = QualityScorer()


@router.post("/sync-fixtures")
def sync_fixtures():
    """
    Sync upcoming fixtures from API-Football for next 7 days

    This job:
    1. Fetches active leagues from DB
    2. For each league, gets fixtures for next 7 days
    3. Upserts fixtures into database
    4. Fetches and stores odds for each fixture
    """
    try:
        # Get active leagues
        leagues = db_service.get_active_leagues()

        if not leagues:
            return {"status": "warning", "message": "No active leagues found", "fixtures_synced": 0}

        client = api_football_client
        total_fixtures = 0
        total_odds = 0

        # Date range: today to 7 days from now
        date_from = datetime.utcnow().strftime("%Y-%m-%d")
        date_to = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")

        logger.info(
            "sync_fixtures_started",
            leagues_count=len(leagues),
            date_from=date_from,
            date_to=date_to,
        )

        for league in leagues:
            league_id = league["id"]
            season = league.get("season", 2025)

            try:
                # Fetch fixtures from API
                api_fixtures = client.get_fixtures(
                    league_id=league_id,
                    season=season,
                    date_from=date_from,
                    date_to=date_to,
                    status="NS",  # Not Started
                )

                if not api_fixtures:
                    logger.info(
                        "no_fixtures_found", league_id=league_id, league_name=league["name"]
                    )
                    continue

                # Transform and upsert fixtures
                db_fixtures = [transform_fixture_to_db(f) for f in api_fixtures]
                fixtures_count = db_service.upsert_fixtures(db_fixtures)
                total_fixtures += fixtures_count

                # Fetch odds for each fixture (limit to first 5 to save API calls)
                for api_fixture in api_fixtures[:5]:
                    fixture_id = api_fixture["fixture"]["id"]

                    try:
                        api_odds = client.get_odds(fixture_id)
                        if api_odds:
                            odds_snapshots = transform_odds_to_db(api_odds[0], fixture_id)
                            if odds_snapshots:
                                odds_count = db_service.insert_odds_snapshots(odds_snapshots)
                                total_odds += odds_count
                    except Exception as e:
                        logger.warning("odds_fetch_failed", fixture_id=fixture_id, error=str(e))

                logger.info(
                    "league_synced",
                    league_id=league_id,
                    league_name=league["name"],
                    fixtures_count=fixtures_count,
                )

            except Exception as e:
                logger.error("league_sync_failed", league_id=league_id, error=str(e))
                continue

        return {
            "status": "success",
            "message": f"Synced {total_fixtures} fixtures and {total_odds} odds snapshots",
            "fixtures_synced": total_fixtures,
            "odds_synced": total_odds,
            "leagues_processed": len(leagues),
            "date_range": {"from": date_from, "to": date_to},
        }

    except Exception as e:
        logger.error("sync_fixtures_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-predictions")
def run_predictions():
    """
    Run ML predictions for all upcoming fixtures

    Generates predictions using ensemble model (Elo + statistical features)
    and calculates quality scores for each prediction
    """
    try:
        # Get upcoming fixtures directly with status filter
        upcoming = db_service.get_fixtures(status="NS", limit=500)

        if not upcoming:
            return {
                "status": "warning",
                "message": "No upcoming fixtures to predict",
                "predictions_generated": 0,
            }

        logger.info("run_predictions_started", fixtures_count=len(upcoming))

        # Generate predictions for all fixtures
        all_predictions = []
        all_quality_scores = []

        for fixture in upcoming:
            try:
                # Generate predictions
                predictions = predictor.predict_fixture(fixture)
                all_predictions.extend(predictions)

                # Generate quality scores for each prediction
                fixture_dict = {fixture["id"]: fixture}
                for pred in predictions:
                    quality = quality_scorer.score_prediction(pred, fixture)
                    all_quality_scores.append(quality)

            except Exception as e:
                logger.warning(
                    "fixture_prediction_failed", fixture_id=fixture.get("id"), error=str(e)
                )
                continue

        # Insert predictions into database
        predictions_inserted = 0
        if all_predictions:
            predictions_inserted = db_service.upsert_predictions(all_predictions)

        # Insert quality scores into database
        quality_inserted = 0
        if all_quality_scores:
            quality_inserted = db_service.upsert_quality_scores(all_quality_scores)

        # Count by grade
        grade_counts = {}
        for pred in all_predictions:
            grade = pred.get("quality_grade", "C")
            grade_counts[grade] = grade_counts.get(grade, 0) + 1

        logger.info(
            "run_predictions_complete",
            predictions_count=predictions_inserted,
            quality_scores_count=quality_inserted,
            grade_distribution=grade_counts,
        )

        return {
            "status": "success",
            "message": f"Generated {predictions_inserted} predictions for {len(upcoming)} fixtures",
            "fixtures_processed": len(upcoming),
            "predictions_generated": predictions_inserted,
            "quality_scores_generated": quality_inserted,
            "grade_distribution": grade_counts,
        }

    except Exception as e:
        logger.error("run_predictions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
def job_status():
    """Get worker status and statistics"""
    try:
        # Get counts from database
        fixtures = db_service.get_fixtures(limit=1000)
        leagues = db_service.get_active_leagues()
        predictions = db_service.get_predictions(limit=1000)

        # Count by status
        upcoming = len([f for f in fixtures if f["status"] == "NS"])
        live = len([f for f in fixtures if f["status"] in ["1H", "2H", "HT"]])
        finished = len([f for f in fixtures if f["status"] == "FT"])

        return {
            "status": "healthy",
            "worker_version": "1.0.0",
            "statistics": {
                "total_fixtures": len(fixtures),
                "upcoming_fixtures": upcoming,
                "live_fixtures": live,
                "finished_fixtures": finished,
                "active_leagues": len(leagues),
                "total_predictions": len(predictions),
            },
        }
    except Exception as e:
        logger.error("status_check_error", error=str(e))
        return {"status": "error", "error": str(e)}


@router.post("/sync-odds")
def sync_odds(limit: int = 50):
    """
    Sync odds from API-Football for all upcoming fixtures

    This job fetches odds from Bet365 for each upcoming fixture
    and stores them in the database for value bet detection.

    Args:
        limit: Maximum number of fixtures to sync odds for (default 50)
    """
    try:
        # Get all upcoming fixtures
        all_fixtures = db_service.get_fixtures(limit=500)
        # Filter: only NS status AND real fixtures (ID > 1300000, not seed data)
        upcoming = [f for f in all_fixtures if f.get("status") == "NS" and f.get("id", 0) > 1300000]

        if not upcoming:
            return {
                "status": "warning",
                "message": "No real upcoming fixtures found (only seed data)",
                "odds_synced": 0,
            }

        # Limit fixtures to process
        fixtures_to_process = upcoming[:limit]

        logger.info(
            "sync_odds_started", total_fixtures=len(upcoming), processing=len(fixtures_to_process)
        )

        client = api_football_client
        total_odds = 0
        fixtures_with_odds = 0
        errors = 0

        for fixture in fixtures_to_process:
            fixture_id = fixture["id"]

            try:
                # Fetch odds from API-Football
                api_odds = client.get_odds(fixture_id)

                if api_odds and len(api_odds) > 0:
                    # Transform to DB format
                    odds_snapshots = transform_odds_to_db(api_odds[0], fixture_id)

                    if odds_snapshots:
                        # Insert into database
                        odds_count = db_service.insert_odds_snapshots(odds_snapshots)
                        total_odds += odds_count
                        fixtures_with_odds += 1

                        logger.info(
                            "odds_synced",
                            fixture_id=fixture_id,
                            match=f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                            odds_count=odds_count,
                        )
                else:
                    logger.info(
                        "no_odds_available",
                        fixture_id=fixture_id,
                        match=f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                    )

            except Exception as e:
                errors += 1
                logger.warning("odds_sync_failed", fixture_id=fixture_id, error=str(e))
                continue

        return {
            "status": "success",
            "message": f"Synced odds for {fixtures_with_odds}/{len(fixtures_to_process)} fixtures",
            "fixtures_processed": len(fixtures_to_process),
            "fixtures_with_odds": fixtures_with_odds,
            "total_odds_snapshots": total_odds,
            "errors": errors,
        }

    except Exception as e:
        logger.error("sync_odds_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# ELO RATING JOBS
# ============================================================================


@router.post("/sync-historical")
def sync_historical_fixtures(league_id: int = 39, season: int = 2024, limit: int = 100):
    """
    Sync historical (finished) fixtures from API-Football

    This job fetches completed matches from past seasons to build
    Elo rating history for more accurate predictions.

    Args:
        league_id: League to sync (default 39 = Premier League)
        season: Season year (default 2024 = last season)
        limit: Max fixtures per request (API limit is ~100)
    """
    try:
        client = api_football_client

        logger.info("sync_historical_started", league_id=league_id, season=season)

        # Get finished fixtures from API
        api_fixtures = client.get_all_season_results(league_id, season)

        if not api_fixtures:
            return {
                "status": "warning",
                "message": f"No historical fixtures found for league {league_id} season {season}",
                "fixtures_synced": 0,
            }

        # Transform and upsert fixtures
        db_fixtures = [transform_fixture_to_db(f) for f in api_fixtures[:limit]]
        fixtures_count = db_service.upsert_fixtures(db_fixtures)

        logger.info(
            "sync_historical_complete",
            league_id=league_id,
            season=season,
            fixtures_synced=fixtures_count,
        )

        return {
            "status": "success",
            "message": f"Synced {fixtures_count} historical fixtures for season {season}",
            "league_id": league_id,
            "season": season,
            "fixtures_synced": fixtures_count,
            "total_available": len(api_fixtures),
        }

    except Exception as e:
        logger.error("sync_historical_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-elo")
def calculate_elo_ratings(season: int = 2025, include_previous_season: bool = True):
    """
    Calculate Elo ratings from historical match results

    This job:
    1. Loads finished fixtures from database (optionally including previous season)
    2. Processes them chronologically to calculate Elo ratings
    3. Persists ratings to team_elo_ratings table
    4. Records rating changes in team_elo_history

    Run this after syncing historical fixtures to improve prediction accuracy.

    Args:
        season: Current season year (default 2025)
        include_previous_season: Also process previous season for more data
    """
    try:
        # Create fresh Elo system
        elo = EloRatingSystem(k_factor=32.0, home_advantage=65.0)

        # Load existing ratings from DB first (to maintain continuity)
        existing_elos = db_service.get_all_team_elos(season)
        for elo_record in existing_elos:
            elo.ratings[elo_record["team_id"]] = float(elo_record["elo_rating"])

        logger.info(
            "calculate_elo_started",
            season=season,
            existing_ratings=len(existing_elos),
            include_previous=include_previous_season,
        )

        # Get finished fixtures to process
        all_fixtures = []

        if include_previous_season:
            prev_fixtures = db_service.get_finished_fixtures(season=season - 1, limit=1000)
            all_fixtures.extend(prev_fixtures)
            logger.info("loaded_previous_season", count=len(prev_fixtures))

        current_fixtures = db_service.get_finished_fixtures(season=season, limit=1000)
        all_fixtures.extend(current_fixtures)
        logger.info("loaded_current_season", count=len(current_fixtures))

        if not all_fixtures:
            return {
                "status": "warning",
                "message": "No finished fixtures found to calculate Elo ratings",
                "ratings_updated": 0,
            }

        # Sort by kickoff time (oldest first)
        all_fixtures.sort(key=lambda x: x.get("kickoff_time", ""))

        # Track team stats
        team_stats: Dict[int, Dict[str, Any]] = {}
        history_records = []
        matches_processed = 0

        for fixture in all_fixtures:
            home_id = fixture["home_team_id"]
            away_id = fixture["away_team_id"]
            home_name = fixture["home_team_name"]
            away_name = fixture["away_team_name"]
            home_score = fixture.get("home_score")
            away_score = fixture.get("away_score")
            league_id = fixture["league_id"]
            match_date = fixture.get("kickoff_time")

            # Skip if no score
            if home_score is None or away_score is None:
                continue

            # Get current ratings
            home_rating_before = elo.get_rating(home_id, league_id)
            away_rating_before = elo.get_rating(away_id, league_id)

            # Calculate actual scores
            if home_score > away_score:
                home_actual, away_actual = 1.0, 0.0
                home_result, away_result = "W", "L"
            elif home_score < away_score:
                home_actual, away_actual = 0.0, 1.0
                home_result, away_result = "L", "W"
            else:
                home_actual, away_actual = 0.5, 0.5
                home_result, away_result = "D", "D"

            # Update Elo ratings
            home_rating_after = elo.update_rating(
                team_id=home_id,
                opponent_id=away_id,
                actual_score=home_actual,
                goal_diff=home_score - away_score,
                is_home=True,
                league_id=league_id,
            )

            away_rating_after = elo.update_rating(
                team_id=away_id,
                opponent_id=home_id,
                actual_score=away_actual,
                goal_diff=away_score - home_score,
                is_home=False,
                league_id=league_id,
            )

            # Initialize team stats if needed
            for team_id, team_name in [(home_id, home_name), (away_id, away_name)]:
                if team_id not in team_stats:
                    team_stats[team_id] = {
                        "team_id": team_id,
                        "team_name": team_name,
                        "league_id": league_id,
                        "season": season,
                        "matches_played": 0,
                        "wins": 0,
                        "draws": 0,
                        "losses": 0,
                        "goals_for": 0,
                        "goals_against": 0,
                        "peak_rating": 1500.0,
                        "peak_date": None,
                        "last_match_id": None,
                        "last_match_date": None,
                        "last_rating_change": 0.0,
                    }

            # Update home team stats
            team_stats[home_id]["matches_played"] += 1
            team_stats[home_id]["goals_for"] += home_score
            team_stats[home_id]["goals_against"] += away_score
            team_stats[home_id]["last_match_id"] = fixture["id"]
            team_stats[home_id]["last_match_date"] = match_date
            team_stats[home_id]["last_rating_change"] = home_rating_after - home_rating_before

            if home_result == "W":
                team_stats[home_id]["wins"] += 1
            elif home_result == "D":
                team_stats[home_id]["draws"] += 1
            else:
                team_stats[home_id]["losses"] += 1

            if home_rating_after > team_stats[home_id]["peak_rating"]:
                team_stats[home_id]["peak_rating"] = home_rating_after
                team_stats[home_id]["peak_date"] = match_date

            # Update away team stats
            team_stats[away_id]["matches_played"] += 1
            team_stats[away_id]["goals_for"] += away_score
            team_stats[away_id]["goals_against"] += home_score
            team_stats[away_id]["last_match_id"] = fixture["id"]
            team_stats[away_id]["last_match_date"] = match_date
            team_stats[away_id]["last_rating_change"] = away_rating_after - away_rating_before

            if away_result == "W":
                team_stats[away_id]["wins"] += 1
            elif away_result == "D":
                team_stats[away_id]["draws"] += 1
            else:
                team_stats[away_id]["losses"] += 1

            if away_rating_after > team_stats[away_id]["peak_rating"]:
                team_stats[away_id]["peak_rating"] = away_rating_after
                team_stats[away_id]["peak_date"] = match_date

            # Record history
            history_records.append(
                {
                    "team_id": home_id,
                    "fixture_id": fixture["id"],
                    "rating_before": round(home_rating_before, 2),
                    "rating_after": round(home_rating_after, 2),
                    "rating_change": round(home_rating_after - home_rating_before, 2),
                    "opponent_id": away_id,
                    "opponent_rating": round(away_rating_before, 2),
                    "was_home": True,
                    "goals_for": home_score,
                    "goals_against": away_score,
                    "result": home_result,
                    "match_date": match_date,
                }
            )

            history_records.append(
                {
                    "team_id": away_id,
                    "fixture_id": fixture["id"],
                    "rating_before": round(away_rating_before, 2),
                    "rating_after": round(away_rating_after, 2),
                    "rating_change": round(away_rating_after - away_rating_before, 2),
                    "opponent_id": home_id,
                    "opponent_rating": round(home_rating_before, 2),
                    "was_home": False,
                    "goals_for": away_score,
                    "goals_against": home_score,
                    "result": away_result,
                    "match_date": match_date,
                }
            )

            matches_processed += 1

        # Prepare final Elo data for DB
        elo_data_list = []
        for team_id, stats in team_stats.items():
            stats["elo_rating"] = round(elo.ratings.get(team_id, 1500.0), 2)
            elo_data_list.append(stats)

        # Save to database
        ratings_saved = 0
        if elo_data_list:
            ratings_saved = db_service.bulk_upsert_team_elos(elo_data_list)

        history_saved = 0
        if history_records:
            # Limit history to last 500 records to avoid timeout
            history_saved = db_service.insert_elo_history(history_records[-500:])

        # Get top 10 teams by Elo
        top_teams = sorted(elo_data_list, key=lambda x: x["elo_rating"], reverse=True)[:10]
        top_teams_summary = [
            {"team": t["team_name"], "elo": t["elo_rating"], "matches": t["matches_played"]}
            for t in top_teams
        ]

        logger.info(
            "calculate_elo_complete",
            matches_processed=matches_processed,
            teams_updated=ratings_saved,
            history_records=history_saved,
        )

        return {
            "status": "success",
            "message": f"Calculated Elo ratings from {matches_processed} matches",
            "matches_processed": matches_processed,
            "teams_updated": ratings_saved,
            "history_records": history_saved,
            "top_teams": top_teams_summary,
        }

    except Exception as e:
        logger.error("calculate_elo_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/elo-rankings")
def get_elo_rankings(league_id: int = None, season: int = 2025, limit: int = 30):
    """
    Get current Elo rankings for teams

    Args:
        league_id: Filter by league (optional)
        season: Season year (default 2025)
        limit: Max teams to return (default 30)
    """
    try:
        all_elos = db_service.get_all_team_elos(season)

        if league_id:
            all_elos = [e for e in all_elos if e.get("league_id") == league_id]

        # Sort by Elo rating
        all_elos.sort(key=lambda x: float(x.get("elo_rating", 1500)), reverse=True)

        # Add rank
        rankings = []
        for i, team in enumerate(all_elos[:limit], 1):
            rankings.append(
                {
                    "rank": i,
                    "team_name": team["team_name"],
                    "team_id": team["team_id"],
                    "league_id": team["league_id"],
                    "elo_rating": float(team["elo_rating"]),
                    "matches_played": team["matches_played"],
                    "wins": team["wins"],
                    "draws": team["draws"],
                    "losses": team["losses"],
                    "goal_diff": team["goals_for"] - team["goals_against"],
                    "last_change": float(team.get("last_rating_change", 0)),
                }
            )

        return {"status": "success", "season": season, "league_id": league_id, "rankings": rankings}

    except Exception as e:
        logger.error("elo_rankings_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-historical-stats")
def get_team_historical_stats(team_id: int = None, league_id: int = None, limit: int = 50):
    """
    Get comprehensive historical statistics for teams

    Calculates from ALL historical fixtures:
    - Goals per game (home/away)
    - Over 2.5 / BTTS percentages
    - Form (last 5 matches)
    - Clean sheet rates
    - Win/Draw/Loss rates

    Args:
        team_id: Get stats for specific team (optional)
        league_id: Filter by league (optional)
        limit: Max teams to return (default 50)

    Returns:
        Team statistics based on historical data
    """
    from app.ml.team_stats import team_stats_calculator

    try:
        # Get all finished fixtures
        fixtures = db_service.get_finished_fixtures(season=None)

        if not fixtures:
            return {"status": "warning", "message": "No historical fixtures found", "stats": []}

        # Calculate stats for all teams
        all_stats = team_stats_calculator.calculate_all_team_stats(fixtures)

        # Filter if team_id specified
        if team_id:
            team_stat = all_stats.get(team_id)
            if team_stat:
                return {"status": "success", "fixtures_analyzed": len(fixtures), "stats": team_stat}
            else:
                return {
                    "status": "warning",
                    "message": f"No stats found for team_id {team_id}",
                    "stats": None,
                }

        # Convert to list and filter by league if needed
        stats_list = list(all_stats.values())

        if league_id:
            stats_list = [s for s in stats_list if s.get("league_id") == league_id]

        # Sort by total matches (most data = most reliable)
        stats_list.sort(key=lambda x: x.get("total_matches", 0), reverse=True)

        # Take top N
        stats_list = stats_list[:limit]

        # Format output
        formatted_stats = []
        for stat in stats_list:
            formatted_stats.append(
                {
                    "team_id": stat["team_id"],
                    "team_name": stat["team_name"],
                    "matches": stat["total_matches"],
                    "win_rate": stat["win_rate"],
                    "goals_per_game": stat["goals_per_game"],
                    "goals_conceded_per_game": stat["goals_conceded_per_game"],
                    "over_2_5_pct": stat["over_2_5_pct"],
                    "btts_pct": stat["btts_pct"],
                    "clean_sheet_pct": stat["clean_sheet_pct"],
                    "form_last_5": stat["form_last_5"],
                    "form_ppg": stat["form_ppg_last_5"],
                    "home_win_rate": stat["home_win_rate"],
                    "away_win_rate": stat["away_win_rate"],
                    "streak": f"{stat['streak_type']}{stat['current_streak']}",
                }
            )

        return {
            "status": "success",
            "fixtures_analyzed": len(fixtures),
            "teams_count": len(all_stats),
            "stats": formatted_stats,
        }

    except Exception as e:
        logger.error("team_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/match-preview")
def get_match_preview(home_team_id: int, away_team_id: int):
    """
    Get comprehensive match preview with predictions

    Combines Elo ratings and historical statistics to provide:
    - Win/Draw/Loss probabilities
    - Expected goals
    - Over/Under and BTTS predictions
    - Form comparison
    - Head-to-head analysis

    Args:
        home_team_id: Home team ID
        away_team_id: Away team ID

    Returns:
        Comprehensive match preview
    """
    from app.ml.elo import elo_system
    from app.ml.team_stats import team_stats_calculator

    try:
        # Load historical stats
        fixtures = db_service.get_finished_fixtures(season=None)
        team_stats_calculator.calculate_all_team_stats(fixtures)

        # Load Elo
        elo_records = db_service.get_all_team_elos(2025)
        for record in elo_records:
            elo_system.ratings[record["team_id"]] = float(record["elo_rating"])

        # Get stats for both teams
        home_stats = team_stats_calculator.get_team_stats(home_team_id)
        away_stats = team_stats_calculator.get_team_stats(away_team_id)

        # Get Elo prediction
        elo_pred = elo_system.predict_match(home_team_id, away_team_id)

        # Get match features
        features = team_stats_calculator.get_match_features(home_team_id, away_team_id)

        # Over/Under prediction
        over_under = team_stats_calculator.predict_over_under(home_team_id, away_team_id)

        # BTTS prediction
        btts = team_stats_calculator.predict_btts(home_team_id, away_team_id)

        return {
            "status": "success",
            "match": {
                "home_team": {
                    "id": home_team_id,
                    "name": home_stats.get("team_name") if home_stats else "Unknown",
                    "elo": elo_pred["home_elo"],
                    "form": home_stats.get("form_last_5") if home_stats else "N/A",
                    "goals_per_game": home_stats.get("home_goals_per_game") if home_stats else None,
                    "over_2_5_pct": home_stats.get("over_2_5_pct") if home_stats else None,
                    "btts_pct": home_stats.get("btts_pct") if home_stats else None,
                },
                "away_team": {
                    "id": away_team_id,
                    "name": away_stats.get("team_name") if away_stats else "Unknown",
                    "elo": elo_pred["away_elo"],
                    "form": away_stats.get("form_last_5") if away_stats else "N/A",
                    "goals_per_game": away_stats.get("away_goals_per_game") if away_stats else None,
                    "over_2_5_pct": away_stats.get("over_2_5_pct") if away_stats else None,
                    "btts_pct": away_stats.get("btts_pct") if away_stats else None,
                },
            },
            "predictions": {
                "match_winner": {
                    "home_win": round(elo_pred["home_win"], 3),
                    "draw": round(elo_pred["draw"], 3),
                    "away_win": round(elo_pred["away_win"], 3),
                },
                "over_under_2_5": over_under,
                "btts": btts,
                "expected_goals": {
                    "home": round(features.get("expected_home_goals", 1.5), 2),
                    "away": round(features.get("expected_away_goals", 1.0), 2),
                    "total": round(
                        features.get("expected_home_goals", 1.5)
                        + features.get("expected_away_goals", 1.0),
                        2,
                    ),
                },
            },
            "elo_analysis": {
                "elo_diff": elo_pred["elo_diff"],
                "home_advantage": 65,
                "effective_diff": elo_pred["elo_diff"] + 65,
            },
        }

    except Exception as e:
        logger.error("match_preview_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all-historical")
def sync_all_historical_data(
    season: int = 2024, matches_per_league: int = 150, recalculate_elo: bool = True
):
    """
    Sync historical data from ALL active leagues with rate limiting

    This endpoint syncs finished matches from all active leagues,
    with a small delay between requests to avoid API rate limits.

    Args:
        season: Season to sync (default 2024 = last season)
        matches_per_league: Max matches per league (default 150)
        recalculate_elo: Whether to recalculate Elo after sync (default True)

    Returns:
        Summary of all synced data
    """
    import time

    try:
        # Get all active leagues
        leagues = db_service.get_active_leagues()

        if not leagues:
            return {"status": "warning", "message": "No active leagues found"}

        client = api_football_client
        results = []
        total_fixtures = 0
        total_teams = set()

        logger.info(
            "sync_all_historical_started",
            leagues_count=len(leagues),
            season=season,
            matches_per_league=matches_per_league,
        )

        for i, league in enumerate(leagues):
            league_id = league["id"]
            league_name = league["name"]

            try:
                # Add delay between requests (1 second) to avoid rate limits
                if i > 0:
                    time.sleep(1.0)

                # Fetch finished fixtures
                api_fixtures = client.get_all_season_results(league_id, season)

                if not api_fixtures:
                    results.append(
                        {
                            "league": league_name,
                            "league_id": league_id,
                            "status": "no_data",
                            "fixtures": 0,
                        }
                    )
                    continue

                # Limit fixtures
                fixtures_to_sync = api_fixtures[:matches_per_league]

                # Transform and upsert
                db_fixtures = [transform_fixture_to_db(f) for f in fixtures_to_sync]
                fixtures_count = db_service.upsert_fixtures(db_fixtures)
                total_fixtures += fixtures_count

                # Track unique teams
                for f in db_fixtures:
                    total_teams.add(f["home_team_id"])
                    total_teams.add(f["away_team_id"])

                results.append(
                    {
                        "league": league_name,
                        "league_id": league_id,
                        "status": "success",
                        "fixtures": fixtures_count,
                        "available": len(api_fixtures),
                    }
                )

                logger.info("league_historical_synced", league=league_name, fixtures=fixtures_count)

            except Exception as e:
                results.append(
                    {
                        "league": league_name,
                        "league_id": league_id,
                        "status": "error",
                        "error": str(e),
                    }
                )
                logger.warning("league_historical_sync_failed", league=league_name, error=str(e))
                continue

        # Recalculate Elo if requested
        elo_result = None
        if recalculate_elo and total_fixtures > 0:
            elo_result = _recalculate_all_elo()

        return {
            "status": "success",
            "message": f"Synced {total_fixtures} fixtures from {len(leagues)} leagues",
            "season": season,
            "total_fixtures": total_fixtures,
            "total_teams": len(total_teams),
            "leagues_processed": len(leagues),
            "league_results": results,
            "elo_calculation": elo_result,
        }

    except Exception as e:
        logger.error("sync_all_historical_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-multi-season")
def sync_multiple_seasons(
    start_season: int = 2021, end_season: int = 2024, matches_per_league: int = 380
):
    """
    Sync historical data from MULTIPLE SEASONS for all active leagues

    This builds a comprehensive Elo rating with 3-4 years of data.
    Each team will have 80-150+ matches for accurate ratings.

    Args:
        start_season: First season to sync (default 2021)
        end_season: Last season to sync (default 2024)
        matches_per_league: Max matches per league per season (default 380 = full season)

    Rate limiting:
        - 1.5 second delay between API calls
        - ~15 seconds per season (10 leagues)
        - Total time: ~1 minute for 4 seasons

    Returns:
        Summary of all synced data across all seasons
    """
    import time

    try:
        leagues = db_service.get_active_leagues()

        if not leagues:
            return {"status": "warning", "message": "No active leagues found"}

        client = api_football_client

        all_results = []
        grand_total_fixtures = 0
        all_teams = set()
        seasons_synced = []

        logger.info(
            "sync_multi_season_started",
            start_season=start_season,
            end_season=end_season,
            leagues_count=len(leagues),
        )

        # Iterate through seasons (oldest first for proper Elo chronology)
        for season in range(start_season, end_season + 1):
            season_fixtures = 0
            season_results = []

            logger.info(f"syncing_season_{season}")

            for i, league in enumerate(leagues):
                league_id = league["id"]
                league_name = league["name"]

                try:
                    # Rate limiting: 1.5s between calls
                    time.sleep(1.5)

                    # Fetch finished fixtures for this season
                    api_fixtures = client.get_all_season_results(league_id, season)

                    if not api_fixtures:
                        season_results.append(
                            {
                                "league": league_name,
                                "season": season,
                                "status": "no_data",
                                "fixtures": 0,
                            }
                        )
                        continue

                    # Limit fixtures (380 = full season for most leagues)
                    fixtures_to_sync = api_fixtures[:matches_per_league]

                    # Transform and upsert
                    db_fixtures = [transform_fixture_to_db(f) for f in fixtures_to_sync]
                    fixtures_count = db_service.upsert_fixtures(db_fixtures)

                    season_fixtures += fixtures_count
                    grand_total_fixtures += fixtures_count

                    # Track unique teams
                    for f in db_fixtures:
                        all_teams.add(f["home_team_id"])
                        all_teams.add(f["away_team_id"])

                    season_results.append(
                        {
                            "league": league_name,
                            "season": season,
                            "status": "success",
                            "fixtures": fixtures_count,
                        }
                    )

                    logger.info(
                        "league_season_synced",
                        league=league_name,
                        season=season,
                        fixtures=fixtures_count,
                    )

                except Exception as e:
                    season_results.append(
                        {
                            "league": league_name,
                            "season": season,
                            "status": "error",
                            "error": str(e),
                        }
                    )
                    continue

            seasons_synced.append(
                {
                    "season": season,
                    "fixtures": season_fixtures,
                    "leagues": len([r for r in season_results if r["status"] == "success"]),
                }
            )
            all_results.extend(season_results)

        # Now recalculate Elo with ALL historical data
        logger.info("recalculating_elo_from_all_seasons")
        elo_result = _recalculate_all_elo()

        return {
            "status": "success",
            "message": f"Synced {grand_total_fixtures} fixtures across {end_season - start_season + 1} seasons",
            "seasons_range": f"{start_season}-{end_season}",
            "total_fixtures": grand_total_fixtures,
            "total_teams": len(all_teams),
            "seasons_summary": seasons_synced,
            "elo_calculation": elo_result,
        }

    except Exception as e:
        logger.error("sync_multi_season_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


def _recalculate_all_elo() -> Dict[str, Any]:
    """
    Helper function to recalculate Elo ratings from ALL finished fixtures
    Processes matches in chronological order across all seasons
    """
    import time

    logger.info("recalculating_all_elo_ratings")

    # Create fresh Elo system
    elo = EloRatingSystem(k_factor=32.0, home_advantage=65.0)

    # Get ALL finished fixtures (up to 5000)
    all_finished = db_service.get_finished_fixtures(season=None, limit=5000)

    # Sort chronologically (oldest first)
    all_finished.sort(key=lambda x: x.get("kickoff_time", ""))

    logger.info(f"processing_{len(all_finished)}_historical_matches")

    # Process matches
    team_stats: Dict[int, Dict[str, Any]] = {}
    matches_processed = 0

    for fixture in all_finished:
        home_id = fixture["home_team_id"]
        away_id = fixture["away_team_id"]
        home_name = fixture["home_team_name"]
        away_name = fixture["away_team_name"]
        home_score = fixture.get("home_score")
        away_score = fixture.get("away_score")
        league_id = fixture["league_id"]
        match_date = fixture.get("kickoff_time")

        if home_score is None or away_score is None:
            continue

        # Calculate actual scores
        if home_score > away_score:
            home_actual, away_actual = 1.0, 0.0
            home_result, away_result = "W", "L"
        elif home_score < away_score:
            home_actual, away_actual = 0.0, 1.0
            home_result, away_result = "L", "W"
        else:
            home_actual, away_actual = 0.5, 0.5
            home_result, away_result = "D", "D"

        # Update Elo
        elo.update_rating(
            home_id, away_id, home_actual, home_score - away_score, True, 1.0, league_id
        )
        elo.update_rating(
            away_id, home_id, away_actual, away_score - home_score, False, 1.0, league_id
        )

        # Track stats
        for team_id, team_name, result, gf, ga in [
            (home_id, home_name, home_result, home_score, away_score),
            (away_id, away_name, away_result, away_score, home_score),
        ]:
            if team_id not in team_stats:
                team_stats[team_id] = {
                    "team_id": team_id,
                    "team_name": team_name,
                    "league_id": league_id,
                    "season": 2025,  # Current season for lookup
                    "matches_played": 0,
                    "wins": 0,
                    "draws": 0,
                    "losses": 0,
                    "goals_for": 0,
                    "goals_against": 0,
                    "peak_rating": 1500.0,
                    "peak_date": None,
                    "last_match_id": fixture["id"],
                    "last_match_date": match_date,
                    "last_rating_change": 0.0,
                }

            team_stats[team_id]["matches_played"] += 1
            team_stats[team_id]["goals_for"] += gf
            team_stats[team_id]["goals_against"] += ga
            team_stats[team_id]["last_match_id"] = fixture["id"]
            team_stats[team_id]["last_match_date"] = match_date

            if result == "W":
                team_stats[team_id]["wins"] += 1
            elif result == "D":
                team_stats[team_id]["draws"] += 1
            else:
                team_stats[team_id]["losses"] += 1

        matches_processed += 1

    # Prepare Elo data with final ratings
    elo_data_list = []
    for team_id, stats in team_stats.items():
        current_elo = round(elo.ratings.get(team_id, 1500.0), 2)
        stats["elo_rating"] = current_elo
        if current_elo > stats["peak_rating"]:
            stats["peak_rating"] = current_elo
        elo_data_list.append(stats)

    # Save to DB
    ratings_saved = 0
    if elo_data_list:
        ratings_saved = db_service.bulk_upsert_team_elos(elo_data_list)

    # Top 15 teams
    top_teams = sorted(elo_data_list, key=lambda x: x["elo_rating"], reverse=True)[:15]

    return {
        "matches_processed": matches_processed,
        "teams_updated": ratings_saved,
        "avg_matches_per_team": round(matches_processed * 2 / max(len(team_stats), 1), 1),
        "top_teams": [
            {"team": t["team_name"], "elo": t["elo_rating"], "matches": t["matches_played"]}
            for t in top_teams
        ],
    }


# ============================================================================
# DIXON-COLES MODEL ENDPOINTS
# ============================================================================


@router.post("/fit-dixon-coles")
def fit_dixon_coles(min_matches: int = 10, max_fixtures: int = 2000):
    """
    Fit the Dixon-Coles model using historical fixtures.

    This is the gold-standard model for football prediction based on:
    "Modelling Association Football Scores" (Dixon & Coles, 1997)

    Features:
    - Bivariate Poisson for correlated scores
    - Time-decay weighting (recent matches matter more)
    - Attack/Defense strength per team

    Args:
        min_matches: Minimum matches per team to be included (default 10)
        max_fixtures: Maximum fixtures to load (default 2000, increase for more accuracy)
    """
    try:
        # Get historical fixtures (limited for speed)
        fixtures = db_service.get_finished_fixtures(limit=max_fixtures)

        if not fixtures:
            raise HTTPException(status_code=404, detail="No historical fixtures found")

        # Fit the model
        dixon_coles_model.fit(fixtures, min_matches=min_matches)

        if not dixon_coles_model.is_fitted:
            raise HTTPException(status_code=500, detail="Model fitting failed")

        # Get team ratings
        ratings = dixon_coles_model.get_team_ratings()[:20]

        return {
            "status": "success",
            "message": f"Dixon-Coles model fitted with {len(fixtures)} fixtures",
            "model_params": {
                "home_advantage": round(dixon_coles_model.home_advantage, 4),
                "rho": round(dixon_coles_model.rho, 4),
                "teams": len(dixon_coles_model.attack_params),
            },
            "top_teams": ratings,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("fit_dixon_coles_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dixon-coles/predict/{fixture_id}")
def predict_with_dixon_coles(fixture_id: int):
    """
    Get Dixon-Coles prediction for a specific fixture.

    Returns comprehensive probability estimates:
    - Match winner (1X2)
    - Over/Under 2.5 and 3.5
    - BTTS
    - Expected goals
    - Most likely score
    """
    try:
        if not dixon_coles_model.is_fitted:
            raise HTTPException(
                status_code=400, detail="Model not fitted. Call POST /jobs/fit-dixon-coles first"
            )

        # Get fixture
        fixture = db_service.get_fixture_by_id(fixture_id)
        if not fixture:
            raise HTTPException(status_code=404, detail=f"Fixture {fixture_id} not found")

        # Get prediction
        prediction = dixon_coles_model.predict_match(
            home_team_id=fixture["home_team_id"],
            away_team_id=fixture["away_team_id"],
            league_id=fixture.get("league_id"),  # Pass league for competition adjustments
        )

        return {
            "fixture_id": fixture_id,
            "home_team": fixture["home_team_name"],
            "away_team": fixture["away_team_name"],
            "kickoff_time": fixture.get("kickoff_time"),
            "prediction": prediction,
            "model": "dixon_coles_v2",  # Updated version
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("dixon_coles_predict_error", fixture_id=fixture_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dixon-coles/team-ratings")
def get_dixon_coles_ratings(limit: int = 50):
    """
    Get team attack/defense ratings from Dixon-Coles model.

    Higher attack = more goals scored
    Lower (more negative) defense = fewer goals conceded
    Strength = attack - defense (overall team quality)
    """
    try:
        if not dixon_coles_model.is_fitted:
            raise HTTPException(
                status_code=400, detail="Model not fitted. Call POST /jobs/fit-dixon-coles first"
            )

        ratings = dixon_coles_model.get_team_ratings()[:limit]

        return {
            "status": "success",
            "model_params": {
                "home_advantage": round(dixon_coles_model.home_advantage, 4),
                "rho": round(dixon_coles_model.rho, 4),
            },
            "ratings": ratings,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("dixon_coles_ratings_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-results")
def sync_finished_fixtures(date_from: str = None, date_to: str = None):
    """
    Sync results from finished fixtures (status=FT) from API-Football.

    Updates fixtures in DB with final scores.

    Args:
        date_from: Start date (YYYY-MM-DD), defaults to 3 days ago
        date_to: End date (YYYY-MM-DD), defaults to today
    """
    try:
        # Default date range: 3 days ago to today
        if not date_from:
            date_from = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%d")
        if not date_to:
            date_to = datetime.utcnow().strftime("%Y-%m-%d")

        leagues = db_service.get_active_leagues()

        if not leagues:
            return {
                "status": "warning",
                "message": "No active leagues found",
                "fixtures_updated": 0,
            }

        client = api_football_client
        total_updated = 0
        results_data = []

        logger.info(
            "sync_results_started", leagues_count=len(leagues), date_from=date_from, date_to=date_to
        )

        for league in leagues:
            league_id = league["id"]
            season = league.get("season", 2025)

            try:
                # Fetch FINISHED fixtures from API
                api_fixtures = client.get_fixtures(
                    league_id=league_id,
                    season=season,
                    date_from=date_from,
                    date_to=date_to,
                    status="FT",  # Finished
                )

                if not api_fixtures:
                    continue

                # Transform and upsert fixtures with scores
                db_fixtures = [transform_fixture_to_db(f) for f in api_fixtures]
                count = db_service.upsert_fixtures(db_fixtures)
                total_updated += count

                # Collect results for return
                for f in db_fixtures:
                    results_data.append(
                        {
                            "fixture_id": f["id"],
                            "home_team": f["home_team_name"],
                            "away_team": f["away_team_name"],
                            "home_score": f["home_score"],
                            "away_score": f["away_score"],
                            "status": f["status"],
                        }
                    )

                logger.info(
                    "league_results_synced",
                    league_id=league_id,
                    league_name=league["name"],
                    fixtures_count=count,
                )

            except Exception as e:
                logger.error("league_results_sync_failed", league_id=league_id, error=str(e))
                continue

        return {
            "status": "success",
            "message": f"Updated {total_updated} fixtures with results",
            "fixtures_updated": total_updated,
            "date_range": {"from": date_from, "to": date_to},
            "results": results_data[:50],  # Limit output
        }

    except Exception as e:
        logger.error("sync_results_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-predictions")
def validate_predictions(date_from: str = None, date_to: str = None):
    """
    Validate predictions against actual results.

    Calculates accuracy, ROI, and Brier score for finished fixtures.
    """
    try:
        # Get finished fixtures
        query = db_service.client.table("fixtures").select("*").eq("status", "FT")

        if date_from:
            query = query.gte("kickoff_time", date_from)
        if date_to:
            query = query.lte("kickoff_time", date_to + "T23:59:59")

        result = query.order("kickoff_time", desc=True).limit(100).execute()
        finished_fixtures = result.data

        if not finished_fixtures:
            return {
                "status": "warning",
                "message": "No finished fixtures found. Run /jobs/sync-results first.",
                "total_fixtures": 0,
            }

        # Get predictions for these fixtures
        validation_results = []
        total_correct = 0
        total_predictions = 0
        total_brier = 0.0

        # Value bet tracking
        value_bet_results = []
        total_stake = 0.0
        total_return = 0.0

        for fixture in finished_fixtures:
            fixture_id = fixture["id"]
            home_score = fixture.get("home_score")
            away_score = fixture.get("away_score")

            if home_score is None or away_score is None:
                continue

            # Determine actual result
            if home_score > away_score:
                actual_result = "home_win"
            elif away_score > home_score:
                actual_result = "away_win"
            else:
                actual_result = "draw"

            actual_over_2_5 = (home_score + away_score) > 2.5
            actual_btts = home_score > 0 and away_score > 0

            # Get predictions for this fixture
            predictions = db_service.get_predictions(fixture_id=fixture_id)

            for pred in predictions:
                market = pred.get("market_key")
                prob = pred.get("prediction", {})

                if market == "match_winner":
                    # Check 1X2 prediction
                    pred_home = prob.get("home_win", 0)
                    pred_draw = prob.get("draw", 0)
                    pred_away = prob.get("away_win", 0)

                    # Predicted winner
                    if pred_home >= pred_draw and pred_home >= pred_away:
                        predicted = "home_win"
                        predicted_prob = pred_home
                    elif pred_away >= pred_draw:
                        predicted = "away_win"
                        predicted_prob = pred_away
                    else:
                        predicted = "draw"
                        predicted_prob = pred_draw

                    is_correct = predicted == actual_result
                    total_correct += 1 if is_correct else 0
                    total_predictions += 1

                    # Brier score component
                    actual_probs = [
                        1 if actual_result == "home_win" else 0,
                        1 if actual_result == "draw" else 0,
                        1 if actual_result == "away_win" else 0,
                    ]
                    pred_probs = [pred_home, pred_draw, pred_away]
                    brier = sum((p - a) ** 2 for p, a in zip(pred_probs, actual_probs)) / 3
                    total_brier += brier

                    validation_results.append(
                        {
                            "fixture_id": fixture_id,
                            "match": f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                            "score": f"{home_score}-{away_score}",
                            "market": market,
                            "predicted": predicted,
                            "predicted_prob": round(predicted_prob, 3),
                            "actual": actual_result,
                            "correct": is_correct,
                            "brier": round(brier, 4),
                        }
                    )

                    # Check if this was a value bet
                    odds = db_service.get_latest_odds(fixture_id)
                    for odd in odds:
                        if odd.get("market_key") == "match_winner":
                            odds_data = odd.get("odds_data", {})

                            # Map prediction to odds key
                            odds_map = {"home_win": "home", "draw": "draw", "away_win": "away"}
                            if predicted in odds_map:
                                market_odds = odds_data.get(odds_map[predicted], 0)
                                if market_odds > 0:
                                    implied_prob = 1 / market_odds
                                    edge = predicted_prob - implied_prob

                                    if edge > 0.05:  # 5% edge threshold
                                        stake = 10  # $10 unit bet
                                        total_stake += stake
                                        winnings = stake * market_odds if is_correct else 0
                                        total_return += winnings

                                        value_bet_results.append(
                                            {
                                                "match": f"{fixture['home_team_name']} vs {fixture['away_team_name']}",
                                                "selection": predicted,
                                                "odds": market_odds,
                                                "edge": round(edge * 100, 1),
                                                "result": "✅ WON" if is_correct else "❌ LOST",
                                                "profit": round(winnings - stake, 2),
                                            }
                                        )

        # Calculate metrics
        accuracy = (total_correct / total_predictions * 100) if total_predictions > 0 else 0
        avg_brier = (total_brier / total_predictions) if total_predictions > 0 else 0
        roi = ((total_return - total_stake) / total_stake * 100) if total_stake > 0 else 0

        return {
            "status": "success",
            "summary": {
                "total_fixtures_analyzed": len(finished_fixtures),
                "total_predictions": total_predictions,
                "correct_predictions": total_correct,
                "accuracy_pct": round(accuracy, 1),
                "brier_score": round(avg_brier, 4),
                "brier_interpretation": (
                    "Good" if avg_brier < 0.25 else "Fair" if avg_brier < 0.33 else "Poor"
                ),
            },
            "value_bets": {
                "total_bets": len(value_bet_results),
                "total_stake": total_stake,
                "total_return": round(total_return, 2),
                "profit_loss": round(total_return - total_stake, 2),
                "roi_pct": round(roi, 1),
                "results": value_bet_results,
            },
            "predictions": validation_results[:30],  # Limit output
        }

    except Exception as e:
        logger.error("validate_predictions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ====================
# Team Statistics Sync
# ====================


@router.post("/sync-team-stats")
def sync_team_stats(limit: int = Query(20, description="Max teams to sync per call")):
    """
    Sync team statistics from API-Football for upcoming match teams.

    Fetches:
    - Goals scored/conceded averages
    - Clean sheets
    - Cards (yellow/red)
    - Form

    Stores in team_statistics table.

    Uses ONLY teams from upcoming fixtures to minimize API calls.
    """
    try:
        client = api_football_client

        # Get unique teams from UPCOMING fixtures only
        fixtures = db_service.get_fixtures(status="NS", limit=100)
        team_data = set()  # (team_id, league_id) pairs
        for f in fixtures:
            team_data.add((f["home_team_id"], f.get("league_id", 39)))
            team_data.add((f["away_team_id"], f.get("league_id", 39)))

        logger.info("sync_team_stats_started", unique_teams=len(team_data), limit=limit)

        stats_synced = 0
        stats_failed = 0

        for team_id, league_id in list(team_data)[:limit]:
            try:
                logger.info("Fetching stats", team_id=team_id, league_id=league_id)

                stats = client.get_team_statistics(
                    team_id=team_id, league_id=league_id, season=2025
                )

                if stats:
                    # Extract key metrics
                    goals_for = stats.get("goals", {}).get("for", {})
                    goals_against = stats.get("goals", {}).get("against", {})
                    cards = stats.get("cards", {})
                    clean_sheets = stats.get("clean_sheet", {})

                    goals_scored_avg = None
                    goals_conceded_avg = None

                    if goals_for.get("average", {}).get("total"):
                        goals_scored_avg = float(goals_for["average"]["total"])
                    if goals_against.get("average", {}).get("total"):
                        goals_conceded_avg = float(goals_against["average"]["total"])

                    # Calculate yellow cards avg
                    yellow_total = 0
                    matches = stats.get("fixtures", {}).get("played", {}).get("total", 0)
                    for period, data in cards.get("yellow", {}).items():
                        if isinstance(data, dict) and data.get("total"):
                            yellow_total += data["total"]
                    yellow_avg = yellow_total / matches if matches > 0 else None

                    # Clean sheets
                    clean_sheets_total = clean_sheets.get("total") if clean_sheets else None

                    # Store in database
                    db_service.client.table("team_statistics").upsert(
                        {
                            "team_id": team_id,
                            "league_id": league_id,
                            "season": 2025,
                            "stats_data": stats,
                            "goals_scored_avg": goals_scored_avg,
                            "goals_conceded_avg": goals_conceded_avg,
                            "clean_sheets_total": clean_sheets_total,
                            "yellow_cards_avg": yellow_avg,
                            "updated_at": datetime.utcnow().isoformat(),
                        },
                        on_conflict="team_id,league_id,season",
                    ).execute()

                    stats_synced += 1
                    logger.info(
                        "synced_team",
                        team_id=team_id,
                        goals_avg=goals_scored_avg,
                        conceded=goals_conceded_avg,
                    )

            except Exception as e:
                stats_failed += 1
                logger.warning("team_stats_fetch_failed", team_id=team_id, error=str(e))

        return {
            "status": "success",
            "message": f"Synced statistics for {stats_synced} teams",
            "teams_synced": stats_synced,
            "teams_failed": stats_failed,
            "total_upcoming_teams": len(team_data),
        }

    except Exception as e:
        logger.error("sync_team_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ====================
# Multi-Market Predictions
# ====================

from app.ml.multi_market_predictor import TeamStats, multi_market_predictor


@router.get("/multi-market-prediction/{fixture_id}")
def get_multi_market_prediction(fixture_id: int):
    """
    Get predictions for ALL betting markets for a fixture.

    Returns:
    - Over/Under goals (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
    - BTTS (Both Teams To Score)
    - Team Goals Over/Under
    - Corners predictions
    - Cards predictions
    - Shots on Target predictions
    - Top 10 Exact Scores
    - Half-Time predictions
    """
    try:
        # Get fixture
        fixture = db_service.get_fixture_by_id(fixture_id)
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")

        home_team_id = fixture["home_team_id"]
        away_team_id = fixture["away_team_id"]
        league_id = fixture.get("league_id")

        # Try to get team statistics from DB
        try:
            home_stats_result = (
                db_service.client.table("team_statistics")
                .select("stats_data")
                .eq("team_id", home_team_id)
                .execute()
            )

            away_stats_result = (
                db_service.client.table("team_statistics")
                .select("stats_data")
                .eq("team_id", away_team_id)
                .execute()
            )

            if home_stats_result.data:
                multi_market_predictor.set_team_stats(
                    home_team_id, TeamStats(home_stats_result.data[0].get("stats_data"))
                )

            if away_stats_result.data:
                multi_market_predictor.set_team_stats(
                    away_team_id, TeamStats(away_stats_result.data[0].get("stats_data"))
                )
        except Exception as e:
            logger.warning("Failed to load team stats", error=str(e))

        # Get Dixon-Coles xG if available
        home_xg = None
        away_xg = None

        if dixon_coles_model.is_fitted:
            dc_pred = dixon_coles_model.predict_match(
                home_team_id, away_team_id, league_id=league_id
            )
            home_xg = dc_pred["expected_goals"]["home"]
            away_xg = dc_pred["expected_goals"]["away"]

        # Check if cup competition
        is_cup = league_id in {2, 3, 848, 48, 81, 137, 143, 66}  # UCL, UEL, UECL + National cups

        # Get all market predictions
        predictions = multi_market_predictor.predict_all_markets(
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            home_xg=home_xg,
            away_xg=away_xg,
            is_cup=is_cup,
            league_id=league_id,
        )

        return {
            "fixture_id": fixture_id,
            "home_team": fixture["home_team_name"],
            "away_team": fixture["away_team_name"],
            "kickoff_time": fixture.get("kickoff_time"),
            "league_id": league_id,
            "is_cup": is_cup,
            "predictions": predictions,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("multi_market_prediction_error", fixture_id=fixture_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# LEAGUE-SPECIFIC TEAM STATISTICS SYNC
# =============================================================================


@router.post("/sync-league-stats/{league_id}")
def sync_league_team_statistics(
    league_id: int, season: int = Query(2025, description="Season (e.g., 2025)")
):
    """
    Sync team statistics from API-Football for a specific league.

    This populates:
    - goals_scored_avg, goals_conceded_avg
    - clean_sheets, cards
    - Full stats_data JSONB for advanced analysis
    """
    try:
        client = api_football_client
        logger.info("Syncing team statistics", league_id=league_id, season=season)

        # Get all teams in the league from fixtures
        fixtures = db_service.get_fixtures(league_id=league_id, limit=500)

        team_ids = set()
        for f in fixtures:
            team_ids.add(f["home_team_id"])
            team_ids.add(f["away_team_id"])

        synced = 0
        failed = 0

        for team_id in list(team_ids)[:30]:  # Limit to 30 teams per call
            try:
                # Get stats from API-Football
                stats = client.get_team_statistics(
                    team_id=team_id, league_id=league_id, season=season
                )

                if stats:
                    # Extract key metrics
                    goals_for = stats.get("goals", {}).get("for", {})
                    goals_against = stats.get("goals", {}).get("against", {})
                    cards = stats.get("cards", {})
                    clean_sheets = stats.get("clean_sheet", {})

                    goals_scored_avg = None
                    goals_conceded_avg = None

                    if goals_for.get("average", {}).get("total"):
                        goals_scored_avg = float(goals_for["average"]["total"])
                    if goals_against.get("average", {}).get("total"):
                        goals_conceded_avg = float(goals_against["average"]["total"])

                    # Calculate yellow cards avg
                    yellow_total = 0
                    matches = stats.get("fixtures", {}).get("played", {}).get("total", 0)
                    for period, data in cards.get("yellow", {}).items():
                        if isinstance(data, dict) and data.get("total"):
                            yellow_total += data["total"]
                    yellow_avg = yellow_total / matches if matches > 0 else None

                    # Clean sheets
                    clean_sheets_total = clean_sheets.get("total") if clean_sheets else None

                    # Upsert to database
                    db_service.client.table("team_statistics").upsert(
                        {
                            "team_id": team_id,
                            "league_id": league_id,
                            "season": season,
                            "stats_data": stats,
                            "goals_scored_avg": goals_scored_avg,
                            "goals_conceded_avg": goals_conceded_avg,
                            "clean_sheets_total": clean_sheets_total,
                            "yellow_cards_avg": yellow_avg,
                            "updated_at": datetime.utcnow().isoformat(),
                        },
                        on_conflict="team_id,league_id,season",
                    ).execute()

                    synced += 1
                    logger.info(
                        "Synced team stats",
                        team_id=team_id,
                        goals_avg=goals_scored_avg,
                        conceded_avg=goals_conceded_avg,
                    )

            except Exception as e:
                failed += 1
                logger.warning("Failed to sync team stats", team_id=team_id, error=str(e))

        return {
            "status": "success",
            "league_id": league_id,
            "season": season,
            "teams_synced": synced,
            "teams_failed": failed,
            "total_teams": len(team_ids),
        }

    except Exception as e:
        logger.error("sync_team_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-player-stats/{team_id}")
def sync_player_statistics(
    team_id: int,
    league_id: int = Query(..., description="League ID"),
    season: int = Query(2025, description="Season"),
):
    """
    Sync player statistics for a specific team.

    Gets top scorers, shooters, and card holders for player props.
    """
    try:
        client = api_football_client
        logger.info("Syncing player statistics", team_id=team_id, league_id=league_id)

        # Get players from API-Football
        players = client.get_team_players(team_id=team_id, season=season)

        synced = 0

        for player in players:
            try:
                player_id = player.get("id")
                player_name = player.get("name", "Unknown")
                stats = player.get("statistics", [{}])[0]

                games = stats.get("games", {})
                goals_data = stats.get("goals", {})
                shots = stats.get("shots", {})
                cards_data = stats.get("cards", {})

                minutes = games.get("minutes") or 0
                games_played = games.get("appearences") or 0

                goals = goals_data.get("total") or 0
                assists = goals_data.get("assists") or 0

                total_shots = shots.get("total") or 0
                shots_on_target = shots.get("on") or 0

                yellow_cards = cards_data.get("yellow") or 0
                red_cards = cards_data.get("red") or 0

                # Calculate per 90 stats
                minutes_90 = minutes / 90 if minutes > 0 else 0
                goals_per_90 = goals / minutes_90 if minutes_90 > 0 else 0
                shots_per_90 = total_shots / minutes_90 if minutes_90 > 0 else 0
                sot_per_90 = shots_on_target / minutes_90 if minutes_90 > 0 else 0

                # Upsert to database
                db_service.client.table("player_statistics").upsert(
                    {
                        "player_id": player_id,
                        "player_name": player_name,
                        "team_id": team_id,
                        "league_id": league_id,
                        "season": season,
                        "goals": goals,
                        "assists": assists,
                        "goals_per_90": round(goals_per_90, 2),
                        "total_shots": total_shots,
                        "shots_on_target": shots_on_target,
                        "shots_per_90": round(shots_per_90, 2),
                        "shots_on_target_per_90": round(sot_per_90, 2),
                        "yellow_cards": yellow_cards,
                        "red_cards": red_cards,
                        "games_played": games_played,
                        "minutes_played": minutes,
                        "stats_data": player,
                        "updated_at": datetime.utcnow().isoformat(),
                    },
                    on_conflict="player_id,league_id,season",
                ).execute()

                synced += 1

            except Exception as e:
                logger.warning("Failed to sync player", player_id=player.get("id"), error=str(e))

        return {
            "status": "success",
            "team_id": team_id,
            "league_id": league_id,
            "players_synced": synced,
        }

    except Exception as e:
        logger.error("sync_player_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-player-stats")
def sync_all_player_statistics(
    limit: int = Query(10, description="Number of teams to sync players for"),
    season: int = Query(2025, description="Season"),
):
    """
    Sync player statistics for teams from upcoming fixtures.

    Gets player stats (goals, shots, cards) for player props markets.
    """
    try:
        import time

        client = api_football_client

        # Get unique team IDs from upcoming fixtures
        fixtures = (
            db_service.client.table("fixtures")
            .select("home_team_id, away_team_id, league_id")
            .eq("status", "NS")
            .execute()
        )

        # Build team -> league mapping
        team_leagues = {}
        for f in fixtures.data:
            team_leagues[f["home_team_id"]] = f["league_id"]
            team_leagues[f["away_team_id"]] = f["league_id"]

        team_ids = list(team_leagues.keys())[:limit]

        logger.info("Syncing player stats", teams_count=len(team_ids))

        synced_teams = 0
        synced_players = 0
        failed_teams = 0

        for team_id in team_ids:
            try:
                league_id = team_leagues[team_id]

                # Get players from API-Football
                players = client.get_team_players(team_id=team_id, season=season)

                for player in players:
                    try:
                        player_id = player.get("id")
                        player_name = player.get("name", "Unknown")
                        stats = player.get("statistics", [{}])[0]

                        games = stats.get("games", {})
                        goals_data = stats.get("goals", {})
                        shots = stats.get("shots", {})
                        cards_data = stats.get("cards", {})

                        minutes = games.get("minutes") or 0
                        games_played = games.get("appearences") or 0

                        goals = goals_data.get("total") or 0
                        assists = goals_data.get("assists") or 0

                        total_shots = shots.get("total") or 0
                        shots_on_target = shots.get("on") or 0

                        yellow_cards = cards_data.get("yellow") or 0
                        red_cards = cards_data.get("red") or 0

                        # Calculate per 90 stats
                        minutes_90 = minutes / 90 if minutes > 0 else 0
                        goals_per_90 = goals / minutes_90 if minutes_90 > 0 else 0
                        shots_per_90 = total_shots / minutes_90 if minutes_90 > 0 else 0
                        sot_per_90 = shots_on_target / minutes_90 if minutes_90 > 0 else 0

                        # Upsert to database
                        db_service.client.table("player_statistics").upsert(
                            {
                                "player_id": player_id,
                                "player_name": player_name,
                                "team_id": team_id,
                                "league_id": league_id,
                                "season": season,
                                "goals": goals,
                                "assists": assists,
                                "goals_per_90": round(goals_per_90, 2),
                                "total_shots": total_shots,
                                "shots_on_target": shots_on_target,
                                "shots_per_90": round(shots_per_90, 2),
                                "shots_on_target_per_90": round(sot_per_90, 2),
                                "yellow_cards": yellow_cards,
                                "red_cards": red_cards,
                                "games_played": games_played,
                                "minutes_played": minutes,
                                "stats_data": player,
                                "updated_at": datetime.utcnow().isoformat(),
                            },
                            on_conflict="player_id,league_id,season",
                        ).execute()

                        synced_players += 1

                    except Exception as e:
                        logger.warning(
                            "Failed to sync player", player_id=player.get("id"), error=str(e)
                        )

                synced_teams += 1
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.warning("Failed to sync team players", team_id=team_id, error=str(e))
                failed_teams += 1

        return {
            "status": "success",
            "message": f"Synced {synced_players} players from {synced_teams} teams",
            "teams_synced": synced_teams,
            "teams_failed": failed_teams,
            "players_synced": synced_players,
            "total_upcoming_teams": len(team_leagues),
        }

    except Exception as e:
        logger.error("sync_all_player_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync-all-league-stats")
def sync_all_statistics(
    leagues: str = Query("2,3", description="Comma-separated league IDs"),
    season: int = Query(2025, description="Season"),
):
    """
    Sync team statistics for multiple leagues.

    Default leagues: UCL(2), UEL(3)
    """
    try:
        league_ids = [int(l.strip()) for l in leagues.split(",")]

        results = []
        total_synced = 0

        for league_id in league_ids:
            try:
                result = sync_league_team_statistics(league_id=league_id, season=season)
                results.append(result)
                total_synced += result.get("teams_synced", 0)
            except Exception as e:
                results.append({"league_id": league_id, "status": "failed", "error": str(e)})

        return {
            "status": "success",
            "total_teams_synced": total_synced,
            "leagues_processed": len(league_ids),
            "results": results,
        }

    except Exception as e:
        logger.error("sync_all_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-scorers")
def get_top_scorers(
    limit: int = Query(20, description="Number of players to return"),
    min_goals: int = Query(3, description="Minimum goals"),
):
    """
    Get top scorers from synced player statistics.
    """
    try:
        result = (
            db_service.client.table("player_statistics")
            .select(
                "player_name, team_id, goals, assists, total_shots, shots_on_target, goals_per_90, games_played, minutes_played"
            )
            .gte("goals", min_goals)
            .order("goals", desc=True)
            .limit(limit)
            .execute()
        )

        return {"status": "success", "count": len(result.data), "players": result.data}

    except Exception as e:
        logger.error("get_top_scorers_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/top-shooters")
def get_top_shooters(
    limit: int = Query(20, description="Number of players to return"),
    min_shots: int = Query(20, description="Minimum total shots"),
):
    """
    Get players with most shots on target.
    """
    try:
        result = (
            db_service.client.table("player_statistics")
            .select(
                "player_name, team_id, total_shots, shots_on_target, shots_per_90, shots_on_target_per_90, goals, games_played"
            )
            .gte("total_shots", min_shots)
            .order("shots_on_target", desc=True)
            .limit(limit)
            .execute()
        )

        return {"status": "success", "count": len(result.data), "players": result.data}

    except Exception as e:
        logger.error("get_top_shooters_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BACKGROUND SCHEDULER MANUAL TRIGGERS
# ============================================================================


@router.post("/trigger-load-fixtures")
def trigger_load_fixtures():
    """
    Trigger manual load of upcoming fixtures using existing sync-fixtures endpoint.
    """
    try:
        logger.info("manual_load_fixtures_triggered")

        # Reusar el endpoint que ya funciona
        response = sync_fixtures()

        return {"status": "success", "message": "Fixtures loaded successfully", "result": response}
    except Exception as e:
        logger.error("manual_load_fixtures_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger-generate-predictions")
def trigger_generate_predictions():
    """
    Trigger manual generation of predictions using existing run-predictions endpoint.
    """
    try:
        logger.info("manual_generate_predictions_triggered")

        # Reusar el endpoint que ya funciona
        response = run_predictions()

        return {
            "status": "success",
            "message": "Predictions generated successfully",
            "result": response,
        }
    except Exception as e:
        logger.error("manual_generate_predictions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/scheduler-status")
async def get_scheduler_status():
    """
    Get status of background scheduler and next run times.
    """
    try:
        from app.scheduler_v2 import scheduler

        if scheduler is None:
            return {"status": "not_running", "jobs": []}

        jobs_info = [
            {
                "id": job.id,
                "name": job.name,
                "next_run": str(job.next_run_time) if job.next_run_time else None,
                "pending": job.pending,
            }
            for job in scheduler.get_jobs()
        ]

        return {"status": "running", "jobs": jobs_info}
    except Exception as e:
        logger.error("scheduler_status_error", error=str(e))
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error("scheduler_status_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
