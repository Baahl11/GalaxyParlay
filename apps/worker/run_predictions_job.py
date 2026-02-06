"""
Script simplificado para generar predicciones - ejecutar manualmente o con cron.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from supabase import create_client
from app.ml.multi_market_predictor import MultiMarketPredictor

# Config
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://jssjwjsuqmkzidigjpwj.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
if not SUPABASE_KEY:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

client = create_client(SUPABASE_URL, SUPABASE_KEY)
predictor = MultiMarketPredictor()

print("\n=== GENERANDO PREDICCIONES ===\n")

# Obtener fixtures próximos sin predicciones
today = datetime.now().strftime('%Y-%m-%d')
week_ahead = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

fixtures = client.table('fixtures').select(
    'id,league_id,home_team_id,away_team_id,home_team_name,away_team_name'
).gte('kickoff_time', f'{today}T00:00:00').lte(
    'kickoff_time', f'{week_ahead}T23:59:59'
).execute()

print(f"Total fixtures: {len(fixtures.data)}")

# Verificar cuáles ya tienen predicciones
fixture_ids = [f['id'] for f in fixtures.data]
existing = client.table('model_predictions').select('fixture_id').in_('fixture_id', fixture_ids).execute()
existing_ids = set(p['fixture_id'] for p in existing.data)

to_predict = [f for f in fixtures.data if f['id'] not in existing_ids]
print(f"Sin predicciones: {len(to_predict)}")

if not to_predict:
    print("✅ Todos los fixtures ya tienen predicciones!")
    sys.exit(0)

# Generar predicciones
success = 0
for i, fixture in enumerate(to_predict, 1):
    try:
        print(f"[{i}/{len(to_predict)}] {fixture['home_team_name']} vs {fixture['away_team_name']}...", end=" ")
        
        prediction = predictor.predict_all_markets(
            home_team_id=fixture['home_team_id'],
            away_team_id=fixture['away_team_id'],
            league_id=fixture['league_id'],
            is_cup=False
        )
        
        client.table('model_predictions').insert({
            'fixture_id': fixture['id'],
            'model_version': 'v2.0.0',
            'model_name': 'multi_market_ensemble',
            'predictions': prediction,
            'confidence_score': prediction.get('confidence', 0.75)
        }).execute()
        
        success += 1
        print("✓")
        
    except Exception as e:
        print(f"✗ {str(e)[:50]}")

print(f"\n✅ Completado: {success}/{len(to_predict)} predicciones generadas")
