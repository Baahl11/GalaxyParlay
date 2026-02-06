"""Check leagues in database."""

import sys

sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from app.services.database import db_service

result = db_service.client.table("leagues").select("id, name, country").execute()
print(f"Ligas actuales en DB: {len(result.data)}")
for league in sorted(result.data, key=lambda x: x["id"]):
    print(f"  {league['id']}: {league['name']} ({league['country']})")
