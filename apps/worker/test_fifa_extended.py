"""
FIFA EXTENDED DATABASE TEST
===========================

Tests the expanded FIFA database with 100+ teams and extended player stats
"""

from app.services.fifa_scraper import fifa_scraper
from app.services.fifa_team_database import (
    LEAGUE_AVERAGES,
    get_all_teams_by_league,
    get_team_fifa_stats,
    get_top_teams,
)

print("=" * 80)
print("FIFA EXTENDED DATABASE - 100+ TEAMS TEST")
print("=" * 80)

# Test 1: Top 20 teams globally
print("\n📊 TEST 1: Top 20 Teams by FIFA Rating")
print("-" * 80)

top_teams = get_top_teams(20)
for i, (team_name, stats) in enumerate(top_teams.items(), 1):
    print(
        f"{i:2}. {team_name.replace('-', ' ').title():30} "
        f"Overall: {stats['overall']:2} | "
        f"Attack: {stats['attack']:2} | "
        f"Defense: {stats['defense']:2} | "
        f"Pace: {stats['pace']:2} | "
        f"Value: €{stats['value']}M | "
        f"{stats['league']}"
    )

# Test 2: Premier League complete standings
print("\n\n🏴󠁧󠁢󠁥󠁮󠁧󠁿 TEST 2: Premier League Teams (All 20)")
print("-" * 80)

pl_teams = get_all_teams_by_league("Premier League")
for team_name, stats in sorted(pl_teams.items(), key=lambda x: x[1]["overall"], reverse=True):
    print(
        f"{team_name.replace('-', ' ').title():30} "
        f"Overall: {stats['overall']:2} | "
        f"Attack: {stats['attack']:2} | "
        f"Pace: {stats['pace']:2} | "
        f"Age: {stats['age']:.1f}"
    )

# Test 3: League comparisons
print("\n\n🌍 TEST 3: League Quality Comparison")
print("-" * 80)

for league, averages in sorted(
    LEAGUE_AVERAGES.items(), key=lambda x: x[1]["overall"], reverse=True
):
    teams_count = len(get_all_teams_by_league(league))
    print(
        f"{league:20} | "
        f"Avg Overall: {averages['overall']:.1f} | "
        f"Avg Pace: {averages['pace']:.1f} | "
        f"Avg Physical: {averages['physical']:.1f} | "
        f"Teams: {teams_count}"
    )

# Test 4: Extended player stats for elite teams
print("\n\n⭐ TEST 4: Elite Team Analysis with Extended Stats")
print("-" * 80)

elite_teams = ["Manchester City", "Real Madrid", "Liverpool", "Paris Saint-Germain"]

for team_name in elite_teams:
    ratings = fifa_scraper.get_team_ratings(team_name)
    if ratings:
        print(f"\n{team_name}:")
        print(f"  Overall: {ratings.avg_overall:.1f}")
        print(f"  Attack: {ratings.avg_attack:.1f}")
        print(f"  Defense: {ratings.avg_defense:.1f}")
        print(f"  Pace: {ratings.avg_pace:.1f}")
        print(f"  Physical: {ratings.avg_physical:.1f}")
        print(f"  Dribbling: {ratings.avg_dribbling:.1f}")
        print(f"  Skill Moves: {ratings.avg_skill_moves:.1f}/5 ⭐")
        print(f"  Weak Foot: {ratings.avg_weak_foot:.1f}/5 ⭐")
        print(f"  Avg Age: {ratings.avg_age:.1f} years")
        print(f"  Avg Height: {ratings.avg_height:.0f} cm")
        print(f"  Top Player: {ratings.top_player_rating}")
        print(f"  Star Players (85+): {ratings.star_players_count}")
        print(f"  Squad Value: €{ratings.total_value_millions:.1f}M")

# Test 5: Cross-league comparisons
print("\n\n🆚 TEST 5: Cross-League Match Predictions")
print("-" * 80)

matches = [
    ("Manchester City", "Bayern München"),  # EPL vs Bundesliga
    ("Real Madrid", "Inter"),  # La Liga vs Serie A
    ("Liverpool", "Paris Saint-Germain"),  # EPL vs Ligue 1
    ("Barcelona", "Juventus"),  # La Liga vs Serie A
]

for home, away in matches:
    advantages = fifa_scraper.calculate_match_advantages(home, away)
    print(f"\n{home} vs {away}:")
    print(
        f"  Quality: {advantages['quality_advantage']:+.1f} "
        f"(favors {home if advantages['quality_advantage'] > 0 else away})"
    )
    print(f"  Pace: {advantages['pace_advantage']:+.1f}")
    print(f"  Attack: {advantages['attack_advantage']:+.1f}")
    print(f"  Defense: {advantages['defense_advantage']:+.1f}")
    print(f"  Physical: {advantages['physical_advantage']:+.1f}")

    # Prediction insights
    if abs(advantages["quality_advantage"]) > 4:
        favorite = home if advantages["quality_advantage"] > 0 else away
        print(
            f"  🎯 PREDICTION: {favorite} strong favorite (quality +{abs(advantages['quality_advantage']):.1f})"
        )
    elif abs(advantages["quality_advantage"]) > 2:
        favorite = home if advantages["quality_advantage"] > 0 else away
        print(f"  🎯 PREDICTION: {favorite} slight favorite")
    else:
        print(f"  🎯 PREDICTION: Balanced match")

    if advantages["pace_advantage"] + advantages["attack_advantage"] > 6:
        print(f"  ⚡ High-scoring game likely (fast + attack advantage)")
    elif advantages["defense_advantage"] > 4:
        favorite = home if advantages["defense_advantage"] > 0 else away
        print(f"  🛡️ Low-scoring game likely ({favorite} defensive solidity)")

# Test 6: Lower-league coverage
print("\n\n📉 TEST 6: Coverage Beyond Top 5 Leagues")
print("-" * 80)

other_leagues = ["Eredivisie", "Liga Portugal", "MLS", "Brazilian Serie A", "Saudi Pro League"]

for league in other_leagues:
    teams = get_all_teams_by_league(league)
    if teams:
        avg_overall = sum(t["overall"] for t in teams.values()) / len(teams)
        top_team = max(teams.items(), key=lambda x: x[1]["overall"])
        print(
            f"{league:20} | "
            f"Teams: {len(teams):2} | "
            f"Avg: {avg_overall:.1f} | "
            f"Best: {top_team[0].replace('-', ' ').title()} ({top_team[1]['overall']})"
        )

# Test 7: Unknown team fallback
print("\n\n❓ TEST 7: Unknown Team Handling")
print("-" * 80)

unknown_teams = ["FC Unknown United", "Random City FC", "Lower League FC"]

for team_name in unknown_teams:
    stats = get_team_fifa_stats(team_name)
    print(
        f"{team_name:25} → Default stats: Overall {stats['overall']} "
        f"(ensures all teams get predictions)"
    )

print("\n\n" + "=" * 80)
print("✅ EXTENDED DATABASE TEST COMPLETE")
print("=" * 80)

print(
    f"""
📊 DATABASE SUMMARY:
-------------------
• 100+ teams covered across multiple leagues
• Premier League: 20/20 teams (100% coverage)
• La Liga: 10/20 teams (50% coverage, top teams)
• Bundesliga: 8/18 teams (44% coverage)
• Serie A: 8/20 teams (40% coverage)
• Ligue 1: 5/18 teams (28% coverage)
• Other leagues: Eredivisie, Liga Portugal, MLS, Brazil, Saudi

🆕 EXTENDED PLAYER STATS:
-------------------------
• Overall, Pace, Shooting, Passing, Dribbling, Defending, Physical
• NEW: Age, Height, Weight (realistic distributions)
• NEW: Weak Foot (1-5 stars)
• NEW: Skill Moves (1-5 stars)
• NEW: Work Rate (H/H, M/M, etc.)
• NEW: Preferred Foot
• NEW: Market Value (calculated from overall + age)

📈 TEAM AGGREGATIONS:
---------------------
• Avg Overall, Attack, Defense ratings
• Avg Pace, Physical, Skill stats
• NEW: Avg Age (squad maturity)
• NEW: Avg Height (aerial threat)
• NEW: Avg Skill Moves (technical quality)
• NEW: Total Squad Value
• NEW: Star Players Count (85+ rating)

💡 USE CASES UNLOCKED:
----------------------
1. Age-based predictions (young vs experienced teams)
2. Height advantage (set pieces, aerial duels)
3. Technical quality (skill moves for possession play)
4. Squad value comparisons (financial power)
5. Star player impact (teams with multiple 85+ players)

🔮 FUTURE ENHANCEMENTS:
-----------------------
• Real-time scraping from SOFIFA.com (when needed)
• Player-specific analysis (top scorers, playmakers)
• Formation analysis (4-3-3 vs 4-4-2 matchups)
• Injury/suspension impact
• Manager tactics integration
"""
)
