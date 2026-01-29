"""
Feature Engineering for Match Predictions
Extracts and computes features from match and team data
"""
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import statistics
import structlog

logger = structlog.get_logger()


class FeatureEngineer:
    """
    Feature extraction for ML models
    
    Features include:
    - Team form (recent results)
    - Head-to-head history
    - Home/away performance
    - Goals scored/conceded
    - Rest days between matches
    """
    
    def __init__(self):
        self.feature_cache: Dict[str, Any] = {}
    
    def extract_features(
        self,
        fixture: Dict[str, Any],
        home_history: List[Dict] = None,
        away_history: List[Dict] = None,
        h2h_history: List[Dict] = None
    ) -> Dict[str, float]:
        """
        Extract all features for a fixture
        
        Args:
            fixture: Fixture data from database
            home_history: Recent matches for home team
            away_history: Recent matches for away team
            h2h_history: Head-to-head matches between teams
        
        Returns:
            Dict of feature_name -> value
        """
        features = {}
        
        home_history = home_history or []
        away_history = away_history or []
        h2h_history = h2h_history or []
        
        # Basic features
        features['league_id'] = fixture.get('league_id', 0)
        features['is_home'] = 1.0
        
        # Form features (last 5 matches)
        features.update(self._calculate_form_features(
            home_history[:5], 
            fixture['home_team_id'],
            prefix='home'
        ))
        features.update(self._calculate_form_features(
            away_history[:5],
            fixture['away_team_id'],
            prefix='away'
        ))
        
        # Goals features
        features.update(self._calculate_goals_features(
            home_history[:10],
            fixture['home_team_id'],
            prefix='home'
        ))
        features.update(self._calculate_goals_features(
            away_history[:10],
            fixture['away_team_id'],
            prefix='away'
        ))
        
        # H2H features
        features.update(self._calculate_h2h_features(
            h2h_history,
            fixture['home_team_id']
        ))
        
        # Derived features
        features['form_diff'] = features.get('home_form_points', 0) - features.get('away_form_points', 0)
        features['goals_diff'] = features.get('home_goals_scored_avg', 0) - features.get('away_goals_scored_avg', 0)
        
        return features
    
    def _calculate_form_features(
        self,
        matches: List[Dict],
        team_id: int,
        prefix: str
    ) -> Dict[str, float]:
        """Calculate form-based features from recent matches"""
        features = {}
        
        if not matches:
            features[f'{prefix}_form_points'] = 0.0
            features[f'{prefix}_form_wins'] = 0.0
            features[f'{prefix}_form_draws'] = 0.0
            features[f'{prefix}_form_losses'] = 0.0
            features[f'{prefix}_form_streak'] = 0.0
            return features
        
        points = []
        wins = draws = losses = 0
        streak = 0
        last_result = None
        
        for match in matches:
            # Determine if team won/drew/lost
            is_home = match.get('home_team_id') == team_id
            home_score = match.get('home_score', 0) or 0
            away_score = match.get('away_score', 0) or 0
            
            if is_home:
                team_score, opp_score = home_score, away_score
            else:
                team_score, opp_score = away_score, home_score
            
            if team_score > opp_score:
                points.append(3)
                wins += 1
                result = 'W'
            elif team_score == opp_score:
                points.append(1)
                draws += 1
                result = 'D'
            else:
                points.append(0)
                losses += 1
                result = 'L'
            
            # Calculate streak
            if last_result is None:
                last_result = result
                streak = 1
            elif result == last_result:
                streak += 1
            
        n = len(matches)
        features[f'{prefix}_form_points'] = sum(points) / (n * 3) if n > 0 else 0.0
        features[f'{prefix}_form_wins'] = wins / n if n > 0 else 0.0
        features[f'{prefix}_form_draws'] = draws / n if n > 0 else 0.0
        features[f'{prefix}_form_losses'] = losses / n if n > 0 else 0.0
        features[f'{prefix}_form_streak'] = streak * (1 if last_result == 'W' else -1 if last_result == 'L' else 0)
        
        return features
    
    def _calculate_goals_features(
        self,
        matches: List[Dict],
        team_id: int,
        prefix: str
    ) -> Dict[str, float]:
        """Calculate goals-based features"""
        features = {}
        
        if not matches:
            features[f'{prefix}_goals_scored_avg'] = 0.0
            features[f'{prefix}_goals_conceded_avg'] = 0.0
            features[f'{prefix}_clean_sheets'] = 0.0
            features[f'{prefix}_btts_rate'] = 0.0
            features[f'{prefix}_over_2_5_rate'] = 0.0
            return features
        
        scored = []
        conceded = []
        clean_sheets = 0
        btts = 0
        over_2_5 = 0
        
        for match in matches:
            is_home = match.get('home_team_id') == team_id
            home_score = match.get('home_score', 0) or 0
            away_score = match.get('away_score', 0) or 0
            
            if is_home:
                team_scored, team_conceded = home_score, away_score
            else:
                team_scored, team_conceded = away_score, home_score
            
            scored.append(team_scored)
            conceded.append(team_conceded)
            
            if team_conceded == 0:
                clean_sheets += 1
            
            if home_score > 0 and away_score > 0:
                btts += 1
            
            if home_score + away_score > 2.5:
                over_2_5 += 1
        
        n = len(matches)
        features[f'{prefix}_goals_scored_avg'] = statistics.mean(scored) if scored else 0.0
        features[f'{prefix}_goals_conceded_avg'] = statistics.mean(conceded) if conceded else 0.0
        features[f'{prefix}_clean_sheets'] = clean_sheets / n if n > 0 else 0.0
        features[f'{prefix}_btts_rate'] = btts / n if n > 0 else 0.0
        features[f'{prefix}_over_2_5_rate'] = over_2_5 / n if n > 0 else 0.0
        
        return features
    
    def _calculate_h2h_features(
        self,
        h2h_matches: List[Dict],
        home_team_id: int
    ) -> Dict[str, float]:
        """Calculate head-to-head features"""
        features = {}
        
        if not h2h_matches:
            features['h2h_home_wins'] = 0.0
            features['h2h_draws'] = 0.0
            features['h2h_away_wins'] = 0.0
            features['h2h_home_goals_avg'] = 0.0
            features['h2h_total_goals_avg'] = 0.0
            return features
        
        home_wins = draws = away_wins = 0
        home_goals = []
        total_goals = []
        
        for match in h2h_matches:
            home_score = match.get('home_score', 0) or 0
            away_score = match.get('away_score', 0) or 0
            match_home_id = match.get('home_team_id')
            
            total_goals.append(home_score + away_score)
            
            # Track from perspective of current home team
            if match_home_id == home_team_id:
                home_goals.append(home_score)
                if home_score > away_score:
                    home_wins += 1
                elif home_score == away_score:
                    draws += 1
                else:
                    away_wins += 1
            else:
                home_goals.append(away_score)
                if away_score > home_score:
                    home_wins += 1
                elif home_score == away_score:
                    draws += 1
                else:
                    away_wins += 1
        
        n = len(h2h_matches)
        features['h2h_home_wins'] = home_wins / n if n > 0 else 0.0
        features['h2h_draws'] = draws / n if n > 0 else 0.0
        features['h2h_away_wins'] = away_wins / n if n > 0 else 0.0
        features['h2h_home_goals_avg'] = statistics.mean(home_goals) if home_goals else 0.0
        features['h2h_total_goals_avg'] = statistics.mean(total_goals) if total_goals else 0.0
        
        return features
    
    def get_feature_importance(self) -> Dict[str, float]:
        """Return feature importance weights (for model interpretation)"""
        return {
            'form_diff': 0.25,
            'home_form_points': 0.15,
            'away_form_points': 0.15,
            'home_goals_scored_avg': 0.10,
            'away_goals_conceded_avg': 0.10,
            'h2h_home_wins': 0.08,
            'home_clean_sheets': 0.07,
            'away_btts_rate': 0.05,
            'league_id': 0.05,
        }


# Global instance
feature_engineer = FeatureEngineer()
