"""Verificar fixtures próximos y sus predicciones."""

import os
from datetime import datetime, timedelta

from supabase import create_client

# Configurar variables de entorno
os.environ["SUPABASE_URL"] = "https://jssjwjsuqmkzidigjpwj.supabase.co"
# SUPABASE_SERVICE_ROLE_KEY must be set in environment variables
if "SUPABASE_SERVICE_ROLE_KEY" not in os.environ:
    raise ValueError("SUPABASE_SERVICE_ROLE_KEY environment variable is required")

client = create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

# Fechas
today = datetime.now().strftime("%Y-%m-%d")
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
weekend_end = (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d")

print(f"\n=== FIXTURES DEL {today} AL {weekend_end} ===\n")

# Buscar fixtures
result = (
    client.table("fixtures")
    .select("id,kickoff_time,home_team_name,away_team_name,league_id")
    .gte("kickoff_time", f"{today}T00:00:00")
    .lte("kickoff_time", f"{weekend_end}T23:59:59")
    .order("kickoff_time")
    .execute()
)

print(f"✅ Total fixtures encontrados: {len(result.data)}\n")

# Agrupar por fecha
from collections import defaultdict

fixtures_by_date = defaultdict(list)

for fixture in result.data:
    date = fixture["kickoff_time"][:10]
    fixtures_by_date[date].append(fixture)

# Mostrar por fecha
for date in sorted(fixtures_by_date.keys()):
    fixtures = fixtures_by_date[date]
    print(f"\n📅 {date} - {len(fixtures)} fixtures:")

    # Agrupar por liga
    by_league = defaultdict(list)
    for f in fixtures:
        by_league[f["league_id"]].append(f)

    for league_id in sorted(by_league.keys()):
        league_fixtures = by_league[league_id]
        print(f"   🏆 Liga {league_id} ({len(league_fixtures)} partidos):")
        for f in league_fixtures[:5]:  # Mostrar máximo 5 por liga
            home = f["home_team_name"]
            away = f["away_team_name"]
            print(f"      - {home} vs {away} (ID: {f['id']})")
        if len(league_fixtures) > 5:
            print(f"      ... y {len(league_fixtures)-5} más")

# Verificar predicciones
print(f"\n\n=== PREDICCIONES ===\n")
fixture_ids = [f["id"] for f in result.data]
if fixture_ids:
    pred_result = (
        client.table("model_predictions")
        .select("fixture_id")
        .in_("fixture_id", fixture_ids)
        .execute()
    )

    fixtures_with_predictions = set(p["fixture_id"] for p in pred_result.data)
    fixtures_without_predictions = set(fixture_ids) - fixtures_with_predictions

    print(f"✅ Fixtures CON predicciones: {len(fixtures_with_predictions)}")
    print(f"❌ Fixtures SIN predicciones: {len(fixtures_without_predictions)}")

    if fixtures_without_predictions:
        print(f"\n🔴 Primeros 10 fixtures sin predicciones:")
        for fid in list(fixtures_without_predictions)[:10]:
            fixture = next(f for f in result.data if f["id"] == fid)
            date = fixture["kickoff_time"][:10]
            home = fixture["home_team_name"]
            away = fixture["away_team_name"]
            print(f"   {date} - Liga {fixture['league_id']}: {home} vs {away} (ID: {fid})")
