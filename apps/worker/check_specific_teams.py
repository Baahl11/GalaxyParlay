"""Check player data for Crystal Palace (52) and Burnley (44)"""

from app.services.database import db_service

# Check Crystal Palace (52)
cp_result = (
    db_service.client.table("player_statistics")
    .select("*")
    .eq("team_id", 52)
    .order("goals", desc=True)
    .limit(5)
    .execute()
)

print("🔍 Crystal Palace (Team ID: 52)")
print(f"   Players found: {len(cp_result.data)}")
if cp_result.data:
    for p in cp_result.data:
        print(f"   - {p.get('player_name')}: {p.get('goals')} goals, {p.get('appearances')} apps")
print()

# Check Burnley (44)
burnley_result = (
    db_service.client.table("player_statistics")
    .select("*")
    .eq("team_id", 44)
    .order("goals", desc=True)
    .limit(5)
    .execute()
)

print("🔍 Burnley (Team ID: 44)")
print(f"   Players found: {len(burnley_result.data)}")
if burnley_result.data:
    for p in burnley_result.data:
        print(f"   - {p.get('player_name')}: {p.get('goals')} goals, {p.get('appearances')} apps")
print()

# Check a few other teams to confirm data exists
print("📊 Verificando otros equipos de Premier League:")
for team_id in [50, 36, 65, 39]:  # Man City, Fulham, Nottingham, Wolves
    result = (
        db_service.client.table("player_statistics")
        .select("player_id", count="exact")
        .eq("team_id", team_id)
        .execute()
    )
    print(f"   Team {team_id}: {result.count} players")
