"""Load fixtures for next 7 days from API-Football"""

import os
from datetime import datetime, timedelta

from app.services.apifootball import APIFootballClient
from app.services.database import db_service

api = APIFootballClient()

# Configurar fechas
today = datetime(2026, 2, 3)
end_date = today + timedelta(days=30)  # Extender a 30 dias para copas

print(f"Cargando fixtures desde {today.date()} hasta {end_date.date()}")
print()

# Ligas a cargar (las más importantes)
leagues = {
    # Ligas principales europeas
    39: "Premier League",
    140: "La Liga",
    135: "Serie A",
    78: "Bundesliga",
    61: "Ligue 1",
    94: "Primeira Liga",
    88: "Eredivisie",
    203: "Super Lig",
    144: "Jupiler Pro League",
    235: "Russian Premier League",
    # Segunda división europea
    40: "Championship",
    141: "LaLiga 2",
    136: "Serie B",
    79: "2. Bundesliga",
    62: "Ligue 2",
    # Copas nacionales
    143: "Copa del Rey",
    81: "DFB Pokal",
    66: "Coupe de France",
    137: "Coppa Italia",
    48: "FA Cup",
    # Ligas internacionales UEFA
    2: "UEFA Champions League",
    3: "UEFA Europa League",
    848: "UEFA Conference League",
    # Ligas internacionales CONMEBOL
    13: "Copa Libertadores",
    11: "Copa Sudamericana",
    # Ligas internacionales CONCACAF
    16: "CONCACAF Champions League",
    # LATAM
    262: "Liga MX",
    274: "Primera División Chile",
    273: "Primera División Uruguay",
    271: "Primera División Venezuela",
    71: "Brasileirão",
    128: "Liga Argentina",
    253: "MLS",
    # Asia
    307: "Saudi Pro League",
    188: "J1 League",
    # Copa del Mundo
    1: "World Cup",
}

total_loaded = 0

for league_id, league_name in leagues.items():
    print(f"[{league_name}] (ID: {league_id})...")

    try:
        # Cargar fixtures de esta liga
        fixtures_data = api.get_fixtures(
            league_id=league_id,
            season=2025,  # Temporada 2025/26
            date_from=today.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d"),
            status="NS",
        )

        if not fixtures_data:
            print(f"  [INFO] Sin fixtures en este rango")
            continue

        fixtures = fixtures_data

        if not fixtures:
            print(f"  [INFO] Sin fixtures en este rango")
            continue

        # Guardar en DB
        saved = 0
        for fixture in fixtures:
            try:
                fixture_id = fixture["fixture"]["id"]
                kickoff = fixture["fixture"]["date"]
                home_team = fixture["teams"]["home"]["name"]
                home_team_id = fixture["teams"]["home"]["id"]
                away_team = fixture["teams"]["away"]["name"]
                away_team_id = fixture["teams"]["away"]["id"]

                # Verificar si ya existe
                existing = (
                    db_service.client.table("fixtures").select("id").eq("id", fixture_id).execute()
                )

                if existing.data:
                    continue  # Ya existe

                # Insertar
                db_service.client.table("fixtures").insert(
                    {
                        "id": fixture_id,
                        "league_id": league_id,
                        "season": 2025,
                        "home_team_id": home_team_id,
                        "home_team_name": home_team,
                        "away_team_id": away_team_id,
                        "away_team_name": away_team,
                        "kickoff_time": kickoff,
                        "status": fixture["fixture"]["status"]["short"],
                        "home_score": fixture["goals"]["home"],
                        "away_score": fixture["goals"]["away"],
                    }
                ).execute()

                saved += 1

            except Exception as e:
                print(f"    [WARN] Error guardando fixture: {e}")
                continue

        print(f"  [OK] {saved} fixtures nuevos cargados")
        total_loaded += saved

    except Exception as e:
        print(f"  [ERROR] {e}")
        continue

print()
print(f"[DONE] Total cargados: {total_loaded} fixtures")
print()

# Verificar fixtures de hoy
today_result = (
    db_service.client.table("fixtures")
    .select("id", count="exact")
    .gte("kickoff_time", today.isoformat())
    .lt("kickoff_time", (today + timedelta(days=1)).isoformat())
    .execute()
)

print(f"[STATS] Fixtures para HOY: {today_result.count}")
