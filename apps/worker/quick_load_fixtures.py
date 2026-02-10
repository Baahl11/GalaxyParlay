"""Quick load fixtures for today and next 7 days"""

import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.apifootball import APIFootballClient
from app.services.database import db_service

api = APIFootballClient()

# Configurar fechas - HOY es 6 de febrero 2026
today = datetime(2026, 2, 6)
end_date = today + timedelta(days=7)

print(f"🔄 Cargando fixtures desde {today.date()} hasta {end_date.date()}")
print()

# Ligas principales que deben tener partidos esta semana
leagues = [
    39,  # Premier League
    140,  # La Liga
    135,  # Serie A
    78,  # Bundesliga
    61,  # Ligue 1
    262,  # Liga MX
    71,  # Brasileirao
    253,  # MLS
    2,  # Champions League
    3,  # Europa League
]

total_loaded = 0

for league_id in leagues:
    try:
        print(f"📥 Cargando liga {league_id}...")

        fixtures = api.get_fixtures(
            league_id=league_id,
            season=(
                2025 if league_id in [262, 253] else 2024
            ),  # MLS y Liga MX están en temporada 2025
            date_from=today.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d"),
            status="NS",
        )

        if not fixtures:
            print(f"  ⚠️  No hay fixtures para liga {league_id}")
            continue

        try:
            loaded = db_service.upsert_fixtures(fixtures)
            print(f"  ✅ {loaded} fixtures cargados")
            total_loaded += loaded
        except Exception as e:
            print(f"  ❌ Error guardando fixtures: {e}")

    except Exception as e:
        print(f"  ❌ Error cargando liga {league_id}: {e}")

print()
print(f"✅ Total cargado: {total_loaded} fixtures")
