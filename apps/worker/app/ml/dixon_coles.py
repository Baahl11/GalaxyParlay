"""
Dixon-Coles Model for Football Match Prediction

Based on the 1997 paper "Modelling Association Football Scores and 
Inefficiencies in the Football Betting Market" by Dixon and Coles.

Key improvements over independent Poisson:
1. Correlation adjustment for low-scoring games (0-0, 1-0, 0-1, 1-1)
2. Time-decay weighting for recent matches
3. Attack/Defense strength parameters per team

ENHANCED (v2.0) - Based on 28 Jan 2026 validation:
4. Competition-specific adjustments (cups vs leagues)
5. Draw probability boost for European knockout games
6. Upset factor for away teams in cup competitions
7. Home advantage reduction for neutral/European venues

Reference: http://www.math.ku.dk/~rolf/teaching/thesis/DixonColes.pdf
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from scipy.stats import poisson
import numpy as np
import math
import json
import os
import structlog

logger = structlog.get_logger()

# Path to persist model parameters
MODEL_CACHE_PATH = os.path.join(os.path.dirname(__file__), "dixon_coles_cache.json")

# Competition type mappings (league_id -> type)
# UEFA Champions League = 2, Europa League = 3, Conference League = 848
CUP_COMPETITIONS = {2, 3, 848, 4, 5}  # UCL, UEL, UECL, Euro, World Cup qualifiers
EUROPEAN_LEAGUES = {2, 3, 848}  # European club competitions


class DixonColesModel:
    """
    Dixon-Coles bivariate Poisson model for football predictions.
    
    Predicts:
    - Match outcome probabilities (1X2)
    - Exact score probabilities
    - Over/Under probabilities
    - BTTS probabilities
    
    Enhanced v2.0:
    - Competition-aware adjustments
    - Improved draw predictions for cup games
    - Upset factor for European away teams
    """
    
    def __init__(
        self,
        rho: float = -0.13,  # Low-score correlation adjustment
        home_advantage: float = 0.27,  # Home field advantage
        time_decay_rate: float = 0.0065,  # Decay rate (xi in paper)
        max_goals: int = 10,  # Max goals to consider in probability matrix
        # NEW v2.0 parameters
        draw_boost_cups: float = 0.12,  # Boost draw prob in cup games
        upset_factor_cups: float = 0.08,  # Boost away win prob in cups
        home_adv_reduction_europe: float = 0.35  # Reduce home advantage in Europe
    ):
        self.rho = rho
        self.home_advantage = home_advantage
        self.time_decay_rate = time_decay_rate
        self.max_goals = max_goals
        
        # NEW v2.0 parameters
        self.draw_boost_cups = draw_boost_cups
        self.upset_factor_cups = upset_factor_cups
        self.home_adv_reduction_europe = home_adv_reduction_europe
        
        # Team parameters (attack and defense strengths)
        self.attack_params: Dict[int, float] = {}
        self.defense_params: Dict[int, float] = {}
        self.team_names: Dict[int, str] = {}
        
        # Fitted flag
        self._is_fitted = False
        
        # Try to load cached model on init
        self._load_from_cache()
    
    def _save_to_cache(self) -> None:
        """Persist model parameters to disk."""
        try:
            data = {
                "rho": self.rho,
                "home_advantage": self.home_advantage,
                "attack_params": {str(k): v for k, v in self.attack_params.items()},
                "defense_params": {str(k): v for k, v in self.defense_params.items()},
                "team_names": {str(k): v for k, v in self.team_names.items()},
                "fitted_at": datetime.utcnow().isoformat()
            }
            with open(MODEL_CACHE_PATH, 'w') as f:
                json.dump(data, f)
            logger.info("Dixon-Coles model saved to cache")
        except Exception as e:
            logger.warning("Failed to save Dixon-Coles cache", error=str(e))
    
    def _load_from_cache(self) -> bool:
        """Load model parameters from disk cache."""
        try:
            if not os.path.exists(MODEL_CACHE_PATH):
                return False
            
            with open(MODEL_CACHE_PATH, 'r') as f:
                data = json.load(f)
            
            self.rho = data["rho"]
            self.home_advantage = data["home_advantage"]
            self.attack_params = {int(k): v for k, v in data["attack_params"].items()}
            self.defense_params = {int(k): v for k, v in data["defense_params"].items()}
            self.team_names = {int(k): v for k, v in data["team_names"].items()}
            self._is_fitted = True
            
            logger.info("Dixon-Coles model loaded from cache", 
                       teams=len(self.attack_params),
                       fitted_at=data.get("fitted_at"))
            return True
        except Exception as e:
            logger.warning("Failed to load Dixon-Coles cache", error=str(e))
            return False
    
    def tau(
        self,
        home_goals: int,
        away_goals: int,
        lambda_home: float,
        mu_away: float,
        rho: float
    ) -> float:
        """
        Dixon-Coles adjustment factor for low-scoring games.
        
        Adjusts the independent Poisson probabilities for:
        - 0-0: Slightly more likely
        - 1-1: Slightly more likely  
        - 1-0: Slightly less likely
        - 0-1: Slightly less likely
        
        For other scores, tau = 1 (no adjustment)
        """
        if home_goals == 0 and away_goals == 0:
            return 1 - (lambda_home * mu_away * rho)
        elif home_goals == 0 and away_goals == 1:
            return 1 + (lambda_home * rho)
        elif home_goals == 1 and away_goals == 0:
            return 1 + (mu_away * rho)
        elif home_goals == 1 and away_goals == 1:
            return 1 - rho
        else:
            return 1.0
    
    def time_weight(
        self,
        match_date: datetime,
        current_date: Optional[datetime] = None
    ) -> float:
        """
        Calculate time decay weight for a match.
        
        Uses exponential decay: weight = exp(-xi * days_ago)
        More recent matches have higher weight.
        """
        if current_date is None:
            current_date = datetime.utcnow()
        
        if isinstance(match_date, str):
            match_date = datetime.fromisoformat(match_date.replace('Z', '+00:00'))
        
        # Make both timezone-naive for comparison
        if match_date.tzinfo is not None:
            match_date = match_date.replace(tzinfo=None)
        if current_date.tzinfo is not None:
            current_date = current_date.replace(tzinfo=None)
        
        days_ago = (current_date - match_date).days
        days_ago = max(0, days_ago)  # No negative days
        
        return math.exp(-self.time_decay_rate * days_ago)
    
    def fit(
        self,
        fixtures: List[Dict[str, Any]],
        min_matches: int = 5
    ) -> 'DixonColesModel':
        """
        Fit the Dixon-Coles model to historical match data.
        
        Uses FAST iterative algorithm instead of slow MLE optimization:
        1. Calculate average goals scored/conceded per team
        2. Iteratively adjust attack/defense ratings
        3. Converges in ~10 iterations (< 1 second for 12k matches)
        """
        # Filter valid fixtures with scores
        valid_fixtures = [
            f for f in fixtures
            if f.get('home_score') is not None and f.get('away_score') is not None
        ]
        
        if len(valid_fixtures) < 20:
            logger.warning("Not enough fixtures to fit Dixon-Coles model", count=len(valid_fixtures))
            return self
        
        # Sort by date (oldest first)
        valid_fixtures.sort(key=lambda x: x.get('kickoff_time', ''))
        
        # Collect team information
        teams = set()
        for f in valid_fixtures:
            teams.add(f['home_team_id'])
            teams.add(f['away_team_id'])
            self.team_names[f['home_team_id']] = f['home_team_name']
            self.team_names[f['away_team_id']] = f['away_team_name']
        
        teams = sorted(list(teams))
        
        # Filter teams with minimum matches
        team_match_count = {t: 0 for t in teams}
        for f in valid_fixtures:
            team_match_count[f['home_team_id']] += 1
            team_match_count[f['away_team_id']] += 1
        
        valid_teams = {t for t, c in team_match_count.items() if c >= min_matches}
        valid_fixtures = [
            f for f in valid_fixtures 
            if f['home_team_id'] in valid_teams and f['away_team_id'] in valid_teams
        ]
        
        teams = sorted(list(valid_teams))
        n_teams = len(teams)
        team_to_idx = {team: idx for idx, team in enumerate(teams)}
        
        logger.info("Fitting Dixon-Coles model (fast)", teams=n_teams, fixtures=len(valid_fixtures))
        
        # Calculate time weights
        weights = {}
        for f in valid_fixtures:
            fid = f['id']
            weights[fid] = self.time_weight(f.get('kickoff_time', datetime.utcnow()))
        
        # Calculate league average goals
        total_home_goals = sum(f['home_score'] * weights[f['id']] for f in valid_fixtures)
        total_away_goals = sum(f['away_score'] * weights[f['id']] for f in valid_fixtures)
        total_weight = sum(weights[f['id']] for f in valid_fixtures)
        
        avg_home_goals = total_home_goals / total_weight  # ~1.5
        avg_away_goals = total_away_goals / total_weight  # ~1.2
        avg_goals = (avg_home_goals + avg_away_goals) / 2
        
        # Home advantage from data
        self.home_advantage = math.log(avg_home_goals / avg_away_goals) / 2
        
        logger.info("League averages", 
                   avg_home=round(avg_home_goals, 3), 
                   avg_away=round(avg_away_goals, 3),
                   home_adv=round(self.home_advantage, 4))
        
        # Initialize attack/defense ratings
        attack = {t: 0.0 for t in teams}
        defense = {t: 0.0 for t in teams}
        
        # Iterative update (converges fast)
        for iteration in range(15):
            # Accumulators for each team
            goals_scored = {t: 0.0 for t in teams}
            goals_conceded = {t: 0.0 for t in teams}
            expected_scored = {t: 0.0 for t in teams}
            expected_conceded = {t: 0.0 for t in teams}
            team_weights = {t: 0.0 for t in teams}
            
            for f in valid_fixtures:
                ht, at = f['home_team_id'], f['away_team_id']
                hg, ag = f['home_score'], f['away_score']
                w = weights[f['id']]
                
                # Expected goals based on current ratings
                exp_home = avg_goals * math.exp(
                    self.home_advantage + attack[ht] + defense[at]
                )
                exp_away = avg_goals * math.exp(
                    -self.home_advantage + attack[at] + defense[ht]
                )
                
                # Accumulate weighted actual vs expected
                goals_scored[ht] += w * hg
                goals_scored[at] += w * ag
                goals_conceded[ht] += w * ag
                goals_conceded[at] += w * hg
                
                expected_scored[ht] += w * exp_home
                expected_scored[at] += w * exp_away
                expected_conceded[ht] += w * exp_away
                expected_conceded[at] += w * exp_home
                
                team_weights[ht] += w
                team_weights[at] += w
            
            # Update ratings
            max_change = 0.0
            for t in teams:
                if team_weights[t] > 0:
                    # Attack: log(actual/expected) adjustment
                    if expected_scored[t] > 0:
                        att_adjust = math.log(goals_scored[t] / expected_scored[t])
                    else:
                        att_adjust = 0
                    
                    # Defense: log(actual/expected) adjustment (inverted)
                    if expected_conceded[t] > 0:
                        def_adjust = math.log(goals_conceded[t] / expected_conceded[t])
                    else:
                        def_adjust = 0
                    
                    # Damped update (learning rate 0.5)
                    new_attack = attack[t] + 0.5 * att_adjust
                    new_defense = defense[t] + 0.5 * def_adjust
                    
                    # Clip to reasonable bounds
                    new_attack = max(-1.5, min(1.5, new_attack))
                    new_defense = max(-1.5, min(1.5, new_defense))
                    
                    max_change = max(max_change, abs(new_attack - attack[t]))
                    max_change = max(max_change, abs(new_defense - defense[t]))
                    
                    attack[t] = new_attack
                    defense[t] = new_defense
            
            # Normalize attack to mean 0
            mean_attack = sum(attack.values()) / len(attack)
            attack = {t: v - mean_attack for t, v in attack.items()}
            
            # Early stopping if converged
            if max_change < 0.001:
                logger.info("Converged", iteration=iteration, max_change=round(max_change, 5))
                break
        
        # Store fitted parameters
        self.attack_params = attack
        self.defense_params = defense
        self._is_fitted = True
        
        # Calculate rho from low-scoring games
        low_score_matches = [f for f in valid_fixtures 
                            if f['home_score'] <= 1 and f['away_score'] <= 1]
        if len(low_score_matches) > 100:
            # Count 0-0 and 1-1 draws vs 1-0 and 0-1
            draws_00 = sum(1 for f in low_score_matches if f['home_score'] == 0 and f['away_score'] == 0)
            draws_11 = sum(1 for f in low_score_matches if f['home_score'] == 1 and f['away_score'] == 1)
            wins_10 = sum(1 for f in low_score_matches if f['home_score'] == 1 and f['away_score'] == 0)
            wins_01 = sum(1 for f in low_score_matches if f['home_score'] == 0 and f['away_score'] == 1)
            
            # More 0-0/1-1 than expected = negative rho
            draw_ratio = (draws_00 + draws_11) / max(1, wins_10 + wins_01)
            self.rho = min(0, -0.05 * (draw_ratio - 1))  # Typically around -0.13
            self.rho = max(-0.3, self.rho)
        
        # Save to cache for persistence across restarts
        self._save_to_cache()
        
        logger.info(
            "Dixon-Coles model fitted (fast)",
            home_advantage=round(self.home_advantage, 4),
            rho=round(self.rho, 4),
            teams=n_teams,
            iterations=iteration + 1
        )
        
        return self
    
    def predict_score_probs(
        self,
        home_team_id: int,
        away_team_id: int
    ) -> np.ndarray:
        """
        Calculate probability matrix for all score combinations.
        
        Returns:
            2D array where [i,j] = P(home_goals=i, away_goals=j)
        """
        # Get team parameters (use defaults if not found)
        home_attack = self.attack_params.get(home_team_id, 0.0)
        home_defense = self.defense_params.get(home_team_id, 0.0)
        away_attack = self.attack_params.get(away_team_id, 0.0)
        away_defense = self.defense_params.get(away_team_id, 0.0)
        
        # Calculate expected goals
        lambda_home = np.exp(self.home_advantage + home_attack + away_defense)
        mu_away = np.exp(away_attack + home_defense)
        
        # Clip to reasonable range
        lambda_home = np.clip(lambda_home, 0.1, 5.0)
        mu_away = np.clip(mu_away, 0.1, 5.0)
        
        # Build probability matrix
        prob_matrix = np.zeros((self.max_goals + 1, self.max_goals + 1))
        
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                prob_home = poisson.pmf(i, lambda_home)
                prob_away = poisson.pmf(j, mu_away)
                tau_val = self.tau(i, j, lambda_home, mu_away, self.rho)
                prob_matrix[i, j] = prob_home * prob_away * tau_val
        
        # Normalize
        prob_matrix /= prob_matrix.sum()
        
        return prob_matrix
    
    def predict_match(
        self,
        home_team_id: int,
        away_team_id: int,
        league_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Get full prediction for a match.
        
        Args:
            home_team_id: ID of home team
            away_team_id: ID of away team
            league_id: Optional league ID for competition-specific adjustments
        
        Returns dict with:
        - match_winner: {home_win, draw, away_win}
        - over_under_2_5: {over, under}
        - over_under_3_5: {over, under}
        - btts: {yes, no}
        - expected_goals: {home, away, total}
        - most_likely_score: tuple
        - competition_adjustments: applied adjustments (v2.0)
        """
        # Determine if cup competition
        is_cup = league_id in CUP_COMPETITIONS if league_id else False
        is_european = league_id in EUROPEAN_LEAGUES if league_id else False
        
        # Calculate effective home advantage
        effective_home_adv = self.home_advantage
        if is_european:
            effective_home_adv *= (1 - self.home_adv_reduction_europe)
        
        prob_matrix = self._predict_score_probs_adjusted(
            home_team_id, away_team_id, effective_home_adv
        )
        
        # Match winner probabilities (raw)
        home_win = 0.0
        draw = 0.0
        away_win = 0.0
        
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if i > j:
                    home_win += prob_matrix[i, j]
                elif i == j:
                    draw += prob_matrix[i, j]
                else:
                    away_win += prob_matrix[i, j]
        
        # Apply competition-specific adjustments
        adjustments_applied = []
        
        if is_cup:
            # ADJUSTMENT 1: Boost draw probability in cup games
            # Observation: Draws are underestimated in knockout rounds
            draw_boost = self.draw_boost_cups
            
            # Take from the favorite
            if home_win > away_win:
                home_win -= draw_boost * 0.6
                away_win -= draw_boost * 0.4
            else:
                away_win -= draw_boost * 0.6
                home_win -= draw_boost * 0.4
            
            draw += draw_boost
            adjustments_applied.append(f"draw_boost: +{draw_boost:.1%}")
            
            # ADJUSTMENT 2: Upset factor for away teams in cups
            # Observation: PSG 1-1 Newcastle, Atlético 1-2 Bodo/Glimt
            # Underdog away teams are more motivated in cups
            upset_bonus = self.upset_factor_cups
            
            # Only apply if home is favorite
            if home_win > away_win + 0.15:
                away_win += upset_bonus
                home_win -= upset_bonus
                adjustments_applied.append(f"upset_factor: away +{upset_bonus:.1%}")
        
        # Normalize to ensure sum = 1
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total
        
        # Over/Under 2.5
        over_2_5 = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if i + j > 2:
                    over_2_5 += prob_matrix[i, j]
        
        # Over/Under 3.5
        over_3_5 = 0.0
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                if i + j > 3:
                    over_3_5 += prob_matrix[i, j]
        
        # BTTS (Both Teams To Score)
        btts_yes = 0.0
        for i in range(1, self.max_goals + 1):
            for j in range(1, self.max_goals + 1):
                btts_yes += prob_matrix[i, j]
        
        # Expected goals
        home_attack = self.attack_params.get(home_team_id, 0.0)
        away_defense = self.defense_params.get(away_team_id, 0.0)
        away_attack = self.attack_params.get(away_team_id, 0.0)
        home_defense = self.defense_params.get(home_team_id, 0.0)
        
        exp_home = np.exp(effective_home_adv + home_attack + away_defense)
        exp_away = np.exp(away_attack + home_defense)
        
        # Most likely score
        most_likely_idx = np.unravel_index(np.argmax(prob_matrix), prob_matrix.shape)
        
        return {
            'match_winner': {
                'home_win': round(home_win, 4),
                'draw': round(draw, 4),
                'away_win': round(away_win, 4)
            },
            'over_under_2_5': {
                'over': round(over_2_5, 4),
                'under': round(1 - over_2_5, 4)
            },
            'over_under_3_5': {
                'over': round(over_3_5, 4),
                'under': round(1 - over_3_5, 4)
            },
            'btts': {
                'yes': round(btts_yes, 4),
                'no': round(1 - btts_yes, 4)
            },
            'expected_goals': {
                'home': round(exp_home, 2),
                'away': round(exp_away, 2),
                'total': round(exp_home + exp_away, 2)
            },
            'most_likely_score': {
                'home': int(most_likely_idx[0]),
                'away': int(most_likely_idx[1]),
                'probability': round(prob_matrix[most_likely_idx], 4)
            },
            'model_params': {
                'home_advantage': round(effective_home_adv, 4),
                'rho': round(self.rho, 4),
                'lambda_home': round(exp_home, 4),
                'mu_away': round(exp_away, 4)
            },
            'competition_adjustments': adjustments_applied if adjustments_applied else None,
            'is_cup_competition': is_cup
        }
    
    def _predict_score_probs_adjusted(
        self,
        home_team_id: int,
        away_team_id: int,
        effective_home_adv: float
    ) -> np.ndarray:
        """
        Calculate probability matrix with adjusted home advantage.
        """
        home_attack = self.attack_params.get(home_team_id, 0.0)
        home_defense = self.defense_params.get(home_team_id, 0.0)
        away_attack = self.attack_params.get(away_team_id, 0.0)
        away_defense = self.defense_params.get(away_team_id, 0.0)
        
        # Calculate expected goals with adjusted home advantage
        lambda_home = np.exp(effective_home_adv + home_attack + away_defense)
        mu_away = np.exp(away_attack + home_defense)
        
        # Clip to reasonable range
        lambda_home = np.clip(lambda_home, 0.1, 5.0)
        mu_away = np.clip(mu_away, 0.1, 5.0)
        
        # Build probability matrix
        prob_matrix = np.zeros((self.max_goals + 1, self.max_goals + 1))
        
        for i in range(self.max_goals + 1):
            for j in range(self.max_goals + 1):
                prob_home = poisson.pmf(i, lambda_home)
                prob_away = poisson.pmf(j, mu_away)
                tau_val = self.tau(i, j, lambda_home, mu_away, self.rho)
                prob_matrix[i, j] = prob_home * prob_away * tau_val
        
        # Normalize
        prob_matrix /= prob_matrix.sum()
        
        return prob_matrix
    
    def get_team_ratings(self) -> List[Dict[str, Any]]:
        """Get team attack and defense ratings, sorted by overall strength"""
        ratings = []
        
        for team_id in self.attack_params:
            attack = self.attack_params[team_id]
            defense = self.defense_params.get(team_id, 0.0)
            
            # Overall strength = attack - defense (higher attack, lower defense is better)
            strength = attack - defense
            
            ratings.append({
                'team_id': team_id,
                'team_name': self.team_names.get(team_id, 'Unknown'),
                'attack': round(attack, 4),
                'defense': round(defense, 4),
                'strength': round(strength, 4)
            })
        
        # Sort by strength (descending)
        ratings.sort(key=lambda x: x['strength'], reverse=True)
        
        return ratings
    
    @property
    def is_fitted(self) -> bool:
        return self._is_fitted


# Global instance
dixon_coles_model = DixonColesModel()
