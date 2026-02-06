"""
Generar predicciones directamente (sin API).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timedelta
from supabase import create_client
from app.ml.multi_market_predictor import MultiMarketPredictor
from app.services.database import db_service

SUPABASE_URL = 'https://jssjwjsuqmkzidigjpwj.supabase.co'
SUPABASE_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Impzc2p3anN1cW1remlkaWdqcHdqIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2OTQzNDQwMiwiZXhwIjoyMDg1MDEwNDAyfQ.iir_GtLYUZmAL66C_7BZJITxkq8rRQklWPqBS_Qp7io'

client = create_client(SUPABASE_URL, SUPABASE_KEY)
predictor = MultiMarketPredictor()

print("\n=== GENERANDO PREDICCIONES DIRECTAMENTE ===\n")

# Obtener fixtures próximos
today = datetime.now().strftime('%Y-%m-%d')
week_ahead = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')

fixtures = client.table('fixtures').select(
    'id,league_id,home_team_id,away_team_id,home_team_name,away_team_name'
).gte('kickoff_time', f'{today}T00:00:00').lte(
    'kickoff_time', f'{week_ahead}T23:59:59'
).execute()

print(f"Total fixtures: {len(fixtures.data)}\n")

success = 0
failed = 0

for i, fixture in enumerate(fixtures.data, 1):
    try:
        print(f"[{i}/{len(fixtures.data)}] {fixture['home_team_name']} vs {fixture['away_team_name']}...", end=" ")
        
        # Generar predicción
        prediction = predictor.predict_all_markets(
            home_team_id=fixture['home_team_id'],
            away_team_id=fixture['away_team_id'],
            league_id=fixture['league_id'],
            is_cup=False
        )
        
        # Guardar usando el método del db_service
        db_service.store_prediction(
            fixture_id=fixture['id'],
            predictions=prediction,
            model_name="multi_market_ensemble",
            model_version="v2.0.0"
        )
        
        success += 1
        print("[OK]")
            
    except Exception as e:
        failed += 1
        print(f"[ERROR] {str(e)[:50]}")

print(f"\n[DONE] Completado: {success} exitos, {failed} fallos")
