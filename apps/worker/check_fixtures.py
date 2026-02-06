from app.services.database import db_service

# Check fixtures in database
fixtures_ft = db_service.get_fixtures(status="FT", limit=10)
print(f"FT fixtures: {len(fixtures_ft)}")

all_fixtures = db_service.get_fixtures(limit=10)
print(f"All fixtures: {len(all_fixtures)}")

print("\nFirst 5 fixtures:")
for f in all_fixtures[:5]:
    print(f"{f.get('id')} - {f.get('status')} - {f.get('kickoff_time')}")
