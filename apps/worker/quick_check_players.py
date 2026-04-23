"""Quick check of player props for fixture 1379222"""

from app.services.database import db_service

# Get the prediction
result = (
    db_service.client.table("model_predictions")
    .select("*")
    .eq("fixture_id", 1379222)
    .limit(1)
    .execute()
)

if result.data:
    pred = result.data[0]
    player_props = pred.get("predictions", {}).get("player_props", {})
    home_players = player_props.get("home_players", [])
    away_players = player_props.get("away_players", [])

    print(f"✅ Crystal Palace vs Burnley (Fixture 1379222)")
    print(f"\n🏠 HOME (Crystal Palace):")
    print(f"   Players found: {len(home_players)}")
    if home_players:
        for i, p in enumerate(home_players[:3], 1):
            prob = p.get("anytime_scorer_probability", 0) * 100
            print(f"   {i}. {p.get('player_name')}: {prob:.1f}% scorer probability")

    print(f"\n✈️  AWAY (Burnley):")
    print(f"   Players found: {len(away_players)}")
    if away_players:
        for i, p in enumerate(away_players[:3], 1):
            prob = p.get("anytime_scorer_probability", 0) * 100
            print(f"   {i}. {p.get('player_name')}: {prob:.1f}% scorer probability")

    if len(home_players) == 0 and len(away_players) == 0:
        print(f"\n❌ Player props VACÍOS - necesita regeneración")
    else:
        print(f"\n✅ Player props FUNCIONANDO!")
else:
    print("❌ No se encontró predicción para fixture 1379222")
