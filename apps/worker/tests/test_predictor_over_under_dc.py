"""
Unit tests for Dixon-Coles over/under logic in MatchPredictor.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ml.predictor import MatchPredictor


def test_dc_over_under_probabilities_sum_to_one():
    predictor = MatchPredictor(stats=MagicMock())
    predictor.stats.predict_over_under.return_value = {
        "over": 0.55,
        "expected_total_goals": 2.7,
    }

    elo_pred = {"home_expected_goals": 1.6, "away_expected_goals": 1.1}
    fixture = {"home_team_id": 1, "away_team_id": 2, "league_id": 39}

    result = predictor._predict_over_under(elo_pred, fixture)
    over = result["probabilities"]["over"]
    under = result["probabilities"]["under"]

    assert 0.0 <= over <= 1.0
    assert 0.0 <= under <= 1.0
    assert abs(over + under - 1.0) < 1e-6
    assert "dc_over" in result["features"]
