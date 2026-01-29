"""
Team Statistics Calculator
Computes historical statistics for teams from finished fixtures
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
from collections import defaultdict
import statistics
import structlog

logger = structlog.get_logger()


class TeamStatsCalculator:
    """
    Calculates comprehensive team statistics from historical match data
    
    Stats include:
    - Goals scored/conceded averages (home/away split)
    - Over/Under percentages (2.5, 3.5)
    - BTTS (Both Teams Score) rates
    - Clean sheet percentages
    - Form (last N matches)
    - Win/Draw/Loss rates (home/away split)
    """
    
    def __init__(self):
        self._stats_cache: Dict[int, Dict[str, Any]] = {}
        self._cache_loaded = False
    
    def calculate_all_team_stats(
        self,
        fixtures: List[Dict[str, Any]],
        min_matches: int = 5
    ) -> Dict[int, Dict[str, Any]]:
        """
        Calculate statistics for all teams from historical fixtures
        
        Args:
            fixtures: List of finished fixtures from database
            min_matches: Minimum matches required for valid stats
        
        Returns:
            Dict mapping team_id -> stats dict
        """
        # Sort fixtures by date (oldest first)
        fixtures = sorted(fixtures, key=lambda x: x.get('kickoff_time', ''))
        
        # Collect match data per team
        team_matches: Dict[int, List[Dict]] = defaultdict(list)
        team_names: Dict[int, str] = {}
        team_leagues: Dict[int, int] = {}
        
        for fixture in fixtures:
            home_id = fixture['home_team_id']
            away_id = fixture['away_team_id']
            home_score = fixture.get('home_score')
            away_score = fixture.get('away_score')
            
            # Skip if no score
            if home_score is None or away_score is None:
                continue
            
            # Store team info
            team_names[home_id] = fixture['home_team_name']
            team_names[away_id] = fixture['away_team_name']
            team_leagues[home_id] = fixture['league_id']
            team_leagues[away_id] = fixture['league_id']
            
            # Record match for both teams
            match_data = {
                'fixture_id': fixture['id'],
                'date': fixture.get('kickoff_time'),
                'home_team_id': home_id,
                'away_team_id': away_id,
                'home_score': home_score,
                'away_score': away_score,
                'league_id': fixture['league_id']
            }
            
            team_matches[home_id].append(match_data)
            team_matches[away_id].append(match_data)
        
        # Calculate stats for each team
        all_stats = {}
        
        for team_id, matches in team_matches.items():
            if len(matches) < min_matches:
                continue
            
            stats = self._calculate_team_stats(
                team_id=team_id,
                team_name=team_names.get(team_id, 'Unknown'),
                league_id=team_leagues.get(team_id, 0),
                matches=matches
            )
            all_stats[team_id] = stats
        
        self._stats_cache = all_stats
        self._cache_loaded = True
        
        logger.info(
            "team_stats_calculated",
            teams=len(all_stats),
            total_matches=len(fixtures)
        )
        
        return all_stats
    
    def _calculate_team_stats(
        self,
        team_id: int,
        team_name: str,
        league_id: int,
        matches: List[Dict]
    ) -> Dict[str, Any]:
        """Calculate comprehensive stats for a single team"""
        
        # Separate home and away matches
        home_matches = [m for m in matches if m['home_team_id'] == team_id]
        away_matches = [m for m in matches if m['away_team_id'] == team_id]
        
        # Overall stats
        total_matches = len(matches)
        wins = draws = losses = 0
        goals_for = goals_against = 0
        clean_sheets = 0
        btts_count = 0
        over_2_5_count = 0
        over_3_5_count = 0
        
        # Home stats
        home_wins = home_draws = home_losses = 0
        home_gf = home_ga = 0
        home_clean_sheets = 0
        
        # Away stats
        away_wins = away_draws = away_losses = 0
        away_gf = away_ga = 0
        away_clean_sheets = 0
        
        # Form tracking (last 5)
        form_points = []
        form_results = []
        
        for match in matches:
            is_home = match['home_team_id'] == team_id
            home_score = match['home_score']
            away_score = match['away_score']
            total_goals = home_score + away_score
            
            if is_home:
                team_gf, team_ga = home_score, away_score
            else:
                team_gf, team_ga = away_score, home_score
            
            goals_for += team_gf
            goals_against += team_ga
            
            # Result
            if team_gf > team_ga:
                wins += 1
                form_points.append(3)
                form_results.append('W')
                if is_home:
                    home_wins += 1
                else:
                    away_wins += 1
            elif team_gf == team_ga:
                draws += 1
                form_points.append(1)
                form_results.append('D')
                if is_home:
                    home_draws += 1
                else:
                    away_draws += 1
            else:
                losses += 1
                form_points.append(0)
                form_results.append('L')
                if is_home:
                    home_losses += 1
                else:
                    away_losses += 1
            
            # Clean sheet
            if team_ga == 0:
                clean_sheets += 1
                if is_home:
                    home_clean_sheets += 1
                else:
                    away_clean_sheets += 1
            
            # BTTS
            if home_score > 0 and away_score > 0:
                btts_count += 1
            
            # Over/Under
            if total_goals > 2.5:
                over_2_5_count += 1
            if total_goals > 3.5:
                over_3_5_count += 1
            
            # Home/Away goals
            if is_home:
                home_gf += team_gf
                home_ga += team_ga
            else:
                away_gf += team_gf
                away_ga += team_ga
        
        # Calculate form (last 5 matches)
        last_5_points = sum(form_points[-5:]) if len(form_points) >= 5 else sum(form_points)
        last_5_form = ''.join(form_results[-5:]) if len(form_results) >= 5 else ''.join(form_results)
        
        # Calculate streak
        streak = 0
        streak_type = None
        for result in reversed(form_results):
            if streak_type is None:
                streak_type = result
                streak = 1
            elif result == streak_type:
                streak += 1
            else:
                break
        
        n_home = len(home_matches) or 1
        n_away = len(away_matches) or 1
        
        return {
            'team_id': team_id,
            'team_name': team_name,
            'league_id': league_id,
            'total_matches': total_matches,
            
            # Overall
            'wins': wins,
            'draws': draws,
            'losses': losses,
            'win_rate': round(wins / total_matches, 3),
            'draw_rate': round(draws / total_matches, 3),
            'loss_rate': round(losses / total_matches, 3),
            
            # Goals
            'goals_for': goals_for,
            'goals_against': goals_against,
            'goal_diff': goals_for - goals_against,
            'goals_per_game': round(goals_for / total_matches, 2),
            'goals_conceded_per_game': round(goals_against / total_matches, 2),
            
            # Special markets
            'clean_sheet_pct': round(clean_sheets / total_matches, 3),
            'btts_pct': round(btts_count / total_matches, 3),
            'over_2_5_pct': round(over_2_5_count / total_matches, 3),
            'over_3_5_pct': round(over_3_5_count / total_matches, 3),
            
            # Home stats
            'home_matches': n_home,
            'home_win_rate': round(home_wins / n_home, 3),
            'home_goals_per_game': round(home_gf / n_home, 2),
            'home_conceded_per_game': round(home_ga / n_home, 2),
            'home_clean_sheet_pct': round(home_clean_sheets / n_home, 3),
            
            # Away stats
            'away_matches': n_away,
            'away_win_rate': round(away_wins / n_away, 3),
            'away_goals_per_game': round(away_gf / n_away, 2),
            'away_conceded_per_game': round(away_ga / n_away, 2),
            'away_clean_sheet_pct': round(away_clean_sheets / n_away, 3),
            
            # Form
            'form_last_5': last_5_form,
            'form_points_last_5': last_5_points,
            'form_ppg_last_5': round(last_5_points / min(5, len(form_points)), 2) if form_points else 0,
            'current_streak': streak,
            'streak_type': streak_type or 'N/A',
            
            # Calculated at
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def get_team_stats(self, team_id: int) -> Optional[Dict[str, Any]]:
        """Get cached stats for a team"""
        return self._stats_cache.get(team_id)
    
    def get_match_features(
        self,
        home_team_id: int,
        away_team_id: int
    ) -> Dict[str, float]:
        """
        Get prediction features for a match based on team stats
        
        Returns features optimized for ML models:
        - Normalized values (0-1 range where possible)
        - Difference features (home - away)
        """
        home_stats = self._stats_cache.get(home_team_id, {})
        away_stats = self._stats_cache.get(away_team_id, {})
        
        if not home_stats or not away_stats:
            return self._get_default_features()
        
        features = {
            # Strength indicators
            'home_strength': home_stats.get('win_rate', 0.33),
            'away_strength': away_stats.get('win_rate', 0.33),
            'strength_diff': home_stats.get('win_rate', 0.33) - away_stats.get('win_rate', 0.33),
            
            # Goals
            'home_attack': home_stats.get('home_goals_per_game', 1.5),
            'home_defense': home_stats.get('home_conceded_per_game', 1.0),
            'away_attack': away_stats.get('away_goals_per_game', 1.0),
            'away_defense': away_stats.get('away_conceded_per_game', 1.5),
            
            # Expected goals (simple model)
            'expected_home_goals': (home_stats.get('home_goals_per_game', 1.5) + away_stats.get('away_conceded_per_game', 1.5)) / 2,
            'expected_away_goals': (away_stats.get('away_goals_per_game', 1.0) + home_stats.get('home_conceded_per_game', 1.0)) / 2,
            
            # Over/Under indicators
            'home_over_2_5_pct': home_stats.get('over_2_5_pct', 0.5),
            'away_over_2_5_pct': away_stats.get('over_2_5_pct', 0.5),
            'combined_over_2_5': (home_stats.get('over_2_5_pct', 0.5) + away_stats.get('over_2_5_pct', 0.5)) / 2,
            
            # BTTS indicators
            'home_btts_pct': home_stats.get('btts_pct', 0.5),
            'away_btts_pct': away_stats.get('btts_pct', 0.5),
            'combined_btts': (home_stats.get('btts_pct', 0.5) + away_stats.get('btts_pct', 0.5)) / 2,
            
            # Clean sheet (inverse = likely to concede)
            'home_clean_sheet_pct': home_stats.get('home_clean_sheet_pct', 0.3),
            'away_clean_sheet_pct': away_stats.get('away_clean_sheet_pct', 0.2),
            
            # Form
            'home_form_ppg': home_stats.get('form_ppg_last_5', 1.5),
            'away_form_ppg': away_stats.get('form_ppg_last_5', 1.5),
            'form_diff': home_stats.get('form_ppg_last_5', 1.5) - away_stats.get('form_ppg_last_5', 1.5),
            
            # Home advantage
            'home_home_win_rate': home_stats.get('home_win_rate', 0.45),
            'away_away_win_rate': away_stats.get('away_win_rate', 0.30),
            
            # Sample size (confidence indicator)
            'home_matches_played': min(home_stats.get('total_matches', 0) / 100, 1.0),
            'away_matches_played': min(away_stats.get('total_matches', 0) / 100, 1.0),
        }
        
        return features
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default features when no history available"""
        return {
            'home_strength': 0.33,
            'away_strength': 0.33,
            'strength_diff': 0.0,
            'home_attack': 1.5,
            'home_defense': 1.0,
            'away_attack': 1.0,
            'away_defense': 1.5,
            'expected_home_goals': 1.5,
            'expected_away_goals': 1.0,
            'home_over_2_5_pct': 0.5,
            'away_over_2_5_pct': 0.5,
            'combined_over_2_5': 0.5,
            'home_btts_pct': 0.5,
            'away_btts_pct': 0.5,
            'combined_btts': 0.5,
            'home_clean_sheet_pct': 0.3,
            'away_clean_sheet_pct': 0.2,
            'home_form_ppg': 1.5,
            'away_form_ppg': 1.5,
            'form_diff': 0.0,
            'home_home_win_rate': 0.45,
            'away_away_win_rate': 0.30,
            'home_matches_played': 0.0,
            'away_matches_played': 0.0,
        }
    
    def predict_over_under(
        self,
        home_team_id: int,
        away_team_id: int,
        line: float = 2.5
    ) -> Dict[str, float]:
        """
        Predict Over/Under probability based on team stats
        
        Returns probability for over and under
        """
        features = self.get_match_features(home_team_id, away_team_id)
        
        expected_total = features['expected_home_goals'] + features['expected_away_goals']
        
        # Simple Poisson-inspired calculation
        # If expected total > line, over is more likely
        if line == 2.5:
            base_over = features['combined_over_2_5']
        elif line == 3.5:
            home_stats = self._stats_cache.get(home_team_id, {})
            away_stats = self._stats_cache.get(away_team_id, {})
            base_over = (home_stats.get('over_3_5_pct', 0.3) + away_stats.get('over_3_5_pct', 0.3)) / 2
        else:
            # Linear interpolation for other lines
            base_over = max(0.1, min(0.9, 0.5 + (expected_total - line) * 0.15))
        
        # Adjust based on expected goals
        adjustment = (expected_total - line) * 0.1
        over_prob = max(0.1, min(0.9, base_over + adjustment))
        
        return {
            'over': round(over_prob, 3),
            'under': round(1 - over_prob, 3),
            'expected_total_goals': round(expected_total, 2)
        }
    
    def predict_btts(
        self,
        home_team_id: int,
        away_team_id: int
    ) -> Dict[str, float]:
        """
        Predict Both Teams to Score probability
        """
        features = self.get_match_features(home_team_id, away_team_id)
        
        # Combine BTTS rates
        base_btts = features['combined_btts']
        
        # Adjust based on clean sheet rates (high clean sheet = lower BTTS)
        clean_sheet_factor = (features['home_clean_sheet_pct'] + features['away_clean_sheet_pct']) / 2
        btts_prob = base_btts * (1 - clean_sheet_factor * 0.3)
        
        # Ensure bounds
        btts_prob = max(0.2, min(0.85, btts_prob))
        
        return {
            'yes': round(btts_prob, 3),
            'no': round(1 - btts_prob, 3)
        }


# Global instance
team_stats_calculator = TeamStatsCalculator()
