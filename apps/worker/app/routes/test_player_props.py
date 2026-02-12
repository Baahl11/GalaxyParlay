"""Test player props endpoint"""

from fastapi import APIRouter

from app.ml.multi_market_predictor import multi_market_predictor
from app.services.database import db_service

router = APIRouter()


@router.get("/test/player-props-debug")
async def test_player_props_debug():
    """Test player props with debug info"""
    
    # Test parameters
    home_team_id = 52  # Crystal Palace
    away_team_id = 44  # Burnley
    home_xg = 1.5
    away_xg = 1.2
    
    # Test query directly first
    direct_query = (
        db_service.client.table("player_statistics")
        .select("player_name, goals, team_id")
        .eq("team_id", home_team_id)
        .limit(5)
        .execute()
    )
    
    # Call the actual method
    result = multi_market_predictor._predict_player_props(
        home_team_id, away_team_id, home_xg, away_xg
    )
    
    return {
        "status": "debug",
        "direct_query_count": len(direct_query.data) if direct_query.data else 0,
        "direct_query_players": [p["player_name"] for p in (direct_query.data or [])[:3]],
        "method_result_home_count": len(result.get("home_players", [])),
        "method_result_away_count": len(result.get("away_players", [])),
        "method_result_home_players": [p.get("player_name") for p in result.get("home_players", [])[:3]],
        "method_result_away_players": [p.get("player_name") for p in result.get("away_players", [])[:3]],
        "full_result": result,
    }
