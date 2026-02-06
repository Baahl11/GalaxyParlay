"""Ver qué ligas tenemos en la base de datos"""

from app.services.database import db_service

leagues = db_service.client.table("leagues").select("id,name,country").execute()

print(f"Total ligas en DB: {len(leagues.data)}\n")
print("=" * 80)

for league in sorted(leagues.data, key=lambda x: x["id"]):
    print(f"{league['id']:4d} - {league['name']:40s} ({league['country']})")

print("=" * 80)

# Ver cuántos fixtures tenemos por liga
fixtures_by_league = (
    db_service.client.table("fixtures").select("league_id", count="exact").execute()
)

print(f"\nTotal fixtures: {fixtures_by_league.count}")

# Contar por liga
from collections import Counter

fixtures_all = db_service.client.table("fixtures").select("league_id").execute()
league_counts = Counter([f["league_id"] for f in fixtures_all.data])

print("\nFixtures por liga:")
print("-" * 80)
league_dict = {l["id"]: l["name"] for l in leagues.data}
for league_id, count in sorted(league_counts.items(), key=lambda x: -x[1]):
    league_name = league_dict.get(league_id, f"Unknown {league_id}")
    print(f"{league_name:40s} {count:5d} fixtures")
