'use client';

import { getTopScorers, getTopShooters } from '@/lib/api';
import type { PlayerStats, TopPlayersResponse } from '@/lib/types';
import { useEffect, useState } from 'react';

type PlayerCategory = 'scorers' | 'shooters';

export function PlayerPropsSection() {
  const [category, setCategory] = useState<PlayerCategory>('scorers');
  const [scorers, setScorers] = useState<TopPlayersResponse | null>(null);
  const [shooters, setShooters] = useState<TopPlayersResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [scorersData, shootersData] = await Promise.all([
        getTopScorers({ limit: 25 }),
        getTopShooters({ limit: 25 })
      ]);
      setScorers(scorersData);
      setShooters(shootersData);
    } catch (err) {
      console.error('Failed to load player data:', err);
    } finally {
      setLoading(false);
    }
  };

  const data = category === 'scorers' ? scorers : shooters;
  const players = data?.players || [];

  return (
    <div className="bg-gray-900/60 rounded-2xl border border-gray-700/50 overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-green-900/40 to-emerald-900/40 p-4 border-b border-gray-700/50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-white">⚽ Player Props</h2>
            <p className="text-sm text-gray-400">Top performers for anytime scorer picks</p>
          </div>
          <button 
            onClick={loadData}
            className="p-2 hover:bg-gray-700/50 rounded-full transition-colors"
            disabled={loading}
          >
            <svg className={`w-5 h-5 text-gray-400 ${loading ? 'animate-spin' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
          </button>
        </div>
        
        {/* Category Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setCategory('scorers')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              category === 'scorers'
                ? 'bg-green-500/30 text-green-400 border border-green-500/30'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
            }`}
          >
            ⚽ Top Scorers
          </button>
          <button
            onClick={() => setCategory('shooters')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              category === 'shooters'
                ? 'bg-blue-500/30 text-blue-400 border border-blue-500/30'
                : 'bg-gray-800/50 text-gray-400 hover:bg-gray-700/50'
            }`}
          >
            🎯 Top Shooters
          </button>
        </div>
      </div>
      
      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="w-10 h-10 border-4 border-gray-700 border-t-green-500 rounded-full animate-spin"></div>
          </div>
        ) : players.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            No player data available
          </div>
        ) : (
          <>
            {/* Summary Stats */}
            <div className="grid grid-cols-3 gap-3 mb-4">
              <div className="bg-gray-800/40 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-green-400">{data?.total_players || 0}</div>
                <div className="text-xs text-gray-500">Players</div>
              </div>
              <div className="bg-gray-800/40 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-purple-400">{data?.total_teams || 0}</div>
                <div className="text-xs text-gray-500">Teams</div>
              </div>
              <div className="bg-gray-800/40 rounded-lg p-3 text-center">
                <div className="text-2xl font-bold text-yellow-400">
                  {category === 'scorers' 
                    ? players[0]?.goals || 0
                    : players[0]?.shots_on_target || 0
                  }
                </div>
                <div className="text-xs text-gray-500">
                  {category === 'scorers' ? 'Top Goals' : 'Top SOT'}
                </div>
              </div>
            </div>
            
            {/* Player List */}
            <div className="space-y-2">
              {players.map((player, idx) => (
                <PlayerCard 
                  key={`${player.team_id}-${player.player_name}`} 
                  player={player} 
                  rank={idx + 1}
                  category={category}
                />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

interface PlayerCardProps {
  player: PlayerStats;
  rank: number;
  category: PlayerCategory;
}

function PlayerCard({ player, rank, category }: PlayerCardProps) {
  const mainStat = category === 'scorers' ? player.goals : player.shots_on_target;
  const mainLabel = category === 'scorers' ? 'Goals' : 'SOT';
  
  const getRankStyle = (rank: number) => {
    if (rank === 1) return 'bg-gradient-to-r from-yellow-500/30 to-amber-500/30 border-yellow-500/30';
    if (rank === 2) return 'bg-gradient-to-r from-gray-400/20 to-slate-400/20 border-gray-400/30';
    if (rank === 3) return 'bg-gradient-to-r from-orange-600/20 to-amber-600/20 border-orange-500/30';
    return 'bg-gray-800/40 border-gray-700/30';
  };
  
  const getRankIcon = (rank: number) => {
    if (rank === 1) return '🥇';
    if (rank === 2) return '🥈';
    if (rank === 3) return '🥉';
    return `${rank}.`;
  };

  // Calculate goals per game ratio for value analysis
  const gamesPlayed = player.games_played || player.appearances || 1;
  const goalsPerGame = player.goals / gamesPlayed;
  const shotsPerGoal = player.goals > 0 ? player.total_shots / player.goals : 0;
  const teamDisplay = player.team_name || `Team ${player.team_id}`;

  return (
    <div className={`rounded-lg p-3 border ${getRankStyle(rank)} transition-all hover:scale-[1.01]`}>
      <div className="flex items-center gap-3">
        {/* Rank */}
        <div className="w-8 text-center">
          <span className={`text-lg ${rank <= 3 ? '' : 'text-gray-500'}`}>
            {getRankIcon(rank)}
          </span>
        </div>
        
        {/* Player Info */}
        <div className="flex-1 min-w-0">
          <div className="font-semibold text-white truncate">{player.player_name}</div>
          <div className="text-xs text-gray-500 truncate">{teamDisplay}</div>
        </div>
        
        {/* Stats */}
        <div className="flex gap-4 items-center">
          {category === 'scorers' ? (
            <>
              <div className="text-center">
                <div className="text-xs text-gray-500">Apps</div>
                <div className="text-sm font-medium text-gray-300">{gamesPlayed}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500">G/Game</div>
                <div className={`text-sm font-medium ${goalsPerGame >= 0.7 ? 'text-green-400' : 'text-gray-300'}`}>
                  {goalsPerGame.toFixed(2)}
                </div>
              </div>
            </>
          ) : (
            <>
              <div className="text-center">
                <div className="text-xs text-gray-500">Shots</div>
                <div className="text-sm font-medium text-gray-300">{player.total_shots}</div>
              </div>
              <div className="text-center">
                <div className="text-xs text-gray-500">Accuracy</div>
                <div className={`text-sm font-medium ${
                  player.total_shots > 0 && (player.shots_on_target / player.total_shots) >= 0.5 
                    ? 'text-green-400' 
                    : 'text-gray-300'
                }`}>
                  {player.total_shots > 0 
                    ? `${((player.shots_on_target / player.total_shots) * 100).toFixed(0)}%`
                    : '-'
                  }
                </div>
              </div>
            </>
          )}
          
          {/* Main Stat */}
          <div className={`text-center min-w-[50px] px-3 py-1 rounded-lg ${
            category === 'scorers' ? 'bg-green-500/20' : 'bg-blue-500/20'
          }`}>
            <div className={`text-xl font-bold ${
              category === 'scorers' ? 'text-green-400' : 'text-blue-400'
            }`}>
              {mainStat}
            </div>
            <div className="text-xs text-gray-500">{mainLabel}</div>
          </div>
        </div>
      </div>
      
      {/* Additional Stats Row */}
      {rank <= 10 && (
        <div className="mt-2 pt-2 border-t border-gray-700/30 flex gap-4 text-xs">
          <span className="text-gray-500">
            ⚡ {player.total_shots} shots
          </span>
          <span className="text-gray-500">
            🎯 {player.shots_on_target} on target
          </span>
          {player.goals > 0 && (
            <span className="text-gray-500">
              📊 {shotsPerGoal.toFixed(1)} shots/goal
            </span>
          )}
        </div>
      )}
    </div>
  );
}
