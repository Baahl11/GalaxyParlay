"""Check if multi-market predictions exist for Feb 11 fixtures"""

from app.services.database import db_service

# Check if predictions exist for fixture 1379222
result = (
    db_service.client.table("model_predictions").select("*").eq("fixture_id", 1379222).execute()
)

print(f"🔍 Predicciones para fixture 1379222 (Crystal Palace vs Burnley): {len(result.data)}")
if result.data:
    pred = result.data[0]
    print(f"   Generada: {pred.get('created_at', 'N/A')}")
    print(f"   Grade: {pred.get('quality_grade', 'N/A')}")

    # Check player props in predictions
    predictions = pred.get("predictions", {})
    player_props = predictions.get("player_props", {})
    home_players = player_props.get("home_players", [])
    away_players = player_props.get("away_players", [])

    print(f"\n   Player Props:")
    print(f"     Home: {len(home_players)} players")
    print(f"     Away: {len(away_players)} players")

    if home_players:
        print(f"\n   🏠 Top 3 home players:")
        for p in home_players[:3]:
            prob = p.get("anytime_scorer_probability", 0) * 100
            print(f"     - {p.get('player_name')}: {prob:.1f}%")

    if away_players:
        print(f"\n   ✈️  Top 3 away players:")
        for p in away_players[:3]:
            prob = p.get("anytime_scorer_probability", 0) * 100
            print(f"     - {p.get('player_name')}: {prob:.1f}%")
else:
    print("   ❌ NO EXISTE - Predicción no generada")
    print("\n📋 Verificando qué fixtures tienen predicciones para Feb 11...")

    # Get all Feb 11 fixtures
    from datetime import datetime, timedelta

    target_date = datetime(2026, 2, 11)
    next_day = target_date + timedelta(days=1)

    fixtures_result = (
        db_service.client.table("fixtures")
        .select("id,home_team_name,away_team_name")
        .gte("kickoff_time", target_date.isoformat())
        .lt("kickoff_time", next_day.isoformat())
        .execute()
    )

    fixture_ids = [f["id"] for f in fixtures_result.data]
    print(f"\n   Total fixtures Feb 11: {len(fixture_ids)}")

    # Check which have predictions
    preds_result = (
        db_service.client.table("model_predictions")
        .select("fixture_id")
        .in_("fixture_id", fixture_ids)
        .execute()
    )

    with_preds = len(preds_result.data)
    print(f"   Con predicciones: {with_preds}/{len(fixture_ids)}")

    if with_preds < len(fixture_ids):
        pred_ids = set(p["fixture_id"] for p in preds_result.data)
        missing = [f for f in fixtures_result.data if f["id"] not in pred_ids]
        print(f"\n   ⚠️  Fixtures sin predicciones:")
        for f in missing[:5]:
            print(f"     - {f['home_team_name']} vs {f['away_team_name']} (ID: {f['id']})")
