"""Check what predictions are being generated."""

import json

from app.services.database import DatabaseService

db = DatabaseService()

# Get a fixture
fixtures = (
    db.client.table("fixtures")
    .select("id, home_team_name, away_team_name")
    .eq("status", "NS")
    .limit(1)
    .execute()
)

if not fixtures.data:
    print("No fixtures found")
    exit()

fixture_id = fixtures.data[0]["id"]
print(
    f"Fixture: {fixtures.data[0]['home_team_name']} vs {fixtures.data[0]['away_team_name']} (ID: {fixture_id})"
)

# Get prediction from database
pred_result = (
    db.client.table("model_predictions").select("*").eq("fixture_id", fixture_id).limit(5).execute()
)

print(f"\nPredictions in DB: {len(pred_result.data)}")
for p in pred_result.data:
    print(f"  - {p['market_key']}: {p['prediction']}")

# Check multi-market predictions table
print("\n=== Checking multi_market_predictions table ===")
multi_pred = (
    db.client.table("multi_market_predictions")
    .select("*")
    .eq("fixture_id", fixture_id)
    .limit(1)
    .execute()
)

if multi_pred.data:
    pred = multi_pred.data[0]["predictions"]
    print(f"Found multi-market prediction")
    print(f"Top-level keys: {list(pred.keys()) if isinstance(pred, dict) else type(pred)}")

    if isinstance(pred, dict):
        for key in ["over_under", "team_goals", "btts", "corners", "cards", "shots", "offsides"]:
            if key in pred:
                val = pred[key]
                if isinstance(val, dict):
                    print(f"\n{key}: {list(val.keys())[:5]}...")
                else:
                    print(f"\n{key}: {val}")
            else:
                print(f"\n{key}: MISSING!")
else:
    print("No multi-market prediction found")
