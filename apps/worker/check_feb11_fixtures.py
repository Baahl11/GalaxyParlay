"""Check fixtures for Feb 11, 2026 and verify player data coverage"""

from datetime import datetime, timedelta

from app.services.database import db_service

target_date = datetime(2026, 2, 11)
next_day = target_date + timedelta(days=1)

# Get fixtures for Feb 11
result = (
    db_service.client.table("fixtures")
    .select(
        "id,home_team_id,away_team_id,home_team_name,away_team_name,kickoff_time,league_id,status"
    )
    .gte("kickoff_time", target_date.isoformat())
    .lt("kickoff_time", next_day.isoformat())
    .order("kickoff_time")
    .execute()
)

print(f"✅ Fixtures para Feb 11, 2026: {len(result.data)}")
print()

# Get teams with player data
player_result = db_service.client.table("player_statistics").select("team_id").execute()

teams_with_players = set(p["team_id"] for p in player_result.data)
print(f"📊 Equipos con player data: {len(teams_with_players)}")
print()

if result.data:
    fixtures_with_players = 0
    fixtures_without_players = 0

    for f in result.data[:20]:  # Show first 20
        home_has = f["home_team_id"] in teams_with_players
        away_has = f["away_team_id"] in teams_with_players
        both_have = home_has and away_has

        if both_have:
            fixtures_with_players += 1
            marker = "✅"
        else:
            fixtures_without_players += 1
            marker = "❌"

        print(f"{marker} [{f['league_id']}] {f['home_team_name']} vs {f['away_team_name']}")
        print(
            f"   Home ID: {f['home_team_id']} {'✓' if home_has else '✗'} | Away ID: {f['away_team_id']} {'✓' if away_has else '✗'}"
        )
        print(f"   Fixture ID: {f['id']}")
        print()

    print(f"📈 Resumen:")
    print(f"   Con player props: {fixtures_with_players}/{len(result.data)}")
    print(f"   Sin player props: {fixtures_without_players}/{len(result.data)}")
else:
    print("⚠️ NO HAY FIXTURES para Feb 11, 2026")
