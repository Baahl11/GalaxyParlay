"""Delete all old predictions and regenerate fresh ones with player props fix"""

from app.services.database import db_service
import requests

print("=" * 60)
print("🗑️  LIMPIEZA Y REGENERACIÓN COMPLETA")
print("=" * 60)

# 1. Get current prediction count
print("\n📊 Estado actual:")
count_result = (
    db_service.client.table("model_predictions")
    .select("id", count="exact")
    .execute()
)
print(f"   Predicciones actuales: {count_result.count}")

# 2. Delete ALL old predictions
print("\n🗑️  Borrando TODAS las predicciones viejas...")
delete_result = (
    db_service.client.table("model_predictions")
    .delete()
    .neq("id", "00000000-0000-0000-0000-000000000000")  # Delete all
    .execute()
)
print(f"✅ Borradas exitosamente")

# 3. Verify deletion
verify_result = (
    db_service.client.table("model_predictions")
    .select("id", count="exact")
    .execute()
)
print(f"   Predicciones restantes: {verify_result.count}")

# 4. Regenerate fresh predictions (next 7 days)
print("\n🔄 Regenerando predicciones FRESCAS (próximos 7 días)...")
print("   ⏳ Esto puede tomar 2-3 minutos...")

try:
    response = requests.post(
        "https://galaxyparlay-production.up.railway.app/jobs/run-predictions?days_ahead=7",
        headers={"Content-Type": "application/json"},
        timeout=300  # 5 minutes timeout
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ REGENERACIÓN COMPLETADA:")
        print(f"   Predicciones: {data.get('predictions_generated', 0)}")
        print(f"   Fixtures: {data.get('fixtures_processed', 0)}")
        print(f"   Fallidos: {data.get('failed', 0)}")
        
        grades = data.get('grade_distribution', {})
        if grades:
            print(f"\n   📊 Distribución:")
            print(f"      Grade A: {grades.get('A', 0)}")
            print(f"      Grade B: {grades.get('B', 0)}")
            print(f"      Grade C: {grades.get('C', 0)}")
            print(f"      Grade D: {grades.get('D', 0)}")
    else:
        print(f"\n⚠️  Status code: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
        
except requests.Timeout:
    print("\n⏳ Timeout (normal) - las predicciones se están generando en background")
    print("   Espera 3-5 minutos y verifica con el siguiente comando:")
    print("   GET /jobs/scheduler-status")
except Exception as e:
    print(f"\n❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ PROCESO COMPLETADO")
print("=" * 60)
print("\n💡 Para verificar player props:")
print("   GET /multi-market-prediction/<fixture_id>")
print("   Busca el campo: predictions.player_props")
