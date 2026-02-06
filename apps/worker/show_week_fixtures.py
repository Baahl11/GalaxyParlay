"""Show fixtures distribution by day"""

from datetime import datetime, timedelta

from app.services.database import db_service

today = datetime(2026, 2, 3)  # Martes

print("=" * 60)
print("FIXTURES POR DIA (3-10 Feb 2026)")
print("=" * 60)
print()

for i in range(8):
    date = today + timedelta(days=i)
    next_date = date + timedelta(days=1)

    # Get fixtures for this day
    result = (
        db_service.client.table("fixtures")
        .select("id,home_team_name,away_team_name,kickoff_time,league_id")
        .gte("kickoff_time", date.isoformat())
        .lt("kickoff_time", next_date.isoformat())
        .order("kickoff_time")
        .execute()
    )

    day_name = ["LUN", "MAR", "MIE", "JUE", "VIE", "SAB", "DOM"][date.weekday()]

    if i == 0:
        print(f"{date.strftime('%Y-%m-%d')} ({day_name}) - HOY: {len(result.data)} partidos")
    else:
        print(f"{date.strftime('%Y-%m-%d')} ({day_name}): {len(result.data)} partidos")

    if result.data:
        for f in result.data[:5]:  # Show first 5
            time = f["kickoff_time"].split("T")[1][:5]
            print(f"  {time} - {f['home_team_name']} vs {f['away_team_name']}")
        if len(result.data) > 5:
            print(f"  ... y {len(result.data) - 5} partidos mas")
    print()

print("=" * 60)
