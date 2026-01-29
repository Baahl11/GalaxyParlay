"""
Value Bets Detection Module

Compares model predictions with bookmaker odds to find +EV opportunities.
A value bet exists when our model probability > implied probability from odds.

Formula:
- Implied Probability = 1 / Decimal Odds
- Edge = Model Probability - Implied Probability  
- Expected Value (EV) = (Model_Prob * (Odds - 1)) - (1 - Model_Prob)
- Kelly Criterion = Edge / (Odds - 1)
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import structlog

logger = structlog.get_logger()


@dataclass
class ValueBet:
    """Represents a detected value bet opportunity"""
    fixture_id: int
    home_team: str
    away_team: str
    league_id: int
    kickoff_time: str
    
    # Market info
    market_key: str  # match_winner, over_under_2.5, both_teams_score
    selection: str   # home_win, away_win, draw, over, under, yes, no
    
    # Probabilities
    model_probability: float
    implied_probability: float
    bookmaker_odds: float
    bookmaker: str
    
    # Value metrics
    edge: float              # Model prob - Implied prob (positive = value)
    expected_value: float    # EV per unit staked
    kelly_fraction: float    # Optimal bet size (fraction of bankroll)
    
    # Quality
    confidence_score: float
    quality_grade: str
    
    # Ranking
    value_score: float  # Combined score for ranking
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fixture_id": self.fixture_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "league_id": self.league_id,
            "kickoff_time": self.kickoff_time,
            "market_key": self.market_key,
            "selection": self.selection,
            "model_probability": round(self.model_probability, 4),
            "implied_probability": round(self.implied_probability, 4),
            "bookmaker_odds": round(self.bookmaker_odds, 2),
            "bookmaker": self.bookmaker,
            "edge": round(self.edge, 4),
            "edge_percent": round(self.edge * 100, 2),
            "expected_value": round(self.expected_value, 4),
            "ev_percent": round(self.expected_value * 100, 2),
            "kelly_fraction": round(self.kelly_fraction, 4),
            "kelly_percent": round(self.kelly_fraction * 100, 2),
            "confidence_score": round(self.confidence_score, 2),
            "quality_grade": self.quality_grade,
            "value_score": round(self.value_score, 2),
        }


class ValueBetDetector:
    """
    Detects value betting opportunities by comparing model predictions
    with bookmaker odds.
    """
    
    # Minimum thresholds for a value bet
    MIN_EDGE = 0.03          # 3% minimum edge
    MIN_EV = 0.02            # 2% minimum expected value
    MIN_ODDS = 1.20          # Don't bet on very short odds
    MAX_ODDS = 10.0          # Avoid extreme longshots
    MIN_CONFIDENCE = 0.40    # Minimum model confidence
    
    # Kelly fraction limiter (never bet more than this fraction)
    MAX_KELLY = 0.10  # 10% max bet size
    
    def __init__(
        self,
        min_edge: float = MIN_EDGE,
        min_ev: float = MIN_EV,
        min_confidence: float = MIN_CONFIDENCE
    ):
        self.min_edge = min_edge
        self.min_ev = min_ev
        self.min_confidence = min_confidence
    
    def calculate_implied_probability(self, odds: float) -> float:
        """Convert decimal odds to implied probability"""
        if odds <= 1:
            return 1.0
        return 1 / odds
    
    def calculate_edge(self, model_prob: float, implied_prob: float) -> float:
        """Calculate edge (advantage over bookmaker)"""
        return model_prob - implied_prob
    
    def calculate_expected_value(self, model_prob: float, odds: float) -> float:
        """
        Calculate Expected Value per unit staked
        EV = (prob * profit) - (1 - prob) * stake
        EV = (prob * (odds - 1)) - (1 - prob)
        """
        return (model_prob * (odds - 1)) - (1 - model_prob)
    
    def calculate_kelly_fraction(self, model_prob: float, odds: float) -> float:
        """
        Calculate Kelly Criterion bet size
        Kelly = (p * (b + 1) - 1) / b
        where p = probability, b = odds - 1
        """
        if odds <= 1:
            return 0
        
        b = odds - 1
        kelly = (model_prob * (b + 1) - 1) / b
        
        # Cap at maximum and floor at 0
        return max(0, min(kelly, self.MAX_KELLY))
    
    def calculate_value_score(
        self,
        edge: float,
        ev: float,
        confidence: float,
        quality_grade: str
    ) -> float:
        """
        Calculate composite value score for ranking bets
        Higher = better opportunity
        """
        # Grade multiplier
        grade_multiplier = {
            'A': 1.5,
            'B': 1.2,
            'C': 1.0,
            'D': 0.8,
            'F': 0.5
        }.get(quality_grade, 1.0)
        
        # Normalize components
        edge_score = min(edge / 0.15, 1.0) * 40  # Max 40 points for 15%+ edge
        ev_score = min(ev / 0.20, 1.0) * 30     # Max 30 points for 20%+ EV
        conf_score = confidence * 30             # Max 30 points for confidence
        
        return (edge_score + ev_score + conf_score) * grade_multiplier
    
    def detect_value_bets(
        self,
        fixtures: List[Dict[str, Any]]
    ) -> List[ValueBet]:
        """
        Analyze fixtures with predictions and odds to find value bets
        
        Args:
            fixtures: List of fixtures with predictions, quality_scores, and odds
            
        Returns:
            List of ValueBet opportunities, sorted by value_score
        """
        value_bets = []
        
        for fixture in fixtures:
            fixture_id = fixture.get("id")
            home_team = fixture.get("home_team_name", "Home")
            away_team = fixture.get("away_team_name", "Away")
            league_id = fixture.get("league_id", 0)
            kickoff_time = fixture.get("kickoff_time", "")
            
            predictions = fixture.get("predictions", [])
            odds_list = fixture.get("odds", [])
            quality_scores = fixture.get("quality_scores", [])
            
            # Skip if no predictions or odds
            if not predictions or not odds_list:
                continue
            
            # Index odds by market_key
            odds_by_market = {}
            for o in odds_list:
                market = o.get("market_key")
                if market not in odds_by_market:
                    odds_by_market[market] = o
            
            # Index quality by market_key
            quality_by_market = {q["market_key"]: q for q in quality_scores}
            
            # Analyze each prediction
            for pred in predictions:
                market_key = pred.get("market_key")
                prediction_data = pred.get("prediction", {})
                confidence = pred.get("confidence_score", 0.5)
                pred_grade = pred.get("quality_grade", "C")
                
                # Skip low confidence predictions
                if confidence < self.min_confidence:
                    continue
                
                # Get corresponding odds
                odds_snapshot = odds_by_market.get(market_key)
                if not odds_snapshot:
                    continue
                
                odds_data = odds_snapshot.get("odds_data", {})
                bookmaker = odds_snapshot.get("bookmaker", "Unknown")
                
                # Get quality grade (use quality_scores if available, else prediction grade)
                quality = quality_by_market.get(market_key, {})
                quality_grade = quality.get("final_grade", pred_grade)
                
                # Analyze each selection in this market
                value_bets_for_market = self._analyze_market(
                    fixture_id=fixture_id,
                    home_team=home_team,
                    away_team=away_team,
                    league_id=league_id,
                    kickoff_time=kickoff_time,
                    market_key=market_key,
                    prediction_data=prediction_data,
                    odds_data=odds_data,
                    bookmaker=bookmaker,
                    confidence=confidence,
                    quality_grade=quality_grade
                )
                
                value_bets.extend(value_bets_for_market)
        
        # Sort by value_score descending
        value_bets.sort(key=lambda x: x.value_score, reverse=True)
        
        logger.info(
            "value_bets_detected",
            total_fixtures=len(fixtures),
            value_bets_found=len(value_bets)
        )
        
        return value_bets
    
    def _analyze_market(
        self,
        fixture_id: int,
        home_team: str,
        away_team: str,
        league_id: int,
        kickoff_time: str,
        market_key: str,
        prediction_data: Dict[str, float],
        odds_data: Dict[str, float],
        bookmaker: str,
        confidence: float,
        quality_grade: str
    ) -> List[ValueBet]:
        """Analyze a single market for value bets"""
        value_bets = []
        
        # Map prediction keys to odds keys
        if market_key == "match_winner":
            mappings = [
                ("home_win", "home"),
                ("draw", "draw"),
                ("away_win", "away")
            ]
        elif market_key == "over_under_2.5":
            mappings = [
                ("over", "over"),
                ("under", "under")
            ]
        elif market_key == "both_teams_score":
            mappings = [
                ("yes", "yes"),
                ("no", "no")
            ]
        else:
            return []
        
        for pred_key, odds_key in mappings:
            model_prob = prediction_data.get(pred_key, 0)
            bookmaker_odds = odds_data.get(odds_key, 0)
            
            # Skip if missing data or invalid odds
            if not model_prob or not bookmaker_odds:
                continue
            if bookmaker_odds < self.MIN_ODDS or bookmaker_odds > self.MAX_ODDS:
                continue
            
            # Calculate value metrics
            implied_prob = self.calculate_implied_probability(bookmaker_odds)
            edge = self.calculate_edge(model_prob, implied_prob)
            ev = self.calculate_expected_value(model_prob, bookmaker_odds)
            kelly = self.calculate_kelly_fraction(model_prob, bookmaker_odds)
            
            # Check if it qualifies as a value bet
            if edge >= self.min_edge and ev >= self.min_ev:
                value_score = self.calculate_value_score(
                    edge, ev, confidence, quality_grade
                )
                
                # Create human-readable selection name
                selection_name = self._get_selection_name(
                    market_key, pred_key, home_team, away_team
                )
                
                value_bet = ValueBet(
                    fixture_id=fixture_id,
                    home_team=home_team,
                    away_team=away_team,
                    league_id=league_id,
                    kickoff_time=kickoff_time,
                    market_key=market_key,
                    selection=selection_name,
                    model_probability=model_prob,
                    implied_probability=implied_prob,
                    bookmaker_odds=bookmaker_odds,
                    bookmaker=bookmaker,
                    edge=edge,
                    expected_value=ev,
                    kelly_fraction=kelly,
                    confidence_score=confidence,
                    quality_grade=quality_grade,
                    value_score=value_score
                )
                
                value_bets.append(value_bet)
        
        return value_bets
    
    def _get_selection_name(
        self,
        market_key: str,
        selection_key: str,
        home_team: str,
        away_team: str
    ) -> str:
        """Generate human-readable selection name"""
        if market_key == "match_winner":
            if selection_key == "home_win":
                return f"{home_team} Win"
            elif selection_key == "away_win":
                return f"{away_team} Win"
            else:
                return "Draw"
        elif market_key == "over_under_2.5":
            return "Over 2.5 Goals" if selection_key == "over" else "Under 2.5 Goals"
        elif market_key == "both_teams_score":
            return "Both Teams Score" if selection_key == "yes" else "BTTS No"
        return selection_key


# Singleton instance
value_detector = ValueBetDetector()
