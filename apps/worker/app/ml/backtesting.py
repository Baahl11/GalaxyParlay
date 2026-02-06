"""
Backtesting Framework for GalaxyParlay Predictions

Validates model improvements by comparing OLD vs NEW model performance
on historical fixtures with known outcomes.

Metrics:
- Accuracy: % of correct predictions
- Brier Score: Measure of calibration (lower = better)
- Log Loss: Probabilistic accuracy (lower = better)
- ROI: Return on Investment (% profit if betting at odds)
- Sharpe Ratio: Risk-adjusted returns
- Correlation Matrix: For smart parlay construction

Expected improvement from Phase 3 enhancements: +8-12% accuracy
"""

import json
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import structlog
from scipy.stats import pearsonr

logger = structlog.get_logger()


class BacktestingFramework:
    """
    Comprehensive backtesting framework for betting predictions

    Compares OLD model (baseline) vs NEW model (with improvements)
    """

    def __init__(self):
        self.results = {
            "old_model": defaultdict(list),
            "new_model": defaultdict(list),
            "market_stats": {},
        }
        self.fixtures_tested = 0
        self.predictions_tested = 0

    def add_prediction_result(
        self,
        model_type: str,  # 'old_model' or 'new_model'
        market_key: str,
        predicted_prob: float,
        actual_outcome: float,  # 0 or 1
        odds: Optional[float] = None,
        confidence: Optional[float] = None,
        fixture_id: Optional[int] = None,
        league_id: Optional[int] = None,
    ):
        """
        Record a single prediction result

        Args:
            model_type: 'old_model' or 'new_model'
            market_key: e.g., 'match_winner_home', 'btts_yes', 'over_2_5'
            predicted_prob: Model's predicted probability (0-1)
            actual_outcome: What actually happened (1 = yes, 0 = no)
            odds: Bookmaker odds for this outcome
            confidence: Model's confidence (0-1)
            fixture_id: ID of the fixture being predicted
            league_id: ID of the league (for per-league analysis)
        """
        self.results[model_type][market_key].append(
            {
                "predicted": predicted_prob,
                "actual": actual_outcome,
                "odds": odds,
                "confidence": confidence,
                "fixture_id": fixture_id,
                "league_id": league_id,
                "correct": (
                    1
                    if (predicted_prob > 0.5 and actual_outcome == 1)
                    or (predicted_prob <= 0.5 and actual_outcome == 0)
                    else 0
                ),
            }
        )

        self.predictions_tested += 1

    def calculate_accuracy(self, model_type: str, market_key: str = None) -> float:
        """
        Calculate simple accuracy (% correct)

        Args:
            model_type: 'old_model' or 'new_model'
            market_key: Specific market (None = all markets)
        """
        if market_key:
            results = self.results[model_type].get(market_key, [])
        else:
            # Aggregate all markets
            results = []
            for market_results in self.results[model_type].values():
                results.extend(market_results)

        if not results:
            return 0.0

        correct = sum(r["correct"] for r in results)
        total = len(results)

        return correct / total if total > 0 else 0.0

    def calculate_brier_score(self, model_type: str, market_key: str = None) -> float:
        """
        Calculate Brier Score (measure of calibration)

        Brier Score = mean((predicted - actual)^2)
        Lower is better. Perfect prediction = 0, worst = 1

        Good calibration: <0.15, Excellent: <0.10
        """
        if market_key:
            results = self.results[model_type].get(market_key, [])
        else:
            results = []
            for market_results in self.results[model_type].values():
                results.extend(market_results)

        if not results:
            return 1.0

        squared_errors = [(r["predicted"] - r["actual"]) ** 2 for r in results]

        return np.mean(squared_errors)

    def calculate_log_loss(self, model_type: str, market_key: str = None) -> float:
        """
        Calculate Log Loss (cross-entropy loss)

        Log Loss = -mean(actual * log(predicted) + (1-actual) * log(1-predicted))
        Lower is better. Perfect = 0, worst = infinity

        Good: <0.50, Excellent: <0.30
        """
        if market_key:
            results = self.results[model_type].get(market_key, [])
        else:
            results = []
            for market_results in self.results[model_type].values():
                results.extend(market_results)

        if not results:
            return 10.0

        # Add epsilon to avoid log(0)
        epsilon = 1e-15

        log_losses = []
        for r in results:
            pred = np.clip(r["predicted"], epsilon, 1 - epsilon)
            actual = r["actual"]

            loss = -(actual * np.log(pred) + (1 - actual) * np.log(1 - pred))
            log_losses.append(loss)

        return np.mean(log_losses)

    def calculate_roi(
        self,
        model_type: str,
        market_key: str = None,
        min_confidence: float = 0.6,
        min_edge: float = 0.05,
    ) -> Dict[str, float]:
        """
        Calculate Return on Investment (ROI)

        Simulates betting $1 on each prediction meeting criteria:
        - Confidence >= min_confidence
        - Edge >= min_edge (predicted_prob * odds > 1 + min_edge)

        Returns:
            total_bets: Number of bets placed
            total_staked: Total money bet
            total_returned: Total money won back
            roi: Return on Investment (%)
            profit: Net profit
        """
        if market_key:
            results = self.results[model_type].get(market_key, [])
        else:
            results = []
            for market_results in self.results[model_type].values():
                results.extend(market_results)

        total_bets = 0
        total_staked = 0.0
        total_returned = 0.0

        for r in results:
            if r.get("odds") is None or r.get("confidence") is None:
                continue

            # Check if prediction meets betting criteria
            confidence = r["confidence"]
            predicted_prob = r["predicted"]
            odds = r["odds"]

            # Calculate edge (expected value)
            expected_value = predicted_prob * odds
            edge = expected_value - 1.0

            # Only bet if criteria met
            if confidence >= min_confidence and edge >= min_edge:
                total_bets += 1
                stake = 1.0
                total_staked += stake

                # If prediction correct, return stake + profit
                if r["correct"] == 1:
                    total_returned += stake * odds

        roi = ((total_returned - total_staked) / total_staked * 100) if total_staked > 0 else 0.0
        profit = total_returned - total_staked

        return {
            "total_bets": total_bets,
            "total_staked": round(total_staked, 2),
            "total_returned": round(total_returned, 2),
            "roi": round(roi, 2),
            "profit": round(profit, 2),
        }

    def calculate_sharpe_ratio(
        self,
        model_type: str,
        market_key: str = None,
        min_confidence: float = 0.6,
        min_edge: float = 0.05,
        risk_free_rate: float = 0.0,
    ) -> float:
        """
        Calculate Sharpe Ratio (risk-adjusted returns)

        Sharpe = (mean_return - risk_free_rate) / std_return

        Higher is better:
        - >1.0: Good
        - >2.0: Very Good
        - >3.0: Excellent
        """
        if market_key:
            results = self.results[model_type].get(market_key, [])
        else:
            results = []
            for market_results in self.results[model_type].values():
                results.extend(market_results)

        returns = []

        for r in results:
            if r.get("odds") is None or r.get("confidence") is None:
                continue

            confidence = r["confidence"]
            predicted_prob = r["predicted"]
            odds = r["odds"]

            expected_value = predicted_prob * odds
            edge = expected_value - 1.0

            if confidence >= min_confidence and edge >= min_edge:
                # Calculate return for this bet (profit/loss per $1 staked)
                if r["correct"] == 1:
                    bet_return = odds - 1.0  # Profit
                else:
                    bet_return = -1.0  # Loss

                returns.append(bet_return)

        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns)

        if std_return == 0:
            return 0.0

        sharpe = (mean_return - risk_free_rate) / std_return

        return round(sharpe, 3)

    def calculate_correlation_matrix(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate correlation matrix between different markets

        Used for smart parlay construction:
        - High correlation = avoid combining in parlay
        - Low/negative correlation = good parlay candidates

        Returns:
            Dict of market pairs with correlation coefficients
        """
        # Get all markets with sufficient data
        markets = [
            m for m in self.results["new_model"].keys() if len(self.results["new_model"][m]) >= 10
        ]

        correlation_matrix = {}

        for i, market_a in enumerate(markets):
            correlation_matrix[market_a] = {}

            for market_b in markets[i:]:  # Only compute upper triangle
                results_a = self.results["new_model"][market_a]
                results_b = self.results["new_model"][market_b]

                # Only correlate if same number of predictions (same fixtures)
                if len(results_a) != len(results_b):
                    continue

                # Get actual outcomes
                outcomes_a = [r["actual"] for r in results_a]
                outcomes_b = [r["actual"] for r in results_b]

                # Calculate Pearson correlation
                if len(outcomes_a) >= 10:
                    try:
                        corr, p_value = pearsonr(outcomes_a, outcomes_b)
                        correlation_matrix[market_a][market_b] = round(corr, 3)

                        # Symmetric
                        if market_b not in correlation_matrix:
                            correlation_matrix[market_b] = {}
                        correlation_matrix[market_b][market_a] = round(corr, 3)
                    except Exception as e:
                        logger.warning(
                            "correlation_calc_failed",
                            market_a=market_a,
                            market_b=market_b,
                            error=str(e),
                        )

        return correlation_matrix

    def compare_models(self) -> Dict[str, Any]:
        """
        Generate comprehensive comparison report

        Returns OLD vs NEW model performance across all metrics
        """
        report = {
            "summary": {
                "fixtures_tested": self.fixtures_tested,
                "predictions_tested": self.predictions_tested,
                "markets_tested": len(self.results["new_model"]),
            },
            "old_model": {},
            "new_model": {},
            "improvement": {},
            "by_market": {},
        }

        # Overall metrics for both models
        for model_type in ["old_model", "new_model"]:
            report[model_type] = {
                "accuracy": round(self.calculate_accuracy(model_type), 4),
                "brier_score": round(self.calculate_brier_score(model_type), 4),
                "log_loss": round(self.calculate_log_loss(model_type), 4),
                "roi_data": self.calculate_roi(model_type),
                "sharpe_ratio": self.calculate_sharpe_ratio(model_type),
            }

        # Calculate improvements
        old_acc = report["old_model"]["accuracy"]
        new_acc = report["new_model"]["accuracy"]
        acc_improvement = ((new_acc - old_acc) / old_acc * 100) if old_acc > 0 else 0

        old_brier = report["old_model"]["brier_score"]
        new_brier = report["new_model"]["brier_score"]
        brier_improvement = ((old_brier - new_brier) / old_brier * 100) if old_brier > 0 else 0

        report["improvement"] = {
            "accuracy_delta": round(new_acc - old_acc, 4),
            "accuracy_improvement_pct": round(acc_improvement, 2),
            "brier_improvement_pct": round(brier_improvement, 2),
            "roi_delta": round(
                report["new_model"]["roi_data"]["roi"] - report["old_model"]["roi_data"]["roi"], 2
            ),
        }

        # Per-market breakdown
        all_markets = set(
            list(self.results["old_model"].keys()) + list(self.results["new_model"].keys())
        )

        for market in all_markets:
            if len(self.results["new_model"].get(market, [])) < 5:
                continue  # Skip markets with insufficient data

            old_market_acc = self.calculate_accuracy("old_model", market)
            new_market_acc = self.calculate_accuracy("new_model", market)

            report["by_market"][market] = {
                "old_accuracy": round(old_market_acc, 3),
                "new_accuracy": round(new_market_acc, 3),
                "improvement": round(new_market_acc - old_market_acc, 3),
                "sample_size": len(self.results["new_model"].get(market, [])),
            }

        return report

    def export_results(self, filepath: str):
        """Export backtesting results to JSON file"""
        report = self.compare_models()

        # Add correlation matrix
        report["correlation_matrix"] = self.calculate_correlation_matrix()

        # Add raw results for FASE 5 deep analysis
        report["raw_predictions"] = {
            "old_model": dict(self.results["old_model"]),
            "new_model": dict(self.results["new_model"]),
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)

        logger.info("backtesting_results_exported", filepath=filepath)

    def print_summary(self):
        """Print human-readable summary to console"""
        report = self.compare_models()

        print("\n" + "=" * 60)
        print("BACKTESTING RESULTS - OLD MODEL vs NEW MODEL")
        print("=" * 60)

        print(f"\nFixtures Tested: {report['summary']['fixtures_tested']}")
        print(f"Predictions Tested: {report['summary']['predictions_tested']}")
        print(f"Markets Tested: {report['summary']['markets_tested']}")

        print("\n" + "-" * 60)
        print("OVERALL PERFORMANCE")
        print("-" * 60)

        print("\nOLD MODEL:")
        print(f"  Accuracy: {report['old_model']['accuracy']:.2%}")
        print(f"  Brier Score: {report['old_model']['brier_score']:.4f}")
        print(f"  Log Loss: {report['old_model']['log_loss']:.4f}")
        print(f"  ROI: {report['old_model']['roi_data']['roi']:.2f}%")
        print(f"  Sharpe Ratio: {report['old_model']['sharpe_ratio']:.2f}")

        print("\nNEW MODEL:")
        print(f"  Accuracy: {report['new_model']['accuracy']:.2%}")
        print(f"  Brier Score: {report['new_model']['brier_score']:.4f}")
        print(f"  Log Loss: {report['new_model']['log_loss']:.4f}")
        print(f"  ROI: {report['new_model']['roi_data']['roi']:.2f}%")
        print(f"  Sharpe Ratio: {report['new_model']['sharpe_ratio']:.2f}")

        print("\n" + "-" * 60)
        print("IMPROVEMENT")
        print("-" * 60)
        print(f"  Accuracy: +{report['improvement']['accuracy_improvement_pct']:.2f}%")
        print(f"  Brier Score: +{report['improvement']['brier_improvement_pct']:.2f}%")
        print(f"  ROI Delta: +{report['improvement']['roi_delta']:.2f}%")

        print("\n" + "-" * 60)
        print("TOP 5 IMPROVED MARKETS")
        print("-" * 60)

        # Sort markets by improvement
        sorted_markets = sorted(
            report["by_market"].items(), key=lambda x: x[1]["improvement"], reverse=True
        )[:5]

        for market, data in sorted_markets:
            print(f"\n{market}:")
            print(f"  OLD: {data['old_accuracy']:.2%} -> NEW: {data['new_accuracy']:.2%}")
            print(f"  Improvement: +{data['improvement']:.2%}")
            print(f"  Sample Size: {data['sample_size']}")

        print("\n" + "=" * 60 + "\n")


# Global instance
backtesting = BacktestingFramework()
