"""Mostrar lista de partidos del 30 de enero"""

from datetime import datetime

from app.services.database import db_service

fixtures_response = (
    db_service.client.table("fixtures")
    .select("id,kickoff_time,home_team_name,away_team_name,home_score,away_score,status,league_id")
    .gte("kickoff_time", "2026-01-30T00:00:00")
    .lt("kickoff_time", "2026-01-31T00:00:00")
    .order("kickoff_time")
    .execute()
)

fixtures = fixtures_response.data

print("=" * 100)
print("PARTIDOS DEL 30 DE ENERO 2026")
print("=" * 100)

for i, f in enumerate(fixtures, 1):
    kickoff = datetime.fromisoformat(f["kickoff_time"].replace("Z", "+00:00"))
    time_str = kickoff.strftime("%H:%M")

    home = f["home_team_name"]
    away = f["away_team_name"]
    status = f["status"]

    home_score = f.get("home_score")
    away_score = f.get("away_score")

    if home_score is not None and away_score is not None:
        score = f"{home_score}-{away_score}"
    else:
        score = "- vs -"

    print(f"\n{i:2d}. [{time_str}] {home:30s} vs {away:30s}")
    print(f"    Status: {status:10s} | Score: {score:7s} | Liga: {f['league_id']}")

print("\n" + "=" * 100)

finished = len([f for f in fixtures if f["status"] == "FT"])
pending = len([f for f in fixtures if f["status"] != "FT"])

print(f"Total: {len(fixtures)} partidos | ✅ Finalizados: {finished} | ⏳ Pendientes: {pending}")
print("=" * 100)
