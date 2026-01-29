'use client';

import { LEAGUE_FLAGS, LEAGUE_NAMES } from '@/lib/types';

export interface ValueBetData {
  fixture_id: number;
  home_team: string;
  away_team: string;
  league_id: number;
  kickoff_time: string;
  market_key: string;
  selection: string;
  model_probability: number;
  implied_probability: number;
  bookmaker_odds: number;
  bookmaker: string;
  edge: number;
  edge_percent: number;
  expected_value: number;
  ev_percent: number;
  kelly_fraction: number;
  kelly_percent: number;
  confidence_score: number;
  quality_grade: string;
  value_score: number;
}

interface ValueBetCardProps {
  valueBet: ValueBetData;
  compact?: boolean;
}

export function ValueBetCard({ valueBet, compact = false }: ValueBetCardProps) {
  const {
    home_team,
    away_team,
    league_id,
    kickoff_time,
    selection,
    market_key,
    model_probability,
    bookmaker_odds,
    bookmaker,
    edge_percent,
    ev_percent,
    kelly_percent,
    confidence_score,
    quality_grade,
    value_score,
  } = valueBet;

  const leagueFlag = LEAGUE_FLAGS[league_id] || '⚽';
  const leagueName = LEAGUE_NAMES[league_id] || `League ${league_id}`;

  // Format kickoff time
  const kickoff = new Date(kickoff_time);
  const timeStr = kickoff.toLocaleTimeString('en-US', { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: false 
  });
  const dateStr = kickoff.toLocaleDateString('en-US', { 
    weekday: 'short',
    month: 'short', 
    day: 'numeric' 
  });

  // Grade colors
  const gradeColors: Record<string, string> = {
    'A': 'bg-green-500',
    'B': 'bg-blue-500',
    'C': 'bg-yellow-500',
    'D': 'bg-orange-500',
    'F': 'bg-red-500',
  };

  // Market display names
  const marketNames: Record<string, string> = {
    'match_winner': '1X2',
    'over_under_2.5': 'O/U 2.5',
    'both_teams_score': 'BTTS',
  };

  // EV color based on value
  const getEvColor = (ev: number) => {
    if (ev >= 10) return 'text-green-400';
    if (ev >= 5) return 'text-emerald-400';
    if (ev >= 3) return 'text-yellow-400';
    return 'text-orange-400';
  };

  if (compact) {
    return (
      <div className="bg-gray-800/50 rounded-xl p-3 border border-gray-700/50 hover:border-purple-500/50 transition-all">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-gray-400">{leagueFlag} {leagueName}</span>
          <span className={`px-1.5 py-0.5 rounded text-xs font-bold text-white ${gradeColors[quality_grade]}`}>
            {quality_grade}
          </span>
        </div>
        
        <div className="text-sm font-medium text-white mb-1">
          {home_team} vs {away_team}
        </div>
        
        <div className="flex items-center justify-between">
          <div>
            <span className="text-purple-400 font-semibold">{selection}</span>
            <span className="text-gray-500 ml-2">@ {bookmaker_odds.toFixed(2)}</span>
          </div>
          <div className={`font-bold ${getEvColor(ev_percent)}`}>
            +{ev_percent}% EV
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl overflow-hidden border border-gray-700/50 hover:border-green-500/50 transition-all duration-300">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-700/50 flex items-center justify-between bg-gradient-to-r from-green-900/20 to-transparent">
        <div className="flex items-center gap-2">
          <span className="text-lg">{leagueFlag}</span>
          <span className="text-sm text-gray-400">{leagueName}</span>
          <span className="text-xs text-gray-500">• {marketNames[market_key]}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className={`px-2 py-0.5 rounded text-xs font-bold text-white ${gradeColors[quality_grade]}`}>
            Grade {quality_grade}
          </span>
          <span className="text-xs text-gray-500">{dateStr} {timeStr}</span>
        </div>
      </div>

      {/* Match Info */}
      <div className="p-4">
        <div className="text-center mb-4">
          <div className="text-lg font-bold text-white">
            {home_team} <span className="text-gray-500">vs</span> {away_team}
          </div>
        </div>

        {/* Selection & Odds */}
        <div className="bg-gray-800/50 rounded-xl p-4 mb-4">
          <div className="flex items-center justify-between mb-3">
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-wide">Selection</div>
              <div className="text-xl font-bold text-purple-400">{selection}</div>
            </div>
            <div className="text-right">
              <div className="text-xs text-gray-400 uppercase tracking-wide">{bookmaker}</div>
              <div className="text-2xl font-bold text-white">{bookmaker_odds.toFixed(2)}</div>
            </div>
          </div>
          
          {/* Probability comparison */}
          <div className="flex items-center gap-4 text-sm">
            <div className="flex-1">
              <div className="text-gray-400 text-xs">Model Probability</div>
              <div className="text-white font-medium">{(model_probability * 100).toFixed(1)}%</div>
            </div>
            <div className="text-2xl text-green-400">→</div>
            <div className="flex-1 text-right">
              <div className="text-gray-400 text-xs">Implied from Odds</div>
              <div className="text-gray-300 font-medium">{(valueBet.implied_probability * 100).toFixed(1)}%</div>
            </div>
          </div>
        </div>

        {/* Value Metrics */}
        <div className="grid grid-cols-3 gap-3">
          {/* Edge */}
          <div className="bg-gray-800/30 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Edge</div>
            <div className="text-xl font-bold text-blue-400">+{edge_percent}%</div>
          </div>
          
          {/* EV */}
          <div className="bg-gray-800/30 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Expected Value</div>
            <div className={`text-xl font-bold ${getEvColor(ev_percent)}`}>+{ev_percent}%</div>
          </div>
          
          {/* Kelly */}
          <div className="bg-gray-800/30 rounded-lg p-3 text-center">
            <div className="text-xs text-gray-400 uppercase tracking-wide mb-1">Kelly Stake</div>
            <div className="text-xl font-bold text-purple-400">{kelly_percent}%</div>
          </div>
        </div>

        {/* Value Score Bar */}
        <div className="mt-4">
          <div className="flex items-center justify-between text-xs text-gray-400 mb-1">
            <span>Value Score</span>
            <span>{value_score.toFixed(0)}/100</span>
          </div>
          <div className="h-2 bg-gray-700 rounded-full overflow-hidden">
            <div 
              className="h-full bg-gradient-to-r from-green-500 to-emerald-400 rounded-full transition-all duration-500"
              style={{ width: `${Math.min(value_score, 100)}%` }}
            />
          </div>
        </div>

        {/* Confidence */}
        <div className="mt-3 flex items-center justify-between text-sm">
          <span className="text-gray-400">Model Confidence</span>
          <span className="text-white font-medium">{(confidence_score * 100).toFixed(0)}%</span>
        </div>
      </div>
    </div>
  );
}
