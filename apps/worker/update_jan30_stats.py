"""Actualizar fixtures del 30 de enero con estadísticas completas"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from datetime import datetime

from app.services.apifootball import APIFootballClient
from app.services.database import db_service

api = APIFootballClient()

print("Obteniendo fixtures del 30 de enero con estadísticas...")

# Obtener los IDs de fixtures del 30 de enero
fixtures_response = (
    db_service.client.table("fixtures")
    .select("id")
    .gte("kickoff_time", "2026-01-30T00:00:00")
    .lt("kickoff_time", "2026-01-31T00:00:00")
    .execute()
)

fixture_ids = [f["id"] for f in fixtures_response.data]
print(f"Encontrados {len(fixture_ids)} fixtures")

updated = 0
for i, fixture_id in enumerate(fixture_ids, 1):
    print(f"[{i}/{len(fixture_ids)}] Fixture {fixture_id}...", end=" ", flush=True)

    try:
        # Obtener datos completos del fixture
        response = api._request("fixtures", {"id": fixture_id}, cache_ttl=0)

        if not response.get("response"):
            print("❌ Sin datos")
            continue

        fixture = response["response"][0]

        # Extraer estadísticas
        score = fixture.get("score", {})
        teams = fixture.get("teams", {})

        # Obtener estadísticas del partido
        stats_response = api._request("fixtures/statistics", {"fixture": fixture_id}, cache_ttl=0)

        home_stats = {}
        away_stats = {}

        if stats_response.get("response"):
            for stat in stats_response["response"]:
                team_name = stat.get("team", {}).get("name", "")
                stats_data = {s.get("type"): s.get("value") for s in stat.get("statistics", [])}

                if team_name == teams.get("home", {}).get("name"):
                    home_stats = stats_data
                elif team_name == teams.get("away", {}).get("name"):
                    away_stats = stats_data

        # Actualizar fixture
        update_data = {
            "half_time_home_score": score.get("halftime", {}).get("home"),
            "half_time_away_score": score.get("halftime", {}).get("away"),
            "corners_home": home_stats.get("Corner Kicks"),
            "corners_away": away_stats.get("Corner Kicks"),
            "shots_on_target_home": home_stats.get("Shots on Goal"),
            "shots_on_target_away": away_stats.get("Shots on Goal"),
            "offsides_home": home_stats.get("Offsides"),
            "offsides_away": away_stats.get("Offsides"),
        }

        # Calcular tarjetas totales
        yellow_home = home_stats.get("Yellow Cards") or 0
        red_home = home_stats.get("Red Cards") or 0
        yellow_away = away_stats.get("Yellow Cards") or 0
        red_away = away_stats.get("Red Cards") or 0

        update_data["cards_home"] = yellow_home + red_home
        update_data["cards_away"] = yellow_away + red_away

        # Filtrar valores None
        update_data = {k: v for k, v in update_data.items() if v is not None}

        if update_data:
            db_service.client.table("fixtures").update(update_data).eq("id", fixture_id).execute()
            updated += 1
            print(f"✅ {len(update_data)} campos actualizados")
        else:
            print("⚠️ Sin estadísticas")

    except Exception as e:
        print(f"❌ Error: {e}")

print(f"\n✅ {updated}/{len(fixture_ids)} fixtures actualizados con estadísticas completas")
