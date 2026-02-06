"""Check available leagues with fixtures in API-Football."""

from datetime import datetime, timedelta

from app.services.apifootball import APIFootballClient

api = APIFootballClient()

# Top leagues to check (first and second divisions)
leagues_to_check = {
    # Europa - Primera División
    39: "Premier League (England)",
    140: "La Liga (Spain)",
    135: "Serie A (Italy)",
    78: "Bundesliga (Germany)",
    61: "Ligue 1 (France)",
    94: "Primeira Liga (Portugal)",
    88: "Eredivisie (Netherlands)",
    203: "Süper Lig (Turkey)",
    144: "Jupiler Pro League (Belgium)",
    88: "Eredivisie (Netherlands)",
    235: "Premier League (Russia)",
    # Europa - Segunda División
    40: "Championship (England)",
    141: "LaLiga 2 (Spain)",
    136: "Serie B (Italy)",
    79: "2. Bundesliga (Germany)",
    62: "Ligue 2 (France)",
    # LATAM - Primera División
    262: "Liga MX (Mexico)",
    71: "Brasileirão Serie A (Brazil)",
    128: "Liga Profesional (Argentina)",
    253: "MLS (USA/Canada)",
    274: "Primera División (Chile)",
    239: "Primera División (Colombia)",
    268: "Primera División (Ecuador)",
    270: "Primera División (Peru)",
    273: "Primera División (Uruguay)",
    271: "Primera División (Venezuela)",
    265: "Superliga (Paraguay)",
    # LATAM - Segunda División
    266: "Liga de Expansión MX (Mexico)",
    72: "Serie B (Brazil)",
    # Asia
    307: "Saudi Pro League",
    188: "J1 League (Japan)",
    292: "K League 1 (South Korea)",
    # Others
    13: "Copa Libertadores",
    11: "Copa Sudamericana",
}

today = datetime.now().date()
end_date = today + timedelta(days=30)

print("=" * 80)
print("CHECKING AVAILABLE LEAGUES WITH FIXTURES (Next 30 days)")
print("=" * 80)

results = []

for league_id, name in leagues_to_check.items():
    try:
        fixtures = api.get_fixtures(
            league_id=league_id,
            season=2025,
            date_from=today.strftime("%Y-%m-%d"),
            date_to=end_date.strftime("%Y-%m-%d"),
            status="NS",
        )

        count = len(fixtures) if fixtures else 0
        results.append((count, league_id, name))

        if count > 0:
            status = "✅"
        else:
            status = "❌"

        print(f"{status} [{league_id:3d}] {name:40s} - {count:3d} fixtures")

    except Exception as e:
        print(f"⚠️  [{league_id:3d}] {name:40s} - ERROR: {str(e)[:50]}")

print("\n" + "=" * 80)
print("TOP 20 LEAGUES BY FIXTURE COUNT")
print("=" * 80)

results.sort(reverse=True)
for i, (count, league_id, name) in enumerate(results[:20], 1):
    if count > 0:
        print(f"{i:2d}. [{league_id:3d}] {name:40s} - {count:3d} fixtures")
