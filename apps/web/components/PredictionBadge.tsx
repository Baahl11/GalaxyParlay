'use client';

import type { MatchWinnerPrediction, OverUnderPrediction, Prediction } from '@/lib/types';
import { QualityIndicator } from './QualityIndicator';

interface PredictionBadgeProps {
  prediction: Prediction;
  homeTeam: string;
  awayTeam: string;
  compact?: boolean;
}

export function PredictionBadge({ prediction, homeTeam, awayTeam, compact = false }: PredictionBadgeProps) {
  const { market_key, confidence_score, quality_grade } = prediction;
  const pred = prediction.prediction;
  
  // Determine the predicted outcome
  const getPredictedOutcome = () => {
    if (market_key === 'match_winner') {
      const mwPred = pred as MatchWinnerPrediction;
      const outcomes = [
        { key: 'home_win', value: mwPred.home_win, label: homeTeam },
        { key: 'draw', value: mwPred.draw, label: 'Draw' },
        { key: 'away_win', value: mwPred.away_win, label: awayTeam },
      ];
      return outcomes.reduce((a, b) => (a.value > b.value ? a : b));
    }
    
    if (market_key.startsWith('over_under')) {
      const ouPred = pred as OverUnderPrediction;
      const threshold = market_key.split('_').pop();
      return ouPred.over > ouPred.under 
        ? { key: 'over', value: ouPred.over, label: `Over ${threshold}` }
        : { key: 'under', value: ouPred.under, label: `Under ${threshold}` };
    }
    
    if (market_key === 'both_teams_score') {
      const btsPred = pred as { yes: number; no: number };
      return btsPred.yes > btsPred.no
        ? { key: 'yes', value: btsPred.yes, label: 'Both Teams Score' }
        : { key: 'no', value: btsPred.no, label: 'No BTTS' };
    }
    
    return { key: 'unknown', value: 0, label: 'Unknown' };
  };

  const outcome = getPredictedOutcome();
  const confidencePct = Math.round(confidence_score * 100);
  const probabilityPct = Math.round(outcome.value * 100);

  if (compact) {
    return (
      <div className="flex items-center gap-2 bg-gray-800/50 rounded-lg px-3 py-2">
        <QualityIndicator grade={quality_grade} size="sm" />
        <div className="text-sm">
          <span className="font-semibold text-white">{outcome.label}</span>
          <span className="text-gray-400 ml-2">{probabilityPct}%</span>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 rounded-xl p-4 border border-gray-700/50">
      <div className="flex items-start justify-between mb-3">
        <div>
          <div className="text-xs text-gray-500 uppercase tracking-wide mb-1">
            {market_key.replace(/_/g, ' ')}
          </div>
          <div className="text-lg font-bold text-white">{outcome.label}</div>
        </div>
        <QualityIndicator grade={quality_grade} size="md" showLabel />
      </div>
      
      {/* Probability Distribution */}
      {market_key === 'match_winner' && (
        <div className="space-y-2 mb-4">
          <ProbabilityRow 
            label={homeTeam} 
            value={(pred as MatchWinnerPrediction).home_win} 
            isHighest={outcome.key === 'home_win'}
          />
          <ProbabilityRow 
            label="Draw" 
            value={(pred as MatchWinnerPrediction).draw}
            isHighest={outcome.key === 'draw'}
          />
          <ProbabilityRow 
            label={awayTeam} 
            value={(pred as MatchWinnerPrediction).away_win}
            isHighest={outcome.key === 'away_win'}
          />
        </div>
      )}
      
      {/* Confidence Meter */}
      <div className="flex items-center gap-3 pt-3 border-t border-gray-700/50">
        <div className="text-xs text-gray-500">Confidence</div>
        <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
          <div 
            className="h-full bg-gradient-to-r from-purple-500 to-indigo-500"
            style={{ width: `${confidencePct}%` }}
          />
        </div>
        <div className="text-sm font-semibold text-white">{confidencePct}%</div>
      </div>
    </div>
  );
}

interface ProbabilityRowProps {
  label: string;
  value: number;
  isHighest?: boolean;
}

function ProbabilityRow({ label, value, isHighest = false }: ProbabilityRowProps) {
  const pct = Math.round(value * 100);
  
  return (
    <div className="flex items-center gap-3">
      <div className={`w-24 text-sm truncate ${isHighest ? 'text-white font-semibold' : 'text-gray-400'}`}>
        {label}
      </div>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div 
          className={`h-full ${isHighest ? 'bg-purple-500' : 'bg-gray-600'}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <div className={`w-10 text-right text-sm ${isHighest ? 'text-white font-semibold' : 'text-gray-500'}`}>
        {pct}%
      </div>
    </div>
  );
}
