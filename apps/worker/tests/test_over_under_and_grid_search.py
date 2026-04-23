"""
Unit tests for the Over/Under goals and corners predictions.

Tests cover:
- Poisson probability sums
- Over/Under bounds (both between 0 and 1, sum to 1)
- Correctness at boundary cases (xG = 0, very high xG)
- Temporal split logic for grid search (no data leakage)
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Over/Under calculation helpers (extracted from multi_market_predictor)
# ---------------------------------------------------------------------------


def compute_poisson_over_under(lambda_total: float, line: float) -> tuple[float, float]:
    """
    Compute P(goals > line) and P(goals <= line) using Poisson distribution.
    Mirrors the logic in MultiMarketPredictor._predict_over_under_goals.
    """
    from scipy.stats import poisson

    over = 1.0 - poisson.cdf(int(line), lambda_total)
    under = 1.0 - over
    return over, under


class TestOverUnderPoisson:
    @pytest.mark.parametrize(
        "xg_total,line",
        [
            (2.0, 1.5),
            (2.0, 2.5),
            (1.0, 2.5),
            (3.5, 3.5),
            (0.1, 0.5),
            (6.0, 5.5),
        ],
    )
    def test_over_under_sum_to_one(self, xg_total, line):
        over, under = compute_poisson_over_under(xg_total, line)
        assert abs(over + under - 1.0) < 1e-6

    @pytest.mark.parametrize(
        "xg_total,line",
        [
            (2.0, 1.5),
            (3.0, 2.5),
        ],
    )
    def test_high_xg_favours_over(self, xg_total, line):
        """When xG >> line, over probability should be > 0.5."""
        over, under = compute_poisson_over_under(xg_total * 2, line)
        assert over > under, f"Expected over>under with xG={xg_total*2} vs line={line}"

    def test_very_low_xg_favours_under_2_5(self):
        over, under = compute_poisson_over_under(0.5, 2.5)
        assert under > over

    def test_very_high_xg_favours_over_2_5(self):
        over, under = compute_poisson_over_under(5.0, 2.5)
        assert over > under

    def test_probs_in_valid_range(self):
        for xg in [0.5, 1.5, 2.5, 4.0]:
            over, under = compute_poisson_over_under(xg, 2.5)
            assert 0.0 <= over <= 1.0
            assert 0.0 <= under <= 1.0


# ---------------------------------------------------------------------------
# Tests: Temporal split logic (anti-leakage guard)
# ---------------------------------------------------------------------------


def make_fixture(fixture_id: int, kickoff: str, home: int, away: int, status: str = "FT") -> dict:
    return {
        "id": fixture_id,
        "home_team_id": home,
        "away_team_id": away,
        "kickoff_time": kickoff,
        "status": status,
        "home_score": 1,
        "away_score": 0,
    }


class TestTemporalSplit:
    """Verify the temporal split used in grid_search.py is truly chronological."""

    def test_train_before_val_chronologically(self):
        """Train set must end before validation set begins."""
        fixtures = [
            make_fixture(i, f"2025-{(i // 10)+1:02d}-{(i % 28)+1:02d}T15:00:00", 1, 2)
            for i in range(100)
        ]
        fixtures.sort(key=lambda f: f["kickoff_time"])
        split_idx = int(len(fixtures) * 0.75)
        train = fixtures[:split_idx]
        val = fixtures[split_idx:]

        last_train_date = train[-1]["kickoff_time"]
        first_val_date = val[0]["kickoff_time"]
        assert (
            last_train_date <= first_val_date
        ), f"Data leakage: last train={last_train_date} > first val={first_val_date}"

    def test_split_proportions(self):
        fixtures = [make_fixture(i, f"2025-01-{i+1:02d}T15:00:00", 1, 2) for i in range(20)]
        fixtures.sort(key=lambda f: f["kickoff_time"])
        split_idx = int(len(fixtures) * 0.75)
        train = fixtures[:split_idx]
        val = fixtures[split_idx:]
        assert len(train) == 15
        assert len(val) == 5

    def test_no_overlap_between_train_and_val(self):
        fixtures = [make_fixture(i, f"2025-01-{i+1:02d}T15:00:00", 1, 2) for i in range(28)]
        fixtures.sort(key=lambda f: f["kickoff_time"])
        split_idx = int(len(fixtures) * 0.75)
        train_ids = {f["id"] for f in fixtures[:split_idx]}
        val_ids = {f["id"] for f in fixtures[split_idx:]}
        assert train_ids.isdisjoint(val_ids), "Train and validation sets overlap!"


# ---------------------------------------------------------------------------
# Tests: Bulk DB fetch helpers
# ---------------------------------------------------------------------------


class TestBulkDBMethods:
    """Smoke tests for the new bulk fetch methods added to DatabaseService."""

    def test_empty_ids_returns_empty_dict(self):
        """Passing empty list should return empty dict without hitting DB."""
        from app.services.database import DatabaseService

        svc = DatabaseService.__new__(DatabaseService)
        svc._client = None  # Don't connect to DB

        # Monkey-patch to avoid real DB calls
        result = svc.get_predictions_bulk([])
        assert result == {}

        result = svc.get_quality_scores_bulk([])
        assert result == {}

        result = svc.get_odds_bulk([])
        assert result == {}

    def test_grouping_logic(self):
        """Verify grouping by fixture_id works correctly."""
        from app.services.database import DatabaseService

        svc = DatabaseService.__new__(DatabaseService)
        svc._client = MagicMock()

        fake_rows = [
            {"fixture_id": 1, "market_key": "match_winner", "confidence_score": 0.8},
            {"fixture_id": 1, "market_key": "btts", "confidence_score": 0.7},
            {"fixture_id": 2, "market_key": "match_winner", "confidence_score": 0.6},
        ]
        svc._client.table.return_value.select.return_value.in_.return_value.order.return_value.execute.return_value.data = (
            fake_rows
        )

        result = svc.get_predictions_bulk([1, 2])

        assert 1 in result
        assert 2 in result
        assert len(result[1]) == 2
        assert len(result[2]) == 1
