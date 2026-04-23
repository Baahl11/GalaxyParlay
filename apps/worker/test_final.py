"""Test final - regenerate and check"""

import time

import requests

from app.services.database import db_service

fixture_id = 1379222

# 1. Delete old predictions
print(f"🗑️  Borrando predicciones viejas...")
delete_result = (
    db_service.client.table("model_predictions").delete().eq("fixture_id", fixture_id).execute()
)
print(f"✅ Borradas: {len(delete_result.data if delete_result.data else [])} predicciones")

# 2. Regenerate
print(f"\n🔄 Regenerando predicciones...")
response = requests.post(
    "https://galaxyparlay-production.up.railway.app/jobs/run-predictions",
    json={"fixture_ids": [fixture_id]},
    headers={"Content-Type": "application/json"},
)
print(f"✅ Respuesta: {response.status_code}")
print(f"   Generadas: {response.json().get('predictions_generated', 0)}")

# 3. Wait
print(f"\n⏳ Esperando 3 segundos...")
time.sleep(3)

# 4. Check
print(f"\n🔍 Verificando player props...")
result = (
    db_service.client.table("model_predictions")
    .select("*")
    .eq("fixture_id", fixture_id)
    .limit(1)
    .execute()
)

if result.data:
    pred = result.data[0]
    player_props = pred.get("predictions", {}).get("player_props", {})
    home_players = player_props.get("home_players", [])
    away_players = player_props.get("away_players", [])

    print(f"\n📊 RESULTADOS:")
    print(f"   Home players: {len(home_players)}")
    print(f"   Away players: {len(away_players)}")

    if home_players:
        print(f"\n🏠 Top 3 Home:")
        for p in home_players[:3]:
            print(f"   - {p.get('player_name')}: {p.get('anytime_scorer', 0)*100:.1f}%")

    if away_players:
        print(f"\n✈️  Top 3 Away:")
        for p in away_players[:3]:
            print(f"   - {p.get('player_name')}: {p.get('anytime_scorer', 0)*100:.1f}%")

    if len(home_players) > 0 and len(away_players) > 0:
        print(f"\n✅✅✅ PLAYER PROPS FUNCIONANDO!! ✅✅✅")
    else:
        print(f"\n❌ Player props vacíos")
else:
    print("❌ No se encontró predicción")
