"""
Multi-Market Predictor
Predicts multiple betting markets beyond just 1X2

Markets covered:
1. Match Winner (1X2) - Already in Dixon-Coles
2. Over/Under Goals (0.5, 1.5, 2.5, 3.5, 4.5, 5.5)
3. BTTS (Both Teams To Score)
4. Team Goals Over/Under
5. Corners (Total, Team, First Half)
6. Cards (Total, Team)
7. Shots on Target
8. Shots Total
9. Offsides (Total, Team)
10. Exact Score
11. Half-Time/Full-Time
12. First/Last Goal

Uses historical team statistics for predictions.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from scipy.stats import poisson, nbinom
import numpy as np
import math
import structlog

logger = structlog.get_logger()


class TeamStats:
    """Container for team statistics"""
    
    def __init__(self, stats_data: Optional[Dict] = None):
        if stats_data:
            self._parse_stats(stats_data)
        else:
            self._set_defaults()
    
    def _parse_stats(self, data: Dict):
        """Parse API-Football team statistics format"""
        try:
            # Goals
            goals = data.get('goals', {})
            self.goals_scored_avg = goals.get('for', {}).get('average', {}).get('total', 1.5)
            self.goals_conceded_avg = goals.get('against', {}).get('average', {}).get('total', 1.2)
            self.goals_scored_home = goals.get('for', {}).get('average', {}).get('home', 1.7)
            self.goals_scored_away = goals.get('for', {}).get('average', {}).get('away', 1.3)
            self.goals_conceded_home = goals.get('against', {}).get('average', {}).get('home', 1.0)
            self.goals_conceded_away = goals.get('against', {}).get('average', {}).get('away', 1.4)
            
            # Clean sheets
            clean_sheets = data.get('clean_sheet', {})
            self.clean_sheets_home = clean_sheets.get('home', 0)
            self.clean_sheets_away = clean_sheets.get('away', 0)
            self.clean_sheets_total = clean_sheets.get('total', 0)
            
            # Failed to score
            failed = data.get('failed_to_score', {})
            self.failed_to_score_home = failed.get('home', 0)
            self.failed_to_score_away = failed.get('away', 0)
            
            # Cards
            cards = data.get('cards', {})
            yellow = cards.get('yellow', {})
            red = cards.get('red', {})
            
            # Sum cards across all time periods
            self.yellow_cards_avg = self._sum_card_periods(yellow) / max(1, data.get('fixtures', {}).get('played', {}).get('total', 1))
            self.red_cards_avg = self._sum_card_periods(red) / max(1, data.get('fixtures', {}).get('played', {}).get('total', 1))
            
            # Fixtures played
            fixtures = data.get('fixtures', {}).get('played', {})
            self.matches_played = fixtures.get('total', 0)
            self.matches_home = fixtures.get('home', 0)
            self.matches_away = fixtures.get('away', 0)
            
        except Exception as e:
            logger.warning("Error parsing team stats, using defaults", error=str(e))
            self._set_defaults()
    
    def _sum_card_periods(self, card_data: Dict) -> int:
        """Sum cards across all time periods (0-15, 16-30, etc.)"""
        total = 0
        for period, data in card_data.items():
            if isinstance(data, dict):
                total += data.get('total', 0) or 0
        return total
    
    def _set_defaults(self):
        """Set league average defaults"""
        self.goals_scored_avg = 1.4
        self.goals_conceded_avg = 1.3
        self.goals_scored_home = 1.6
        self.goals_scored_away = 1.2
        self.goals_conceded_home = 1.1
        self.goals_conceded_away = 1.5
        self.clean_sheets_home = 3
        self.clean_sheets_away = 2
        self.clean_sheets_total = 5
        self.failed_to_score_home = 2
        self.failed_to_score_away = 3
        self.yellow_cards_avg = 1.8
        self.red_cards_avg = 0.05
        self.matches_played = 15
        self.matches_home = 8
        self.matches_away = 7
        
        # Corners defaults (league average)
        self.corners_for_avg = 5.2
        self.corners_against_avg = 4.8
        
        # Shots defaults
        self.shots_avg = 12.5
        self.shots_on_target_avg = 4.5
        
        # Offsides defaults
        self.offsides_avg = 2.3
        self.offsides_home_avg = 2.5
        self.offsides_away_avg = 2.1


class MultiMarketPredictor:
    """
    Predicts multiple betting markets using team statistics.
    
    Uses Poisson distribution for count-based markets (goals, corners, cards)
    and probability calculations for binary markets (BTTS, clean sheet).
    """
    
    def __init__(self):
        self.team_stats_cache: Dict[int, TeamStats] = {}
        
        # League average constants
        self.league_avg_goals = 2.7
        self.league_avg_corners = 10.5
        self.league_avg_cards = 3.5
        self.league_avg_shots = 25.0
        self.league_avg_shots_on_target = 9.0
        self.league_avg_offsides = 4.5
        
        # Home advantage factors
        self.home_advantage_goals = 1.15
        self.home_advantage_corners = 1.10
        self.home_advantage_shots = 1.12
        self.home_advantage_offsides = 1.08
    
    def set_team_stats(self, team_id: int, stats: TeamStats):
        """Cache team statistics"""
        self.team_stats_cache[team_id] = stats
    
    def get_team_stats(self, team_id: int) -> TeamStats:
        """Get cached team stats or return defaults"""
        return self.team_stats_cache.get(team_id, TeamStats())
    
    def predict_all_markets(
        self,
        home_team_id: int,
        away_team_id: int,
        home_xg: float = None,
        away_xg: float = None,
        is_cup: bool = False
    ) -> Dict[str, Any]:
        """
        Predict all available markets for a fixture.
        
        Args:
            home_team_id: Home team ID
            away_team_id: Away team ID  
            home_xg: Expected goals for home (from Dixon-Coles if available)
            away_xg: Expected goals for away
            is_cup: Whether this is a cup competition
            
        Returns:
            Dict with predictions for all markets
        """
        home_stats = self.get_team_stats(home_team_id)
        away_stats = self.get_team_stats(away_team_id)
        
        # Use provided xG or calculate from stats
        if home_xg is None:
            home_xg = (home_stats.goals_scored_home + away_stats.goals_conceded_away) / 2
            home_xg *= self.home_advantage_goals
        
        if away_xg is None:
            away_xg = (away_stats.goals_scored_away + home_stats.goals_conceded_home) / 2
        
        total_xg = home_xg + away_xg
        
        # Build predictions
        predictions = {
            # Over/Under Goals
            'over_under': self._predict_over_under_goals(home_xg, away_xg),
            
            # Team Goals Over/Under
            'team_goals': self._predict_team_goals(home_xg, away_xg),
            
            # BTTS
            'btts': self._predict_btts(home_xg, away_xg, home_stats, away_stats),
            
            # Corners
            'corners': self._predict_corners(home_stats, away_stats),
            
            # Cards
            'cards': self._predict_cards(home_stats, away_stats, is_cup),
            
            # Shots
            'shots': self._predict_shots(home_stats, away_stats),
            
            # Offsides
            'offsides': self._predict_offsides(home_stats, away_stats),
            
            # Exact Scores (top 10 most likely)
            'exact_scores': self._predict_exact_scores(home_xg, away_xg),
            
            # Half-Time Results
            'half_time': self._predict_half_time(home_xg, away_xg),
            
            # Expected values
            'expected': {
                'home_goals': round(home_xg, 2),
                'away_goals': round(away_xg, 2),
                'total_goals': round(total_xg, 2),
            }
        }
        
        return predictions
    
    def _predict_over_under_goals(
        self,
        home_xg: float,
        away_xg: float
    ) -> Dict[str, Dict[str, float]]:
        """Predict Over/Under for various goal lines"""
        total_xg = home_xg + away_xg
        
        lines = [0.5, 1.5, 2.5, 3.5, 4.5, 5.5]
        results = {}
        
        for line in lines:
            # P(Total > line) = 1 - P(Total <= floor(line))
            under_prob = 0.0
            for goals in range(int(line) + 1):
                # Convolution of two Poissons
                for h in range(goals + 1):
                    a = goals - h
                    p_h = poisson.pmf(h, home_xg)
                    p_a = poisson.pmf(a, away_xg)
                    under_prob += p_h * p_a
            
            over_prob = 1 - under_prob
            
            key = f"over_under_{str(line).replace('.', '_')}"
            results[key] = {
                'over': round(over_prob, 4),
                'under': round(under_prob, 4),
                'line': line
            }
        
        return results
    
    def _predict_team_goals(
        self,
        home_xg: float,
        away_xg: float
    ) -> Dict[str, Dict[str, float]]:
        """Predict Over/Under for each team's goals"""
        results = {}
        
        for team, xg in [('home', home_xg), ('away', away_xg)]:
            for line in [0.5, 1.5, 2.5]:
                under_prob = sum(poisson.pmf(g, xg) for g in range(int(line) + 1))
                over_prob = 1 - under_prob
                
                key = f"{team}_over_{str(line).replace('.', '_')}"
                results[key] = {
                    'over': round(over_prob, 4),
                    'under': round(under_prob, 4),
                    'team': team,
                    'line': line
                }
        
        return results
    
    def _predict_btts(
        self,
        home_xg: float,
        away_xg: float,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> Dict[str, float]:
        """Predict Both Teams To Score"""
        # P(BTTS) = P(Home > 0) * P(Away > 0)
        p_home_scores = 1 - poisson.pmf(0, home_xg)
        p_away_scores = 1 - poisson.pmf(0, away_xg)
        
        btts_yes = p_home_scores * p_away_scores
        
        # Adjust based on clean sheet history
        home_cs_rate = home_stats.clean_sheets_home / max(1, home_stats.matches_home)
        away_cs_rate = away_stats.clean_sheets_away / max(1, away_stats.matches_away)
        
        # Blend Poisson calculation with historical clean sheet rate
        adjustment = ((1 - home_cs_rate) + (1 - away_cs_rate)) / 2
        btts_yes = btts_yes * 0.7 + (adjustment * btts_yes) * 0.3
        
        return {
            'yes': round(btts_yes, 4),
            'no': round(1 - btts_yes, 4)
        }
    
    def _predict_corners(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> Dict[str, Any]:
        """Predict corner markets"""
        # Expected corners
        home_corners = getattr(home_stats, 'corners_for_avg', 5.2) * self.home_advantage_corners
        away_corners = getattr(away_stats, 'corners_for_avg', 4.8)
        total_corners = home_corners + away_corners
        
        results = {
            'expected': {
                'home': round(home_corners, 1),
                'away': round(away_corners, 1),
                'total': round(total_corners, 1)
            }
        }
        
        # Total corners over/under
        for line in [7.5, 8.5, 9.5, 10.5, 11.5, 12.5]:
            under_prob = sum(poisson.pmf(c, total_corners) for c in range(int(line) + 1))
            over_prob = 1 - under_prob
            
            key = f"total_over_{str(line).replace('.', '_')}"
            results[key] = {
                'over': round(over_prob, 4),
                'under': round(under_prob, 4)
            }
        
        # Team corners over/under
        for team, xc in [('home', home_corners), ('away', away_corners)]:
            for line in [3.5, 4.5, 5.5, 6.5]:
                under_prob = sum(poisson.pmf(c, xc) for c in range(int(line) + 1))
                results[f"{team}_over_{str(line).replace('.', '_')}"] = {
                    'over': round(1 - under_prob, 4),
                    'under': round(under_prob, 4)
                }
        
        return results
    
    def _predict_cards(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats,
        is_cup: bool = False
    ) -> Dict[str, Any]:
        """Predict card markets"""
        # Base expected cards
        home_cards = home_stats.yellow_cards_avg
        away_cards = away_stats.yellow_cards_avg
        
        # Cup matches tend to have more cards
        if is_cup:
            home_cards *= 1.15
            away_cards *= 1.15
        
        total_cards = home_cards + away_cards
        
        results = {
            'expected': {
                'home_yellow': round(home_cards, 2),
                'away_yellow': round(away_cards, 2),
                'total_yellow': round(total_cards, 2)
            }
        }
        
        # Total cards over/under
        for line in [2.5, 3.5, 4.5, 5.5, 6.5]:
            under_prob = sum(poisson.pmf(c, total_cards) for c in range(int(line) + 1))
            results[f"total_over_{str(line).replace('.', '_')}"] = {
                'over': round(1 - under_prob, 4),
                'under': round(under_prob, 4)
            }
        
        return results
    
    def _predict_shots(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> Dict[str, Any]:
        """Predict shots and shots on target"""
        home_shots = getattr(home_stats, 'shots_avg', 12.5) * self.home_advantage_shots
        away_shots = getattr(away_stats, 'shots_avg', 11.0)
        home_sot = getattr(home_stats, 'shots_on_target_avg', 4.5) * self.home_advantage_shots
        away_sot = getattr(away_stats, 'shots_on_target_avg', 4.0)
        
        total_shots = home_shots + away_shots
        total_sot = home_sot + away_sot
        
        results = {
            'expected': {
                'home_shots': round(home_shots, 1),
                'away_shots': round(away_shots, 1),
                'total_shots': round(total_shots, 1),
                'home_shots_on_target': round(home_sot, 1),
                'away_shots_on_target': round(away_sot, 1),
                'total_shots_on_target': round(total_sot, 1)
            }
        }
        
        # Shots on target over/under
        for line in [6.5, 7.5, 8.5, 9.5, 10.5]:
            under_prob = sum(poisson.pmf(s, total_sot) for s in range(int(line) + 1))
            results[f"sot_over_{str(line).replace('.', '_')}"] = {
                'over': round(1 - under_prob, 4),
                'under': round(under_prob, 4)
            }
        
        return results
    
    def _predict_exact_scores(
        self,
        home_xg: float,
        away_xg: float,
        max_goals: int = 6
    ) -> List[Dict[str, Any]]:
        """Get most likely exact scores"""
        scores = []
        
        for h in range(max_goals + 1):
            for a in range(max_goals + 1):
                prob = poisson.pmf(h, home_xg) * poisson.pmf(a, away_xg)
                scores.append({
                    'home': h,
                    'away': a,
                    'score': f"{h}-{a}",
                    'probability': round(prob, 4)
                })
        
        # Sort by probability and return top 10
        scores.sort(key=lambda x: x['probability'], reverse=True)
        return scores[:10]
    
    def _predict_half_time(
        self,
        home_xg: float,
        away_xg: float
    ) -> Dict[str, float]:
        """Predict half-time result"""
        # Assume goals are roughly evenly distributed
        ht_home_xg = home_xg * 0.45
        ht_away_xg = away_xg * 0.45
        
        ht_home = 0
        ht_draw = 0
        ht_away = 0
        
        for h in range(6):
            for a in range(6):
                prob = poisson.pmf(h, ht_home_xg) * poisson.pmf(a, ht_away_xg)
                if h > a:
                    ht_home += prob
                elif h == a:
                    ht_draw += prob
                else:
                    ht_away += prob
        
        return {
            'home': round(ht_home, 4),
            'draw': round(ht_draw, 4),
            'away': round(ht_away, 4)
        }
    
    def _predict_offsides(
        self,
        home_stats: TeamStats,
        away_stats: TeamStats
    ) -> Dict[str, Any]:
        """
        Predict offsides markets
        
        Offsides correlate with attacking play and possession.
        Teams that attack more and play high lines tend to get more offsides.
        """
        # Expected offsides (league average ~2.3 per team)
        home_offsides = getattr(home_stats, 'offsides_home_avg', 2.5) * self.home_advantage_offsides
        away_offsides = getattr(away_stats, 'offsides_away_avg', 2.1)
        total_offsides = home_offsides + away_offsides
        
        results = {
            'expected': {
                'home': round(home_offsides, 1),
                'away': round(away_offsides, 1),
                'total': round(total_offsides, 1)
            }
        }
        
        # Total offsides over/under (common lines: 3.5, 4.5, 5.5)
        for line in [3.5, 4.5, 5.5, 6.5]:
            under_prob = sum(poisson.pmf(o, total_offsides) for o in range(int(line) + 1))
            over_prob = 1 - under_prob
            
            key = f"total_over_{str(line).replace('.', '_')}"
            results[key] = {
                'over': round(over_prob, 4),
                'under': round(under_prob, 4),
                'line': line
            }
        
        # Team offsides over/under
        for team, xo in [('home', home_offsides), ('away', away_offsides)]:
            for line in [1.5, 2.5, 3.5]:
                under_prob = sum(poisson.pmf(o, xo) for o in range(int(line) + 1))
                results[f"{team}_over_{str(line).replace('.', '_')}"] = {
                    'over': round(1 - under_prob, 4),
                    'under': round(under_prob, 4),
                    'team': team,
                    'line': line
                }
        
        return results


# Global instance
multi_market_predictor = MultiMarketPredictor()
