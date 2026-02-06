"""
Fixture Loader Service
Carga fixtures desde API-Football de manera eficiente.
"""

import asyncio
from datetime import datetime, timedelta
from time import time
from typing import Any, Dict, List

import httpx
import structlog

from app.config import settings
from app.core.database import get_supabase_client

logger = structlog.get_logger(__name__)

# Ligas activas que queremos monitorear
ACTIVE_LEAGUES = {
    # Europa Primera División
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    94: "Primeira Liga",
    88: "Eredivisie",
    203: "Süper Lig",
    144: "Jupiler Pro League",
    235: "Russian Premier League",
    # Europa Segunda División
    40: "Championship",
    141: "LaLiga 2",
    136: "Serie B",
    79: "2. Bundesliga",
    62: "Ligue 2",
    # LATAM
    262: "Liga MX",
    274: "Primera División Chile",
    273: "Primera División Uruguay",
    271: "Primera División Venezuela",
    71: "Brasileirão",
    128: "Liga Argentina",
    253: "MLS",
    # Asia
    307: "Saudi Pro League",
    188: "J1 League",
    # Copas Internacionales
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League",
    # Copas Nacionales
    48: "FA Cup",
    81: "DFB Pokal",
    137: "Coppa Italia",
    143: "Copa del Rey",
    66: "Coupe de France",
    # LATAM Continental
    13: "Copa Libertadores",
    11: "Copa Sudamericana",
    16: "CONCACAF Champions League",
}


async def fetch_fixtures_from_api(
    league_id: int, from_date: str, to_date: str, http_client: httpx.AsyncClient
) -> List[Dict[str, Any]]:
    """Obtener fixtures de una liga desde API-Football."""
    try:
        url = f"{settings.APIFOOTBALL_BASE_URL}/fixtures"
        params = {
            "league": league_id,
            "season": 2025,  # Temporada actual
            "from": from_date,
            "to": to_date,
            "timezone": "UTC",
        }
        headers = {"x-apisports-key": settings.APIFOOTBALL_API_KEY}

        response = await http_client.get(url, params=params, headers=headers, timeout=15.0)

        if response.status_code != 200:
            logger.warning(
                "api_request_failed", league_id=league_id, status_code=response.status_code
            )
            return []

        data = response.json()
        fixtures = data.get("response", [])

        logger.debug("api_fixtures_fetched", league_id=league_id, count=len(fixtures))

        return fixtures

    except Exception as e:
        logger.error("fetch_fixtures_error", league_id=league_id, error=str(e))
        return []


def transform_fixture_to_db_format(fixture_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transformar fixture de API-Football al formato de nuestra DB."""
    fixture = fixture_data["fixture"]
    league = fixture_data["league"]
    teams = fixture_data["teams"]
    goals = fixture_data["goals"]

    return {
        "id": fixture["id"],
        "league_id": league["id"],
        "season": league["season"],
        "kickoff_time": fixture["date"],
        "status": fixture["status"]["short"],
        "venue": fixture["venue"]["name"] if fixture.get("venue") else None,
        "referee": fixture.get("referee"),
        "home_team_id": teams["home"]["id"],
        "home_team_name": teams["home"]["name"],
        "away_team_id": teams["away"]["id"],
        "away_team_name": teams["away"]["name"],
        "home_score": goals["home"],
        "away_score": goals["away"],
        "round": league.get("round"),
        "last_synced_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }


async def upsert_fixtures_to_db(fixtures: List[Dict[str, Any]]) -> Dict[str, int]:
    """Insertar o actualizar fixtures en la base de datos."""
    if not fixtures:
        return {"new": 0, "updated": 0}

    client = get_supabase_client()

    try:
        # Upsert en lotes de 100
        batch_size = 100
        new_count = 0
        updated_count = 0

        for i in range(0, len(fixtures), batch_size):
            batch = fixtures[i : i + batch_size]

            # Upsert (on_conflict actualiza)
            result = client.table("fixtures").upsert(batch, on_conflict="id").execute()

            # Contar nuevos vs actualizados (aproximado)
            new_count += len([f for f in batch if f.get("created_at") is None])
            updated_count += len(batch) - new_count

        return {"new": new_count, "updated": updated_count}

    except Exception as e:
        logger.error("upsert_fixtures_error", error=str(e))
        return {"new": 0, "updated": 0}


async def load_upcoming_fixtures(days_ahead: int = 14) -> Dict[str, Any]:
    """
    Cargar fixtures de todas las ligas activas para los próximos N días.

    Args:
        days_ahead: Número de días hacia adelante para cargar

    Returns:
        Dict con estadísticas de la carga
    """
    start_time = time()

    today = datetime.now().date()
    end_date = today + timedelta(days=days_ahead)

    from_date = today.strftime("%Y-%m-%d")
    to_date = end_date.strftime("%Y-%m-%d")

    logger.info(
        "load_fixtures_started",
        from_date=from_date,
        to_date=to_date,
        leagues_count=len(ACTIVE_LEAGUES),
    )

    all_fixtures = []

    async with httpx.AsyncClient() as http_client:
        # Cargar fixtures de todas las ligas en paralelo (con rate limiting)
        semaphore = asyncio.Semaphore(3)  # Max 3 requests simultáneos

        async def fetch_with_semaphore(league_id: int):
            async with semaphore:
                fixtures = await fetch_fixtures_from_api(league_id, from_date, to_date, http_client)
                # Rate limiting: esperar 0.5s entre requests
                await asyncio.sleep(0.5)
                return fixtures

        tasks = [fetch_with_semaphore(lid) for lid in ACTIVE_LEAGUES.keys()]
        results = await asyncio.gather(*tasks)

        # Flatten results
        for fixtures in results:
            all_fixtures.extend(fixtures)

    logger.info("fixtures_fetched_from_api", total_count=len(all_fixtures))

    # Transformar a formato DB
    db_fixtures = [transform_fixture_to_db_format(f) for f in all_fixtures]

    # Upsert a la base de datos
    upsert_result = await upsert_fixtures_to_db(db_fixtures)

    duration = time() - start_time

    result = {
        "new_fixtures": upsert_result["new"],
        "updated_fixtures": upsert_result["updated"],
        "total_fetched": len(all_fixtures),
        "duration": round(duration, 2),
    }

    logger.info("load_fixtures_completed", **result)

    return result
