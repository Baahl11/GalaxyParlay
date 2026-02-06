"""Generar predicciones para todos los fixtures próximos sin predicciones."""

import asyncio
import os
from datetime import datetime, timedelta

import httpx
from supabase import create_client

# Configurar variables de entorno
os.environ["SUPABASE_URL"] = "https://jssjwjsuqmkzidigjpwj.supabase.co"
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc2p3anN1cW1remlkaWdqcHdqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQzNDQwMiwiZXhwIjoyMDg1MDEwNDAyfQ.iir_GtLYUZmAL66C_7BZJITxkq8rRQklWPqBS_Qp7io"
)

# Backend URL
BACKEND_URL = "https://galaxyparlay-production.up.railway.app"

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])


async def generate_predictions_for_fixture(
    fixture_id: int, league_id: int, http_client: httpx.AsyncClient
):
    """Generar predicciones para un fixture usando el endpoint del backend."""
    try:
        url = f"{BACKEND_URL}/jobs/multi-market-prediction/{fixture_id}"
        response = await http_client.post(url, timeout=30.0)

        if response.status_code == 200:
            return {"status": "success", "fixture_id": fixture_id}
        else:
            return {"status": "error", "fixture_id": fixture_id, "error": response.text}
    except Exception as e:
        return {"status": "error", "fixture_id": fixture_id, "error": str(e)}


async def main():
    # Obtener fixtures próximos sin predicciones
    today = datetime.now().strftime("%Y-%m-%d")
    weekend_end = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"\n=== GENERANDO PREDICCIONES PARA FIXTURES DEL {today} AL {weekend_end} ===\n")

    # Buscar fixtures
    fixtures_result = (
        client.table("fixtures")
        .select("id,kickoff_time,home_team_name,away_team_name,league_id")
        .gte("kickoff_time", f"{today}T00:00:00")
        .lte("kickoff_time", f"{weekend_end}T23:59:59")
        .order("kickoff_time")
        .execute()
    )

    print(f"Total fixtures encontrados: {len(fixtures_result.data)}")

    # Filtrar los que no tienen predicciones
    fixture_ids = [f["id"] for f in fixtures_result.data]
    pred_result = (
        client.table("model_predictions")
        .select("fixture_id")
        .in_("fixture_id", fixture_ids)
        .execute()
    )

    fixtures_with_predictions = set(p["fixture_id"] for p in pred_result.data)
    fixtures_without_predictions = [
        f for f in fixtures_result.data if f["id"] not in fixtures_with_predictions
    ]

    print(f"Fixtures sin predicciones: {len(fixtures_without_predictions)}")

    if not fixtures_without_predictions:
        print("\nTodos los fixtures ya tienen predicciones!")
        return

    print(f"\nGenerando predicciones para {len(fixtures_without_predictions)} fixtures...")
    print("=" * 80)

    # Generar predicciones en paralelo (máximo 5 a la vez)
    async with httpx.AsyncClient() as http_client:
        semaphore = asyncio.Semaphore(5)  # Máximo 5 requests paralelos

        async def generate_with_semaphore(fixture):
            async with semaphore:
                result = await generate_predictions_for_fixture(
                    fixture["id"], fixture["league_id"], http_client
                )

                if result["status"] == "success":
                    print(
                        f"[OK] {fixture['home_team_name']} vs {fixture['away_team_name']} (ID: {fixture['id']})"
                    )
                else:
                    print(
                        f"[ERROR] {fixture['home_team_name']} vs {fixture['away_team_name']} (ID: {fixture['id']}): {result.get('error', 'Unknown')}"
                    )

                return result

        # Ejecutar todas las tareas
        tasks = [generate_with_semaphore(f) for f in fixtures_without_predictions]
        results = await asyncio.gather(*tasks)

    # Resumen
    print("\n" + "=" * 80)
    success_count = sum(1 for r in results if r["status"] == "success")
    error_count = sum(1 for r in results if r["status"] == "error")

    print(f"\nRESUMEN:")
    print(f"  Exitosos: {success_count}")
    print(f"  Errores: {error_count}")
    print(f"  Total: {len(results)}")


if __name__ == "__main__":
    asyncio.run(main())
