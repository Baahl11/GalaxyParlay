'use client';

import { formatKickoffTime, getTimeUntilKickoff } from '@/lib/api';
import type { Fixture, MatchWinnerOdds } from '@/lib/types';
import { LEAGUE_FLAGS, LEAGUE_NAMES } from '@/lib/types';
import { PredictionBadge } from './PredictionBadge';
import { QualityIndicator } from './QualityIndicator';

interface FixtureCardProps {
  fixture: Fixture;
  expanded?: boolean;
  onToggle?: () => void;
  onClick?: () => void;
}

export function FixtureCard({ fixture, expanded = false, onToggle, onClick }: FixtureCardProps) {
  const {
    home_team_name,
    away_team_name,
    kickoff_time,
    venue,
    league_id,
    status,
    predictions = [],
    quality_scores = [],
    odds = [],
  } = fixture;

  const leagueName = LEAGUE_NAMES[league_id] || `League ${league_id}`;
  const leagueFlag = LEAGUE_FLAGS[league_id] || '⚽';
  
  // Get main prediction (match_winner)
  const mainPrediction = predictions.find(p => p.market_key === 'match_winner');
  const mainQuality = quality_scores.find(q => q.market_key === 'match_winner');
  const mainOdds = odds.find(o => o.market_key === 'match_winner');

  // Determine predicted winner
  const getPredictedWinner = () => {
    if (!mainPrediction) return null;
    const pred = mainPrediction.prediction as { home_win: number; draw: number; away_win: number };
    if (pred.home_win > pred.draw && pred.home_win > pred.away_win) return 'home';
    if (pred.away_win > pred.draw && pred.away_win > pred.home_win) return 'away';
    return 'draw';
  };

  const predictedWinner = getPredictedWinner();
  const timeUntil = getTimeUntilKickoff(kickoff_time);
  const isLive = ['LIVE', '1H', 'HT', '2H'].includes(status);
  const isFinished = status === 'FT';

  const handleClick = () => {
    if (onClick) {
      onClick();
    }
  };

  return (
    <div 
      onClick={handleClick}
      className={`
        bg-gradient-to-br from-gray-900 to-gray-800 
        rounded-2xl overflow-hidden
        border border-gray-700/50
        hover:border-purple-500/50 
        transition-all duration-300
        ${expanded ? 'ring-2 ring-purple-500/30' : ''}
        ${onClick ? 'cursor-pointer hover:scale-[1.02]' : ''}
      `}
    >
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-lg">{leagueFlag}</span>
          <span className="text-sm text-gray-400">{leagueName}</span>
        </div>
        <div className="flex items-center gap-3">
          {mainQuality && (
            <QualityIndicator grade={mainQuality.final_grade} size="sm" />
          )}
          {isLive && (
            <span className="px-2 py-0.5 bg-red-500 text-white text-xs font-bold rounded animate-pulse">
              LIVE
            </span>
          )}
          {!isLive && !isFinished && (
            <span className="text-sm text-purple-400 font-medium">{timeUntil}</span>
          )}
        </div>
      </div>

      {/* Teams */}
      <div className="p-4" onClick={onToggle} role="button" tabIndex={0}>
        <div className="flex items-center justify-between gap-4">
          {/* Home Team */}
          <div className={`flex-1 text-right ${predictedWinner === 'home' ? 'opacity-100' : 'opacity-70'}`}>
            <div className={`text-lg font-bold ${predictedWinner === 'home' ? 'text-white' : 'text-gray-300'}`}>
              {home_team_name}
            </div>
            {mainOdds && (
              <div className="text-sm text-gray-500 mt-1">
                {(mainOdds.odds_data as MatchWinnerOdds).home.toFixed(2)}
              </div>
            )}
          </div>

          {/* VS / Score */}
          <div className="flex flex-col items-center px-4">
            {isFinished ? (
              <div className="text-2xl font-bold text-white">
                {fixture.home_score} - {fixture.away_score}
              </div>
            ) : (
              <>
                <div className="text-gray-500 text-sm font-medium">VS</div>
                {mainOdds && (
                  <div className="text-xs text-gray-600 mt-1">
                    Draw {(mainOdds.odds_data as MatchWinnerOdds).draw.toFixed(2)}
                  </div>
                )}
              </>
            )}
          </div>

          {/* Away Team */}
          <div className={`flex-1 text-left ${predictedWinner === 'away' ? 'opacity-100' : 'opacity-70'}`}>
            <div className={`text-lg font-bold ${predictedWinner === 'away' ? 'text-white' : 'text-gray-300'}`}>
              {away_team_name}
            </div>
            {mainOdds && (
              <div className="text-sm text-gray-500 mt-1">
                {(mainOdds.odds_data as MatchWinnerOdds).away.toFixed(2)}
              </div>
            )}
          </div>
        </div>

        {/* Quick Prediction Preview */}
        {mainPrediction && !expanded && (
          <div className="mt-4 flex items-center justify-center">
            <PredictionBadge 
              prediction={mainPrediction} 
              homeTeam={home_team_name}
              awayTeam={away_team_name}
              compact 
            />
          </div>
        )}
      </div>

      {/* Expanded Details */}
      {expanded && mainPrediction && (
        <div className="px-4 pb-4 space-y-4 animate-fadeIn">
          <PredictionBadge 
            prediction={mainPrediction} 
            homeTeam={home_team_name}
            awayTeam={away_team_name}
          />
          
          {/* Additional Markets */}
          {predictions.filter(p => p.market_key !== 'match_winner').length > 0 && (
            <div className="grid grid-cols-2 gap-3">
              {predictions
                .filter(p => p.market_key !== 'match_winner')
                .map(pred => (
                  <PredictionBadge 
                    key={pred.id}
                    prediction={pred}
                    homeTeam={home_team_name}
                    awayTeam={away_team_name}
                    compact
                  />
                ))
              }
            </div>
          )}

          {/* Match Info */}
          <div className="text-xs text-gray-500 flex items-center justify-between pt-3 border-t border-gray-700/50">
            <span>📅 {formatKickoffTime(kickoff_time)}</span>
            {venue && <span>🏟️ {venue}</span>}
          </div>
        </div>
      )}
    </div>
  );
}
