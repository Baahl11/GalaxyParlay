"""
Quality Scoring System
Evaluates and grades prediction quality based on multiple factors
"""
from typing import Dict, List, Any, Optional
from datetime import datetime
import structlog

logger = structlog.get_logger()


class QualityScorer:
    """
    Assigns quality grades to predictions based on:
    - Data coverage (how much data available for prediction)
    - Model confidence (how certain the model is)
    - Historical accuracy (how accurate similar predictions have been)
    """
    
    # Grade thresholds
    GRADE_THRESHOLDS = {
        'A': 0.75,  # Excellent - high confidence, good data
        'B': 0.60,  # Good - solid prediction
        'C': 0.45,  # Fair - moderate confidence
        'D': 0.30,  # Low - limited data or confidence
        'F': 0.0,   # Poor - insufficient for prediction
    }
    
    # Historical accuracy by league (simulated for now)
    LEAGUE_ACCURACY = {
        39: 0.62,   # Premier League
        140: 0.64,  # La Liga
        78: 0.60,   # Bundesliga
        135: 0.63,  # Serie A
        61: 0.65,   # Ligue 1
        2: 0.58,    # Champions League
        3: 0.56,    # Europa League
    }
    
    def __init__(self):
        self.accuracy_history: Dict[str, List[float]] = {}
    
    def score_prediction(
        self,
        prediction: Dict[str, Any],
        fixture: Dict[str, Any],
        data_availability: Dict[str, bool] = None
    ) -> Dict[str, Any]:
        """
        Calculate quality score for a prediction
        
        Args:
            prediction: Prediction data
            fixture: Fixture data
            data_availability: Dict indicating what data was available
        
        Returns:
            Quality score dict ready for database insertion
        """
        data_availability = data_availability or {}
        
        # 1. Data Coverage Score (0-1)
        data_score = self._calculate_data_coverage(data_availability, fixture)
        
        # 2. Model Confidence (already 0-1)
        confidence = prediction.get('confidence_score', 0.5)
        
        # 3. Historical Accuracy (0-1)
        league_id = fixture.get('league_id', 39)
        historical_accuracy = self._get_historical_accuracy(
            league_id=league_id,
            market_key=prediction.get('market_key', 'match_winner')
        )
        
        # Calculate weighted final score
        final_score = (
            0.35 * data_score +
            0.40 * confidence +
            0.25 * historical_accuracy
        )
        
        # Determine grade
        grade = self._score_to_grade(final_score)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(
            data_score=data_score,
            confidence=confidence,
            historical_accuracy=historical_accuracy,
            grade=grade
        )
        
        return {
            'fixture_id': fixture['id'],
            'market_key': prediction.get('market_key', 'match_winner'),
            'data_coverage_score': round(data_score, 2),
            'model_confidence': round(confidence, 2),
            'historical_accuracy': round(historical_accuracy, 2),
            'final_grade': grade,
            'reasoning': reasoning,
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def _calculate_data_coverage(
        self,
        data_availability: Dict[str, bool],
        fixture: Dict[str, Any]
    ) -> float:
        """
        Calculate data coverage score based on available data
        """
        # Default weights for different data sources
        data_weights = {
            'has_team_stats': 0.20,
            'has_h2h': 0.15,
            'has_recent_form': 0.20,
            'has_odds': 0.15,
            'has_injuries': 0.10,
            'has_lineups': 0.10,
            'has_weather': 0.05,
            'has_venue_stats': 0.05,
        }
        
        if not data_availability:
            # Estimate based on league tier
            league_id = fixture.get('league_id', 0)
            if league_id in [39, 140, 78, 135, 61]:  # Top 5 leagues
                return 0.85  # Usually have good data
            elif league_id in [2, 3]:  # European cups
                return 0.80
            else:
                return 0.70
        
        score = 0.0
        for key, weight in data_weights.items():
            if data_availability.get(key, False):
                score += weight
        
        # Bonus for complete data
        if score >= 0.90:
            score = min(1.0, score + 0.05)
        
        return score
    
    def _get_historical_accuracy(
        self,
        league_id: int,
        market_key: str
    ) -> float:
        """
        Get historical accuracy for predictions in this league/market
        """
        # Base accuracy from league
        base_accuracy = self.LEAGUE_ACCURACY.get(league_id, 0.55)
        
        # Market-specific adjustments
        market_adjustments = {
            'match_winner': 0.0,
            'over_under_2.5': -0.02,  # Slightly harder to predict
            'both_teams_score': -0.03,
        }
        
        adjustment = market_adjustments.get(market_key, 0)
        
        return max(0.40, min(0.75, base_accuracy + adjustment))
    
    def _score_to_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        for grade, threshold in self.GRADE_THRESHOLDS.items():
            if score >= threshold:
                return grade
        return 'F'
    
    def _generate_reasoning(
        self,
        data_score: float,
        confidence: float,
        historical_accuracy: float,
        grade: str
    ) -> str:
        """Generate human-readable reasoning for the quality grade"""
        
        reasons = []
        
        # Data coverage assessment
        if data_score >= 0.90:
            reasons.append("Excellent data coverage")
        elif data_score >= 0.75:
            reasons.append("High data coverage")
        elif data_score >= 0.60:
            reasons.append("Good data coverage")
        else:
            reasons.append("Limited data available")
        
        # Confidence assessment
        if confidence >= 0.80:
            reasons.append("very strong model confidence")
        elif confidence >= 0.70:
            reasons.append("strong model confidence")
        elif confidence >= 0.60:
            reasons.append("moderate model confidence")
        else:
            reasons.append("lower model confidence")
        
        # Historical accuracy
        if historical_accuracy >= 0.65:
            reasons.append("excellent historical accuracy")
        elif historical_accuracy >= 0.58:
            reasons.append("good historical accuracy")
        else:
            reasons.append("mixed historical results")
        
        return ", ".join(reasons)
    
    def batch_score(
        self,
        predictions: List[Dict[str, Any]],
        fixtures: Dict[int, Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Score multiple predictions
        
        Args:
            predictions: List of prediction dicts
            fixtures: Dict mapping fixture_id -> fixture data
        
        Returns:
            List of quality score dicts
        """
        scores = []
        
        for pred in predictions:
            fixture_id = pred.get('fixture_id')
            fixture = fixtures.get(fixture_id, {'id': fixture_id, 'league_id': 39})
            
            try:
                score = self.score_prediction(pred, fixture)
                scores.append(score)
            except Exception as e:
                logger.error(
                    "quality_scoring_failed",
                    fixture_id=fixture_id,
                    error=str(e)
                )
                continue
        
        logger.info(
            "batch_scoring_complete",
            predictions_count=len(predictions),
            scores_count=len(scores)
        )
        
        return scores
    
    def update_accuracy_history(
        self,
        market_key: str,
        league_id: int,
        was_correct: bool
    ):
        """
        Update historical accuracy after match completion
        Used for model calibration
        """
        key = f"{league_id}_{market_key}"
        
        if key not in self.accuracy_history:
            self.accuracy_history[key] = []
        
        self.accuracy_history[key].append(1.0 if was_correct else 0.0)
        
        # Keep only last 100 results
        if len(self.accuracy_history[key]) > 100:
            self.accuracy_history[key] = self.accuracy_history[key][-100:]
        
        logger.info(
            "accuracy_updated",
            market_key=market_key,
            league_id=league_id,
            was_correct=was_correct,
            running_accuracy=sum(self.accuracy_history[key]) / len(self.accuracy_history[key])
        )


# Global instance
quality_scorer = QualityScorer()
