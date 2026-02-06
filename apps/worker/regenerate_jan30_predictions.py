"""
Regenerate predictions for January 30 with FIFA MAXIMIZED
This will test if FIFA integration is now working across all 35 markets
"""

from app.ml.predictor import match_predictor
from app.services.database import db_service


def regenerate_predictions():
    print("=" * 80)
    print("REGENERANDO PREDICCIONES CON FIFA MAXIMIZADO - 30 DE ENERO 2026")
    print("=" * 80)

    # 1. Get fixtures from January 30
    print("\n[1] Cargando fixtures del 30 de enero...")
    fixtures_response = (
        db_service.client.table("fixtures")
        .select("*")
        .gte("kickoff_time", "2026-01-30T00:00:00")
        .lt("kickoff_time", "2026-01-31T00:00:00")
        .eq("status", "FT")  # Only finished matches
        .execute()
    )

    fixtures = fixtures_response.data
    print(f"   Total fixtures: {len(fixtures)}")

    if not fixtures:
        print("\n[!] No hay fixtures finalizados del 30 de enero")
        return

    # 2. Load Elo ratings and historical stats
    print("\n[2] Cargando modelo...")
    match_predictor.load_elo_from_db()
    match_predictor.load_historical_stats()

    # 3. Delete old predictions
    print("\n[3] Eliminando predicciones antiguas...")
    fixture_ids = [f["id"] for f in fixtures]
    delete_response = (
        db_service.client.table("model_predictions")
        .delete()
        .in_("fixture_id", fixture_ids)
        .execute()
    )
    print(f"   Predicciones eliminadas: {len(delete_response.data) if delete_response.data else 0}")

    # 4. Generate new predictions with FIFA
    print("\n[4] Generando predicciones con FIFA...")
    total_predictions = 0

    for i, fixture in enumerate(fixtures, 1):
        print(
            f"\n   [{i}/{len(fixtures)}] {fixture['home_team_name']} vs {fixture['away_team_name']}"
        )

        try:
            # Generate predictions with ALL markets enabled
            predictions = match_predictor.predict_fixture(
                fixture=fixture, include_all_markets=True  # This enables the 35 markets
            )

            if predictions:
                # Save to database
                db_service.client.table("model_predictions").insert(predictions).execute()
                total_predictions += len(predictions)
                print(f"      [OK] {len(predictions)} predicciones generadas")
            else:
                print("      [WARN] No predictions generated")

        except Exception as e:
            print(f"      [ERROR] {e}")

    print("\n" + "=" * 80)
    print(f"[OK] Regeneracion completada: {total_predictions} predicciones totales")
    print("=" * 80)
    print("\n[INFO] Ahora ejecuta: python analyze_all_markets_jan30.py")


if __name__ == "__main__":
    regenerate_predictions()
