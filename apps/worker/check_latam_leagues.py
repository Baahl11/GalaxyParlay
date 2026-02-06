"""Check LATAM fixtures."""

from datetime import datetime, timedelta

from app.services.database import DatabaseService

db = DatabaseService()

# Check if leagues are in DB
latam_leagues = {253: "MLS", 71: "Brasileirão", 128: "Liga Argentina", 262: "Liga MX"}

print("=== CHECKING LATAM LEAGUES IN DATABASE ===\n")
for league_id, name in latam_leagues.items():
    league = db.client.table("leagues").select("*").eq("id", league_id).execute()
    if league.data:
        print(f"✅ {name} (ID: {league_id}) - EXISTS in DB")
    else:
        print(f"❌ {name} (ID: {league_id}) - MISSING in DB")

print("\n=== CHECKING FIXTURES FOR NEXT 7 DAYS ===\n")
today = datetime.now().date()
end_date = today + timedelta(days=7)

for league_id, name in latam_leagues.items():
    fixtures = (
        db.client.table("fixtures")
        .select("id, home_team_name, away_team_name, kickoff_time")
        .eq("league_id", league_id)
        .gte("kickoff_time", today.isoformat())
        .lte("kickoff_time", end_date.isoformat())
        .execute()
    )

    print(f"{name} (ID: {league_id}): {len(fixtures.data)} fixtures")
    for f in fixtures.data[:3]:
        print(f"  - {f['home_team_name']} vs {f['away_team_name']} ({f['kickoff_time']})")
    if len(fixtures.data) > 3:
        print(f"  ... and {len(fixtures.data) - 3} more")
    print()
