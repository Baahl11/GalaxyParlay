"""
Prediction Generator Service
Genera predicciones en lotes de manera eficiente.
"""

import asyncio
from time import time
from typing import Any, Dict, List

import httpx
import structlog

from app.core.database import get_supabase_client
from app.ml.multi_market_predictor import MultiMarketPredictor

logger = structlog.get_logger(__name__)


async def generate_prediction_for_fixture(
    fixture: Dict[str, Any], predictor: MultiMarketPredictor, force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Generar predicción para un fixture específico.

    Args:
        fixture: Dict con id, league_id, home_team_id, away_team_id
        predictor: Instancia del predictor
        force_refresh: Si True, regenerar incluso si ya existe

    Returns:
        Dict con resultado de la operación
    """
    try:
        fixture_id = fixture["id"]
        league_id = fixture["league_id"]
        home_team_id = fixture["home_team_id"]
        away_team_id = fixture["away_team_id"]

        # Generar predicción usando el predictor
        prediction = await asyncio.to_thread(
            predictor.predict_all_markets,
            home_team_id=home_team_id,
            away_team_id=away_team_id,
            league_id=league_id,
            is_cup=False,  # TODO: detectar si es copa
        )

        # Guardar en base de datos
        client = get_supabase_client()

        prediction_data = {
            "fixture_id": fixture_id,
            "model_version": "v2.0.0",
            "model_name": "multi_market_ensemble",
            "predictions": prediction,
            "confidence_score": prediction.get("confidence", 0.75),
            "created_at": None if not force_refresh else None,  # Let DB set timestamp
        }

        if force_refresh:
            # Eliminar predicción anterior
            client.table("model_predictions").delete().eq("fixture_id", fixture_id).execute()

        # Insertar nueva predicción
        result = client.table("model_predictions").insert(prediction_data).execute()

        return {"status": "success", "fixture_id": fixture_id}

    except Exception as e:
        logger.error("generate_prediction_error", fixture_id=fixture.get("id"), error=str(e))
        return {"status": "error", "fixture_id": fixture.get("id"), "error": str(e)}


async def generate_predictions_batch(
    fixtures: List[Dict[str, Any]], force_refresh: bool = False, batch_size: int = 10
) -> Dict[str, Any]:
    """
    Generar predicciones para múltiples fixtures en paralelo.

    Args:
        fixtures: Lista de fixtures
        force_refresh: Si True, regenerar predicciones existentes
        batch_size: Número de predicciones a procesar en paralelo

    Returns:
        Dict con estadísticas de la operación
    """
    start_time = time()

    if not fixtures:
        return {"success_count": 0, "error_count": 0, "duration": 0}

    logger.info(
        "generate_predictions_batch_started",
        total_fixtures=len(fixtures),
        force_refresh=force_refresh,
    )

    # Inicializar predictor (carga modelos en memoria)
    predictor = MultiMarketPredictor()

    # Procesar en lotes para no sobrecargar
    semaphore = asyncio.Semaphore(batch_size)

    async def generate_with_semaphore(fixture):
        async with semaphore:
            result = await generate_prediction_for_fixture(fixture, predictor, force_refresh)
            return result

    # Ejecutar todas las tareas
    tasks = [generate_with_semaphore(f) for f in fixtures]
    results = await asyncio.gather(*tasks)

    # Contar resultados
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    duration = time() - start_time

    result = {
        "success_count": success_count,
        "error_count": error_count,
        "total": len(results),
        "duration": round(duration, 2),
    }

    logger.info("generate_predictions_batch_completed", **result)

    return result
