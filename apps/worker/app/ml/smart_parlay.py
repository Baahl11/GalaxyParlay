"""
Smart Parlay Validator

Validates parlay combinations based on correlation analysis from FASE 5
Prevents users from combining highly correlated markets that reduce value.
"""

from typing import Dict, List, Tuple

import structlog

from .league_config import (
    HIGH_CORRELATION_PAIRS,
    RECOMMENDED_PARLAY_COMBINATIONS,
    SMART_PARLAY_CONFIG,
)

logger = structlog.get_logger()


class SmartParlayValidator:
    """
    Validates parlay combinations to ensure they're not highly correlated

    Based on FASE 5 correlation matrix analysis:
    - High correlation (>0.7): Markets move together, reduces parlay value
    - Low correlation (<0.3): Independent markets, good for parlays
    """

    def __init__(self):
        self.high_corr_threshold = SMART_PARLAY_CONFIG["high_correlation_threshold"]
        self.moderate_corr_threshold = SMART_PARLAY_CONFIG["moderate_correlation_threshold"]
        self.correlation_pairs = HIGH_CORRELATION_PAIRS

    def validate_parlay(self, selections: List[Dict]) -> Tuple[bool, str, float]:
        """
        Validate if a parlay combination is acceptable

        Args:
            selections: List of selections, each with:
                - market_key: e.g., "match_winner_home_win"
                - fixture_id: Fixture ID
                - odds: Decimal odds

        Returns:
            Tuple of (is_valid, reason, odds_penalty)
            - is_valid: True if parlay is acceptable
            - reason: Explanation if rejected or warning
            - odds_penalty: Multiplier to apply to odds (1.0 = no penalty)
        """

        # Single selection - always valid
        if len(selections) <= 1:
            return True, "Single selection", 1.0

        # Check if selections are from same fixture
        same_fixture_markets = self._get_same_fixture_markets(selections)

        for fixture_id, markets in same_fixture_markets.items():
            if len(markets) < 2:
                continue

            # Check correlations between markets in same fixture
            for i, market1 in enumerate(markets):
                for market2 in markets[i + 1 :]:
                    correlation = self._get_correlation(market1, market2)

                    # High correlation - reject
                    if abs(correlation) > self.high_corr_threshold:
                        logger.warning(
                            "parlay_rejected_high_correlation",
                            market1=market1,
                            market2=market2,
                            correlation=correlation,
                            fixture_id=fixture_id,
                        )
                        return (
                            False,
                            f"⚠️ {self._format_market_name(market1)} and "
                            f"{self._format_market_name(market2)} are highly correlated "
                            f"(r={correlation:.2f}). Combining them reduces value.",
                            1.0,
                        )

                    # Moderate correlation - warn and apply penalty
                    if abs(correlation) > self.moderate_corr_threshold:
                        logger.info(
                            "parlay_moderate_correlation_warning",
                            market1=market1,
                            market2=market2,
                            correlation=correlation,
                            fixture_id=fixture_id,
                        )
                        penalty = SMART_PARLAY_CONFIG["moderate_correlation_penalty"]
                        return (
                            True,
                            f"⚠️ Moderate correlation detected (r={correlation:.2f}). "
                            f"Odds adjusted by {penalty:.1%}.",
                            penalty,
                        )

        # All checks passed
        logger.info(
            "parlay_validated",
            num_selections=len(selections),
            fixtures=list(same_fixture_markets.keys()),
        )
        return True, "✅ Valid parlay combination", 1.0

    def get_recommendations(
        self, available_markets: List[str], fixture_id: int
    ) -> List[Tuple[str, str, float]]:
        """
        Get recommended parlay combinations for a fixture

        Args:
            available_markets: List of market keys available for this fixture
            fixture_id: Fixture ID

        Returns:
            List of (market1, market2, correlation) recommendations
        """
        recommendations = []

        # Check recommended combinations
        for combo in RECOMMENDED_PARLAY_COMBINATIONS:
            # Extract market type (without outcome)
            market_type1 = combo[0]
            market_type2 = combo[1]

            # Find matching markets in available_markets
            matches1 = [m for m in available_markets if market_type1 in m]
            matches2 = [m for m in available_markets if market_type2 in m]

            for m1 in matches1:
                for m2 in matches2:
                    if m1 != m2:
                        corr = self._get_correlation(m1, m2)
                        if abs(corr) < self.moderate_corr_threshold:
                            recommendations.append((m1, m2, corr))

        # Sort by lowest correlation (most independent)
        recommendations.sort(key=lambda x: abs(x[2]))

        return recommendations[:5]  # Top 5 recommendations

    def _get_same_fixture_markets(self, selections: List[Dict]) -> Dict[int, List[str]]:
        """
        Group selections by fixture ID

        Returns:
            Dict of fixture_id -> list of market_keys
        """
        fixture_markets = {}

        for selection in selections:
            fixture_id = selection.get("fixture_id")
            market_key = selection.get("market_key")

            if fixture_id and market_key:
                if fixture_id not in fixture_markets:
                    fixture_markets[fixture_id] = []
                fixture_markets[fixture_id].append(market_key)

        return fixture_markets

    def _get_correlation(self, market1: str, market2: str) -> float:
        """
        Get correlation coefficient between two markets

        Returns:
            Correlation coefficient (-1.0 to 1.0)
        """
        # Check both orderings
        pair1 = (market1, market2)
        pair2 = (market2, market1)

        if pair1 in self.correlation_pairs:
            return self.correlation_pairs[pair1]
        if pair2 in self.correlation_pairs:
            return self.correlation_pairs[pair2]

        # Not in known correlations - estimate based on market types
        return self._estimate_correlation(market1, market2)

    def _estimate_correlation(self, market1: str, market2: str) -> float:
        """
        Estimate correlation for market pairs not in database

        Uses heuristics based on market types
        """
        # Same market type with different outcomes = perfectly inverse
        if market1.rsplit("_", 1)[0] == market2.rsplit("_", 1)[0]:
            if market1 != market2:
                return -1.0  # e.g., over vs under

        # Over/Under markets with adjacent thresholds
        if "over_under" in market1 and "over_under" in market2:
            return 0.6  # Moderate-high correlation (conservative)

        # Match winner vs Over/Under - typically low correlation
        if "match_winner" in market1 and "over_under" in market2:
            return 0.05  # Very low correlation
        if "match_winner" in market2 and "over_under" in market1:
            return 0.05

        # Different match winner outcomes - mutually exclusive
        if "match_winner" in market1 and "match_winner" in market2:
            return -0.5  # High negative correlation

        # Default: assume low correlation for unknown pairs
        return 0.15

    def _format_market_name(self, market_key: str) -> str:
        """Format market key for user-friendly display"""
        # Convert snake_case to Title Case
        parts = market_key.split("_")

        # Special handling for common terms
        formatted = []
        for part in parts:
            if part == "over":
                formatted.append("Over")
            elif part == "under":
                formatted.append("Under")
            elif part == "home":
                formatted.append("Home")
            elif part == "away":
                formatted.append("Away")
            elif part == "win":
                formatted.append("Win")
            elif part == "draw":
                formatted.append("Draw")
            elif part.replace(".", "").isdigit():
                formatted.append(part)
            else:
                formatted.append(part.title())

        return " ".join(formatted)


# Global instance
smart_parlay_validator = SmartParlayValidator()
