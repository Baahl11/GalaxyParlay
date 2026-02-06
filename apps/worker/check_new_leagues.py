"""Check if new leagues have fixtures available"""

from datetime import datetime

from app.services.apifootball import APIFootballClient

api = APIFootballClient()

# Ligas/Copas a verificar
leagues_to_check = {
    143: "Copa del Rey",
    81: "DFB Pokal",
    66: "Coupe de France",
    137: "Coppa Italia",
    48: "FA Cup",
    13: "Copa Libertadores",
    11: "Copa Sudamericana",
    16: "CONCACAF Champions League",
    307: "Saudi Pro League",
}

print("Verificando disponibilidad de fixtures (proximos 30 dias)...")
print("=" * 70)
print()

today = datetime(2026, 2, 3)

for league_id, league_name in leagues_to_check.items():
    try:
        # Buscar fixtures sin filtro de fecha para ver si hay alguno
        fixtures = api.get_fixtures(
            league_id=league_id,
            season=2025,
            date_from="2026-02-01",
            date_to="2026-03-01",
            status="NS",
        )

        print(f"{league_name:30} (ID {league_id:3}): {len(fixtures):3} fixtures")

        if fixtures and len(fixtures) > 0:
            # Mostrar primeros 3
            for i, f in enumerate(fixtures[:3]):
                home = f["teams"]["home"]["name"]
                away = f["teams"]["away"]["name"]
                date = f["fixture"]["date"][:10]
                print(f"  - {date}: {home} vs {away}")

    except Exception as e:
        print(f"{league_name:30} (ID {league_id:3}): ERROR - {e}")

    print()

print("=" * 70)
