"""Show summary of loaded fixtures."""

import sys

sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from app.services.database import db_service

# Get total fixtures
result = db_service.client.table("fixtures").select("id").execute()
print(f"\nTotal fixtures en DB: {len(result.data)}")

# Get fixtures by league
result = db_service.client.table("fixtures").select("league_id").execute()
league_counts = {}
for f in result.data:
    lid = f["league_id"]
    league_counts[lid] = league_counts.get(lid, 0) + 1

# Get league names
result = db_service.client.table("leagues").select("id, name").execute()
league_names = {l["id"]: l["name"] for l in result.data}

print("\nFixtures por liga:")
for lid in sorted(league_counts.keys()):
    name = league_names.get(lid, f"League {lid}")
    count = league_counts[lid]
    print(f"  {name}: {count} fixtures")

# Get today's fixtures count
result = (
    db_service.client.table("fixtures")
    .select("id")
    .gte("kickoff_time", "2026-02-03T00:00:00")
    .lte("kickoff_time", "2026-02-03T23:59:59")
    .execute()
)
print(f"\nFixtures HOY (3 Feb): {len(result.data)}")
