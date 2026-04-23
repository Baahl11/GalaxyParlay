"""Simple final check"""
import requests

# Get full prediction
url = "https://galaxyparlay-production.up.railway.app/multi-market-prediction/1379222"
print(f"🔍 Buscando predicción...")

try:
    response = requests.get(url, timeout=10)
    
    if response.status_code == 404:
        print("❌ 404 - Predicción no existe")
        print("\n🔄 Regenerando...")
        regen = requests.post(
            "https://galaxyparlay-production.up.railway.app/jobs/run-predictions",
            json={"fixture_ids": [1379222]},
            timeout=30
        )
        print(f"✅ Status: {regen.status_code}")
        
        import time
        time.sleep(3)
        
        print("\n🔍 Verificando de nuevo...")
        response = requests.get(url, timeout=10)
    
    data = response.json()
    player_props = data["predictions"]["player_props"]
    home_count = len(player_props["home_players"])
    away_count = len(player_props["away_players"])
    
    print(f"\n📊 RESULTADOS:")
    print(f"   Home players: {home_count}")
    print(f"   Away players: {away_count}")
    
    if home_count > 0:
        print(f"\n🏠 Top home player: {player_props['home_players'][0]['player_name']}")
        print(f"   Scorer prob: {player_props['home_players'][0]['anytime_scorer']*100:.1f}%")
    
    if away_count > 0:
        print(f"\n✈️  Top away player: {player_props['away_players'][0]['player_name']}")
        print(f"   Scorer prob: {player_props['away_players'][0]['anytime_scorer']*100:.1f}%")
    
    if home_count > 0 and away_count > 0:
        print(f"\n✅✅✅ PLAYER PROPS FUNCIONANDO! ✅✅✅")
    else:
        print(f"\n❌ Vacíos")
        
except Exception as e:
    print(f"❌ Error: {e}")
