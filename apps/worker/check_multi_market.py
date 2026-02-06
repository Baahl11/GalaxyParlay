"""Check multi-market prediction structure from API."""

import json

from app.services.database import DatabaseService

db = DatabaseService()

# Get a fixture for Marseille vs Rennes (Coupe de France)
fixtures = (
    db.client.table("fixtures")
    .select("id, home_team_name, away_team_name, home_team_id, away_team_id, league_id")
    .eq("status", "NS")
    .limit(10)
    .execute()
)

print("Available fixtures:")
for f in fixtures.data:
    print(f"  {f['id']}: {f['home_team_name']} vs {f['away_team_name']} (League {f['league_id']})")

# Use first fixture
fixture = fixtures.data[0]
fixture_id = fixture["id"]
home_team_id = fixture["home_team_id"]
away_team_id = fixture["away_team_id"]

print(f"\nTesting: {fixture['home_team_name']} vs {fixture['away_team_name']}")
print(f"Home ID: {home_team_id}, Away ID: {away_team_id}")

# Now call the predictor directly
from app.ml.multi_market_predictor import multi_market_predictor

predictions = multi_market_predictor.predict_all_markets(
    home_team_id=home_team_id,
    away_team_id=away_team_id,
)

print("\n=== PREDICTION STRUCTURE ===")
for key in predictions:
    val = predictions[key]
    if isinstance(val, dict):
        subkeys = list(val.keys())
        print(f"\n{key}: {len(subkeys)} items")
        for sk in subkeys[:3]:
            print(f"  - {sk}: {val[sk]}")
        if len(subkeys) > 3:
            print(f"  ... and {len(subkeys) - 3} more")
    else:
        print(f"\n{key}: {val}")
