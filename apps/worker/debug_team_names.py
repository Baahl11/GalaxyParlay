"""Debug script to check team names in fixtures"""

import json

from app.services.database import DatabaseService

db = DatabaseService()

# Get fixtures with NS status
fixtures = db.get_fixtures(status="NS", limit=5)

print("\n=== FIXTURES WITH NS STATUS ===")
for f in fixtures[:3]:
    print(
        f"\n{f['id']}: {f.get('home_team_name', 'NO_NAME')} vs {f.get('away_team_name', 'NO_NAME')}"
    )
    print(f"  Home ID: {f.get('home_team_id')}")
    print(f"  Away ID: {f.get('away_team_id')}")
    print(f"  Kickoff: {f['kickoff_time']}")
    print(f"  League: {f.get('league_id')}")
