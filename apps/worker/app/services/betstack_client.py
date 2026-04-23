"""
BetStack API Client
Fetches consensus odds from multiple bookmakers to use as ML features.

Free tier: 1 req/60s — we cache aggressively.
Auth: X-API-Key header
Docs: https://api.betstack.dev/docs#sports
"""

import time
from typing import Any, Dict, List, Optional

import requests
import structlog

from app.config import settings

logger = structlog.get_logger(__name__)

# Simple in-memory cache to respect the 1 req/60s free-tier limit
_cache: Dict[str, tuple[float, Any]] = {}
_CACHE_TTL = 300  # 5 minutes


def _get_cached(key: str) -> Optional[Any]:
    entry = _cache.get(key)
    if entry and (time.time() - entry[0]) < _CACHE_TTL:
        return entry[1]
    return None


def _set_cached(key: str, value: Any) -> None:
    _cache[key] = (time.time(), value)


class BetStackClient:
    """Thin wrapper around the BetStack REST API."""

    def __init__(self) -> None:
        self.base_url = settings.BETSTACK_BASE_URL
        self.api_key = settings.BETSTACK_API_KEY
        self._session = requests.Session()
        self._session.headers.update({"X-API-Key": self.api_key})

    def _get(self, path: str, params: Optional[Dict] = None) -> Optional[Dict]:
        if not self.api_key:
            logger.debug("betstack_key_missing", path=path)
            return None
        cache_key = f"{path}:{params}"
        cached = _get_cached(cache_key)
        if cached is not None:
            return cached
        try:
            resp = self._session.get(f"{self.base_url}{path}", params=params, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            _set_cached(cache_key, data)
            return data
        except requests.RequestException as exc:
            logger.warning("betstack_request_failed", path=path, error=str(exc))
            return None

    def get_events(self, sport: str = "soccer", league_id: Optional[int] = None) -> List[Dict]:
        """Fetch upcoming events with embedded lines (odds)."""
        params: Dict[str, Any] = {"sport": sport, "include_lines": "true"}
        if league_id:
            params["league_id"] = league_id
        data = self._get("/events", params=params)
        if data is None:
            return []
        return data.get("data", data) if isinstance(data, dict) else []

    def get_consensus_odds(self, event_id: str) -> Optional[Dict[str, float]]:
        """
        Return consensus 1X2 odds for a single event as implied probabilities.
        Returns dict with keys 'home_win', 'draw', 'away_win', or None if unavailable.
        """
        data = self._get(f"/events/{event_id}/lines")
        if not data:
            return None
        lines = data.get("data", data) if isinstance(data, dict) else data
        if not lines:
            return None

        # Aggregate across bookmakers — simple average of implied probs
        home_probs, draw_probs, away_probs = [], [], []
        for line in lines if isinstance(lines, list) else [lines]:
            try:
                home_odds = float(line.get("home_odds") or line.get("home") or 0)
                draw_odds = float(line.get("draw_odds") or line.get("draw") or 0)
                away_odds = float(line.get("away_odds") or line.get("away") or 0)
                if home_odds > 1 and draw_odds > 1 and away_odds > 1:
                    home_probs.append(1 / home_odds)
                    draw_probs.append(1 / draw_odds)
                    away_probs.append(1 / away_odds)
            except (TypeError, ValueError):
                continue

        if not home_probs:
            return None

        # Normalize to remove overround
        raw_home = sum(home_probs) / len(home_probs)
        raw_draw = sum(draw_probs) / len(draw_probs)
        raw_away = sum(away_probs) / len(away_probs)
        total = raw_home + raw_draw + raw_away
        if total <= 0:
            return None

        return {
            "home_win": raw_home / total,
            "draw": raw_draw / total,
            "away_win": raw_away / total,
        }

    def find_event_by_teams(
        self, home_team: str, away_team: str, sport: str = "soccer"
    ) -> Optional[str]:
        """
        Search events to find the BetStack event_id for a given fixture.
        Returns event_id string or None.
        """
        events = self.get_events(sport=sport)
        home_lower = home_team.lower()
        away_lower = away_team.lower()
        for event in events:
            h = str(event.get("home_team") or event.get("home") or "").lower()
            a = str(event.get("away_team") or event.get("away") or "").lower()
            if home_lower in h and away_lower in a:
                return str(event.get("id") or event.get("event_id") or "")
        return None


# Singleton
betstack_client = BetStackClient()
