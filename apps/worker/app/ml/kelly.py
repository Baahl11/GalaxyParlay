"""
Kelly Criterion for Optimal Bet Sizing

Based on the 1956 paper "A New Interpretation of Information Rate" by J.L. Kelly Jr.

The Kelly Criterion determines the optimal fraction of bankroll to bet
to maximize long-term growth while minimizing risk of ruin.

Formula: f* = (bp - q) / b
Where:
- f* = fraction of bankroll to bet
- b = decimal odds - 1 (net odds)
- p = probability of winning
- q = probability of losing (1 - p)

References:
- Kelly (1956): https://www.princeton.edu/~wbialek/rome/refs/kelly_56.pdf
- Thorp (2006): The Kelly Criterion in Blackjack, Sports Betting, and the Stock Market
"""
from typing import Dict, Optional, Any
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()


@dataclass
class KellyResult:
    """Result of Kelly Criterion calculation."""
    kelly_fraction: float      # Full Kelly (often too aggressive)
    half_kelly: float          # Half Kelly (more conservative, recommended)
    quarter_kelly: float       # Quarter Kelly (very conservative)
    edge: float                # Expected edge (model_prob - implied_prob)
    expected_value: float      # Expected value per unit bet
    is_value_bet: bool         # Whether this is a positive EV bet
    confidence: str            # "high", "medium", "low"
    recommendation: str        # Human-readable recommendation


class KellyCriterion:
    """
    Kelly Criterion calculator for sports betting.
    
    Implements fractional Kelly strategies to balance
    growth rate vs volatility.
    """
    
    def __init__(
        self,
        max_kelly: float = 0.25,      # Never bet more than 25% of bankroll
        min_edge: float = 0.02,        # Minimum 2% edge required
        min_probability: float = 0.10, # Minimum 10% win probability
        max_probability: float = 0.95  # Maximum 95% win probability
    ):
        self.max_kelly = max_kelly
        self.min_edge = min_edge
        self.min_probability = min_probability
        self.max_probability = max_probability
    
    def calculate(
        self,
        model_probability: float,
        decimal_odds: float,
        confidence_score: float = 0.7
    ) -> KellyResult:
        """
        Calculate optimal bet size using Kelly Criterion.
        
        Args:
            model_probability: Our model's probability of the outcome
            decimal_odds: Bookmaker's decimal odds (e.g., 2.50)
            confidence_score: Model confidence (0-1), used to adjust Kelly
            
        Returns:
            KellyResult with recommended bet sizes
        """
        # Validate inputs
        if model_probability <= 0 or model_probability >= 1:
            return self._no_bet_result("Invalid probability")
        
        if decimal_odds <= 1:
            return self._no_bet_result("Invalid odds")
        
        # Calculate implied probability from odds
        implied_probability = 1 / decimal_odds
        
        # Calculate edge
        edge = model_probability - implied_probability
        
        # Net odds (what you win per unit bet)
        b = decimal_odds - 1
        
        # Kelly formula: f* = (bp - q) / b
        # Where p = model_probability, q = 1 - p
        p = model_probability
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Calculate expected value
        # EV = (prob_win * profit) - (prob_lose * stake)
        # EV = p * b - q * 1 = p * b - q
        expected_value = p * b - q
        
        # Check if this is a value bet
        is_value_bet = edge >= self.min_edge and kelly_fraction > 0
        
        # Apply constraints
        if kelly_fraction <= 0:
            return self._no_bet_result("Negative Kelly (no edge)", edge=edge)
        
        if edge < self.min_edge:
            return self._no_bet_result(f"Edge too small ({edge:.1%} < {self.min_edge:.1%})", edge=edge)
        
        if model_probability < self.min_probability:
            return self._no_bet_result("Probability too low (high variance)")
        
        if model_probability > self.max_probability:
            return self._no_bet_result("Probability too high (low value)")
        
        # Cap Kelly at maximum
        kelly_fraction = min(kelly_fraction, self.max_kelly)
        
        # Adjust Kelly based on model confidence
        # Lower confidence = more conservative betting
        confidence_multiplier = 0.5 + (confidence_score * 0.5)  # Range: 0.5 to 1.0
        adjusted_kelly = kelly_fraction * confidence_multiplier
        
        # Calculate fractional Kelly strategies
        half_kelly = adjusted_kelly * 0.5
        quarter_kelly = adjusted_kelly * 0.25
        
        # Determine confidence level
        if confidence_score >= 0.8 and edge >= 0.10:
            confidence = "high"
        elif confidence_score >= 0.6 and edge >= 0.05:
            confidence = "medium"
        else:
            confidence = "low"
        
        # Generate recommendation
        recommendation = self._generate_recommendation(
            half_kelly, edge, confidence, decimal_odds
        )
        
        return KellyResult(
            kelly_fraction=round(adjusted_kelly, 4),
            half_kelly=round(half_kelly, 4),
            quarter_kelly=round(quarter_kelly, 4),
            edge=round(edge, 4),
            expected_value=round(expected_value, 4),
            is_value_bet=is_value_bet,
            confidence=confidence,
            recommendation=recommendation
        )
    
    def calculate_for_match(
        self,
        predictions: Dict[str, float],
        odds: Dict[str, float],
        confidence_score: float = 0.7
    ) -> Dict[str, KellyResult]:
        """
        Calculate Kelly for all outcomes of a match.
        
        Args:
            predictions: Dict with probabilities (e.g., {"home_win": 0.45, "draw": 0.28, ...})
            odds: Dict with decimal odds (e.g., {"home": 2.10, "draw": 3.40, ...})
            confidence_score: Model confidence
            
        Returns:
            Dict mapping outcome to KellyResult
        """
        results = {}
        
        # Map prediction keys to odds keys
        key_mapping = {
            "home_win": "home",
            "draw": "draw", 
            "away_win": "away",
            "over": "over",
            "under": "under",
            "yes": "yes",
            "no": "no"
        }
        
        for pred_key, probability in predictions.items():
            odds_key = key_mapping.get(pred_key, pred_key)
            
            if odds_key in odds:
                results[pred_key] = self.calculate(
                    model_probability=probability,
                    decimal_odds=odds[odds_key],
                    confidence_score=confidence_score
                )
        
        return results
    
    def _no_bet_result(self, reason: str, edge: float = 0.0) -> KellyResult:
        """Return a result indicating no bet should be placed."""
        return KellyResult(
            kelly_fraction=0.0,
            half_kelly=0.0,
            quarter_kelly=0.0,
            edge=round(edge, 4),
            expected_value=0.0,
            is_value_bet=False,
            confidence="none",
            recommendation=f"No bet: {reason}"
        )
    
    def _generate_recommendation(
        self,
        half_kelly: float,
        edge: float,
        confidence: str,
        odds: float
    ) -> str:
        """Generate human-readable betting recommendation."""
        if half_kelly < 0.01:
            return "Skip: Edge too small for meaningful bet"
        
        # Convert to percentage of bankroll
        bet_pct = half_kelly * 100
        
        if confidence == "high":
            strength = "Strong"
        elif confidence == "medium":
            strength = "Moderate"
        else:
            strength = "Speculative"
        
        return f"{strength} bet: {bet_pct:.1f}% of bankroll @ {odds:.2f} (edge: {edge:.1%})"


# Global instance
kelly_calculator = KellyCriterion()
