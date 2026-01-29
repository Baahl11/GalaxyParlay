'use client';

import type { MultiMarketPrediction } from '@/lib/types';
import { LEAGUE_FLAGS, LEAGUE_NAMES } from '@/lib/types';
import { useState } from 'react';

interface MultiMarketCardProps {
  prediction: MultiMarketPrediction;
}

type TabKey = 'goals' | 'corners' | 'cards' | 'shots' | 'scores';

export function MultiMarketCard({ prediction }: MultiMarketCardProps) {
  const [activeTab, setActiveTab] = useState<TabKey>('goals');
  
  const { predictions, home_team, away_team, is_cup, league_id } = prediction;
  const expected = predictions.expected;
  
  const tabs: { key: TabKey; label: string; icon: string }[] = [
    { key: 'goals', label: 'Goals', icon: '⚽' },
    { key: 'corners', label: 'Corners', icon: '🚩' },
    { key: 'cards', label: 'Cards', icon: '🟨' },
    { key: 'shots', label: 'Shots', icon: '🎯' },
    { key: 'scores', label: 'Scores', icon: '📊' },
  ];
  
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  const getProbColor = (p: number) => {
    if (p >= 0.7) return 'text-green-400';
    if (p >= 0.5) return 'text-yellow-400';
    if (p >= 0.3) return 'text-orange-400';
    return 'text-red-400';
  };

  return (
    <div className="bg-gray-800/60 rounded-2xl border border-gray-700/50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-purple-900/40 to-pink-900/40 p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm text-gray-400">
            {LEAGUE_FLAGS[league_id] || '🏆'} {LEAGUE_NAMES[league_id] || 'League'}
            {is_cup && <span className="ml-2 px-2 py-0.5 bg-yellow-500/20 text-yellow-400 text-xs rounded-full">Cup</span>}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-lg font-bold text-white">{home_team}</span>
          <div className="flex flex-col items-center mx-4">
            <span className="text-2xl font-black text-purple-400">
              {expected.home_goals.toFixed(1)} - {expected.away_goals.toFixed(1)}
            </span>
            <span className="text-xs text-gray-500">Expected Goals</span>
          </div>
          <span className="text-lg font-bold text-white text-right">{away_team}</span>
        </div>
      </div>
      
      {/* Quick Stats */}
      <div className="grid grid-cols-3 gap-2 p-3 bg-gray-900/30 border-b border-gray-700/50">
        <div className="text-center">
          <div className={`text-lg font-bold ${getProbColor(predictions.over_under.over_under_2_5?.over || 0)}`}>
            {formatProb(predictions.over_under.over_under_2_5?.over || 0)}
          </div>
          <div className="text-xs text-gray-500">Over 2.5</div>
        </div>
        <div className="text-center">
          <div className={`text-lg font-bold ${getProbColor(predictions.btts.yes)}`}>
            {formatProb(predictions.btts.yes)}
          </div>
          <div className="text-xs text-gray-500">BTTS</div>
        </div>
        <div className="text-center">
          <div className="text-lg font-bold text-purple-400">
            {(predictions.corners?.expected?.total || 10.5).toFixed(1)}
          </div>
          <div className="text-xs text-gray-500">Exp. Corners</div>
        </div>
      </div>
      
      {/* Tabs */}
      <div className="flex border-b border-gray-700/50">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex-1 px-2 py-2.5 text-xs font-medium transition-colors ${
              activeTab === tab.key
                ? 'bg-purple-500/20 text-purple-400 border-b-2 border-purple-500'
                : 'text-gray-500 hover:text-gray-300 hover:bg-gray-700/30'
            }`}
          >
            <span className="mr-1">{tab.icon}</span>
            {tab.label}
          </button>
        ))}
      </div>
      
      {/* Tab Content */}
      <div className="p-4 min-h-[200px]">
        {activeTab === 'goals' && (
          <GoalsTab predictions={predictions} homeTeam={home_team} awayTeam={away_team} />
        )}
        {activeTab === 'corners' && (
          <CornersTab corners={predictions.corners} homeTeam={home_team} awayTeam={away_team} />
        )}
        {activeTab === 'cards' && (
          <CardsTab cards={predictions.cards} />
        )}
        {activeTab === 'shots' && (
          <ShotsTab shots={predictions.shots} homeTeam={home_team} awayTeam={away_team} />
        )}
        {activeTab === 'scores' && (
          <ScoresTab 
            exactScores={predictions.exact_scores} 
            halfTime={predictions.half_time}
            homeTeam={home_team}
            awayTeam={away_team}
          />
        )}
      </div>
    </div>
  );
}

// Sub-components for each tab
function GoalsTab({ predictions, homeTeam, awayTeam }: { 
  predictions: MultiMarketPrediction['predictions']; 
  homeTeam: string; 
  awayTeam: string;
}) {
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  
  const overUnderLines = [
    { key: 'over_under_1_5', label: 'O/U 1.5' },
    { key: 'over_under_2_5', label: 'O/U 2.5' },
    { key: 'over_under_3_5', label: 'O/U 3.5' },
    { key: 'over_under_4_5', label: 'O/U 4.5' },
  ];
  
  return (
    <div className="space-y-4">
      {/* Total Goals */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Total Goals</h4>
        <div className="grid grid-cols-2 gap-2">
          {overUnderLines.map(line => {
            const data = predictions.over_under[line.key];
            if (!data) return null;
            return (
              <div key={line.key} className="bg-gray-700/30 rounded-lg p-2">
                <div className="text-xs text-gray-500 mb-1">{line.label}</div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-400">Over: {formatProb(data.over)}</span>
                  <span className="text-red-400">Under: {formatProb(data.under)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
      
      {/* Team Goals */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Team Goals</h4>
        <div className="grid grid-cols-2 gap-3">
          {/* Home Team */}
          <div className="space-y-1">
            <div className="text-xs text-purple-400 font-medium">{homeTeam}</div>
            {['home_over_0_5', 'home_over_1_5', 'home_over_2_5'].map(key => {
              const data = predictions.team_goals[key];
              if (!data) return null;
              return (
                <div key={key} className="flex justify-between text-xs bg-gray-700/20 rounded px-2 py-1">
                  <span className="text-gray-400">O {data.line}</span>
                  <span className="text-green-400">{formatProb(data.over)}</span>
                </div>
              );
            })}
          </div>
          {/* Away Team */}
          <div className="space-y-1">
            <div className="text-xs text-pink-400 font-medium">{awayTeam}</div>
            {['away_over_0_5', 'away_over_1_5', 'away_over_2_5'].map(key => {
              const data = predictions.team_goals[key];
              if (!data) return null;
              return (
                <div key={key} className="flex justify-between text-xs bg-gray-700/20 rounded px-2 py-1">
                  <span className="text-gray-400">O {data.line}</span>
                  <span className="text-green-400">{formatProb(data.over)}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>
      
      {/* BTTS */}
      <div className="bg-gradient-to-r from-green-900/20 to-red-900/20 rounded-lg p-3">
        <h4 className="text-xs font-semibold text-gray-400 mb-2">Both Teams to Score</h4>
        <div className="flex justify-around">
          <div className="text-center">
            <div className="text-xl font-bold text-green-400">{formatProb(predictions.btts.yes)}</div>
            <div className="text-xs text-gray-500">Yes</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-red-400">{formatProb(predictions.btts.no)}</div>
            <div className="text-xs text-gray-500">No</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function CornersTab({ corners, homeTeam, awayTeam }: { 
  corners: MultiMarketPrediction['predictions']['corners'];
  homeTeam: string;
  awayTeam: string;
}) {
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  const expected = corners.expected;
  
  return (
    <div className="space-y-4">
      {/* Expected Corners */}
      <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 mb-3">Expected Corners</h4>
        <div className="flex justify-around items-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-400">{expected.home.toFixed(1)}</div>
            <div className="text-xs text-gray-500">{homeTeam}</div>
          </div>
          <div className="text-3xl font-black text-gray-600">+</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-pink-400">{expected.away.toFixed(1)}</div>
            <div className="text-xs text-gray-500">{awayTeam}</div>
          </div>
          <div className="text-3xl font-black text-gray-600">=</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{expected.total.toFixed(1)}</div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
        </div>
      </div>
      
      {/* Total Corners O/U */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Total Corners</h4>
        <div className="grid grid-cols-2 gap-2">
          {['total_over_8_5', 'total_over_9_5', 'total_over_10_5', 'total_over_11_5'].map(key => {
            const data = corners[key] as { over?: number; under?: number } | undefined;
            if (!data || !data.over) return null;
            const line = key.replace('total_over_', '').replace('_', '.');
            return (
              <div key={key} className="bg-gray-700/30 rounded-lg p-2">
                <div className="text-xs text-gray-500 mb-1">O/U {line}</div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-400">O: {formatProb(data.over)}</span>
                  <span className="text-red-400">U: {formatProb(data.under || 0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function CardsTab({ cards }: { cards: MultiMarketPrediction['predictions']['cards'] }) {
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  const expected = cards.expected;
  
  return (
    <div className="space-y-4">
      {/* Expected Cards */}
      <div className="bg-gradient-to-r from-yellow-900/30 to-red-900/30 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 mb-3">Expected Yellow Cards</h4>
        <div className="flex justify-around items-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{expected.home_yellow.toFixed(1)}</div>
            <div className="text-xs text-gray-500">Home</div>
          </div>
          <div className="text-3xl font-black text-gray-600">+</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-400">{expected.away_yellow.toFixed(1)}</div>
            <div className="text-xs text-gray-500">Away</div>
          </div>
          <div className="text-3xl font-black text-gray-600">=</div>
          <div className="text-center">
            <div className="text-2xl font-bold text-yellow-500">{expected.total_yellow.toFixed(1)}</div>
            <div className="text-xs text-gray-500">Total</div>
          </div>
        </div>
      </div>
      
      {/* Total Cards O/U */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Total Yellow Cards</h4>
        <div className="grid grid-cols-2 gap-2">
          {['total_over_2_5', 'total_over_3_5', 'total_over_4_5', 'total_over_5_5'].map(key => {
            const data = cards[key] as { over?: number; under?: number } | undefined;
            if (!data || !data.over) return null;
            const line = key.replace('total_over_', '').replace('_', '.');
            return (
              <div key={key} className="bg-gray-700/30 rounded-lg p-2">
                <div className="text-xs text-gray-500 mb-1">O/U {line}</div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-400">O: {formatProb(data.over)}</span>
                  <span className="text-red-400">U: {formatProb(data.under || 0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ShotsTab({ shots, homeTeam, awayTeam }: { 
  shots: MultiMarketPrediction['predictions']['shots'];
  homeTeam: string;
  awayTeam: string;
}) {
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  const expected = shots.expected;
  
  return (
    <div className="space-y-4">
      {/* Expected Shots */}
      <div className="bg-gradient-to-r from-blue-900/30 to-cyan-900/30 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 mb-3">Expected Shots</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <div className="text-xs text-gray-500 mb-2">Total Shots</div>
            <div className="flex justify-between items-center">
              <div className="text-center">
                <div className="text-lg font-bold text-blue-400">{expected.home_shots}</div>
                <div className="text-xs text-gray-500">{homeTeam}</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-cyan-400">{expected.away_shots}</div>
                <div className="text-xs text-gray-500">{awayTeam}</div>
              </div>
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-2">Shots on Target</div>
            <div className="flex justify-between items-center">
              <div className="text-center">
                <div className="text-lg font-bold text-green-400">{expected.home_shots_on_target}</div>
                <div className="text-xs text-gray-500">{homeTeam}</div>
              </div>
              <div className="text-center">
                <div className="text-lg font-bold text-green-400">{expected.away_shots_on_target}</div>
                <div className="text-xs text-gray-500">{awayTeam}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      {/* SOT O/U */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Shots on Target</h4>
        <div className="grid grid-cols-2 gap-2">
          {['sot_over_7_5', 'sot_over_8_5', 'sot_over_9_5', 'sot_over_10_5'].map(key => {
            const data = shots[key] as { over?: number; under?: number } | undefined;
            if (!data || !data.over) return null;
            const line = key.replace('sot_over_', '').replace('_', '.');
            return (
              <div key={key} className="bg-gray-700/30 rounded-lg p-2">
                <div className="text-xs text-gray-500 mb-1">O/U {line}</div>
                <div className="flex justify-between text-sm">
                  <span className="text-green-400">O: {formatProb(data.over)}</span>
                  <span className="text-red-400">U: {formatProb(data.under || 0)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

function ScoresTab({ exactScores, halfTime, homeTeam, awayTeam }: { 
  exactScores: MultiMarketPrediction['predictions']['exact_scores'];
  halfTime: MultiMarketPrediction['predictions']['half_time'];
  homeTeam: string;
  awayTeam: string;
}) {
  const formatProb = (p: number) => `${(p * 100).toFixed(1)}%`;
  
  return (
    <div className="space-y-4">
      {/* Half-Time Result */}
      <div className="bg-gradient-to-r from-gray-800/50 to-gray-700/50 rounded-lg p-4">
        <h4 className="text-xs font-semibold text-gray-400 mb-3">Half-Time Result</h4>
        <div className="flex justify-around">
          <div className="text-center">
            <div className="text-xl font-bold text-purple-400">{formatProb(halfTime.home)}</div>
            <div className="text-xs text-gray-500">{homeTeam}</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-gray-400">{formatProb(halfTime.draw)}</div>
            <div className="text-xs text-gray-500">Draw</div>
          </div>
          <div className="text-center">
            <div className="text-xl font-bold text-pink-400">{formatProb(halfTime.away)}</div>
            <div className="text-xs text-gray-500">{awayTeam}</div>
          </div>
        </div>
      </div>
      
      {/* Top Exact Scores */}
      <div>
        <h4 className="text-sm font-semibold text-gray-400 mb-2">Most Likely Scores</h4>
        <div className="grid grid-cols-2 gap-2">
          {exactScores.slice(0, 8).map((score, idx) => (
            <div 
              key={score.score}
              className={`rounded-lg p-2 ${
                idx === 0 
                  ? 'bg-gradient-to-r from-yellow-900/30 to-orange-900/30 border border-yellow-500/30' 
                  : 'bg-gray-700/30'
              }`}
            >
              <div className="flex justify-between items-center">
                <span className={`text-lg font-bold ${idx === 0 ? 'text-yellow-400' : 'text-white'}`}>
                  {score.score}
                </span>
                <span className={`text-sm font-medium ${idx === 0 ? 'text-yellow-400' : 'text-gray-400'}`}>
                  {formatProb(score.probability)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
