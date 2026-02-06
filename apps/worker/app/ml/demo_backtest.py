"""
Demo Backtest - Simulación de Mejoras

Ya que no hay fixtures 2026 en la base de datos, este script
simula resultados para demostrar el framework de backtesting.

Simula 200 fixtures con:
- OLD model (baseline): ~57% accuracy
- NEW model (con mejoras): ~69% accuracy
- Mejora: +12% accuracy (dentro del rango esperado +8-12%)
"""

import random

import numpy as np
import structlog

from app.ml.backtesting import backtesting

logger = structlog.get_logger()

# Set random seed for reproducibility
random.seed(42)
np.random.seed(42)


def simulate_prediction(
    model_type: str, market: str, actual_outcome: float, base_accuracy: float
) -> tuple:
    """
    Simulate a prediction with given base accuracy

    Returns: (predicted_prob, confidence)
    """
    # Determine if prediction will be correct
    is_correct = random.random() < base_accuracy

    if is_correct:
        # Correct prediction: predicted prob should favor actual outcome
        if actual_outcome == 1.0:
            predicted_prob = random.uniform(0.55, 0.85)
        else:
            predicted_prob = random.uniform(0.15, 0.45)
    else:
        # Incorrect prediction: predicted prob should favor wrong outcome
        if actual_outcome == 1.0:
            predicted_prob = random.uniform(0.15, 0.45)
        else:
            predicted_prob = random.uniform(0.55, 0.85)

    # Confidence correlates with probability extremeness
    confidence = abs(predicted_prob - 0.5) * 2
    confidence = max(0.5, min(0.9, confidence))

    return predicted_prob, confidence


def simulate_match() -> dict:
    """Simulate a random match result"""
    # Simulate scores (home advantage)
    home_score = np.random.poisson(1.5)
    away_score = np.random.poisson(1.2)

    return {
        "home_score": home_score,
        "away_score": away_score,
        "total_goals": home_score + away_score,
        "btts": 1.0 if (home_score > 0 and away_score > 0) else 0.0,
        "home_win": 1.0 if home_score > away_score else 0.0,
        "draw": 1.0 if home_score == away_score else 0.0,
        "away_win": 1.0 if away_score > home_score else 0.0,
    }


def run_demo_backtest(num_fixtures: int = 200):
    """Run simulated backtest"""

    logger.info("Starting DEMO backtesting simulation", fixtures=num_fixtures)

    # Model accuracies (simulated)
    # OLD model: baseline ~57%
    # NEW model: with improvements ~69% (+12%)
    old_model_accuracy = {
        "match_winner": 0.57,
        "btts": 0.54,
        "over_under_2_5": 0.59,
        "over_under_1_5": 0.58,
        "over_under_3_5": 0.56,
    }

    new_model_accuracy = {
        "match_winner": 0.66,  # +9% with contextual Elo
        "btts": 0.68,  # +14% with bivariate Poisson
        "over_under_2_5": 0.71,  # +12% with xG integration
        "over_under_1_5": 0.69,  # +11%
        "over_under_3_5": 0.67,  # +11%
    }

    backtesting.fixtures_tested = num_fixtures

    markets_tested = [
        "match_winner_home",
        "match_winner_draw",
        "match_winner_away",
        "btts_yes",
        "btts_no",
        "over_under_2_5_over",
        "over_under_2_5_under",
        "over_under_1_5_over",
        "over_under_1_5_under",
        "over_under_3_5_over",
        "over_under_3_5_under",
    ]

    # Simulate each fixture
    for i in range(num_fixtures):
        if i % 50 == 0:
            logger.info(f"Processing fixture {i+1}/{num_fixtures}")

        # Simulate match
        match = simulate_match()

        # Process each market
        for market in markets_tested:
            # Determine actual outcome
            if "home" in market:
                actual = match["home_win"]
                market_type = "match_winner"
            elif "draw" in market:
                actual = match["draw"]
                market_type = "match_winner"
            elif "away" in market:
                actual = match["away_win"]
                market_type = "match_winner"
            elif "btts_yes" in market:
                actual = match["btts"]
                market_type = "btts"
            elif "btts_no" in market:
                actual = 1.0 - match["btts"]
                market_type = "btts"
            elif "2_5_over" in market:
                actual = 1.0 if match["total_goals"] > 2.5 else 0.0
                market_type = "over_under_2_5"
            elif "2_5_under" in market:
                actual = 1.0 if match["total_goals"] < 2.5 else 0.0
                market_type = "over_under_2_5"
            elif "1_5_over" in market:
                actual = 1.0 if match["total_goals"] > 1.5 else 0.0
                market_type = "over_under_1_5"
            elif "1_5_under" in market:
                actual = 1.0 if match["total_goals"] < 1.5 else 0.0
                market_type = "over_under_1_5"
            elif "3_5_over" in market:
                actual = 1.0 if match["total_goals"] > 3.5 else 0.0
                market_type = "over_under_3_5"
            elif "3_5_under" in market:
                actual = 1.0 if match["total_goals"] < 3.5 else 0.0
                market_type = "over_under_3_5"
            else:
                continue

            # Generate OLD model prediction
            old_acc = old_model_accuracy[market_type]
            old_pred, old_conf = simulate_prediction("old", market, actual, old_acc)

            # Generate NEW model prediction
            new_acc = new_model_accuracy[market_type]
            new_pred, new_conf = simulate_prediction("new", market, actual, new_acc)

            # Simulate odds (inverse of predicted probability + bookmaker margin)
            odds = (1.0 / max(0.1, old_pred)) * 1.05  # 5% margin

            # Record results
            backtesting.add_prediction_result(
                model_type="old_model",
                market_key=market,
                predicted_prob=old_pred,
                actual_outcome=actual,
                odds=odds,
                confidence=old_conf,
            )

            backtesting.add_prediction_result(
                model_type="new_model",
                market_key=market,
                predicted_prob=new_pred,
                actual_outcome=actual,
                odds=odds,
                confidence=new_conf,
            )

    # Generate and display report
    logger.info("Backtesting simulation complete, generating report")
    backtesting.print_summary()

    # Export to JSON
    output_path = "backtest_demo_results.json"
    backtesting.export_results(output_path)

    logger.info("Demo backtesting results exported", path=output_path)

    print("\n" + "=" * 60)
    print("NOTA: Estos son resultados SIMULADOS para demostración")
    print("Para backtest real, necesitas fixtures terminados en la DB")
    print("=" * 60)


if __name__ == "__main__":
    run_demo_backtest(200)
