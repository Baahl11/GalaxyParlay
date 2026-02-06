"""
Grid Search for Parameter Optimization
=======================================

Optimizes parameters for MultiMarketPredictor using historical data:
- rho: Dixon-Coles correlation parameter
- blend_ratio_dc/hist: Dixon-Coles vs historical blend in BTTS
- home_advantage: Home advantage multiplier for goals

Uses train/validation split to find best parameter combination.
"""

import itertools
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import structlog

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent))

from app.ml.predictor import MatchPredictor
from app.services.database import db_service

logger = structlog.get_logger()


class ParameterGridSearch:
    """Grid search for optimal prediction parameters"""

    def __init__(self, train_fixtures: List, validation_fixtures: List):
        self.train_fixtures = train_fixtures
        self.validation_fixtures = validation_fixtures

        # Parameter grid to search
        self.param_grid = {
            "rho": [-0.10, -0.13, -0.15, -0.17, -0.20],
            "blend_ratio_dc": [0.70, 0.75, 0.80, 0.85],
            "home_advantage": [1.10, 1.12, 1.15, 1.18, 1.20],
        }

        # Markets to evaluate (same as backtest)
        self.markets_to_test = [
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

        logger.info(
            "grid_search_initialized",
            train_fixtures=len(train_fixtures),
            validation_fixtures=len(validation_fixtures),
            param_combinations=self._count_combinations(),
        )

    def _count_combinations(self) -> int:
        """Count total parameter combinations"""
        return (
            len(self.param_grid["rho"])
            * len(self.param_grid["blend_ratio_dc"])
            * len(self.param_grid["home_advantage"])
        )

    def get_actual_outcome(self, fixture: Dict, market_key: str, outcome: str) -> bool:
        """
        Determine if outcome actually occurred
        (Updated to use database format: home_score/away_score)
        """
        home_goals = fixture.get("home_score")
        away_goals = fixture.get("away_score")

        if home_goals is None or away_goals is None:
            return None

        total_goals = home_goals + away_goals

        # Match Winner
        if market_key == "match_winner":
            if outcome == "home_win":
                return home_goals > away_goals
            elif outcome == "draw":
                return home_goals == away_goals
            elif outcome == "away_win":
                return away_goals > home_goals

        # BTTS
        elif market_key == "btts":
            btts_occurred = home_goals > 0 and away_goals > 0
            if outcome == "yes":
                return btts_occurred
            elif outcome == "no":
                return not btts_occurred

        # Over/Under
        elif market_key.startswith("over_under"):
            line = float(market_key.split("_")[-1].replace("_", "."))
            if outcome == "over":
                return total_goals > line
            elif outcome == "under":
                return total_goals <= line

        return None

    def extract_market_probabilities(self, predictions: List, market_key: str) -> Dict[str, float]:
        """
        Extract probabilities for a specific market from predictions
        (Copied from Backtester - predictions is a LIST of dicts)
        """
        for pred in predictions:
            if pred.get("market_key") == market_key or pred.get("market") == market_key:
                return pred.get("prediction", pred.get("probabilities", {}))

        return {}

    def evaluate_parameters(
        self, rho: float, blend_ratio_dc: float, home_advantage: float
    ) -> Tuple[float, Dict]:
        """
        Evaluate a specific parameter combination on validation set

        Returns:
            (accuracy, detailed_metrics)
        """
        from app.ml.multi_market_predictor import MultiMarketPredictor

        blend_ratio_hist = 1.0 - blend_ratio_dc

        # Create predictor with custom parameters
        predictor = MatchPredictor(model_version="grid_search")

        # Load historical data
        predictor.load_historical_stats()
        predictor.load_elo_from_db()

        # Create custom MultiMarketPredictor with test parameters
        custom_multi_market = MultiMarketPredictor(
            rho=rho,
            blend_ratio_dc=blend_ratio_dc,
            blend_ratio_hist=blend_ratio_hist,
            home_advantage=home_advantage,
        )

        # Replace default multi_market_predictor
        import app.ml.multi_market_predictor as mmp_module

        original_predictor = mmp_module.multi_market_predictor
        mmp_module.multi_market_predictor = custom_multi_market

        try:
            # Evaluate on validation set
            correct = 0
            total = 0
            market_metrics = {}

            for fixture in self.validation_fixtures:
                try:
                    predictions = predictor.predict_fixture(fixture, include_all_markets=True)

                    # DEBUG: Log first prediction to see structure
                    if total == 0:
                        logger.info(
                            "DEBUG_first_prediction",
                            fixture_id=fixture.get("id"),
                            num_predictions=(
                                len(predictions) if isinstance(predictions, list) else "NOT A LIST"
                            ),
                            first_pred_keys=(
                                list(predictions[0].keys())
                                if isinstance(predictions, list) and len(predictions) > 0
                                else "EMPTY"
                            ),
                        )

                    for market_key, outcome in self.markets_to_test:
                        actual = self.get_actual_outcome(fixture, market_key, outcome)

                        if actual is None:
                            if total < 10:
                                logger.warning(
                                    "DEBUG_actual_is_none",
                                    fixture_id=fixture.get("id"),
                                    market_key=market_key,
                                    outcome=outcome,
                                    score=fixture.get("score"),
                                )
                            continue

                        probs = self.extract_market_probabilities(predictions, market_key)

                        if not probs or outcome not in probs:
                            if total < 5:  # Log first few issues
                                logger.warning(
                                    "DEBUG_no_probs",
                                    market_key=market_key,
                                    outcome=outcome,
                                    probs=probs,
                                )
                            continue

                        predicted_prob = probs[outcome]
                        predicted = predicted_prob > 0.5

                        is_correct = predicted == actual
                        total += 1

                        if is_correct:
                            correct += 1

                        # Track per-market metrics
                        market_outcome_key = f"{market_key}_{outcome}"
                        if market_outcome_key not in market_metrics:
                            market_metrics[market_outcome_key] = {"correct": 0, "total": 0}

                        market_metrics[market_outcome_key]["total"] += 1
                        if is_correct:
                            market_metrics[market_outcome_key]["correct"] += 1

                except Exception as e:
                    logger.warning("prediction_failed", fixture_id=fixture.get("id"), error=str(e))
                    continue

            accuracy = correct / total if total > 0 else 0.0

            return accuracy, market_metrics

        finally:
            # Restore original predictor
            mmp_module.multi_market_predictor = original_predictor

    def run_grid_search(self) -> Dict:
        """
        Run grid search over all parameter combinations

        Returns:
            {
                "best_params": {...},
                "best_accuracy": 0.75,
                "all_results": [...]
            }
        """
        results = []

        total_combinations = self._count_combinations()
        logger.info("starting_grid_search", total_combinations=total_combinations)

        for i, (rho, blend_dc, home_adv) in enumerate(
            itertools.product(
                self.param_grid["rho"],
                self.param_grid["blend_ratio_dc"],
                self.param_grid["home_advantage"],
            )
        ):
            logger.info(
                "testing_parameters",
                combination=f"{i+1}/{total_combinations}",
                rho=rho,
                blend_dc=blend_dc,
                home_adv=home_adv,
            )

            try:
                accuracy, market_metrics = self.evaluate_parameters(rho, blend_dc, home_adv)

                result = {
                    "params": {
                        "rho": rho,
                        "blend_ratio_dc": blend_dc,
                        "blend_ratio_hist": 1.0 - blend_dc,
                        "home_advantage": home_adv,
                    },
                    "accuracy": accuracy,
                    "market_metrics": market_metrics,
                }

                results.append(result)

                logger.info(
                    "parameters_evaluated",
                    combination=f"{i+1}/{total_combinations}",
                    accuracy=f"{accuracy:.4f}",
                )

            except Exception as e:
                logger.error(
                    "parameter_evaluation_failed",
                    rho=rho,
                    blend_dc=blend_dc,
                    home_adv=home_adv,
                    error=str(e),
                )
                continue

        # Find best parameters
        best_result = max(results, key=lambda x: x["accuracy"])

        return {
            "best_params": best_result["params"],
            "best_accuracy": best_result["accuracy"],
            "all_results": sorted(results, key=lambda x: x["accuracy"], reverse=True),
        }


def main():
    """Run grid search"""
    logger.info("grid_search_started", timestamp=datetime.now().isoformat())

    # Load fixtures from database
    logger.info("loading_fixtures")
    all_fixtures = db_service.get_finished_fixtures(limit=200)

    if len(all_fixtures) < 100:
        logger.error("insufficient_fixtures", count=len(all_fixtures))
        return

    # Split: 150 train, 50 validation
    train_fixtures = all_fixtures[:150]
    validation_fixtures = all_fixtures[150:200]

    logger.info(
        "fixtures_split",
        train=len(train_fixtures),
        validation=len(validation_fixtures),
    )

    # Run grid search
    grid_search = ParameterGridSearch(train_fixtures, validation_fixtures)
    results = grid_search.run_grid_search()

    # Print results
    print("\n" + "=" * 80)
    print("GRID SEARCH RESULTS")
    print("=" * 80)
    print(f"\nBest Accuracy: {results['best_accuracy']:.4f}")
    print("\nBest Parameters:")
    for param, value in results["best_params"].items():
        print(f"  {param}: {value}")

    print("\n\nTop 10 Parameter Combinations:")
    print("-" * 80)
    for i, result in enumerate(results["all_results"][:10], 1):
        params = result["params"]
        accuracy = result["accuracy"]
        print(
            f"{i}. Accuracy: {accuracy:.4f} | rho={params['rho']:.2f}, "
            f"blend_dc={params['blend_ratio_dc']:.2f}, home_adv={params['home_advantage']:.2f}"
        )

    print("\n" + "=" * 80)

    # Save results to file
    import json

    output_file = Path(__file__).parent / "grid_search_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("grid_search_completed", output_file=str(output_file))


if __name__ == "__main__":
    main()
