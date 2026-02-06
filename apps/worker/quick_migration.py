"""
Quick league migration - Direct Supabase connection
"""

import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print(f"❌ Missing credentials:")
    print(f"   SUPABASE_URL: {'✅' if SUPABASE_URL else '❌ MISSING'}")
    print(f"   SUPABASE_SERVICE_ROLE_KEY: {'✅' if SUPABASE_KEY else '❌ MISSING'}")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

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

print(f"🚀 Inserting {len(leagues_data)} leagues to Supabase...")
print()

for league in leagues_data:
    try:
        result = client.table("leagues").upsert(league).execute()
        print(f"✅ {league['name']:<25} ({league['country']:<15}) - ID: {league['id']}")
    except Exception as e:
        print(f"❌ {league['name']:<25}: {e}")

print("\n" + "=" * 60)

# Verify
all_leagues = client.table("leagues").select("*").eq("is_active", True).execute()
print(f"✅ Total active leagues in DB: {len(all_leagues.data)}")

# Count by region
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

print("\nLeagues by region:")
for region, countries in regions.items():
    count = len([l for l in all_leagues.data if l.get("country") in countries])
    if count > 0:
        print(f"  {region:<20}: {count} leagues")

print("\n🎉 Migration complete!")
