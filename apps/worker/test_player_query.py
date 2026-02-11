"""Test player props query directly"""

from app.services.database import db_service

# Test query directly
team_id = 52  # Crystal Palace

print(f"🔍 Testing query for team {team_id}...")

result = (
    db_service.client.table("player_statistics")
    .select(
        "player_name, goals, assists, total_shots, shots_on_target, "
        "goals_per_90, shots_per_90, games_played, minutes_played, team_id"
    )
    .eq("team_id", team_id)
    .gte("goals", 0)
    .order("goals", desc=True)
    .limit(15)
    .execute()
)

print(f"\n✅ Result:")
print(f"   Has data: {bool(result.data)}")
print(f"   Count: {len(result.data) if result.data else 0}")
print(f"   Type: {type(result.data)}")

if result.data:
    print(f"\n📋 Players found:")
    for p in result.data[:5]:
        print(f"   - {p.get('player_name')}: {p.get('goals')} goals, team_id={p.get('team_id')}")
else:
    print("\n❌ NO DATA")
    print(f"   Result attributes: {dir(result)}")
    if hasattr(result, 'error'):
        print(f"   Error: {result.error}")
