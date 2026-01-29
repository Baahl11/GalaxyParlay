"""
Elo Rating System for Football Teams
Based on FiveThirtyEight's Soccer Power Index methodology
"""
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import math
import structlog

logger = structlog.get_logger()

# Default Elo ratings by league tier
DEFAULT_RATINGS = {
    # Tier 1 - Top 5 leagues
    39: 1600,   # Premier League
    140: 1580,  # La Liga
    78: 1560,   # Bundesliga
    135: 1540,  # Serie A
    61: 1520,   # Ligue 1
    # Tier 2
    94: 1450,   # Primeira Liga
    88: 1440,   # Eredivisie
    203: 1420,  # Süper Lig
    # European competitions
    2: 1650,    # Champions League
    3: 1550,    # Europa League
}

# Top team bonuses (based on historical performance)
TOP_TEAM_BONUSES = {
    # Premier League
    50: 120,   # Manchester City
    40: 100,   # Liverpool
    42: 90,    # Arsenal
    33: 70,    # Manchester United
    49: 60,    # Chelsea
    47: 50,    # Tottenham
    # La Liga
    541: 130,  # Real Madrid
    529: 120,  # Barcelona
    530: 130,  # Real Madrid (alt id)
    532: 70,   # Atletico Madrid
    # Bundesliga
    157: 110,  # Bayern Munich
    165: 60,   # Borussia Dortmund
    173: 50,   # RB Leipzig
    168: 55,   # Bayer Leverkusen
    # Serie A
    489: 80,   # AC Milan
    496: 75,   # Juventus
    505: 85,   # Inter
    # Ligue 1
    85: 100,   # PSG
}


class EloRatingSystem:
    """
    Dynamic Elo rating system for football teams
    
    Key features:
    - K-factor adjusted for match importance
    - Home advantage factor
    - Goal difference margin
    - Regression to mean over time
    """
    
    def __init__(
        self,
        k_factor: float = 32.0,
        home_advantage: float = 65.0,
        regression_factor: float = 0.03
    ):
        self.k_factor = k_factor
        self.home_advantage = home_advantage
        self.regression_factor = regression_factor
        self.ratings: Dict[int, float] = {}
        self.last_updated: Dict[int, datetime] = {}
    
    def get_rating(self, team_id: int, league_id: int = 39) -> float:
        """Get current Elo rating for a team"""
        if team_id in self.ratings:
            return self.ratings[team_id]
        
        # Initialize with default rating + any team bonus
        base_rating = DEFAULT_RATINGS.get(league_id, 1500)
        bonus = TOP_TEAM_BONUSES.get(team_id, 0)
        
        self.ratings[team_id] = base_rating + bonus
        self.last_updated[team_id] = datetime.utcnow()
        
        return self.ratings[team_id]
    
    def expected_score(
        self,
        rating_a: float,
        rating_b: float,
        home_advantage: bool = True
    ) -> float:
        """
        Calculate expected score (win probability) for team A
        
        Uses logistic distribution with home advantage adjustment
        """
        diff = rating_a - rating_b
        if home_advantage:
            diff += self.home_advantage
        
        return 1.0 / (1.0 + 10 ** (-diff / 400))
    
    def predict_match(
        self,
        home_team_id: int,
        away_team_id: int,
        league_id: int = 39
    ) -> Dict[str, float]:
        """
        Predict match outcome probabilities
        
        Returns:
            Dict with home_win, draw, away_win probabilities
        """
        home_rating = self.get_rating(home_team_id, league_id)
        away_rating = self.get_rating(away_team_id, league_id)
        
        # Expected score for home team
        home_expected = self.expected_score(home_rating, away_rating, home_advantage=True)
        
        # Convert to three-way probabilities
        # Draw probability is higher when teams are evenly matched
        rating_diff = abs(home_rating - away_rating)
        
        # Base draw probability (decreases as rating diff increases)
        draw_base = 0.26  # Historical average draw rate in top leagues
        draw_adjustment = max(0, 0.12 - (rating_diff / 1000))
        draw_prob = draw_base + draw_adjustment
        
        # Remaining probability split between win/loss
        remaining = 1.0 - draw_prob
        
        if home_expected >= 0.5:
            home_win = remaining * home_expected
            away_win = remaining * (1 - home_expected)
        else:
            away_win = remaining * (1 - home_expected)
            home_win = remaining * home_expected
        
        # Normalize to ensure sum = 1
        total = home_win + draw_prob + away_win
        
        return {
            "home_win": round(home_win / total, 3),
            "draw": round(draw_prob / total, 3),
            "away_win": round(away_win / total, 3),
            "home_elo": round(home_rating, 1),
            "away_elo": round(away_rating, 1),
            "elo_diff": round(home_rating - away_rating + self.home_advantage, 1)
        }
    
    def update_rating(
        self,
        team_id: int,
        opponent_id: int,
        actual_score: float,  # 1 = win, 0.5 = draw, 0 = loss
        goal_diff: int = 0,
        is_home: bool = True,
        match_importance: float = 1.0,
        league_id: int = 39
    ) -> float:
        """
        Update Elo rating after a match
        
        Args:
            actual_score: 1 for win, 0.5 for draw, 0 for loss
            goal_diff: Goal difference (positive = team scored more)
            is_home: Whether the team played at home
            match_importance: Multiplier for K-factor (playoffs = 1.5, etc.)
        
        Returns:
            New rating
        """
        team_rating = self.get_rating(team_id, league_id)
        opponent_rating = self.get_rating(opponent_id, league_id)
        
        expected = self.expected_score(team_rating, opponent_rating, home_advantage=is_home)
        
        # Margin of victory multiplier
        mov_multiplier = math.log(abs(goal_diff) + 1) + 1 if goal_diff != 0 else 1.0
        
        # Adjusted K-factor
        k = self.k_factor * match_importance * mov_multiplier
        
        # Calculate new rating
        new_rating = team_rating + k * (actual_score - expected)
        
        # Apply bounds
        new_rating = max(1200, min(2000, new_rating))
        
        self.ratings[team_id] = new_rating
        self.last_updated[team_id] = datetime.utcnow()
        
        logger.info(
            "elo_updated",
            team_id=team_id,
            old_rating=team_rating,
            new_rating=new_rating,
            change=new_rating - team_rating
        )
        
        return new_rating
    
    def apply_time_regression(self, team_id: int, league_id: int = 39):
        """
        Apply regression to mean over time
        
        Ratings slowly decay toward league average when team hasn't played
        """
        if team_id not in self.last_updated:
            return
        
        days_since_update = (datetime.utcnow() - self.last_updated[team_id]).days
        
        if days_since_update > 30:
            league_mean = DEFAULT_RATINGS.get(league_id, 1500)
            current = self.ratings[team_id]
            
            # Regress 3% toward mean per month inactive
            months_inactive = days_since_update / 30
            regression = self.regression_factor * months_inactive
            regression = min(regression, 0.15)  # Cap at 15% regression
            
            new_rating = current + (league_mean - current) * regression
            self.ratings[team_id] = new_rating
            
            logger.info(
                "elo_regressed",
                team_id=team_id,
                old_rating=current,
                new_rating=new_rating,
                months_inactive=months_inactive
            )


# Global instance
elo_system = EloRatingSystem()
