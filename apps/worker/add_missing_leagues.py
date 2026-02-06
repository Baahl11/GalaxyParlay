"""Add missing leagues to database."""

import sys

sys.path.insert(0, str(__file__).rsplit("\\", 1)[0])

from app.services.database import db_service

# Ligas/copas que faltan en la base de datos
new_leagues = [
    {"id": 48, "name": "FA Cup", "country": "England", "season": 2025},
    {"id": 66, "name": "Coupe de France", "country": "France", "season": 2025},
    {"id": 81, "name": "DFB Pokal", "country": "Germany", "season": 2025},
    {"id": 137, "name": "Coppa Italia", "country": "Italy", "season": 2025},
    {"id": 143, "name": "Copa del Rey", "country": "Spain", "season": 2025},
    {"id": 307, "name": "Saudi Pro League (307)", "country": "Saudi Arabia", "season": 2025},
]

print(f"Agregando {len(new_leagues)} ligas a la base de datos...")

for league in new_leagues:
    try:
        result = (
            db_service.client.table("leagues")
            .insert(
                {
                    "id": league["id"],
                    "name": league["name"],
                    "country": league["country"],
                    "season": league["season"],
                    "coverage": {},
                    "is_active": True,
                }
            )
            .execute()
        )
        print(f"[OK] {league['name']} (ID {league['id']}) agregada")
    except Exception as e:
        print(f"[ERROR] {league['name']}: {e}")

print("\nListo! Ahora puedes volver a ejecutar load_next_week.py")
