"""Delete old predictions for specific fixture"""

from app.services.database import db_service

fixture_id = 1379222

print(f"🗑️  Borrando predicciones viejas para fixture {fixture_id}...")

result = (
    db_service.client.table("model_predictions").delete().eq("fixture_id", fixture_id).execute()
)

print(f"✅ Borradas: {len(result.data if result.data else [])} predicciones")
print("\n🔄 Ahora regenera las predicciones con el endpoint run-predictions")
