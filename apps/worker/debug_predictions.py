"""Debug script to inspect prediction structure"""

from app.ml.predictor import MatchPredictor
from app.services.database import db_service

# Fetch one fixture
fixtures = db_service.client.table("fixtures").select("*").eq("status", "FT").limit(1).execute()

if fixtures.data:
    fixture = fixtures.data[0]
    print(f"\n===FIXTURE {fixture['id']}===")
    print(f"{fixture['home_team_name']} vs {fixture['away_team_name']}")
    print(f"Score: {fixture.get('home_score')} - {fixture.get('away_score')}")

    # Get predictions
    predictor = MatchPredictor()
    predictor.use_live_xg = False  # Disable API calls for speed

    predictions = predictor.predict_fixture(fixture, include_all_markets=True)

    print(f"\n===PREDICTIONS ({len(predictions)})===")
    for pred in predictions[:5]:  # Show first 5
        print(f"\nMarket: {pred.get('market_key')}")
        print(f"Prediction: {pred.get('prediction')}")
        print(f"Confidence: {pred.get('confidence_score')}")
        print(f"Type: {type(pred.get('prediction'))}")
