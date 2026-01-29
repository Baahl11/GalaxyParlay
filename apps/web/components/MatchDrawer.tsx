'use client';

import { getMultiMarketPrediction } from '@/lib/api';
import type { Fixture, MultiMarketPrediction } from '@/lib/types';
import { LEAGUE_FLAGS, LEAGUE_NAMES } from '@/lib/types';
import { useEffect, useState } from 'react';
import { MultiMarketCard } from './MultiMarketCard';

interface MatchDrawerProps {
  fixture: Fixture | null;
  isOpen: boolean;
  onClose: () => void;
}

export function MatchDrawer({ fixture, isOpen, onClose }: MatchDrawerProps) {
  const [prediction, setPrediction] = useState<MultiMarketPrediction | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (fixture && isOpen) {
      loadPrediction();
    }
  }, [fixture?.id, isOpen]);

  const loadPrediction = async () => {
    if (!fixture) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const data = await getMultiMarketPrediction(fixture.id);
      setPrediction(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load predictions');
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { 
      weekday: 'short', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 transition-opacity"
        onClick={onClose}
      />
      
      {/* Drawer */}
      <div className="fixed inset-y-0 right-0 w-full max-w-lg bg-gray-900 shadow-2xl z-50 overflow-y-auto border-l border-gray-700/50 transform transition-transform">
        {/* Header */}
        <div className="sticky top-0 bg-gray-900/95 backdrop-blur-sm border-b border-gray-700/50 p-4 z-10">
          <div className="flex items-center justify-between">
            <div>
              {fixture && (
                <span className="text-sm text-gray-400">
                  {LEAGUE_FLAGS[fixture.league_id] || '🏆'} {LEAGUE_NAMES[fixture.league_id] || 'League'}
                </span>
              )}
            </div>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-700/50 rounded-full transition-colors"
            >
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          {fixture && (
            <div className="mt-3">
              <div className="flex items-center justify-between text-xl font-bold text-white">
                <span>{fixture.home_team_name}</span>
                <span className="text-gray-500">vs</span>
                <span className="text-right">{fixture.away_team_name}</span>
              </div>
              <div className="text-center text-sm text-gray-500 mt-1">
                {formatDate(fixture.kickoff_time)}
              </div>
            </div>
          )}
        </div>
        
        {/* Content */}
        <div className="p-4">
          {loading && (
            <div className="flex flex-col items-center justify-center py-16">
              <div className="relative w-16 h-16">
                <div className="absolute inset-0 rounded-full border-4 border-purple-500/20"></div>
                <div className="absolute inset-0 rounded-full border-4 border-transparent border-t-purple-500 animate-spin"></div>
              </div>
              <p className="text-gray-500 mt-4">Analyzing match...</p>
            </div>
          )}
          
          {error && (
            <div className="bg-red-900/20 border border-red-500/30 rounded-lg p-4 text-center">
              <p className="text-red-400">{error}</p>
              <button
                onClick={loadPrediction}
                className="mt-3 px-4 py-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition-colors"
              >
                Retry
              </button>
            </div>
          )}
          
          {prediction && !loading && (
            <div className="space-y-6">
              {/* Main Prediction Card */}
              <MultiMarketCard prediction={prediction} />
              
              {/* Quality & Confidence */}
              <div className="bg-gray-800/60 rounded-xl p-4 border border-gray-700/50">
                <h3 className="text-sm font-semibold text-gray-400 mb-3">Prediction Quality</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Quality Score</div>
                    <div className="flex items-center">
                      <div className="text-2xl font-bold text-purple-400">
                        {prediction.quality_score.toFixed(2)}
                      </div>
                      <div className="ml-2 text-xs text-gray-500">/1.00</div>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-500 mb-1">Status</div>
                    <div className={`inline-flex items-center px-2 py-1 rounded-full text-sm ${
                      prediction.quality_score >= 0.7 
                        ? 'bg-green-500/20 text-green-400'
                        : prediction.quality_score >= 0.5
                        ? 'bg-yellow-500/20 text-yellow-400'
                        : 'bg-orange-500/20 text-orange-400'
                    }`}>
                      {prediction.quality_score >= 0.7 ? '✅ High' : prediction.quality_score >= 0.5 ? '⚠️ Medium' : '🔶 Low'}
                    </div>
                  </div>
                </div>
              </div>
              
              {/* Best Bets Section */}
              <div className="bg-gradient-to-r from-purple-900/30 to-pink-900/30 rounded-xl p-4 border border-purple-500/20">
                <h3 className="text-sm font-semibold text-purple-400 mb-3">🎯 Best Picks</h3>
                <div className="space-y-2">
                  {prediction.predictions.over_under.over_under_2_5?.over >= 0.6 && (
                    <BestPickItem 
                      label="Over 2.5 Goals"
                      probability={prediction.predictions.over_under.over_under_2_5.over}
                    />
                  )}
                  {prediction.predictions.btts.yes >= 0.6 && (
                    <BestPickItem 
                      label="Both Teams to Score"
                      probability={prediction.predictions.btts.yes}
                    />
                  )}
                  {(() => {
                    const corners95 = prediction.predictions.corners?.total_over_9_5;
                    if (corners95 && 'over' in corners95 && typeof corners95.over === 'number' && corners95.over >= 0.6) {
                      return (
                        <BestPickItem 
                          label="Over 9.5 Corners"
                          probability={corners95.over}
                        />
                      );
                    }
                    return null;
                  })()}
                  {prediction.predictions.exact_scores[0] && (
                    <BestPickItem 
                      label={`Correct Score: ${prediction.predictions.exact_scores[0].score}`}
                      probability={prediction.predictions.exact_scores[0].probability}
                    />
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function BestPickItem({ label, probability }: { label: string; probability: number }) {
  return (
    <div className="flex items-center justify-between bg-gray-800/40 rounded-lg px-3 py-2">
      <span className="text-sm text-white">{label}</span>
      <span className={`text-sm font-bold ${
        probability >= 0.7 ? 'text-green-400' : 
        probability >= 0.5 ? 'text-yellow-400' : 'text-orange-400'
      }`}>
        {(probability * 100).toFixed(1)}%
      </span>
    </div>
  );
}
