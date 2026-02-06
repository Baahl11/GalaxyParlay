"""Check fixtures for today (Feb 3, 2026)"""

from datetime import datetime, timedelta

from app.services.database import db_service

today = datetime(2026, 2, 3)
tomorrow = today + timedelta(days=1)

result = (
    db_service.client.table("fixtures")
    .select("id,home_team_name,away_team_name,kickoff_time,league_id,status")
    .gte("kickoff_time", today.isoformat())
    .lt("kickoff_time", tomorrow.isoformat())
    .order("kickoff_time")
    .execute()
)

print(f"✅ Fixtures para HOY (3 febrero 2026): {len(result.data)}")
print()

if result.data:
    for f in result.data:
        status = f.get("status", "NS")
        print(f"  [{status}] {f['home_team_name']} vs {f['away_team_name']}")
        print(f"       Kickoff: {f['kickoff_time']}")
        print(f"       League: {f['league_id']}")
        print()
else:
    print("⚠️ NO HAY FIXTURES para hoy en la base de datos")
    print()

    # Check próximos días
    print("Verificando próximos 7 días...")
    for i in range(1, 8):
        future_date = today + timedelta(days=i)
        next_day = future_date + timedelta(days=1)
        future_result = (
            db_service.client.table("fixtures")
            .select("id", count="exact")
            .gte("kickoff_time", future_date.isoformat())
            .lt("kickoff_time", next_day.isoformat())
            .execute()
        )

        if future_result.count > 0:
            print(f"  {future_date.strftime('%Y-%m-%d')}: {future_result.count} fixtures")
