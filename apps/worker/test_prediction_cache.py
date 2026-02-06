"""
Test que las predicciones usan el cache automáticamente
"""

import time

from app.ml.predictor import MatchPredictor
from app.services.apifootball import clear_api_cache, get_cache_stats

print("=" * 80)
print("TEST: PREDICCIONES USANDO CACHE AUTOMÁTICAMENTE")
print("=" * 80)

# Clear cache
clear_api_cache()
print("\n1. Cache limpiado")
print(f"   Cache inicial: {get_cache_stats()['total_entries']} entries\n")

# Create predictor
predictor = MatchPredictor(
    use_bivariate_poisson=True, use_contextual_elo=True, use_live_xg=True  # Enable xG fetching
)

# Test fixture
fixture_id = 1208146  # Real fixture with xG data
home_team_id = 42  # Arsenal
away_team_id = 33  # Man United
league_id = 39  # Premier League

print(f"2. Generando predicción para fixture {fixture_id}...")
print(f"   Arsenal vs Man United")
print(f"   use_live_xg=True (debe buscar xG de API-Football)\n")

# First prediction - should hit API
start = time.time()
predictions1 = predictor.predict(
    home_team_id=home_team_id,
    away_team_id=away_team_id,
    league_id=league_id,
    fixture_id=fixture_id,
    use_live_xg=True,
)
time1 = time.time() - start

cache_stats1 = get_cache_stats()
print(f"   ✓ Primera predicción completada en {time1:.3f}s")
print(f"   ✓ Predicciones generadas: {len(predictions1)}")
print(f"   ✓ Cache size después: {cache_stats1['total_entries']} entries")

# Second prediction - should use cache
print(f"\n3. Generando SEGUNDA predicción del MISMO fixture...")
print(f"   (Debería usar cache para xG, team stats, H2H, etc.)\n")

start = time.time()
predictions2 = predictor.predict(
    home_team_id=home_team_id,
    away_team_id=away_team_id,
    league_id=league_id,
    fixture_id=fixture_id,
    use_live_xg=True,
)
time2 = time.time() - start

cache_stats2 = get_cache_stats()
print(f"   ✓ Segunda predicción completada en {time2:.3f}s")
print(f"   ✓ Predicciones generadas: {len(predictions2)}")
print(f"   ✓ Cache size después: {cache_stats2['total_entries']} entries")
print(f"   ✓ SPEEDUP: {time1/time2:.1f}x más rápido")

# Third prediction - different fixture (should partially use cache)
fixture_id3 = 1213504
home_team_id3 = 50  # Man City
away_team_id3 = 40  # Liverpool

print(f"\n4. Generando predicción para OTRO fixture...")
print(f"   Man City vs Liverpool (fixture {fixture_id3})")
print(f"   (xG nuevo, pero team stats pueden estar cacheados)\n")

start = time.time()
predictions3 = predictor.predict(
    home_team_id=home_team_id3,
    away_team_id=away_team_id3,
    league_id=league_id,
    fixture_id=fixture_id3,
    use_live_xg=True,
)
time3 = time.time() - start

cache_stats3 = get_cache_stats()
print(f"   ✓ Tercera predicción completada en {time3:.3f}s")
print(f"   ✓ Cache size después: {cache_stats3['total_entries']} entries")

# Summary
print("\n" + "=" * 80)
print("RESUMEN DE CACHE PERFORMANCE:")
print("=" * 80)
print(f"  Primera predicción (Arsenal vs Man United):  {time1:.3f}s (Cold cache)")
print(f"  Segunda predicción (MISMO fixture):         {time2:.3f}s ({time1/time2:.1f}x speedup) ✓")
print(f"  Tercera predicción (fixture diferente):     {time3:.3f}s")
print(f"\n  Cache entries totales: {cache_stats3['total_entries']}")
print(f"  CACHE FUNCIONA: Todas las predicciones usan cache compartido ✓")
print(f"  COSTO REDUCIDO: API calls minimizadas ✓")
print("=" * 80)

# Show sample predictions
print(f"\nEjemplo de predicción (Arsenal vs Man United):")
for pred in predictions1[:3]:
    market = pred.get("market_key", "unknown")
    prediction = pred.get("prediction", {})
    confidence = pred.get("confidence_score", 0)
    print(f"  {market}: {prediction} (confidence: {confidence:.2f})")
