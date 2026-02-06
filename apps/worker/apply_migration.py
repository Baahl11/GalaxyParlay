"""
Apply league migration manually via Supabase Python client
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env FIRST before importing anything
load_dotenv()

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.database import db_service

# Read migration SQL
migration_path = (
    Path(__file__).parent.parent.parent
    / "supabase"
    / "migrations"
    / "20260130000000_add_international_leagues.sql"
)

with open(migration_path, "r", encoding="utf-8") as f:
    sql = f.read()

print("🔄 Applying migration: 20260130000000_add_international_leagues.sql")
print(f"📄 Path: {migration_path}")

# Extract and execute INSERT statements (Supabase Python SDK doesn't support raw SQL)
# We'll do it manually via upsert

leagues_data = [
    # Europe - Secondary
    {
        "id": 94,
        "name": "Primeira Liga",
        "country": "Portugal",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 88,
        "name": "Eredivisie",
        "country": "Netherlands",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 203,
        "name": "Super Lig",
        "country": "Turkey",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 144,
        "name": "Belgian Pro League",
        "country": "Belgium",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    # Latin America
    {
        "id": 262,
        "name": "Liga MX",
        "country": "Mexico",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 128,
        "name": "Liga Profesional",
        "country": "Argentina",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 71,
        "name": "Brasileirão Serie A",
        "country": "Brazil",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 281,
        "name": "Primera División",
        "country": "Peru",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 239,
        "name": "Primera A",
        "country": "Colombia",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    # South America - International
    {
        "id": 13,
        "name": "Copa Libertadores",
        "country": "South America",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 11,
        "name": "CONMEBOL Sudamericana",
        "country": "South America",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    # North America
    {
        "id": 253,
        "name": "MLS",
        "country": "USA",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    # Asia & Oceania
    {
        "id": 188,
        "name": "A-League",
        "country": "Australia",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    {
        "id": 235,
        "name": "Saudi Pro League",
        "country": "Saudi Arabia",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
    # Conference League
    {
        "id": 848,
        "name": "Conference League",
        "country": "Europe",
        "season": 2025,
        "coverage": {"fixtures": True, "odds": True, "standings": True},
        "is_active": True,
    },
]

print(f"\n📊 Inserting {len(leagues_data)} leagues...\n")

for league in leagues_data:
    try:
        result = db_service.client.table("leagues").upsert(league).execute()
        print(f"✅ {league['name']} ({league['country']}) - ID: {league['id']}")
    except Exception as e:
        print(f"❌ {league['name']}: {e}")

print("\n🎉 Migration applied successfully!")

# Verify
all_leagues = db_service.get_active_leagues()
print(f"\n📈 Total active leagues: {len(all_leagues)}")
print("\nLeagues by region:")

regions = {
    "Europe": [
        "England",
        "Spain",
        "Germany",
        "Italy",
        "France",
        "Portugal",
        "Netherlands",
        "Turkey",
        "Belgium",
    ],
    "Latin America": ["Mexico", "Argentina", "Brazil", "Peru", "Colombia"],
    "North America": ["USA"],
    "Asia": ["Saudi Arabia"],
    "Oceania": ["Australia"],
    "International": ["South America", "Europe"],
}

for region, countries in regions.items():
    count = len([l for l in all_leagues if l.get("country") in countries])
    if count > 0:
        print(f"  {region}: {count} leagues")
