"""
Backtesting Runner Script

Collects ALL finished fixtures from Jan 1 2025 - Jan 29 2026 (full year)
for maximum statistical validation between OLD model (baseline)
and NEW model (with Phase 3 improvements + configurable parameters).

Usage:
    python -m app.ml.run_backtest

Expected results:
- OLD model accuracy: ~72-73%
- NEW model accuracy: ~72-74% (with optimized parameters)
- Brier Score: <0.19 (excellent calibration)
- Statistical significance: ALL available fixtures × 18 markets = maximum validation
"""

import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List

import structlog

from app.config import settings
from app.ml.backtesting import backtesting
from app.ml.predictor import MatchPredictor
from app.services.database import db_service

logger = structlog.get_logger()


class BacktestRunner:
    """
    Orchestrates backtesting process

    Steps:
    1. Fetch finished fixtures (Jan 15-29 2026)
    2. Run OLD model (without improvements)
    3. Run NEW model (with improvements)
    4. Compare and generate report
    """

    def __init__(self):
        self.old_predictor = MatchPredictor()
        self.new_predictor = MatchPredictor()

        # Configure predictors
        # OLD: Disable Phase 3 improvements
        self.old_predictor.use_bivariate_poisson = False
        self.old_predictor.use_contextual_elo = False
        self.old_predictor.use_live_xg = False  # Use Elo-estimated xG

        # NEW: Enable all improvements (xG disabled for speed)
        self.new_predictor.use_bivariate_poisson = True
        self.new_predictor.use_contextual_elo = True
        self.new_predictor.use_live_xg = False  # Disable API calls for faster backtest

    def fetch_test_fixtures(
        self, start_date: str = "2025-01-01", end_date: str = "2026-01-29"
    ) -> List[Dict[str, Any]]:
        """
        Fetch finished fixtures from database for testing

        Target: ALL fixtures available (full year) for ultimate statistical validation
        This provides maximum predictions across all markets for the most robust analysis
        """
        logger.info("Fetching test fixtures", start_date=start_date, end_date=end_date)

        # Query directly with date filter for better performance
        # Remove limit to get ALL finished fixtures in the date range
        fixtures_result = (
            db_service.client.table("fixtures")
            .select("*")
            .eq("status", "FT")
            .gte("kickoff_time", start_date)
            .lte("kickoff_time", end_date)
            .order("kickoff_time")
            .limit(5000)  # Set high limit to get all available fixtures
            .execute()
        )

        filtered_fixtures = fixtures_result.data

        logger.info("Test fixtures fetched", count=len(filtered_fixtures))

        return filtered_fixtures

    def get_actual_outcome(
        self, fixture: Dict[str, Any], market_key: str, outcome: str = None
    ) -> float:
        """
        Determine actual outcome for a market

        Args:
            fixture: Fixture data
            market_key: Market type (e.g., "match_winner", "over_under_2_5")
            outcome: Specific outcome (e.g., "home_win", "over")

        Returns 1.0 if outcome occurred, 0.0 if not
        """
        home_score = fixture.get("home_score")
        away_score = fixture.get("away_score")

        if home_score is None or away_score is None:
            return None

        # Match winner
        if market_key == "match_winner":
            if outcome == "home_win":
                return 1.0 if home_score > away_score else 0.0
            elif outcome == "draw":
                return 1.0 if home_score == away_score else 0.0
            elif outcome == "away_win":
                return 1.0 if away_score > home_score else 0.0

        # BTTS
        elif market_key == "btts":
            both_scored = home_score > 0 and away_score > 0
            if outcome == "yes":
                return 1.0 if both_scored else 0.0
            elif outcome == "no":
                return 1.0 if not both_scored else 0.0

        # Over/Under
        elif "over_under" in market_key:
            total_goals = home_score + away_score

            # Extract threshold from market_key
            if "0_5" in market_key:
                threshold = 0.5
            elif "1_5" in market_key:
                threshold = 1.5
            elif "2_5" in market_key:
                threshold = 2.5
            elif "3_5" in market_key:
                threshold = 3.5
            elif "4_5" in market_key:
                threshold = 4.5
            else:
                return None

            if outcome == "over":
                return 1.0 if total_goals > threshold else 0.0
            elif outcome == "under":
                return 1.0 if total_goals < threshold else 0.0

        # TODO: Add more markets (corners, cards, shots, offsides)
        # For now, return None for unsupported markets
        return None

    def extract_market_probabilities(
        self, predictions: List[Dict[str, Any]], market_key: str
    ) -> Dict[str, float]:
        """
        Extract probabilities for a specific market from predictions
        """
        for pred in predictions:
            if pred.get("market_key") == market_key or pred.get("market") == market_key:
                return pred.get("prediction", pred.get("probabilities", {}))

        return {}

    def run_backtest(self, start_date: str = "2026-01-15", end_date: str = "2026-01-29"):
        """
        Run full backtesting comparison
        """
        logger.info("Starting backtesting run")

        # 1. Fetch test fixtures
        fixtures = self.fetch_test_fixtures(start_date, end_date)

        if len(fixtures) < 50:
            logger.warning("Insufficient fixtures for robust backtesting", count=len(fixtures))
            return

        backtesting.fixtures_tested = len(fixtures)

        # 2. Process each fixture
        for i, fixture in enumerate(fixtures):
            if i % 20 == 0:
                logger.info(f"Processing fixture {i+1}/{len(fixtures)}")

            fixture_id = fixture["id"]

            try:
                # Get predictions from BOTH models
                old_predictions = self.old_predictor.predict_fixture(
                    fixture, include_all_markets=True
                )

                new_predictions = self.new_predictor.predict_fixture(
                    fixture, include_all_markets=True
                )

                # Process each market
                # Map to predictor market_keys and outcomes
                markets_to_test = [
                    ("match_winner", "home_win"),
                    ("match_winner", "draw"),
                    ("match_winner", "away_win"),
                    ("btts", "yes"),
                    ("btts", "no"),
                    ("over_under_2_5", "over"),
                    ("over_under_2_5", "under"),
                    ("over_under_1_5", "over"),
                    ("over_under_1_5", "under"),
                    ("over_under_3_5", "over"),
                    ("over_under_3_5", "under"),
                ]

                for market_key, outcome in markets_to_test:
                    # Get actual outcome for this market+outcome combo
                    actual = self.get_actual_outcome(fixture, market_key, outcome)

                    if actual is None:
                        continue  # Skip if can't determine outcome

                    # Extract predictions for this market
                    old_probs = self.extract_market_probabilities(old_predictions, market_key)
                    new_probs = self.extract_market_probabilities(new_predictions, market_key)

                    # Check if probs are empty
                    if not old_probs or not new_probs:
                        continue  # Skip if predictions not available for this market

                    # Get probability for specific outcome
                    old_prob = old_probs.get(outcome, 0.33)  # Default to 33% if missing
                    new_prob = new_probs.get(outcome, 0.33)

                    # Validate probabilities are numbers
                    if not isinstance(old_prob, (int, float)) or not isinstance(
                        new_prob, (int, float)
                    ):
                        logger.warning(
                            f"Invalid probability type for {market_key}.{outcome}: old={type(old_prob)}, new={type(new_prob)}"
                        )
                        continue

                    # Get confidence
                    old_confidence = 0.7
                    new_confidence = 0.7
                    for pred in old_predictions:
                        if pred.get("market_key") == market_key:
                            old_confidence = pred.get("confidence_score", 0.7)
                    for pred in new_predictions:
                        if pred.get("market_key") == market_key:
                            new_confidence = pred.get("confidence_score", 0.7)

                    # Record results with combined market_key
                    combined_market = f"{market_key}_{outcome}"
                    backtesting.add_prediction_result(
                        model_type="old_model",
                        market_key=combined_market,
                        predicted_prob=old_prob,
                        actual_outcome=actual,
                        odds=None,  # TODO: Fetch odds if available
                        confidence=old_confidence,
                        fixture_id=fixture.get("id"),
                        league_id=fixture.get("league_id"),
                    )

                    backtesting.add_prediction_result(
                        model_type="new_model",
                        market_key=combined_market,
                        predicted_prob=new_prob,
                        actual_outcome=actual,
                        odds=None,
                        confidence=new_confidence,
                        fixture_id=fixture.get("id"),
                        league_id=fixture.get("league_id"),
                    )

            except Exception as e:
                logger.error(
                    "Error processing fixture for backtest", fixture_id=fixture_id, error=str(e)
                )
                continue

        # 3. Generate and display report
        logger.info("Backtesting complete, generating report")
        backtesting.print_summary()

        # 4. Export to JSON
        output_path = "backtest_results.json"
        backtesting.export_results(output_path)

        logger.info("Backtesting results exported", path=output_path)


def main():
    """Entry point for backtesting"""
    runner = BacktestRunner()

    # Run backtest on ALL available historical data (2024-2025)
    # With 24 leagues, expect 5,000+ fixtures for comprehensive validation
    runner.run_backtest(start_date="2024-01-01", end_date="2026-01-29")


if __name__ == "__main__":
    main()
