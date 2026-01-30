"""
Match Predictor - Generates predictions for fixtures
Combines Elo ratings with statistical features and historical data
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import random
import structlog

from .elo import elo_system, EloRatingSystem
from .features import feature_engineer, FeatureEngineer
from .team_stats import team_stats_calculator, TeamStatsCalculator
from .multi_market_predictor import multi_market_predictor, MultiMarketPredictor

logger = structlog.get_logger()

# Market type configurations - EXPANDED for multi-market predictions
MARKETS = {
    # Core markets (already implemented)
    'match_winner': {
        'outcomes': ['home_win', 'draw', 'away_win'],
        'description': '1X2 Match Result'
    },
    'over_under_2.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Goals Over/Under 2.5'
    },
    'both_teams_score': {
        'outcomes': ['yes', 'no'],
        'description': 'Both Teams to Score'
    },
    
    # Additional goal lines
    'over_under_1.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Goals Over/Under 1.5'
    },
    'over_under_3.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Goals Over/Under 3.5'
    },
    
    # Corners
    'corners_over_under_9.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Corners Over/Under 9.5'
    },
    'corners_over_under_10.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Corners Over/Under 10.5'
    },
    
    # Cards
    'cards_over_under_3.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Cards Over/Under 3.5'
    },
    'cards_over_under_4.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Cards Over/Under 4.5'
    },
    
    # Shots on Target
    'shots_on_target_over_under_8.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Shots on Target Over/Under 8.5'
    },
    
    # Offsides
    'offsides_over_under_4.5': {
        'outcomes': ['over', 'under'],
        'description': 'Total Offsides Over/Under 4.5'
    },
    
    # Team-specific markets
    'home_team_over_under_1.5': {
        'outcomes': ['over', 'under'],
        'description': 'Home Team Goals Over/Under 1.5'
    },
    'away_team_over_under_0.5': {
        'outcomes': ['over', 'under'],
        'description': 'Away Team Goals Over/Under 0.5'
    },
    
    # Half-time markets
    'first_half_over_under_0.5': {
        'outcomes': ['over', 'under'],
        'description': 'First Half Goals Over/Under 0.5'
    }
}


class MatchPredictor:
    """
    Generates predictions for football matches
    
    Uses ensemble approach:
    - 50% Elo-based probabilities
    - 50% Historical statistics (Over/Under, BTTS, Form)
    
    Outputs calibrated probabilities for multiple markets
    """
    
    def __init__(
        self,
        elo: EloRatingSystem = None,
        features: FeatureEngineer = None,
        stats: TeamStatsCalculator = None,
        model_version: str = "v1.1.0"
    ):
        self.elo = elo or elo_system
        self.features = features or feature_engineer
        self.stats = stats or team_stats_calculator
        self.model_version = model_version
        self.model_name = "ensemble_xgb_elo_historical"
        self._db_elo_loaded = False
        self._stats_loaded = False
    
    def load_elo_from_db(self, season: int = 2025):
        """
        Load Elo ratings from database for more accurate predictions
        
        This should be called before running predictions if historical
        Elo data has been calculated.
        """
        try:
            from app.services.database import db_service
            
            elo_records = db_service.get_all_team_elos(season)
            
            if elo_records:
                for record in elo_records:
                    self.elo.ratings[record["team_id"]] = float(record["elo_rating"])
                
                logger.info(
                    "elo_loaded_from_db",
                    teams_loaded=len(elo_records),
                    season=season
                )
                self._db_elo_loaded = True
                return len(elo_records)
            
            return 0
        except Exception as e:
            logger.warning("elo_load_from_db_failed", error=str(e))
            return 0
    
    def load_historical_stats(self):
        """
        Load and calculate historical statistics for all teams
        from finished fixtures in database
        """
        try:
            from app.services.database import db_service
            
            # Get ALL finished fixtures (all seasons)
            fixtures = db_service.get_finished_fixtures(season=None)
            
            if fixtures:
                stats = self.stats.calculate_all_team_stats(fixtures)
                self._stats_loaded = True
                
                logger.info(
                    "historical_stats_loaded",
                    teams=len(stats),
                    fixtures_analyzed=len(fixtures)
                )
                return len(stats)
            
            return 0
        except Exception as e:
            logger.warning("historical_stats_load_failed", error=str(e))
            return 0
    
    def predict_fixture(
        self,
        fixture: Dict[str, Any],
        include_all_markets: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Generate predictions for a fixture
        
        Args:
            fixture: Fixture data from database
            include_all_markets: Whether to predict all markets or just match_winner
        
        Returns:
            List of prediction dicts ready for database insertion
        """
        # Auto-load Elo from DB if not already loaded
        if not self._db_elo_loaded:
            self.load_elo_from_db()
        
        # Auto-load historical stats if not already loaded
        if not self._stats_loaded:
            self.load_historical_stats()
        
        predictions = []
        
        home_id = fixture['home_team_id']
        away_id = fixture['away_team_id']
        league_id = fixture['league_id']
        fixture_id = fixture['id']
        
        # Get Elo-based prediction
        elo_pred = self.elo.predict_match(home_id, away_id, league_id)
        
        # Calculate Expected Goals from Elo
        home_xg = elo_pred.get('home_expected_goals', 1.5)
        away_xg = elo_pred.get('away_expected_goals', 1.2)
        
        # Match Winner prediction
        match_winner_pred = self._predict_match_winner(elo_pred, fixture)
        predictions.append(self._format_prediction(
            fixture_id=fixture_id,
            market_key='match_winner',
            prediction=match_winner_pred['probabilities'],
            confidence=match_winner_pred['confidence'],
            features_used=match_winner_pred.get('features')
        ))
        
        if include_all_markets:
            # Get multi-market predictions (corners, cards, shots, offsides, etc.)
            multi_markets = multi_market_predictor.predict_all_markets(
                home_team_id=home_id,
                away_team_id=away_id,
                home_xg=home_xg,
                away_xg=away_xg
            )
            
            # Extract and format multi-market predictions
            
            # Over/Under Goals (multiple lines)
            over_under = multi_markets.get('over_under', {})
            for line_key, data in over_under.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    line = data.get('line', 2.5)
                    market_key = f"over_under_{str(line).replace('.', '_')}"
                    
                    # Calculate confidence based on probability spread
                    max_prob = max(data['over'], data['under'])
                    confidence = self._calculate_market_confidence(max_prob)
                    
                    predictions.append(self._format_prediction(
                        fixture_id=fixture_id,
                        market_key=market_key,
                        prediction={'over': data['over'], 'under': data['under']},
                        confidence=confidence,
                        features_used={'expected_goals': home_xg + away_xg}
                    ))
            
            # BTTS
            btts = multi_markets.get('btts', {})
            if btts:
                btts_pred = self._predict_btts(elo_pred, fixture)
                predictions.append(self._format_prediction(
                    fixture_id=fixture_id,
                    market_key='both_teams_score',
                    prediction=btts_pred['probabilities'],
                    confidence=btts_pred['confidence'],
                    features_used=btts_pred.get('features')
                ))
            
            # Corners
            corners = multi_markets.get('corners', {})
            for corner_key, data in corners.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    if 'total_over' in corner_key:
                        # Extract line number from key like "total_over_9_5"
                        line_str = corner_key.replace('total_over_', '').replace('_', '.')
                        market_key = f"corners_over_under_{corner_key.replace('total_over_', '')}"
                        
                        max_prob = max(data['over'], data['under'])
                        confidence = self._calculate_market_confidence(max_prob)
                        
                        predictions.append(self._format_prediction(
                            fixture_id=fixture_id,
                            market_key=market_key,
                            prediction={'over': data['over'], 'under': data['under']},
                            confidence=confidence,
                            features_used={'expected_corners': corners.get('expected', {}).get('total', 10.5)}
                        ))
            
            # Cards
            cards = multi_markets.get('cards', {})
            for card_key, data in cards.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    if 'total_over' in card_key:
                        market_key = f"cards_over_under_{card_key.replace('total_over_', '')}"
                        
                        max_prob = max(data['over'], data['under'])
                        confidence = self._calculate_market_confidence(max_prob)
                        
                        predictions.append(self._format_prediction(
                            fixture_id=fixture_id,
                            market_key=market_key,
                            prediction={'over': data['over'], 'under': data['under']},
                            confidence=confidence,
                            features_used={'expected_cards': cards.get('expected', {}).get('total_yellow', 3.5)}
                        ))
            
            # Shots on Target
            shots = multi_markets.get('shots', {})
            for shot_key, data in shots.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    if 'sot_over' in shot_key:
                        market_key = f"shots_on_target_over_under_{shot_key.replace('sot_over_', '')}"
                        
                        max_prob = max(data['over'], data['under'])
                        confidence = self._calculate_market_confidence(max_prob)
                        
                        predictions.append(self._format_prediction(
                            fixture_id=fixture_id,
                            market_key=market_key,
                            prediction={'over': data['over'], 'under': data['under']},
                            confidence=confidence,
                            features_used={'expected_sot': shots.get('expected', {}).get('total_shots_on_target', 9.0)}
                        ))
            
            # Offsides
            offsides = multi_markets.get('offsides', {})
            for offside_key, data in offsides.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    if 'total_over' in offside_key:
                        market_key = f"offsides_over_under_{offside_key.replace('total_over_', '')}"
                        
                        max_prob = max(data['over'], data['under'])
                        confidence = self._calculate_market_confidence(max_prob)
                        
                        predictions.append(self._format_prediction(
                            fixture_id=fixture_id,
                            market_key=market_key,
                            prediction={'over': data['over'], 'under': data['under']},
                            confidence=confidence,
                            features_used={'expected_offsides': offsides.get('expected', {}).get('total', 4.5)}
                        ))
            
            # Team-specific goals
            team_goals = multi_markets.get('team_goals', {})
            for team_key, data in team_goals.items():
                if isinstance(data, dict) and 'over' in data and 'under' in data:
                    team = data.get('team', 'home' if 'home' in team_key else 'away')
                    line = data.get('line', 1.5)
                    market_key = f"{team}_team_over_under_{str(line).replace('.', '_')}"
                    
                    max_prob = max(data['over'], data['under'])
                    confidence = self._calculate_market_confidence(max_prob)
                    
                    predictions.append(self._format_prediction(
                        fixture_id=fixture_id,
                        market_key=market_key,
                        prediction={'over': data['over'], 'under': data['under']},
                        confidence=confidence,
                        features_used={'expected_goals': home_xg if team == 'home' else away_xg}
                    ))
            
            # First Half Goals
            half_time = multi_markets.get('half_time', {})
            if half_time:
                # Convert half-time result to first half O/U 0.5
                ht_home = half_time.get('home', 0.3)
                ht_draw = half_time.get('draw', 0.4)
                ht_away = half_time.get('away', 0.3)
                
                # Probability of at least 1 goal in first half
                first_half_over = 1 - (ht_draw * 0.6)  # Rough approximation
                first_half_under = 1 - first_half_over
                
                confidence = self._calculate_market_confidence(max(first_half_over, first_half_under))
                
                predictions.append(self._format_prediction(
                    fixture_id=fixture_id,
                    market_key='first_half_over_under_0_5',
                    prediction={'over': round(first_half_over, 4), 'under': round(first_half_under, 4)},
                    confidence=confidence,
                    features_used={'expected_ht_goals': (home_xg + away_xg) * 0.45}
                ))
        
        return predictions
    
    def _predict_match_winner(
        self,
        elo_pred: Dict[str, float],
        fixture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict 1X2 match result combining Elo and historical form"""
        
        home_id = fixture['home_team_id']
        away_id = fixture['away_team_id']
        
        # Base probabilities from Elo
        home_win = elo_pred['home_win']
        draw = elo_pred['draw']
        away_win = elo_pred['away_win']
        
        # Get historical features for form adjustment
        features = self.stats.get_match_features(home_id, away_id)
        
        # Apply form adjustment (last 5 matches)
        form_diff = features.get('form_diff', 0.0)  # home_form_ppg - away_form_ppg
        
        # Form adjustment (max ±10%)
        form_adjustment = form_diff * 0.04  # PPG diff of 1.0 = 4% shift
        form_adjustment = max(-0.10, min(0.10, form_adjustment))
        
        # Apply home/away strength adjustments
        home_home_rate = features.get('home_home_win_rate', 0.45)
        away_away_rate = features.get('away_away_win_rate', 0.30)
        
        # Adjust based on venue performance (max ±5%)
        venue_adjustment = (home_home_rate - 0.45) * 0.08 - (away_away_rate - 0.30) * 0.08
        venue_adjustment = max(-0.05, min(0.05, venue_adjustment))
        
        total_adjustment = form_adjustment + venue_adjustment
        
        # Apply adjustments
        home_win = max(0.05, min(0.85, home_win + total_adjustment))
        away_win = max(0.05, min(0.85, away_win - total_adjustment * 0.7))
        draw = 1 - home_win - away_win
        draw = max(0.10, min(0.40, draw))
        
        # Renormalize
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total
        
        # Add some variance based on league competitiveness
        league_variance = self._get_league_variance(fixture['league_id'])
        noise = random.gauss(0, 0.015 * league_variance)
        home_win = max(0.05, min(0.90, home_win + noise))
        away_win = max(0.05, min(0.90, away_win - noise))
        draw = 1 - home_win - away_win
        
        # Calculate confidence based on prediction certainty
        max_prob = max(home_win, draw, away_win)
        confidence = self._calculate_confidence(max_prob, elo_pred['elo_diff'])
        
        # Boost confidence if form agrees with Elo
        if (form_diff > 0 and home_win > away_win) or (form_diff < 0 and away_win > home_win):
            confidence = min(0.92, confidence + 0.05)
        
        return {
            'probabilities': {
                'home_win': round(home_win, 3),
                'draw': round(draw, 3),
                'away_win': round(away_win, 3)
            },
            'confidence': confidence,
            'features': {
                'elo_diff': elo_pred['elo_diff'],
                'home_elo': elo_pred['home_elo'],
                'away_elo': elo_pred['away_elo'],
                'form_diff': round(form_diff, 2),
                'home_form_ppg': features.get('home_form_ppg', 0),
                'away_form_ppg': features.get('away_form_ppg', 0)
            }
        }
    
    def _predict_over_under(
        self,
        elo_pred: Dict[str, float],
        fixture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict Over/Under 2.5 goals using historical data"""
        
        home_id = fixture['home_team_id']
        away_id = fixture['away_team_id']
        
        # Get historical stats prediction
        hist_pred = self.stats.predict_over_under(home_id, away_id, line=2.5)
        
        # Base from historical data (50% weight)
        hist_over = hist_pred['over']
        
        # Elo-based adjustments (50% weight)
        elo_diff = abs(elo_pred['elo_diff'])
        avg_elo = (elo_pred['home_elo'] + elo_pred['away_elo']) / 2
        
        elo_over = 0.52  # Base
        
        # Evenly matched teams tend to have more goals
        if elo_diff < 50:
            elo_over += 0.08
        elif elo_diff < 100:
            elo_over += 0.04
        elif elo_diff > 200:
            elo_over -= 0.05
        
        # Higher quality teams score more
        if avg_elo > 1650:
            elo_over += 0.06
        elif avg_elo > 1550:
            elo_over += 0.03
        elif avg_elo < 1450:
            elo_over -= 0.04
        
        # League adjustments
        league_over_adj = {
            78: 0.05,   # Bundesliga (high scoring)
            135: -0.03, # Serie A (defensive)
            61: 0.02,   # Ligue 1
            39: 0.04,   # Premier League
        }
        elo_over += league_over_adj.get(fixture['league_id'], 0)
        
        # Combine historical and Elo (50/50)
        combined_over = 0.5 * hist_over + 0.5 * elo_over
        
        over_prob = max(0.25, min(0.80, combined_over))
        under_prob = 1 - over_prob
        
        # Confidence higher when both methods agree
        agreement = 1 - abs(hist_over - elo_over)
        confidence = 0.55 + (0.20 * agreement) + (0.10 * abs(over_prob - 0.5) / 0.30)
        
        return {
            'probabilities': {
                'over': round(over_prob, 3),
                'under': round(under_prob, 3)
            },
            'confidence': round(min(0.85, confidence), 2),
            'features': {
                'hist_over': hist_over,
                'elo_over': round(elo_over, 3),
                'expected_goals': hist_pred.get('expected_total_goals', 2.5)
            }
        }
    
    def _predict_btts(
        self,
        elo_pred: Dict[str, float],
        fixture: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict Both Teams to Score using historical data"""
        
        home_id = fixture['home_team_id']
        away_id = fixture['away_team_id']
        
        # Get historical stats prediction
        hist_pred = self.stats.predict_btts(home_id, away_id)
        hist_btts = hist_pred['yes']
        
        # Elo-based BTTS calculation
        elo_diff = abs(elo_pred['elo_diff'])
        
        elo_btts = 0.53  # Base BTTS probability (~53% in top leagues)
        
        # Very mismatched games less likely BTTS
        if elo_diff > 200:
            elo_btts -= 0.12
        elif elo_diff > 150:
            elo_btts -= 0.06
        elif elo_diff < 50:
            elo_btts += 0.05
        
        # High-quality matchups more likely BTTS
        avg_elo = (elo_pred['home_elo'] + elo_pred['away_elo']) / 2
        if avg_elo > 1600:
            elo_btts += 0.04
        
        # Combine historical and Elo (50/50)
        combined_btts = 0.5 * hist_btts + 0.5 * elo_btts
        
        btts_prob = max(0.25, min(0.80, combined_btts))
        no_btts_prob = 1 - btts_prob
        
        # Confidence higher when both methods agree
        agreement = 1 - abs(hist_btts - elo_btts)
        confidence = 0.50 + (0.25 * agreement) + (0.10 * abs(btts_prob - 0.5) / 0.30)
        
        return {
            'probabilities': {
                'yes': round(btts_prob, 3),
                'no': round(no_btts_prob, 3)
            },
            'confidence': round(min(0.85, confidence), 2),
            'features': {
                'hist_btts': hist_btts,
                'elo_btts': round(elo_btts, 3)
            }
        }
    
    def _calculate_confidence(
        self,
        max_prob: float,
        elo_diff: float
    ) -> float:
        """
        Calculate prediction confidence score (0-1)
        
        Higher confidence when:
        - Prediction is more decisive (higher max probability)
        - Elo difference is significant
        - Historical accuracy for similar situations is high
        """
        # Base confidence from prediction certainty
        certainty_score = (max_prob - 0.33) / 0.57  # Normalize from random (0.33) to certain (0.90)
        certainty_score = max(0, min(1, certainty_score))
        
        # Elo difference confidence
        elo_score = min(abs(elo_diff) / 200, 1.0)
        
        # Weighted combination
        confidence = 0.6 * certainty_score + 0.4 * elo_score
        
        # Apply floor and ceiling
        confidence = max(0.45, min(0.92, confidence))
        
        return round(confidence, 2)
    
    def _calculate_market_confidence(self, max_probability: float) -> float:
        """
        Calculate confidence for binary markets based on probability spread
        
        Args:
            max_probability: The highest probability in the market
            
        Returns:
            Confidence score between 0.45 and 0.90
        """
        # Distance from 50/50 (more spread = higher confidence)
        spread = abs(max_probability - 0.5)
        
        # Map spread to confidence
        # 0.50 prob (no edge) -> 0.50 confidence
        # 0.60 prob (20% edge) -> 0.65 confidence
        # 0.70 prob (40% edge) -> 0.75 confidence
        # 0.80 prob (60% edge) -> 0.85 confidence
        confidence = 0.50 + (spread * 0.8)
        
        # Apply floor and ceiling
        confidence = max(0.45, min(0.90, confidence))
        
        return round(confidence, 2)
    
    def _get_league_variance(self, league_id: int) -> float:
        """Get variance factor by league (some leagues more predictable)"""
        variance_map = {
            39: 1.1,   # Premier League (competitive)
            140: 0.9,  # La Liga (top heavy)
            78: 1.2,   # Bundesliga (competitive outside Bayern)
            135: 0.85, # Serie A (predictable)
            61: 0.8,   # Ligue 1 (PSG dominates)
            2: 1.0,    # Champions League
            3: 1.1,    # Europa League
        }
        return variance_map.get(league_id, 1.0)
    
    def _format_prediction(
        self,
        fixture_id: int,
        market_key: str,
        prediction: Dict[str, float],
        confidence: float,
        features_used: Dict = None
    ) -> Dict[str, Any]:
        """Format prediction for database insertion"""
        
        # Determine quality grade based on confidence
        if confidence >= 0.75:
            grade = 'A'
        elif confidence >= 0.65:
            grade = 'B'
        elif confidence >= 0.55:
            grade = 'C'
        else:
            grade = 'D'
        
        return {
            'fixture_id': fixture_id,
            'model_version': self.model_version,
            'model_name': self.model_name,
            'market_key': market_key,
            'prediction': prediction,
            'confidence_score': confidence,
            'quality_grade': grade,
            'features_used': features_used,
            'predicted_at': datetime.utcnow().isoformat()
        }
    
    def batch_predict(
        self,
        fixtures: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Generate predictions for multiple fixtures"""
        all_predictions = []
        
        for fixture in fixtures:
            try:
                predictions = self.predict_fixture(fixture)
                all_predictions.extend(predictions)
            except Exception as e:
                logger.error(
                    "prediction_failed",
                    fixture_id=fixture.get('id'),
                    error=str(e)
                )
                continue
        
        logger.info(
            "batch_prediction_complete",
            fixtures_count=len(fixtures),
            predictions_count=len(all_predictions)
        )
        
        return all_predictions


# Global instance
match_predictor = MatchPredictor()
