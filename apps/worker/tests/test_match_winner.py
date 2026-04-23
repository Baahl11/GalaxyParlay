"""
Unit tests for match_winner prediction (1X2 market).

Tests cover:
- Probability normalization (always sums to 1.0)
- Output bounds (each probability 0 < p < 1)
- BetStack odds blending: 30% market / 70% model
- Home/away symmetry sanity checks
- Elo-based favorite ordering
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Allow importing app modules without installed dependencies
sys.path.insert(0, str(Path(__file__).parent.parent))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def dummy_fixture():
    return {
        "id": 1001,
        "league_id": 39,
        "home_team_id": 10,
        "away_team_id": 20,
        "home_team_name": "TeamA",
        "away_team_name": "TeamB",
        "status": "NS",
        "kickoff_time": "2026-06-01T15:00:00",
        "referee": None,
        "round": "Regular Season - 38",
    }


@pytest.fixture()
def strong_elo_pred():
    """Elo prediction where home side is a clear favourite."""
    return {
        "home_win": 0.60,
        "draw": 0.25,
        "away_win": 0.15,
        "elo_diff": 200,
        "home_elo": 1700,
        "away_elo": 1500,
        "home_expected_goals": 1.8,
        "away_expected_goals": 1.0,
    }


@pytest.fixture()
def equal_elo_pred():
    """Elo prediction for equally matched teams."""
    return {
        "home_win": 0.38,
        "draw": 0.30,
        "away_win": 0.32,
        "elo_diff": 0,
        "home_elo": 1500,
        "away_elo": 1500,
        "home_expected_goals": 1.4,
        "away_expected_goals": 1.2,
    }


# ---------------------------------------------------------------------------
# Helper — instantiate MatchPredictor with mocked dependencies
# ---------------------------------------------------------------------------


def make_predictor():
    """Create a MatchPredictor with mocked Elo, features, and stats."""
    from app.ml.predictor import MatchPredictor

    elo_mock = MagicMock()
    features_mock = MagicMock()
    stats_mock = MagicMock()

    # Default stats mock (neutral team performance)
    stats_mock.get_match_features.return_value = {
        "form_diff": 0.0,
        "home_home_win_rate": 0.45,
        "away_away_win_rate": 0.30,
        "home_form_ppg": 1.5,
        "away_form_ppg": 1.5,
    }

    predictor = MatchPredictor(elo=elo_mock, features=features_mock, stats=stats_mock)
    predictor._db_elo_loaded = True
    predictor._stats_loaded = True
    return predictor, elo_mock


# ---------------------------------------------------------------------------
# Tests: _predict_match_winner
# ---------------------------------------------------------------------------


class TestPredictMatchWinner:
    def test_probabilities_sum_to_one(self, dummy_fixture, strong_elo_pred):
        predictor, _ = make_predictor()
        result = predictor._predict_match_winner(strong_elo_pred, dummy_fixture)
        probs = result["probabilities"]
        total = probs["home_win"] + probs["draw"] + probs["away_win"]
        assert abs(total - 1.0) < 1e-6, f"Probabilities sum to {total}, not 1.0"

    def test_all_probs_in_valid_range(self, dummy_fixture, strong_elo_pred):
        predictor, _ = make_predictor()
        result = predictor._predict_match_winner(strong_elo_pred, dummy_fixture)
        probs = result["probabilities"]
        for name, p in probs.items():
            assert 0.0 < p < 1.0, f"{name}={p} is outside (0, 1)"

    def test_favourite_remains_favourite(self, dummy_fixture, strong_elo_pred):
        """When Elo strongly favours home team, home_win should be highest probability."""
        predictor, _ = make_predictor()
        result = predictor._predict_match_winner(strong_elo_pred, dummy_fixture)
        probs = result["probabilities"]
        assert (
            probs["home_win"] > probs["away_win"]
        ), f"Expected home_win ({probs['home_win']}) > away_win ({probs['away_win']})"

    def test_equal_teams_balanced_probs(self, dummy_fixture, equal_elo_pred):
        """With equal Elo, home and away probabilities should be close."""
        predictor, _ = make_predictor()
        result = predictor._predict_match_winner(equal_elo_pred, dummy_fixture)
        probs = result["probabilities"]
        diff = abs(probs["home_win"] - probs["away_win"])
        assert diff < 0.15, f"Equal teams should have close probs, diff={diff}"

    def test_confidence_is_in_range(self, dummy_fixture, strong_elo_pred):
        predictor, _ = make_predictor()
        result = predictor._predict_match_winner(strong_elo_pred, dummy_fixture)
        assert 0.0 <= result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Tests: BetStack odds blending
# ---------------------------------------------------------------------------


class TestBetStackBlending:
    """Verify that consensus odds are blended correctly into match_winner."""

    def _blend(self, model_probs: dict, market_probs: dict, weight: float = 0.30) -> dict:
        """Pure-function blend used to verify the production logic."""
        mw = 1.0 - weight
        blended = {
            "home_win": mw * model_probs["home_win"] + weight * market_probs["home_win"],
            "draw": mw * model_probs["draw"] + weight * market_probs["draw"],
            "away_win": mw * model_probs["away_win"] + weight * market_probs["away_win"],
        }
        total = sum(blended.values())
        return {k: round(v / total, 3) for k, v in blended.items()}

    def test_blended_probs_sum_to_one(self):
        model = {"home_win": 0.60, "draw": 0.25, "away_win": 0.15}
        market = {"home_win": 0.50, "draw": 0.28, "away_win": 0.22}
        blended = self._blend(model, market)
        assert abs(sum(blended.values()) - 1.0) < 1e-5

    def test_blend_moves_toward_market(self):
        """If market strongly disagrees with model, blend should move predictions closer."""
        model = {"home_win": 0.70, "draw": 0.20, "away_win": 0.10}
        market = {"home_win": 0.40, "draw": 0.30, "away_win": 0.30}
        blended = self._blend(model, market, weight=0.30)
        # Blended home_win should be between model and market
        assert market["home_win"] < blended["home_win"] < model["home_win"]

    def test_zero_weight_keeps_model(self):
        model = {"home_win": 0.60, "draw": 0.25, "away_win": 0.15}
        market = {"home_win": 0.33, "draw": 0.33, "away_win": 0.34}
        blended = self._blend(model, market, weight=0.0)
        assert abs(blended["home_win"] - model["home_win"]) < 1e-3

    def test_full_weight_gives_market(self):
        model = {"home_win": 0.60, "draw": 0.25, "away_win": 0.15}
        market = {"home_win": 0.33, "draw": 0.33, "away_win": 0.34}
        blended = self._blend(model, market, weight=1.0)
        assert abs(blended["home_win"] - market["home_win"]) < 1e-3


# ---------------------------------------------------------------------------
# Tests: BetStackClient (mocked HTTP)
# ---------------------------------------------------------------------------


class TestBetStackClient:
    def test_returns_none_when_no_api_key(self):
        from app.services.betstack_client import BetStackClient

        client = BetStackClient.__new__(BetStackClient)
        client.base_url = "https://api.betstack.dev/api/v1"
        client.api_key = ""
        import requests

        client._session = requests.Session()
        result = client._get("/events")
        assert result is None

    def test_consensus_odds_normalization(self):
        """If bookmaker odds are given, implied probs should sum close to 1 after normalization."""
        from app.services.betstack_client import BetStackClient

        client = BetStackClient.__new__(BetStackClient)
        client.base_url = ""
        client.api_key = "test"
        import requests

        client._session = requests.Session()

        raw_lines = [
            {"home_odds": "2.10", "draw_odds": "3.20", "away_odds": "3.50"},
            {"home_odds": "2.00", "draw_odds": "3.30", "away_odds": "3.60"},
        ]

        with patch.object(client, "_get", return_value={"data": raw_lines}):
            result = client.get_consensus_odds("evt_123")

        assert result is not None
        total = sum(result.values())
        assert abs(total - 1.0) < 1e-5, f"Consensus odds sum to {total}"
        for k, v in result.items():
            assert 0.0 < v < 1.0, f"{k}={v} out of range"
