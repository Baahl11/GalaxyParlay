"""
Galaxy API - Public endpoints for frontend
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

from app.services.database import db_service
from app.ml.value_bets import value_detector, ValueBet

router = APIRouter(prefix="/api", tags=["galaxy-api"])
logger = structlog.get_logger()


@router.get("/fixtures")
async def get_fixtures(
    league_id: Optional[int] = Query(None, description="Filter by league ID"),
    status: Optional[str] = Query("NS", description="Match status (NS, LIVE, FT)"),
    limit: int = Query(50, le=100, description="Max results")
):
    """
    Get fixtures with optional filters
    
    Returns fixtures with their predictions and quality scores
    """
    try:
        fixtures = db_service.get_fixtures(
            league_id=league_id,
            status=status,
            limit=limit
        )
        
        # Enrich with predictions and quality scores
        enriched_fixtures = []
        for fixture in fixtures:
            fixture_id = fixture["id"]
            
            # Get predictions
            predictions = db_service.get_predictions(fixture_id=fixture_id)
            
            # Get quality scores  
            quality_query = db_service.client.table("quality_scores")\
                .select("*")\
                .eq("fixture_id", fixture_id)\
                .execute()
            quality_scores = quality_query.data
            
            # Get latest odds
            odds = db_service.get_latest_odds(fixture_id)
            
            enriched_fixtures.append({
                **fixture,
                "predictions": predictions,
                "quality_scores": quality_scores,
                "odds": odds
            })
        
        return {
            "data": enriched_fixtures,
            "count": len(enriched_fixtures),
            "filters": {
                "league_id": league_id,
                "status": status,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error("get_fixtures_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fixtures/{fixture_id}")
async def get_fixture_detail(fixture_id: int):
    """
    Get detailed fixture information with all predictions and odds
    """
    try:
        # Get fixture
        fixture = db_service.get_fixture_by_id(fixture_id)
        if not fixture:
            raise HTTPException(status_code=404, detail="Fixture not found")
        
        # Get predictions
        predictions = db_service.get_predictions(fixture_id=fixture_id)
        
        # Get quality scores
        quality_query = db_service.client.table("quality_scores")\
            .select("*")\
            .eq("fixture_id", fixture_id)\
            .execute()
        quality_scores = quality_query.data
        
        # Get all odds history
        odds_query = db_service.client.table("odds_snapshots")\
            .select("*")\
            .eq("fixture_id", fixture_id)\
            .order("snapshot_at", desc=True)\
            .limit(50)\
            .execute()
        odds_history = odds_query.data
        
        return {
            "fixture": fixture,
            "predictions": predictions,
            "quality_scores": quality_scores,
            "odds_history": odds_history
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_fixture_detail_error", fixture_id=fixture_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/predictions")
async def get_predictions(
    quality_grade: Optional[str] = Query(None, description="Filter by grade (A, B, C)"),
    min_confidence: Optional[float] = Query(None, ge=0.0, le=1.0, description="Min confidence score"),
    limit: int = Query(50, le=100, description="Max results")
):
    """
    Get top predictions across all fixtures
    
    Useful for displaying "Today's Best Picks"
    """
    try:
        predictions = db_service.get_predictions(
            quality_grade=quality_grade,
            limit=limit
        )
        
        # Filter by confidence if specified
        if min_confidence is not None:
            predictions = [
                p for p in predictions
                if p.get("confidence_score", 0) >= min_confidence
            ]
        
        # Enrich with fixture data
        enriched_predictions = []
        for pred in predictions:
            fixture = db_service.get_fixture_by_id(pred["fixture_id"])
            if fixture:
                enriched_predictions.append({
                    **pred,
                    "fixture": fixture
                })
        
        return {
            "data": enriched_predictions,
            "count": len(enriched_predictions),
            "filters": {
                "quality_grade": quality_grade,
                "min_confidence": min_confidence,
                "limit": limit
            }
        }
        
    except Exception as e:
        logger.error("get_predictions_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/leagues")
async def get_leagues():
    """Get all active leagues"""
    try:
        leagues = db_service.get_active_leagues()
        return {
            "data": leagues,
            "count": len(leagues)
        }
    except Exception as e:
        logger.error("get_leagues_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_stats():
    """
    Get platform statistics
    
    Useful for dashboard/landing page
    """
    try:
        # Get all fixtures
        all_fixtures = db_service.get_fixtures(limit=1000)
        
        # Get all predictions
        all_predictions = db_service.get_predictions(limit=1000)
        
        # Calculate stats
        upcoming_count = len([f for f in all_fixtures if f["status"] == "NS"])
        live_count = len([f for f in all_fixtures if f["status"] in ["1H", "2H", "HT"]])
        
        grade_a_count = len([p for p in all_predictions if p["quality_grade"] == "A"])
        high_confidence_count = len([
            p for p in all_predictions 
            if p.get("confidence_score", 0) >= 0.75
        ])
        
        return {
            "fixtures": {
                "total": len(all_fixtures),
                "upcoming": upcoming_count,
                "live": live_count
            },
            "predictions": {
                "total": len(all_predictions),
                "grade_a": grade_a_count,
                "high_confidence": high_confidence_count
            },
            "leagues": {
                "active": len(db_service.get_active_leagues())
            }
        }
        
    except Exception as e:
        logger.error("get_stats_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/value-bets")
async def get_value_bets(
    min_edge: Optional[float] = Query(0.03, ge=0.0, le=0.5, description="Minimum edge (e.g., 0.05 = 5%)"),
    min_ev: Optional[float] = Query(0.02, ge=0.0, le=0.5, description="Minimum expected value"),
    min_confidence: Optional[float] = Query(0.40, ge=0.0, le=1.0, description="Minimum model confidence"),
    quality_grade: Optional[str] = Query(None, description="Filter by quality grade (A, B, C, D)"),
    league_id: Optional[int] = Query(None, description="Filter by league"),
    limit: int = Query(20, le=50, description="Max results")
):
    """
    Get value betting opportunities
    
    Returns fixtures where model probability > bookmaker implied probability,
    sorted by value score (combination of edge, EV, and confidence).
    
    A value bet exists when:
    - Edge >= min_edge (model prob - implied prob)
    - Expected Value >= min_ev
    - Model confidence >= min_confidence
    """
    try:
        # Get all upcoming fixtures with predictions and odds
        fixtures = db_service.get_fixtures(status="NS", limit=500)
        
        # Enrich with predictions, quality scores, and odds
        enriched_fixtures = []
        for fixture in fixtures:
            # Apply league filter early
            if league_id and fixture.get("league_id") != league_id:
                continue
                
            fixture_id = fixture["id"]
            
            predictions = db_service.get_predictions(fixture_id=fixture_id)
            
            quality_query = db_service.client.table("quality_scores")\
                .select("*")\
                .eq("fixture_id", fixture_id)\
                .execute()
            quality_scores = quality_query.data
            
            odds = db_service.get_latest_odds(fixture_id)
            
            # Only include if we have both predictions and odds
            if predictions and odds:
                enriched_fixtures.append({
                    **fixture,
                    "predictions": predictions,
                    "quality_scores": quality_scores,
                    "odds": odds
                })
        
        # Configure detector with request parameters
        detector = value_detector
        detector.min_edge = min_edge
        detector.min_ev = min_ev
        detector.min_confidence = min_confidence
        
        # Detect value bets
        value_bets = detector.detect_value_bets(enriched_fixtures)
        
        # Apply quality grade filter
        if quality_grade:
            value_bets = [vb for vb in value_bets if vb.quality_grade == quality_grade]
        
        # Limit results
        value_bets = value_bets[:limit]
        
        # Convert to dict for JSON response
        return {
            "data": [vb.to_dict() for vb in value_bets],
            "count": len(value_bets),
            "filters": {
                "min_edge": min_edge,
                "min_ev": min_ev,
                "min_confidence": min_confidence,
                "quality_grade": quality_grade,
                "league_id": league_id,
                "limit": limit
            },
            "summary": {
                "fixtures_analyzed": len(enriched_fixtures),
                "value_bets_found": len(value_bets),
                "avg_edge": round(sum(vb.edge for vb in value_bets) / len(value_bets), 4) if value_bets else 0,
                "avg_ev": round(sum(vb.expected_value for vb in value_bets) / len(value_bets), 4) if value_bets else 0
            }
        }
        
    except Exception as e:
        logger.error("get_value_bets_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-stats/{team_id}")
async def get_team_stats(team_id: int):
    """
    Get comprehensive stats for a team based on Elo data and historical fixtures.
    
    Returns Elo rating and basic match statistics.
    """
    try:
        # Get Elo rating from DB (fast)
        elo_data = db_service.get_team_elo(team_id)
        
        if not elo_data:
            raise HTTPException(status_code=404, detail=f"No stats found for team {team_id}")
        
        # Calculate derived stats from Elo data
        matches = elo_data.get("matches_played", 0)
        wins = elo_data.get("wins", 0)
        draws = elo_data.get("draws", 0)
        losses = elo_data.get("losses", 0)
        goals_for = elo_data.get("goals_for", 0)
        goals_against = elo_data.get("goals_against", 0)
        
        return {
            "team_id": team_id,
            "team_name": elo_data.get("team_name", "Unknown"),
            "league_id": elo_data.get("league_id"),
            "elo": {
                "rating": elo_data.get("elo_rating", 1500),
                "peak_rating": elo_data.get("peak_rating", 1500),
                "peak_date": elo_data.get("peak_date"),
                "last_change": elo_data.get("last_rating_change", 0)
            },
            "stats": {
                "matches_played": matches,
                "wins": wins,
                "draws": draws,
                "losses": losses,
                "win_rate": round(wins / matches, 3) if matches > 0 else 0,
                "draw_rate": round(draws / matches, 3) if matches > 0 else 0,
                "loss_rate": round(losses / matches, 3) if matches > 0 else 0,
                "goals_for": goals_for,
                "goals_against": goals_against,
                "goal_diff": goals_for - goals_against,
                "goals_per_game": round(goals_for / matches, 2) if matches > 0 else 0,
                "goals_conceded_per_game": round(goals_against / matches, 2) if matches > 0 else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_team_stats_error", team_id=team_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# UNIFIED MATCH ANALYSIS - Combines all models + AI
# ============================================================

from app.ml.dixon_coles import dixon_coles_model
from app.ml.kelly import kelly_calculator
from app.ml.ai_analysis import generate_match_analysis, generate_daily_summary


@router.get("/match-analysis/{fixture_id}")
async def get_match_analysis(
    fixture_id: int,
    include_ai: bool = Query(True, description="Include AI narrative analysis"),
    language: str = Query("es", description="Language for AI analysis (es/en)")
):
    """
    Get comprehensive match analysis combining all prediction models.
    
    Returns:
    - Elo ratings comparison
    - Dixon-Coles predictions (1X2, O/U, BTTS, expected goals)
    - Value bets detected
    - Kelly Criterion bet sizing
    - AI-generated narrative analysis (optional)
    """
    try:
        # 1. Get fixture
        fixture = db_service.get_fixture_by_id(fixture_id)
        if not fixture:
            raise HTTPException(status_code=404, detail=f"Fixture {fixture_id} not found")
        
        home_team_id = fixture['home_team_id']
        away_team_id = fixture['away_team_id']
        
        # 2. Get Elo ratings
        elo_data = None
        try:
            home_elo_result = db_service.client.table("team_elo_ratings")\
                .select("*").eq("team_id", home_team_id).execute()
            away_elo_result = db_service.client.table("team_elo_ratings")\
                .select("*").eq("team_id", away_team_id).execute()
            
            if home_elo_result.data and away_elo_result.data:
                elo_data = {
                    "home_elo": home_elo_result.data[0].get('elo_rating', 1500),
                    "away_elo": away_elo_result.data[0].get('elo_rating', 1500),
                    "home_form": home_elo_result.data[0].get('form', 'N/A'),
                    "away_form": away_elo_result.data[0].get('form', 'N/A')
                }
        except Exception as e:
            logger.warning("Failed to get Elo data", error=str(e))
        
        # 3. Get Dixon-Coles prediction
        dixon_coles_pred = None
        if dixon_coles_model.is_fitted:
            try:
                prediction = dixon_coles_model.predict_match(
                    home_team_id=home_team_id,
                    away_team_id=away_team_id,
                    league_id=fixture.get('league_id')  # Pass league for competition adjustments
                )
                dixon_coles_pred = {"prediction": prediction}
            except Exception as e:
                logger.warning("Dixon-Coles prediction failed", error=str(e))
        
        # 4. Get odds and calculate value bets
        odds = db_service.get_latest_odds(fixture_id)
        value_bets = []
        kelly_results = {}
        
        if odds and dixon_coles_pred:
            # Extract odds data
            match_odds = {}
            for odd in odds:
                market = odd.get('market_key', '')
                data = odd.get('odds_data', {})
                if market == 'match_winner':
                    match_odds = {
                        'home': data.get('home', 0),
                        'draw': data.get('draw', 0),
                        'away': data.get('away', 0)
                    }
                elif market == 'over_under_2.5':
                    match_odds['over'] = data.get('over', 0)
                    match_odds['under'] = data.get('under', 0)
                elif market == 'both_teams_score':
                    match_odds['yes'] = data.get('yes', 0)
                    match_odds['no'] = data.get('no', 0)
            
            # Calculate value bets
            pred = dixon_coles_pred['prediction']
            
            # Check each market
            if match_odds.get('home') and pred.get('match_winner'):
                mw = pred['match_winner']
                
                # Home win
                implied = 1 / match_odds['home'] if match_odds['home'] > 1 else 0
                edge = mw['home_win'] - implied
                if edge > 0.02:
                    value_bets.append({
                        'market': 'Ganador Local',
                        'selection': fixture['home_team_name'],
                        'odds': match_odds['home'],
                        'model_prob': round(mw['home_win'], 3),
                        'implied_prob': round(implied, 3),
                        'edge': round(edge, 3),
                        'ev': round(edge * match_odds['home'], 3)
                    })
                
                # Away win
                implied = 1 / match_odds['away'] if match_odds['away'] > 1 else 0
                edge = mw['away_win'] - implied
                if edge > 0.02:
                    value_bets.append({
                        'market': 'Ganador Visitante',
                        'selection': fixture['away_team_name'],
                        'odds': match_odds['away'],
                        'model_prob': round(mw['away_win'], 3),
                        'implied_prob': round(implied, 3),
                        'edge': round(edge, 3),
                        'ev': round(edge * match_odds['away'], 3)
                    })
            
            # Over 2.5
            if match_odds.get('over') and pred.get('over_under_2_5'):
                ou = pred['over_under_2_5']
                implied = 1 / match_odds['over'] if match_odds['over'] > 1 else 0
                edge = ou['over'] - implied
                if edge > 0.02:
                    value_bets.append({
                        'market': 'Over 2.5',
                        'selection': 'Más de 2.5 goles',
                        'odds': match_odds['over'],
                        'model_prob': round(ou['over'], 3),
                        'implied_prob': round(implied, 3),
                        'edge': round(edge, 3),
                        'ev': round(edge * match_odds['over'], 3)
                    })
            
            # Sort by edge
            value_bets.sort(key=lambda x: x['edge'], reverse=True)
            
            # 5. Calculate Kelly for value bets
            for vb in value_bets:
                kelly = kelly_calculator.calculate(
                    model_probability=vb['model_prob'],
                    decimal_odds=vb['odds'],
                    confidence_score=0.7
                )
                kelly_results[vb['market']] = {
                    'kelly_fraction': kelly.kelly_fraction,
                    'half_kelly': kelly.half_kelly,
                    'recommendation': kelly.recommendation
                }
        
        # 6. Generate AI analysis
        ai_analysis = None
        if include_ai:
            ai_analysis = await generate_match_analysis(
                fixture=fixture,
                elo_data=elo_data,
                dixon_coles=dixon_coles_pred,
                value_bets=value_bets,
                kelly_results=None,  # Pass kelly as dict
                language=language
            )
        
        return {
            "fixture_id": fixture_id,
            "home_team": fixture['home_team_name'],
            "away_team": fixture['away_team_name'],
            "kickoff_time": fixture.get('kickoff_time'),
            "league_id": fixture.get('league_id'),
            "venue": fixture.get('venue'),
            
            "elo": elo_data,
            "dixon_coles": dixon_coles_pred,
            "value_bets": value_bets,
            "kelly": kelly_results,
            "ai_analysis": ai_analysis,
            
            "models_used": [
                "elo_v1" if elo_data else None,
                "dixon_coles_v1" if dixon_coles_pred else None,
                "kelly_criterion" if kelly_results else None
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("match_analysis_error", fixture_id=fixture_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/daily-analysis")
async def get_daily_analysis(
    include_ai: bool = Query(False, description="Include AI analysis for each match (slower, ~$0.02)"),
    include_ai_summary: bool = Query(True, description="Include AI daily summary"),
    language: str = Query("es", description="Language (es/en)")
):
    """
    Get analysis for all matches today.
    
    Returns comprehensive analysis for each fixture plus
    an AI-generated daily summary with top picks.
    
    Use include_ai=true to get individual AI analysis per match (costs ~$0.0004 each).
    """
    try:
        # Get upcoming fixtures
        fixtures = db_service.get_fixtures(status="NS", limit=50)
        
        if not fixtures:
            return {
                "date": datetime.utcnow().date().isoformat(),
                "total_matches": 0,
                "matches": [],
                "daily_summary": "No hay partidos programados para hoy."
            }
        
        # Analyze each fixture
        matches = []
        for fixture in fixtures:
            try:
                # Get analysis with optional AI for each match
                analysis = await get_match_analysis(
                    fixture_id=fixture['id'],
                    include_ai=include_ai,
                    language=language
                )
                matches.append(analysis)
            except Exception as e:
                logger.warning("Failed to analyze fixture", 
                            fixture_id=fixture['id'], error=str(e))
        
        # Generate daily summary
        daily_summary = None
        if include_ai_summary:
            daily_summary = await generate_daily_summary(matches, language)
        
        # Calculate stats
        total_value_bets = sum(len(m.get('value_bets', [])) for m in matches)
        
        return {
            "date": datetime.utcnow().date().isoformat(),
            "total_matches": len(matches),
            "total_value_bets": total_value_bets,
            "matches": matches,
            "daily_summary": daily_summary,
            "top_picks": sorted(
                [vb for m in matches for vb in m.get('value_bets', [])],
                key=lambda x: x.get('edge', 0),
                reverse=True
            )[:5]
        }
        
    except Exception as e:
        logger.error("daily_analysis_error", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
